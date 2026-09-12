---
id: DESIGN-HYDROLOGY-NETWORK-WATERDEPTH-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# RiverNetwork и WaterDepth Hydrology v0.1

Этот checkpoint превращает runtime classification streams/lakes в направленный `RiverNetwork` и canonical raster `water_depth_m`, не вводя физическую ширину river и не выполняя vectorization polygons lakes.

## Область действия

Вход:

```text
TerrainState.elevation_m
HydrologyState.routing_elevation_m
HydrologyState.fill_elevation_m
HydrologyState.flow_direction
HydrologyState.flow_accumulation_km2
HydrologyState.stream_mask
HydrologyState.lake_candidates
GenerationPlan.hydrology
```

Дополнения к runtime `HydrologyState` на выходе:

```text
river_network: RiverNetwork
water_depth_m: float32[rows, columns]
```

RNG не используется.

## Расширение semantic recipe hydrology

`DomainSpec.hydrology` и `GenerationPlan.hydrology` дополнительно требуют:

```yaml
river_depth_at_threshold_m: <float > 0>
river_depth_exponent: <float >= 0>
```

Это семантические inputs, участвующие в fingerprints spec/plan.

Скрытых defaults нет.

## Стабильные id lakes

Принятые candidates lakes уже находятся в каноническом порядке.

Id назначаются по каноническому порядку candidates:

```text
lake-0001
lake-0002
lake-0003
...
```

Эти id являются runtime references для `RiverNode.feature_id` и будущей сборки hydro features в `DomainData`.

Текущий checkpoint не materialize-ит `AreaGeometry` lakes.

## Raster-граф rivers

Stream cell — это cell, для которой `stream_mask == true`.

Направленное ребро stream-to-stream существует от stream cell `A` к её D8 receiver `B` тогда и только тогда, когда:

- `A` не является cell принятого lake;
- `B` находится внутри domain;
- `B` является stream cell;
- `B` не является cell принятого lake.

Cells принятых lakes подавляют внутренние видимые river edges, хотя D8 routing внутри них сохраняется.

Для каждой stream cell вне принятых lakes определяется **effective visible indegree**:

```text
ordinary upstream stream-to-stream edges
+ incoming lake_outlet transitions
```

Это предотвращает ситуацию, когда outlet lake и обычный tributary соединяются в одной downstream stream cell без node confluence.

## Nodes network

River node создаётся в каждой топологической точке разрыва видимого stream graph.

### source

Stream cell вне lakes с effective visible indegree `0`.

Position: canonical world-space center cell.

### confluence

Stream cell вне lakes с effective visible indegree `>= 2`.

Position: canonical world-space center cell.

### domain_outlet

Stream path, достигающий outlet edge-cell, создаёт node `domain_outlet` на фактической boundary domain.

Segment включает center edge cell, затем boundary point.

Boundary point — ортогональная проекция center edge-cell на выбранную сторону domain.

Для corner edge cell канонический приоритет sides:

```text
north, east, south, west
```

`boundary_side` соответствует выбранной стороне.

### lake_inflow

Когда receiver D8 stream cell вне lake находится внутри принятого lake `L`, создаётся node `lake_inflow` с `feature_id = lake-id(L)`.

Position — midpoint между center внешней stream cell и center внутренней lake cell.

Допускается несколько inflows на один lake.

### lake_outlet

Когда lake cell имеет D8 receiver вне того же принятого lake и receiver является stream cell, создаётся node `lake_outlet` с id этого lake.

Position — midpoint между center внутренней lake cell и center внешней stream cell.

Если routing создаёт несколько outlets у lake, допускаются все.

Внутренние D8 edges внутри принятых lakes никогда не становятся river segments.

## Извлечение segments

Segments соединяют river nodes вдоль downstream raster graph.

Начиная от downstream continuation каждого node, алгоритм следует по единственным stream successors до следующего условия node.

Centerline каждого segment — упорядоченный tuple world-space points от upstream node position до downstream node position.

Промежуточные raster stream points — canonical centers cells.

