# MSF Studio v2 — автономный вертикальный срез

**Базовый коммит:** `1a6454f`  
**Старт реализации:** 2026-08-14 05:37 GMT+7  
**Целевой дедлайн:** 2026-08-14 14:00 GMT+7

## Цель среза

До дедлайна реализовать обратимое, работоспособное основание для MSF Studio v2. Работа фокусируется на едином Python/Remotion execution path, versioned contracts, schema-driven catalog, предсказуемом agent workflow, структурированных событиях и нескольких готовых расширениях библиотеки. Необходимо избежать создания второго renderer-а, второй копии registry или нового небезопасного bypass пути к production render.

## Включено в реализацию

| Поток | Поставляемый результат |
|---|---|
| Canonical core | Application-level request/run contracts, единый сервис запуска, job/run identity и статусы без замены существующего LangGraph renderer-а. |
| Catalog | Scene/Audio/Voice manifests, dynamic discovery из существующего TypeScript registry, schema-compatible search и storyboard validation. |
| Agent safety | Capability tiers, draft/stable lifecycle, workflow prompts и унифицированный `msf-studio` skill в репозитории. |
| Observability | Структурированные run events, event store и API для чтения событий/артефактов; текущий stdout остаётся совместимым fallback. |
| MCP foundation | Неопасный adapter с discovery, draft и validation operations; тяжёлый render остаётся явной compute action. |
| Library | Несколько универсальных стабильных сцен, sound-design manifests и новые/обновлённые demo props. |
| API and tests | REST endpoints для catalog/storyboards/runs, unit tests новых contracts/catalog/events и существующая статическая проверка. |
| Documentation | Архитектурная спецификация, migration notes, skill/readme и release notes. |

## Осознанно отложено

В этот срез не входят удалённый multi-tenant control plane, OAuth MCP через интернет, биллинг, CRDT-редактор, публичный marketplace и социальный автопостинг. Они требуют отдельного security/reliability цикла и не должны задерживать local-first Studio foundation.

## Критерии завершения

1. Старый panel-run продолжает работать или получает совместимый adapter к каноническому сервису.
2. Агент может discover-получить schema/manifest и построить проверяемый storyboard без hardcoded scene lists.
3. Ошибка storyboard или job имеет структурированный event и возвращается через API.
4. Новые assets проходят type/schema/static checks и содержат demo data.
5. Тесты, которые возможно выполнить в текущем окружении, задокументированы с точными результатами; непроверенные GPU/renderer пути явно отмечены.
