---
project: domain_generator
target_version: core-0.1
phase: release-hardening
status: in-progress
current_milestone: core-0.1-hardening
checkpoint: m11-acceptance-suite-v0.1-merged
next_topic: core-0.1-release-candidate-review
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
  - M11-acceptance-suite-v0.1
implemented_integrations:
  - local-model-skill-adapter-v0.1
  - codex-integration-packaging-v0.1
  - remote-github-actions-generation-adapter-v0.1
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
  - codex-integration-packaging-v0.1
  - remote-github-actions-generation-adapter-v0.1
  - m11-acceptance-suite-v0.1
implemented_infrastructure:
  - github-actions-pytest-ci-on-push-and-pull-request
  - github-actions-remote-domain-generation-v0.1
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
  codex_integration: docs/design/codex-integration-packaging-v0.1.md
  remote_github_actions_generation: docs/design/remote-github-actions-generation-adapter-v0.1.md
  m11_acceptance_suite: docs/design/m11-acceptance-suite-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — независимое setting-agnostic procedural Core. M0–M11 завершены. Integration track для Core 0.1 также завершён. Release gate Core 0.1 закрыт зелёным M11 Acceptance Suite; проект перешёл в короткий hardening / release-candidate review.

## Карта прогресса

```text
[готово] M0–M10 Core capabilities
[готово] DomainData / DomainBundle / Technical Renderer
[готово] canonical Python API + CLI
[готово] Local Model Skill / Adapter v0.1
[готово] Codex Integration Packaging v0.1
[готово] Remote GitHub Actions Generation Adapter v0.1
[готово] remote-generation E2E + automatic branch cleanup
[готово] visual remote smoke example
[готово] M11 Acceptance Suite v0.1

[сейчас] Core 0.1 hardening / release-candidate review
[следом] Core 0.1 release candidate declaration
[отдельно позже] Presentation / ImageGen Guide Renderer
```

## M11 Acceptance Suite v0.1 — complete

Normative design: `docs/design/m11-acceptance-suite-v0.1.md`.

Implementation merged through PR #57. Accepted implementation head before merge:

```text
6580046bcf13f38960ad75a8697e79a9594c881c
```

Merge commit:

```text
cd0a79b337f5e16e6336e36d843e8cba42251ca7
```

Final PR CI:

```text
357 passed in 12.47s
```

M11 fixes seven representative worlds:

```text
A01 minimal
A02 terrain-ridge
A03 hydrology-lake-river
A04 surface
A05 dependent-poi
A06 constraints-ranking
A07 complex-mixed
```

Каждый case проверяет одновременно:

1. exact replay;
2. compact deterministic baseline;
3. semantic correctness.

Baseline strategy:

- fixed `GenerationRequest` / `PresetCatalog` / seed;
- explicit `expected.json`, без auto-update;
- canonical DomainData SHA-256;
- field SHA-256 + dtype/shape/min/max;
- fingerprints/provenance;
- semantic assertions для соответствующего subsystem;
- два независимых generation run для exact replay.

## Acceptance coverage

### A01 Minimal

Проверяет пустой корректный world, canonical 4 fields, finite/range invariants, validation и bundle baseline.

### A02 Terrain Ridge

Проверяет materialized terrain `Band`, non-constant elevation, bounds и deterministic ridge field.

### A03 Hydrology / Lake / River

Фиксированный case реально материализует:

```text
lake-0001
72 river nodes
36 river segments
```

Проверяются water depth, generated hydro feature и internal river references.

### A04 Surface

Проверяет water forcing:

```text
water cell → moisture = 1
water cell → vegetation_density = 0
```

и material effect от deterministic surface moisture bias.

### A05 Dependent POI

Проверяет stage boundary:

```text
Layout → reservation exists, final point absent
Placement → final point exists
```

Final POI обязан лежать в allowed region.

### A06 Constraints / Ranking

Проверяет реальный multi-attempt selection:

```text
16 attempts executed
2 hard-valid candidates: attempts 8 and 7
soft scores differ
winner: attempt 8
```

Это доказывает hard rejection + soft ranking + deterministic winner ordering.

### A07 Complex Mixed

Representative mixed world объединяет terrain, basin/lake, river network, surface bias, dependent settlement POI, hard/soft constraints, ranking, assembly и export.

Фиксированный baseline выбирает attempt 1 из двух valid candidates и содержит generated lake + river network.

## Bug found by M11

M11 обнаружил production defect: Layout concrete-geometry validation пытался обрабатывать structural soft constraint как hard predicate и бросал `LayoutCapabilityError`.

Исправление было вынесено отдельно, согласно bug policy:

```text
PR #58
→ regression test
→ 342 tests green
→ accepted separately
→ merged as cd15b986e9a68f62fb7f8b80bd266e897125062b
```

После bugfix A06 прошёл и был зафиксирован baseline.

## Core 0.1 release gate

Сейчас green одновременно:

```text
[green] full unit/integration suite
[green] A01..A07 acceptance worlds
[green] exact replay all cases
[green] compact deterministic baselines
[green] canonical bundle acceptance
[green] engine/hard invariants
[green] provenance/fingerprints/digests
[green] remote GitHub generation E2E
```

Таким образом функциональный release gate Core 0.1 закрыт.

## Следующий bounded step

Новые generation capabilities сейчас не требуются. Следующий этап — короткий Core 0.1 release-candidate review/hardening: проверить package/version/release metadata, документационную согласованность и отсутствие известных блокирующих дефектов, после чего отдельно объявить Core 0.1 RC.

Presentation/ImageGen Guide Renderer остаётся downstream presentation track и не блокирует Core 0.1.

## Invariants

INV-001..INV-011 remain unchanged. Architecture changes are discussed and documented before implementation; implementation PRs merge only after separate explicit acceptance.