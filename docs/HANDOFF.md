# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. Core release gate — M11 Acceptance Suite. Canonical generation/application/CLI boundary merged.

`Local Model Skill / Adapter v0.1` implemented and merged through PR #47.

`Codex Integration Packaging v0.1` implemented and merged through PR #49. Merge commit: `495fca9b85c56074f4a3c881e12a01f6689ed440`. Clean implementation suite: `330 passed`.

Текущий accepted bounded design — `Remote GitHub Actions Generation Adapter v0.1`.

Normative design:

```text
docs/design/remote-github-actions-generation-adapter-v0.1.md
```

## Accepted remote execution model

Remote GitHub Actions integration является transport/execution layer над canonical CLI и не создаёт новый generator.

```text
workflow_dispatch                 pull_request: remote-requests/**
       │                                      │
       └──────────────┬───────────────────────┘
                      ↓
             exact repository checkout
                      ↓
              safe path validation
                      ↓
           domain-generator generate
              exactly once
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
 domain-bundle  technical-preview  generation-diagnostics
```

## Trigger paths

### Manual / Codex / CLI client

`workflow_dispatch` принимает только transport-level inputs:

- `request_path`;
- optional `presets_path`;
- `preview` boolean.

Semantic generation configuration не дублируется в Actions inputs.

### Chat/agent path

Для клиентов, которые умеют создавать branch/files/PR, но не умеют `workflow_dispatch`, используется PR trigger только по:

```text
remote-requests/**
```

Runnable unit:

```text
remote-requests/<id>/request.json
remote-requests/<id>/presets.json   # optional
remote-requests/<id>/run.json       # transport-only manifest
```

Temporary generation branch использует namespace:

```text
remote-generation/<id>
```

## Accepted execution semantics

- exact workflow checkout SHA является generator revision;
- никакого secondary checkout `main` или установки другой generator revision;
- repository paths проходят traversal/absolute/out-of-workspace safety checks;
- canonical CLI вызывается максимум один раз;
- semantic validation остаётся в application/compiler;
- generation failure не вызывает seed change, reroll, max-attempts increase, constraint relaxation, feature deletion/move или LLM repair;
- generated world data не коммитится в repository;
- generation workflow permissions: `contents: read`;
- local Codex path через `AGENTS.md` + skill сохраняется параллельно.

## Artifacts

Success:

```text
domain-bundle
technical-preview        # when preview=true
generation-diagnostics
```

Failure:

```text
generation-diagnostics
+ failed workflow status
```

Diagnostics включают execution metadata, snapshots request/presets, stdout/stderr. Они не входят в canonical DomainBundle.

Technical preview публикуется отдельно для удобного retrieval. Возможность конкретного chat host показать downloaded PNG inline проверяется первым реальным end-to-end run и не является частью generator semantics.

## Temporary branch cleanup

Remote-generation branches являются эфемерным transport state и не должны накапливаться.

Lifecycle:

```text
create remote-generation/<id>
→ write remote-requests/<id>/...
→ open generation PR
→ run workflow
→ retrieve artifacts/diagnostics
→ close PR without merge
→ delete remote-generation/<id>
```

Generation workflow остаётся read-only. Автоматический cleanup изолирован в отдельный workflow, запускаемый только после `pull_request: closed`, с минимальным `contents: write` и строгой проверкой same-repository branch prefix `remote-generation/`.

Cleanup не влияет на результат уже завершённой generation. Если он не сработал, ветка удаляется вручную позднее. Workflow artifacts остаются привязаны к workflow run согласно retention policy; удаление temporary branch не является удалением run/artifacts.

## Implementation slice

Следующий отдельный implementation PR должен добавить минимум:

```text
.github/workflows/generate-domain.yml
.github/workflows/cleanup-remote-generation.yml
scripts/remote_generation.py
docs/integrations/github-actions-generation.md
remote-requests/example/
tests/test_github_actions_generation_adapter.py
```

`scripts/remote_generation.py` остаётся repository integration helper вне `src/domain_generator`.

Tests должны покрыть triggers, generation read-only permissions, exact checkout contract, path safety, canonical CLI single invocation, artifacts/diagnostics, no reroll/repair, а также закрытый-PR cleanup только для same-repository `remote-generation/` branches.

После implementation merge обязателен первый реальный end-to-end generation run через temporary `remote-generation/**` branch + `remote-requests/**` PR с artifact retrieval, PR close и branch cleanup.

## Merge rule

Design уже принят. Docs-only design PR может быть смержен после зелёного CI.

Implementation PR НЕ merge-ится без отдельного явного пользовательского принятия.

После этого:

```text
M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.