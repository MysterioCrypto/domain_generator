# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. Core release gate — M11 Acceptance Suite. Canonical generation/application/CLI boundary уже merged.

Normative Local Model Adapter design merged через PR #46. Implementation находится в открытом PR #47 и требует отдельного пользовательского принятия до merge.

Implementation branch:

```text
impl/local-model-adapter-v0.1
```

Clean functional checkpoint до финального status-doc commit:

```text
323 passed
```

Новые 11 tests находятся в `tests/test_local_model_adapter.py`.

## Что реализовано в PR #47

```text
user intent
  + base GenerationRequest
  + canonical PresetCatalog
  + optional PresetGuideCatalog
        ↓
ModelAuthoringContext
        ↓
provider-neutral LocalModelHost Protocol
        ↓
LocalModelDecision
        ├─ needs_clarification
        └─ ready
             ↓
        edit-policy validation
        registry/compiler preflight
             ↓
        max 2 technical repairs after initial draft
             ↓
        one canonical application generation
             ↓
        DomainBundle + optional technical preview
```

Implemented details:

- `src/domain_generator/adapters/local_model.py` and public adapter namespace;
- deterministic preset projection, sorted by canonical preset/parameter ids;
- projection preserves fixed/range/choice semantics from canonical `PresetCatalog`;
- adapter-only `PresetGuideCatalog` and consistency validation;
- `LocalModelEditPolicy` with seed/simulation/hydrology/surface/generation-config changes forbidden by default;
- `ReadyDecision` and `NeedsClarificationDecision`;
- provider-neutral `LocalModelHost.create_decision(context)` Protocol;
- Pydantic parsing of typed/mapping/JSON model drafts;
- compiler preflight before any generation;
- initial draft + maximum two technical repairs;
- edit-policy/compiler/decision diagnostics passed into subsequent repair context;
- generation occurs exactly once after successful preflight;
- generation/output failure does not call the model again;
- no visual feedback/reroll loop;
- SHA-256 audit digests for base request/catalog/guide/final request;
- audit stores diagnostics/counts/result but not model chain-of-thought;
- reference model instruction: `docs/skills/local-model-authoring-v0.1.md`.

No concrete Ollama, llama.cpp, OpenAI or other provider dependency was added.

## Tests added

The adapter tests cover:

- canonical projection order/ranges;
- invalid guide references;
- hidden seed edit rejection;
- clarification without generation;
- invalid draft → repair → exactly one generation;
- maximum three drafts total;
- compiler preflight failure without generation;
- generation failure without model retry;
- edit-policy diagnostic and repair;
- bounded `max_repairs`;
- stable audit digests and no reasoning field.

Full suite after warning cleanup: `323 passed`.

## Merge rule

PR #47 MUST remain unmerged until a separate explicit user acceptance of the implementation checkpoint.

After acceptance/merge:

```text
Remote GitHub Actions Generation Adapter — design gate
→ implementation
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer remains a separate downstream track.
