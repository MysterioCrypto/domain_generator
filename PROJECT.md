---
project: domain_generator
target_version: core-0.2
phase: surface-climate-redesign
status: in-progress
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
development_branch: dev/0.2
current_milestone: v0.2-batch-c2-effective-surface-moisture
checkpoint: c1-annual-climate-accepted
next_topic: design-c2-effective-surface-moisture
working_context: docs/CONTEXT.md
progress_tree: docs/PROGRESS.md
accepted_designs:
  - continuous-terrain-foundation-v0.2
  - continuous-drainage-routing-v0.2
  - low-bias-contributing-area-v0.2
  - channel-skeleton-extraction-v0.2
  - terrain-aware-channel-initiation-v0.2
  - additive-terrain-aware-source-promotion-v0.2
  - multiscale-drainage-hierarchy-v0.2
  - lake-shoreline-morphology-v0.2
  - nested-depression-hierarchy-diagnostic-v0.2
  - annual-climate-forcing-v0.2
completed:
  - core-0.1-prealpha-infrastructure
  - core-0.1-m11-acceptance-suite
  - core-0.1-local-portability-hardening
  - core-0.1-codex-and-remote-generation-integrations
  - core-0.2-continuous-terrain-foundation
  - core-0.2-domain-provenance-boundary
  - core-0.2-hydrology
  - core-0.2-annual-climate-forcing
rejected_or_superseded:
  - core-0.1-world-generation-semantics
  - guide-renderer-as-fix-for-upstream-world-state
  - v0.2-d8-river-reconstruction-experiment-pr70
  - v0.2-two-receiver-dinf-accumulation-h09-pr72
implemented_integrations:
  - local-model-skill-adapter-v0.1
  - codex-integration-packaging-v0.1
  - remote-github-actions-generation-adapter-v0.1
canonical_documents:
  working_context: docs/CONTEXT.md
  progress_tree: docs/PROGRESS.md
  architecture: docs/architecture.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  continuous_terrain_v0_2: docs/design/continuous-terrain-foundation-v0.2.md
  continuous_drainage_v0_2: docs/design/continuous-drainage-routing-v0.2.md
  low_bias_contributing_area_v0_2: docs/design/low-bias-contributing-area-v0.2.md
  channel_skeleton_extraction_v0_2: docs/design/channel-skeleton-extraction-v0.2.md
  terrain_aware_channel_initiation_v0_2: docs/design/terrain-aware-channel-initiation-v0.2.md
  additive_terrain_aware_source_promotion_v0_2: docs/design/additive-terrain-aware-source-promotion-v0.2.md
  multiscale_drainage_hierarchy_v0_2: docs/design/multiscale-drainage-hierarchy-v0.2.md
  annual_climate_forcing_v0_2: docs/design/annual-climate-forcing-v0.2.md
historical_documents:
  core_0_1_roadmap: docs/roadmap.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — setting-agnostic procedural Core для генерации региональных/глобальных карт.

## Как восстанавливать рабочий контекст

Читать в таком порядке:

```text
PROJECT.md
→ docs/CONTEXT.md
→ docs/PROGRESS.md
→ relevant accepted docs/design/*
→ code/tests
```

- `PROJECT.md` — устойчивая версия, архитектурная граница и активная линия разработки.
- `docs/CONTEXT.md` — rolling semantic context: что принято, что отвергнуто, почему и какой checkpoint сейчас активен.
- `docs/PROGRESS.md` — простое дерево `DONE / IN PROGRESS / NEXT`, чтобы новый чат не реконструировал план из истории PR.
- `docs/design/`, `docs/contracts/`, `docs/decisions/` — нормативные semantics.
- Git/PR history — только для археологии.

## Версионная граница

```text
release/0.1-prealpha
└─ historical; infrastructure proved, world-generation semantics rejected

dev/0.2
└─ active development line
```

Не выводить текущее состояние проекта из `main`.

## Core 0.2: принятая база

### Terrain 0.2 — ACCEPTED

```text
continuous multi-scale base elevation
→ smooth semantic Band spine
→ massif-scale ridge modifier
→ blended Area raise/depress
```

Normative design: `docs/design/continuous-terrain-foundation-v0.2.md`.

### Hydrology 0.2 — ACCEPTED

После отклонённых D8 / two-receiver D∞ / direct MFD-support вариантов текущая сохранённая линия:

```text
Priority-Flood conditioning
→ MFD p=1.1 contributing area
→ continuous MFD vector field
→ dominant one-downstream channel skeleton
→ H09-D2 regional river network
→ H09-E denser potential drainage hierarchy
→ Strahler ordering
```

Текущий H09-E implementation checkpoint:
- regional H09-D2 network сохранён без изменений;
- potential network использует threshold `0.40 × regional T`;
- potential hierarchy: 43 sources, 10 realized confluences, 66 segments;
- max Strahler order 3;
- final potential vector grid-lock ~8.66%;
- regional skeleton coverage by potential scaffold: 100%;
- engine invariants / hard constraints / full pytest: green.

H09-E **ACCEPTED by operator for the river-hierarchy slice**. MFD + H09-D2 regional network + H09-E potential hierarchy are frozen unless a new concrete defect requires reopening them.

Hydrology 0.2 formally ACCEPTED by operator and merged through PR #72 into `dev/0.2`.

## Deferred hydro-surface finishing

Hydrology 0.2 base is frozen. The following cross-layer finishing remains deferred until Surface / climate / biomes provide environmental context:

- размытые/мелкие headwater roots;
- seasonal/minor tributary fan-out;
- estuary/delta/fan semantics там, где известен реальный receiving water;
- cartographic fading/visibility low-order channels.

Это не повод снова менять тело основной реки. Эти детали требуют следующего контекста — climate/biomes/surface и типа receiving water — и поэтому не должны преждевременно встраиваться в текущий regional river skeleton.

Если река просто выходит за границу regional domain, Core не должен рисовать фиктивную дельту: это `domain_outlet`. Delta/estuary имеет смысл только при известном водоёме/побережье-приёмнике.

## Process invariants

INV-001..INV-011 остаются в силе.

Для spatial/procedural semantics:

```text
implementation
→ automated guardrails
→ representative operator-visible render
→ explicit ACCEPT / REJECT
```

Green CI не заменяет human visual acceptance. Визуально удачный render также не отменяет failed invariants.


## Surface / Climate 0.2 — C1 ACCEPTED

C1 annual climate forcing is formally ACCEPTED by operator and merged through PR #81 into `dev/0.2`.

Representative C1-A:
- annual temperature range: ~1.64 .. 11.50 °C;
- temperature/elevation correlation: ~-0.774;
- requested land-mean annual precipitation: 900 mm/year;
- actual land mean: 900 mm/year;
- precipitation p05 / median / p95: ~473 / 796 / 1647 mm/year;
- precipitation maximum: ~3954 mm/year;
- synthetic windward/lee fixture ratio: ~3.22, guard passed.

CI:
- push pytest: GREEN;
- PR pytest: GREEN;
- C1 checkpoint workflow: GREEN.

Accepted C1 interpretation:
- C1 is regional atmospheric forcing, not a planetary moisture-source simulation;
- mean precipitation represents moisture supplied to the regional domain from outside the modeled atmospheric system;
- terrain redistributes that forcing through windward/lee effects;
- local rivers/lakes do not themselves generate the atmospheric precipitation field in C1;
- calibration remains setting-dependent and may be revisited only if a later layer reveals a concrete blocker.

Next bounded layer: climate + hydrology + terrain → effective surface moisture.
