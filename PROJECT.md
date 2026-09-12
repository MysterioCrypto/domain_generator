---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-hydrology-network-waterdepth-v0.1
next_topic: surface-moisture-vegetation-semantics
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
  - terrain-area-depress-v0.1
  - world-space-value-noise-v1
  - terrain-band-ridge-v0.1
  - terrain-flatten-shaping-v0.1
  - terrain-validation-v0.1
  - hydrology-state-v0.1
  - priority-flood-routing-v0.1
  - deterministic-d8-v0.1
  - catchment-accumulation-km2-v0.1
  - hydrology-semantic-recipe-v0.1
  - physical-fill-surface-v0.1
  - stream-mask-classification-v0.1
  - lake-candidate-classification-v0.1
  - river-network-extraction-v0.1
  - canonical-water-depth-v0.1
  - hydrology-validation-v0.1
accepted_designs:
  - dependent-placement-site-selection-v0.1
infrastructure_queue:
  - github-actions-pytest-ci-on-push-and-pull-request
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
  hydrology_routing: docs/design/hydrology-routing-core-v0.1.md
  hydrology_classification: docs/design/hydrology-classification-v0.1.md
  hydrology_network_waterdepth: docs/design/hydrology-network-waterdepth-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет завершённую базовую цепочку structural + shaping. Hydrology теперь покрывает routing, physical depression fill, stream/lake classification, directed river topology и canonical runtime water depth.

## Карта прогресса простыми словами

```text
[готово] описание карты
[готово] генерация геометрии объектов
[готово] ограничения, где объекты можно размещать
[готово] базовое поле высот
[готово] поднятия / впадины / хребты
[готово] flatten / shaping уже созданного рельефа
[готово] куда течёт вода: Priority-Flood + D8 + catchment
[готово] raster stream mask + физические lake candidates
[готово] directed RiverNetwork + canonical water_depth
[в очереди] GitHub Actions: pytest на push/PR
[потом] влажность/растительность
[потом] размещение POI
[потом] сборка финального мира
```

Текущий hydrology checkpoint отвечает на вопросы: **как raster stream paths сжимаются в directed river graph** и **какая canonical глубина воды находится в каждой raster cell**. Lake polygon/HydroFeature materialization и physical river width остаются отдельными будущими задачами.

### Terrain pipeline

```text
BaseField = 0 m
  + Area/raise
  + Area/depress
  + Band/ridge
  = StructuralElevation
  -> Area/flatten shaping
  = CanonicalElevation
  -> TerrainState.elevation_m
```

Hydrology читает этот canonical terrain только как upstream input и не мутирует его.

### Hydrology pipeline

Normative routing semantics: `docs/design/hydrology-routing-core-v0.1.md`.

Normative classification semantics: `docs/design/hydrology-classification-v0.1.md`.

Normative network/water semantics: `docs/design/hydrology-network-waterdepth-v0.1.md`.

Runtime pipeline:

```text
TerrainState.elevation_m
  -> Priority-Flood
       ├─ physical fill_elevation_m
       └─ routing_elevation_m with minimal routing-only gradient
  -> deterministic D8 receivers
  -> integer upstream-cell accumulation
  -> physical flow_accumulation_km2
       └─ threshold -> stream_mask
  -> physical depression depth = fill_elevation_m - terrain.elevation_m
       -> 8-connected components
       -> area/depth thresholds
       -> lake_candidates
  -> visible stream topology
       -> source / confluence / domain_outlet / lake_inflow / lake_outlet
       -> directed RiverNetwork
  -> accepted lake depth + explicit catchment river-depth proxy
       -> canonical runtime water_depth_m float32
  -> HydrologyState
```

Реализовано:

- stable accepted-lake ids `lake-0001...` для river-node references;
- accepted lakes suppress internal visible river segments;
- visible indegree учитывает ordinary upstream river edges и lake-outlet transitions;
- raster chains deterministically compress into existing `RiverNetwork` nodes/segments;
- domain outlets лежат на фактической границе domain;
- corner outlet precedence: north, east, south, west;
- segment centerlines используют world-space cell centers без renderer smoothing;
- segment catchment property берётся из downstream raster accumulation по фиксированной semantics;
- два обязательных semantic river-depth proxy parameters добавлены в DomainSpec/GenerationPlan;
- accepted lake cells получают depth `fill - terrain`;
- stream cells вне accepted lakes получают explicit catchment-based depth proxy;
- остальные cells получают zero water depth;
- canonical runtime `water_depth_m` имеет dtype float32 после одного final cast;
- river topology/water generation не используют RNG;
- validation deterministic recomputation проверяет network и water-depth consistency.

### Hydrology recipe

```yaml
hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
  river_depth_at_threshold_m: 0.5
  river_depth_exponent: 0.30
```

Все значения — semantic world inputs, а не execution settings. Hidden defaults и ad-hoc runtime arguments запрещены. Изменение recipe меняет semantic plan fingerprint.

River depth proxy:

```text
D = river_depth_at_threshold_m
    * (flow_accumulation_km2 / stream_threshold_km2)
      ** river_depth_exponent
```

Это deterministic proxy, не rainfall/runoff/discharge simulation.

### Инфраструктурная очередь

Добавить минимальный GitHub Actions CI, не связанный с semantic Core:

```text
push / pull_request
  -> GitHub-hosted Ubuntu runner
  -> install package + test dependencies
  -> pytest
```

Цель — автоматически подтверждать полный regression suite на каждом PR/push и больше не зависеть от доступности локального execution-container. На semantic result, RNG и generator architecture этот workflow влиять не должен.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Приняты world-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG. Runtime implementation остаётся gated до terrain/hydrology/surface states.

## Следующий шаг

Следующий bounded design-вопрос — **surface moisture + vegetation numerical semantics v0.1**.

Нужно зафиксировать до реализации:

- canonical runtime `SurfaceState`;
- exact moisture baseline и диапазон `[0,1]`;
- deterministic water-proximity contribution из canonical hydrology;
- elevation/slope penalties;
- generic world-space environmental noise semantics;
- vegetation potential и vegetation-density semantics;
- explicit surface feature biases;
- validation и causal boundary: surface читает terrain + hydrology, не мутирует их.

## Ещё не сделано

- GitHub Actions pytest CI (`push` + `pull_request`);
- lake polygon vectorization / canonical `HydroFeature` materialization;
- physical river width/sub-cell rasterization;
- runoff/discharge/climate model;
- surface generator;
- dependent placement final point selection runtime;
- standalone terrain `blend` operator;
- advanced terrain shaping/erosion;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators;
- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
- DomainData assembler/export bundle;
- renderer.

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
