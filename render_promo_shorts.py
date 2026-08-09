import sys, json, os, shutil, subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from msf.graph.video_graph import node_script_split, node_build_remotion_spec
from msf.orchestrators.remotion_runner import render_remotion_video, _synthesize_cloned_audio
from msf.skills_bridge.qwen3_tts import resolve_voice

PROMO_SCENARIOS = {
    "promo_v1_local_llm": {
        "voice": "voice_3",
        "accent": "gold",
        "storyboard": [
            {
                "preset": "HeroKinetic",
                "text": "Запустить мощную модель на семьдесят миллиардов параметров на домашней видеокарте — теперь реально.",
                "title": "70B МОДЕЛЬ НА ОДНОЙ КАРТЕ?",
                "subtitle": "Локальный инференс без облаков"
            },
            {
                "preset": "LayerStack3D",
                "text": "Секрет в квантовании весов и новой архитектуре оптимизации кэша внимания.",
                "title": "КВАНТОВАНИЕ И КЭШ",
                "subtitle": "Оптимизация слоев внимания",
                "layers": ["Attention Cache", "Quantized Weights", "CUDA Core"]
            },
            {
                "preset": "StatCounter",
                "text": "Потребление видеопамяти снижается почти в четыре раза без потери логики рассуждений.",
                "stat_value": 6.8,
                "stat_suffix": " GB",
                "stat_label": "Потребление VRAM вместо 24 GB",
                "title": "СНИЖЕНИЕ VRAM"
            },
            {
                "preset": "CodeReveal",
                "text": "Все настраивается одной командой прямо на твоем компьютере.",
                "title": "ОДНА КОМАНДА ДЛЯ ЗАПУСКА",
                "code": "llama-server --model llama3-70b-q4.gguf --ctx-size 8192 --n-gpu-layers 99",
                "language": "bash"
            },
            {
                "preset": "QuoteCard",
                "text": "Подробный гайд и готовые конфиги запуска выложили в канале элэлэм Хабс. Ссылка в шапке профиля!",
                "author": "@llm_hubs",
                "role": "Telegram Канал"
            }
        ]
    },
    "promo_v2_ai_agents": {
        "voice": "voice_2",
        "accent": "cyan",
        "storyboard": [
            {
                "preset": "HeroKinetic",
                "text": "Программисты больше не пишут бойлерплейт руками. Встречайте эпоху мульти-агентных систем.",
                "title": "АГЕНТЫ ВМЕСТО ПРОГРАММИСТОВ",
                "subtitle": "Эпоха автономных систем"
            },
            {
                "preset": "FlowDiagram",
                "text": "Один промпт запускает связку из трех агентов: архитектора, кодера и валидатора тестов.",
                "title": "МУЛЬТИ-АГЕНТНЫЙ ПАЙПЛАЙН",
                "nodes": [
                    {"label": "Промпт", "sub": "Одна задача"},
                    {"label": "Архитектор", "sub": "План и структура"},
                    {"label": "Кодер", "sub": "Пишет модули"},
                    {"label": "Валидатор", "sub": "Гоняет тесты"}
                ]
            },
            {
                "preset": "TokenCloud3D",
                "text": "Агенты взаимодействуют через контекст и исправляют ошибки еще до первого запуска.",
                "title": "ВЕКТОРНЫЙ КОНТЕКСТ",
                "subtitle": "Авто-исправление ошибок",
                "point_count": 180
            },
            {
                "preset": "CompareSplit",
                "text": "То, на что раньше уходил целый рабочий день, теперь собирается за четыре минуты.",
                "title": "ЭКОНОМИЯ ВРЕМЕНИ",
                "cards": [
                    {"title": "10 часов", "description": "Ручная разработка модуля", "tag": "БЫЛО"},
                    {"title": "4 минуты", "description": "Связка агентов под ключ", "tag": "СТАЛО"}
                ]
            },
            {
                "preset": "SwipePanels",
                "text": "Лучшие шаблоны связок агентов и свежие репозитории разбираем в элэлэм Хабс. Подписывайся!",
                "title": "ПОДПИСЫВАЙСЯ НА @LLM_HUBS",
                "subtitle": "Шаблоны и исходники внутри",
                "cards": [
                    {"title": "Шаблоны агентов", "description": "Готовые связки под задачи", "tag": "01"},
                    {"title": "Исходники промптов", "description": "Копируй и запускай", "tag": "02"},
                    {"title": "@llm_hubs", "description": "Подписывайся на канал", "tag": "03"}
                ]
            }
        ]
    },
    "promo_v3_opensource": {
        "voice": "voice_3",
        "accent": "green",
        "storyboard": [
            {
                "preset": "HeroKinetic",
                "text": "Платить двадцать долларов за закрытые нейросети больше нет никакого смысла.",
                "title": "ХВАТИТ ПЛАТИТЬ ЗА ПОДПИСКИ",
                "subtitle": "Open-Source стал сильнее"
            },
            {
                "preset": "CompareSplit",
                "text": "Открытые модели нового поколения сравнялись с флагманами в кодинге и аналитике.",
                "title": "СРАВНЕНИЕ ЭФФЕКТИВНОСТИ",
                "cards": [
                    {"title": "$20 в месяц", "description": "Закрытое API, лимиты, данные на чужом сервере", "tag": "ПОДПИСКА"},
                    {"title": "0 рублей", "description": "Веса у тебя, работает офлайн без лимитов", "tag": "ЛОКАЛЬНО"}
                ]
            },
            {
                "preset": "StatCounter",
                "text": "Полная приватность ваших данных, нулевая задержка сети и работа офлайн.",
                "stat_value": 100,
                "stat_suffix": "%",
                "stat_label": "Данные не покидают твою машину",
                "title": "ПОЛНАЯ БЕЗОПАСНОСТЬ"
            },
            {
                "preset": "LayerStack3D",
                "text": "Вы получаете полный контроль над весами и можете файнтюнить модель под любые задачи.",
                "title": "ФАЙНТЮН ПОД СЕБЯ",
                "layers": ["Fine-Tuning", "Base Model Weights", "Local GPU Memory"]
            },
            {
                "preset": "QuoteCard",
                "text": "Ссылки на веса и пошаговые инструкции уже ждут тебя в элэлэм Хабс. Заходи по ссылке!",
                "author": "@llm_hubs",
                "role": "Канал о Локальном ИИ"
            }
        ]
    },
    "promo_v4_rust_inference": {
        "voice": "voice_2",
        "accent": "gold",
        "storyboard": [
            {
                "preset": "HeroKinetic",
                "text": "Медленный инференс съедает ресурсы твоего сервера? Пора переписать пайплайн.",
                "title": "PYTHON СЛИШКОМ МЕДЛЕННЫЙ?",
                "subtitle": "Ускорение инференса в 5 раз"
            },
            {
                "preset": "CodeReveal",
                "text": "Перенос движка на чистый Раст или Си-плюс-плюс снижает задержку с двухсот миллисекунд до пятнадцати.",
                "title": "БЫСТРЫЙ ДВИЖОК НА RUST",
                "code": "pub fn infer_fast(ctx: &Context, tensor: &Tensor) -> Result<Token> {\n    unsafe { tensor.matmul_cuda_stream(ctx.stream()) }\n}",
                "language": "rust"
            },
            {
                "preset": "TokenCloud3D",
                "text": "Максимальный упор на векторные инструкции процессора и параллельные ядра видеокарты.",
                "title": "АППАРАТНОЕ УСКОРЕНИЕ",
                "point_count": 220
            },
            {
                "preset": "StatCounter",
                "text": "Сервер выдерживает в пять раз больше параллельных пользователей при меньших затратах.",
                "stat_value": 15,
                "stat_suffix": " ms",
                "stat_label": "Задержка вместо 200 ms",
                "title": "ПРИРОСТ СКОРОСТИ"
            },
            {
                "preset": "SwipePanels",
                "text": "Исходники быстрых движков и бенчмарки выкладываем в элэлэм Хабс. Жми подписку!",
                "title": "ПОДПИШИСЬ НА @LLM_HUBS",
                "subtitle": "Код и бенчмарки внутри",
                "cards": [
                    {"title": "Быстрый движок", "description": "Исходники инференс-ядра", "tag": "01"},
                    {"title": "Бенчмарки", "description": "Замеры latency и throughput", "tag": "02"},
                    {"title": "@llm_hubs", "description": "Жми подписку", "tag": "03"}
                ]
            }
        ]
    }
}

