---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: remote-github-actions-generation-adapter-v0.1-merged
next_topic: m11-acceptance-suite-design
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
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — независимое setting-agnostic procedural Core. M0–M10 функционально завершены. Integration track до Core 0.1 также собран; текущий release gate — M11 Acceptance Suite.

## Карта прогресса

```text
[готово] Core pipeline / validation / ranking
[готово] DomainData / DomainBundle / Technical Renderer
[готово] canonical Python API + CLI
[готово] Local Model Skill / Adapter v0.1
[готово] Codex Integration Packaging v0.1
[готово] Remote GitHub Actions Generation Adapter v0.1
[готово] remote-generation E2E + automatic branch cleanup
[готово] visual remote smoke example

[дальше] M11 Acceptance Suite — design gate
[release gate] M11 Acceptance Suite / Core 0.1 hardening
[отдельно позже] Presentation / ImageGen Guide Renderer
```

## Remote GitHub Actions Generation Adapter v0.1 — complete

Normative design: `docs/design/remote-github-actions-generation-adapter-v0.1.md`.

Implementation merged through PR #52. It provides:

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

Verified properties:

- generation workflow is `contents: read`;
- cleanup write permission is isolated in the closed-PR cleanup workflow;
- cleanup only targets same-repository `remote-generation/*` branches;
- exact checked-out revision is recorded as generator provenance;
- request/preset paths reject absolute/traversal/out-of-workspace inputs;
- canonical CLI runs at most once;
- semantic failures do not trigger reroll/repair;
- outputs are Actions artifacts, never repository commits.

## Real E2E verification

A real temporary `remote-generation/cleanup-e2e-20260913` flow was executed after merge:

```text
create temporary branch
→ create remote request
→ open PR #54
→ generate-domain success
→ close PR without merge
→ cleanup-remote-generation success
→ branch no longer exists
```

This verifies the complete branch lifecycle, not only static tests.

## Visual smoke example

PR #53 added `remote-requests/visual-example/` with a real ridge preset and a larger grid. The resulting technical preview visibly contains generated terrain, water/surface layers and feature geometry. This remains an engineering diagnostic representation, not a player-facing map.

## Next gate: M11 Acceptance Suite

The next bounded design slice is the Core 0.1 acceptance suite. It should define fixed representative specs/seeds and semantic assertions for the already implemented pipeline before any release-candidate declaration.

Presentation/ImageGen Guide Renderer remains a separate downstream track and does not block M11.

## Invariants

INV-001..INV-011 remain unchanged. Architecture changes are discussed and documented before implementation; implementation PRs merge only after separate explicit acceptance.