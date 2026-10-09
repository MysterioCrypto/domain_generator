# H13-A — Gross Catchment Precipitation Input v0.2

Status: **PROPOSED — INV-006 design gate; implementation NOT authorized**
Target: `dev/0.2` post-release line. The frozen `release/0.2-prealpha` is out of scope.
Dependencies: accepted C1 annual precipitation, Terrain/Hydrology 0.2 MFD weighted DAG, lake supernodes, optional H12 marine boundary.

## 1. Post-H12 dependency audit

| Candidate | H12 effect | Remaining blocker |
| --- | --- | --- |
| Delta / estuary | Known marine receiver and explicit `marine_outlet` now exist | actual discharge, sediment transport, coastal processes, depositional morphology |
| Perennial / seasonal / dry streams | Marine mouths and C4 monthly climatology exist | infiltration, groundwater/baseflow, storage, streamflow losses |
| Lake / wetland / playa / dry depression | Explicit marine vs inland water distinction exists | basin water balance, infiltration, retention/permanence |
| Direct biome labels | Optional C5 climate and C3 vegetation potential exist | substrate/soil, ecological classification policy, disturbance/history |
| Gross upstream precipitation input | C1 spatial annual precipitation and accepted MFD DAG exist | **No new physical process required** |

Decision for proposal: implement only **gross climate water input**, not yet a hydrologic discharge or biome/land-cover classifier.

## 2. Purpose and exact semantic meaning

Existing `flow_accumulation_km2` measures upstream contributing **area**, treating each contributing grid cell as equal-area input. A 100 km² arid basin and a 100 km² humid basin can therefore have the same area accumulation despite receiving very different annual precipitation.

H13-A computes a second, *derived diagnostic*: the gross annual volume of precipitation falling on cells whose existing MFD fractions contribute to a downstream grid location.

It answers:

> How much atmospheric precipitation volume arrives at this location's contributing catchment, **before any hydrological losses, snow storage, groundwater exchange or runoff generation?**

It deliberately does **not** answer:
- how much water becomes overland runoff;
- what river discharge (m³/s) is;
- whether a channel flows permanently, seasonally or at all;
- how much water reaches an estuary or forms a delta after storage and losses;
- whether precipitation falls as snow or rain.

This distinction is normative. The word `runoff`, `streamflow`, `discharge` or `recharge` must not label this field.

## 3. Explicit opt-in contract

Propose optional Core 0.2 request subrecipe:

```yaml
hydrology:
  climatic_input:
    scheme: gross_mfd_precipitation_v1
```

Constraints:
- classification/calculation is absent unless the recipe is present;
- exactly one scheme id is accepted for H13-A;
- Core 0.1 explicitly rejects it;
- Core 0.2 annual climate is mandatory and supplies its existing `annual_precipitation` raster;
- C4 seasonality and C5 Köppen are **not** required;
- H12 marine may independently be present or absent;
- no hidden runoff coefficient, evapotranspiration, infiltration or storage parameter is introduced.

An absent `hydrology.climatic_input=None` must be omitted from both historical specification and plan fingerprint payloads. An enabled or changed recipe changes spec/plan identity.

## 4. Units and input precision

Inputs:
- accepted `annual_precipitation` in mm/year (persisted float32);
- grid cell area in km²;
- accepted MFD receiver fractions / routing DAG;
- accepted lake supernodes and outlets;
- optional H12 `marine_mask` / component ids.

Local source per non-marine cell:

```text
cell_area_km2 = cell_size_km²
precipitation_input_m3_per_year =
    annual_precipitation_mm_per_year × cell_area_km2 × 1000
```

Reason: 1 mm falling on 1 km² equals 1,000 m³. This is a **gross annual volume/rate**, not a measured discharge.

Source precipitation comes from accepted persisted float32 C1 data, converted to float64 for accumulation. No new climate RNG is consumed.

## 5. MFD transport and accounting

Use the accepted weighted MFD DAG, not a newly generated river graph. Reuse the same receiver fractions, tie ordering, lake supernode concept and deterministic topological accumulation as accepted Hydrology 0.2.

