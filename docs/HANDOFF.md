# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. Core release gate — M11 Acceptance Suite. Canonical generation/application/CLI boundary merged.

`Local Model Skill / Adapter v0.1` design был принят и implementation PR #47 смержен. Provider-neutral adapter теперь является частью integration track.

Текущий bounded gate — `Codex Integration Packaging v0.1`.

Normative design:

```text
docs/design/codex-integration-packaging-v0.1.md
```

## Зачем нужен Codex packaging

Programmatic model integration и interactive Codex usage — разные внешние оболочки над одной canonical generator boundary.

```text
Programmatic model
    ↓
LocalModelHost
    ↓
Local Model Adapter
    ↓
canonical application API
```

```text
Codex
    ├─ AGENTS.md
    └─ domain-generator-authoring skill
             ↓
canonical CLI / public application API
```

Codex packaging не добавляет OpenAI dependency в Core и не создаёт отдельный генератор.

## Accepted Codex design

Implementation должен добавить:

```text
AGENTS.md
.codex/skills/domain-generator-authoring/SKILL.md
docs/integrations/codex.md
tests/test_codex_packaging.py
```

`AGENTS.md`:

- действует как короткая карта repository/workflow;
- направляет к `PROJECT.md` и canonical design docs;
- закрепляет docs-before-implementation / separate implementation acceptance;
- отправляет domain authoring/generation задачи к specialized skill;
- запрещает обход canonical application boundary.

Codex skill:

- имеет YAML frontmatter только `name` + `description`;
- trigger description покрывает создание/редактирование/validation/generation domain requests;
- body ссылается на `docs/skills/local-model-authoring-v0.1.md` как provider-neutral semantic reference;
- использует `GenerationRequest`, `PresetCatalog` и `domain-generator generate`;
- сохраняет bounded technical repair policy;
- не делает hidden reroll/replanning после generation failure;
- не вызывает internal generation stages напрямую.

User integration note должна объяснить repository-local usage и optional user-level installation через Codex `$skill-installer` из GitHub directory URL. После user-level install Codex может потребовать restart для discovery skill.

## Проверка implementation

`tests/test_codex_packaging.py` должен статически проверять структуру упаковки, frontmatter, существование repository references, canonical CLI boundary и отсутствие инструкций на прямой вызов внутренних stages.

Сетевой OpenAI/Codex test не нужен.

## Merge rule

После docs-only design PR implementation идёт отдельным PR и не merge-ится без отдельного пользовательского принятия.

## После Codex Integration Packaging

```text
Remote GitHub Actions Generation Adapter — design gate
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.
