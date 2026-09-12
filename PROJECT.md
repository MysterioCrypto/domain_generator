---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-surface-base-fields-v0.1
next_topic: surface-feature-bias-v0.1
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
  - surface-semantic-recipe-v0.1
  - exact-distance-to-water-km-v0.1
  - terrain-slope-derived-v0.1
  - surface-moisture-base-v0.1
  - surface-vegetation-base-v0.1
  - surface-validation-v0.1
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
  surface_base_fields: docs/design/surface-base-fields-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет structural + shaping pipeline. Hydrology покрывает routing, lake/stream classification, directed river topology и canonical runtime water depth. Текущий slice добавляет базовые continuous surface fields moisture и terrestrial vegetation density.

## Карта прогресса простыми словами

```text
[готово] описание карты
[готово] генерация геометрии объектов
[готово] ограничения, где объекты можно размещать
[готово] terrain: поднятия / впадины / хребты / shaping
[готово] hydrology: routing / streams / lakes / RiverNetwork / water_depth
[PR]     базовые moisture + vegetation fields
[потом] explicit surface feature biases
[потом] dependent POI placement
[потом] сборка финального DomainData

[в очереди] GitHub Actions: pytest на push/PR
```

## Surface Base Fields

Normative semantics: `docs/design/surface-base-fields-v0.1.md`.

Runtime:

```text
TerrainState.elevation_m ──→ derived slope_deg ─────────────┐
                                                            │
HydrologyState.water_depth_m ─→ exact distance_to_water_km ─┤
                                                            ↓
world-space coherent moisture noise ─────────────────→ moisture
                                                            │
                                               slope_deg ────┤
                                                            ↓
                                                 vegetation_density
                                                            ↓
                                                      SurfaceState
```

Текущий slice реализует:

- обязательный semantic `surface` recipe в `DomainSpec` и `GenerationPlan`;
- surface recipe включён в semantic plan fingerprint;
- `SurfaceState.moisture` float32 `[0,1]`;
- `SurfaceState.vegetation_density` float32 `[0,1]`;
- canonical water cells определяются только как `water_depth_m > 0`;
- exact physical Euclidean distance-to-water между cell centers;
- no-water domain даёт zero water contribution;
- moisture water-proximity использует exponential decay в километрах;
- moisture environmental variation использует world-space value noise v1 с отдельным surface RNG namespace;
- canonical water получает moisture `1`;
- slope — derived maximum local distance-normalized 8-neighbor gradient;
- terrestrial vegetation density = moisture × slope factor;
- canonical water получает terrestrial vegetation density `0`;
- absolute elevation не вводит hidden climate penalty;
- float64 intermediates и один final float32 cast для canonical fields;
- surface validation выполняет deterministic recomputation;
- terrain и hydrology остаются immutable upstream outputs.

Semantic recipe:

```yaml
surface:
  moisture_base: 0.35
  water_moisture_boost: 0.55
  water_moisture_decay_km: 8.0
  moisture_noise_amplitude: 0.10
  moisture_noise_scale_km: 12.0
  vegetation_slope_zero_deg: 45.0
```

Значения выше — только пример. Hidden defaults отсутствуют.

## Инфраструктурная очередь

Добавить минимальный GitHub Actions CI, не связанный с semantic Core:

```text
push / pull_request
  -> GitHub-hosted Ubuntu runner
  -> install package + test dependencies
  -> pytest
```

Workflow не должен влиять на semantic result, RNG или generator architecture.

## Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

World-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG уже приняты. Runtime implementation остаётся gated до завершения surface semantics.

## Следующий шаг

После принятия этого checkpoint следующий bounded design-вопрос — **Surface Feature Bias v0.1**.

Нужно отдельно зафиксировать:

- какие generic surface operators входят в v0.1 (`moisture_bias`, `vegetation_bias`);
- допустимую geometry (первый кандидат — Area);
- additive/order-independent contribution semantics;
- sampling/RNG namespace для feature parameters;
- момент final clamp относительно base fields и feature contributions;
- validation конфликтов/capability errors;
- отсутствие binary forest semantics.

## Ещё не сделано

- GitHub Actions pytest CI (`push` + `pull_request`);
- explicit surface feature biases;
- lake polygon vectorization / canonical `HydroFeature` materialization;
- physical river width/sub-cell rasterization;
- runoff/discharge/climate model;
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
