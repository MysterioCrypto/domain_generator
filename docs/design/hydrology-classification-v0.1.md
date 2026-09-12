---
id: DESIGN-HYDROLOGY-CLASSIFICATION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Hydrology Classification v0.1

Этот checkpoint развивает deterministic routing core до semantic классификации stream и lake candidates, но ещё не materialize-ит canonical `water_depth` или vector `RiverNetwork`.

## Semantic hydrology recipe

`DomainSpec` получает обязательную секцию:

```yaml
hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
```

Все три значения являются semantic world inputs:

- `stream_threshold_km2 > 0`;
- `lake_min_area_km2 > 0`;
- `lake_min_depth_m > 0`.

Hidden defaults в Core 0.1 запрещены. Секция обязательна в `DomainSpec` и компилируется без RNG в immutable `GenerationPlan.hydrology`.

`GenerationPlan.hydrology` входит в semantic plan fingerprint.

## Routing fill vs drainage gradient

Priority-Flood теперь materialize-ит два разных elevation fields:

```text
canonical terrain
      ↓
Priority-Flood
  ├── fill_elevation_m
  └── routing_elevation_m
```

### `fill_elevation_m`

Физический depression-fill level без искусственного drainage gradient.

Для neighbor, достигнутого из processed cell `current`:

```text
fill[neighbor] = max(terrain[neighbor], fill[current])
```

Edge cells retain canonical terrain elevation.

### `routing_elevation_m`

Численная routing surface из Hydrology Routing Core v0.1. Она получает minimum 1-ULP gradient через `nextafter` там, где иначе возникла бы flat/depression ambiguity.

`routing_elevation_m` существует только для deterministic D8 routing.

`fill_elevation_m` используется для lake classification и не содержит synthetic ULP slope.

Ни одно поле не мутирует `TerrainState.elevation_m`.

## Stream candidates

После flow accumulation:

```text
stream_mask = flow_accumulation_km2 >= stream_threshold_km2
```

- dtype `bool`;
- shape совпадает с grid;
- threshold выражен в physical km²;
- stream mask является runtime classification, ещё не vector `RiverNetwork`.

Stream classification deterministic и не использует RNG.

## Potential lake depth

Для каждой grid cell:

```text
potential_lake_depth_m = fill_elevation_m - canonical_elevation_m
```

Priority-Flood invariant гарантирует `potential_lake_depth_m >= 0`.

Cell является depression cell iff:

```text
potential_lake_depth_m > 0
```

Synthetic ULP routing gradient никогда не участвует в lake depth.

## Lake candidate components

Depression cells группируются по 8-connectivity, соответствующей D8 neighborhood.

Для каждой connected component вычисляются:

```text
cells
area_km2 = cell_count * cell_size_km²
max_depth_m = max(potential_lake_depth_m)
surface_elevation_m = common fill elevation of component
```

В корректном Priority-Flood fill одна connected positive-depth component имеет один физический fill/spill level. Если внутри одной component обнаруживаются разные exact `fill_elevation_m`, это engine invariant failure, а не silent averaging.

Component становится `LakeCandidate` только если одновременно:

```text
area_km2 >= lake_min_area_km2
max_depth_m >= lake_min_depth_m
```

Не прошедшие thresholds depressions остаются routing information и не объявляются озёрами.

Lake candidates сортируются deterministically по lexicographically smallest `(row, column)` cell; `cells` внутри candidate сортируются lexicographically.

## Runtime state

```text
HydrologyState
├── routing_elevation_m       float64
├── fill_elevation_m          float64
├── flow_direction            int8
├── flow_accumulation_km2     float64
├── stream_mask               bool
└── lake_candidates           tuple[LakeCandidate, ...]
```

```text
LakeCandidate
├── cells                     tuple[(row, column), ...]
├── area_km2                  float
├── max_depth_m               float
└── surface_elevation_m       float
```

Это runtime types, не serialized `DomainData` contracts.

## Contract boundary

Этот checkpoint изменяет serialized inputs/plan:

- `DomainSpec.hydrology`;
- `GenerationPlan.hydrology`;
- generated JSON Schema snapshots;
- compiler transfer;
- semantic plan fingerprint.

Он НЕ изменяет `DomainData` output contract: тот уже заранее определяет canonical `water_depth`, generated hydro/lake features и directed `RiverNetwork`.

## Validation

Hydrology validation дополнительно проверяет:

- `fill_elevation_m` shape/dtype/finite;
- `fill_elevation_m >= canonical terrain`;
- `routing_elevation_m >= fill_elevation_m`;
- `stream_mask` bool + correct shape;
- `stream_mask` exactly equals plan threshold classification;
- every lake candidate cells are unique, in bounds and depression cells;
- candidate area equals exact cell count × cell area;
- candidate max depth matches field;
- candidate cells are 8-connected;
- candidate fill surface is constant;
- every candidate satisfies both plan lake thresholds;
- candidate ordering is canonical.

No RNG is used.

## Non-goals

Not included:

- canonical `water_depth`;
- raster river width/depth model;
- vector stream/river extraction;
- `RiverNetwork` materialization;
- lake polygon vectorization / `HydroFeature` assembly;
- runoff/discharge/climate model;
- terrain erosion or mutation.

Следующий bounded checkpoint: stream/lake vectorization and river-water semantics needed to assemble canonical `water_depth`, generated lake features and `RiverNetwork`.
