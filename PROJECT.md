---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-canonical-cli-python-entrypoint-v0.1-design
next_topic: canonical-cli-python-entrypoint-v0.1-implementation
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
  - canonical-cli-python-entrypoint-v0.1
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
  domain_data_assembler: docs/design/domain-data-assembler-v0.1.md
  domain_bundle_export: docs/design/domain-bundle-export-v0.1.md
  technical_renderer: docs/design/technical-renderer-v0.1.md
  canonical_entrypoint: docs/design/canonical-cli-python-entrypoint-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа. Подробные normative semantics находятся в `docs/design/`, `docs/contracts/` и `docs/decisions/`.

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

Core знает generic geometry, terrain, hydrology, fields, networks, constraints, procedural features и placement rules. Core не знает конкретный setting/campaign, game-system rules, lore, LLM provider, GitHub как обязательный runtime, UI или художественный renderer.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

На `main` до этого design PR находятся полный generation pipeline до Final Validation, HydroFeature materialization, DomainData Assembler, DomainBundle Export v0.1 и Technical Renderer v0.1.

Базовый `main` для принятого design:

```text
0eaf1b0269afd39089be0975c504601df5f28685
```

Последний принятый implementation checkpoint — `Technical Renderer v0.1`; PR #41 merged, полный CI — `290 passed`.

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
[принято] canonical CLI / Python application entrypoint v0.1 — design
[дальше после docs merge] canonical CLI / Python application entrypoint — implementation
[потом] local model skill/adapter
[потом] remote GitHub Actions generation adapter

[готово] GitHub Actions: pytest на push/PR
```

## Реализованная сквозная граница

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
     ├-> DomainBundle Export -> persisted bundle
     └-> Technical Renderer -> technical-map.png
```

Core stages работают в одном Python process. Local и remote execution должны использовать один canonical application entrypoint; GitHub Actions остаётся adapter/infrastructure, а не dependency Core.

## Canonical CLI / Python Application Entrypoint v0.1 — accepted design

Normative semantics: `docs/design/canonical-cli-python-entrypoint-v0.1.md`.

Канонический in-memory API:

```text
generate_domain(spec, config, registry) -> DomainAssembly
```

Он связывает compiler, фиксированный stage order, deterministic candidate selection и assembler, но не выполняет filesystem IO или rendering.

Application layer поверх него:

```text
GenerationRequest JSON
+ optional external PresetCatalog JSON
+ caller-provided output path
        ↓
generate_domain(...)
        ↓
DomainAssembly
        ↓
DomainBundle Export
        ↓
optional Technical Renderer
        ↓
atomic application publication
```

Ключевые semantics:

- один и тот же application entrypoint для local/remote execution;
- `GenerationRequest` содержит `DomainSpec + GenerationConfig`;
- reusable `PresetCatalog` остаётся внешним и setting-specific catalogs не зашиваются в Core;
- user catalog не может объявлять возможности движка: application использует versioned `CORE_OPERATOR_IDS`;
- canonical CLI: `domain-generator generate <request.json> --output <dir>`;
- `--presets <catalog.json>` требуется при непустом feature set;
- `--preview` создаёт non-canonical `preview/technical-map.png` и не меняет semantic fingerprint;
- mandatory `input/`, `requests/` и `output/` directories отсутствуют;
- output target задаётся caller-ом и не перезаписывается;
- requested bundle + preview публикуются как единый application result через temporary sibling root;
- JSON stdout используется для machine-readable success result; diagnostics идут в stderr;
- stable exit classes: `0`, `2`, `3`, `4`, `5`, `70`;
- CLI не принимает fake `--generator-version`, version берётся из installed package;
- базовый serialized input/catalog v0.1 — JSON; YAML остаётся будущим adapter-ом.

## Technical Renderer и художественная карта

`technical-map.png` — diagnostic non-canonical artifact, а не оптимальный control image для image-generation model.

Отдельно зарезервирован будущий downstream слой:

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

Он пока не спроектирован и не блокирует canonical application entrypoint.

## Следующий checkpoint

После merge принятого docs PR — отдельный implementation PR `canonical CLI / Python application entrypoint v0.1`. Он не merge-ится без отдельного пользовательского принятия.

После него:

```text
local model skill/adapter
→ remote GitHub Actions generation adapter
```

## Ещё не сделано

- canonical CLI/application entrypoint implementation;
- local model skill/adapter;
- remote generation GitHub workflow;
- presentation/imagegen guide renderer;
- production generic preset catalog;
- YAML preset/request adapter;
- physical river width/sub-cell rasterization;
- runoff/discharge/climate model;
- standalone terrain `blend` operator;
- advanced terrain shaping/erosion;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators.

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

Перед существенным изменением архитектуры сначала объяснить изменение и последствия; после принятия обновить normative docs и только затем runtime implementation. Implementation PR merge-ится только после отдельного явного принятия checkpoint.
