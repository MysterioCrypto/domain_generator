---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-final-validation-hard-v0.1
next_topic: soft-constraint-compilation-scoring-v0.1
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
accepted_designs:
  - dependent-placement-site-selection-v0.1
  - end-to-end-runtime-bundle-v0.1
  - final-validation-hard-v0.1
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

Layout Core 0.1 покрывает point/corridor/band/area и `PlacementReservation` для deferred point POI. Terrain имеет structural + shaping pipeline. Hydrology покрывает routing, lake/stream classification, directed river topology и canonical runtime water depth. Surface покрывает base moisture/vegetation и explicit area feature biases. Dependent point placement реализован полностью. Final Validation теперь имеет production hard-only gate и neutral ranking для реально поддерживаемых compiler plans.

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
[готово] candidate lattice + reservation filtering + hard requirements
[готово] preference scoring + near-best + weighted final selection + PlacementState
[готово] Final Validation hard-complete + neutral ranking
[принято] end-to-end runtime / bundle architecture
[следом] soft constraint compilation + scoring semantics
[потом] HydroFeature/lake materialization
[потом] DomainData assembler
[потом] bundle exporter + technical renderer + CLI/adapters

[готово] GitHub Actions: pytest на push/PR
```

## End-to-End Runtime & Bundle Architecture v0.1 — accepted

Normative semantics: `docs/design/end-to-end-runtime-bundle-v0.1.md`.

Ключевые решения:

- Core — один Python package; stages вызываются как функции в одном process, а не как subprocess scripts;
- local и remote execution используют один canonical generation entrypoint;
- local mode — Python/CLI/API на машине пользователя;
- remote mode — тот же entrypoint в GitHub Actions runner, request JSON в repository, result как workflow artifact;
- GitHub Actions не является dependency Core;
- canonical persisted rasters — `fields/*.npy`;
- `domain.json` хранит structured metadata/features/networks/field descriptors, а не массивы raster values;
- assembler не делает IO и не использует RNG;
- exporter физически пишет bundle;
- technical renderer и artistic/image-generation presentation находятся downstream и не меняют world state;
- LLM/model работает через внешний adapter над DomainSpec/GenerationConfig и не управляет внутренними stages напрямую;
- одинаковые semantic inputs + exact generator/RNG version должны давать один semantic result локально и в remote runner-е.

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

## Dependent Placement — complete

Normative semantics:

- `docs/design/dependent-placement-site-selection-v0.1.md`;
- `docs/design/dependent-placement-site-metrics-v0.1.md`;
- `docs/design/dependent-placement-candidate-filtering-v0.1.md`.

Полный runtime pipeline:

```text
PlacementReservation
-> rotated/phase-shifted world-space lattice
-> reservation containment
-> canonical candidate order
-> site metrics
-> hard requirements
-> valid sites
-> maximize / minimize / preferred_range scores
-> weighted composite suitability
-> near-best set
-> deterministic weighted choice
-> PlacementState.final_points
-> placement validation
```

## Final Validation v0.1 — hard-complete

Normative semantics: `docs/design/final-validation-hard-v0.1.md`.

Реализовано:

- temporary final geometry view объединяет structural `LayoutCandidate.geometry_realizations` и deferred `PlacementState.final_points` без mutation upstream state;
- Final проверяет наличие layout/terrain/hydrology/surface/placement, attempt identity, plan fingerprint и complete/disjoint final feature geometry sets;
- все hard compiled constraints повторно оцениваются против final geometry в canonical `constraint.id` order;
- Final использует существующую spatial measurement/predicate semantics через общий evaluation boundary и не содержит второго набора численных правил;
- hard predicate failure является normal rejected attempt;
- missing/incomplete upstream state является normal rejected attempt без constraint evaluation;
- unsupported evaluator/predicate или вручную вставленный soft constraint являются capability error;
- hard-only valid plan получает neutral ranking `(worst_effective_violation=0.0, weighted_mean_score=1.0)`;
- Final не использует RNG, не делает IO и ничего не исправляет.

## Следующий design gate: Soft Constraint Compilation & Scoring v0.1

Current `DomainSpec` уже различает hard/soft constraints и имеет `weight`, а `GenerationPlan` уже имеет `CompiledScoring`, но current compiler slice явно отклоняет soft constraints.

До implementation нужно зафиксировать scoring semantics для generic relations, включая:

- как `near`/`far_from` превращают distance в normalized score `[0,1]`;
- scoring для `inside`/`outside`/`overlaps`/`crosses`/`adjacent`;
- exact meaning `ideal`/`worst` и поведение за пределами диапазона;
- какие relation/evaluator combinations входят в Core 0.1 capability;
- aggregation `effective_violation = (1-score)*weight`;
- weighted mean score и worst effective violation;
- canonical ordering soft results;
- поведение degenerate/equal thresholds;
- отсутствие скрытого влияния intrinsic SiteProfile suitability на global ranking.

После этого Final Validation сможет перейти от neutral hard-only ranking к полному user-soft global ranking без изменения attempt-selection protocol.

## После soft-scoring

Следующие bounded checkpoints принятой end-to-end последовательности:

1. HydroFeature / lake materialization v0.1;
2. DomainData Assembler v0.1;
3. DomainBundle Export v0.1;
4. Technical Renderer v0.1;
5. canonical CLI / Python application entrypoint;
6. local model skill/adapter;
7. remote GitHub Actions generation adapter.

## Ещё не сделано

- soft constraint scoring compilation/evaluation;
- DomainData assembler/export bundle;
- lake polygon vectorization / canonical `HydroFeature` materialization;
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
