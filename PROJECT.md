---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-technical-renderer-v0.1-merged
next_topic: canonical-cli-python-entrypoint-design
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
  - corridor-layout-generation-v0.1
  - band-layout-generation-v0.1
  - area-layout-generation-v0.1
  - shapely-geos-boolean-backend-v0.1
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
  - domain-data-assembler-v0.1
  - domain-bundle-export-v0.1
  - bundle-manifest-v0.1
  - technical-renderer-v0.1
accepted_designs:
  - dependent-placement-site-selection-v0.1
  - end-to-end-runtime-bundle-v0.1
  - final-validation-hard-v0.1
  - soft-constraint-compilation-scoring-v0.1
  - hydrofeature-lake-materialization-v0.1
  - domain-data-assembler-v0.1
  - domain-bundle-export-v0.1
  - technical-renderer-v0.1
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
  domain_bundle_export: docs/design/domain-bundle-export-v0.1.md
  technical_renderer: docs/design/technical-renderer-v0.1.md
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
  surface_feature_bias: docs/design/surface-feature-bias-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента. Подробные normative semantics находятся в `docs/design/`, `docs/contracts/` и `docs/decisions/`.

## Цель и граница продукта

`domain_generator` — независимое setting-agnostic procedural Core для генерации ограниченных пространственных регионов с управляемой случайностью.

```text
world / setting / application
          ↓
   adapter / presets
          ↓
      DomainSpec
          ↓
   domain_generator
          ↓
 DomainData / DomainBundle
          ↓
 renderer / integration
```

Core знает generic geometry, terrain, hydrology, fields, networks, constraints, procedural features и placement rules. Core не знает конкретный setting/campaign, game-system rules, lore, LLM provider, GitHub как обязательный runtime, UI или renderer.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

На `main` находятся полный generation pipeline до Final Validation, HydroFeature materialization, DomainData Assembler, DomainBundle Export v0.1 и Technical Renderer v0.1.

`main` после merge PR #41:

```text
e050dc8c609f01c70ebfc7c2fe79e9c4b425ff6a
```

Technical Renderer v0.1 принят пользователем и смержен. Подтверждённый полный CI implementation PR #41:

```text
290 passed
```

## Карта прогресса простыми словами

```text
[готово] описание region/domain
[готово] генерация геометрии объектов
[готово] ограничения размещения
[готово] terrain: поднятия / впадины / хребты / shaping
[готово] hydrology: routing / streams / lakes / RiverNetwork / water_depth
[готово] semantic HydroFeature для lakes
[готово] moisture + vegetation fields
[готово] explicit surface feature biases
[готово] dependent placement
[готово] Final Validation hard gate
[готово] soft constraint compilation + scoring + final ranking
[готово] DomainData Assembler v0.1
[готово] DomainBundle Export v0.1
[готово] Technical Renderer v0.1
[дальше] canonical CLI / Python application entrypoint — design gate
[потом] local model skill/adapter
[потом] remote GitHub Actions generation adapter

[готово] GitHub Actions: pytest на push/PR
```

## End-to-End Runtime & Bundle Architecture v0.1

Normative semantics: `docs/design/end-to-end-runtime-bundle-v0.1.md`.

```text
DomainSpec
  -> Compiler
  -> GenerationPlan
  -> Layout
  -> Terrain
  -> Hydrology
  -> Surface
  -> Dependent Placement
  -> Final Validation
  -> DomainData Assembler
  -> DomainAssembly
  -> DomainBundle Export
  -> persisted bundle
  -> Technical Renderer / adapters downstream
```

Core stages работают в одном Python process. Local и remote execution должны использовать один canonical entrypoint. GitHub Actions остаётся adapter/infrastructure, а не dependency Core.

## DomainData Assembler v0.1 — accepted / implemented / merged PR #36

Normative semantics: `docs/design/domain-data-assembler-v0.1.md`.

Assembler не использует RNG/IO/rendering, не reroll-ит candidate и не пересчитывает upstream state. Canonical raster payloads — exact `float32`, independent read-only copies.

## DomainBundle Export v0.1 — accepted / implemented / merged PR #38

Normative semantics: `docs/design/domain-bundle-export-v0.1.md`.

Canonical persisted layout:

```text
<caller-provided-output>/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
```

Exporter не меняет semantic world state, не использует RNG и публикует final directory только после успешной записи temporary sibling tree.

## Technical Renderer v0.1 — accepted / implemented / merged PR #41

Normative semantics: `docs/design/technical-renderer-v0.1.md`.

Implementation boundary:

```text
DomainAssembly
  data: DomainData
  field_payloads
        ↓
render_technical_map(...)
        ↓
technical-map.png
```

Реализовано:

- optional package extra `domain-generator[render]`;
- Matplotlib `Agg` headless backend;
- caller-provided PNG path;
- 1600 px long-side baseline с сохранением world aspect ratio;
- north-up world coordinate convention;
- elevation, vegetation и canonical water raster layers;
- lake RegionSet outlines и river centerlines;
- Point/POI, Corridor, Band width samples, Area/Surface overlays;
- labels, north indicator, scale, legend и domain boundary;
- nearest-neighbour raster display без semantic smoothing;
- existing target rejection и temporary sibling publication;
- no RNG, reroll, generation or mutation.

`technical-map.png` остаётся diagnostic non-canonical artifact. Он не считается оптимальным control image для image-generation model.

## Presentation / imagegen guide boundary

Для будущей художественной карты отдельно зарезервирован downstream слой:

```text
DomainData + canonical rasters + vectors
        ↓
Presentation / imagegen guide renderer
        ↓
imagegen-guide.png
        ↓
image generation / artistic transform
        ↓
campaign-map.png
```

Он должен сохранять canonical geography, но может подготавливать её в более удобной для image model форме, чем nearest-neighbour technical grid. Этот слой пока не спроектирован.

## Следующий bounded design gate

```text
canonical CLI / Python application entrypoint
```

Нужно определить единый application-level вызов для local и remote execution: входной request path, output path, compilation/generation/assembly/export/render orchestration, error/exit-code semantics и Python API boundary. До принятия design runtime implementation не начинается.

После него:

```text
local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide renderer остаётся отдельной downstream задачей и не блокирует canonical CLI.

## Ещё не сделано

- presentation/imagegen guide renderer;
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
