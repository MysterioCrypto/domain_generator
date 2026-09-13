# Repository instructions for Codex

Read `PROJECT.md` first for the current checkpoint, accepted designs, and next bounded task. Use `docs/HANDOFF.md` only as an operational summary; normative architecture and semantics live under `docs/design/`, `docs/contracts/`, and `docs/decisions/`.

For requests that create, revise, validate, troubleshoot, or generate a procedural domain/region, use the `domain-generator-authoring` skill in `.codex/skills/domain-generator-authoring/SKILL.md` when available.

Do not bypass the canonical application boundary. Domain authoring should produce or revise `GenerationRequest` / `PresetCatalog` inputs and use the public application API or `domain-generator generate`. Do not directly call internal generation stages to satisfy an end-user authoring request, and do not edit canonical generated `.npy`/`domain.json` outputs as a substitute for changing the request.

Follow INV-006: substantial architecture changes are discussed and documented before implementation. Accepted design documentation is merged before runtime implementation. Implementation pull requests are not merged until the user explicitly accepts the implementation checkpoint.

When changing code, run the relevant tests; the default full verification is:

```bash
python -m pytest
```

Keep the repository setting-agnostic. Setting/campaign content, provider-specific LLM integrations, and presentation/image-generation layers stay outside procedural Core unless an accepted design explicitly changes that boundary.
