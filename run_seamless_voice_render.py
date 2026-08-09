import sys, json, os, shutil, subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_v4_showcase import STORYBOARD
from msf.graph.video_graph import node_script_split, node_build_remotion_spec
from msf.orchestrators.remotion_runner import render_remotion_video, _synthesize_cloned_audio
from msf.skills_bridge.qwen3_tts import resolve_voice

def render_for_voice(voice_name: str, out_name: str):
    print(f"\n========================================================")
    print(f"       STARTING SEAMLESS RENDER FOR {voice_name}")
    print(f"========================================================")

    PUBLIC = ROOT / "remotion" / "public"
    PUBLIC.mkdir(parents=True, exist_ok=True)
    OUT_DIR = ROOT / "output"
    OUT_DIR.mkdir(exist_ok=True)
    audio_dir = OUT_DIR / f"audio_{voice_name}"
    audio_dir.mkdir(exist_ok=True)

    st = {"storyboard": STORYBOARD, "preset":"HeroKinetic", "accent":"gold", "agent_level":5, "video_format":"vertical"}
    st = node_script_split(st)

    ref_audio, ref_text = resolve_voice(voice_name)
    print(f"[{voice_name}] Synthesizing audio for {len(st['scenes'])} scenes with lexicon accent fixes...")

    processed_audio_files = []
    for i, sc in enumerate(st["scenes"]):
        print(f"Synthesizing scene {i:02d}/{len(st['scenes'])}...", flush=True)
        raw_wav_path, dur = _synthesize_cloned_audio(sc["text"], ref_audio, ref_text)
        
        # Apply seamless fade-in/out and micro-silence padding via ffmpeg
        sc_wav = audio_dir / f"scene_{i:02d}.wav"
        pad_wav = audio_dir / f"scene_{i:02d}_padded.wav"

        # Read audio to get exact duration
        x, sr = sf.read(raw_wav_path)
        actual_dur = len(x) / sr
        fade_out_start = max(0.01, actual_dur - 0.08)

        # Process with ffmpeg: fade in 40ms, fade out 80ms, pad with 120ms silence
        filter_str = f"afade=t=in:ss=0:d=0.04,afade=t=out:st={fade_out_start:.3f}:d=0.08,apad=pad_dur=0.12"
        cmd = [
            "ffmpeg", "-y", "-i", raw_wav_path,
            "-af", filter_str,
            "-ar", "24000", "-ac", "1",
            str(sc_wav)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        # Copy padded audio to public dir for Remotion
        pub_wav = PUBLIC / f"scene_{i:02d}.wav"
        shutil.copy(str(sc_wav), str(pub_wav))

        # Calculate exact duration in frames (24000 Hz padded audio)
        padded_info = sf.info(str(sc_wav))
        dur_frames = int(np.ceil(padded_info.duration * 60))
        sc["duration_in_frames"] = dur_frames
        processed_audio_files.append(str(sc_wav))

    st = node_build_remotion_spec(st)
    spec = st["spec_dict"]

    raw_mp4 = str(OUT_DIR / f"{out_name}_raw.mp4")
    final_mp4 = str(OUT_DIR / f"{out_name}.mp4")

    print(f"[{voice_name}] Starting Remotion render...", flush=True)
    render_remotion_video(spec, raw_mp4)
    print(f"[{voice_name}] Raw MP4 created: {raw_mp4}", flush=True)

    audio_list_path = OUT_DIR / f"audio_list_{voice_name}.txt"
    with open(audio_list_path, "w") as f:
        for fpath in processed_audio_files:
            fpath_clean = str(fpath).replace("\\", "/")
            f.write(f"file '{fpath_clean}'\n")

    merged_wav = str(OUT_DIR / f"merged_audio_{voice_name}.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list_path), "-c", "pcm_s16le", merged_wav], check=True, capture_output=True)

    # Master and mux audio seamlessly
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_mp4,
        "-i", merged_wav,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5,aresample=48000",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        final_mp4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[{voice_name}] ERR:", res.stderr, flush=True)
    else:
        print(f"[{voice_name}] SUCCESS! Created {final_mp4}", flush=True)

if __name__ == "__main__":
    voice = sys.argv[1] if len(sys.argv) > 1 else "voice_2"
    out = sys.argv[2] if len(sys.argv) > 2 else "video_voice_2"
    render_for_voice(voice, out)
