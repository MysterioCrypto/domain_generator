---
name: domain-generator-authoring
description: Use when Codex is asked to create, revise, validate, troubleshoot, or generate a procedural domain/region with this repository, including natural-language map descriptions, GenerationRequest editing, PresetCatalog-driven authoring, compiler/input repair, DomainBundle generation, or technical preview generation.
---

# Domain Generator Authoring

Use the repository's canonical authoring and application boundaries. Do not invent a second Codex-only generation path.

## Read only the context you need

Start with:

- `PROJECT.md` for current project status and boundaries;
- `docs/skills/local-model-authoring-v0.1.md` for provider-neutral authoring policy;
- `docs/design/codex-integration-packaging-v0.1.md` for this integration contract;
- `docs/design/canonical-cli-python-entrypoint-v0.1.md` when CLI/application details matter.

Do not load every design document unless the task requires it.

## Author from canonical inputs

Identify the base `GenerationRequest` and canonical `PresetCatalog` for the requested generation. If the repository/task provides an optional guide, use it only as semantic help; the real catalog defines supported preset ids, operators, parameters, ranges, and choices.

If a necessary base request or preset catalog cannot be determined from the user's files or repository context, state which artifact is missing instead of inventing capabilities.

Preserve technical defaults from the base request unless the user's intent explicitly requires changing them. Prefer changing domain id/label/size, features, feature parameters, and constraints. Do not silently change seed, simulation settings, hydrology/surface technical constants, or generation policy to make generation easier.

## Validate before semantic generation

Validate the request and catalog through the repository's public contracts/compiler/application APIs. Technical drafting follows this bounded policy:

1. Produce the initial draft.
2. If parsing, contract, registry, or compiler validation fails, repair only the reported technical problem.
3. Allow at most two technical repair drafts after the initial draft.
4. Do not use repair to change user intent, remove requested features, weaken hard constraints, change seed for a different result, or enlarge the attempt budget merely to obtain success.

Once preflight succeeds, perform one semantic generation run. If generation exhausts attempts or otherwise fails after successful preflight, report that failure; do not autonomously replan or reroll.

Do not inspect `technical-map.png` and repeatedly alter the request until the image subjectively looks better unless the user explicitly starts a new revision cycle.

## Use the canonical application boundary

For ordinary repository usage, prefer the installed CLI:

```bash
domain-generator generate <request.json> \
  --presets <presets.json> \
  --output <output-dir> \
  --preview
```

If the request contains no features, `--presets` may be omitted according to the canonical CLI contract.

The public Python application API may be used when typed validation or preflight is more convenient. Do not call `layout_stage`, `terrain_stage`, `hydrology_stage`, `surface_stage`, `placement_stage`, or `final_stage` directly for an end-user domain-authoring task.

Do not edit generated canonical `.npy` fields or `domain.json` to change geography. Change the request/preset inputs and regenerate through the canonical boundary.

## Report the result

On success, report the output directory, accepted attempt index when available, and technical preview path when one was requested. Keep assumptions explicit and short.

When clarification is materially necessary, ask the smallest specific question needed instead of making up a setting/capability.
