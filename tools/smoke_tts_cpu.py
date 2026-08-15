from __future__ import annotations

from pathlib import Path

from msf.skills_bridge.qwen3_tts import synthesize_voice_clone

OUT = Path("/tmp/msf_tts_cpu_smoke.wav")


def main() -> int:
    path, duration = synthesize_voice_clone(
        text="Это короткая проверка локальной озвучки MSF Studio.",
        voice="msf_narrator_recovered",
        output_path=str(OUT),
        max_new_tokens=512,
    )
    result = Path(path)
    if not result.is_file() or result.stat().st_size < 1000:
        raise RuntimeError("TTS did not create a usable WAV")
    print(f"output={result}")
    print(f"bytes={result.stat().st_size}")
    print(f"duration_sec={duration:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
