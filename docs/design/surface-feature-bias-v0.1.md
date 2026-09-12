---
id: DESIGN-SURFACE-FEATURE-BIAS-0.1
kind: design
status: accepted
normative: true
target: core-0.1
---

# Surface Feature Bias v0.1

## Scope

Core 0.1 adds two generic surface operators over concrete `AreaGeometry`:

- `moisture_bias`;
- `vegetation_bias`.

These operators are setting-agnostic numeric field modifiers. They do not encode forest, wetland, biome, climate, soil or other domain-specific semantics.

## Upstream inputs

Surface generation reads immutable upstream outputs:

```text
LayoutCandidate
TerrainState
HydrologyState
GenerationPlan
```

Surface never mutates layout, terrain or hydrology.

Only features with `family=surface` are handled by this slice. Every such feature must use `effect.stage=surface`, have concrete geometry in `LayoutCandidate.geometry_realizations`, and use a supported operator/geometry combination. Unsupported constructs are explicit capability errors; they are never silently skipped.

## Supported operators

### moisture_bias

Required exact effect parameter set:

```text
{"delta_moisture"}
```

`delta_moisture` resolves to one finite float in `[-1, 1]`.

For each raster cell whose world-space center lies inside or on the feature `AreaGeometry`, the feature contributes that signed delta to the moisture contribution field. Other cells receive zero contribution.

### vegetation_bias

Required exact effect parameter set:

```text
{"delta_vegetation"}
```

`delta_vegetation` resolves to one finite float in `[-1, 1]`.

For each raster cell whose world-space center lies inside or on the feature `AreaGeometry`, the feature contributes that signed delta to the vegetation contribution field. Other cells receive zero contribution.

## Rasterization

Area rasterization uses the existing canonical world-coordinate cell-center rule:

```text
cell center inside/on AreaGeometry -> feature applies
otherwise                         -> feature does not apply
```

No edge smoothing, sub-cell coverage, renderer sampling or polygon mutation is introduced in v0.1.

## Parameter sampling and RNG

Surface feature effect parameters use the existing generic resolved-parameter sampling machinery.

RNG key:

```text
stage   = surface
scope   = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Changing feature iteration order or unrelated features must not change the sampled value of another feature.

Rasterization and contribution accumulation consume no RNG.

## Additive and order-independent composition

Each supported surface feature materializes its own float64 contribution field.

Features are processed in canonical ascending `feature.id` order. Signed contributions are accumulated in float64. Overlap is allowed and is not a conflict.

No per-feature clamp is allowed.

### Moisture

```text
BaseMoisture64
+ sum(MoistureBiasContribution64)
= BiasedMoisture64
-> clamp once to [0, 1]
-> canonical water cells forced to 1
= Moisture64
```

A moisture bias therefore also affects downstream terrestrial vegetation because vegetation potential is derived from final moisture.

### Vegetation

```text
slope_factor = clamp(1 - slope_deg / vegetation_slope_zero_deg, 0, 1)
VegetationPotential64 = Moisture64 * slope_factor

VegetationPotential64
+ sum(VegetationBiasContribution64)
= BiasedVegetation64
-> clamp once to [0, 1]
-> canonical water cells forced to 0
= Vegetation64
```

Canonical water is defined only by `water_depth_m > 0`.

Only after all composition and water overrides are complete are canonical fields cast once to float32.

## Water precedence

Surface biases cannot override canonical water semantics:

```text
water_depth_m > 0 -> moisture = 1
water_depth_m > 0 -> vegetation_density = 0
```

This prevents generic terrestrial surface effects from creating dry water cells or terrestrial vegetation on canonical water.

## Validation

Surface validation checks at least:

- upstream layout exists and attempt index matches;
- terrain and hydrology exist and match grid shape;
- surface state exists, uses float32, is finite and in `[0,1]`;
- canonical water overrides are exact;
- every expected surface feature is applied exactly once;
- deterministic recomputation matches the stored `SurfaceState` exactly.

Expected surface feature ids are all `GenerationPlan.features` with `family=surface`.

## Capability errors

The attempt fails explicitly for unsupported/malformed surface feature semantics, including:

- surface family with non-surface effect stage;
- missing materialized geometry;
- reservation layout instead of concrete geometry;
- geometry other than `AreaGeometry`;
- unsupported surface operator;
- wrong exact effect parameter set;
- non-float resolved parameter recipe;
- unsupported parameter sampler;
- non-numeric or non-finite sampled value;
- delta outside `[-1,1]`.

## Non-goals v0.1

Not included:

- binary forest/wetland/biome masks;
- climate, temperature, precipitation or seasonality;
- soil simulation;
- multiplicative or priority-based biases;
- surface shaping operators;
- edge falloff/feathering;
- Band/Corridor surface influence;
- aquatic vegetation;
- setting-specific surface types or preset vocabulary.

Setting-specific presets may resolve to these generic operators externally, but such vocabulary is not part of Core semantics.
