---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-domain-data-assembler-v0.1
next_topic: domain-bundle-export-v0.1
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
  - domain-data-assembler-v0.1
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
      DomainData
          ↓
 renderer / exporter / integration
```

Core знает generic geometry, terrain, hydrology, fields, networks, constraints, procedural features и placement rules. Core не знает конкретный setting/campaign, game-system rules, lore, LLM provider, GitHub как обязательный runtime, UI или renderer.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Layout, Terrain, Hydrology, Surface, Dependent Placement и Final Validation реализованы. Hydrology materializes accepted lakes в exact semantic `HydroFeature`. DomainData Assembler implementation готов в PR #36 и проходит CI, но до отдельного принятия пользователя не считается merged-состоянием `main`.

`main` после design PR #35:

```text
7cbd089d4530ff3db8238710edf988bbc6b1dd17
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
[принято] end-to-end runtime / bundle architecture
[готово в PR #36] DomainData Assembler v0.1
[следующий design gate после merge #36] DomainBundle Export v0.1
[потом] Technical Renderer
[потом] canonical CLI/Python entrypoint
[потом] local/remote adapters

[готово] GitHub Actions: pytest на push/PR
```

## End-to-End Runtime & Bundle Architecture v0.1 — accepted

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
  -> DomainData Assembly
  -> DomainBundle Export
  -> Technical Renderer / adapters downstream
```

Core stages работают в одном Python process. Local и remote execution должны использовать один canonical entrypoint. GitHub Actions остаётся adapter/infrastructure, а не dependency Core.

Canonical bundle baseline:

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

## Final Validation v0.1 — complete

Normative hard semantics: `docs/design/final-validation-hard-v0.1.md`.
Normative soft semantics: `docs/design/soft-constraint-compilation-scoring-v0.1.md`.

Final Validation наблюдает полный upstream state без mutation, повторно применяет hard constraints к final geometry, оценивает soft constraints через тот же canonical spatial measurement boundary и выдаёт deterministic ranking. RNG/IO/fallback отсутствуют.

## HydroFeature / Lake Materialization v0.1 — accepted / implemented / merged PR #34

Normative semantics: `docs/design/hydrofeature-lake-materialization-v0.1.md`.

```text
LakeCandidate.cells
→ exact world-space cell squares
→ exact polygonal union
→ canonical RegionSet
→ HydroFeature
```

- `HydroFeature.geometry` — `RegionSet`;
- holes и D8 diagonal multipart geometry сохраняются точно;
- `lake_feature_id()` централизует `lake-NNNN` protocol;
- `LakeProperties` содержит `max_depth_m`;
- `HydrologyState` содержит готовые `lake_features`;
- river lake references проверяются против materialized features.

PR #34 merged commit:

```text
d9c6145f6e49df351fb86372f05ffc6f953ea85b
```

## DomainData Assembler v0.1 — accepted / implemented in PR #36

Normative semantics: `docs/design/domain-data-assembler-v0.1.md`.
Design documentation merged через PR #35. Runtime implementation находится в PR #36 и ждёт отдельного принятия перед merge.

Canonical boundary:

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

Реализовано:

- `DomainAssembly` как in-memory, non-serialized boundary;
- `assemble_domain()` принимает только уже selected final-valid candidate;
- spec↔plan provenance проверяется до assembly;
- `identity.id/label` сохраняются из `DomainSpec`;
- semantic generation-config fingerprint включает version + semantic и исключает observability;
- user final features собираются из layout/placement geometry без повторной generation;
- готовые hydrology `HydroFeature` переносятся без повторной vectorization;
- user feature IDs, совпадающие с `^lake-[0-9]{4,}$`, отклоняются на `DomainSpec` validation boundary;
- specified/generated feature collision вызывает explicit error, silent overwrite невозможен;
- `rivers` network присутствует всегда, включая empty network;
- canonical field descriptors фиксированы для elevation/water_depth/moisture/vegetation_density;
- payload arrays обязаны иметь exact expected shape и `float32`, implicit cast/resize запрещены;
- assembler делает independent C-order copies и помечает payload arrays read-only;
- `field_payloads` mapping structurally read-only;
- validation summary использует уже успешный Final Validation ranking;
- deterministic mapping order не зависит от traversal order runtime dicts;
- assembler не использует RNG, IO, renderer, reroll, re-ranking или hidden regeneration.

Serialized `DomainData` contract не изменился; schema snapshot regeneration не понадобилась.

Подтверждённый полный push CI implementation semantics:

```text
272 passed
```

Финальный PR head должен пройти push + PR checks повторно после status-doc synchronization.

## Следующий bounded design gate после принятия и merge PR #36

`DomainBundle Export v0.1`.

Нужно будет отдельно определить persisted boundary: `domain.json`, `.npy`, manifest, deterministic serialization, path validation, overwrite/atomic-write semantics, failure cleanup и отношение canonical vs optional debug/preview artifacts.

После exporter:

```text
Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

## Ещё не сделано

- DomainBundle Export v0.1;
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
