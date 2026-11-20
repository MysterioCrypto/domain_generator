---
project: domain_generator
target_version: core-0.2
phase: post-release-development
status: in-progress
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
development_branch: dev/0.2
release_branch: release/0.2-prealpha
release_commit: c69c1af010a085fb80d248af703a77471fc6c9d7
current_milestone: v0.2-non-earth-product-readiness
checkpoint: source-grounded-world-fixtures-and-repository-navigation
next_topic: recover-geodata-and-render-genuinely-distinct-regional-fixtures
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
  - placement-environmental-site-metrics-v0.2
  - environmental-seasonality-v0.2
  - koppen-geiger-climate-regimes-v0.2
  - marine-coastal-boundary-v0.2
  - gross-catchment-precipitation-input-v0.2
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
  - core-0.2-potential-drainage-public-export
  - core-0.2-placement-environmental-site-metrics
  - core-0.2-integrated-acceptance
  - core-0.2-release-metadata-hardening
  - core-0.2-c4-environmental-seasonality
  - core-0.2-c5-koppen-geiger-climate-regimes
  - core-0.2-h12-marine-coastal-boundary
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

**Context-map freshness invariant (working rule):** после каждого принятого дизайна, merge, диагностически значимого исправления или смены checkpoint синхронизировать оба вида внешнего состояния:
- **план/статус:** `PROJECT.md`, `docs/PROGRESS.md` (DONE / IN PROGRESS / NEXT, PR/SHA);
- **семантическая карта:** `docs/CONTEXT.md` (dependency DAG, инварианты, причины решений, оставшиеся blockers, следующий gate);
- при изменении контрактной архитектуры — `docs/architecture.md` и нормативный `docs/design/*`;
- `docs/CHAT-HANDOFF.md` обновлять вместе с checkpoint, но он всегда ниже по приоритету, чем три канонических документа.

Не накапливать в начале канонических файлов устаревший `CURRENT`: исторические checkpoint-блоки должны быть явно помечены как исторические. При потере чата допустима потеря максимум одного незавершённого смыслового шага.


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

Operator decision: **H11-A IMPLEMENTATION ACCEPTED**.

Implementation PR #87 merged into `dev/0.2`:
`cef91e81c86c64555ae1e1363d7ffaf2934ff6ce`

Accepted public boundary:
```text
Core 0.1:
  networks["rivers"]

Core 0.2:
  networks["rivers"]
  networks["potential_drainage"]
```

The H09-E potential geometry itself was not modified; H11-A only exposes the already accepted scaffold.

H11-A is frozen unless a concrete public-contract defect appears.

Remaining physical hydro classifications stay deferred:
- perennial / seasonal / dry;
- lake vs wetland/playa/dry basin;
- delta / estuary / fan.

Next active area: **Placement continuation / readiness audit**.


## Placement 0.2 — P08-A environmental site metrics design

Placement readiness audit result:
- candidate lattice: KEEP;
- reservation containment: KEEP;
- footprint semantics: KEEP;
- hard requirements: KEEP;
- preference scoring / near-best / weighted selection: KEEP;
- existing physical metrics: KEEP;
- `moisture_mean` now observes accepted C2 in Core 0.2;
- `vegetation_density_mean` now observes accepted C3 in Core 0.2.

Design PR #88:
`https://github.com/MysterioCrypto/domain_generator/pull/88`

Proposed Core 0.2-only metrics:
```text
temperature_mean
annual_precipitation_mean
distance_to_potential_drainage
```

`distance_to_potential_drainage` means exact geometric proximity to the accepted H09-E drainage scaffold, not distance to permanent water.

No candidate-generation or site-selection algorithm changes are proposed.

Operator decision: **P08-A DESIGN ACCEPTED**.

Design PR #88 merged:
`66003288e528fc340663d92f84ed14cbee88744b`

Accepted scope:
- Core 0.1 site metric registry remains unchanged;
- Core 0.2 adds only `temperature_mean`, `annual_precipitation_mean`, `distance_to_potential_drainage`;
- existing C2/C3-backed metrics keep their IDs;
- candidate lattice / requirements / scoring / near-best / final selection semantics remain unchanged;
- potential drainage proximity is geometry proximity, not permanent-water access.

Next: separate implementation branch with P01–P11 and representative diagnostic checkpoint.


## Placement 0.2 — P08-A implementation checkpoint

Implementation PR #89:
`https://github.com/MysterioCrypto/domain_generator/pull/89`

Branch:
`impl/v0.2-placement-environmental-site-metrics`

