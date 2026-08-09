import sys, json, os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_v4_showcase import STORYBOARD
from msf.graph.video_graph import node_script_split, node_build_remotion_spec
from msf.orchestrators.remotion_runner import render_remotion_video, _synthesize_cloned_audio
from msf.skills_bridge.qwen3_tts import resolve_voice

def main():
    PUBLIC = ROOT / "remotion" / "public"
    PUBLIC.mkdir(parents=True, exist_ok=True)
    OUT_DIR = ROOT / "output"
    OUT_DIR.mkdir(exist_ok=True)
    audio_dir = OUT_DIR / "audio_voice2"
    audio_dir.mkdir(exist_ok=True)

    st = {"storyboard": STORYBOARD, "preset":"HeroKinetic", "accent":"gold", "agent_level":5, "video_format":"vertical"}
    st = node_script_split(st)

    ref_audio, ref_text = resolve_voice("voice_2")
    print(f"[voice_2] Synthesizing audio for {len(st['scenes'])} scenes...", flush=True)

    audio_files = []
    for i, sc in enumerate(st["scenes"]):
        print(f"Synthesizing scene {i:02d}/{len(st['scenes'])}...", flush=True)
        wav_path, dur = _synthesize_cloned_audio(sc["text"], ref_audio, ref_text)
        sc_wav = audio_dir / f"scene_{i:02d}.wav"
        shutil.copy(wav_path, str(sc_wav))
        pub_wav = PUBLIC / f"scene_{i:02d}.wav"
        shutil.copy(str(sc_wav), str(pub_wav))
        
        dur_frames = int(max(90, (dur + 0.3) * 60))
        sc["duration_in_frames"] = dur_frames
        audio_files.append(str(sc_wav))

    st = node_build_remotion_spec(st)
    spec = st["spec_dict"]

    raw_mp4 = str(OUT_DIR / "v4_voice2_raw.mp4")
    final_mp4 = str(OUT_DIR / "v4_voice2.mp4")

    print("[render] Starting Remotion render with voice_2...", flush=True)
    render_remotion_video(spec, raw_mp4)
    print(f"[render] Raw MP4 created: {raw_mp4}", flush=True)

    audio_list_path = OUT_DIR / "audio_voice2_list.txt"
    with open(audio_list_path, "w") as f:
        for fpath in audio_files:
            fpath_clean = str(fpath).replace("\\", "/")
            f.write(f"file '{fpath_clean}'\n")

    merged_wav = str(OUT_DIR / "merged_voice2_audio.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list_path), "-c", "pcm_s16le", merged_wav], check=True)

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
        print("ERR:", res.stderr, flush=True)
    else:
        print(f"SUCCESS! Created {final_mp4}", flush=True)

if __name__ == "__main__":
    main()
