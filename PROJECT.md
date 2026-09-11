---
project: domain_generator
target_version: core-0.1
phase: foundation
status: in-progress
current_milestone: M0-project-foundation
next_milestone: M1-data-contracts
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006]
---

# Project state

This file is the short canonical entry point for a new chat or agent.

## Goal

Build an independent procedural domain-generation core with constrained randomness. User intent becomes a formal specification; the core produces deterministic structured domain data and debug outputs.

## Current state

Milestone `M0 — Project foundation` is in progress. We are creating the external project memory and architecture documents. Generator code has not started.

## Next

`M1 — Data contracts`: define `DomainSpec v0.1`, `GenerationPlan v0.1`, and `DomainData v0.1` before implementing terrain generation.

## Invariants

- **INV-001:** Core is independent from ChatGPT/OpenAI, GitHub Actions, a specific chat, Valhalla lore, and any renderer.
- **INV-002:** `DomainSpec` describes intent and constraints; `DomainData` describes the generated result.
- **INV-003:** Same supported `DomainSpec + root seed + generator version` produces the same result.
- **INV-004:** Examples are non-normative and must not silently become generator rules.
- **INV-005:** Core uses generic fields, networks, features, spatial primitives, and constraints instead of campaign-specific special cases.
- **INV-006:** Significant architecture changes are explained and discussed before implementation; documentation is updated before code.

## Working rule

At the end of each milestone update this file with: what works, guarantees added, remaining limitations, decisions made, and the next milestone.
