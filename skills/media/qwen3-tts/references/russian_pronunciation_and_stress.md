# Russian TTS pronunciation, stress and artifact fixing

Reference for Qwen3-TTS Russian narration. Two failure classes dominate: English
terms read with an English phoneme set, and Russian homographs stressed on the
wrong syllable. Both are fixed in the *text*, before synthesis — not with filters
after it.

## 1. Transliterate English terms into Cyrillic

The model switches phoneme sets mid-sentence when it sees Latin script, which
produces the "unnatural accent" effect. Rewrite the script itself.

| Source | Write as | Note |
|---|---|---|
| LLM | эл-эл-эм | Spell the letters. Plain `ЛЛМ` gets read as one mangled syllable — this was an observed user complaint. |
| motion | мо́ушен | `моушн` collapses; the `е` restores the second syllable. Also an observed complaint. |
| GitHub | Гитха́б | |
| open source | о́упен-со́рс | |
| DevTools | Дев-Ту́лз | |
| transformer | трансфо́рмер | |
| token / tokens | то́кен / то́кены | |
| prompt | про́мпт | |
| inference | и́нференс | |
| embedding | эмбе́ддинг | |
| checkpoint | чекпо́инт | |
| fine-tuning | файн-тю́нинг | |
| benchmark | бе́нчмарк | |
| latency | лэ́йтенси | |
| framework | фре́ймворк | |
| GPU / CPU | джи-пи-ю́ / си-пи-ю́ | Spell out. |
| API | эй-пи-а́й | Spell out. |
| VRAM | ви-ра́м | |
| Hugging Face | Ха́гинг Фэйс | |
| PyTorch | Па́йторч | |
| Qwen | Кве́н | |
| Claude | Клод | |
| Gemini | Дже́мини | |
| Rust | Раст | |
| Python | Па́йтон | |

Rules of thumb:
- **Acronyms get spelled out letter-by-letter with hyphens**, not glued together.
- Keep brand names in Latin only when a visual reads them on screen; the *spoken*
  line should still be Cyrillic.
- Multi-word English phrases take a hyphen so the model does not insert a pause.

## 2. Stress marks (combining acute U+0301)

Place the acute **after** the stressed vowel: `дока́з` = `дока` + `\u0301` + `з`.
Only mark words that are genuinely ambiguous or that you have heard go wrong —
over-marking makes delivery stilted.

Homographs that change meaning and must be marked:

| Written | Stress for meaning | |
|---|---|---|
| больше | бо́льше (more) | |
| замок | замо́к (lock) / за́мок (castle) |
| потом | пото́м (later) / по́том (by sweat) |
| уже | уже́ (already) / у́же (narrower) |
| дома | до́ма (at home) / дома́ (houses) |
| много | мно́го | |
| понял | по́нял | |
| начали | на́чали | |
| включит | включи́т | |
| звонит | звони́т | |
| облегчит | облегчи́т | |
| средства | сре́дства | |
| контекст | конте́кст | |
| процент | проце́нт | |

Numerals and units are a frequent miss — write them as words when the reading is
ambiguous: `60 FPS` -> `шестьдеся́т ка́дров в секу́нду`, `1080p` -> `ты́сяча
во́семьдесят пи́`, `-16 LUFS` -> `ми́нус шестна́дцать луфс`, `3.5 ГБ` ->
`три с полови́ной гигаба́йта`.

## 3. Punctuation controls pacing

- Comma = short breath. Period = full stop with a longer tail.
- **Em dash forces the longest pause** — use it for dramatic beats instead of
  ellipsis, which the model tends to swallow.
- Question marks do lift intonation; exclamation marks raise energy but also
  raise pitch, so avoid stacking them in a cloned voice (it exaggerates any
  vocoder harshness).
- Keep one sentence per scene chunk and <= 28 words. Long sentences drift in
  prosody and are harder to align to frames.

## 4. Implementation pattern

Keep the dictionary in code, apply it as a preprocessing pass, and keep the
*display* text separate from the *spoken* text — on-screen captions should show
`LLM`, while the TTS input receives `эл-эл-эм`.

```python
PRONUNCIATION = {"LLM": "эл-эл-эм", "motion": "мо́ушен", "GitHub": "Гитха́б"}
STRESS = {"больше": "бо́льше", "начали": "на́чали"}

def for_speech(text: str) -> str:
    """Return the TTS-facing string; keep the original for on-screen captions."""
    for src, dst in PRONUNCIATION.items():
        text = re.sub(rf"\b{re.escape(src)}\b", dst, text, flags=re.IGNORECASE)
    for src, dst in STRESS.items():
        text = re.sub(rf"\b{src}\b", dst, text)
    return text
```

## 5. What NOT to do

- Do not fix pronunciation with FFmpeg EQ or compression. Aggressive
  `equalizer=f=3000` / `acompressor` on Qwen3-TTS output creates high-pitched
  whistle artifacts and volume decay toward the end of the clip.
- Do not fix a "robotic" voice by editing the script — that symptom is about the
  reference audio, not the text. See "Reference Audio Vetting" in SKILL.md.
- Do not add stress marks to every word; mark ambiguity only.
