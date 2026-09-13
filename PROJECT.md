---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-domain-data-assembler-design-v0.1
next_topic: domain-data-assembler-implementation-v0.1
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
  - dependent-placement-preference-scoring-v0.1
  - dependent-placement-near-best-selection-v0.1
  - placement-state-v0.1
  - placement-validation-v0.1
  - final-validation-hard-v0.1
  - final-neutral-ranking-v0.1
  - soft-constraint-compilation-v0.1
  - soft-constraint-scoring-v0.1
  - final-soft-ranking-v0.1
  - hydrofeature-lake-materialization-v0.1
accepted_designs:
  - dependent-placement-site-selection-v0.1
  - end-to-end-runtime-bundle-v0.1
  - final-validation-hard-v0.1
  - soft-constraint-compilation-scoring-v0.1
  - hydrofeature-lake-materialization-v0.1
  - domain-data-assembler-v0.1
implemented_infrastructure:
  - github-actions-pytest-ci-on-push-and-pull-request
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
  runtime_bundle: docs/design/end-to-end-runtime-bundle-v0.1.md
  final_validation_hard: docs/design/final-validation-hard-v0.1.md
  soft_constraint_scoring: docs/design/soft-constraint-compilation-scoring-v0.1.md
  hydrofeature_lake_materialization: docs/design/hydrofeature-lake-materialization-v0.1.md
  domain_data_assembler: docs/design/domain-data-assembler-v0.1.md
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

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет structural + shaping pipeline. Hydrology покрывает routing, lake/stream classification, directed river topology, canonical runtime water depth и exact semantic lake materialization. Surface покрывает base moisture/vegetation и explicit area feature biases. Dependent point placement реализован полностью. Final Validation имеет production hard gate и полный user-soft global ranking для поддерживаемых canonical spatial measurements.

PR #34 `HydroFeature / Lake Materialization v0.1` принят и merged в `main` commit `d9c6145f6e49df351fb86372f05ffc6f953ea85b`.

Следующая принятая архитектурная граница — `DomainData Assembler v0.1`; runtime implementation ещё не выполнен.

## Карта прогресса простыми словами

```text
[готово] описание region/domain
[готово] генерация геометрии объектов
[готово] ограничения размещения
[готово] terrain: поднятия / впадины / хребты / shaping
[готово] hydrology: routing / streams / lakes / RiverNetwork / water_depth
[готово] semantic HydroFeature для lakes
[готово] базовые moisture + vegetation fields
[готово] explicit surface feature biases
[готово] dependent-placement site metrics
[готово] candidate lattice + reservation filtering + hard requirements
[готово] preference scoring + near-best + weighted final selection + PlacementState
[готово] Final Validation hard gate
[готово] soft constraint compilation + scoring + final ranking
[принято] end-to-end runtime / bundle architecture
[принято] DomainData Assembler v0.1 design
[следом] DomainData Assembler implementation v0.1
[потом] DomainBundle Export
[потом] Technical Renderer
[потом] CLI/Python entrypoint + local/remote adapters

[готово] GitHub Actions: pytest на push/PR
```

## End-to-End Runtime & Bundle Architecture v0.1 — accepted

Normative semantics: `docs/design/end-to-end-runtime-bundle-v0.1.md`.

Ключевые решения:

- Core — один Python package; stages вызываются как functions в одном process;
- local и remote execution используют один canonical generation entrypoint;
- canonical persisted rasters — `fields/*.npy`;
- `domain.json` хранит structured metadata/features/networks/field descriptors;
- assembler не делает IO и не использует RNG;
- exporter физически пишет bundle;
- technical renderer и artistic presentation downstream и не меняют world state;
- exact supported semantic inputs + exact generator/RNG version должны быть reproducible между local и remote execution.

Reference output boundary:

```text
DomainBundle
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
  preview/        # optional, non-canonical
  debug/          # optional, non-canonical
```

## Final Validation v0.1 — hard + soft complete

Normative hard semantics: `docs/design/final-validation-hard-v0.1.md`.
Normative soft semantics: `docs/design/soft-constraint-compilation-scoring-v0.1.md`.

Final Validation:

- наблюдает complete upstream state без mutation;
- повторно оценивает hard constraints по final geometry;
- оценивает soft constraints через тот же canonical spatial measurement boundary;
- выдаёт deterministic ranking;
- не использует RNG/IO и ничего не исправляет.

## HydroFeature / Lake Materialization v0.1 — accepted / implemented / merged PR #34

Normative semantics: `docs/design/hydrofeature-lake-materialization-v0.1.md`.

Реализовано:

```text
LakeCandidate.cells
→ exact world-space cell squares
→ exact polygonal union
→ canonical RegionSet
→ HydroFeature
```

- `HydroFeature.geometry` — `RegionSet`;
- holes и D8 diagonal multipart geometry сохраняются точно;
- `lake_feature_id()` централизует protocol `lake-0001`, `lake-0002`, ...;
- `LakeProperties` содержит `max_depth_m`;
- `HydrologyState` содержит готовые `lake_features`;
- river lake references валидируются против materialized features;
- schema snapshot синхронизирован;
- финальный suite PR #34: `266 passed`.

## DomainData Assembler v0.1 — accepted design

Normative semantics: `docs/design/domain-data-assembler-v0.1.md`.

Принята conceptual граница:

```text
DomainSpec
GenerationPlan
GenerationConfig
selected DomainCandidate
        ↓
DomainData Assembler
        ↓
DomainAssembly
  data: DomainData
  field_payloads:
    elevation
    water_depth
    moisture
    vegetation_density
```

Ключевые решения:

- assembler получает выбранный final-valid candidate и не занимается ranking/selection;
- spec↔plan provenance обязательно проверяется;
- `DomainSpec.label` сохраняется в `DomainData.identity`;
- generation-config fingerprint включает version + semantic config и исключает observability;
- specified final geometry берётся только из layout/placement results;
- hydrology lakes переносятся как уже готовые `HydroFeature`;
- generated lake namespace `^lake-[0-9]{4,}$` зарезервирован от user feature IDs;
- duplicate semantic feature IDs запрещены, silent overwrite невозможен;
- `rivers` network присутствует canonical всегда;
- canonical fields фиксированы: elevation, water_depth, moisture, vegetation_density;
- canonical payload arrays должны быть exact float32 + expected shape;
- assembler создаёт independent read-only copies payloads;
- validation summary берётся из уже успешного final validation;
- assembler не использует RNG, IO, renderer, reroll, re-ranking или regeneration.

## Следующий bounded checkpoint

`DomainData Assembler implementation v0.1`.

После него:

```text
DomainBundle Export v0.1
→ Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

## Ещё не сделано

- DomainData Assembler implementation;
- DomainBundle exporter/manifest/atomic-write semantics;
- technical renderer;
- canonical CLI/application entrypoint;
- local model skill/adapter;
- remote generation GitHub workflow;
- physical river width/sub-cell rasterization;
- runoff/discharge/climate model;
- standalone terrain `blend` operator;
- advanced terrain shaping/erosion;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators;
- YAML/file preset loader и production generic preset catalog.

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
