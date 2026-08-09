"""MSF LangGraph StateGraph Orchestrator (v3.0).

Provides a structured, state-driven multi-agent workflow for generating
remotion-based videos with fail-closed QA and self-correction repair loop.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from msf.spec import Scene, build_spec, frames_for, validate_spec, FPS, WIDTH, HEIGHT
from msf.orchestrators.remotion_runner import (
    _split_into_scenes,
    _synthesize_cloned_audio,
    render_remotion_video,
)
from msf.engines.audio.mastering import master_video_audio

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = REPO_ROOT / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"
DEFAULT_OUTPUT = REPO_ROOT / "output" / "remotion"

# Presets a low-capability agent may request. Must stay in sync with
# SAFE_PRESETS in remotion/src/VideoSpec.schema.ts.
ALLOWED_PRESETS = {
    # 2D
    "HeroKinetic",
    "StatCounter",
    "GridGridFloor",
    "SwipePanels",
    "TypewriterSub",
    "CompareSplit",
    "FlowDiagram",
    "CodeReveal",
    "QuoteCard",
    # 3D
    "TokenCloud3D",
    "LayerStack3D",
}


class VideoState(TypedDict, total=False):
    text: str
    storyboard: Optional[List[Dict[str, Any]]]
    preset: str
    accent: Optional[str]
    reference_audio: Optional[str]
    voice: Optional[str]
    video_format: Optional[str]
    theme: Optional[str]
    agent_level: Optional[int]
    output_path: Optional[str]
    scenes: Optional[List[Dict[str, Any]]]
    audio_paths: Optional[List[str]]
    spec_path: Optional[str]
    spec_dict: Optional[Dict[str, Any]]
    raw_mp4: Optional[str]
    final_mp4: Optional[str]
    retry_count: int
    qa_passed: bool
    qa_report: Optional[Dict[str, Any]]
    error: Optional[str]


def node_gate_check(state: VideoState) -> VideoState:
    """Check agent level and validate allowed capabilities."""
    level = state.get("agent_level", 1)
    preset = state.get("preset", "HeroKinetic")

    state["retry_count"] = state.get("retry_count", 0)

    if level <= 2 and preset not in ALLOWED_PRESETS:
        state["preset"] = "HeroKinetic"
        state["error"] = (
            f"Agent level={level} attempted unsupported preset ({preset}). Fallback to HeroKinetic."
        )

    return state


def node_script_split(state: VideoState) -> VideoState:
    """Split text into sentence-sized scenes, or accept a hand-authored storyboard.

    When the caller supplies `storyboard` (a list of scene dicts), it wins: this is
    how presets that need structured data (StatCounter's statValue, SwipePanels'
    cards) get driven, since plain narration can't express them. Each storyboard
    entry still needs a `text` field — that's what gets voiced.
    """
    storyboard = state.get("storyboard")
    if storyboard:
        scenes = [dict(sc) for sc in storyboard]
        for i, sc in enumerate(scenes):
            if not sc.get("text"):
                raise ValueError(
                    f"storyboard[{i}] has no 'text' — every scene needs narration to voice."
                )
        state["scenes"] = scenes
        return state

    state["scenes"] = _split_into_scenes(state.get("text", ""))
    return state


# Rotating presets for multi-scene videos. StatCounter and SwipePanels need
# structured data (statValue/cards) that plain narration text doesn't provide, so
# they are excluded from automatic rotation — they'd render their ⚠ placeholder.
_TEXT_SAFE_PRESETS = ["HeroKinetic", "TypewriterSub", "GridGridFloor"]


def _rotated_preset(base: str, index: int) -> str:
    """Vary the visual template across scenes so a long short isn't one static card.

    The requested preset always leads scene 0; later scenes cycle through the
    text-safe presets (which accept plain narration) to keep the video moving.
    """
    if base in _TEXT_SAFE_PRESETS:
        cycle = [base] + [p for p in _TEXT_SAFE_PRESETS if p != base]
        return cycle[index % len(cycle)]
    return base


def node_voice_synthesis(state: VideoState) -> VideoState:
    """Synthesize voice cloning for all scenes using Qwen3 1.7B-Base.

    Voice selection goes through the registry (`voice` key or wav path) so the
    transcript travels with the audio and ICL prosody transfer stays on. An
    explicit `reference_audio` path still wins for one-off overrides.
    """
    from msf.skills_bridge.qwen3_tts import describe_reference, resolve_voice

    override = state.get("reference_audio")
    ref_audio, ref_text = resolve_voice(override or state.get("voice"))
    ref_info = describe_reference(override or state.get("voice"))
    print(f"[voice] {ref_info['mode']} ref={Path(ref_audio).name} "
          f"dur={ref_info['duration_sec']}s sr={ref_info['sample_rate']}")
    if ref_text is None:
        print("[voice] WARNING: no transcript for this reference — "
              "falling back to x-vector timbre copy without prosody transfer.")

    scenes = state.get("scenes", [])
    audio_paths = []

    output_dir = (
        Path(state["output_path"]).parent
        if state.get("output_path")
        else DEFAULT_OUTPUT
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    base_preset = state.get("preset", "HeroKinetic")

    for i, sc in enumerate(scenes):
        wav_path, dur = _synthesize_cloned_audio(sc["text"], ref_audio, ref_text)
        scene_wav_name = f"scene_{i:02d}.wav"
        dst_wav = audio_dir / scene_wav_name
        shutil.copy(wav_path, str(dst_wav))

        # Copy into Remotion public directory
        pub_wav = PUBLIC_DIR / scene_wav_name
        shutil.copy(str(dst_wav), str(pub_wav))

        audio_paths.append(str(dst_wav))
        sc["duration_in_frames"] = frames_for(dur, FPS)
        sc["audio_file"] = scene_wav_name
        # A storyboard scene names its own preset; only auto-rotate when it didn't.
        if not sc.get("preset"):
            sc["preset"] = _rotated_preset(base_preset, i)
        sc["accent"] = state.get("accent", "gold")

    state["audio_paths"] = audio_paths
    return state


def node_build_remotion_spec(state: VideoState) -> VideoState:
    """Generate VideoSpec via single source of truth msf.spec."""
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    accent_color = "#E6C475" if state.get("accent") == "gold" else (state.get("accent") or "#E6C475")

    # Copy every field the Scene dataclass knows about, so adding a preset field
    # in msf/spec.py is enough — no parallel edit needed here.
    scene_fields = {f.name for f in dataclasses.fields(Scene)}

    scenes_objs: List[Scene] = []
    for i, sc in enumerate(state.get("scenes", [])):
        audio_name = f"scene_{i:02d}.wav"
        kwargs = {k: v for k, v in sc.items() if k in scene_fields and v is not None}
        kwargs.update(
            id=sc.get("id", f"scene-{i+1}"),
            duration_in_frames=sc.get("duration_in_frames", 90),
            preset=sc.get("preset", state.get("preset", "HeroKinetic")),
            accent_color=sc.get("accent_color") or accent_color,
            audio_url=audio_name,
        )
        scenes_objs.append(Scene(**kwargs))

    spec_dict = build_spec(
        scenes_objs,
        fps=FPS,
        video_format=state.get("video_format"),
        theme=state.get("theme"),
    )

    # Fail fast at the graph level too: never persist or render an unusable spec.
    validate_spec(spec_dict)

    state["spec_dict"] = spec_dict

    spec_path = PUBLIC_DIR / "video-spec.json"
    props_path = PUBLIC_DIR / "props.json"
    json_str = json.dumps(spec_dict, ensure_ascii=False, indent=2)
    spec_path.write_text(json_str, encoding="utf-8")
    props_path.write_text(json_str, encoding="utf-8")

    state["spec_path"] = str(spec_path)
    return state


def _resolve_output_paths(state: VideoState) -> tuple[str, str]:
    """Return (raw_mp4, final_mp4) — always DISTINCT paths.

    ffmpeg cannot edit a file in place, so the mastering step must never be handed
    the same path for input and output. The raw render always gets a `.raw.mp4`
    suffix; `output_path` (when supplied) names the FINAL mastered artifact.
    """
    out_param = state.get("output_path")
    preset_name = (state.get("preset") or "HeroKinetic").lower()

    if out_param:
        final_path = Path(out_param)
        out_dir = final_path.parent
    else:
        out_dir = DEFAULT_OUTPUT
        final_path = out_dir / f"msf_{preset_name}.mp4"

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = final_path.with_suffix(".raw.mp4")
    return str(raw_path), str(final_path)


def node_remotion_render(state: VideoState) -> VideoState:
    """Invoke Remotion render via remotion_runner."""
    raw_mp4, _ = _resolve_output_paths(state)

    render_remotion_video(state["spec_dict"], raw_mp4)
    state["raw_mp4"] = raw_mp4
    return state


def node_master_audio(state: VideoState) -> VideoState:
    """Master output video audio using loudnorm."""
    raw_mp4, final_mp4 = _resolve_output_paths(state)

    if Path(raw_mp4).resolve() == Path(final_mp4).resolve():
        raise RuntimeError(
            f"Refusing to master in place: raw and final paths are identical ({final_mp4})."
        )

    master_video_audio(state.get("raw_mp4") or raw_mp4, final_mp4)
    state["final_mp4"] = final_mp4
    return state


def _check_mp4_size(mp4_path: str) -> tuple[bool, int]:
    p = Path(mp4_path)
    if not p.exists():
        return False, 0
    size = p.stat().st_size
    return size > 100 * 1024, size


def _check_duration(mp4_path: str, expected_sec: float) -> tuple[bool, float]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        mp4_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if res.returncode != 0 or not res.stdout.strip():
        return False, 0.0
    actual_sec = float(res.stdout.strip())
    diff = abs(actual_sec - expected_sec)
    passed = diff <= (0.15 * expected_sec) if expected_sec > 0 else False
    return passed, actual_sec


def _check_volume(mp4_path: str) -> tuple[bool, float]:
    devnull = "NUL" if os.name == "nt" else "/dev/null"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        mp4_path,
        "-af",
        "volumedetect",
        "-vn",
        "-sn",
        "-dn",
        "-f",
        "null",
        devnull,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    match = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", res.stderr)
    if match:
        vol = float(match.group(1))
        return vol > -50.0, vol
    return False, -99.0


def _get_frame_stddev(image_path: str) -> float:
    try:
        from PIL import Image, ImageStat
        with Image.open(image_path) as img:
            gray = img.convert("L").resize((108, 192))
            stat = ImageStat.Stat(gray)
            return float(stat.stddev[0])
    except Exception:
        cmd = ["ffmpeg", "-i", image_path, "-vf", "signalstats", "-f", "null", "-"]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        match = re.search(r"YSTD=([\d.]+)", res.stderr)
        if match:
            return float(match.group(1))
        return 0.0


def _extract_midpoint_frames(
    mp4_path: str, spec_dict: dict, out_dir: Path
) -> tuple[list[str], list[float]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes = spec_dict.get("scenes", [])

    frame_paths = []
    stddevs = []

    cumulative_frames = 0
    for idx, sc in enumerate(scenes):
        dur_frames = sc.get("durationInFrames", 90)
        mid_frame = cumulative_frames + (dur_frames // 2)
        cumulative_frames += dur_frames

        frame_file = out_dir / f"scene_{idx:02d}_mid.png"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            mp4_path,
            "-vf",
            f"select='eq(n\\,{mid_frame})'",
            "-vframes",
            "1",
            str(frame_file),
        ]
        subprocess.run(cmd, capture_output=True, text=True, errors="replace")

        if frame_file.exists():
            frame_paths.append(str(frame_file))
            sd = _get_frame_stddev(str(frame_file))
            stddevs.append(sd)

    return frame_paths, stddevs


def node_qa(state: VideoState) -> VideoState:
    """Fail-closed QA node checking size, duration, audio volume, midpoint frames, and diversity."""
    report: Dict[str, Any] = {}
    try:
        mp4_path = state.get("final_mp4") or state.get("raw_mp4")
        if not mp4_path:
            state["qa_passed"] = False
            state["qa_report"] = {"error": "No output mp4 path found"}
            return state

        # 1. Size check (> 100 KB)
        size_pass, size_bytes = _check_mp4_size(mp4_path)
        report["check_1_size"] = {"pass": size_pass, "bytes": size_bytes}

        # 2. Duration check
        spec_dict = state.get("spec_dict", {})
        fps = spec_dict.get("fps", FPS)
        scenes = spec_dict.get("scenes", [])
        # Transitions overlap, so the video is shorter than the sum. Use the
        # same logic spec.py uses to set durationInFrames, or this check will
        # fail on every video that has crossfades.
        from msf.spec import compute_total_frames
        expected_frames = compute_total_frames(scenes)
        expected_sec = expected_frames / fps
        dur_pass, actual_sec = _check_duration(mp4_path, expected_sec)
        report["check_2_duration"] = {
            "pass": dur_pass,
            "actual_sec": actual_sec,
            "expected_sec": expected_sec,
        }

        # 3. Volume check (> -50 dB)
        vol_pass, mean_vol = _check_volume(mp4_path)
        report["check_3_volume"] = {"pass": vol_pass, "mean_volume_db": mean_vol}

        # 4 & 5. Frame luminance check (stddev >= 3)
        qa_frames_dir = Path(mp4_path).parent / "qa_frames"
        frame_paths, stddevs = _extract_midpoint_frames(mp4_path, spec_dict, qa_frames_dir)
        lum_pass = len(stddevs) > 0 and all(sd >= 3.0 for sd in stddevs)
        report["check_4_5_luminance"] = {
            "pass": lum_pass,
            "stddevs": stddevs,
            "frame_paths": frame_paths,
        }

        # 6. Diversity check if > 1 scene
        if len(frame_paths) > 1:
            hashes = [
                hashlib.md5(Path(p).read_bytes()).hexdigest()
                for p in frame_paths
                if Path(p).exists()
            ]
            div_pass = len(set(hashes)) > 1
        else:
            div_pass = True
        report["check_6_diversity"] = {"pass": div_pass}

        all_passed = size_pass and dur_pass and vol_pass and lum_pass and div_pass
        report["all_passed"] = all_passed
        state["qa_passed"] = all_passed
        state["qa_report"] = report

    except Exception as exc:
        report["all_passed"] = False
        report["exception"] = str(exc)
        state["qa_passed"] = False
        state["qa_report"] = report

    return state


def node_repair(state: VideoState) -> VideoState:
    """Self-correction repair node. Modifies spec/assets based on failure reason."""
    retry_count = state.get("retry_count", 0)
    report = state.get("qa_report") or {}

    if retry_count >= 2:
        raise RuntimeError(
            f"Video QA failed after 2 repairs. Pipeline failed closed.\n"
            f"QA Report: {json.dumps(report, indent=2, ensure_ascii=False)}"
        )

    remotion_public = PUBLIC_DIR
    remotion_public.mkdir(parents=True, exist_ok=True)
    audio_paths = state.get("audio_paths") or []

    # 1. If audio failure: re-copy wavs into remotion/public
    vol_check = report.get("check_3_volume", {})
    if not vol_check.get("pass", True):
        for audio_path in audio_paths:
            if os.path.exists(audio_path):
                shutil.copy(audio_path, remotion_public / Path(audio_path).name)

    # 2. If blank frames or non-diverse: fall back to a preset that can render the
    #    scene's own data. StatCounter/SwipePanels scenes carry structured fields
    #    (statValue/cards) that HeroKinetic cannot show, so only text-driven scenes
    #    are downgraded — otherwise the repair would destroy the storyboard.
    lum_check = report.get("check_4_5_luminance", {})
    div_check = report.get("check_6_diversity", {})
    if not lum_check.get("pass", True) or not div_check.get("pass", True):
        scenes = state.get("scenes") or []
        for sc in scenes:
            if sc.get("stat_value") is not None or sc.get("cards"):
                continue
            sc["preset"] = "HeroKinetic"

    # 3. If duration mismatch: recompute duration from actual wav files
    dur_check = report.get("check_2_duration", {})
    if not dur_check.get("pass", True):
        scenes = state.get("scenes") or []
        for i, sc in enumerate(scenes):
            if i < len(audio_paths) and os.path.exists(audio_paths[i]):
                cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    audio_paths[i],
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                if res.returncode == 0 and res.stdout.strip():
                    dur = float(res.stdout.strip())
                    sc["duration_in_frames"] = frames_for(dur, FPS)

    state["retry_count"] = retry_count + 1

    # Rebuild spec_dict with updated scene properties, preserving every field the
    # Scene dataclass knows about (3D layers, code, quote attribution, ...).
    scene_fields = {f.name for f in dataclasses.fields(Scene)}
    scenes_objs: List[Scene] = []
    accent_color = "#E6C475" if state.get("accent") == "gold" else (state.get("accent") or "#E6C475")
    for i, sc in enumerate(state.get("scenes", [])):
        audio_name = f"scene_{i:02d}.wav"
        kwargs = {k: v for k, v in sc.items() if k in scene_fields and v is not None}
        kwargs.update(
            id=sc.get("id", f"scene-{i+1}"),
            duration_in_frames=sc.get("duration_in_frames", 90),
            preset=sc.get("preset", "HeroKinetic"),
            accent_color=sc.get("accent_color") or accent_color,
            audio_url=audio_name,
        )
        scenes_objs.append(Scene(**kwargs))

    spec_dict = build_spec(
        scenes_objs,
        fps=FPS,
        video_format=state.get("video_format"),
        theme=state.get("theme"),
    )
    state["spec_dict"] = spec_dict

    props_path = remotion_public / "props.json"
    spec_json_path = remotion_public / "video-spec.json"
    json_str = json.dumps(spec_dict, ensure_ascii=False, indent=2)
    props_path.write_text(json_str, encoding="utf-8")
    spec_json_path.write_text(json_str, encoding="utf-8")

    return state


def check_qa_decision(state: VideoState) -> str:
    """Conditional Edge: proceed to END if QA passed, else retry repair."""
    if state.get("qa_passed") is True:
        return "end"
    return "repair"


def build_msf_graph():
    """Build and compile the MSF LangGraph workflow with Vision QA loop."""
    workflow = StateGraph(VideoState)

    workflow.add_node("gate_check", node_gate_check)
    workflow.add_node("script_split", node_script_split)
    workflow.add_node("voice_synthesis", node_voice_synthesis)
    workflow.add_node("build_spec", node_build_remotion_spec)
    workflow.add_node("render", node_remotion_render)
    workflow.add_node("master_audio", node_master_audio)
    workflow.add_node("qa", node_qa)
    workflow.add_node("repair", node_repair)

    workflow.set_entry_point("gate_check")
    workflow.add_edge("gate_check", "script_split")
    workflow.add_edge("script_split", "voice_synthesis")
    workflow.add_edge("voice_synthesis", "build_spec")
    workflow.add_edge("build_spec", "render")
    workflow.add_edge("render", "master_audio")
    workflow.add_edge("master_audio", "qa")

    workflow.add_conditional_edges(
        "qa",
        check_qa_decision,
        {
            "repair": "repair",
            "end": END,
        },
    )

    workflow.add_edge("repair", "render")

    return workflow.compile()


if __name__ == "__main__":
    app = build_msf_graph()
    print("✅ LangGraph MSF Workflow (v3.0 with fail-closed QA & Self-Correction) compiled successfully!")
