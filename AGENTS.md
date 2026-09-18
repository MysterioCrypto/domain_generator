# Repository instructions for Codex

Read `PROJECT.md` first for the stable version boundary and active development line, then read `docs/CONTEXT.md` for the current semantic checkpoint, rejected paths that still constrain the work, and the next bounded task. Do this before inferring current state from `main`, PR chronology, or historical roadmap documents.

`docs/CONTEXT.md` is intentionally a rolling context compression, not an append-only log. Rewrite it when a meaningful project checkpoint changes (accepted/rejected human checkpoint, accepted design gate, active-line change, or completed implementation that changes what comes next). Do not update it for ordinary commits, CI runs, small bugfixes, or refactors that do not change the semantic checkpoint. Remove stale details instead of accumulating history.

Use `docs/HANDOFF.md` only as a compatibility pointer. Normative architecture and semantics live under `docs/design/`, `docs/contracts/`, and `docs/decisions/`. Historical documents such as the Core 0.1 roadmap must not override `PROJECT.md` + `docs/CONTEXT.md` for current work.

For requests that create, revise, validate, troubleshoot, or generate a procedural domain/region, use the `domain-generator-authoring` skill in `.codex/skills/domain-generator-authoring/SKILL.md` when available.

Do not bypass the canonical application boundary. Domain authoring should produce or revise `GenerationRequest` / `PresetCatalog` inputs and use the public application API or `domain-generator generate`. Do not directly call internal generation stages to satisfy an end-user authoring request, and do not edit canonical generated `.npy`/`domain.json` outputs as a substitute for changing the request.

Follow INV-006: substantial architecture changes are discussed and documented before implementation. Accepted design documentation is merged before runtime implementation. Implementation pull requests are not merged until the user explicitly accepts the implementation checkpoint.

When changing code, run the relevant tests; the default full verification is:

```bash
python -m pytest
```

Keep the repository setting-agnostic. Setting/campaign content, provider-specific LLM integrations, and presentation/image-generation layers stay outside procedural Core unless an accepted design explicitly changes that boundary.
