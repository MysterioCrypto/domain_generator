---
id: DESIGN-LOCAL-MODEL-SKILL-ADAPTER-0.1
kind: integration-design
status: accepted
normative: true
target: integration-0.1
implemented: false
---

# Local Model Skill / Adapter v0.1

Этот документ фиксирует provider-neutral слой между natural-language intent пользователя и уже реализованным canonical application boundary `domain_generator`.

## 1. Цель

Local Model Adapter должен позволить LLM/agent-host сформировать корректный `GenerationRequest` из человеческого описания региона и запустить существующий generator без прямого доступа модели к внутренним Core stages.

Canonical flow:

```text
user intent
  + base GenerationRequest
  + PresetCatalog
  + optional PresetGuideCatalog
        ↓
model-facing authoring context
        ↓
local model / agent host
        ↓
LocalModelDecision
        ↓
contract validation
        ↓
compiler preflight
        ↓
canonical application API
        ↓
DomainBundle + optional technical preview
```

Adapter является integration layer и не изменяет semantics Core.

## 2. Архитектурная граница

Core остаётся независимым от LLM provider, agent framework и inference runtime.

В Core/package base dependencies не добавляются обязательные зависимости на:

- Ollama;
- llama.cpp;
- OpenAI;
- Anthropic;
- Transformers;
- конкретный agent framework.

Reference implementation adapter-а может находиться в integration/adapters namespace репозитория, но использует только публичные contracts/application API Core.

Модель не получает прямой control surface для:

```text
layout_stage
terrain_stage
hydrology_stage
surface_stage
placement_stage
final_stage
```

и не редактирует `DomainData`, `.npy` payloads или generated bundle после generation.

## 3. Canonical application dependency

Adapter использует существующую публичную границу:

```python
registry_for_request(...)
generate_domain_bundle(...)
```

Для compiler preflight он может использовать публичные `compile_domain_spec(...)` и validated `PresetRegistry`, не запуская generation stages.

Local reference implementation использует Python API, а не shell subprocess. Будущий remote GitHub Actions adapter использует canonical CLI, сохраняя те же generation semantics.

## 4. Base GenerationRequest

Adapter не просит модель каждый раз заново изобретать технические defaults.

Caller предоставляет validated base `GenerationRequest`, содержащий нормальные project/runtime defaults, включая при необходимости:

- grid resolution;
- hydrology settings;
- surface settings;
- generation semantic config;
- project seed policy.

Модель формирует финальный `GenerationRequest` на основе этого base request.

Все effective значения должны присутствовать в финальном request; hidden runtime defaults adapter-а не становятся частью semantic generation state.

## 5. Политика изменения base request

В v0.1 модель по умолчанию предназначена для изменения пользовательского generation intent:

- `domain_spec.id` / label;
- domain extent, если размер задан или явно выводится из пользовательского запроса;
- features;
- feature parameters;
- constraints.

Модель не должна произвольно менять технические настройки только ради получения иного результата:

- grid cell size;
- `max_attempts`;
- `target_valid_candidates`;
- низкоуровневые hydrology constants;
- низкоуровневые surface constants.

Изменение таких параметров допустимо только если оно явно входит в пользовательский intent или caller policy разрешает конкретное поле.

`seed` не меняется скрыто. Изменение seed требует explicit user intent/caller policy и считается semantic change.

## 6. Model-facing catalog projection

Canonical `PresetCatalog` является источником истины, но его raw recipe representation не считается достаточной человекоориентированной инструкцией для модели.

Adapter строит deterministic model-facing projection из реального catalog. Projection содержит только сведения, выведенные из canonical preset definitions, например:

```json
{
  "id": "mountain_ridge",
  "family": "terrain",
  "geometry": "band",
  "stage": "terrain",
  "operator": "ridge",
  "parameters": {
    "height_m": {
      "kind": "range",
      "type": "float",
      "min": 200,
      "max": 1800
    }
  }
}
```

Projection не является вторым источником истины и не может расширять допустимые parameter ranges, operator ids, family/layout/stage semantics или capabilities.

Порядок presets и parameter names в projection должен быть canonical/deterministic.

## 7. Optional PresetGuideCatalog

