---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: m11-acceptance-suite-v0.1-design
next_topic: m11-acceptance-suite-v0.1-implementation
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

[принято] M11 Acceptance Suite v0.1 — design
[дальше] M11 Acceptance Suite v0.1 — implementation
[release gate] acceptance green → Core 0.1 hardening / release candidate
[отдельно позже] Presentation / ImageGen Guide Renderer
```

## M11 Acceptance Suite v0.1 — accepted design

Normative design: `docs/design/m11-acceptance-suite-v0.1.md`.

M11 не добавляет новые generation capabilities. Он закрепляет семь representative fixed worlds:

```text
A01 minimal
A02 terrain-ridge
A03 hydrology-lake-river
A04 surface
A05 dependent-poi
A06 constraints-ranking
A07 complex-mixed
```

Каждый case проверяет два независимых уровня:

1. exact replay / compact golden identity;
2. semantic correctness результата.

Baseline strategy:

- fixed `GenerationRequest` / `PresetCatalog` / seed;
- `expected.json` вместо больших `.npy` goldens;
- canonical DomainData digest + field/bundle hashes;
- explicit semantic assertions для terrain/hydrology/surface/placement/ranking;
- два независимых run для exact replay;
- technical preview не является Core binary golden.

Особые cases:

- A05 дополнительно проверяет reservation-before-placement и final point after placement через test-only stage harness;
- A06 обязан реально задействовать attempts/ranking и фиксировать expected winning attempt;
- A07 объединяет terrain + hydrology + surface + deferred POI + constraints + validation + assembly/export.

Если M11 обнаруживает production bug, fix оформляется отдельным bugfix PR; acceptance implementation не должен тихо менять Core behavior.

## Release gate

Core 0.1 переходит к release candidate только когда green одновременно:

```text
full unit/integration suite
A01..A07 acceptance worlds
exact replay all cases
canonical bundle acceptance
engine/hard invariants
provenance/fingerprints/digests
```

## Invariants

INV-001..INV-011 remain unchanged. Architecture changes are discussed and documented before implementation; implementation PRs merge only after separate explicit acceptance.