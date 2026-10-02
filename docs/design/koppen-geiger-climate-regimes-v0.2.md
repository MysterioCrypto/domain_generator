# Köppen–Geiger Climate Regimes v0.2

Status: **ACCEPTED / IMPLEMENTED — C5-A merged into dev/0.2**
Target development line: `dev/0.2`
Checkpoint: C5-A
Depends on: accepted C1 annual climate + accepted C4-A monthly seasonality

## 1. Why C5 exists

C4-A removed one major blocker for climate-regime classification by providing explicit deterministic monthly temperature and precipitation climatologies.

However, this does **not** mean Core is ready to emit ecological biome labels directly.

A biome label would mix:
- atmospheric climate regime;
- vegetation response;
- potentially soils/substrate;
- hydrology;
- disturbance/history;
- categorical ecological policy.

Those concerns should remain separable.

C5-A therefore adds a **climate regime classification**, not a biome classification.

The selected basis is the widely used Köppen–Geiger system as formalized by Peel et al. (2007) and used by Beck et al. (2018) for modern high-resolution climate maps.

References:
- Peel, Finlayson & McMahon (2007), Hydrology and Earth System Sciences 11, 1633–1644, doi:10.5194/hess-11-1633-2007.
- Beck et al. (2018), Scientific Data 5:180214, doi:10.1038/sdata.2018.214.

C5-A is intentionally a derived climate layer that future biome logic may consume.

## 2. Important model adaptation

Published Köppen–Geiger rules refer to summer/winter half-years.

Core deliberately has:
- no latitude;
- no inferred hemisphere;
- abstract climatological months;
- explicit configured temperature peak month.

Therefore C5-A must not silently pretend month numbers imply a real-world hemisphere.

Instead it uses a **model-local warm/cold half-year** anchored to the explicit C4 temperature peak month.

For configured temperature peak month `p`:

```text
warm_half_year =
    p-3, p-2, p-1, p, p+1, p+2
    modulo 12

cold_half_year =
    remaining six months
```

Examples:

```text
peak month 07
warm half-year = 04..09
cold half-year = 10..03

peak month 01
warm half-year = 10..03
cold half-year = 04..09
```

For normal Earth-like seasonal phasing this reproduces the familiar hemispheric six-month windows without inferring hemisphere from map coordinates.

Because this is an explicit adaptation, the scheme identifier is **not** merely `koppen_geiger`.

Public scheme id:

```text
koppen_geiger_local_season_v1
```

## 2A. Universality boundary

C4 climate generation and C5 climate classification are intentionally separate concerns.

C4 does **not** hard-code a northern-hemisphere or Earth-regional season:
- `temperature_peak_month` is explicit input;
- `temperature_seasonal_amplitude_c` is explicit input;
- `precipitation_peak_month` is explicit input;
- `precipitation_seasonality_log_amplitude` is explicit input;
- none of those values has a hidden default when seasonality is enabled.

Therefore the same generator contract can represent, for example:
- a cold northern-style regional climate;
- a hot arid regional climate;
- a winter-wet or summer-wet climate;
- an equatorial low-seasonality climate;
- an inverted or otherwise fictional seasonal phase.

C5 does **not** constrain those inputs. It only interprets already generated monthly climate when explicitly requested.

Köppen–Geiger itself is Earth-derived and its thresholds are not universal laws of climate or ecology. Therefore:

> `koppen_geiger_local_season_v1` is an optional named interpretation scheme, not canonical Core climate semantics.

Consequences:
- no Köppen classifier is enabled by default;
- absence of `surface.climate.classification` means no climate-regime categorical field exists;
- a non-Earthlike fantasy world may use C1/C4 climate without any Köppen classification;
- future classifiers may coexist under different explicit scheme ids;
- biome generation must not assume Köppen classes exist;
- climate generation must never be retuned to make Köppen output look more familiar.

The generator is universal at the contract/composition level, not a claim that the current physical model already contains every real-world process. For example, current C1/C4 do not yet model oceanic circulation, latitude-driven insolation, migrating monsoons, groundwater, or daily weather unless future bounded layers add those semantics explicitly.