Для человекоориентированной семантики вводится adapter-only optional guide contract:

```json
{
  "preset_guide_version": "0.1",
  "presets": [
    {
      "id": "mountain_ridge",
      "summary": "Длинный горный хребет.",
      "keywords": ["mountains", "ridge", "горный хребет"],
      "parameter_notes": {
        "height_m": "Выраженность хребта."
      }
    }
  ]
}
```

Guide находится за границей Core и не меняет compiler/runtime semantics.

Validation guide-а:

- каждый guide preset id обязан существовать в canonical `PresetCatalog`;
- каждый `parameter_notes` key обязан существовать в corresponding canonical preset;
- duplicate guide ids запрещены;
- guide не объявляет operator, range, geometry, stage или capability;
- отсутствие guide допустимо.

## 8. Model authoring context

Adapter передаёт модели структурированный context, содержащий как минимум:

- user intent;
- serialized base `GenerationRequest`;
- deterministic model-facing catalog projection;
- optional validated guide metadata;
- краткие правила allowed/forbidden edits;
- schema/contract instruction для `LocalModelDecision`;
- при repair attempt — только релевантные validation/preflight diagnostics предыдущего draft.

Context должен быть serializable и provider-neutral.

## 9. LocalModelDecision v0.1

Модель возвращает не произвольный текст, а adapter-level envelope.

Ready:

```json
{
  "decision_version": "0.1",
  "status": "ready",
  "request": { "...": "GenerationRequest" },
  "assumptions": [
    "Размер поселения не был указан; использован стандартный preset."
  ]
}
```

Needs clarification:

```json
{
  "decision_version": "0.1",
  "status": "needs_clarification",
  "questions": [
    "Река должна начинаться внутри региона или входить с северной границы?"
  ]
}
```

`assumptions` и `questions` не попадают в `DomainSpec`, provenance или Core contracts.

Decision contract является adapter/integration contract, а не Core world contract.

## 10. Clarification semantics

Модель имеет право вернуть `needs_clarification`, если без ответа пришлось бы существенно выдумывать пользовательский intent.

Adapter в этом случае:

- не запускает compiler/generation;
- возвращает questions caller-у;
- не подставляет скрытые semantic assumptions самостоятельно.

## 11. Preflight

Для decision со `status=ready` adapter выполняет до generation:

```text
parse/validate LocalModelDecision
→ validate GenerationRequest
→ validate PresetCatalog / guide consistency
→ build PresetRegistry
→ compile_domain_spec(...)
→ READY FOR GENERATION
```

Compiler preflight не выполняет layout/terrain/hydrology/surface/placement/final generation stages и не создаёт candidate.

Цель preflight — ловить structural/capability errors до дорогостоящей generation.

## 12. Technical repair loop

v0.1 разрешает максимум два automatic repair attempts после initial model draft:

```text
initial draft
→ preflight error
→ repair #1
→ preflight error
→ repair #2
→ still invalid => stop
```

Итого model может сформировать максимум три drafts для одного user intent в одном adapter run.

Repair допустим только для технической корректности, например:

- invalid JSON / decision contract;
- wrong field/type;
- unknown preset id;
- parameter outside canonical domain;
- unsupported relation/selector/operator capability;
- compiler error, который можно исправить без изменения пользовательского смысла.

Diagnostics repair attempt-а должны передаваться модели явно и сохраняться в audit result.

## 13. Repair не является semantic reroll

Adapter не имеет права под видом repair самостоятельно:

- менять seed;
- ослаблять/удалять hard constraint;
- удалять requested feature;
- менять размер/тип requested geography;
- увеличивать `max_attempts`;
- менять generation policy ради успеха;
- заменять пользовательское намерение более удобным для Core вариантом.

Если технически корректный request не может быть сгенерирован, это generation failure, а не повод для скрытого semantic rewrite.

## 14. Ровно один semantic generation после успешного preflight

После успешного preflight v0.1 выполняет один canonical application run для финального request.

Adapter не запускает автономный цикл:

```text
generate
→ inspect preview
→ change seed/request
→ generate again
```

и не делает несколько generation runs, выбирая субъективно «красивый» результат.

