# Repository instructions for Codex

Start with the root `PROJECT.md`. If it declares an `active_development_branch`, switch your state inspection to that branch before deciding what the current project task is.

On the active development branch, read:

```text
PROJECT.md
→ docs/CONTEXT.md
→ relevant accepted design under docs/design/
→ code/tests
```

Do not infer current work from `main` code, historical Core 0.1 roadmap text, or PR ordering alone. `main` may intentionally remain an administrative entry point over an older code baseline.

The active branch `docs/CONTEXT.md` is a rolling semantic compression, not an append-only log. It is rewritten only at meaningful checkpoints and should not accumulate ordinary commit/CI history.

Normative architecture and semantics live under `docs/design/`, `docs/contracts/`, and `docs/decisions/` on the active development branch. Follow INV-006 there: substantial architecture changes are documented before implementation and implementation checkpoints require explicit user acceptance where the design specifies it.

For procedural domain authoring, use the repository's `domain-generator-authoring` skill when available and do not bypass the canonical application boundary.
