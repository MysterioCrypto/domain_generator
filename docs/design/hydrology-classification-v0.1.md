---
id: DESIGN-HYDROLOGY-CLASSIFICATION-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Классификация Hydrology v0.1

Этот checkpoint развивает детерминированный routing core до семантической классификации candidates streams и lakes, но ещё не materialize-ит canonical `water_depth` или vector `RiverNetwork`.

## Семантический recipe hydrology

`DomainSpec` получает обязательную секцию:

```yaml
hydrology:
  stream_threshold_km2: 25.0
  lake_min_area_km2: 1.0
  lake_min_depth_m: 2.0
```

Все три значения являются семантическими входными данными мира:

- `stream_threshold_km2 > 0`;
- `lake_min_area_km2 > 0`;
- `lake_min_depth_m > 0`.

Скрытые defaults в Core 0.1 запрещены. Секция обязательна в `DomainSpec` и без RNG компилируется в неизменяемый `GenerationPlan.hydrology`.

`GenerationPlan.hydrology` входит в semantic plan fingerprint.

## Routing fill и градиент drainage

Priority-Flood теперь materialize-ит два разных поля elevation:

```text
canonical terrain
      ↓
Priority-Flood
  ├── fill_elevation_m
  └── routing_elevation_m
```

### `fill_elevation_m`

Физический уровень заполнения впадин без искусственного drainage gradient.

Для neighbor, достигнутого из processed cell `current`:

```text
fill[neighbor] = max(terrain[neighbor], fill[current])
```

Edge cells сохраняют canonical terrain elevation.

### `routing_elevation_m`

Численная routing surface из Hydrology Routing Core v0.1. Она получает минимальный 1-ULP gradient через `nextafter` там, где иначе возникла бы неоднозначность flat/depression.

`routing_elevation_m` существует только для детерминированного D8 routing.

`fill_elevation_m` используется для классификации lakes и не содержит synthetic ULP slope.

Ни одно поле не мутирует `TerrainState.elevation_m`.

## Candidates streams

После flow accumulation:

```text
stream_mask = flow_accumulation_km2 >= stream_threshold_km2
```

- dtype `bool`;
- shape совпадает с grid;
- threshold выражен в физических km²;
- stream mask является runtime classification, ещё не vector `RiverNetwork`.

Классификация streams детерминирована и не использует RNG.

## Потенциальная глубина lake

Для каждой grid cell:

```text
potential_lake_depth_m = fill_elevation_m - canonical_elevation_m
```

Invariant Priority-Flood гарантирует `potential_lake_depth_m >= 0`.

Cell является depression cell тогда и только тогда, когда:

```text
potential_lake_depth_m > 0
```

Synthetic ULP routing gradient никогда не участвует в lake depth.

## Компоненты candidates lake

Depression cells группируются по 8-connectivity, соответствующей D8 neighborhood.

Для каждой connected component вычисляются:

```text
cells
area_km2 = cell_count * cell_size_km²
max_depth_m = max(potential_lake_depth_m)
surface_elevation_m = common fill elevation of component
```

В корректном Priority-Flood fill одна connected positive-depth component имеет один физический уровень fill/spill. Если внутри одной component обнаруживаются разные exact `fill_elevation_m`, это нарушение engine invariant, а не скрытое усреднение.

Component становится `LakeCandidate` только если одновременно:

```text
area_km2 >= lake_min_area_km2
max_depth_m >= lake_min_depth_m
```

Depressions, не прошедшие thresholds, остаются routing information и не объявляются озёрами.

Candidates lakes детерминированно сортируются по лексикографически минимальной cell `(row, column)`; `cells` внутри candidate также сортируются лексикографически.

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

Это runtime types, а не serialized contracts `DomainData`.

## Граница contracts

Этот checkpoint изменяет serialized inputs/plan:

- `DomainSpec.hydrology`;
- `GenerationPlan.hydrology`;
- generated JSON Schema snapshots;
- transfer compiler-а;
- semantic plan fingerprint.

Он НЕ изменяет output contract `DomainData`: тот уже заранее определяет canonical `water_depth`, generated hydro/lake features и направленный `RiverNetwork`.

## Validation

Validation hydrology дополнительно проверяет:

- shape/dtype/finite для `fill_elevation_m`;
- `fill_elevation_m >= canonical terrain`;
- `routing_elevation_m >= fill_elevation_m`;
- `stream_mask` имеет bool dtype и правильный shape;
- `stream_mask` в точности соответствует threshold classification из plan;
- cells каждого candidate lake уникальны, находятся в bounds и являются depression cells;
- area candidate равна точному cell count × cell area;
- max depth candidate совпадает с field;
- cells candidate 8-connected;
- fill surface candidate постоянна;
- каждый candidate удовлетворяет обоим thresholds lake из plan;
- порядок candidates канонический.

RNG не используется.

## Что не входит

- canonical `water_depth`;
- raster-модель ширины/глубины rivers;
- vector extraction streams/rivers;
- materialization `RiverNetwork`;
- vectorization polygon lakes / сборка `HydroFeature`;
- модель runoff/discharge/climate;
- erosion или мутация terrain.

Следующий ограниченный checkpoint: vectorization streams/lakes и семантика river-water, необходимые для сборки canonical `water_depth`, generated lake features и `RiverNetwork`.
