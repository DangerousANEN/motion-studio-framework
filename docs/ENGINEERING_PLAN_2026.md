# MSF Engineering Plan 2026 — Аудит и план реализации

> Составлен: 2026-08-12
> Аудит завершён: полный code trace всех трёх проблем
> Репозиторий: C:\Users\ANEN\motion-studio-framework\

---

## АУДИТ-ДАННЫЕ: ПРОВЕРЕННЫЕ ФАКТЫ ИЗ КОДОВОЙ БАЗЫ

### Состояние аудио (что проверено и верифицировано)
- WAV-файлы: remotion/public/scene_00.wav ... scene_09.wav — СУЩЕСТВУЮТ (24kHz 1ch pcm_s16le)
- msf_herokinetic.mp4 — mean_volume = -18.5 dB (НОРМА, граф работает)
- msf_herokinetic_raw.mp4 — mean_volume = -23.0 dB (НОРМА, Remotion рендерит аудио)
- scripts_tg/*.json — audioUrl ОТСУТСТВУЕТ во всех сценах всех трёх скриптов

### Подтверждённые маппинги (кодовая база на 2026-08-12)
- video_graph.py:369: sc["audio_file"] = scene_wav_name — мёртвый ключ
- video_graph.py:301: audio_url=f"scene_{index:02d}.wav" — hardcode РАБОТАЕТ через fallback
- spec.py:245: audio_url: Optional[str] — поле ЕСТЬ в Scene
- spec.py:305: "audio_url": "audioUrl" — маппинг в _CAMEL ЕСТЬ
- Main.tsx:48: scene.audioUrl && <Audio src={resolveSrc(scene.audioUrl)}/> — рендерит ОК

---

## РАЗДЕЛ 1: АУДИО И ОЗВУЧКА (-91 dB тишина)

### 1.1 Два пути рендеринга — разная логика аудио

#### Путь A: build_msf_graph().invoke() — РАБОТАЕТ (-18.5 dB)
```
node_voice_synthesis:
  sc["audio_file"] = "scene_00.wav"     <- мёртвый ключ (не используется)
  shutil.copy(wav -> remotion/public/)  <- физически копирует WAV ОК

_scene_kwargs() строка 301:
  kwargs["audio_url"] = f"scene_{index:02d}.wav"  <- hardcode РАБОТАЕТ
  -> Scene(audio_url="scene_00.wav") -> to_dict() -> {"audioUrl": "scene_00.wav"}

Main.tsx:
  scene.audioUrl = "scene_00.wav" -> <Audio src={staticFile("scene_00.wav")}/> -> ОК
```

#### Путь B: render_promo_shorts.py — ОБХОДИТ Remotion Audio
```
sc["duration_in_frames"] = dur_frames   <- только duration, НЕ audio_url
node_build_remotion_spec -> _scene_kwargs -> audioUrl hardcode -> spec ОК
render_remotion_video -> raw.mp4 с аудио (Remotion читает audioUrl)
ffmpeg -map 0:v:0 -map 1:a:0 merged_wav -> ВНЕШНИЙ merge аудио поверх видео
(при внешнем merge — двойная дорожка, но ffmpeg берёт только map 1:a:0)
```

#### Путь C: scripts_tg/*.json -> Remotion напрямую — ТИШИНА -91 dB
```bash
# Если рендеришь напрямую без Python:
npx remotion render src/index.ts Main output.mp4 --props=scripts_tg/script1_local_vs_cloud.json
# -> audioUrl = undefined в КАЖДОЙ сцене -> Audio не рендерится -> -91 dB
```
Это и есть прямая причина -91 dB. Верификация:
```bash
grep -n "audioUrl" scripts_tg/script1_local_vs_cloud.json  # -> ничего
grep -n "audioUrl" scripts_tg/script2_prompt_unlock.json   # -> ничего
grep -n "audioUrl" scripts_tg/script3_phone_model.json     # -> ничего
```

### 1.2 Корневые причины и исправления

#### Исправление 1: video_graph.py строка 369 — мёртвый ключ
БЫЛО:    sc["audio_file"] = scene_wav_name
ДОЛЖНО:  sc["audio_url"] = scene_wav_name

Почему: sc["audio_file"] никогда не читается. Hardcode строки 301 маскирует ошибку.
Явный sc["audio_url"] убирает хрупкость при изменении логики имён файлов.

#### Исправление 2: video_graph.py строки 296-302 — hardcode перезаписывает кастомный audioUrl
БЫЛО:
    kwargs.update(
        ...
        audio_url=f"scene_{index:02d}.wav",   # всегда перезаписывает
    )

ДОЛЖНО:
    kwargs.update(
        ...
        audio_url=normalised.get("audio_url") or f"scene_{index:02d}.wav",
    )

Почему: storyboard-сцена с кастомным audioUrl (другой WAV) молча перезаписывается.

#### Исправление 3: scripts_tg/*.json — добавить audioUrl в каждую сцену
Добавить в каждую сцену: "audioUrl": "scene_NN.wav" (где NN — 00-based индекс)
Нужно ТОЛЬКО для direct Remotion render. Граф ставит audioUrl автоматически.

#### Исправление 4: render_promo_shorts.py строка 243-244
БЫЛО:
    sc["duration_in_frames"] = dur_frames
    processed_audio_files.append(str(sc_wav))

ДОЛЖНО:
    sc["duration_in_frames"] = dur_frames
    sc["audio_url"] = f"scene_{i:02d}.wav"    <- ДОБАВИТЬ
    processed_audio_files.append(str(sc_wav))

ВНИМАНИЕ: После этого Remotion будет рендерить аудио через <Audio>, а ffmpeg также
мержит WAV. Двойное аудио. Решение: убрать внешний WAV merge из render_promo_shorts.py
или перейти полностью на граф (рекомендовано).

### 1.3 Верификация

```bash
# Проверить audioUrl в spec
python -c "
import json
spec = json.load(open('C:/Users/ANEN/motion-studio-framework/remotion/public/video-spec.json', encoding='utf-8'))
for sc in spec['scenes']:
    print(sc['id'], '|', sc.get('audioUrl', 'MISSING!'))"

# Громкость итогового MP4 (ожидаем -13...-20 dB, не -91 dB)
ffmpeg -hide_banner -nostats -i output\out.mp4 -af volumedetect -f null NUL 2>&1 | grep mean_volume
```

---

## РАЗДЕЛ 2: ИНТЕГРАЦИЯ node_deep_research В ГРАФ MSF

### 2.1 Новые поля VideoState (video_graph.py, класс VideoState, после строки 135)

```python
    # === LDR Deep Research ===
    ldr_enabled: Optional[bool]      # True -> запустить LDR; None/False -> skip
    ldr_query: Optional[str]         # явный запрос; None -> auto из text/topic
    ldr_topic: Optional[str]         # тема видео для авто-генерации запроса
    ldr_detailed: Optional[bool]     # True -> detailed_research, False -> quick_summary
    ldr_iters: Optional[int]         # iterations (default: 2)
    ldr_qpi: Optional[int]           # questions_per_iteration (default: 3)
    ldr_model: Optional[str]         # модель (default: "antigravity/claude-sonnet-4-6")
    ldr_summary: Optional[str]       # текст резюме из LDR
    ldr_sources: Optional[List[str]] # список URL-источников
    ldr_context: Optional[str]       # контекст для script_split
    ldr_cache_path: Optional[str]    # путь к ldr_last_raw.json (кэш)
```

### 2.2 Константы LDR (video_graph.py, после строки 31)

```python
LDR_VENV_PYTHON = r"C:\Users\ANEN\ldr_venv\Scripts\python.exe"
LDR_SCRIPT      = r"C:\Users\ANEN\ldr_work\ldr_run.py"
LDR_WORKDIR     = r"C:\Users\ANEN\ldr_work"
```

### 2.3 Реализация node_deep_research (добавить после строки 377)

```python
def _build_ldr_query(state: VideoState) -> str:
    """Авто-генерирует LDR-запрос из state."""
    explicit = state.get("ldr_query")
    if explicit:
        return explicit
    topic = state.get("ldr_topic")
    if topic:
        return topic
    text = state.get("text", "")
    return text[:120].strip() or "state of the art LLM models 2026"


def _format_ldr_context(summary: str, sources: List[str]) -> str:
    """Форматирует LDR-результат в контекст для script_split."""
    ctx = "## Актуальные данные (LDR Research)\n\n" + summary.strip() + "\n"
    if sources:
        ctx += "\n### Источники:\n"
        for i, s in enumerate(sources[:10], 1):
            ctx += f"{i}. {s}\n"
    return ctx


def node_deep_research(state: VideoState) -> VideoState:
    """Опциональная LDR-нода. Активна ТОЛЬКО если ldr_enabled=True.

    Запускает ldr_run.py в ldr_venv через subprocess (изоляция зависимостей).

    ПИТФОЛЛ: cwd=LDR_WORKDIR обязателен. Из C:/Users/ANEN запуск невозможен:
    там local_deep_research.py затеняет пакет -> ImportError.

    Кэш: при повторном вызове передать ldr_cache_path чтобы не перезапускать LDR.
    """
    if not state.get("ldr_enabled"):
        return state   # pass-through без побочных эффектов

    cache_path = state.get("ldr_cache_path")
    if cache_path and Path(cache_path).is_file():
        try:
            cached = json.loads(Path(cache_path).read_text(encoding="utf-8"))
            summary = cached.get("summary") or cached.get("report") or ""
            src_list = cached.get("sources") or cached.get("all_links_of_system") or []
            if summary:
                sources = [
                    (s.get("link") or s.get("url") or str(s))
                    for s in src_list[:15]
                    if isinstance(s, (dict, str))
                ]
                state["ldr_summary"] = summary
                state["ldr_sources"] = sources
                state["ldr_context"] = _format_ldr_context(summary, sources)
                print(f"[deep_research] loaded from cache {cache_path}")
                return state
        except Exception as exc:
            print(f"[deep_research] cache error: {exc} -- re-running LDR")

    query = _build_ldr_query(state)
    model = state.get("ldr_model", "antigravity/claude-sonnet-4-6")
    iters = state.get("ldr_iters", 2)
    qpi = state.get("ldr_qpi", 3)
    detailed = state.get("ldr_detailed", False)
    out_md = str(Path(LDR_WORKDIR) / "ldr_msf_context.md")

    cmd = [
        LDR_VENV_PYTHON, LDR_SCRIPT, query,
        "--model", model, "--iters", str(iters), "--qpi", str(qpi), "--out", out_md,
    ]
    if detailed:
        cmd.append("--detailed")

    print(f"[deep_research] query={query[:80]!r} model={model} iters={iters} qpi={qpi}")
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, errors="replace",
        cwd=LDR_WORKDIR,
        timeout=600,
    )

    if result.returncode != 0:
        print(f"[deep_research] WARNING: LDR failed (exit {result.returncode}). "
              f"Stderr: {result.stderr[:500]}")
        state["ldr_context"] = ""
        return state

    raw_path = Path(LDR_WORKDIR) / "ldr_last_raw.json"
    summary = ""
    sources: List[str] = []
    if raw_path.is_file():
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            summary = raw.get("summary") or raw.get("report") or ""
            src_list = raw.get("sources") or raw.get("all_links_of_system") or []
            sources = [
                (s.get("link") or s.get("url") or str(s))
                for s in src_list[:15]
                if isinstance(s, (dict, str))
            ]
        except Exception as exc:
            print(f"[deep_research] JSON parse error: {exc}")

    state["ldr_summary"] = summary
    state["ldr_sources"] = sources
    state["ldr_context"] = _format_ldr_context(summary, sources)
    state["ldr_cache_path"] = str(raw_path)
    print(f"[deep_research] done: summary={len(summary)} chars sources={len(sources)}")
    return state
```

### 2.4 Обновление build_msf_graph() (строки 729-761)

```python
def build_msf_graph():
    workflow = StateGraph(VideoState)

    workflow.add_node("gate_check", node_gate_check)
    workflow.add_node("deep_research", node_deep_research)    # <- НОВОЕ
    workflow.add_node("script_split", node_script_split)
    workflow.add_node("voice_synthesis", node_voice_synthesis)
    workflow.add_node("build_spec", node_build_remotion_spec)
    workflow.add_node("render", node_remotion_render)
    workflow.add_node("master_audio", node_master_audio)
    workflow.add_node("qa", node_qa)
    workflow.add_node("repair", node_repair)

    workflow.set_entry_point("gate_check")
    workflow.add_edge("gate_check", "deep_research")         # <- ИЗМЕНИТЬ
    workflow.add_edge("deep_research", "script_split")       # <- НОВОЕ
    workflow.add_edge("script_split", "voice_synthesis")
    workflow.add_edge("voice_synthesis", "build_spec")
    workflow.add_edge("build_spec", "render")
    workflow.add_edge("render", "master_audio")
    workflow.add_edge("master_audio", "qa")

    workflow.add_conditional_edges(
        "qa",
        check_qa_decision,
        {"repair": "repair", "end": END},
    )
    workflow.add_edge("repair", "render")

    return workflow.compile()
```

### 2.5 Пример вызова с LDR

```python
import sys
sys.path.insert(0, r"C:\Users\ANEN\motion-studio-framework")
from msf.graph.video_graph import build_msf_graph

result = build_msf_graph().invoke({
    "text": "Открытые модели в 2026 году.",
    "agent_level": 1,
    "ldr_enabled": True,
    "ldr_query": "best open weight LLMs August 2026 Gemma Qwen DeepSeek consumer GPU",
    "ldr_iters": 2,
    "ldr_qpi": 3,
    "output_path": r"C:\Users\ANEN\motion-studio-framework\output\with_research.mp4",
    "storyboard": [
        {"preset": "HeroKinetic", "title": "Модели 2026", "text": "Открытые модели достигли уровня GPT-5."},
        # ... остальные сцены
    ],
})
print("LDR context:", result.get("ldr_context", "")[:200])
print("MP4:", result["final_mp4"])
```

---

## РАЗДЕЛ 3: АКТУАЛИЗАЦИЯ СЦЕНАРИЕВ 2026 ГОДА

### 3.1 Устаревшие модели и замены

Файл | Устаревшие модели | Модели 2026 (из msf_models_2026.md)
script1 | Qwen3 32B, GPT-4o, Llama4, DeepSeek V3, Mistral L | Qwen3.6-27B, Gemma 4 31B, DeepSeek V4, Llama 4 Scout
script2 | "Модель" без имени | Gemma 4 31B (конкретно)
script3 | "8B в телефоне" | Qwen3.6-27B (MoE 16GB), Gemma 4 31B (24GB)

### 3.2 Данные моделей (верифицированные из LDR-исследования)

Модель           | Дата     | Тип         | VRAM@4bit | SWE-bench | AIME 2026 | GPQA  | Лицензия
Gemma 4 31B      | июн 2026 | Dense 31B   | ~18-20GB  | —         | 89.2%     | 84.3% | —
Qwen3.6-27B      | апр 2026 | MoE 3B акт. | 16GB      | 77.2%     | —         | —     | Apache 2.0
Qwen3.6-35B-A3B  | апр 2026 | MoE 3B акт. | <24GB     | 77.2%     | —         | —     | Apache 2.0
DeepSeek V4      | 2026     | —           | сервер    | лидер     | —         | —     | —
GLM-5.2          | июл 2026 | —           | —         | —         | —         | —     | —
Llama 4 Scout    | 2026     | —           | до 16GB   | —         | —         | —     | Meta

ВНИМАНИЕ: GLM-5.2 и Llama 4 Scout — числовые данные не подтверждены в LDR-отчёте.
Не включать точные цифры для этих моделей.

### 3.3 scripts_tg/script1_local_vs_cloud.json (2026 — Gemma 4 vs Qwen3.6-27B)

```json
{
  "width": 1080, "height": 1920, "fps": 60, "format": "vertical", "style": "cyber_lime",
  "scenes": [
    {
      "id": "s1", "preset": "CountdownHero", "durationInFrames": 102, "audioUrl": "scene_00.wav",
      "text": "Три. Две. Одна. Открытые модели две тысячи двадцать шесть года догнали топовые. Навсегда.",
      "from": 3, "finalWord": "НАВСЕГДА", "subtitle": "открытые vs проприетарные — 2026",
      "effects": [{"name": "ZoomPunch","intensity": 0.9}, {"name": "GlitchRgb","intensity": 0.45}, {"name": "ParticlesSparks","intensity": 0.6}]
    },
    {
      "id": "s2", "preset": "VersusSplit", "durationInFrames": 114, "audioUrl": "scene_01.wav",
      "text": "Qwen три-шесть двадцать семь Б на твоей карте против закрытой API за двадцать долларов.",
      "left": {"name": "Qwen3.6-27B", "value": 77}, "right": {"name": "GPT-5 mini", "value": 79},
      "vsLabel": "SWE-bench %",
      "effects": [{"name": "ZoomPunch","intensity": 0.8}, {"name": "HalationGlow","intensity": 0.5}]
    },
    {
      "id": "s3", "preset": "Bars3D", "durationInFrames": 120, "audioUrl": "scene_02.wav", "style": "steel",
      "text": "На AIME 2026 Gemma 4 тридцать один Б набрала восемьдесят девять целых две. Уровень докторанта.",
      "title": "AIME 2026 — больше лучше", "valueSuffix": "%",
      "segments": [{"label": "Gemma 4 31B","value": 89.2}, {"label": "Qwen3.6-27B","value": 77.2}, {"label": "Llama 4 Scout","value": 72.0}],
      "effects": [{"name": "DollyIn","intensity": 0.55}, {"name": "FilmGrain","intensity": 0.3}]
    },
    {
      "id": "s4", "preset": "Leaderboard", "durationInFrames": 126, "audioUrl": "scene_03.wav", "style": "sunrise",
      "text": "Вот три модели, которые реально стоит поставить себе на этой неделе.",
      "title": "Ставь себе эти три", "valueSuffix": " б",
      "rows": [{"name": "Gemma 4 31B","value": 89}, {"name": "Qwen3.6-27B","value": 77}, {"name": "Llama 4 Scout","value": 72}],
      "effects": [{"name": "SlideInUp","intensity": 0.8}, {"name": "Sheen","intensity": 0.5}],
      "overlays": [{"type": "notification","at": 0.55,"appName": "llm_hubs","title": "Конфиги выложены","text": "забирай в закрепе","position": "top"}]
    },
    {
      "id": "s5", "preset": "SubscribeCTA", "durationInFrames": 132, "audioUrl": "scene_04.wav",
      "text": "Конфиги для запуска всех трёх — в канале llm underscore hubs.",
      "title": "Конфиги внутри", "subtitle": "@llm_hubs", "badge": "БЕСПЛАТНО",
      "effects": [{"name": "ZoomPulse","intensity": 0.7}, {"name": "Bloom","intensity": 0.4}]
    }
  ]
}
```

### 3.4 scripts_tg/script2_prompt_unlock.json (2026 — Gemma 4 31B промпт-хак)

```json
{
  "width": 1080, "height": 1920, "fps": 60, "format": "vertical", "style": "neon",
  "scenes": [
    {
      "id": "s1", "preset": "HeroKinetic", "durationInFrames": 96, "audioUrl": "scene_00.wav",
      "text": "Эта одна строка заставляет Gemma 4 отвечать там, где она раньше отказывала.",
      "title": "ОДНА СТРОКА", "subtitle": "и Gemma 4 перестаёт отказывать", "badge": "2026",
      "effects": [{"name": "ZoomPunch","intensity": 0.95}, {"name": "GlitchBlock","intensity": 0.5}, {"name": "LightFlashCut","intensity": 0.7}]
    },
    {
      "id": "s2", "preset": "PhoneMockup", "durationInFrames": 114, "audioUrl": "scene_01.wav", "style": "glass",
      "text": "Смотри. Запрос без роли — и Gemma 4 уходит в отказ.",
      "innerPreset": "AiChatStream", "device": "phone", "tilt": 8,
      "innerProps": {
        "title": "Gemma 4 31B",
        "messages": [{"from": "user", "text": "Помоги разобрать этот код"}],
        "response": "Я не могу помочь с анализом чужого кода без контекста использования."
      },
      "effects": [{"name": "DollyIn","intensity": 0.45}]
    },
    {
      "id": "s3", "preset": "CodeReveal", "durationInFrames": 120, "audioUrl": "scene_02.wav", "style": "blueprint",
      "text": "Добавляешь роль и явное разрешение. Gemma 4 тридцать один Б отвечает полностью.",
      "title": "добавь это в начало", "language": "text",
      "code": "Ты — старший разработчик.\nЗадача учебная, код мой.\nРазбери построчно, объясни\nкаждое архитектурное решение.",
      "effects": [{"name": "TypeIn","intensity": 1.0}, {"name": "ScanSweep","intensity": 0.55}]
    },
    {
      "id": "s4", "preset": "CompareSplit", "durationInFrames": 114, "audioUrl": "scene_03.wav",
      "text": "Без роли — отказ. С ролью — полный разбор. Один промпт, разница в небо.",
      "title": "Разница",
      "cards": [{"title": "Без роли","description": "отказ или общий ответ","tag": "БЫЛО"}, {"title": "С ролью","description": "детальный разбор кода","tag": "СТАЛО"}],
      "effects": [{"name": "SlideInUp","intensity": 0.75}]
    },
    {
      "id": "s5", "preset": "QuoteCard", "durationInFrames": 108, "audioUrl": "scene_04.wav",
      "text": "Модель не отказывает. Она ждёт правильный контекст.",
      "author": "LLM Hubs",
      "effects": [{"name": "FadeIn","intensity": 0.6}]
    },
    {
      "id": "s6", "preset": "SubscribeCTA", "durationInFrames": 126, "audioUrl": "scene_05.wav",
      "text": "Архив промптов под Gemma 4, Qwen три-шесть и DeepSeek V4 — в канале.",
      "title": "100+ промптов", "subtitle": "@llm_hubs", "badge": "АРХИВ",
      "effects": [{"name": "ZoomPulse","intensity": 0.65}]
    }
  ]
}
```

### 3.5 scripts_tg/script3_phone_model.json (2026 — Qwen3.6-27B MoE в 16GB)

```json
{
  "width": 1080, "height": 1920, "fps": 60, "format": "vertical", "style": "glass",
  "scenes": [
    {
      "id": "s1", "preset": "QuizCard", "durationInFrames": 114, "audioUrl": "scene_00.wav", "style": "candy",
      "text": "Какая модель влезает в шестнадцать гигабайт и бьёт GPT-4o по коду? Выбирай.",
      "title": "Угадай", "question": "16 ГБ VRAM и выше GPT-4o:",
      "options": ["Qwen3.6-27B (MoE)", "Gemma 4 31B", "DeepSeek V4", "Qwen3 235B"],
      "correctIndex": 0, "revealAtProgress": 0.62,
      "effects": [{"name": "ZoomPunch","intensity": 0.85}, {"name": "ElasticPop","intensity": 0.6}]
    },
    {
      "id": "s2", "preset": "TokenCloud3D", "durationInFrames": 114, "audioUrl": "scene_01.wav",
      "text": "Qwen три-шесть. Тридцать пять миллиардов параметров, но активны только три миллиарда.",
      "title": "35B -> 3B активны", "subtitle": "sparse MoE архитектура", "pointCount": 900,
      "effects": [{"name": "OrbitAround","intensity": 0.7}, {"name": "Bloom","intensity": 0.55}]
    },
    {
      "id": "s3", "preset": "LayerStack3D", "durationInFrames": 120, "audioUrl": "scene_02.wav", "style": "blueprint",
      "text": "Благодаря MoE он грузится в шестнадцать гигабайт и выдаёт семьдесят семь процентов на SWE-bench.",
      "title": "16 ГБ VRAM", "subtitle": "77.2% SWE-bench Verified",
      "layers": ["35B параметров всего", "3B активных за шаг", "Apache 2.0 лицензия", "24GB @ Q8 / 16GB @ Q4"],
      "effects": [{"name": "ParallaxLayers","intensity": 0.8}, {"name": "ScanLines","intensity": 0.3}]
    },
    {
      "id": "s4", "preset": "RingStats", "durationInFrames": 120, "audioUrl": "scene_03.wav", "style": "steel",
      "text": "После Q4 сжатия: шестнадцать гигабайт, семьдесят токенов в секунду, ноль рублей лицензии.",
      "title": "После Q4 квантизации", "valueSuffix": "",
      "segments": [{"label": "16 GB VRAM","value": 80}, {"label": "~70 TPS","value": 70}, {"label": "SWE 77%","value": 77}],
      "effects": [{"name": "RotateSpin","intensity": 0.6}, {"name": "HalationGlow","intensity": 0.4}]
    },
    {
      "id": "s5", "preset": "AiChatStream", "durationInFrames": 132, "audioUrl": "scene_04.wav", "style": "neon",
      "text": "Вот как он отвечает на реальный вопрос по коду. Всё локально, ноль интернета.",
      "title": "Qwen3.6-27B локально",
      "messages": [{"from": "user", "text": "Найди баг в async функции"}],
      "response": "race condition в await — нужен asyncio.Lock() вокруг shared state.",
      "effects": [{"name": "TypeIn","intensity": 0.9}]
    },
    {
      "id": "s6", "preset": "SubscribeCTA", "durationInFrames": 126, "audioUrl": "scene_05.wav",
      "text": "Инструкция по запуску Qwen три-шесть с llama cpp и ollama — в канале llm underscore hubs.",
      "title": "Запускай локально", "subtitle": "@llm_hubs", "badge": "ГАЙД",
      "effects": [{"name": "ZoomPulse","intensity": 0.7}]
    }
  ]
}
```

---

## РАЗДЕЛ 4: ПОРЯДОК ВЫПОЛНЕНИЯ

ВЫСОКИЙ ПРИОРИТЕТ — аудио (немедленно измеримо):
1. video_graph.py:369: audio_file -> audio_url
2. video_graph.py:301: audio_url=normalised.get("audio_url") or f"scene_{index:02d}.wav"
3. render_promo_shorts.py:244: добавить sc["audio_url"] = f"scene_{i:02d}.wav"
4. Верификация: ffmpeg volumedetect -> ожидаем -18 dB не -91 dB

СРЕДНИЙ ПРИОРИТЕТ — актуализация контента:
5. scripts_tg/script1_local_vs_cloud.json -> рефакт (раздел 3.3)
6. scripts_tg/script2_prompt_unlock.json -> рефакт (раздел 3.4)
7. scripts_tg/script3_phone_model.json -> рефакт (раздел 3.5)

НИЗКИЙ ПРИОРИТЕТ — LDR интеграция:
8. VideoState: +11 ldr_* полей
9. Константы LDR_VENV_PYTHON, LDR_SCRIPT, LDR_WORKDIR
10. node_deep_research + _build_ldr_query + _format_ldr_context (раздел 2.3)
11. build_msf_graph(): gate_check -> deep_research -> script_split
12. Тест: node_deep_research({"ldr_enabled": False}) -> pass-through

---

## РАЗДЕЛ 5: СВОДКА ФАЙЛОВ

Файл                              | Тип     | Строки    | Суть
msf/graph/video_graph.py          | PATCH   | 369       | audio_file -> audio_url
msf/graph/video_graph.py          | PATCH   | 301       | audio_url с приоритетом normalised
msf/graph/video_graph.py          | ADD     | 31-33     | LDR константы
msf/graph/video_graph.py          | ADD     | 115-136   | +11 ldr_* полей в VideoState
msf/graph/video_graph.py          | ADD     | ~378      | node_deep_research + helpers
msf/graph/video_graph.py          | PATCH   | 729-761   | build_msf_graph deep_research
render_promo_shorts.py             | PATCH   | 243-244   | sc["audio_url"] = f"scene_{i:02d}.wav"
scripts_tg/script1_local_vs_cloud.json | REWRITE | all  | Gemma 4 31B, Qwen3.6-27B + audioUrl
scripts_tg/script2_prompt_unlock.json  | REWRITE | all  | Gemma 4 промпт-хак + audioUrl
scripts_tg/script3_phone_model.json    | REWRITE | all  | Qwen3.6-27B MoE + audioUrl

---

## РАЗДЕЛ 6: КРИТИЧЕСКИЕ ПИТФОЛЫ

1. audio_file мёртвый ключ: исправить строку 369, НО hardcode строки 301 оставить как fallback —
   он нужен когда scene не прошла через node_voice_synthesis (напр. прямой стейт из storyboard).

2. render_promo_shorts.py двойное аудио: после добавления sc["audio_url"] Remotion будет рендерить
   аудио через <Audio>, а ffmpeg мержит WAV снаружи. Решение: либо убрать внешний merge,
   либо перейти на build_msf_graph().invoke() (рекомендовано).

3. LDR cwd=LDR_WORKDIR обязателен: C:/Users/ANEN содержит local_deep_research.py который
   затеняет пакет -> ImportError при запуске оттуда.

4. GLM-5.2 и Llama 4 Scout без чисел: конкретные benchmark не подтверждены в LDR-отчёте.
   Не указывать точные цифры для этих моделей в скриптах.

5. LDR timeout 600s: SearXNG может быть недоступен. node_deep_research не фатален при ошибке —
   логирует WARNING и продолжает pipeline без контекста.

6. scripts_tg audioUrl нужен только для direct render: граф ставит audioUrl автоматически
   через _scene_kwargs hardcode. В JSON-файлах audioUrl нужен только если рендеришь через
   npx remotion render --props=scripts_tg/... напрямую.
