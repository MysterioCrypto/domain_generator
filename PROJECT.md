---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: remote-github-actions-generation-adapter-v0.1-design
next_topic: remote-github-actions-generation-adapter-v0.1-implementation
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
  - remote-github-actions-generation-adapter-v0.1
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
  remote_github_actions_generation: docs/design/remote-github-actions-generation-adapter-v0.1.md
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
[готово] Codex Integration Packaging v0.1

[принято] Remote GitHub Actions Generation Adapter v0.1 — design
[дальше] Remote GitHub Actions Generation Adapter v0.1 — implementation
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

## Codex Integration Packaging v0.1 — implemented and merged

Normative semantics: `docs/design/codex-integration-packaging-v0.1.md`.

Merged implementation provides root `AGENTS.md`, repository-local Codex skill, integration guide and packaging tests. Codex uses the same canonical CLI/application contract and does not introduce provider-specific Core semantics.

Merged implementation PR: `#49`, merge commit `495fca9b85c56074f4a3c881e12a01f6689ed440`. Clean implementation suite: `330 passed`.

## Remote GitHub Actions Generation Adapter v0.1 — accepted design

Normative semantics: `docs/design/remote-github-actions-generation-adapter-v0.1.md`.

Accepted boundary:

```text
workflow_dispatch                 pull_request: remote-requests/**
       │                                      │
       └──────────────┬───────────────────────┘
                      ↓
             exact repository checkout
                      ↓
              safe path validation
                      ↓
           canonical CLI exactly once
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
 domain-bundle  technical-preview  generation-diagnostics
```

Properties:

- `workflow_dispatch` supports manual/Codex/CLI clients;
- PR-trigger path supports chat/agents that can create branch/files/PR but cannot dispatch workflows directly;
- PR requests live under `remote-requests/<id>/` with `request.json`, optional `presets.json` and transport-only `run.json`;
- exact workflow checkout SHA is the generator revision;
- workflow inputs do not duplicate semantic `GenerationRequest` fields;
- repository-relative input paths are validated against traversal/absolute paths;
- canonical `domain-generator generate` runs at most once per workflow execution;
- no automatic seed changes, reroll, semantic repair or hidden replanning;
- canonical DomainBundle remains unmodified;
- technical preview is additionally published as a small separate artifact when requested;
- diagnostics are published even on failure while the job remains failed;
- workflow permissions remain `contents: read` and generated world data is never pushed back to Git;
- local Codex execution remains available in parallel with remote execution.

## Следующий implementation checkpoint

Отдельный implementation PR должен добавить минимум:

```text
.github/workflows/generate-domain.yml
scripts/remote_generation.py
docs/integrations/github-actions-generation.md
remote-requests/example/
tests/test_github_actions_generation_adapter.py
```

После merge implementation должен пройти первый реальный end-to-end generation test через временный `remote-requests/**` PR, включая retrieval artifacts.

Implementation PR не merge-ится без отдельного явного принятия пользователя.

## После Remote GitHub Actions Adapter

```text
M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.

## Still outside current checkpoint

- concrete local-model/OpenAI backend runtime;
- M11 Acceptance Suite / release hardening;
- presentation/imagegen guide renderer;
- production generic/setting-specific preset catalogs outside Core;
- YAML adapter;
- physical river width/discharge;
- climate/biome model;
- advanced terrain shaping/erosion;
- LLM inside GitHub Actions;
- automatic semantic repair/reroll;
- batch generation, artifact attestations, Releases/S3/Pages publication.

## Invariants

INV-001..INV-011 remain unchanged. Architecture changes are discussed and documented before implementation; implementation PRs merge only after separate explicit acceptance.