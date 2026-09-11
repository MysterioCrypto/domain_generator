# domain_generator

Procedural domain generation engine with constrained randomness.

## Start here

- [`PROJECT.md`](PROJECT.md) — current canonical project state and invariants.
- [`docs/roadmap.md`](docs/roadmap.md) — Core 0.1 milestones.
- [`docs/architecture.md`](docs/architecture.md) — current architecture.
- [`docs/glossary.md`](docs/glossary.md) — shared terminology.
- [`docs/decisions/`](docs/decisions/) — accepted architecture decisions and their rationale.

## Core principle

The generator core is independent from ChatGPT/OpenAI-specific tooling, GitHub Actions, campaign-specific lore, and any particular renderer. Human/LLM interaction produces formal input; the deterministic core produces structured domain data.

## Development status

The project is currently in the architecture/foundation phase. Generator implementation has not started yet.

## Documentation rule

Normative project documents use machine-readable YAML front matter plus human-readable Markdown. Illustrative examples are explicitly marked `normative: false` and must not silently become Core requirements.