def render_scenario(scenario_key: str, data: dict):
    print(f"\n========================================================")
    print(f"       STARTING PROMO RENDER FOR {scenario_key}")
    print(f"========================================================")

    PUBLIC = ROOT / "remotion" / "public"
    PUBLIC.mkdir(parents=True, exist_ok=True)
    OUT_DIR = ROOT / "output" / "promo_shorts"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_dir = OUT_DIR / f"audio_{scenario_key}"
    audio_dir.mkdir(exist_ok=True)

    voice_name = data["voice"]
    st = {
        "storyboard": data["storyboard"],
        "preset": "HeroKinetic",
        "accent": data.get("accent", "gold"),
        "agent_level": 5,
        "video_format": "vertical"
    }
    st = node_script_split(st)

    ref_audio, ref_text = resolve_voice(voice_name)
    print(f"[{scenario_key}] Synthesizing audio with {voice_name}...")

    processed_audio_files = []
    for i, sc in enumerate(st["scenes"]):
        sc_wav = audio_dir / f"scene_{i:02d}.wav"
        if not sc_wav.exists():
            print(f"Synthesizing scene {i:02d}/{len(st['scenes'])}...", flush=True)
            raw_wav_path, dur = _synthesize_cloned_audio(sc["text"], ref_audio, ref_text)
            
            x, sr = sf.read(raw_wav_path)
            actual_dur = len(x) / sr
            fade_out_start = max(0.01, actual_dur - 0.08)

            filter_str = f"afade=t=in:ss=0:d=0.04,afade=t=out:st={fade_out_start:.3f}:d=0.08,apad=pad_dur=0.12"
            cmd = [
                "ffmpeg", "-y", "-i", raw_wav_path,
                "-af", filter_str,
                "-ar", "24000", "-ac", "1",
                str(sc_wav)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        else:
            print(f"Reusing cached audio for scene {i:02d}...")

        pub_wav = PUBLIC / f"scene_{i:02d}.wav"
        shutil.copy(str(sc_wav), str(pub_wav))

        padded_info = sf.info(str(sc_wav))
        dur_frames = int(np.ceil(padded_info.duration * 60))
        sc["duration_in_frames"] = dur_frames
        processed_audio_files.append(str(sc_wav))

    st = node_build_remotion_spec(st)
    spec = st["spec_dict"]

    # Pre-flight: run the spec through the REAL Zod schema before rendering.
    # Python's validate_spec() only checks preset names and required keys; Zod
    # additionally enforces types. Skipping this lets a bad spec render a red
    # RENDER ERROR screen that looks like a finished video.
    spec_json = OUT_DIR / f"spec_{scenario_key}.json"
    spec_json.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    check = subprocess.run(
        ["node", "validate_spec.mjs", str(spec_json)],
        cwd=str(ROOT / "remotion"),
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        raise RuntimeError(
            f"[{scenario_key}] spec rejected by Zod before render:\n"
            f"{check.stdout}\n{check.stderr}"
        )
    print(f"[{scenario_key}] Zod pre-flight OK", flush=True)

    raw_mp4 = str(OUT_DIR / f"{scenario_key}_raw.mp4")
    final_mp4 = str(OUT_DIR / f"{scenario_key}.mp4")
    tg_mp4 = str(OUT_DIR / f"{scenario_key}_tg.mp4")

    print(f"[{scenario_key}] Rendering Remotion video...", flush=True)
    render_remotion_video(spec, raw_mp4)

    # Post-flight: Remotion renders its error screen as a valid MP4, so a failed
    # render still produces a plausible-looking file. Sample a frame and reject
    # the dominant-red error screen instead of shipping it.
    probe_png = OUT_DIR / f"probe_{scenario_key}.png"
    subprocess.run(
        ["ffmpeg", "-y", "-i", raw_mp4, "-vf", "select=eq(n\\,30),scale=64:64",
         "-frames:v", "1", str(probe_png), "-loglevel", "error"],
        check=True,
    )
    # Decode the probe frame and check for the error screen's saturated red.
    raw_rgb = subprocess.run(
        ["ffmpeg", "-i", str(probe_png), "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-", "-loglevel", "error"],
        capture_output=True,
    ).stdout
    if raw_rgb:
        px = np.frombuffer(raw_rgb, dtype=np.uint8).reshape(-1, 3).astype(int)
        r, g, b = px[:, 0].mean(), px[:, 1].mean(), px[:, 2].mean()
        if r > 100 and r > g * 2.0 and r > b * 2.0:
            raise RuntimeError(
                f"[{scenario_key}] render produced Remotion's RENDER ERROR screen "
                f"(mean RGB = {r:.0f},{g:.0f},{b:.0f}). Spec/preset props are wrong."
            )
        print(f"[{scenario_key}] frame check OK (RGB {r:.0f},{g:.0f},{b:.0f})", flush=True)

    audio_list_path = OUT_DIR / f"audio_list_{scenario_key}.txt"
    with open(audio_list_path, "w") as f:
        for fpath in processed_audio_files:
            fpath_clean = str(fpath).replace("\\", "/")
            f.write(f"file '{fpath_clean}'\n")

    merged_wav = str(OUT_DIR / f"merged_{scenario_key}.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list_path), "-c", "pcm_s16le", merged_wav], check=True, capture_output=True)

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
    subprocess.run(cmd, check=True, capture_output=True)

    cmd_tg = [
        "ffmpeg", "-y", "-i", final_mp4,
        "-b:v", "800k", "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        tg_mp4
    ]
    subprocess.run(cmd_tg, check=True, capture_output=True)

    desktop_file = f"F:/ANEN/Desktop/{scenario_key}.mp4"
    shutil.copy(final_mp4, desktop_file)
    print(f"[{scenario_key}] SUCCESS! Final: {final_mp4} | Desktop: {desktop_file}", flush=True)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target and target in PROMO_SCENARIOS:
        render_scenario(target, PROMO_SCENARIOS[target])
    else:
        for k, v in PROMO_SCENARIOS.items():
            render_scenario(k, v)
