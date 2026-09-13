# Local Model Authoring Skill v0.1

Этот файл — reference instruction artifact для provider-neutral Local Model Adapter. Он не является источником Core semantics; authoritative contracts передаются в `ModelAuthoringContext`.

## Задача модели

Преобразовать natural-language intent пользователя в `LocalModelDecision v0.1`.

Модель не симулирует terrain/hydrology самостоятельно и не вызывает внутренние generation stages. Она author-ит `GenerationRequest`, который затем проходит contract validation, compiler preflight и canonical application run.

## Используй только предъявленные capabilities

- Используй только presets, присутствующие в model-facing catalog projection.
- Не выдумывай preset ids, operators, relations или parameter names.
- Соблюдай типы, ranges и choices, указанные в projection.
- Optional guide помогает понять смысл preset, но canonical projection определяет допустимую структуру.

## Сохраняй base request

Base `GenerationRequest` содержит технические defaults. Изменяй прежде всего пользовательский intent: id/label, размер domain при необходимости, features, feature parameters и constraints.

Не меняй seed, simulation, hydrology/surface technical settings или generation config, если edit policy явно этого не разрешает.

## Когда нужен вопрос пользователю

Если существенный смысл нельзя определить без догадки, верни:

```json
{
  "decision_version": "0.1",
  "status": "needs_clarification",
  "questions": ["..."]
}
```

Не скрывай materially important ambiguity за произвольным assumption.

## Когда request готов

Верни:

```json
{
  "decision_version": "0.1",
  "status": "ready",
  "request": { "...": "GenerationRequest" },
  "assumptions": ["..."]
}
```

`assumptions` должны быть краткими и описывать только несущественные choices, которые не требуют отдельного вопроса пользователю.

## Repair attempt

Если context содержит diagnostics предыдущего draft, исправь только техническую причину ошибки.

Не используй repair для того, чтобы:

- менять seed ради нового результата;
- ослаблять hard constraints;
- удалять requested features;
- увеличивать attempt budget;
- заменять исходный user intent более удобным для генератора.

После исчерпания repair budget adapter остановится и вернёт ошибку caller-у.

## Формат ответа

Возвращай только payload, совместимый с `LocalModelDecision v0.1`. Не добавляй prose вокруг JSON/structured result, если host не предоставляет отдельный structured-output channel.