Внутренние attempts внутри одного canonical `GenerationConfig` являются частью Core semantics и не считаются adapter reroll.

## 15. Generation failure

Если request прошёл preflight, но canonical generation не смог получить valid candidate или завершился другой generation error, adapter возвращает failure caller-у.

v0.1 не делает automatic semantic replanning после generation failure.

Новый request после такой ошибки требует нового explicit user/caller decision.

## 16. Preview semantics

Technical preview может быть запрошен caller-ом как обычный application output.

Модель v0.1 не использует `technical-map.png` для автоматической эстетической оценки, semantic replanning или reroll.

Visual feedback loop требует отдельного design decision.

## 17. Provider-neutral model interface

Reference adapter определяет минимальный provider-neutral interface/Protocol: host получает `ModelAuthoringContext` и возвращает serialized/typed `LocalModelDecision` draft.

Конкретная transport/inference implementation находится снаружи v0.1 adapter semantics.

Adapter не требует network access и не знает API key/provider-specific model ids.

## 18. Auditability

Adapter result должен позволять восстановить ход authoring без включения model chain-of-thought.

Сохраняются как structured metadata/result:

- final decision status;
- final validated `GenerationRequest`, если ready;
- assumptions/questions;
- число draft/repair attempts;
- normalized diagnostics каждого failed preflight;
- использованный catalog identity/fingerprint или deterministic digest;
- использованный guide digest при наличии;
- base request digest;
- generation result/output path при success.

Private model reasoning/chain-of-thought не требуется и не считается audit artifact.

## 19. Determinism boundary

Core generation determinism не зависит от модели: после того как final `GenerationRequest` и `PresetCatalog` зафиксированы, generator выполняет обычные INV-003/INV-009 semantics.

Natural-language → request translation сама по себе не обязана быть deterministic между model versions/providers.

Поэтому audit boundary фиксирует final request и relevant input digests, а не обещает exact replay самой LLM authoring phase.

## 20. Skill boundary

Model skill/instruction описывает модели:

- цель — authoring `GenerationRequest`, а не симуляция мира внутри LLM;
- использовать только presented presets/parameters;
- предпочитать feature/constraint semantics изменению низкоуровневых physical constants;
- возвращать `needs_clarification`, когда intent materially ambiguous;
- не выдумывать capabilities;
- не менять seed/constraints ради скрытого reroll;
- возвращать только contract-compatible decision payload.

Skill является integration artifact и не становится нормативным источником Core semantics.

## 21. Local execution boundary

Reference local adapter после успешного preflight вызывает Python application API напрямую.

Он не должен:

- запускать shell-команду для внутренних stages;
- импортировать private implementation internals, когда существует public application/compiler API;
- использовать filesystem как внутреннюю message bus между generation stages.

CLI остаётся самостоятельной canonical surface для человека и будущего remote adapter.

## 22. Out of scope v0.1

Не входят:

- concrete Ollama/llama.cpp/OpenAI backend;
- network/API credential management;
- remote GitHub Actions generation;
- automatic semantic replanning после generation failure;
- preview/image visual critique loop;
- ImageGen;
- artistic campaign map;
- automatic preset authoring;
- editing canonical `DomainData` after generation;
- infinite/self-directed agent loop;
- hidden retries/rerolls;
- YAML adapter;
- production setting-specific preset content.

## 23. Implementation scope после docs merge

Отдельный implementation PR включает bounded provider-neutral slice:

- adapter contracts для `LocalModelDecision`, guide и authoring context/result;
- deterministic model-facing preset projection;
- guide/catalog consistency validation;
- base-request/caller edit policy boundary;
- provider-neutral model Protocol/callback;
- decision parsing/validation;
- compiler preflight;
- maximum-two-repair orchestration;
- one-generation execution boundary;
- structured audit result без chain-of-thought;
- tests для ready/clarification/repair/failure/no-reroll semantics;
- reference model skill/instruction artifact;
- status docs.

Implementation PR не merge-ится без отдельного явного принятия пользователем.

## 24. Следующие checkpoints

После implementation и отдельного принятия `Local Model Skill / Adapter v0.1`:

```text
Remote GitHub Actions Generation Adapter
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.
