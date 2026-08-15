# LLM Hubs — Voice-over beat sheet v2.2

Новые тексты синхронизированы с визуальными beat-ами, а не с абстрактным пересказом evidence pack. Каждая фраза рассчитана на одну scene group: hook, proof, practical takeaway и CTA. Формулировка **«вышел из preview»** заменяет внутреннее сокращение `GA`.

| Video | Beat sequence | Spoken script |
|---|---|---|
| `01_gemini37_flash_vs_sonnet5` | Hook 0–6 s → metric 6–15 s → caveat 15–25 s → price/CTA 25–33 s | Google показывает Gemini 3.7 Flash выше Sonnet 5 в двух конкретных метриках. FrontierCode: 43.6 против 42.7. И выше Code Arena для web development. Но это не общий рейтинг. По list price Flash дешевле на 62.5 процента. Сначала проверьте свой workload. Больше свежих разборов — в LLM Hubs. |
| `02_deepseek_v4pro_0813` | Preview hook 0–7 s → Telegram routing 7–16 s → API facts 16–25 s → code/CTA 25–35 s | DeepSeek V4 Pro 0813 вышел из preview. Он доступен в Expert Mode и через API. Главное — не ставить max на любую задачу. Для простого запроса выбирайте low. Для сложного разбора и tools — high или max. В API: миллион токенов контекста и до 384 тысяч output. Больше практики — в LLM Hubs. |
| `03_deepseek_v4pro_cost_clock` | Date hook 0–6 s → schedule 6–15 s → current price 15–24 s → CTA 24–32 s | У DeepSeek V4 Pro тариф меняется 16 августа в 16:00 UTC. Поэтому не подставляйте будущую цену в сегодняшний estimate. Сейчас output стоит 87 центов за миллион токенов. Новая peak и off-peak сетка начинается позже. Цена без даты — не цена. Честные разборы тарифов — в LLM Hubs. |
| `04_grok46_long_agent` | Agent hook 0–6 s → timeline 6–14 s → metric 14–22 s → API/CTA 22–32 s | Grok 4.6 вышел для длинных агентских задач. Но длинный агент не означает бесконтрольный счёт. В API: 500 тысяч токенов контекста, tools, JSON output и reasoning. Кэшированный input стоит 50 центов, обычный — 2 доллара. Считайте output и retries. Новые модели без иллюзий — в LLM Hubs. |
| `05_august_model_costmap` | Cost hook 0–5 s → input map 5–13 s → output map 13–20 s → decision/CTA 20–35 s | Кто сжигает бюджет? По input DeepSeek V4 Pro — 43.5 цента, Gemini Flash — 75. Grok 4.6 и Sonnet 5 — по 2 доллара. Но по output порядок другой. DeepSeek — 87 центов, Gemini — 3.75, Grok — 6, Sonnet — 10. Цена токена не равна цене задачи. Сравнивайте ваш workload. |

Тексты намеренно не пытаются озвучить каждую букву on-screen текста. Voice-over объясняет, а scene выводит число, дату или правило ровно в момент его произнесения.
