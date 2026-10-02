# Environmental Seasonality v0.2

Status: **PROPOSED — INV-006 design gate; no runtime implementation yet**
Target development line: `dev/0.2`
Checkpoint: C4-A
Depends on: accepted C1 annual climate + frozen Core 0.2 prealpha release

## 1. Why C4 exists

Core 0.2 prealpha deliberately stops at annual climate:

```text
annual mean temperature
annual precipitation
effective annual moisture
annual vegetation potential
```

That is enough for broad regional forcing and continuous vegetation potential, but not enough for season-sensitive semantics.

The accepted C3 design explicitly records this limitation:
- monthly/growing-season behavior is absent;
- annual climate alone is not sufficient for a defensible biome classifier;
- annual moisture alone is not enough to call low-order drainage perennial/seasonal/dry.

C4-A adds a bounded **climatological monthly envelope** while preserving every accepted annual field exactly.

C4-A does not classify biomes and does not classify stream permanence.

## 2. Release/version boundary

`release/0.2-prealpha` remains frozen at:
`c69c1af010a085fb80d248af703a77471fc6c9d7`.

C4-A exists only on the post-release development line.

For current schema/plan 0.2, C4 seasonality is an **optional additive climate subrecipe**.

If the seasonality recipe is absent:
- generation follows the frozen annual-only Core 0.2 behavior;
- no monthly runtime arrays are created;
- no monthly derived fields are exported;
- existing 0.2 requests remain semantically compatible with the frozen prealpha release.

If the seasonality recipe is present, every C4 parameter is explicit. There are no hidden seasonal defaults.

## 3. Bounded input recipe

Extend `surface.climate` with optional:

```text
seasonality:
  temperature_seasonal_amplitude_c: <finite float >= 0>
  temperature_peak_month: <integer 1..12>

  precipitation_seasonality_log_amplitude: <finite float >= 0>
  precipitation_peak_month: <integer 1..12>
```

Interpretation:

### temperature_seasonal_amplitude_c

Peak deviation from the accepted annual mean temperature.

Example:

```text
annual mean = 8 °C
amplitude   = 7 °C

warm peak   = 15 °C
cold trough = 1 °C
```

It is a regional climatological amplitude, not a daily temperature range.

### temperature_peak_month

Climatological month with maximum monthly mean temperature.

C4 does not infer hemisphere or latitude.

### precipitation_seasonality_log_amplitude

Dimensionless concentration of annual precipitation around the configured wet-season peak.

`0` means all twelve months receive exactly `annual_precipitation / 12`.

Larger values progressively concentrate precipitation around the peak month.

### precipitation_peak_month

Climatological month with the maximum precipitation fraction.

Temperature and precipitation phases are independent so the model can represent, for example:
- summer-wet climate;
- winter-wet climate;
- nearly uniform rainfall.

## 4. Climatological month convention

Months are indexed `1..12`.

They are abstract climatological months. Core does not attach:
- real-world latitude;
- hemisphere;
- Gregorian day counts;
- leap years;
- daily weather.

For month `m` and configured peak month `p`:

```text
phase(m, p) = 2π * (m - p) / 12
```

The configured peak month therefore has `cos(phase) = 1`.

## 5. Monthly temperature

For every cell:

```text
T_month[m] =
    annual_mean_temperature_c
    + temperature_seasonal_amplitude_c
      * cos(phase(m, temperature_peak_month))
```

Consequences:
- the arithmetic mean of the twelve monthly fields equals the accepted C1 annual mean at every cell;
- the warmest configured month is `annual + amplitude`;
- the opposite month is `annual - amplitude`;
- elevation, north/south gradient and accepted C1 temperature noise are inherited through the annual field;
- no new monthly temperature noise is added.

C4-A does not introduce a spatially varying seasonal amplitude.

## 6. Monthly precipitation

Let:

```text
raw_weight[m] =
    exp(
        precipitation_seasonality_log_amplitude
        * cos(phase(m, precipitation_peak_month))
    )

fraction[m] =
    raw_weight[m] / sum(raw_weight[1..12])

P_month[m] =
    annual_precipitation_mm * fraction[m]
```

Properties:
- every monthly precipitation field is strictly positive;
- the sum of all twelve monthly fields equals accepted C1 annual precipitation at every cell;
- `log_amplitude = 0` gives exactly uniform `1/12` monthly fractions;
- the wettest configured month is the peak month;
- no additional monthly precipitation noise is added.

C4-A deliberately keeps the accepted annual C1 spatial precipitation pattern fixed across months and redistributes only its annual total through time.

That means C4-A does **not** model:
- seasonal wind-direction changes;
- moving storm tracks;
- monsoon-front migration;
- seasonal orographic reversal.

Those require a later redesign if concrete use cases demand them.

## 7. Runtime state

When seasonality is enabled, `SurfaceState` gains internal climatological arrays:

```text
monthly_mean_temperature_c  float32 [12, rows, columns]
monthly_precipitation_mm    float32 [12, rows, columns]
```

Month axis order is exactly index 0 = month 1 through index 11 = month 12.

These arrays are deterministic and derived only from:
- accepted annual C1 arrays;
- explicit seasonality parameters.

They do not consume RNG.

When seasonality is absent, both runtime values are `None`.

## 8. Public DomainData export

The existing `FieldDescriptor` contract is 2D, so C4-A does not change it to 3D.

When seasonality is enabled, assembly exports 24 additional **derived** 2D fields:

```text
temperature_month_01
...
temperature_month_12

precipitation_month_01
...
precipitation_month_12
```

Descriptor semantics:

```text
temperature_month_NN:
  role = derived
  dtype = float32
  unit = degC
  shape = grid shape

precipitation_month_NN:
  role = derived
  dtype = float32
  unit = mm/month
  shape = grid shape
```

Existing canonical fields remain:

```text
temperature
annual_precipitation
```

and remain authoritative annual climate fields.

C4-A does not rename or replace them.

## 9. Relationship to C2 and C3

C4-A is accepted/rejected independently.

During C4-A:
- C2 effective moisture continues to use accepted annual temperature/precipitation;
- C3 vegetation continues to use accepted annual temperature + C2 moisture;
- no biome labels are generated;
- no seasonal stream permanence is generated.

Reason:

```text
annual climate
→ monthly envelope C4-A   [new layer under review]

annual climate
→ C2 moisture
→ C3 vegetation           [accepted frozen semantics]
```

Changing C2/C3 in the same checkpoint would make it impossible to determine whether a bad result came from seasonality generation or from seasonal ecological/hydrologic response.

## 10. What C4-A unlocks later

After C4-A acceptance, later bounded designs may derive:
- warmest/coldest month metrics;
- wettest/driest month metrics;
- growing-season duration;
- dry-season severity;
- seasonal vegetation constraints;
- biome classification;
- stronger evidence for channel-regime classification.

C4-A alone is **not sufficient** to label channels perennial/seasonal/dry because groundwater/baseflow/storage remain absent.

It removes the missing-seasonality blocker but not the missing-baseflow blocker.

## 11. Automated guardrails

### S01 — temperature annual-mean conservation

At every cell:

```text
mean(T_month[1..12]) == annual_mean_temperature_c
```

within deterministic float tolerance.

### S02 — precipitation annual-total conservation

At every cell:

```text
sum(P_month[1..12]) == annual_precipitation_mm
```

within deterministic float tolerance.

### S03 — temperature phase

With positive amplitude, the configured temperature peak month is maximal and the opposite month is minimal.

### S04 — precipitation phase

With positive precipitation seasonality, the configured precipitation peak month has the maximal monthly fraction.

### S05 — zero temperature amplitude

Amplitude `0` produces twelve monthly temperature fields exactly equal to the annual temperature field.

### S06 — zero precipitation seasonality

Log amplitude `0` produces twelve monthly precipitation fields exactly equal to `annual_precipitation / 12`.

### S07 — positivity / finiteness

All monthly arrays are finite.
Monthly precipitation is strictly positive.

### S08 — no hidden spatial seasonality

For a fixed month, monthly precipitation divided by annual precipitation is spatially constant within numeric tolerance.

This guard deliberately freezes the C4-A limitation that monthly timing redistributes the accepted annual field rather than generating a second spatial climate model.

### S09 — upstream annual immutability

Terrain, Hydrology, accepted annual C1 fields, C2 moisture and C3 vegetation remain unchanged.

### S10 — no-seasonality compatibility

A Core 0.2 request without `climate.seasonality` remains bit-identical to the frozen prealpha annual-only generation path and exports no monthly fields.

### S11 — Core 0.1 compatibility

Core 0.1 remains unchanged and cannot contain the C4 seasonality recipe.

### S12 — public export contract

When C4 is enabled:
- exactly 12 temperature-month derived fields exist;
- exactly 12 precipitation-month derived fields exist;
- names, units, dtypes and shapes are exact;
- annual canonical fields remain canonical.

### S13 — replay

Identical plan/attempt produces bit-identical monthly arrays and bundle payloads.

Changing only seasonality parameters changes the plan fingerprint.

## 12. Operator checkpoint C4-A

Use the accepted representative Core 0.2 world and one explicit seasonality recipe.

Recommended diagnostic recipe:

```text
temperature_seasonal_amplitude_c = 7
temperature_peak_month = 7

precipitation_seasonality_log_amplitude = 1
precipitation_peak_month = 1
```

This intentionally creates a warm-season / wet-season phase offset that is easy to inspect.

Required evidence:
1. annual temperature + warmest month + coldest month;
2. annual precipitation + wettest month + driest month;
3. twelve-month temperature curve at several representative cells;
4. twelve-month precipitation-fraction curve;
5. per-cell annual temperature conservation error map/statistics;
6. per-cell annual precipitation conservation error map/statistics;
7. confirmation that C2 moisture and C3 vegetation hashes are unchanged;
8. monthly-field descriptor inventory.

Operator questions:
- is seasonality smooth and interpretable rather than noisy?
- are configured peak months correct?
- is annual climate preserved exactly enough?
- does the same annual spatial structure remain recognizable across months?
- is the limitation of fixed regional seasonal phase acceptable for this bounded layer?

## 13. Stop rules

- Do not infer latitude or hemisphere from map coordinates.
- Do not add hidden peak-month defaults.
- Do not add monthly random/coherent noise.
- Do not rotate moisture-bearing wind by season in C4-A.
- Do not modify accepted annual C1 fields to make monthly maps prettier.
- Do not rewrite C2 moisture or C3 vegetation in C4-A.
- Do not classify biomes in C4-A.
- Do not classify perennial/seasonal/dry channels in C4-A.
- Do not introduce soils, groundwater, snowpack or daily weather in this slice.
- If fixed spatial precipitation fractions are insufficient for a concrete later use case, redesign seasonal transport explicitly rather than hiding a second monthly climate model inside C4-A.

## 14. Acceptance boundary

C4-A implementation may be accepted only if:
- S01–S13 are green;
- annual C1/C2/C3 outputs remain unchanged;
- no-seasonality Core 0.2 compatibility is proven;
- operator-visible seasonal checkpoint is reviewed;
- explicit implementation ACCEPT / REJECT is recorded.

Green CI alone is not acceptance.