Semantic head:
`ec59e0b6693c10fb6064ebf4b68d7f8c019097e8`

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36849780012`

Automation:
- P01–P11 GREEN;
- push pytest GREEN;
- PR pytest GREEN;
- P08-A checkpoint GREEN.

Implemented registry:
```text
Core 0.1:
  historical 8 metrics only

Core 0.2:
  historical 8
  + temperature_mean
  + annual_precipitation_mean
  + distance_to_potential_drainage
```

Representative diagnostic fixture:
- 148 candidate sites;
- 133 valid under fixture-only requirements;
- 1 near-best;
- selected x≈23.326 km, y≈38.308 km;
- selected suitability ≈0.895.

New metric ranges:
- temperature_mean ~2.96..11.34 °C, median ~8.24;
- annual_precipitation_mean ~302..3243 mm/year, median ~794;
- distance_to_potential_drainage 0..~23.69 km, median ~4.38.

Integrity:
- upstream canonical hashes unchanged;
- potential drainage network unchanged;
- candidate lattice/scoring/selection semantics unchanged.

The diagnostic placement recipe is test evidence only, not a hidden production settlement policy.

Operator decision: **P08-A IMPLEMENTATION ACCEPTED**.

Implementation PR #89 merged into `dev/0.2`:
`57e77c8de6ac8668ddd09e25167e30aa773cf645`

Accepted Placement 0.2 observation boundary:
- Core 0.1 registry remains the historical eight metrics;
- Core 0.2 adds `temperature_mean`, `annual_precipitation_mean`, `distance_to_potential_drainage`;
- `moisture_mean` observes C2;
- `vegetation_density_mean` observes C3;
- candidate generation / filtering / scoring / near-best / weighted selection remain unchanged.

P08-A is frozen unless a concrete metric/contract defect appears.

Next: audit the remaining Placement boundary and choose one bounded follow-up slice.


## Core 0.2 integrated acceptance hardening

Placement next-slice audit found no additional Core 0.2 semantic gap after P08-A:
- existing preset/plan `SiteProfile.metric` contract already carries the new metric IDs;
- compiler does not require a new schema shape;
- deferred-to-deferred POI, roads and human geography remain higher-layer work rather than missing base Placement semantics.

Placement 0.2 is therefore considered Core-ready at the current scope.

Hardening PR #90:
`https://github.com/MysterioCrypto/domain_generator/pull/90`

Purpose:
- add an end-to-end Core 0.2 acceptance fixture;
- exercise new P08-A metrics through normal preset/compiler path;
- cover Terrain/Hydrology/C1/C2/C3/Placement/DomainData/bundle/exact replay together;
- freeze a deterministic baseline after review.

No world-generation semantics change.

A08 Core 0.2 integrated acceptance is GREEN and merged through PR #90.

Merge commit:
`568eeff9676ee387d5837cfb1fca1a8ff087e99b`

Accepted frozen A08:
- full spec/preset/compiler/runtime/assembly/bundle path;
- exact replay GREEN;
- 6 Core 0.2 canonical fields;
- regional network 49 nodes / 31 segments;
- potential drainage 104 nodes / 73 segments;
- dependent placement consumes P08-A metrics through normal preset SiteProfile;
- full pytest GREEN.

No world-generation semantics changed in A08.

Current checkpoint: **CORE 0.2 RELEASE HARDENING — METADATA / DOC CONSISTENCY**.


Release-hardening PR #91:
`https://github.com/MysterioCrypto/domain_generator/pull/91`

Planned identity change:
`0.1.0.dev0 -> 0.2.0.dev0`

Expected acceptance impact:
- plan fingerprints change;
- DomainData hashes change through provenance;
- numerical world fields and semantic geometry must remain unchanged.

A01–A08 are temporarily PENDING on the hardening branch only to emit exact post-bump snapshots.


## Core 0.2 release-candidate readiness

Release metadata hardening PR #91 merged:
`5cafb8119050f19765447d65dcef022ebebe052b`

Generator development identity:
`0.2.0.dev0`

