---
project: domain_generator
target_version: core-0.1
phase: integration-and-hardening
status: in-progress
current_milestone: M11-acceptance-suite
checkpoint: remote-github-actions-generation-adapter-v0.1-implementation
next_topic: remote-github-actions-generation-adapter-v0.1-acceptance
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

`domain_generator` — независимое setting-agnostic procedural Core. M0–M10 функционально завершены; M11 Acceptance Suite остаётся release gate Core 0.1.

## Карта прогресса

```text
[готово] Core pipeline / validation / ranking
[готово] DomainData / DomainBundle / Technical Renderer
[готово] canonical Python API + CLI
[готово] Local Model Skill / Adapter v0.1
[готово] Codex Integration Packaging v0.1

[PR #52 / 341 passed] Remote GitHub Actions Generation Adapter v0.1 — implementation
[сейчас] отдельное принятие implementation PR #52
[после merge] real remote-generation E2E + cleanup verification
[release gate] M11 Acceptance Suite / Core 0.1 hardening
[отдельно позже] Presentation / ImageGen Guide Renderer
```

## Remote GitHub Actions Generation Adapter v0.1 — implementation checkpoint

Normative design: `docs/design/remote-github-actions-generation-adapter-v0.1.md`.

PR #52 реализует:

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

Добавлены:

```text
.github/workflows/generate-domain.yml
.github/workflows/cleanup-remote-generation.yml
scripts/remote_generation.py
docs/integrations/github-actions-generation.md
remote-requests/example/
tests/test_github_actions_generation_adapter.py
```

Проверенные свойства:

- generation workflow использует `contents: read`;
- cleanup write permission изолирован в closed-PR workflow;
- cleanup ограничен same-repository branches `remote-generation/*`;
- request/preset paths защищены от absolute/traversal/out-of-workspace inputs;
- canonical `domain-generator generate` вызывается максимум один раз;
- semantic failure не вызывает reroll/repair;
- outputs не коммитятся в repository;
- PR workflow checkout-ит exact PR head SHA;
- `generator_commit` получает exact actually checked-out revision, а synthetic/raw `github_sha` хранится отдельно;
- full suite: `341 passed`.

## Реальный remote smoke-test

Новый `generate-domain` workflow уже был реально выполнен на PR #52, потому что implementation добавляет `remote-requests/example/**`.

Исправленный smoke run:

```text
run: 34775535265
head: d16c681ebf1d97c00568e7c7f130c81654a9297d
result: success
```

Он успешно прошёл exact checkout, canonical generation и создал все три artifacts:

```text
domain-bundle
technical-preview
generation-diagnostics
```

Artifact ZIP успешно извлекается GitHub connector-ом в chat runtime. Прямое распаковывание ZIP/inline PNG в текущем runtime пока не подтверждено из-за ошибки файлового runtime; это downstream retrieval/UI issue, а не failure remote generation.

До implementation acceptance PR #52 не merge-ится.

## После merge

Первый production-shaped E2E выполняется отдельным temporary flow:

```text
remote-generation/<id>
→ remote-requests/<id>/...
→ PR
→ generation artifacts
→ close PR without merge
→ cleanup workflow
→ verify branch deleted
```

Этот post-merge E2E нужен, потому что branch PR #52 намеренно имеет namespace `impl/...` и cleanup workflow не должен её удалять.

После успешного E2E следующий Core gate — M11 Acceptance Suite / Core 0.1 hardening.

## Invariants

INV-001..INV-011 remain unchanged. Implementation PRs merge only after separate explicit acceptance.