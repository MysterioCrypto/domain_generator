---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-hydrology-routing-core-v0.1
next_topic: hydrology-recipe-and-water-extraction
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
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет завершённую базовую цепочку structural + shaping. Текущий slice добавляет первый hydrology runtime слой: deterministic drainage routing поверх canonical elevation.

## Карта прогресса простыми словами

```text
[готово] описание карты
[готово] генерация геометрии объектов
[готово] ограничения, где объекты можно размещать
[готово] базовое поле высот
[готово] поднятия / впадины / хребты
[готово] flatten / shaping уже созданного рельефа
[PR]     куда течёт вода: Priority-Flood + D8 + catchment
[потом] порог ручьёв, реки и озёра
[потом] влажность/растительность
[потом] размещение POI
[потом] сборка финального мира
```

Текущий checkpoint отвечает на вопрос: **куда из каждой клетки уйдёт вода и какую площадь бассейна она собирает**, но пока ещё не объявляет raster streams, реки или озёра canonical world objects.

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

### Hydrology Routing Core

Normative semantics: `docs/design/hydrology-routing-core-v0.1.md`.

Runtime pipeline:

```text
TerrainState.elevation_m
  -> float64 RoutingSurface
  -> Priority-Flood depression conditioning
  -> deterministic D8 receivers
  -> integer upstream-cell accumulation
  -> physical flow_accumulation_km2
  -> HydrologyState
```

Реализовано:

- runtime `HydrologyState`;
- edge cells — open-boundary outlets, не море;
- Priority-Flood не изменяет canonical terrain;
- depression/flat routing получает минимальный representable 1-ULP gradient через `nextafter`;
- D8 использует distance-normalized slope;
- canonical tie-break order: `N, NE, E, SE, S, SW, W, NW`;
- accumulation сначала считается exact integer cell counts, затем один раз переводится в km²;
- routing не использует RNG;
- hydrology validation проверяет формы, dtype, finite values, outlets, strictly-lower receivers и accumulation minimum.

### Почему stream_mask пока отложен

`stream_threshold_km2` влияет на semantic result мира. В текущем `GenerationPlan` нет принятого root hydrology-recipe/settings contract. Поэтому threshold не вводится hidden constant и не передаётся ad-hoc аргументом.

Следующий design checkpoint должен отдельно решить, где живут semantic hydrology parameters, после чего можно materialize stream graph/river extraction.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Приняты world-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG. Runtime implementation остаётся gated до terrain/hydrology/surface states.

## Следующий шаг

После принятия routing core следующий bounded design-вопрос — **hydrology recipe + canonical water extraction**.

Нужно отдельно зафиксировать:

- где в semantic plan хранится `stream_threshold_km2` и будущие hydrology parameters;
- как из `routing_elevation - canonical_elevation` выделяются candidate depressions;
- какие physical thresholds (`area_km2`, `depth_m`, возможно volume) отличают canonical lake от малой routing depression;
- как raster stream cells превращаются в directed vector `RiverNetwork`;
- как формируется canonical `water_depth` без изменения terrain elevation.

## Ещё не сделано

- hydrology semantic recipe/settings contract;
- stream mask / stream graph;
- canonical lakes / water_depth;
- vector RiverNetwork;
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