For an ordinary land cell `i`:

```text
Qgross[i] = Pvolume[i] + sum(Qgross[j] × f[j -> i] for all upstream j)
```

`Qgross` here is only an algebraic temporary for **gross precipitation input** and must not be exposed as discharge.

Requirements:
- MFD splits are retained; do not collapse to dominant single-receiver flow;
- the source term varies per cell according to accepted C1 precipitation;
- every valid outgoing weight is preserved, except existing lake-supernode normalization required by accepted Hydrology;
- no channel thresholds, source promotion or river depths are recomputed;
- zero precipitation is not invented: C1 guarantees positive annual precipitation, though zero may be used in isolated synthetic unit fixtures;
- all intermediate values use float64 and deterministic traversal.

## 6. Lake supernodes

Preserve accepted one-lake/one-outlet routing identity.

Every land or fresh-water lake cell receives local atmospheric precipitation input. For an accepted lake:
- add precipitation falling on its own raster support **once**, not once per inflow;
- aggregate all upstream contributions in the lake supernode;
- forward the accumulated gross input once through the accepted lake outlet;
- present the supernode value consistently on accepted lake raster cells if a grid field is needed;
- do not infer evaporation, infiltration, lake residence time, water level or permanence.

The old contributing-area field remains unchanged.

## 7. H12 marine and domain-edge behavior

With explicit H12 marine:
- marine cells contribute **zero** local source to the terrestrial catchment-input diagnostic;
- a weighted MFD link from non-marine terrain into marine support is a terminal/absorbing transfer for this diagnostic;
- do not let offshore precipitation or downstream routing on the seabed contribute back into a terrestrial catchment;
- the public gross-upstream-input raster is zero on marine cells to avoid confusing marine ocean precipitation with land-drainage supply;
- keep deterministic *internal* accounting of each marine-component inlet flux for conservation checks, without yet exporting it as a river discharge or marine feature property;
- do not change H12's four-neighbour classification or redraw the coastline.

With no marine recipe, the existing open land-domain edge remains a valid terminal sink. Include delivered flux at domain-edge sinks in conservation checks, exactly once.

At a marine boundary the accepted MFD topology remains the upstream authority. H13-A must not quietly reroute terrain drainage or turn split MFD transport into new river-mouth topology.

## 8. Public output and stage boundary

Enabled output: exactly one new **derived** 2D field.

```text
id    gross_upstream_precipitation_m3_per_year
role  derived
dtype float64
unit  m3/year
shape [rows, columns]
```

Value is finite and non-negative on land/freshwater cells, zero on marine cells; it is explicitly not canonical `water_depth`, stream width, channel permanence or physical river discharge.

Add a read-only, deterministic **environmental diagnostic** computation after accepted C1/Surface climate exists and before final validation/assembly. It may produce a separate diagnostic state consumed only by export and its own invariants.

It must not:
- reorder the accepted Terrain → Hydrology → Surface dependencies;
- mutate accepted HydrologyState or SurfaceState;
- affect candidate ranking, channel selection, Placement, canonical water, vegetation, weather or climate;
- calculate physics as an incidental side effect of bundle assembly;
- add a new independently seeded attempt.

If this stage boundary cannot be implemented without mutating accepted upstream state, stop for explicit architectural review instead of smuggling the computation into an unrelated stage.

## 9. Physical and mathematical checks

Use total gross precipitation input as a conserved scalar over the chosen MFD network. For finite inputs and an acyclic receiver graph:

```text
sum(source volume on non-marine cells including lake support)
  ≈ sum(gross volume delivered to non-marine domain-edge terminals)
    + sum(gross volume transferred into marine components)
```

Do not sum the raster at every grid cell to estimate system mass: upstream contributions are intentionally repeated along downstream locations.

Uniform precipitation, absent marine:

```text
gross_upstream_precipitation_m3_per_year
  ≈ uniform_precipitation_mm_per_year × 1000
    × accepted_flow_accumulation_km2
```

including accepted lake supernode semantics. This is a mandatory compatibility/correctness oracle, not an excuse to replace the accepted area algorithm.

