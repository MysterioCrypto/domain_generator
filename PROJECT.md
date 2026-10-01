---
project: domain_generator
target_version: core-0.2
phase: surface-climate-redesign
status: in-progress
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
development_branch: dev/0.2
current_milestone: v0.2-batch-hydro-surface-finishing
checkpoint: h11-a-potential-drainage-export-ready-for-operator-review
next_topic: operator-review-h11-a-implementation
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
  - effective-surface-moisture-v0.2
  - vegetation-biome-readiness-v0.2
  - potential-drainage-public-export-v0.2
completed:
  - core-0.1-prealpha-infrastructure
  - core-0.1-m11-acceptance-suite
  - core-0.1-local-portability-hardening
  - core-0.1-codex-and-remote-generation-integrations
  - core-0.2-continuous-terrain-foundation
  - core-0.2-domain-provenance-boundary
  - core-0.2-hydrology
  - core-0.2-annual-climate-forcing
  - core-0.2-effective-surface-moisture
  - core-0.2-climate-aware-vegetation
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
  effective_surface_moisture_v0_2: docs/design/effective-surface-moisture-v0.2.md
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


## Surface / Climate 0.2 — C2 ACCEPTED

C2 effective surface moisture is formally ACCEPTED and merged through PR #83 into `dev/0.2`.

Accepted production semantics remain the accepted C2 design:
- climate-driven annual effective surface moisture;
- local actual-water proximity;
- climate-gated contributing-area concentration;
- `cos(slope)^2` retention;
- no additional C2 moisture-noise layer;
- canonical water moisture exactly `1.0`;
- Core 0.1 unchanged.

C2-A with representative `water_moisture_decay_km = 8` was rejected because the actual-water term created broad artificial-looking halos around rivers/lakes. The rejected component was only the representative water-proximity spatial scale.

C2-B changed only the representative decay scale to `2 km`. Terrain, Hydrology, C1, catchment contribution, slope retention and the effective-moisture combination remained unchanged.

Accepted C2-B workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36837227248`

Representative C2-B land result:
- effective moisture p05 / median / p95 ~0.548 / 0.658 / 0.864;
- mean ~0.673;
- land >= 0.8 ~10.4%;
- precipitation correlation ~+0.820;
- temperature correlation ~-0.747;
- distance-to-water correlation ~-0.069;
- water-proximity signal mean ~0.068;
- slope retention mean ~0.99875.

The `2 km` value is accepted representative calibration, not a hard universal constant: `water_moisture_decay_km` remains an explicit required semantic parameter.

PR #83 merge commit:
`de5646a1af9c9057fe13cf1e7eb92bb1a3728e46`

Next bounded layer: INV-006 design gate for C3 vegetation / biome readiness. No C3 runtime implementation before design acceptance.


## Surface / Climate 0.2 — C3 design gate

INV-006 design PR #84 is open as draft:
`https://github.com/MysterioCrypto/domain_generator/pull/84`

Proposed normative document:
`docs/design/vegetation-biome-readiness-v0.2.md`

Proposed bounded semantics:
```text
normalized annual thermal suitability
× accepted C2 effective moisture
+ existing vegetation_bias
-> Core 0.2 vegetation_density

canonical water = 0
```

Design boundaries:
- no direct precipitation term in C3;
- no new vegetation noise;
- no second legacy linear slope penalty;
- Core 0.1 unchanged;
- no biome labels yet;
- no C3 runtime implementation before explicit design ACCEPT.

Operator decision: **C3 DESIGN ACCEPTED**.

Acceptance note:
- this is a formal project/operator acceptance;
- the operator explicitly noted insufficient subject-matter expertise for independent expert ecological validation;
- therefore acceptance authorizes implementation under the agreed bounded semantics but is not evidence of expert scientific validation.

Design PR #84 merged:
`2ad695d059b4f198b5f06c6451b005c0d630fbc9`

Next: implement C3 on a separate branch with V01–V11 guardrails and an operator-visible C3-A checkpoint.


## Surface / Climate 0.2 — C3-A implementation checkpoint

Implementation PR #85:
`https://github.com/MysterioCrypto/domain_generator/pull/85`

Branch:
`impl/v0.2-c3-vegetation-biome-readiness`

Current semantic head:
`eb1365759f891991e8614f712eb1db7ab7da2bae`

