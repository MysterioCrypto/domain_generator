# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. M11 Acceptance Suite остаётся release gate.

`Local Model Skill / Adapter v0.1` и `Codex Integration Packaging v0.1` реализованы и смержены.

`Remote GitHub Actions Generation Adapter v0.1` design принят и смержен через docs PR #51. Implementation находится в открытом PR #52 и требует отдельного пользовательского принятия до merge.

## Implementation PR #52

Добавлены:

```text
.github/workflows/generate-domain.yml
.github/workflows/cleanup-remote-generation.yml
scripts/remote_generation.py
docs/integrations/github-actions-generation.md
remote-requests/example/request.json
remote-requests/example/run.json
tests/test_github_actions_generation_adapter.py
```

Generation path:

```text
workflow_dispatch / PR remote-requests/**
        ↓
exact checkout revision
        ↓
safe path validation
        ↓
canonical domain-generator CLI exactly once
        ↓
domain-bundle + technical-preview + generation-diagnostics
```

Generation workflow остаётся `contents: read`. Cleanup write permission находится только в отдельном `pull_request: closed` workflow и применяется только к same-repository branches `remote-generation/*`.

## Проверки

Полный suite на исправленном implementation head:

```text
341 passed
```

Реальный remote smoke-test также уже прошёл на PR #52:

```text
run id: 34775535265
head SHA: d16c681ebf1d97c00568e7c7f130c81654a9297d
result: success
```

Workflow:

- checkout-нул exact PR head SHA;
- вызвал canonical generator один раз;
- успешно загрузил `domain-bundle`;
- успешно загрузил `technical-preview`;
- успешно загрузил `generation-diagnostics`.

Artifact ZIP удалось получить из GitHub через доступный chat connector. Прямое извлечение PNG из ZIP текущим файловым runtime пока не подтверждено; это downstream retrieval/UI вопрос, не проблема generator workflow.

## Provenance correction

Первый smoke-test обнаружил, что GitHub `pull_request` event имеет synthetic `GITHUB_SHA`, который не обязан совпадать с явно checkout-нутым PR head.

Уточнение зафиксировано до code fix в:

```text
docs/decisions/remote-generation-pr-sha-provenance.md
```

Теперь:

- `generator_commit` = exact revision, реально переданная в `actions/checkout`;
- PR path использует `github.event.pull_request.head.sha`;
- raw GitHub event SHA сохраняется отдельно как `github_sha`;
- никакого второго checkout/revision не появляется.

## Temporary branches

После merge #52 нужен отдельный production-shaped E2E:

```text
create remote-generation/<id>
→ add remote-requests/<id>/...
→ open PR
→ retrieve artifacts
→ close PR without merge
→ cleanup-remote-generation
→ verify temporary branch deleted
```

PR #52 сам для cleanup-test не используется, потому что его branch имеет namespace `impl/...` и намеренно не должен автоматически удаляться.

## Merge rule

PR #52 MUST remain unmerged until separate explicit user acceptance of this implementation checkpoint.

После acceptance/merge и реального cleanup E2E:

```text
M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.