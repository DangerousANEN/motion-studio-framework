import sys, json, time, subprocess
sys.path.insert(0, r"C:\Users\ANEN\motion-studio-framework")
from msf.graph.video_graph import build_msf_graph

OUT = r"C:\Users\ANEN\motion-studio-framework\output\v3_final.mp4"

app = build_msf_graph()
t0 = time.time()
result = app.invoke({
    # Multi-sentence -> exercises multi-scene split, per-scene audio,
    # frame diversity check, and duration accumulation.
    "text": "Канал ЛЛМ Хабс. Топовые нейросети и открытый исходный код. "
            "Рендер идёт локально в шестьдесят кадров в секунду. "
            "Озвучка клонируется моделью Qwen три. Без облака и без подписок.",
    "preset": "HeroKinetic",
    "accent": "gold",
    "agent_level": 1,
    "reference_audio": r"C:\Users\ANEN\qwen3_1.7B_clone_test.wav",
    "output_path": OUT,
})
print(f"=== GRAPH FINISHED in {time.time()-t0:.0f}s ===", flush=True)
print("final_mp4 :", result.get("final_mp4"))
print("qa_passed :", result.get("qa_passed"))
print("retry_cnt :", result.get("retry_count"))
spec = result.get("spec_dict", {})
print("fps       :", spec.get("fps"))
print("scenes    :", len(spec.get("scenes", [])))
for i, sc in enumerate(spec.get("scenes", [])):
    print(f"  [{i}] {sc.get('durationInFrames')}f audio={sc.get('audioUrl')} text={(sc.get('text') or '')[:45]!r}")
print("--- QA REPORT ---")
print(json.dumps(result.get("qa_report", {}), ensure_ascii=False, indent=1)[:1800])

# Independent verification straight from the artifact
f = result.get("final_mp4")
probe = subprocess.run(["ffprobe","-v","error","-show_entries",
    "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
    "-show_entries","format=duration,size","-of","default=noprint_wrappers=1",f],
    capture_output=True, text=True).stdout
print("--- FFPROBE ---"); print(probe.strip())
vol = subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",f,"-af","volumedetect","-f","null","-"],
    capture_output=True, text=True).stderr
print("--- LOUDNESS ---")
print("\n".join(l for l in vol.splitlines() if "mean_volume" in l or "max_volume" in l))
print("=== DONE_MARKER ===", flush=True)
