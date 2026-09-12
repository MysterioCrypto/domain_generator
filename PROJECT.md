---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-hydrology-classification-v0.1
next_topic: hydrology-river-network-and-water-depth
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
  - hydrology-validation-v0.1
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
  hydrology_routing: docs/design/hydrology-routing-core-v0.1.md
  hydrology_classification: docs/design/hydrology-classification-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет завершённую базовую цепочку structural + shaping. Hydrology теперь покрывает deterministic drainage routing, physical depression fill и первую классификацию streams/lake candidates.

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
[потом] vector RiverNetwork + canonical water_depth/lakes
[потом] влажность/растительность
[потом] размещение POI
[потом] сборка финального мира
```

Текущий checkpoint отвечает на два дополнительных вопроса: **какие raster cells считаются stream cells** и **какие заполненные депрессии достаточно велики/глубоки, чтобы сохраниться как lake candidates**. Он ещё не материализует vector river network, final lake feature geometry или canonical `water_depth`.

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
  -> HydrologyState
```

Реализовано:

- runtime `HydrologyState`;
- edge cells — open-boundary outlets, не море;
- Priority-Flood не изменяет canonical terrain;
- physical fill surface отделена от routing-only ULP gradient;
- depression/flat routing получает минимальный representable 1-ULP gradient через `nextafter`;
- D8 использует distance-normalized slope;
- canonical tie-break order: `N, NE, E, SE, S, SW, W, NW`;
- accumulation сначала считается exact integer cell counts, затем один раз переводится в km²;
- обязательный semantic hydrology recipe живёт в `DomainSpec`/`GenerationPlan` и входит в semantic plan fingerprint;
- `stream_mask = flow_accumulation_km2 >= stream_threshold_km2`;
- lake candidate mask строится только из physical fill depth, не из routing ULP artifacts;
- lake components используют 8-connectivity, canonical row-major cell order и deterministic candidate order;
- lake candidates фильтруются по physical `area_km2` и `max_depth_m`;
- routing/classification не используют RNG;
- hydrology validation проверяет routing, fill, stream classification и lake candidate consistency.

### Hydrology recipe

```yaml
hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
```

Это semantic world input, а не execution setting. Hidden defaults и ad-hoc runtime arguments для этих thresholds запрещены. Изменение recipe меняет semantic plan fingerprint.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Приняты world-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG. Runtime implementation остаётся gated до terrain/hydrology/surface states.

## Следующий шаг

Следующий bounded design-вопрос — **vector RiverNetwork + canonical water representation v0.1**.

Нужно отдельно решить до реализации:

- как stream raster cells группируются/трассируются в directed river reaches;
- как junctions/outlets становятся canonical network nodes;
- как river geometry переводится из raster flow path в world-space polyline без renderer-specific smoothing;
- как lake candidates превращаются в canonical lake geometry/features;
- как river/lake representation формирует canonical `water_depth` field;
- как streams входят в lakes и выходят из них, не ломая directed topology;
- какие hydrology outputs остаются runtime intermediates, а какие попадают в `DomainData`.

## Ещё не сделано

- vector RiverNetwork;
- canonical lakes и lake feature geometry;
- canonical `water_depth`;
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