Merge-head full pytest:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36853774759`
— GREEN.

Release-readiness evidence:
- Terrain 0.2 ACCEPTED;
- Hydrology 0.2 ACCEPTED;
- C1 annual climate ACCEPTED;
- C2 effective moisture ACCEPTED;
- C3 climate-aware vegetation ACCEPTED;
- H11-A public potential drainage ACCEPTED;
- P08-A environmental Placement metrics ACCEPTED;
- A08 integrated spec→bundle exact-replay acceptance GREEN;
- A01–A08 baselines GREEN after provenance-only version re-sign;
- package/module version aligned at `0.2.0.dev0`;
- README and canonical architecture identify Core 0.2 as active;
- no known world-state or contract blocker remains inside the accepted Core 0.2 scope.

Explicitly deferred beyond this release scope:
- perennial / seasonal / dry channel classification;
- lake vs wetland/playa/dry-basin classification;
- delta/estuary/fan process morphology;
- true biome labels / seasonality model;
- roads, human geography and deferred-to-deferred POI graphs.

Operator decision: **CORE 0.2 RELEASE CANDIDATE ACCEPTED**.

Frozen release line:
`release/0.2-prealpha`

Exact release freeze commit:
`c69c1af010a085fb80d248af703a77471fc6c9d7`

The branch was created directly from the accepted `dev/0.2` head before any post-release documentation commits.

Release scope is frozen:
- no deferred new world semantics are to be added to `release/0.2-prealpha`;
- fixes on the release line must be bounded release/blocker corrections only;
- new semantic work resumes on the development line after release closure.

Current state: **CORE 0.2 PREALPHA RELEASE FROZEN**.

Next: select the next post-release semantic layer on `dev/0.2` without reopening accepted Core 0.2 layers speculatively.


## Post-release C4-A — Environmental Seasonality design

Dependency audit result:
- true biome classification remains premature on annual-only climate;
- perennial/seasonal/dry drainage also remains underdetermined while seasonality/baseflow are absent;
- therefore the next bounded environmental layer is seasonality, not biome labels.

Design PR #92:
`https://github.com/MysterioCrypto/domain_generator/pull/92`

Proposed C4-A:
- optional explicit seasonality recipe under Core 0.2 climate;
- 12 climatological monthly temperature fields derived from accepted annual temperature;
- 12 monthly precipitation fields whose sum equals accepted annual precipitation;
- explicit temperature peak month and amplitude;
- explicit precipitation peak month and log-amplitude;
- no latitude/hemisphere inference;
- no monthly noise;
- no seasonal wind changes;
- C2/C3 remain unchanged during C4-A;
- no biome or stream-permanence classification yet.

Compatibility:
- absence of `climate.seasonality` preserves frozen prealpha annual-only behavior;
- `release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.

Operator decision: **C4-A DESIGN ACCEPTED**.

Design PR #92 merged into `dev/0.2`:
`e729d836d29df790fa1c0056e7b686d6189703f9`

Accepted scope:
- optional explicit monthly climatological envelope for Core 0.2;
- exact annual temperature-mean and precipitation-total conservation;
- explicit peak months/amplitudes only;
- no latitude/hemisphere inference;
- no monthly climate noise or seasonal wind rotation;
- accepted annual C1 remains canonical;
- C2/C3 remain unchanged during C4-A;
- no biome or flow-permanence classification yet;
- absence of seasonality recipe preserves frozen prealpha annual-only behavior.

Implementation PR #93:
`https://github.com/MysterioCrypto/domain_generator/pull/93`

Semantic head:
`5b9b4e7341bfb3c8b496f25b3e9f741128f31b2a`

C4-A workflow:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36959449118`

Artifact:
`surface-v02-c4`

Automation:
- S01–S13 GREEN;
- JSON Schema snapshots GREEN;
- push full pytest GREEN;
- PR full pytest GREEN;
- C4-A checkpoint GREEN.

Compatibility issue found and fixed during implementation:
- adding optional `seasonality=None` initially changed frozen annual-only spec/plan fingerprints;
- the historical A08 baseline was NOT re-signed;
- fingerprint canonicalization now omits only absent seasonality, restoring exact frozen prealpha fingerprints;
- explicitly configured seasonality remains semantic and changes the plan fingerprint.

Representative C4-A recipe:
```text
temperature amplitude = 7 C
temperature peak      = month 07
precip log amplitude  = 1
precip peak            = month 01
```

Checkpoint evidence:
- all accepted canonical annual fields exact-equal between annual-only and seasonal runs;
- features exact-equal;
- networks exact-equal;
- exactly 24 monthly derived descriptors exported;
- temperature annual-mean max abs conservation error ~4.77e-7 C after float32 persistence;
- precipitation annual-total max abs conservation error ~1.91e-4 mm after float32 persistence.

Visual review:
- month 07 / month 01 temperature fields preserve the same accepted spatial climate pattern with the configured ±7 C seasonal offset;
- monthly precipitation preserves the accepted annual spatial pattern and changes only the climatological fraction;
- configured wettest/driest and warmest/coldest months are correct;
- no hidden monthly spatial noise is visible.

Operator decision: **C4-A IMPLEMENTATION ACCEPTED**.

Implementation PR #93 merged into `dev/0.2`:
`570a5c4730419d17bce69f9e804b805125343fa5`

Accepted post-release C4-A semantics:
- optional explicit 12-month climatological envelope;
- 12 derived monthly temperature fields;
- 12 derived monthly precipitation fields;
- annual C1 climate remains canonical;
- exact annual conservation within persisted float32 tolerance;
- C2 moisture and C3 vegetation remain annual and unchanged;
- no hidden latitude/hemisphere inference;
- no monthly climate noise;
- no seasonal wind rotation;
- no biome or flow-permanence classification;
- no-seasonality requests preserve frozen prealpha annual-only behavior and fingerprints.

C4-A is complete.

Next gate: perform a fresh dependency audit before selecting the next post-release semantic layer. Do not infer that biome labels or flow-permanence are automatically next simply because seasonality now exists; each still needs its remaining dependencies checked.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Post-C4 dependency audit / C5-A design

Audit result:
- perennial / seasonal / dry drainage remains blocked by absent groundwater/baseflow/storage;
- standing lake vs wetland/playa/dry-basin remains blocked by absent basin water-balance/infiltration/permanence;
- delta/estuary/fan remains blocked by absent receiving-environment/process context;
- direct biome labels remain deliberately deferred because they would mix climate regionalization with vegetation/substrate policy.

C4 does fully support one bounded intermediate layer: monthly-temperature/precipitation climate regionalization.

Design PR #94:
`https://github.com/MysterioCrypto/domain_generator/pull/94`

