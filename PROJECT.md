---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-json-schema-slice-3
next_topic: deterministic-rng-derivation-v1
completed:
  - M0-project-foundation
  - M1-data-contracts
accepted_m1_topics:
  - domain-size-and-grid
  - world-coordinate-convention
  - feature-preset-model
  - constraint-and-spatial-selector-model
  - parameter-domain-and-sampling-model
  - preset-registry-boundary
  - generation-plan-role
  - layout-candidate-role
  - placement-reservations
  - domain-data-bundle-model
  - canonical-derived-debug-data
  - staged-validation-and-ranking
  - terrain-generation-baseline
  - hydrology-generation-baseline
  - surface-generation-baseline
  - poi-suitability-v0.1
  - attempt-model-v0.1
  - deterministic-rng-namespaces-v0.1
  - versioning-and-replay-v0.1
  - core-stage-dependency-dag
  - python-data-model-v0.1
  - domain-spec-v0.1-design
  - generation-plan-v0.1-design
  - layout-candidate-v0.1-design
  - domain-data-v0.1-design
  - validation-result-v0.1-design
  - generation-config-v0.1-design
  - m1-contract-consistency-review
implemented_m2:
  - minimal-python-package
  - geometry-value-models-v0.1
  - domain-spec-pydantic-v0.1
  - generation-plan-pydantic-v0.1
  - layout-candidate-pydantic-v0.1
  - validation-result-pydantic-v0.1
  - generation-config-pydantic-v0.1
  - domain-data-pydantic-v0.1
  - generated-json-schema-v0.1
  - contract-schema-roundtrip-tests
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены.

`M2 — Deterministic pipeline` начат с полного contract layer. В `src/domain_generator` реализованы Pydantic v2-модели всех основных Core 0.1 contracts и geometry/value types:

- `DomainSpec`;
- `GenerationPlan`;
- `LayoutCandidate` / `PlacementReservation`;
- `ValidationResult`;
- `GenerationConfig`;
- `DomainData`;
- point/corridor/band/area/RegionSet geometry.

Для шести root serialized contracts теперь генерируются и коммитятся JSON Schema snapshots Draft 2020-12. Экспорт выполняется из текущих Pydantic models с aliases enabled; snapshots имеют deterministic compact JSON representation. Schema tests проверяют, что committed snapshots совпадают с моделями, сами schemas валидны как Draft 2020-12, а canonical JSON serialization проходит model round-trip и schema validation.

JSON Schema является interchange/documentation layer, а не полной заменой Core validation: cross-field правила из `model_validator` (например exact grid divisibility, aggregate validation state и обязательный canonical field set `DomainData`) по-прежнему проверяются Python contract models.

Contract models используют `extra="forbid"` и strict scalar annotations, но не глобальный `ConfigDict(strict=True)`, чтобы JSON/YAML lists могли нормализоваться в immutable tuples, а строки — в `StrEnum`. Где требует contract, serialized floats отклоняют `NaN`/`±Inf`.

Локальный combined test suite после schema slice: **37/37 tests passed**.

Генерационных алгоритмов, compiler и RNG implementation пока нет.

## Следующий шаг

До реализации RNG зафиксировать exact reproducibility details `rng v1`: canonical namespace encoding, cryptographic derivation и concrete PRNG/seed width. После принятия реализовать deterministic RNG derivation и тесты isolation/order-independence, затем basic attempt/pipeline skeleton.

## Ещё не сделано

- exact RNG v1 derivation implementation;
- compiler и preset registry implementation;
- runtime CandidateState/dataclasses;
- basic attempt/pipeline skeleton;
- geometry/grid operators;
- terrain/hydrology/surface/placement generators;
- renderer и GitHub Actions.

## Инварианты

- **INV-001:** Core независим от ChatGPT/OpenAI, GitHub Actions, конкретного чата, лора Вальхаллы и renderer.
- **INV-002:** `DomainSpec` описывает намерение; `GenerationPlan` — resolved recipe; `DomainData` — итоговый мир.
- **INV-003:** одинаковые поддерживаемые semantic inputs при одной версии генератора дают воспроизводимый результат.
- **INV-004:** illustrative examples ненормативны и не могут молча становиться правилами Core.
- **INV-005:** Core использует generic fields, networks, features, geometry primitives и constraints вместо campaign-specific special cases.
- **INV-006:** существенные архитектурные изменения сначала объясняются и обсуждаются; документация обновляется до реализации.
- **INV-007:** RNG streams адресуются стабильными semantic namespaces и не зависят от порядка выполнения или random draws соседних подсистем.
- **INV-008:** logging, debug export, instrumentation и preview generation не влияют на semantic result.
- **INV-009:** exact procedural replay определяется exact generator version; стабильность generated world между generator versions не гарантируется.
- **INV-010:** каждая stage читает только declared upstream outputs и не мутирует результаты предыдущих stages.
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей stage, а не hidden side effect позднего объекта.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
