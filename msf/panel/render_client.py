"""Client for the long-lived Remotion render server.

WHY NOT `npx remotion still` PER PREVIEW
----------------------------------------
Because the panel promises previews that update as you change a parameter, and
`npx remotion still` re-bundles every time. Measured on this machine: 19.7s cold,
and even warm the CLI pays process startup plus bundle resolution. Holding one
node process open with the bundle in memory brings a still down to ~1.7s, which is
the difference between "adjust and see" and "adjust and go make tea".

The server is `remotion/scripts/render_server.mjs`, spoken to over newline-JSON on
stdin/stdout. This module owns its lifecycle: one process per panel, started on
first use, restarted if it dies.

THREAD SAFETY
-------------
FastAPI serves requests on a threadpool, so two previews can arrive at once. A
single lock serialises access to the pipe — interleaved writes would corrupt the
JSON stream, and the server processes requests serially anyway (renderMedia
already uses all cores).
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

REPO = Path(__file__).resolve().parents[2]
REMOTION = REPO / "remotion"
SERVER_SCRIPT = REMOTION / "scripts" / "render_server.mjs"

# Cold start includes a webpack bundle. 19.7s measured; 180s leaves room for a
# slower machine or a cache miss without hanging a request forever.
_STARTUP_TIMEOUT = 180.0
# A still is ~1.7s and a 60-frame clip ~4.3s, both at scale 0.5. 300s is generous
# for a full-length clip of a long scene.
_REQUEST_TIMEOUT = 300.0


class RenderServerError(RuntimeError):
    """Raised when the render server fails or cannot be reached.

    Deliberately NOT caught-and-defaulted anywhere: a preview that silently shows
    a stale PNG is worse than an error, because the whole point of the preview is
    to tell you what the current parameters look like.
    """


class RenderClient:
    """Owns one render server process."""

    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._seq = 0
        self.last_error: Optional[str] = None
        self.started_at: Optional[float] = None

    # ------------------------------------------------------------- lifecycle

    def _alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _spawn(self) -> None:
        if not SERVER_SCRIPT.is_file():
            raise RenderServerError(f"render server script missing: {SERVER_SCRIPT}")
        if not (REMOTION / "node_modules").is_dir():
            raise RenderServerError(
                "remotion/node_modules is missing — run `npm install` in remotion/"
            )
        env = os.environ.copy()
        # Sandbox images ship Chromium already. Explicitly choosing it avoids a
        # first-preview attempt that waits for Remotion to download another browser
        # shell; non-Linux or custom installations keep Remotion's default.
        system_chromium = Path("/usr/bin/chromium")
        if system_chromium.is_file() and not env.get("MSF_CHROMIUM"):
            env["MSF_CHROMIUM"] = str(system_chromium)
        self._proc = subprocess.Popen(
            ["node", str(SERVER_SCRIPT)],
            cwd=str(REMOTION),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            shell=False,
            env=env,
        )
        self.started_at = time.time()

        # Wait for the `ready` event: the first preview would otherwise block for
        # the whole bundle with no way to tell the user why.
        deadline = time.time() + _STARTUP_TIMEOUT
        while time.time() < deadline:
            line = self._readline(deadline - time.time())
            if line is None:
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("event") == "ready":
                if not msg.get("ok"):
                    self.last_error = msg.get("error", "bundle failed")
                    raise RenderServerError(f"render server bundle failed: {self.last_error}")
                return
        raise RenderServerError(
            f"render server did not become ready within {_STARTUP_TIMEOUT:.0f}s"
        )

    def _readline(self, timeout: float) -> Optional[str]:
        """Read one line with a deadline.

        `readline()` on a pipe blocks forever if the child dies without closing
        stdout, which turns a crashed renderer into a hung panel. A reader thread
        with a join timeout is the portable way to bound it — select() does not
        work on Windows pipes.
        """
        assert self._proc is not None and self._proc.stdout is not None
        box: Dict[str, Optional[str]] = {"line": None}

        def read() -> None:
            try:
                box["line"] = self._proc.stdout.readline()  # type: ignore[union-attr]
            except Exception:
                box["line"] = None

        t = threading.Thread(target=read, daemon=True)
        t.start()
        t.join(max(0.1, timeout))
        if t.is_alive():
            return None
        line = box["line"]
        return line.strip() if line else None

    def stop(self) -> None:
        with self._lock:
            if self._alive():
                assert self._proc is not None
                try:
                    self._proc.stdin.close()  # type: ignore[union-attr]
                except Exception:
                    pass
                try:
                    self._proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            self._proc = None

    # --------------------------------------------------------------- request

    def _request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if not self._alive():
                self._spawn()
            assert self._proc is not None and self._proc.stdin is not None

            self._seq += 1
            req_id = f"r{self._seq}"
            payload["id"] = req_id
            try:
                self._proc.stdin.write(json.dumps(payload) + "\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                self._proc = None
                raise RenderServerError(f"render server pipe broke: {exc}") from exc

            deadline = time.time() + _REQUEST_TIMEOUT
            while time.time() < deadline:
                line = self._readline(deadline - time.time())
                if line is None:
                    if not self._alive():
                        self._proc = None
                        raise RenderServerError("render server exited mid-request")
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Ignore stale replies from a previous, timed-out request rather
                # than returning one request's answer for another.
                if msg.get("id") != req_id:
                    continue
                if not msg.get("ok"):
                    self.last_error = msg.get("error", "unknown render error")
                    raise RenderServerError(self.last_error)
                return msg
            raise RenderServerError(f"render timed out after {_REQUEST_TIMEOUT:.0f}s")

    # ------------------------------------------------------------------ ops

    def ping(self) -> Dict[str, Any]:
        return self._request({"op": "ping"})

    def still(
        self,
        spec: Dict[str, Any],
        out: Path,
        frame: Optional[int] = None,
        frame_pct: Optional[float] = None,
        scale: float = 1.0,
    ) -> Dict[str, Any]:
        """Render one frame of a full VideoSpec.

        `frame_pct` is resolved server-side against the composition's real
        duration, because the caller does not know it: durationInFrames comes from
        calculateMetadata after transitions shorten the timeline.
        """
        payload: Dict[str, Any] = {
            "op": "still",
            "spec": spec,
            "out": str(out),
            "scale": scale,
        }
        if frame is not None:
            payload["frame"] = frame
        elif frame_pct is not None:
            # Resolved server-side against the real composition duration.
            payload["frame_pct"] = frame_pct
        return self._request(payload)

    def clip(
        self,
        spec: Dict[str, Any],
        out: Path,
        frm: int = 0,
        to: Optional[int] = None,
        scale: float = 0.5,
        crf: int = 26,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "op": "clip",
            "spec": spec,
            "out": str(out),
            "from": frm,
            "scale": scale,
            "crf": crf,
        }
        if to is not None:
            payload["to"] = to
        return self._request(payload)

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "running": self._alive(),
            "uptime_sec": round(time.time() - self.started_at, 1) if self.started_at else None,
            "last_error": self.last_error,
        }


# One client per panel process. Building a second would bundle twice and double
# the memory for no gain.
_client: Optional[RenderClient] = None
_client_lock = threading.Lock()


def get_client() -> RenderClient:
    global _client
    with _client_lock:
        if _client is None:
            _client = RenderClient()
        return _client


def shutdown() -> None:
    global _client
    with _client_lock:
        if _client is not None:
            _client.stop()
            _client = None
