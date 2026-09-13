---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: local-model-skill-adapter-v0.1-design
next_topic: local-model-skill-adapter-v0.1-implementation
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
  - local-model-skill-adapter-v0.1
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
  local_model_adapter: docs/design/local-model-skill-adapter-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — независимое setting-agnostic procedural Core для генерации ограниченных пространственных регионов с управляемой случайностью.

Core generation/application boundary уже замкнут: M0–M10 функционально завершены. Core 0.1 release gate — M11 Acceptance Suite. Параллельно идёт integration track, который не меняет Core semantics.

## Карта прогресса простыми словами

```text
[готово] contracts / geometry / layout / constraints
[готово] terrain / hydrology / surface
[готово] dependent placement / validation / ranking
[готово] DomainData / DomainBundle / manifest
[готово] Technical Renderer v0.1
[готово] GenerationRequest + PresetCatalog v0.1
[готово] canonical Python API + domain-generator CLI

[принято] Local Model Skill / Adapter v0.1 — design
[дальше после docs merge] Local Model Skill / Adapter v0.1 — implementation
[потом] Remote GitHub Actions Generation Adapter
[release gate] M11 Acceptance Suite / Core 0.1 hardening
[отдельно позже] Presentation / ImageGen Guide Renderer
```

## Реализованная canonical application boundary

```text
GenerationRequest + external PresetCatalog
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
→ deterministic selection
→ DomainData Assembler
        ↓
DomainAssembly
   ├─ DomainBundle Export
   └─ optional Technical Renderer
        ↓
atomic application publication
```

CLI:

```text
domain-generator generate <request.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir> --preview
```

## Local Model Skill / Adapter v0.1 — accepted design

Normative semantics: `docs/design/local-model-skill-adapter-v0.1.md`.

Цель integration layer:

```text
natural-language user intent
  + base GenerationRequest
  + canonical PresetCatalog
  + optional PresetGuideCatalog
        ↓
model-facing authoring context
        ↓
provider-neutral local model host
        ↓
LocalModelDecision
        ↓
validation + compiler preflight
        ↓
canonical application API
        ↓
DomainBundle + optional technical preview
```

Ключевые границы:

- Core не получает LLM/provider dependencies;
- model-facing preset projection детерминированно выводится из canonical catalog;
- optional guide описывает смысл preset/parameter, но не меняет capabilities/ranges;
- caller предоставляет base `GenerationRequest` с техническими defaults;
- модель возвращает strict `ready` или `needs_clarification` decision;
- preflight выполняет contract/registry/compiler validation до generation;
- допускается initial draft + максимум два automatic technical repair;
- repair не может менять user semantics, seed, hard constraints или generation policy ради успеха;
- после успешного preflight выполняется один semantic application run;
- generation failure не запускает hidden replanning/reroll;
- technical preview не используется для автономной эстетической оценки;
- audit сохраняет final request, assumptions/questions, attempts/diagnostics и input digests, но не chain-of-thought;
- concrete Ollama/llama.cpp/OpenAI backend находится вне v0.1 semantics.

## Следующий implementation checkpoint

После merge принятого docs PR отдельный implementation PR должен реализовать provider-neutral bounded slice: adapter contracts, catalog projection, guide validation, edit policy, model Protocol/callback, decision parsing, compiler preflight, maximum-two-repair orchestration, one-generation boundary, structured audit result и reference skill/instruction artifact.

Implementation PR не merge-ится без отдельного явного принятия пользователя.

## Core 0.1 release gate

M11 Acceptance Suite должен проверить representative fixed specs/seeds, semantic properties, topology, provenance/fingerprints и bundle output. После этого можно формировать Core 0.1 release candidate.

## Ещё не сделано

- Local Model Skill / Adapter v0.1 implementation;
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