Smoothing/spline simplification в v0.1 не применяется.

Id segments назначаются после канонической сортировки:

```text
river-segment-0001
river-segment-0002
...
```

Канонический ключ сортировки segment:

```text
(from_node_id, to_node_id, centerline coordinates)
```

Id nodes назначаются после сортировки descriptors nodes по:

```text
(kind, position.x_km, position.y_km, boundary_side-or-empty, feature_id-or-empty)
```

с id:

```text
river-node-0001
river-node-0002
...
```

## Свойство catchment segment

`RiverSegment.properties.catchment_area_km2` равно `flow_accumulation_km2` в последней raster stream cell segment перед переходом в downstream node.

Для segment, заканчивающегося domain outlet, используется terminal edge stream cell.

Для segment, заканчивающегося lake inflow, используется внешняя stream cell непосредственно перед входом в lake.

Для segment, заканчивающегося confluence, используется последняя upstream raster stream cell перед confluence. Если segment `lake_outlet` сразу входит в confluence, используется последняя lake cell перед outlet transition; accumulation receiver confluence не используется, потому что оно уже включает другие входящие branches.

Для segment, начинающегося lake outlet и продолжающегося через обычные внешние stream cells, downstream accumulation следует по этому внешнему stream path до следующего node transition.

## Proxy глубины river

Для stream cells вне принятых lakes:

```text
A  = flow_accumulation_km2
A0 = stream_threshold_km2
D0 = river_depth_at_threshold_m
p  = river_depth_exponent

river_depth_m = D0 * (A / A0) ** p
```

Поскольку stream cells удовлетворяют `A >= A0`, отношение не меньше 1.

Это явный детерминированный proxy, а не симуляция discharge/hydraulics.

## Глубина lake

Для cells принятых lakes:

```text
lake_depth_m = fill_elevation_m - terrain_elevation_m
```

Только cells принятых candidates lakes становятся canonical lake water в этом checkpoint. Depressions ниже thresholds остаются сухими в canonical `water_depth_m`.

## Canonical water depth

Для каждой grid cell:

```text
if cell belongs to accepted lake candidate:
    water_depth = fill - terrain
elif stream_mask[cell]:
    water_depth = river depth proxy
else:
    water_depth = 0
```

Классификация lake имеет приоритет над stream classification, подавляя технические D8 river lines внутри lakes.

Вычисления выполняются в float64. Один финальный cast создаёт canonical runtime:

```text
water_depth_m.dtype == float32
```

Все значения должны быть конечными и `>= 0`.

## Runtime state

```text
HydrologyState
├── routing_elevation_m
├── fill_elevation_m
├── flow_direction
├── flow_accumulation_km2
├── stream_mask
├── lake_candidates
├── river_network
└── water_depth_m
```

`river_network` использует существующий сериализационно совместимый type `contracts.data.RiverNetwork`, но остаётся runtime output до сборки `DomainData`.

## Validation

Validation hydrology дополнительно проверяет:

- shape `water_depth_m` совпадает с grid;
- dtype ровно float32;
- все значения конечны и неотрицательны;
- cells принятых lakes равны физической fill depth;
- stream cells вне принятых lakes равны точному proxy river depth после cast в float32;
- non-lake/non-stream cells равны нулю;
- id nodes/segments river network канонические и references валидны;
- source nodes соответствуют effective visible indegree 0;
- confluence nodes соответствуют effective visible indegree >= 2;
- domain outlets лежат на объявленной boundary side;
- lake nodes ссылаются на canonical ids принятых lakes;
- centerlines segments следуют downstream topology stream D8 и никогда не проходят через interior принятого lake;
- свойство catchment segment соответствует semantics terminal raster accumulation.

Любая несогласованность topology является нарушением engine invariant/capability. Скрытых repair/retry нет.

## Что не входит

- физическая ширина river;
- sub-cell rasterization river;
- модель discharge/runoff;
- модель precipitation/climate;
- erosion channel;
- meandering/smoothing;
- vectorization polygon lakes;
- materialization `HydroFeature`;
- assembler/export `DomainData`.