Proposed C5-A:
- opt-in `koppen_geiger_local_season_v1`;
- derived `uint8` field `climate_regime_koppen_geiger`;
- fixed 30-class Beck/Peel-style codebook;
- B arid class precedence;
- explicit 0 C C/D boundary;
- local warm/cold half-years anchored to the configured C4 temperature peak month because Core has no latitude/hemisphere semantics;
- no use of C2/C3 to force climate classes;
- no biome labels;
- no hydrologic-permanence inference.

This is climate regionalization, not a biome raster.

Operator decision: **C5-A DESIGN ACCEPTED**.

Design PR #94 merged:
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`

Accepted clarification:
- C1/C4 climate generation remains configurable and does not hard-code hemisphere/region;
- Köppen–Geiger is an optional Earth-derived interpretation layer only;
- non-Earthlike/fantasy worlds may omit classification entirely;
- climate generation must not be tuned to fit Köppen labels;
- exact Beck/Peel group boundary retained: C/D require `Thot > 10 C`, E uses `Thot <= 10 C`.

Implementation PR #95:
`https://github.com/MysterioCrypto/domain_generator/pull/95`

Semantic head:
`43519587fac92e94cb8bbbb64222c876d7579882`

C5-A checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`

Artifact:
`surface-v02-c5`

Automation:
- K01–K15 GREEN;
- JSON Schema snapshots GREEN;
- push full pytest GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36968139972`;
- PR full pytest GREEN:
  `https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143609`;
- representative C5-A checkpoint GREEN.

Implemented boundary:
- classification remains opt-in;
- requires explicit C4 seasonality;
- output is one derived `uint8` field `climate_regime_koppen_geiger`;
- fixed code range 1..30;
- C1/C4 climate generation remains independent from the classifier;
- C2/C3, features, networks and every pre-existing C4 field remain exact-unchanged.

Representative diagnostic classes:
```text
Csb  76.93%
Dsc  10.40%
Dsb   7.40%
Dfc   3.24%
ET    1.49%
Cfb   0.33%
Dfb   0.22%
```

The Csb dominance is expected for the deliberately winter-wet / warm-season-dry diagnostic recipe and is not a Core default.

Visual review:
- climate classes track accepted temperature/orographic gradients;
- mountain belts transition coherently C → D → ET;
- boundaries are categorical/threshold-like but not random/noisy;
- the raster is visibly climate regionalization rather than C3 vegetation;
- classification does not feed back into climate generation.

Operator decision: **C5-A IMPLEMENTATION ACCEPTED**.

Implementation PR #95 merged into `dev/0.2`:
`8af34da0c66c48b62172b8654edc5876d9414085`

Accepted C5-A semantics:
- Köppen–Geiger remains opt-in and Earth-derived;
- no classification is generated unless explicitly requested;
- classification requires explicit C4 seasonality;
- C1/C4 climate generation remains independent and configurable;
- output is exactly one derived `uint8` field with fixed codes 1..30;
- C1/C2/C3/C4, Terrain, Hydrology, features, networks, and Placement remain unchanged;
- no biome labels or hydrologic-permanence semantics were added.

