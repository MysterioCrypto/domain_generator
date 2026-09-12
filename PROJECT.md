---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-corridor-layout-v0.1
next_topic: band-layout-semantics
completed:
  - M0-project-foundation
  - M1-data-contracts
implemented_m2:
  - minimal-python-package
  - serialized-contract-layer-v0.1
  - generated-json-schema-v0.1
  - deterministic-rng-protocol-v1
  - xoshiro256starstar-v1
  - attempt-pipeline-skeleton-v0.1
  - deterministic-candidate-ranking-v0.1
  - typed-preset-definition-v0.1
  - in-memory-preset-registry-boundary
  - deterministic-domain-spec-compiler-slice
  - semantic-plan-fingerprint
  - point-layout-generation-v0.1
  - point-layout-validation-v0.1
  - generic-resolved-parameter-sampling-v0.1
  - triangular-sampler-rng-v1-mapping
  - corridor-layout-generation-v0.1
  - corridor-layout-validation-v0.1
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

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Уже реализованы serialized Pydantic contracts, JSON Schema snapshots, deterministic RNG v1, attempt orchestrator, deterministic candidate ranking, compiler/preset-registry boundary и первые реальные layout paths.

### Point layout

Generic point layout реализует `GenerationPlan -> LayoutCandidate` для `shape=point` с независимым feature RNG stream, domain-bound validation и базовыми hard point/rectangle constraints.

### Corridor layout

Принятый алгоритм зафиксирован в `docs/design/corridor-layout-v0.1.md` и реализует:

- canonical corridor как ordered polyline;
- обязательные layout parameters `control_point_count` и `curvature`;
- независимые RNG streams для start, end и control points;
- отдельные parameter sampling streams;
- internal control points на равномерных `t` вдоль start→end;
- signed perpendicular displacement через envelope `4*t*(1-t)`;
- ограничение displacement доступным расстоянием до rectangular domain boundary без clamp/retry;
- explicit degenerate-corridor rejection через layout engine invariant;
- resolution `start`, `end`, `center` (50% arc length), `whole`;
- point↔corridor minimum-distance hard evaluation;
- mixed point+corridor deterministic geometry generation.

### Parameter sampling

Runtime sampler поддерживает `fixed`, float `uniform`, inclusive `integer_uniform`, `categorical` и float `triangular`. Triangular mapping использует зафиксированную inverse-CDF формулу и считается частью RNG v1 semantics.

Никакого constraint-aware steering или hidden retries нет: geometry сначала materialize-ится, затем supported hard constraints могут отклонить весь attempt.

## Следующий шаг

Следующий bounded geometry path — `band`. До реализации нужно отдельно зафиксировать: как band переиспользует corridor centerline semantics, как sample-ится full-width profile и какие profile parameters входят в Core 0.1.

## Ещё не сделано

- band/area layout generation;
- placement reservation materialization и RegionSet boolean operations;
- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
- terrain/hydrology/surface/dependent-placement generators;
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
