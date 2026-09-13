---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-canonical-cli-python-entrypoint-v0.1-implementation
next_topic: canonical-cli-python-entrypoint-v0.1-acceptance
completed:
  - M0-project-foundation
  - M1-data-contracts
implemented_m2:
  - minimal-python-package
  - serialized-contract-layer-v0.1
  - generated-json-schema-v0.1
  - deterministic-rng-protocol-v1
  - attempt-pipeline-skeleton-v0.1
  - deterministic-candidate-ranking-v0.1
  - typed-preset-definition-v0.1
  - in-memory-preset-registry-boundary
  - deterministic-domain-spec-compiler-slice
  - layout-point-corridor-band-area-v0.1
  - placement-reservation-materialization-v0.1
  - terrain-core-v0.1
  - hydrology-core-v0.1
  - surface-core-v0.1
  - dependent-placement-v0.1
  - final-validation-and-ranking-v0.1
  - hydrofeature-lake-materialization-v0.1
  - domain-data-assembler-v0.1
  - domain-bundle-export-v0.1
  - bundle-manifest-v0.1
  - technical-renderer-v0.1
  - generation-request-v0.1
  - preset-catalog-v0.1
  - canonical-cli-python-entrypoint-v0.1
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

`domain_generator` — независимое setting-agnostic procedural Core для генерации ограниченных пространственных регионов с управляемой случайностью.

```text
world / setting / application
          ↓
   adapters / presets
          ↓
      DomainSpec
          ↓
   domain_generator
          ↓
 DomainData / DomainBundle
          ↓
 renderer / integration
```

Core не знает конкретный setting/campaign, game-system rules, lore, LLM provider, GitHub как обязательный runtime, UI или художественный renderer.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Базовый `main` implementation PR #44:

```text
8a6fec23ddf14d2e64ac6153c841c1f6b05bbe1d
```

PR #43 с принятым normative design `Canonical CLI / Python Application Entrypoint v0.1` merged. Runtime implementation готов в PR #44 и **не должен merge-иться без отдельного принятия пользователя**.

Подтверждённый полный functional CI implementation head до финального status-doc sync:

```text
312 passed
```

## Карта прогресса простыми словами

```text
[готово] описание region/domain
[готово] генерация geometry / constraints / terrain
[готово] hydrology / rivers / lakes / water_depth
[готово] moisture / vegetation / surface biases
[готово] dependent placement
[готово] Final Validation + soft ranking
[готово] DomainData Assembler v0.1
[готово] DomainBundle Export v0.1
[готово] Technical Renderer v0.1
[готово в PR #44] GenerationRequest + PresetCatalog v0.1
[готово в PR #44] canonical Python application entrypoint
[готово в PR #44] domain-generator generate CLI
[сейчас] отдельное принятие implementation PR #44
[после merge] local model skill/adapter — design gate
[потом] remote GitHub Actions generation adapter

[готово] GitHub Actions: pytest на push/PR
```

## Реализованная сквозная граница

```text
GenerationRequest
  ├─ DomainSpec
  └─ GenerationConfig
        +
external PresetCatalog
        ↓
PresetRegistry + CORE_OPERATOR_IDS
        ↓
generate_domain(...)
        ↓
Compiler
→ Layout
→ Terrain
→ Hydrology
→ Surface
→ Dependent Placement
→ Final Validation
→ deterministic candidate selection
→ DomainData Assembler
        ↓
DomainAssembly
   ├─ DomainBundle Export
   └─ optional Technical Renderer
        ↓
atomic application publication
```

## Canonical CLI / Python Application Entrypoint v0.1 — accepted / implemented in PR #44

Normative semantics: `docs/design/canonical-cli-python-entrypoint-v0.1.md`.

Канонический in-memory API:

```python
generate_domain(
    *,
    spec: DomainSpec,
    config: GenerationConfig,
    registry: PresetRegistry,
) -> DomainAssembly
```

Он использует package `__version__`, compiler, фиксированный stage order, существующий `run_generation()` и assembler. Filesystem IO/rendering в `generate_domain()` отсутствуют.

Canonical stage order не настраивается caller-ом:

```text
layout_stage
→ terrain_stage
→ hydrology_stage
→ surface_stage
→ placement_stage
→ final_stage
```

