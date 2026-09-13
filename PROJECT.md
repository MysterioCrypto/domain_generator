---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: codex-integration-packaging-v0.1-implementation
next_topic: codex-integration-packaging-v0.1-acceptance
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
implemented_integrations:
  - local-model-skill-adapter-v0.1
  - codex-integration-packaging-v0.1
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
  codex_integration: docs/design/codex-integration-packaging-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — независимое setting-agnostic procedural Core. M0–M10 функционально завершены; M11 Acceptance Suite остаётся release gate Core 0.1. Integration track использует публичную application boundary и не меняет Core semantics.

## Карта прогресса простыми словами

```text
[готово] contracts / geometry / layout / constraints
[готово] terrain / hydrology / surface
[готово] dependent placement / validation / ranking
[готово] DomainData / DomainBundle / manifest
[готово] Technical Renderer v0.1
[готово] GenerationRequest + PresetCatalog v0.1
[готово] canonical Python API + domain-generator CLI
[готово] Local Model Skill / Adapter v0.1

[PR #49 / CI 330 passed] Codex Integration Packaging v0.1 — implementation
[сейчас] отдельное принятие implementation PR #49
[после merge] Remote GitHub Actions Generation Adapter — design gate
[release gate] M11 Acceptance Suite / Core 0.1 hardening
[отдельно позже] Presentation / ImageGen Guide Renderer
```

## Canonical application boundary

```text
GenerationRequest + external PresetCatalog
        ↓
PresetRegistry + CORE_OPERATOR_IDS
        ↓
generate_domain(...)
        ↓
Compiler → Layout → Terrain → Hydrology → Surface
→ Dependent Placement → Final Validation → deterministic selection
→ DomainData Assembler
        ↓
DomainAssembly
   ├─ DomainBundle Export
   └─ optional Technical Renderer
        ↓
atomic application publication
```

## Local Model Skill / Adapter v0.1 — implemented and merged

Normative semantics: `docs/design/local-model-skill-adapter-v0.1.md`.

Provider-neutral integration реализует model-facing preset projection, optional guide validation, strict `LocalModelDecision`, conservative edit policy, compiler preflight, maximum-two-repair orchestration, exactly one canonical generation after successful preflight and structured audit without chain-of-thought.

## Codex Integration Packaging v0.1 — implementation ready in PR #49

Normative semantics: `docs/design/codex-integration-packaging-v0.1.md`.

Implementation adds:

```text
AGENTS.md
.codex/skills/domain-generator-authoring/SKILL.md
docs/integrations/codex.md
tests/test_codex_packaging.py
```

Runtime/user flow:

```text
Codex
  ├─ root AGENTS.md
  └─ domain-generator-authoring skill
             ↓
GenerationRequest + PresetCatalog
             ↓
canonical domain-generator CLI / public application API
             ↓
DomainBundle + optional technical preview
```

Properties:

- no OpenAI API/provider dependency enters Core;
- `AGENTS.md` remains concise routing/workflow guidance;
- skill frontmatter uses only `name` and `description`;
- skill reuses `docs/skills/local-model-authoring-v0.1.md` rather than duplicating semantics;
- bounded technical repair / no hidden semantic reroll policy is explicit;
- internal generation stages are explicitly forbidden as end-user authoring entrypoints;
- user integration note documents repository-local use and `$skill-installer` installation from the GitHub skill directory;
- 7 packaging-specific tests were added;
- full clean functional suite: `330 passed`.

## Current checkpoint rule

PR #49 remains open and must not be merged until the user separately accepts this implementation checkpoint.

After acceptance/merge the next bounded integration design gate is:

```text
Remote GitHub Actions Generation Adapter
```

Then M11 Acceptance Suite / Core 0.1 hardening and release candidate work.

## Still outside current checkpoint

- concrete local-model/OpenAI backend runtime;
- Remote GitHub Actions Generation Adapter;
- M11 Acceptance Suite / release hardening;
- presentation/imagegen guide renderer;
- production generic/setting-specific preset catalogs outside Core;
- YAML adapter;
- physical river width/discharge;
- climate/biome model;
- advanced terrain shaping/erosion.

## Invariants

INV-001..INV-011 remain unchanged. Architecture changes are discussed and documented before implementation; implementation PRs merge only after separate explicit acceptance.
