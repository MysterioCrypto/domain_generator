---
id: DESIGN-HYDROFEATURE-LAKE-MATERIALIZATION-0.1
kind: design
status: accepted
normative: true
target: core-0.1
implemented: true
---

# HydroFeature / Lake Materialization v0.1

Этот документ фиксирует принятую семантику materialization raster `LakeCandidate` в semantic `HydroFeature` Core 0.1.

## Назначение и ownership

Hydrology уже классифицирует озёра как ordered `LakeCandidate` из grid cells. Materialization переводит этот готовый hydrology result в canonical vector feature; она не является новой simulation stage и не меняет raster state.

```text
LakeCandidate.cells
→ exact world-space cell squares
→ exact polygonal union
→ canonical RegionSet
→ HydroFeature
```

Materialization принадлежит hydrology layer. `DomainData Assembler` не vectorize raster заново: он только упаковывает готовые `lake_features`.

## Canonical identity

Сохраняется существующий порядок `lake_candidates`. IDs:

```text
candidate[0] → lake-0001
candidate[1] → lake-0002
...
```

Один helper `lake_feature_id(index_zero_based)` должен использоваться network, water и materializer, чтобы ID protocol не дублировался.

## Cell geometry

Для cell `(row, column)` и `s = cell_size_km`:

```text
x_min = column * s
x_max = (column + 1) * s
y_max = domain_height_km - row * s
y_min = domain_height_km - (row + 1) * s
```

Это соответствует принятому grid convention: southwest world origin, `+x` east, `+y` north, raster row 0 north.

Geometry озера равна точному union всех cell squares. Запрещены smoothing, marching-squares approximation, simplification, buffer-rounding, удаление holes и искусственные bridges между diagonal cells.

## Geometry contract

`AreaGeometry` недостаточен: D8-connected candidate может дать multipart polygon при diagonal touch, а connected footprint может иметь holes.

Поэтому Core 0.1 фиксирует:

```python
HydroFeature.geometry: RegionSet
```

Не используется union type `AreaGeometry | RegionSet`: все lakes имеют один contract. Exact union выполняется через существующий Shapely/GEOS backend и existing canonical `to_region_set` conversion. Новый polygon canonicalizer не вводится.

## HydroFeature и properties

Materialized feature:

```text
family = hydro
source.type = generated
source.system = hydrology
label = None
tags = ()
geometry = canonical RegionSet
```

`LakeProperties` хранит:

```text
area_km2
surface_elevation_m
max_depth_m
```

`max_depth_m` уже вычислен в `LakeCandidate` и участвует в lake qualification; materialization только переносит его, не пересчитывает.

Properties должны точно соответствовать source candidate.

## Area invariant

Площадь canonical `RegionSet` должна соответствовать `candidate.area_km2` в пределах backend numeric check. Ожидаемая площадь:

```text
len(candidate.cells) * cell_size_km²
```

Несогласованность — invariant/capability error, не повод исправлять properties или geometry скрытым fallback.

## RiverNetwork

`RiverNode.kind = lake_inflow/lake_outlet` уже использует `feature_id = lake-NNNN`. После materialization каждый такой ID обязан существовать в `HydrologyState.lake_features` и ссылаться на соответствующий `HydroFeature`.

Обратное требование не вводится: lake feature может не иметь видимого river inflow/outlet.

Materialization не перестраивает river topology.

## Runtime state

После implementation:

```python
HydrologyState.lake_features: dict[str, HydroFeature]
```

`lake_candidates` остаются runtime hydrology data. Materialization детерминирована и не использует RNG, IO, renderer или external model.

## Validation rules

Отклоняются:

- candidate cell вне grid;
- overlap accepted lake candidates;
- пустой candidate;
- пустой polygonal result;
- non-canonical `RegionSet`;
- area mismatch с `candidate.area_km2`;
- duplicate lake feature id;
- river lake reference на отсутствующий materialized lake.

Silent fallback geometry запрещён.

## Implementation checkpoint v0.1

Реализованы:

- canonical `lake_feature_id` helper;
- exact cell-square union materializer;
- `HydroFeature.geometry: RegionSet`;
- `LakeProperties.max_depth_m`;
- `HydrologyState.lake_features`;
- единый ID protocol для network/water/materializer;
- validation и tests для simple polygon, hole, diagonal D8 multipart geometry, IDs/order/properties/error cases;
- schema snapshot regeneration из-за изменения serialized contracts.

Не входят shoreline smoothing, volume, names/tags generation, runoff/climate, river width polygons, изменение lake classification/D8, DomainData Assembler, export, renderer, CLI и adapters.