C5-A is complete.

Next gate: perform a fresh post-C5 dependency audit before selecting the next semantic layer. Re-evaluate biome readiness and the still-deferred hydrology candidates using the now-accepted C5 climate-regime context, but do not assume any candidate is automatically ready.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Post-C5 dependency audit / H12-A design

Audit result:
- direct biome labels remain deferred: C5 is optional Earth-derived climate regionalization, not a universal biome truth; C3 is ecological potential rather than literal land cover; soil/substrate/disturbance remain absent;
- perennial/seasonal/dry channel classification remains blocked by groundwater/baseflow/storage;
- lake/wetland/playa/dry-basin classification remains blocked by basin water balance/infiltration/permanence;
- delta/estuary/fan remains blocked by known receiving-environment/process context.

A more fundamental universality gap was found:
- Core has no sea/ocean/coastline semantics;
- negative elevation is currently just terrain;
- archipelago/coastal worlds cannot distinguish marine water from inland depressions;
- rivers only terminate at lakes or generic domain outlets.

Selected next bounded layer: **H12-A Marine / Coastal Boundary Semantics**.

Design PR #96:
`https://github.com/MysterioCrypto/domain_generator/pull/96`

Proposed H12-A:
- optional explicit `hydrology.marine.sea_level_m`;
- no hidden sea level;
- marine = below-sea terrain connected to domain boundary;
- fixed 4-neighbour connectivity avoids diagonal point-contact flooding;
- enclosed below-sea depressions remain inland;
- marine cells excluded from lake/channel support;
- canonical water depth includes sea depth;
- derived `marine_mask`;
- refined 4× coastline geometry;
- distinct `MarineFeature`;
- new `marine_outlet` river node;
- regional and potential river networks terminate at first coastline intersection.

H12-A does not add tides, waves, salinity, submarine channels, estuaries or deltas.

Operator decision: **H12-A DESIGN ACCEPTED**.

Design PR #96 merged:
`f8efae6e24cdda68fb10960f13ca69d342a61a7b`

Accepted scope:
- explicit opt-in `hydrology.marine.sea_level_m`;
- no hidden sea-level datum;
- boundary-connected below-sea marine semantics using fixed 4-neighbour connectivity;
- enclosed below-sea basins remain inland;
- marine/lake/channel semantics remain distinct;
- canonical water depth may include marine depth;
- coastline refinement is semantic;
- distinct `MarineFeature`;
- `marine_outlet` nodes terminate regional/potential drainage at coastline;
- no tides/waves/salinity/submarine channels/delta/estuary morphology;
- inland worlds without marine recipe remain exact-compatible.

Next: implement H12-A separately with O01–O13 and a dedicated coastal/archipelago checkpoint.


## H12-A implementation in progress

Draft PR #97:
`https://github.com/MysterioCrypto/domain_generator/pull/97`

Implementation branch:
`impl/v0.2-marine-coastal-boundary`

Implemented so far:
- optional marine spec/plan contract with frozen-fingerprint normalization when absent;
- Core 0.1 marine rejection;
- deterministic 4-neighbour boundary-connected marine classification;
- deterministic `marine-XXXX` component identity;
- distinct `MarineFeature` public contract;
- refined 4× coastline geometry;
- marine exclusion from lake support;
- marine canonical water depth;
- marine exclusion from regional/potential semantic channel topology;
- `marine_outlet` nodes on refined coastline;
- public derived `marine_mask`;
- marine-aware hydrology invariants.

First regression run found one bounded implementation error:
- marine exclusion was accidentally passed into MFD accumulation;
- this contradicted accepted H12 routing boundary;
- the argument was removed; MFD routing/accumulation remains unchanged.

O01–O13 guardrails are now added and under CI.

Further accepted clarification:
- C2/C3 algorithms are unchanged, but marine canonical water may alter C2/C3 values wherever their already accepted water-distance/moisture dependencies change;
- C1/C4/C5 climate remains exact-unchanged;
- no marine-specific ecology term is added.

PR #97 remains draft/unmerged.


## H12-A implementation checkpoint — OPERATOR REVIEW

Implementation PR #97:
`https://github.com/MysterioCrypto/domain_generator/pull/97`

Semantic head:
`4dc897906d2e67ae7c3bccb2c9ef49934339f4a6`

Technical gate:
```text
O01-O13                  GREEN
schema snapshots          GREEN
PR full pytest            502 passed
push full pytest          502 passed
coastal checkpoint        GREEN
```

