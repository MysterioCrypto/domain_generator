---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-dependent-placement-candidate-filtering-v0.1
next_topic: dependent-placement-preference-selection-v0.1
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
  - surface-feature-bias-v0.1
  - dependent-placement-site-metrics-v0.1
  - dependent-placement-candidate-filtering-v0.1
accepted_designs:
  - dependent-placement-site-selection-v0.1
implemented_infrastructure:
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
  dependent_placement_site_metrics: docs/design/dependent-placement-site-metrics-v0.1.md
  dependent_placement_candidate_filtering: docs/design/dependent-placement-candidate-filtering-v0.1.md
  terrain_area_raise: docs/design/terrain-area-raise-v0.1.md
  terrain_band_ridge: docs/design/terrain-band-ridge-v0.1.md
  terrain_structural_flatten: docs/design/terrain-structural-flatten-v0.1.md
  world_space_noise: docs/design/world-space-value-noise-v1.md
  hydrology_routing: docs/design/hydrology-routing-core-v0.1.md
  hydrology_classification: docs/design/hydrology-classification-v0.1.md
  hydrology_network_waterdepth: docs/design/hydrology-network-waterdepth-v0.1.md
  surface_base_fields: docs/design/surface-base-fields-v0.1.md
  surface_feature_bias: docs/design/surface-feature-bias-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое setting-agnostic процедурное ядро генерации ограниченных пространственных регионов с управляемой случайностью. Пользователь или внешний consumer описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

`Domain` означает generic bounded spatial region — кусок мира/карты, генерируемый как единое целое. Термин не несёт специальной лоровой семантики.

## Граница продукта

`domain_generator` является самостоятельным Core. Конкретные миры, кампании, жанры, игровые системы и приложения используют его как внешний consumer.

```text
world / setting / application
          ↓
   adapter / presets
          ↓
      DomainSpec
          ↓
   domain_generator
          ↓
      DomainData
          ↓
 renderer / exporter / integration
```

В Core допустимы generic concepts: geometry, terrain, hydrology, fields, networks, constraints, procedural features и placement rules.

В Core не входят setting identity, campaign lore, game-system rules, setting-specific preset catalogs, UI или presentation logic.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет structural + shaping pipeline. Hydrology покрывает routing, lake/stream classification, directed river topology и canonical runtime water depth. Surface покрывает base moisture/vegetation и explicit area feature biases. Dependent placement теперь покрывает site metrics и deterministic candidate filtering до множества valid sites.

## Карта прогресса простыми словами

```text
[готово] описание region/domain
[готово] генерация геометрии объектов
[готово] ограничения размещения
[готово] terrain: поднятия / впадины / хребты / shaping
[готово] hydrology: routing / streams / lakes / RiverNetwork / water_depth
[готово] базовые moisture + vegetation fields
[готово] explicit surface feature biases
[готово] dependent-placement site metrics
[текущий PR] rotated candidate lattice + reservation filtering + hard requirements
[следом] preference scoring + near-best + weighted final selection + PlacementState
[потом] сборка финального DomainData

[готово] GitHub Actions: pytest на push/PR
```

## Setting Decoupling Cleanup — complete

- `Domain` = generic bounded spatial region;
- Core не знает конкретный setting/campaign/game system;
- setting-specific presets, adapters и world data находятся вне базового Core;
- generic examples не создают setting dependency.

## Surface — complete baseline

Normative semantics:

- `docs/design/surface-base-fields-v0.1.md`;
- `docs/design/surface-feature-bias-v0.1.md`.

Canonical runtime fields:

- `SurfaceState.moisture` float32 `[0,1]`;
- `SurfaceState.vegetation_density` float32 `[0,1]`;
- generic area operators `moisture_bias` / `vegetation_bias`;
- canonical water precedence after surface contributions.

## Dependent Placement Site Metrics v0.1 — complete

Normative semantics: `docs/design/dependent-placement-site-metrics-v0.1.md`.

Реализовано:

- canonical world-point -> containing raster cell mapping;
- internal vertical boundary tie -> east;
- internal horizontal boundary tie -> north;
- north/east external boundary clamp to final in-domain cell;
- circular footprint support через cell-center inclusion;
- fallback to containing cell, если footprint не содержит raster centers;
- attempt-global `SiteMetricContext` с precomputed slope и exact distance-to-water;
- 8 generic metrics;
- float64 aggregation;
- no-water sentinel `distance_to_water = +inf`;
- explicit capability errors;
- no RNG and no upstream mutation.

## Dependent Placement Candidate Filtering v0.1 — current checkpoint

Normative semantics: `docs/design/dependent-placement-candidate-filtering-v0.1.md`.

Реализовано:

- semantic `candidate_spacing_km` через standard placement parameter sampling namespace;
- deterministic square lattice с независимыми `rotation` и `phase` streams;
- `rotation ∈ [0, pi/2)`;
- два phase draws в rotated coordinates;
- finite lattice enumeration через inverse-rotated domain bounds;
- filtering по domain и `PlacementReservation.allowed_region`;
- RegionSet `covers` semantics для inside/on placement;
- exact duplicate removal и canonical sort `(x_km, y_km)`;
- reuse `SiteMetricContext` для всех candidates;
- hard evaluators `less_or_equal` / `greater_or_equal`;
- empty reservation/valid set без fallback и hidden retry;
- no preference scoring и no final selection.

## Dependent placement site selection — accepted design, partially implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Уже реализовано:

```text
PlacementReservation
-> candidate lattice
-> reservation containment
-> canonical candidate order
-> site metrics
-> hard requirements
-> valid sites
```

Остаётся:

```text
valid sites
-> intrinsic preferences
-> suitability
-> near-best
-> deterministic weighted selection
-> PlacementState.final_points
-> placement validation / attempt rejection
```

## Следующий шаг

Следующий bounded implementation slice — **Dependent Placement Preference Selection v0.1**.

Он должен реализовать принятую семантику:

- `maximize`, `minimize`, `preferred_range`;
- normalized preference scores `[0,1]`;
- weighted composite suitability;
- semantic `near_best_delta`;
- canonical near-best set;
- deterministic weighted choice через `("feature", id, "site-selection") / "weighted-choice"`;
- runtime `PlacementState.final_points`;
- rejection attempt при empty valid-site set;
- placement validation.

## Ещё не сделано

- preference scoring / near-best / weighted final selection;
- `PlacementState.final_points`;
- placement-stage validation/rejection semantics;
- lake polygon vectorization / canonical `HydroFeature` materialization;
- physical river width/sub-cell rasterization;
- runoff/discharge/climate model;
- standalone terrain `blend` operator;
- advanced terrain shaping/erosion;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators;
- YAML/file preset loader и production generic preset catalog;
- soft constraint scoring compilation;
- DomainData assembler/export bundle;
- renderer.

## Инварианты

- **INV-001:** Core независим от конкретных сеттингов, кампаний, игровых систем, LLM/agent tooling, GitHub/CI orchestration, UI и renderer-ов; setting-specific adapters/content находятся за границей Core.
- **INV-002:** `DomainSpec` описывает намерение; `GenerationPlan` — resolved recipe; `DomainData` — итоговый generated region.
- **INV-003:** одинаковые поддерживаемые semantic inputs при одной версии генератора дают воспроизводимый результат.
- **INV-004:** illustrative examples ненормативны и не могут молча становиться правилами Core.
- **INV-005:** Core использует generic fields, networks, features, geometry primitives и constraints вместо scenario/setting-specific special cases.
- **INV-006:** существенные архитектурные изменения сначала объясняются и обсуждаются; документация обновляется до реализации.
- **INV-007:** RNG streams адресуются стабильными semantic namespaces и не зависят от порядка выполнения или random draws соседних подсистем.
- **INV-008:** logging, debug export, instrumentation и preview generation не влияют на semantic result.
- **INV-009:** exact procedural replay определяется exact generator version; стабильность generated region между generator versions не гарантируется.
- **INV-010:** каждая stage читает только declared upstream outputs и не мутирует результаты предыдущих stages.
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей стадии, а не hidden side effect позднего объекта.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
