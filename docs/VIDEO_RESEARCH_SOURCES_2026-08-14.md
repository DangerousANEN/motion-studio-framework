# Проверенные источники для серии LLM-роликов

**Дата retrieval:** 2026-08-14 (GMT+7).

## Ролик 1 — локальные LLM с Ollama

| ID | Проверяемый факт | Первичный источник |
|---|---|---|
| `ollama_quickstart` | Ollama документирует запуск на macOS, Windows и Linux; quickstart показывает запуск модели командой `ollama run gemma4`. | https://docs.ollama.com/quickstart |
| `ollama_quant` | Официальная документация указывает, что квантование снижает потребление памяти и позволяет запускать модель на более скромном железе, с компромиссом по точности; приведён пример `ollama create --quantize q4_K_M`. | https://docs.ollama.com/import |
| `ollama_api` | После установки Ollama API доступен локально по умолчанию на `http://localhost:11434/api`; есть официальные библиотеки Python и JavaScript. | https://docs.ollama.com/api/introduction |

**Сценарное ограничение:** не обещать, что любая модель бесплатно и быстро заработает на любом ноутбуке. Говорить о локальном запуске и о компромиссе память/скорость/качество.

## Ролик 2 — Gemini API и Google AI Studio

| ID | Проверяемый факт | Первичный источник |
|---|---|---|
| `gemini_free` | Google описывает Free tier для разработчиков и небольших проектов: доступ к части моделей, бесплатные input/output tokens и Google AI Studio; контент Free tier используется для улучшения продуктов. | https://ai.google.dev/gemini-api/docs/pricing |
| `gemini_rate_limits` | Лимиты Gemini API измеряются как RPM, TPM и RPD, различаются по модели/usage tier, применяются к project, а не API key; фактические лимиты следует смотреть в AI Studio. | https://ai.google.dev/gemini-api/docs/rate-limits |
| `gemini_billing` | Новые аккаунты начинают на Free tier, который открывает часть моделей Gemini API и AI Studio в рамках их free-tier rate limits; для paid tier нужно подключить billing. | https://ai.google.dev/gemini-api/docs/billing |

**Сценарное ограничение:** не называть фиксированные RPM/TPM без проверки конкретного проекта и модели. Явно сказать, что бесплатный доступ ограничен, зависит от модели и project limits; не советовать отправлять чувствительные данные в Free tier.

## Ссылки

1. [Ollama Quickstart](https://docs.ollama.com/quickstart)
2. [Ollama — Importing and quantizing a model](https://docs.ollama.com/import)
3. [Ollama API Introduction](https://docs.ollama.com/api/introduction)
4. [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)
5. [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
6. [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing)

## Ролик 3 — OpenRouter Free Models Router

| ID | Проверяемый факт | Первичный источник |
|---|---|---|
| `openrouter_free_router` | `openrouter/free` выбирает случайную доступную бесплатную модель после фильтрации по требуемым возможностям; ответ включает модель, которая фактически использовалась. | https://openrouter.ai/docs/guides/routing/routers/free-router |
| `openrouter_free_limits` | Для free variants документация указывает 20 RPM; суточный лимит зависит от объёма купленных credits: 50 RPD при суммарных credits менее $10 и 1000 RPD при $10 и более. | https://openrouter.ai/docs/api_reference/limits |
| `openrouter_free_limitations` | Free router подходит для экспериментов, обучения и low-volume use cases; список бесплатных моделей меняется, доступность/latency варьируются, а выбор конкретной модели не контролируется. | https://openrouter.ai/docs/guides/routing/routers/free-router |
| `openrouter_fallback` | OpenRouter документирует прозрачный fallback к следующему provider при ошибке и API endpoint для получения текущей информации о ключе/лимитах. | https://openrouter.ai/docs/faq ; https://openrouter.ai/docs/api_reference/limits |

**Сценарное ограничение:** не называть `openrouter/free` стабильным production-model и не обещать фиксированное качество. Рекомендовать его для тестов/прототипов; проверять поле `model` в ответе и предусматривать fallback.

## Дополнительные ссылки

7. [OpenRouter Free Models Router](https://openrouter.ai/docs/guides/routing/routers/free-router)
8. [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits)
9. [OpenRouter FAQ](https://openrouter.ai/docs/faq)
10. [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart)

## Ролик 4 — Hugging Face Inference Providers

| ID | Проверяемый факт | Первичный источник |
|---|---|---|
| `hf_monthly_credits` | Hugging Face публикует для Free Users ежемесячные credits в $0.10, subject to change; после исчерпания credits доступен pay-as-you-go при покупке credits. | https://huggingface.co/docs/inference-providers/en/pricing |
| `hf_routing` | Inference Providers предоставляют единый API к моделям/провайдерам; при automatic selection выбирается самый быстрый доступный provider, а суффикс `:cheapest` запрашивает наиболее экономичный provider для модели. | https://huggingface.co/docs/inference-providers/en/index |
| `hf_playground` | Hugging Face документирует Inference Playground и виджеты на model pages для интерактивного тестирования моделей; для API требуется HF token с inference permissions. | https://huggingface.co/docs/hub/en/models-inference |

**Сценарное ограничение:** не называть $0.10 полноценной бесплатной production-инфраструктурой. Позиционировать как микро-бюджет для сравнения/тестов, затем показать `:cheapest` и мониторинг usage.

## Дополнительные ссылки

11. [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/en/index)
12. [Hugging Face pricing and billing](https://huggingface.co/docs/inference-providers/en/pricing)
13. [Inference Providers on the Hub](https://huggingface.co/docs/hub/en/models-inference)

## Ролик 5 — экономичный Gemini Batch и Flex

| ID | Проверяемый факт | Первичный источник |
|---|---|---|
| `gemini_batch_half` | Gemini Batch API предназначен для больших объёмов асинхронных запросов по 50% стандартной стоимости; ориентир turnaround — до 24 часов, хотя часто быстрее. | https://ai.google.dev/gemini-api/docs/batch-api |
| `gemini_batch_use_case` | Google рекомендует Batch для не срочных массовых задач, например preprocessing и evaluations; для крупных пакетов поддерживается JSONL input. | https://ai.google.dev/gemini-api/docs/batch-api |
| `gemini_flex_half` | Google представил Flex inference для latency-tolerant задач с заявленной 50% экономией против Standard в обмен на меньшую критичность/добавленную latency; Flex доступен paid tiers. | https://blog.google/innovation-and-ai/technology/developers-tools/introducing-flex-and-priority-inference/ |
| `gemini_batch_paid` | Pricing documentation относит Batch API с 50% cost reduction к Paid tier, а не к универсальному Free tier. | https://ai.google.dev/gemini-api/docs/pricing |

**Сценарное ограничение:** это ролик об экономии, не о бесплатном доступе. Чётко разделять Batch (асинхронно, не для live ответа) и Flex (синхронно, но с компромиссом по latency/reliability); перед запуском сверять model/tier.

## Дополнительные ссылки

14. [Gemini Batch API](https://ai.google.dev/gemini-api/docs/batch-api)
15. [Google: Flex and Priority inference](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-flex-and-priority-inference/)
