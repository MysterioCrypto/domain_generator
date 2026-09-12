---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-terrain-structural-flatten-v0.1
next_topic: hydrology-baseline-semantics
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
  - world-space-value-noise-v1
  - terrain-band-ridge-v0.1
  - terrain-area-depress-v0.1
  - terrain-flatten-shaping-v0.1
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
  terrain_band_ridge: docs/design/terrain-band-ridge-v0.1.md
  terrain_structural_flatten: docs/design/terrain-structural-flatten-v0.1.md
  world_space_noise: docs/design/world-space-value-noise-v1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain теперь имеет явные structural и shaping phases.

## Карта прогресса простыми словами

```text
[готово] описание карты
[готово] генерация геометрии объектов
[готово] ограничения, где объекты можно размещать
[готово] базовое поле высот
[готово] Area -> поднятый регион
[готово] Band -> плавный хребет
[PR]     Area -> впадина + flatten/shaping уже созданного рельефа
[потом] вода
[потом] влажность/растительность
[потом] размещение POI
[потом] сборка финального мира
```

Текущий checkpoint завершает базовую terrain-модель: сначала structural contributions строят поле высот, затем shaping может локально изменить уже накопленный рельеф. После принятия этого PR следующий крупный слой — hydrology.

### Terrain pipeline

```text
BaseField = 0 m
  + Area/raise
  + Area/depress
  + Band/ridge
  = StructuralElevation (float64)
  -> frozen structural snapshot
  -> Area/flatten
  = CanonicalElevation
  -> float32
  = TerrainState.elevation_m
```

Structural contributions применяются deterministic order по `feature.id`; shaping operators читают один и тот же frozen StructuralElevation snapshot.

### Area Raise / Depress

- `raise(height_m > 0)` добавляет положительную высоту внутри Area;
- `depress(depth_m > 0)` добавляет отрицательный contribution `-depth_m`;
- оба используют canonical cell-center rasterization;
- depress сам по себе не означает воду или озеро.

### Band Ridge

Normative semantics: `docs/design/terrain-band-ridge-v0.1.md`.

Band/ridge использует distance-to-centerline, arc-length width interpolation, power falloff и optional world-space coherent roughness. Он остаётся additive structural contribution.

### Flatten shaping

Normative semantics: `docs/design/terrain-structural-flatten-v0.1.md`.

`Area + flatten(target_elevation_m, blend_width_km)`:

- читает frozen StructuralElevation;
- задаёт absolute target elevation;
- blend происходит только внутрь Area;
- boundary имеет shaping weight 0;
- `blend_width_km=0` даёт полный flatten внутри;
- positive-width blend использует linear `w = clamp(distance_to_boundary / blend_width, 0, 1)`;
- два flatten region с positive-area interior overlap делают attempt invalid;
- boundary-only touching разрешён;
- conflict определяется в world-vector geometry, не raster cells;
- никакого implicit shaping priority/order нет.

### World-space coherent noise v1

Normative semantics: `docs/design/world-space-value-noise-v1.md`.

Reusable random-access coherent value noise остаётся independent primitive и не зависит от raster traversal order.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Приняты world-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG. Runtime implementation остаётся gated до terrain/hydrology/surface states.

## Следующий шаг

После принятия текущего terrain checkpoint следующий bounded design-вопрос — **hydrology baseline v0.1**.

Нужно формализовать первый реализуемый vertical slice уже принятой цепочки:

```text
CanonicalElevation
-> routing surface
-> D8 flow direction
-> flow accumulation
-> streams / outlets
-> canonical water result
```

До реализации нужно отдельно зафиксировать depression conditioning, edge outlets, D8 tie-breaks, physical catchment units и минимальную границу между derived routing data и canonical hydrology output.

## Ещё не сделано

- hydrology generator;
- surface generator;
- dependent placement final point selection runtime;
- standalone terrain `blend` operator;
- advanced terrain shaping/erosion;
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
