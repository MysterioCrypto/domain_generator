---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-technical-renderer-v0.1-design
next_topic: technical-renderer-v0.1-implementation
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

На `main` находятся generation pipeline до Final Validation, HydroFeature materialization, DomainData Assembler и DomainBundle Export v0.1. `Technical Renderer v0.1` design принят; runtime implementation ещё отсутствует.

`main` до merge этого design PR:

```text
901be6c39fed43d1756253d95d1b653ece1a6bc8
```

Подтверждённый полный CI implementation PR #38:

```text
281 passed
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
[принято] Technical Renderer v0.1 — design
[дальше после docs merge] Technical Renderer v0.1 — implementation
[потом] canonical CLI / Python application entrypoint
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

Canonical boundary:

```text
DomainSpec + GenerationPlan + GenerationConfig + selected DomainCandidate
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

Assembler не использует RNG/IO/rendering, не reroll-ит candidate и не пересчитывает upstream state. Canonical raster payloads — exact `float32`, independent read-only copies.

## DomainBundle Export v0.1 — accepted / implemented / merged PR #38

Normative semantics: `docs/design/domain-bundle-export-v0.1.md`.
Design PR #37 и implementation PR #38 merged.

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

Ключевые semantics:

- input path и output path не привязаны к обязательным `input/`/`output/` directories;
- target output path задаётся caller-ом;
- internal persisted paths — relative POSIX paths;
- filesystem API построен на `pathlib.Path`, поэтому рассчитан на Windows и POSIX environments;
- `BundleManifest v0.1` хранит SHA-256 и size canonical persisted files;
- `manifest.json` не хэширует сам себя;
- existing output target → explicit error, overwrite/force в v0.1 отсутствует;
- запись идёт в temporary sibling tree с final rename;
- normal failure вызывает best-effort cleanup;
- exporter не меняет semantic world state и не использует RNG.

## Technical Renderer v0.1 — accepted design

Normative semantics: `docs/design/technical-renderer-v0.1.md`.

Technical renderer создаёт deterministic diagnostic top-down PNG из `DomainAssembly` без изменения world semantics. Базовые layers: elevation, vegetation, water, lakes, rivers и semantic features. World-space north находится сверху; aspect ratio сохраняется; long side baseline — 1600 px; raster visualisation не выполняет semantic smoothing.

Renderer является optional downstream component с отдельной `render` dependency boundary и headless backend. PNG не является canonical world state.

Важно: `technical-map.png` не считается оптимальным control image для художественной image generation. В будущем может появиться отдельный `Presentation / imagegen guide renderer`, который из canonical rasters/vectors строит image-model-friendly reference без изменения geography. Raw `.npy`/JSON не принимаются как надёжный прямой spatial interface к image model.

## Следующий bounded implementation checkpoint

`Technical Renderer v0.1` implementation.

Implementation выполняется отдельным PR после merge normative design docs и не merge-ится без отдельного явного принятия пользователя.

После renderer:

```text
canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide layer является отдельной downstream задачей и не блокирует canonical CLI.

## Ещё не сделано

- Technical Renderer v0.1 implementation;
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