Full pytest:
- PR: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161043`
- push: `https://github.com/MysterioCrypto/domain_generator/actions/runs/36979156078`

H12 checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098`

Artifact:
`hydrology-v02-h12`

Representative checkpoint:
- domain 84×54 at 1 km;
- one boundary-connected marine component;
- marine fraction ≈ 42.64%;
- one preserved island hole;
- two inland lakes;
- enclosed below-sea diagnostic basin is not marine;
- regional marine outlets = 35;
- potential-drainage marine outlets = 101;
- engine invariants and hard constraints GREEN.

Visual review:
- coastline follows accepted 4× sub-cell reconstruction, not raw 1 km raster union;
- 250 m stair-stepping remains visible, which is expected from the accepted fixed 4× refinement;
- island geometry is preserved;
- enclosed below-sea basin remains disconnected from marine water;
- regional/potential drainage terminates at coastline;
- no visible channel continues through marine interior;
- lake and marine semantics remain distinct.

Recovery fixes retained:
- absent additive `marine=None` does not alter frozen pre-H12 fingerprints;
- marine terminal support is propagated consistently through Strahler hierarchy;
- accepted no-marine routing/accumulation remains upstream authority;
- C1 climate normalization uses pre-marine baseline water state;
- C2/C3 only respond through already accepted canonical-water dependencies.

Historical H12-A checkpoint: **IMPLEMENTATION — OPERATOR REVIEW**, now closed by explicit operator ACCEPT.

## H12-A implementation acceptance — DONE

Operator formally accepted H12-A implementation on 2026-10-09.

- Implementation PR #97: https://github.com/MysterioCrypto/domain_generator/pull/97 — **MERGED** into `dev/0.2`.
- Accepted implementation head: `4dc897906d2e67ae7c3bccb2c9ef49934339f4a6`.
- Merge commit: `3d275466ec5bfdb74f5dcb88bea6c8b641347f70`.
- O01–O13, schema snapshots, coastal operator checkpoint: GREEN.
- Push and PR full pytest: **502 passed** on accepted implementation head.
- Operator workflow: https://github.com/MysterioCrypto/domain_generator/actions/runs/36979161098

Frozen H12-A semantics:
- optional explicit `hydrology.marine.sea_level_m`, never an implicit sea-level datum;
- boundary-connected (4-neighbour) below-sea marine components; enclosed below-sea depressions remain inland;
- separate `MarineFeature`, derived `marine_mask`, 4× refined coastline, canonical marine depth;
- lake/marine separation, `marine_outlet` for regional and potential drainage; no submarine rivers;
- accepted Terrain/MFD and no-marine behavior stay stable; C1/C4/C5 climate remains unaffected;
- C2/C3 algorithms unchanged, but values can change on coastal land via existing water proximity/moisture dependencies;
- no tides, waves, salinity, coastal erosion, delta or estuary processes.

Current checkpoint: **POST-H12 DEPENDENCY AUDIT — NEXT**.
Reassess previously deferred candidates against the new marine receiving-environment capability; choose one bounded design only after an explicit dependency audit.
`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## Historical post-H12 dependency audit — DONE / H13-A design gate (closed by DESIGN ACCEPT)

Dependency audit after accepted H12-A:
- delta/estuary: a known marine receiving environment is now available, but actual discharge, sediment supply and coastal processes are still missing — **BLOCKED**;
- perennial/seasonal/dry channels: monthly precipitation from C4 exists when explicitly requested, but runoff formation, infiltration, groundwater/baseflow and storage are absent — **BLOCKED**;
- lake/wetland/playa/dry basin: basin water balance and permanence/infiltration still absent — **BLOCKED**;
- direct biome labels: C3 potential + optional Earth-derived C5 climate classes are not a substrate/ecological classification policy — **DEFERRED**;
- **gross annual precipitation input per contributing catchment**: C1 spatial precipitation and the accepted MFD weighted DAG/lake supernodes are already available — **DESIGN-READY**.

Selected bounded slice: **H13-A Gross Catchment Precipitation Input**.

Design-only draft PR #98:
https://github.com/MysterioCrypto/domain_generator/pull/98

Proposal (NOT ACCEPTED, NOT IMPLEMENTED):
```yaml
hydrology:
  climatic_input:
    scheme: gross_mfd_precipitation_v1
```

Proposed optional derived float64 field:
`gross_upstream_precipitation_m3_per_year` (m³/year).

Interpretation: gross precipitation volume **falling on upstream cells and mathematically allocated by MFD fractions** before evaporation, infiltration, storage or runoff generation. It is NOT physically delivered water, actual river discharge, runoff, channel permanence or a delta predictor.

