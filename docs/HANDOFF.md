# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. Core release gate — M11 Acceptance Suite. Canonical generation/application/CLI boundary merged.

`Local Model Skill / Adapter v0.1` implemented and merged through PR #47.

`Codex Integration Packaging v0.1` design merged through PR #48. Implementation находится в открытом PR #49 и требует отдельного пользовательского принятия до merge.

Implementation branch:

```text
impl/codex-integration-packaging-v0.1
```

Functional checkpoint до финального status-doc commit:

```text
330 passed
```

Новые 7 tests находятся в `tests/test_codex_packaging.py`.

## Что реализовано в PR #49

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

Implementation details:

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
- user-level location is documented as `$CODEX_HOME/skills` with restart guidance;
- no OpenAI API client, CodexHost, MCP server or provider dependency was added.

## Tests added

Packaging tests cover:

- required files exist;
- exact minimal frontmatter keys;
- skill name matches directory id;
- `AGENTS.md` routes to project status/skill/canonical CLI and test command;
- referenced canonical repository documents exist;
- skill uses `domain-generator generate`, bounded repair, one-generation/no-reroll semantics;
- manual canonical-output editing is prohibited;
- integration note includes repository-local and `$skill-installer` installation paths.

Full suite before final status-doc commits: `330 passed`.

## Merge rule

PR #49 MUST remain unmerged until a separate explicit user acceptance of this implementation checkpoint.

After acceptance/merge:

```text
Remote GitHub Actions Generation Adapter — design gate
→ implementation
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer remains a separate downstream track.
