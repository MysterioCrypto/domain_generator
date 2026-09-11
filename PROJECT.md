---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-attempt-pipeline-skeleton
next_topic: compiler-and-preset-registry-minimal-slice
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
  - deterministic-rng-protocol-v1
  - xoshiro256starstar-v1
  - rng-golden-and-isolation-tests
  - runtime-candidate-state-v0.1
  - attempt-pipeline-skeleton-v0.1
  - deterministic-candidate-ranking-v0.1
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

`M2 — Deterministic pipeline` уже содержит полный serialized contract layer Core 0.1, generated JSON Schema snapshots Draft 2020-12, deterministic RNG v1 и минимальный runtime attempt orchestrator.

В `src/domain_generator` реализованы Pydantic v2-модели основных contracts и geometry/value types:

- `DomainSpec`;
- `GenerationPlan`;
- `LayoutCandidate` / `PlacementReservation`;
- `ValidationResult`;
- `GenerationConfig`;
- `DomainData`;
- point/corridor/band/area/RegionSet geometry.

Для шести root serialized contracts генерируются и коммитятся JSON Schema snapshots. JSON Schema является interchange/documentation layer, а cross-field правила из `model_validator` остаются ответственностью Python Core models.

RNG v1 зафиксирован нормативно в ADR-0010 и реализован без зависимости от `random.Random` или NumPy RNG:

- semantic `RngKey = attempt_index + stage + scope + purpose`;
- canonical length-prefixed binary namespace encoding;
- BLAKE2b-256 с personalization `dg-rng-v1`;
- 256-bit state `xoshiro256**`;
- `next_u64`, `uniform01`, `uniform`, unbiased inclusive `integer_uniform`, `choice`;
- independent streams per logical random task;
- golden vectors и isolation/order-independence tests.

`root_seed` на RNG boundary должен быть unsigned uint64. До compiler implementation это проверяет `RngFactory`; compiler позже должен отклонять неподдерживаемый seed до generation.

Минимальный attempt/pipeline skeleton реализует уже принятый M1 lifecycle без реальных terrain/hydrology algorithms:

- фиксированный порядок `layout -> terrain -> hydrology -> surface -> placement -> final`;
- mutable runtime `CandidateState`, отдельный от serialized contracts;
- один `AttemptContext` с immutable Plan, `attempt_index` и `RngFactory`;
- каждый stage handler вызывается не более одного раза в attempt;
- первый failed engine invariant или hard constraint завершает attempt немедленно;
- завершённый valid attempt становится runtime `DomainCandidate`;
- outer loop идёт по `attempt_index` по возрастанию, собирает до `target_valid_candidates` либо исчерпания budget;
- если есть хотя бы один valid candidate, выбирается лучший по `worst_effective_violation`, затем `weighted_mean_score`, затем меньшему `attempt_index`;
- если valid candidates нет, выбрасывается runtime `GenerationFailure`;
- observability settings orchestrator не читает и на semantic result они не влияют.

Stage handlers пока synthetic/injected: реальных layout/terrain/hydrology/surface/placement implementations ещё нет.

## Следующий шаг

Перейти к минимальному compiler/preset registry slice: определить исполнимый registry boundary, несколько generic preset definitions для contract tests и compilation `DomainSpec -> GenerationPlan` без procedural geometry generation.

После compiler можно подключить первый настоящий layout/geometry vertical slice к уже существующему attempt orchestrator.

## Ещё не сделано

- compiler и preset registry implementation;
- реальные stage handlers;
- geometry/grid operators;
- terrain/hydrology/surface/placement generators;
- DomainData assembler/export bundle;
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