Design clarification on 2026-11-15: compute the optional diagnostic within the accepted `SURFACE` stage after C1 rainfall is available, without adding a ValidationStage, mutating upstream state or calculating new physics in assembly. The design-only PR #98 includes this clarification (commit `5fbd6b5904071feefc38a0ab66f093e68845e81e`).

Dependency proposal (dashed; not an accepted architecture edge):
```text
accepted C1 annual precipitation ─┐
                                  ├─[PROPOSED H13-A read-only diagnostic]
accepted MFD + lake supernodes ───┤         └→ gross upstream precipitation field
accepted optional H12 marine ─────┘
```

Normative draft exists only on `design/v0.2-gross-catchment-precipitation` until accepted. Guardrails G01–G15 include uniform-precipitation equivalence to accepted area accumulation, volume conservation, marine absorption and exact off/on world immutability.

Current gate: **H13-A DESIGN — OPERATOR REVIEW**.
PR #98 is draft/open, not merged. Runtime implementation MUST NOT begin before explicit design ACCEPT / REJECT.

`release/0.2-prealpha` remains frozen at `c69c1af010a085fb80d248af703a77471fc6c9d7`.


## H13-A operator DESIGN ACCEPT — 2026-11-15

- Operator explicitly accepted H13-A design (not implementation).
- PR #98 merged into `dev/0.2` at `0000a208183a2ff3b1d7dc8eee8f93d54f72ef35` after HEAD and both CI checks verified green.
- Normative design now: `docs/design/gross-catchment-precipitation-input-v0.2.md`.
- Current checkpoint: separate H13-A implementation; G01–G15, full pytest, contrasting wet/dry/coastal operator-visible checkpoint; no implementation merge until separate explicit ACCEPT.
- Proposed semantic field is gross no-loss allocated annual atmospheric input, not actual runoff/discharge, basin water balance or stream permanence.
- Keep `release/0.2-prealpha` exactly at `c69c1af010a085fb80d248af703a77471fc6c9d7`.
- Earlier statements in historical post-H12 sections saying design is pending are superseded by this decision; consult top-level front matter, `docs/CONTEXT.md` and `docs/PROGRESS.md`.


## Продуктовый маршрут и реальный литературный источник — 2026-11-15

- Единая человеческая точка входа: [START_HERE.md](START_HERE.md); маршрут P0–P6: [docs/PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md); первая боeвая source-backed задача: [Д’Акхар](docs/world-fixtures/dakhar-first-arc.md).
- Генератор рассчитан на преимущественно **неземные миры**. Классы Köppen C5 опциональны, C3 является индексом растительного потенциала, не картой леса/биома. Цель — управляемый ландшафт сверху между спутниковым видом и иллюстрацией, позже опциональный ImageGen с возвратом географических слоёв.
- На dev/0.2 остаются только принятые Terrain/Hydrology/C1–C3 и опциональные C4/C5/H12. H13 **дизайн** #98 слит; **реализация** #99 — draft/open/unmerged, как и #100 (параметрическое исследование C2) и #101 (слоистый картографический renderer).
- Две Drive-папки пользователя изучены через connector. 11.11 авторская справка и 08.11 сводный атлас различают канон и рабочие A/B/C кандидаты. A8/A10/A11/A12 ZIP и PNG геоатлас **обнаружены при прямом fetch папок**, несмотря на пустую выдачу search; A8/A12 **теперь открыты и SHA/географические оси проверены** (A8 lat север→юг, A12 юг→север, высоты совпадают exact после разворота), A10/A11 содержимое и SHA также проверены; **в Core не импортированы**. Планетный год ≈202,755 земных суток, поэтому осадки mm/planetary-year не считать автоматически земным C1 mm/year.
- Это только документы + исходный JSON-реестр с тестами против несанкционированного повышения статуса модели. Не менялись runtime, accepted contracts, release/0.2-prealpha SHA c69c1af010a085fb80d248af703a77471fc6c9d7. Новую чистую репу пока не создавать.


- Реальный source-audit: [A8/A12 alignment report](docs/reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md); ZIP A8/A12 и A12_inputs NPZ SHA-256 сверены, 600×1200 массивы прочитаны, `A8[::-1,:]` высота и маска суши точно совпадают с A12. Следующий этап — отдельный надёжный geogrid import/adapter, а не генерация случайного материка взамен найденной исходной модели.


## P1 planetary macro-geogrid adapter — 2026-11-15, DRAFT #103

