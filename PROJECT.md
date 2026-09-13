---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: canonical-cli-python-entrypoint-v0.1-merged
next_topic: local-model-skill-adapter-v0.1-design
completed:
  - M0-project-foundation
  - M1-data-contracts
  - M2-deterministic-pipeline
  - M3-spatial-foundation
  - M4-layout-and-constraints-core-0.1
  - M5-elevation-v0.1
  - M6-hydrology-v0.1
  - M7-surface-v0.1
  - M8-dependent-placement-v0.1
  - M9-validation-ranking-v0.1
  - M10-stable-outputs-v0.1
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
      GenerationRequest
          ↓
   domain_generator
          ↓
 DomainData / DomainBundle
          ↓
 renderer / integration
```

Core не знает конкретный setting/campaign, game-system rules, lore, LLM provider, GitHub как обязательный runtime, UI или художественный renderer.

## Текущее состояние

PR #44 `Canonical CLI / Python Application Entrypoint v0.1` принят пользователем и merged.

Текущий `main` после merge:

```text
f5efd8cc88fca28713d000d7112f3caa59292ad5
```

CI merge commit — success. Implementation checkpoint до merge проходил полный suite `312 passed`.

Основной Core pipeline и application boundary замкнуты. M0–M10 функционально завершены; следующий release gate Core 0.1 — M11 Acceptance Suite. Параллельно следующий выбранный integration design gate — `Local Model Skill / Adapter v0.1`.

## Карта прогресса простыми словами

```text
[готово] описание region/domain и serialized contracts
[готово] geometry + layout + constraints
[готово] terrain / elevation / noise / shaping
[готово] hydrology / rivers / lakes / water_depth
[готово] moisture / vegetation / surface biases
[готово] dependent placement
[готово] Final Validation + soft ranking
[готово] DomainData Assembler v0.1
[готово] DomainBundle Export v0.1
[готово] Technical Renderer v0.1
[готово] GenerationRequest + PresetCatalog v0.1
[готово] canonical Python application entrypoint
[готово] domain-generator generate CLI

[дальше] Local Model Skill / Adapter v0.1 — design gate
[потом] Remote GitHub Actions Generation Adapter
[release gate Core 0.1] Acceptance Suite / hardening
[отдельно позже] Presentation / ImageGen Guide Renderer
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

## Canonical application boundary — implemented

Канонический in-memory API:

```python
generate_domain(
    *,
    spec: DomainSpec,
    config: GenerationConfig,
    registry: PresetRegistry,
) -> DomainAssembly
```

Filesystem API:

```python
generate_domain_bundle(
    *,
    request: GenerationRequest,
    registry: PresetRegistry,
    output_dir: Path,
    render_preview: bool = False,
) -> GenerateApplicationResult
```

CLI:

```text
domain-generator generate <request.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir> --preview
```

Application-level output публикуется атомарно. Existing target не перезаписывается. Success stdout — machine-readable JSON, diagnostics — stderr.

## Local Model Skill / Adapter — следующий design gate

Следующий слой должен превращать человеческое описание региона в validated `GenerationRequest`, выбирать только существующие presets/capabilities и запускать canonical application boundary без прямого доступа модели к внутренним stages.

Базовая идея:

```text
natural-language intent
        ↓
Local Model Adapter
        ↓
GenerationRequest + selected external PresetCatalog
        ↓
canonical application entrypoint
        ↓
DomainBundle + optional technical preview
```

Нужно определить:

- input/output contract adapter-а;
- как модель видит catalog/capabilities;
- разрешённые и запрещённые действия;
- validation/repair loop для технически невалидных requests;
- предел количества автоматических исправлений;
- границу между техническим repair и скрытым semantic reroll;
- local execution/tool boundary;
- logging/auditability.

До принятия design runtime implementation adapter-а не начинается.

## Core 0.1 release gate

После integration work необходимо пройти M11 Acceptance Suite: фиксированные representative specs/seeds и end-to-end assertions на semantic properties, topology, provenance/fingerprints и bundle output. После этого можно формировать Core 0.1 release candidate.

## Technical Renderer и художественная карта

`technical-map.png` — diagnostic non-canonical artifact, не финальная карта и не оптимальный image-generation control image.

Будущий отдельный downstream flow:

```text
DomainData + canonical rasters + vectors
        ↓
Presentation / ImageGen Guide Renderer
        ↓
imagegen-guide.png
        ↓
image generation
        ↓
campaign-map.png
```

## Ещё не сделано

- Local Model Skill / Adapter v0.1;
- Remote GitHub Actions Generation Adapter;
- Core 0.1 Acceptance Suite / release hardening;
- presentation/imagegen guide renderer;
- production generic/setting-specific preset catalogs outside Core;
- YAML preset/request adapter;
- physical river width/discharge;
- climate/biome model;
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