Application API:

```python
generate_domain_bundle(
    *,
    request: GenerationRequest,
    registry: PresetRegistry,
    output_dir: Path,
    render_preview: bool = False,
) -> GenerateApplicationResult
```

Requested bundle и preview сначала создаются в temporary sibling tree и публикуются единым final rename. Existing `output_dir` не перезаписывается.

## Serialized input contracts

`GenerationRequest v0.1`:

```json
{
  "request_version": "0.1",
  "domain_spec": { "...": "DomainSpec" },
  "generation_config": { "...": "GenerationConfig" }
}
```

`PresetCatalog v0.1`:

```json
{
  "preset_catalog_version": "0.1",
  "presets": [ { "...": "PresetDefinition" } ]
}
```

Для обоих committed JSON Schema snapshots находятся в `schemas/v0.1/`. Всего schema-export теперь содержит 9 root contracts.

Preset catalog остаётся внешним reusable input. User catalog не задаёт возможности движка; application использует versioned `CORE_OPERATOR_IDS`:

```text
raise
depress
ridge
flatten
moisture_bias
vegetation_bias
suitability_placement
```

## CLI v0.1

```text
domain-generator generate <request.json> --output <directory>
```

При непустом feature set:

```text
domain-generator generate <request.json> --presets <presets.json> --output <directory>
```

С diagnostic preview:

```text
domain-generator generate <request.json> --presets <presets.json> --output <directory> --preview
```

`--preview` использует optional `domain-generator[render]`, не входит в semantic fingerprint и создаёт `preview/technical-map.png` только как non-canonical artifact.

Mandatory `input/`, `requests/` и `output/` directories отсутствуют. Все host paths задаёт caller через `pathlib.Path`; canonical bundle descriptors остаются relative POSIX paths.

Stable CLI exit classes:

```text
0   success
2   invalid CLI arguments
3   request/catalog parse or validation error
4   compile/generation/capability/attempt exhaustion
5   assembly/export/render/filesystem failure
70  internal invariant or unexpected application failure
```

Success stdout — один machine-readable JSON object; diagnostics идут в stderr. `--generator-version` отсутствует: provenance version берётся из установленного package.

## Technical Renderer и художественная карта

`technical-map.png` остаётся diagnostic artifact, а не финальной картой для игрового стола и не оптимальным control image для image-generation model.

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

Он не входит в PR #44.

## Следующий checkpoint

Сейчас требуется отдельное пользовательское принятие implementation PR #44. До него merge запрещён.

После принятия/merge следующий bounded design gate:

```text
local model skill/adapter
```

Далее:

```text
remote GitHub Actions generation adapter
```

## Ещё не сделано

- merge canonical CLI/application entrypoint implementation PR #44;
- local model skill/adapter;
- remote generation GitHub workflow;
- presentation/imagegen guide renderer;
- production generic preset catalog;
- YAML preset/request adapter;
- physical river width/sub-cell rasterization;
- runoff/discharge/climate model;
- advanced terrain shaping/erosion;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators.

## Инварианты

- **INV-001:** Core независим от setting/campaign/game-system/LLM/GitHub/UI/renderer; adapters/content находятся за границей Core.
- **INV-002:** `DomainSpec` — intent; `GenerationPlan` — executable resolved recipe; `DomainData` — generated region.
- **INV-003:** одинаковые semantic inputs при точной версии generator дают воспроизводимый результат.
- **INV-004:** examples ненормативны.
- **INV-005:** Core использует generic primitives, а не scenario-specific special cases.
- **INV-006:** архитектурные изменения обсуждаются и документируются до реализации.
- **INV-007:** RNG адресуется semantic namespaces.
- **INV-008:** observability/debug/preview не меняют semantic result.
- **INV-009:** exact replay ограничен exact generator version.
- **INV-010:** stage читает только declared upstream outputs и не мутирует их.
- **INV-011:** earlier-layer effects выражаются earlier-stage feature/constraint, а не hidden late side effect.

## Правило совместной работы

После design acceptance normative docs фиксируются до runtime implementation. Implementation PR merge-ится только после отдельного явного принятия implementation checkpoint.