## 10. Automated guardrails

### G01 — opt-in / frozen compatibility
Absent recipe: no runtime diagnostic, no new descriptor/payload, no mutation, exact previously accepted fingerprints.

### G02 — explicit scheme and version boundary
Only `gross_mfd_precipitation_v1` is valid; Core 0.1 rejects it.

### G03 — source and unit conversion
A one-cell 1 km² fixture with 1000 mm/year yields exactly 1,000,000 m³/year at its outlet, absent losses.

### G04 — uniform climate vs accepted accumulation
With no marine and spatially uniform input, diagnostic matches accepted `flow_accumulation_km2 × P × 1000` within a stated floating-point tolerance.

### G05 — heterogeneous precipitation
Same terrain/MFD, different rain input distribution yields correspondingly different gross supply; no constant-area shortcut.

### G06 — MFD split conservation
Synthetic bifurcating fraction graph accounts for all supplied precipitation exactly once at its sinks.

### G07 — lake supernode
Lake support source counted once; upstream contributions collected; exactly one valid outlet, no artificially multiplied lake flux.

### G08 — marine absorption
Marine local source = 0; transferred terrestrial gross supply counted at first marine entry; no seabed drainage contribution.

### G09 — enclosed below-sea basin
An enclosed below-sea inland component is not marine and is treated by ordinary accepted inland hydrology.

### G10 — land edge outlets
A non-marine domain outlet captures delivered gross supply; no invented marine receiver.

### G11 — global volume conservation
Across mixed lakes, land outlets and marine components, total local input equals total terminal delivery within documented float64 tolerance.

### G12 — upstream state immutability
Terrain, MFD fractions, contributing area, river/lake/marine networks, all C1–C5 fields, C2/C3 and Placement remain exact-equal with H13 off/on.

### G13 — public derived field
Exactly one `float64` `m3/year` derived field appears only when enabled; finite/nonnegative; marine cells zero; bundle and schema round-trip.

### G14 — deterministic replay / fingerprints
No RNG; exact repeated spec/plan/attempt yields identical field and bundle; enabled recipe changes fingerprints, absent recipe preserves historical identity.

### G15 — representative environments
Inland dry basin, humid mountain basin and a H12 coastal/archipelago fixture all pass checks, without hard-coded geography/latitude/seasonal phasing.

## 11. Operator-visible checkpoint H13-A

Review at least two contrasting environment fixtures: inland wet/dry precipitation contrast and coastal/archipelago with H12 marine.

Required views:
1. accepted C1 annual precipitation;
2. accepted MFD contributing area;
3. new gross upstream precipitation input (m³/year; readable logarithmic display permitted only in the renderer);
4. regional rivers, potential drainage, lakes and coast overlaid without altering geometry;
5. selected upstream-to-downstream traces annotated with local source/accumulated input;
6. land edge versus marine receiving-terminal volume ledger;
7. conservation errors, histogram, finite/nonnegative checks;
8. exact off/on comparison of pre-existing world fields/features/networks;
9. a uniform-rainfall fixture demonstrating the area-accumulation identity.

Operator questions:
- do equally sized wet/dry catchments carry different **gross precipitation inputs**?
- is the spatial signal consistent with accepted C1 precipitation and MFD convergence?
- does lake routing count its local precipitation once?
- is coastal volume captured without continuing through the sea?
- is the result clearly labeled as gross input, **not** a hydrograph or discharge?

## 12. Stop rules and acceptance

- No runoff coefficient, potential evapotranspiration subtraction or soil/groundwater shortcut in H13-A.
- No monthly streamflow/permanence classification just because C4 monthly climate exists.
- No estuary/delta selection from gross precipitation input alone.
- No river width/depth/source edits from this diagnostic.
- No hidden Earth latitude, land-cover, soil or biome assumptions.
- No marine precipitation contamination of land-based catchment supply.
- No acceptance by green CI alone: G01–G15, full suite, meaningful representative render and explicit operator ACCEPT/REJECT are mandatory.

Next gate: **H13-A DESIGN — OPERATOR REVIEW**. Implementation remains blocked pending formal design acceptance.