## 3. Opt-in contract

C5-A must not silently add new output to every previously accepted C4 request.

Extend optional `surface.climate` with:

```text
classification:
  scheme: koppen_geiger_local_season_v1
```

Rules:
- classification is optional;
- if absent, C4 behavior and output remain unchanged;
- if present, C4 seasonality must also be present;
- no hidden default scheme;
- only `koppen_geiger_local_season_v1` is accepted in C5-A.

The explicit recipe therefore participates in spec/plan fingerprints.

## 4. Inputs

C5-A reads only accepted climate fields:

```text
monthly_mean_temperature_c [12, rows, columns]
monthly_precipitation_mm   [12, rows, columns]
annual_mean_temperature_c
annual_precipitation_mm
temperature_peak_month
```

C5-A does not read:
- C2 moisture;
- C3 vegetation;
- rivers/lakes;
- terrain directly;
- latitude;
- biome tags;
- POIs.

Terrain effects already enter the accepted climate through C1.

## 5. Per-cell climate statistics

For each cell:

```text
MAT    = annual mean temperature
MAP    = annual precipitation total

Thot   = maximum monthly mean temperature
Tcold  = minimum monthly mean temperature
Tmon10 = count(monthly mean temperature > 10 C)

Pdry   = minimum monthly precipitation

Pwarm  = sum precipitation over warm_half_year
Pcold  = sum precipitation over cold_half_year

Psdry  = minimum precipitation in warm_half_year
Pswet  = maximum precipitation in warm_half_year
Pwdry  = minimum precipitation in cold_half_year
Pwwet  = maximum precipitation in cold_half_year
```

All classification computations use float64 views of the accepted persisted monthly arrays.

No RNG is used.

## 6. Arid B-class threshold

Following the Peel/Beck rule family, calculate:

```text
if Pwarm / MAP >= 0.70:
    Pthreshold = 2 * MAT + 28
elif Pcold / MAP >= 0.70:
    Pthreshold = 2 * MAT
else:
    Pthreshold = 2 * MAT + 14
```

Then:

```text
B climate if MAP < 10 * Pthreshold

BW desert if MAP < 5 * Pthreshold
BS steppe otherwise

h if MAT >= 18 C
k if MAT < 18 C
```

B classification has precedence over A/C/D/E, matching the published Köppen–Geiger decision structure.

If `Pthreshold <= 0`, the B test naturally cannot classify positive-MAP cells as arid.

## 7. Main climate groups

After testing B first:

### A — tropical

```text
Tcold >= 18 C
```

Subtype:

```text
Af:
    Pdry >= 60 mm

Am:
    not Af
    and Pdry >= 100 - MAP / 25

Aw:
    otherwise
```

C5-A uses the 30-class Beck/Peel vocabulary and therefore does not add a separate `As` code.

### E — polar

```text
Thot <= 10 C
```

Subtype:

```text
ET if Thot > 0 C
EF otherwise
```

### C — temperate

```text
Thot > 10 C
and 0 C < Tcold < 18 C
```

### D — cold

```text
Thot > 10 C
and Tcold <= 0 C
```

This keeps the Beck/Peel threshold exactly: `Thot = 10 C` belongs to group E rather than being reassigned to C/D.

The C/D boundary follows the Beck/Peel 0 C convention rather than the older -3 C alternative.

## 8. C/D precipitation subtype

Compute candidate predicates:

```text
summer_dry =
    Psdry < 40 mm
    and Psdry < Pwwet / 3

winter_dry =
    Pwdry < Pswet / 10
```

Then:

```text
if summer_dry and winter_dry:
    if Pcold > Pwarm:
        second letter = s
    else:
        second letter = w
elif summer_dry:
    second letter = s
elif winter_dry:
    second letter = w
else:
    second letter = f
```

This makes `s` and `w` mutually exclusive while preserving the Peel/Beck intent.

## 9. C/D temperature subtype

For both C and D:

```text
a:
    Thot >= 22 C

b:
    Thot < 22 C
    and Tmon10 >= 4
```

For C:

```text
c:
    otherwise
```

For D:

```text
d:
    not a or b
    and Tcold < -38 C

c:
    otherwise
```

This produces the standard 30-class vocabulary.

## 10. Fixed class codebook

Public raster dtype:

```text
uint8
```

Public field id:

```text
climate_regime_koppen_geiger
```

Descriptor:

```text
role  = derived
dtype = uint8
unit  = koppen_geiger_local_season_v1
```

Fixed numeric mapping, aligned with the commonly used Beck 2018 ordering:

```text
 1 Af   2 Am   3 Aw
 4 BWh  5 BWk  6 BSh  7 BSk

 8 Csa  9 Csb 10 Csc
11 Cwa 12 Cwb 13 Cwc
14 Cfa 15 Cfb 16 Cfc

17 Dsa 18 Dsb 19 Dsc 20 Dsd
21 Dwa 22 Dwb 23 Dwc 24 Dwd
25 Dfa 26 Dfb 27 Dfc 28 Dfd

29 ET
30 EF
```

Value `0` is reserved and must never appear in a successfully classified C5-A field.

The unit string identifies the normative codebook without changing the existing FieldDescriptor shape.

## 11. Runtime state

When classification is enabled:

```text
SurfaceState.climate_regime_koppen_geiger
    uint8 [rows, columns]
```

When classification is absent:

```text
None
```

The classifier is deterministic and consumes no RNG.

## 12. Public export

When enabled, assembly exports exactly one additional derived 2D field:

```text
climate_regime_koppen_geiger
```

No existing field changes role or meaning.

Canonical annual fields remain:
- `temperature`;
- `annual_precipitation`.

Monthly C4 fields remain derived.

C5-A classification is also derived.

## 13. Relationship to vegetation and biomes

Köppen–Geiger is climate regionalization with ecological relevance; it is **not** a direct vegetation-state raster.

C5-A must not:
- replace C3 vegetation;
- call climate classes biome IDs;
- force vegetation to match a climate class;
- infer forest/grassland/desert cover directly from the class code.

Future biome logic may use:

```text
C5 climate regime
+ C3 vegetation potential
+ accepted hydrology
+ future substrate/soil context if required
→ biome classification
```

Keeping C5 separate makes disagreements diagnosable.

## 14. Relationship to deferred hydrology

C5-A does not classify:
- perennial streams;
- seasonal streams;
- dry gullies;
- wetlands/playas/dry basins;
- deltas/estuaries/fans.

C4+C5 improve climatic context, but channel permanence still lacks groundwater/baseflow/storage and basin permanence still lacks water balance/infiltration.

## 15. Automated guardrails

### K01 — opt-in only

No classification recipe:
- runtime classification is `None`;
- no C5 field descriptor/payload is exported;
- frozen C4 output remains unchanged.

### K02 — classification requires seasonality

A classification recipe without C4 seasonality is rejected explicitly at contract/compiler validation.

### K03 — exhaustive valid code range

Every classified cell is in integer range `1..30`.
Zero never appears.

### K04 — no RNG

Classification consumes no RNG and exact replay is bit-identical.

### K05 — B precedence

Synthetic cells satisfying both thermal group criteria and arid B threshold classify as B.

### K06 — A subtype fixtures

Synthetic monthly climates cover exact Af / Am / Aw decisions.

### K07 — B subtype fixtures

Synthetic climates cover BWh / BWk / BSh / BSk.

### K08 — C subtype fixtures

Synthetic climates cover:
- Csa/Csb/Csc;
- Cwa/Cwb/Cwc;
- Cfa/Cfb/Cfc.

### K09 — D subtype fixtures

Synthetic climates cover:
- Dsa/Dsb/Dsc/Dsd;
- Dwa/Dwb/Dwc/Dwd;
- Dfa/Dfb/Dfc/Dfd.

### K10 — E subtype fixtures

Synthetic climates cover ET and EF.

### K11 — local warm/cold season indexing

For temperature peak month 07:
- warm half-year is 04..09.

For peak month 01:
- warm half-year is 10..03.

Modulo behavior is exact and deterministic.

