---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-terrain-area-raise-v0.1
next_topic: terrain-band-ridge-semantics
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
  - band-layout-generation-v0.1
  - band-width-profile-v0.1
  - band-layout-validation-v0.1
  - area-layout-generation-v0.1
  - area-layout-validation-v0.1
  - area-point-spatial-evaluators-v0.1
  - shapely-geos-boolean-backend-v0.1
  - canonical-region-set-conversion-v0.1
  - placement-reservation-materialization-v0.1
  - canonical-grid-cell-center-adapter-v0.1
  - terrain-state-v0.1
  - terrain-area-raise-v0.1
  - terrain-validation-v0.1
accepted_designs:
  - dependent-placement-site-selection-v0.1
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
  placement_reservations: docs/design/placement-reservation-materialization-v0.1.md
  dependent_placement: docs/design/dependent-placement-site-selection-v0.1.md
  terrain_area_raise: docs/design/terrain-area-raise-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Семантика final dependent placement принята и документирована, но runtime implementation отложена до появления всех необходимых upstream fields.

Теперь добавлен первый реальный numerical world layer: **canonical terrain elevation**.

### Layout + PlacementReservation

- point — deterministic point inside domain;
- corridor — ordered polyline с isolated RNG streams;
- band — centerline + deterministic full-width profile;
- area — simple CCW polygon;
- reservation — canonical `RegionSet` через hard `inside/outside/near/far_from` semantics.

Boolean geometry backend — exact pinned `shapely==2.1.2` / GEOS 3.13.1. Backend objects не входят в serialized contracts.

### Terrain baseline / Area Raise

Normative semantics: `docs/design/terrain-area-raise-v0.1.md`.

Реализовано:

- runtime `TerrainState.elevation_m`;
- canonical elevation shape `(rows, columns)`, dtype `float32`, unit meters;
- BaseField = `0.0 m`, где zero datum не означает water/sea;
- canonical grid adapter: world origin southwest, raster row 0 north;
- cell-center mapping `x=(col+0.5)*cell_size`, `y=height-(row+0.5)*cell_size`;
- `AreaGeometry` rasterization по cell-center inside/on polygon;
- первый terrain operator `raise` с единственным effect parameter `height_m > 0`;
- terrain parameter RNG namespace `terrain / feature-id / parameter / sample`;
- отдельный float64 contribution на feature;
- additive accumulation в sorted feature-id order;
- один final cast `float64 -> float32` после structural accumulation;
- `CandidateState.terrain` как downstream runtime state;
- terrain validation: layout causality, attempt match, shape, dtype, finite values и complete feature application;
- unsupported terrain operator/geometry не игнорируется и даёт capability error.

Не реализованы shaping operators и naturalistic falloff/noise: первый slice намеренно даёт резкую area mask.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Приняты world-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG. Implementation остаётся gated до terrain/hydrology/surface state.

## Следующий шаг

Следующий bounded design-вопрос — **terrain band/ridge semantics v0.1**: как `BandGeometry.centerline + width_profile` превращается в smooth additive elevation contribution.

Нужно отдельно определить:

- distance-to-centerline и local width interpolation;
- normalized cross-band profile/falloff;
- `height_m`/ridge profile parameters;
- поведение за пределами band width;
- coherent perturbation/noise boundary и его RNG namespace;
- clipping к raster domain;
- как сохранить additive/order-independent terrain semantics.

До принятия этих правил `ridge` operator не реализовывать.

## Ещё не сделано

- terrain band/ridge/depress/flatten/blend/noise operators;
- hydrology generator;
- surface generator;
- dependent placement final point selection runtime;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators;
- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
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
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей стадии, а не hidden side effect позднего объекта.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
