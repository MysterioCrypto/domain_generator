# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/roadmap.md`.
3. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
4. Прочитать `docs/design/canonical-cli-python-entrypoint-v0.1.md`.
5. Прочитать `docs/design/local-model-skill-adapter-v0.1.md`.
6. Соблюдать INV-006: существенные изменения сначала обсуждаются и документируются.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

M0–M10 Core 0.1 функционально завершены. Canonical Python/application/CLI boundary реализован и merged через PR #44. Post-merge status sync — PR #45.

Core release gate остаётся M11 Acceptance Suite. Текущий integration checkpoint — принятый design `Local Model Skill / Adapter v0.1`.

## Canonical generator boundary

```text
GenerationRequest + external PresetCatalog
        ↓
PresetRegistry + CORE_OPERATOR_IDS
        ↓
generate_domain(...)
        ↓
Compiler
→ Layout
→ Terrain
→ Hydrology
→ Surface
→ Dependent Placement
→ Final Validation
→ deterministic selection
→ DomainData Assembler
        ↓
DomainAssembly
   ├─ DomainBundle Export
   └─ optional Technical Renderer
        ↓
atomic application output
```

## Local Model Skill / Adapter v0.1 — design accepted

Normative document:

```text
docs/design/local-model-skill-adapter-v0.1.md
```

Accepted architecture:

```text
user intent
  + base GenerationRequest
  + PresetCatalog
  + optional PresetGuideCatalog
        ↓
model-facing authoring context
        ↓
provider-neutral model host
        ↓
LocalModelDecision
        ├─ needs_clarification → return questions, no generation
        └─ ready
             ↓
        contract validation
             ↓
        registry/compiler preflight
             ↓
        max 2 technical repairs after initial draft
             ↓
        exactly one semantic application run
             ↓
        DomainBundle + optional technical preview
```

Key rules:

- LLM/provider dependencies do not enter Core/base package requirements;
- adapter uses public application/compiler APIs, not internal stages;
- model-facing catalog view is deterministic projection of canonical `PresetCatalog`;
- optional guide may explain preset meaning but cannot redefine ranges/capabilities;
- base request carries technical defaults explicitly;
- model decision contract is `ready` or `needs_clarification`;
- maximum three model drafts total: initial + repair #1 + repair #2;
- repair is technical only and cannot silently change seed, user-requested features, hard constraints or generation policy;
- successful preflight is followed by one application generation call;
- generation failure returns to caller, no hidden semantic replanning/reroll;
- technical preview is not fed into an autonomous aesthetic regeneration loop;
- audit stores final request, assumptions/questions, preflight diagnostics and input digests, not chain-of-thought;
- concrete Ollama/llama.cpp/OpenAI backend is out of scope v0.1.

## Следующий шаг после docs merge

Отдельный implementation PR для bounded provider-neutral adapter slice:

```text
adapter contracts
→ model-facing preset projection
→ guide validation
→ base request/edit policy
→ model Protocol/callback
→ decision parsing
→ compiler preflight
→ max-two-repair orchestration
→ one-generation execution boundary
→ structured audit result
→ reference skill/instruction artifact
→ tests
```

Implementation PR не merge-ить без отдельного `Принято.` пользователя.

## После Local Model Adapter

```text
Remote GitHub Actions Generation Adapter
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.