- User's non-Earth source A8/A10/A11/A12 archives are verified (SHA/CRC, A8 north-first vs A10/A11/A12 south-first) and kept PRIVATE. Source A8 global D8 is an older research hydrology, not Core 0.2 accepted MFD.
- On an isolated DRAFT [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), external-only script scripts/export_planetary_macro_region_v02.py reads paths of original ZIPs, validates exact A8/A12 shared land/DEM, accepts user-specified planetary radius/year and local km source crop, remaps BOTH endpoints of A8 global flattened D8 downstream indices, and flags rivers exiting crop. It emits source NPZ+manifest+PNG, deliberately NOT DomainData and NOT fake local 1-km elevation.
- Synthetic workflow [GREEN](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913) passes 4 targeted tests and writes a demo artifact. No private source ZIP/PNG was committed or uploaded to Actions.
- [CLI instructions and explicit boundaries](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Next meaningful work is source-constrained finer regional terrain and new MFD river generation, followed by non-Earth profile-based land cover; not further parchment filters or full planetary climate science.
- This is a parallel draft branch. PR #99 H13, #100 C2 tests, #101 atlas composer remain DRAFT/UNMERGED. Frozen release c69c1af010a085fb80d248af703a77471fc6c9d7 remains unchanged.


### P2-A terrain conditioning (2026-11-15; draft #103, unmerged)

- External adapter chain: planetary macro ZIP → north-first source NPZ → new modeled 1-km child DEM. Source DEM station heights are mathematically preserved by subtracting interpolated stationary noise; baseline is C1 Hermite instead of square-edged bilinear interpolation. World-profile radius/year explicitly required. It neither changes accepted Core 0.2 terrain/hydrology nor asserts physical validity of the novel's historical A8 D8 channels.
- Private original A/B/C regions generated at 230×230 km, 231×231 samples, original parent anchors 63/49/49, zero observed anchor errors. Real derived images remain private; CI uploads only synthetic world previews. Details: [P2-A notes](docs/world-fixtures/planetary-child-terrain.md).
- Next P2-B: actual new child MFD routing and basin outlet constraints, then non-Earth per-world land cover. This PR #103 and #99–101 remain draft/unmerged, frozen release unchanged.


### P2-B1 MFD source-to-child audit (2026-11-16)

- In **draft #103** new standalone `scripts/diagnose_planetary_child_mfd_v02.py`: accepted Core 0.2 Priority-Flood/MFD fractions on P2-A source-pinned child DEM; independent strict-topological accumulation validated against canonical Core on small synthetic grids; boundary local-area ledger. Macro A8 D8 old river edges are a separately labelled overlay, **NOT** child MFD source authority. [P2-B audit](docs/reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).
- GREEN [synthetic Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775): 19 tests + 3-panel PNG + NPZ/manifest, private user planet files NOT pushed. Real original world A/B/C locally screened using SciPy cubic (NOT exactly the P2-A C1 GitHub interpolator): 230×230km, 1km cells; all local 53,361km² area accounted at boundary to ~1e-10km².
- **Real blocker**: candidate filled depressions in B/C have virtual depth ~88.5/60m, creating artificial MFD fan patterns. New diagnostic explicitly exports unresolved-depression mask; does NOT claim accepted lake spill, materialized vector rivers, global basin conditioning or outside-crop upstream source. Next P2-B2: accepted lake supernodes plus macro-boundary-constrained routing. PR #103 remains DRAFT/UNMERGED, #99/#100/#101 unchanged, release frozen.


### P2-B2.1 — geometric lake basin review (2026-11-20, PR #103 DRAFT)

- [Visual synthetic QA](https://github.com/MysterioCrypto/domain_generator/actions/runs/44748762996) and [operator review](docs/reviews/p2-b2-1-child-lake-basin-operator-checkpoint-2026-11-20.md): external read-only `scripts/audit_planetary_child_lakes_v02.py`, Core Priority Flood/extract_lake_candidates/choose_lake_outlets, bounded nested hierarchy, Core lake-supernode conservation on SMALL bowl only. Proposed basin ≠ actual water occupancy; no universal Earth-specific thresholds, no external inflow, no source-D8 substitution.
- 27 focused tests GREEN; full algorithmic SHA pytest 532 GREEN; final docs SHA must have new CI. Private A/B/C sensitivity screening performed locally using independently interpolated DEM, not an exact PR P2-A regression; resulting numerical/visual data stay in conversation only.
- P2-B2.2 next: source-macro boundary inflows/outflows and constrained MFD+lake supernode routing, before asserting credible river/ford/waterfall geometry. Keep PR #103, #99–101 draft/unmerged. Frozen `release/0.2-prealpha` unchanged.


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.
