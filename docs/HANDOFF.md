# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. Core release gate — M11 Acceptance Suite. Canonical generation/application/CLI boundary merged.

`Local Model Skill / Adapter v0.1` implemented and merged through PR #47.

`Codex Integration Packaging v0.1` design merged through PR #48, implementation accepted and merged through PR #49.

Implementation merge commit:

```text
495fca9b85c56074f4a3c881e12a01f6689ed440
```

Clean implementation suite:

```text
330 passed
```

Новые 7 tests находятся в `tests/test_codex_packaging.py`.

## Что теперь доступно для Codex

```text
Codex
  ├─ AGENTS.md
  └─ .codex/skills/domain-generator-authoring/SKILL.md
             ↓
GenerationRequest + PresetCatalog
             ↓
canonical CLI / public application API
             ↓
DomainBundle + optional technical preview
```

Merged integration details:

- root `AGENTS.md` provides concise project/workflow routing;
- root instructions route domain authoring/generation work to `domain-generator-authoring`;
- skill uses Codex-compatible YAML frontmatter with only `name` and `description`;
- trigger metadata covers creation, revision, validation, troubleshooting, generation, DomainBundle and preview tasks;
- skill points to `docs/skills/local-model-authoring-v0.1.md` for provider-neutral semantic policy;
- skill requires actual base `GenerationRequest` / canonical `PresetCatalog` rather than invented capabilities;
- technical repair is bounded to initial draft + maximum two repairs;
- successful preflight is followed by one semantic generation run;
- generation failure does not trigger hidden replanning/reroll;
- internal generation stages are explicitly rejected as end-user authoring entrypoints;
- canonical `.npy` / `domain.json` outputs are not manually edited to alter world geography;
- `docs/integrations/codex.md` explains repository-local use and user-level installation via `$skill-installer` from the GitHub skill directory;
- no OpenAI API client, CodexHost, MCP server or provider dependency was added.

## Следующий bounded gate

```text
Remote GitHub Actions Generation Adapter — design gate
```

Следующий design должен определить remote wrapper вокруг существующего `domain-generator generate`:

- какие request/catalog inputs принимает workflow;
- как фиксируется exact generator revision;
- какие canonical/noncanonical artifacts публикуются;
- как передаются ошибки и provenance;
- как гарантируется, что GitHub Actions не становится вторым генератором и не меняет semantics Core.

После design acceptance:

```text
Remote GitHub Actions Generation Adapter — implementation
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.