C3-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36842261493`

Artifact:
`surface-v02-c3`

Automation:
- push pytest GREEN;
- pull-request pytest GREEN;
- C3-A checkpoint GREEN;
- V01–V11 GREEN.

Representative vegetation:
- p05 / median / p95 ~0.261 / 0.297 / 0.348;
- mean ~0.299;
- min / max ~0.181 / 0.400;
- effective-moisture correlation ~+0.369;
- temperature correlation ~+0.330;
- precipitation correlation ~+0.290;
- slope correlation ~-0.169;
- distance-to-water correlation ~-0.178.

Interpretation:
- no single driver dominates;
- accepted C2 moisture remains visible;
- thermal suitability moderates cold/wet terrain;
- no second legacy slope penalty;
- no extra vegetation noise;
- canonical water vegetation remains exactly zero.

Important semantic caveat:
`vegetation_density` in C3 is an abstract normalized ecological potential/density index. It is not canopy-cover percentage and not literal NPP; absolute values such as 0.30 must not be read as 30% physical vegetation cover.

Operator decision: **C3-A IMPLEMENTATION ACCEPTED**.

Implementation PR #85 merged into `dev/0.2`:
`37e213ebf5f82ebfae149d21088c07e08d836549`

C3 is now frozen unless later evidence identifies a concrete defect.

Mountain influence clarification:
- C3 has no second direct slope penalty;
- elevation affects vegetation through C1 lapse-rate temperature;
- terrain affects precipitation through C1 windward/lee forcing;
- slope affects moisture through accepted C2 `cos²(slope)` retention;
- terrain-shaped drainage affects C2 catchment/water signals;
- therefore mountains influence vegetation through accepted physical/environmental layers without double-counting slope.

Next bounded area: revisit deferred hydro-surface finishing now that climate/moisture/vegetation context exists.


## Hydrology 0.2 — H11-A public potential-drainage export design

Design PR #86:
`https://github.com/MysterioCrypto/domain_generator/pull/86`

Proposed document:
`docs/design/potential-drainage-public-export-v0.2.md`

Readiness audit:
- perennial / seasonal / dry classification remains blocked by missing seasonality/baseflow/groundwater semantics;
- lake vs wetland/playa/dry-basin classification remains blocked by missing water-balance/permanence semantics;
- delta/estuary/fan remains blocked by missing known receiving-environment/process context;
- low-order/headwater visibility is presentation-ready, but currently the accepted potential hierarchy is not exposed at the public DomainData boundary.

Proposed H11-A:
```text
Core 0.2:
networks["rivers"]              = accepted H09-D2 regional network
networks["potential_drainage"]  = accepted H09-E potential network
```

No routing, geometry, water-depth, climate, moisture or vegetation changes.

Operator decision: **H11-A DESIGN ACCEPTED**.

Design PR #86 merged:
`712dae3179605b894558a9e399cd6929ffcda459`

Acceptance scope:
- public export boundary only;
- no routing/network geometry changes;
- no Strahler public metadata extension;
- no perennial/seasonal/dry labels;
- no basin-regime or delta/estuary/fan inference.

Next: implement H11-A on a separate branch with X01–X08 and operator-visible contract evidence.


## Hydrology 0.2 — H11-A implementation checkpoint

Implementation PR #87:
`https://github.com/MysterioCrypto/domain_generator/pull/87`

Branch:
`impl/v0.2-potential-drainage-export`

Semantic head:
`b77d3247577c552117ba6bf4567d4e7563f062b1`

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36845608659`

Automation:
- X01–X08 GREEN;
- push pytest GREEN;
- PR pytest GREEN;
- H11-A checkpoint GREEN.

Representative public boundary:
```text
networks:
  rivers
  potential_drainage

regional runtime/export:
  58 nodes / 33 segments
  exact equality = true

potential runtime/export:
  111 nodes / 66 segments
  exact equality = true

upstream canonical field hashes unchanged = true
```

Implementation note:
the first checkpoint exposed a historical runtime `DomainData` validator that enforced the Core 0.1 single-network restriction even for 0.2 provenance. The bounded fix makes allowed network IDs version-aware:
- 0.1: `rivers` only;
- 0.2: `rivers` plus `potential_drainage`.

No root DomainData version bump and no arbitrary extra network IDs.

Current gate: **H11-A IMPLEMENTATION — OPERATOR REVIEW**.
Do not merge PR #87 before explicit ACCEPT / REJECT.
