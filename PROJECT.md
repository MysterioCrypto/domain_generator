---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-compiler-registry-minimal-slice
next_topic: first-layout-geometry-vertical-slice
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
  - typed-preset-definition-v0.1
  - in-memory-preset-registry-boundary
  - deterministic-domain-spec-compiler-slice
  - semantic-plan-fingerprint
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

`M2 — Deterministic pipeline` уже содержит полный serialized contract layer Core 0.1, generated JSON Schema snapshots Draft 2020-12, deterministic RNG v1, attempt orchestrator и первый compiler/preset-registry vertical slice.

RNG v1 зафиксирован нормативно в ADR-0010 и реализован через semantic namespaces, BLAKE2b-256 и `xoshiro256**`. Attempt skeleton реализует fixed stage order, early reject, отсутствие hidden retries и deterministic candidate ranking.

Compiler slice теперь добавляет:

- типизированный `PresetDefinition`;
- immutable in-memory `PresetRegistry` boundary с duplicate-id и known-operator checks;
- loader-independent registry API: YAML/file loading намеренно ещё не реализован;
- deterministic `compile_domain_spec()` из `DomainSpec` в immutable `GenerationPlan`;
- сохранение layout/effect ownership параметров;
- fixed/range/one_of overrides с проверкой preset domain;
- перенос sampler recipe в Plan без attempt-specific sampling;
- physical compilation normalized points, anchors и 3x3 domain regions;
- feature-reference и geometry-part compatibility checks;
- rejection unsupported deferred-to-deferred hard dependencies;
- uint64 seed check на compiler boundary для RNG v1;
- canonical `spec_fingerprint` и semantic `plan_fingerprint`, исключающий labels/tags/source provenance;
- hard relation compilation для `near`, `far_from`, `inside`, `outside`, `crosses`, `overlaps`, `adjacent`.

Test presets существуют только внутри tests и не становятся Core content. Production preset YAML ещё не добавлялся.

Soft constraint scoring compilation пока намеренно не реализован: DomainSpec с soft constraint compiler отклоняет явно, потому что точная relation->scoring mapping ещё не была зафиксирована и не должна быть выдумана реализацией.

## Следующий шаг

Подключить первый настоящий layout/geometry vertical slice к уже существующим Plan + RNG + attempt orchestrator. Начать с одной generic geometry family/shape path, достаточной для проверки полного пути `Plan -> LayoutCandidate`, не пытаясь сразу реализовать все terrain/hydrology algorithms.

Перед этим отдельно решить только те детали layout algorithm, которые действительно влияют на deterministic semantics; illustrative mountain/fort examples не превращать в Core rules.

## Ещё не сделано

- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
- реальные layout stage handlers и placement reservation materialization;
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