### K12 — s/w exclusivity

No cell can receive both dry-summer and dry-winter subtype semantics.

Synthetic overlap cases verify the `Pcold > Pwarm` tie-resolution rule.

### K13 — upstream immutability

Enabling C5 changes none of:
- Terrain;
- Hydrology;
- annual C1;
- monthly C4;
- C2 moisture;
- C3 vegetation;
- features;
- networks;
- Placement.

### K14 — public field contract

When enabled:
- exactly one `climate_regime_koppen_geiger` descriptor exists;
- role = derived;
- dtype = uint8;
- unit = `koppen_geiger_local_season_v1`;
- payload shape equals grid;
- payload IDs exactly match the fixed codebook.

### K15 — fingerprint semantics

Adding/changing the classification recipe changes the semantic spec/plan fingerprint.

Absence of classification preserves accepted C4 fingerprints.

## 16. Operator-visible checkpoint C5-A

Use the accepted representative C4 world.

Required views:
1. C5 climate-regime raster with the fixed 30-class legend;
2. same raster over hillshade;
3. annual temperature for comparison;
4. annual precipitation for comparison;
5. warmest/coldest monthly temperature;
6. wettest/driest monthly precipitation;
7. C3 vegetation underneath/alongside the climate classes;
8. class histogram and area fractions;
9. boundary diagnostics showing the climate variables around representative class transitions.

Operator questions:
- do mountain temperature gradients produce plausible transitions?
- do wet/dry transitions correspond to accepted precipitation gradients?
- are class boundaries coherent rather than noisy?
- does the map read as a climate-regime map rather than pretending to be vegetation?
- are any large regions classified in ways that clearly contradict their monthly climatology?

## 17. Acceptance criteria

Implementation may be accepted only if:
- K01–K15 are green;
- full pytest is green;
- C4 annual/monthly outputs remain exact-unchanged;
- representative C5-A checkpoint is reviewed;
- the fixed codebook and local-season adaptation remain explicit;
- explicit implementation ACCEPT / REJECT is recorded.

## 18. Stop rules

- Do not call C5 classes biomes.
- Do not use C3 vegetation to force a preferred Köppen class.
- Do not infer hemisphere from y-coordinate.
- Do not change C4 peak months or amplitudes inside classification.
- Do not smooth class boundaries by mutating climate.
- Do not add stochastic class noise.
- Do not add soils/groundwater to C5.
- Do not classify hydrologic permanence in C5.
- Do not silently introduce a second climate-classification scheme.
- Do not make Köppen classification mandatory for Core 0.2/C4 worlds.
- Do not use Köppen thresholds to alter or validate the generated climate itself.
- If the local warm/cold half-year adaptation proves visibly inadequate, reject/redesign that adaptation rather than altering accepted monthly climate fields.


## 19. Design acceptance

Operator decision: **ACCEPTED**.

PR #94 merged into `dev/0.2` at:
`d75b2f6f55b53a14b048a38bb2a69d339c8cf44e`.

Acceptance explicitly includes the universality boundary:
Köppen–Geiger is an optional Earth-derived classifier and never a mandatory canonical climate representation.


## 20. Implementation acceptance

Operator decision: **C5-A IMPLEMENTATION ACCEPTED**.

Implementation PR #95:
`https://github.com/MysterioCrypto/domain_generator/pull/95`

Accepted semantic head:
`43519587fac92e94cb8bbbb64222c876d7579882`

Implementation merge commit:
`8af34da0c66c48b62172b8654edc5876d9414085`

Acceptance evidence:
- K01–K15 GREEN;
- generated JSON Schema snapshots GREEN;
- push and PR full pytest GREEN;
- representative C5-A checkpoint GREEN;
- all pre-existing C4 fields, features, and networks remain exact-unchanged when classification is enabled;
- output remains one optional derived `uint8` field.

Checkpoint:
`https://github.com/MysterioCrypto/domain_generator/actions/runs/36968143576`

The historical release line `release/0.2-prealpha` remains unchanged at
`c69c1af010a085fb80d248af703a77471fc6c9d7`.
