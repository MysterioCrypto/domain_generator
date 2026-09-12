---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-terrain-band-ridge-v0.1
next_topic: terrain-shaping-semantics
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
  world_space_noise: docs/design/world-space-value-noise-v1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Семантика final dependent placement принята и документирована, но runtime implementation отложена до появления всех необходимых upstream fields.

Canonical terrain elevation теперь поддерживает два additive structural operator: `AreaGeometry + raise` и `BandGeometry + ridge`.

## Карта прогресса простыми словами

Это high-level представление проекта без внутренних архитектурных деталей:

```text
[готово] описание карты
[готово] генерация геометрии объектов
[готово] ограничения, где объекты можно размещать
[готово] базовое поле высот
[готово] Area -> поднятый регион
[готово] Band -> плавный хребет
[дальше] изменение уже созданного рельефа
[потом] вода
[потом] влажность/растительность
[потом] размещение POI
[потом] сборка финального мира
```

Текущий этап проекта — конец базовой **structural terrain** части и переход к **terrain shaping**: от простого суммирования вкладов высоты к операциям, которые изменяют уже накопленное поле рельефа.

### Terrain baseline

Реализовано:

- runtime `TerrainState.elevation_m`, canonical float32 meters;
- BaseField = `0.0 m`;
- canonical grid adapter и cell-center world mapping;
- каждый terrain feature создаёт отдельный float64 contribution;
- contributions применяются в sorted feature-id order;
- один final cast `float64 -> float32` после additive structural phase;
- terrain validation для causality/shape/dtype/finite/complete feature application.

### Area Raise

Normative semantics: `docs/design/terrain-area-raise-v0.1.md`.

`AreaGeometry + raise(height_m)` даёт constant additive contribution внутри/on area по cell-center inclusion.

### Band Ridge

Normative semantics: `docs/design/terrain-band-ridge-v0.1.md`.

Реализовано:

- nearest point projection каждого cell center на ordered band polyline;
- deterministic earliest-segment tie break;
- normalized `t` по total centerline arc length;
- linear interpolation canonical full-width profile;
- normalized cross-band distance `u = distance / half_width`;
- profile `(1-u)^profile_power` внутри effective band;
- `height_m > 0`, `profile_power > 0`, `roughness in [0,1]`, `roughness_scale_km > 0`;
- roughness деформирует transverse distance, не изменяя centerline peak;
- ridge остаётся additive и суммируется с area/raise.

### World-space coherent noise v1

Normative semantics: `docs/design/world-space-value-noise-v1.md`.

Reusable primitive:

- world-space physical `scale_km`;
- random-access lattice nodes через independent RNG-v1 keys;
- node values не зависят от raster traversal/order;
- cubic smoothstep + bilinear interpolation;
- no hidden scale defaults, octaves или fractal composition;
- golden regression vector зафиксирован в tests.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Приняты world-space candidate lattice, footprint-aware metrics, hard requirements, weighted intrinsic preferences, near-best filtering и isolated deterministic weighted-choice RNG. Implementation остаётся gated до terrain/hydrology/surface state.

## Следующий шаг

Следующий bounded design-вопрос — **terrain shaping semantics v0.1**.

Нужно отдельно определить границу structural additive phase и shaping phase для generic operators вроде `flatten`/`blend`, включая:

- что именно shaping operator читает: BaseField или уже accumulated StructuralElevation;
- deterministic order для noncommutative shaping operators;
- как задаётся target elevation / blend strength / falloff;
- как обнаруживаются несовместимые overlapping shaping regions;
- нужен ли сначала отдельный additive `depress` operator или его разумнее включить в тот же checkpoint;
- validation semantics до hydrology.

До принятия этих правил shaping operators не реализовывать.

## Ещё не сделано

- terrain `depress`/`flatten`/`blend` и shaping phase;
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
