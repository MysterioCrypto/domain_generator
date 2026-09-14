# Hydrology & River Geometry v0.2

Status: **proposed design gate**  
Target branch: `dev/0.2`  
Upstream prerequisite: Continuous Terrain Foundation v0.2 (`bbd8a7fb2c9ddb39d348f4d1c472c512f14e2148`)  
Application boundary fix: `52292dd7163a3df103df3b2f2d8fa77add0cbbe8`

## 1. Причина изменения

После принятия Continuous Terrain Foundation текущая Hydrology 0.1 была без изменений прогнана на новом рельефе 180×120 км.

Аудит подтвердил две разные вещи:

1. новый continuous terrain сам по себе исправил исходную проблему пустой плоскости;
2. речная сеть всё ещё наследует raster/D8 representation слишком буквально.

В audit fixture текущий pipeline создал:

```text
13 lake features
63 river nodes
45 river segments
23 lake_outlet nodes
11 confluences
11 sources
9 domain outlets
9 lake inflows
```

При этом `RiverSegment.centerline` по-прежнему строится как последовательность центров D8-клеток. На карте это проявляется длинными горизонтальными/вертикальными/45° участками и резкими углами. Дополнительно 13 озёр породили 23 `lake_outlet`, потому что Core 0.1 материализует каждый переход `lake cell → outside stream cell` как отдельный outlet.

Batch B исправляет hydrology semantics и canonical river vector geometry. Это не presentation-only изменение.

## 2. Scope Batch B

Batch B является одним bounded slice:

```text
conditioned elevation
→ raster drainage topology
→ accepted lakes
→ canonical single-outlet lake routing
→ effective accumulation
→ stream/channel skeleton
→ semantic river graph
→ deterministic vector river geometry
→ hydrology-only visual checkpoint
```

Pipeline order не меняется:

```text
Layout → Terrain → Hydrology → Surface → Placement → Final
```

Новая generation stage не добавляется.

В Batch B не перерабатываются:

- Terrain synthesis;
- Surface/climate/vegetation;
- POI placement;
- artistic/cartographic final renderer;
- coastal/ocean model;
- precipitation/runoff balance;
- hydraulic erosion;
- physically simulated river width/discharge.

## 3. Главный принцип

Core 0.1 фактически использует одну и ту же дискретную структуру одновременно как:

```text
routing representation
≈ drainage topology
≈ final RiverSegment geometry
```

Core 0.2 разделяет эти роли:

```text
raster routing graph
        ↓
semantic drainage topology
        ↓
vector river reconstruction
        ↓
RiverNetwork / RiverSegment.centerline
```

**INV-HYD-001:** computational routing representation не является автоматически canonical river geometry.

D8 может оставаться внутренним способом вычислить receiver/catchment, но координаты центров D8-клеток не должны напрямую становиться финальным river polyline без reconstruction pass.

## 4. Priority Flood сохраняется

Batch B сохраняет существующий Priority Flood как depression conditioning mechanism.

Outputs остаются концептуально разделёнными:

- `fill_elevation_m` — physical fill surface, используемая для определения закрытых depression/lake candidates;
- `routing_elevation_m` — строго дренирующая техническая поверхность для построения acyclic receiver graph.

`routing_elevation_m` не является физическим terrain field и не экспортируется как world geography.

Batch B не меняет Terrain elevation ради удобства гидрологии.

## 5. D8 сохраняется как первый computational topology backend

Для Batch B canonical routing backend остаётся single-flow D8.

Причины:

- он уже детерминирован;
- даёт однозначный receiver и directed acyclic graph после conditioning;
- flow accumulation и topology хорошо тестируются;
- основная визуально подтверждённая проблема сейчас — буквальное превращение raster path в river geometry;
- замена одновременно routing backend и geometry reconstruction затруднит диагностику.

Это осознанное промежуточное решение, а не утверждение, что D8 достаточен навсегда.

После visual checkpoint действует правило:

> Если reconstructed vectors всё ещё демонстрируют систематически неверную basin/channel topology, следующий bounded slice заменяет routing backend (например, D∞/continuous-flow approach). Batch B не маскирует такую проблему дополнительной декоративной постобработкой.

## 6. Canonical lake outlet

### 6.1 Проблема Core 0.1

Сейчас `build_river_network()` создаёт `lake_outlet` для каждого lake boundary cell, whose D8 receiver leaves the lake. Поэтому одно озеро может получить несколько независимых outlets и flow accumulation разделяется между ними.

Для обычного accepted lake в Batch B это запрещено.

### 6.2 Правило

Каждый accepted internal lake получает **ровно один canonical spill outlet**.

Для lake candidate собираются boundary transitions:

```text
(lake_cell, outside_neighbor)
```

которые являются допустимыми downstream exits на conditioned routing graph.

Canonical transition выбирается детерминированным ranking, основанным сначала на физическом spill saddle, затем на conditioned downstream elevation, затем на stable grid-coordinate tie-break.

Conceptual key:

```text
(
  saddle_elevation,
  downstream_routing_elevation,
  lake_row,
  lake_column,
  receiver_row,
  receiver_column
)
```

Точные numeric epsilon/tie rules фиксируются implementation tests и не зависят от iteration order.

**INV-HYD-002:** один accepted internal lake → один semantic `lake_outlet`.

## 7. Lake routing collapse

Выбрать один outlet только при materialization недостаточно: raster accumulation тоже должна агрегировать catchment озера в этот outlet.

После lake detection Batch B выполняет lake-collapse routing pass:

1. берётся исходный strictly-draining D8 graph;
2. для каждого accepted lake выбирается canonical outlet boundary cell и его outside receiver;
3. внутри lake component строится deterministic acyclic 8-neighbor tree к outlet cell;
4. outlet cell направляется в canonical outside receiver;
5. остальные non-lake receivers не меняются;
6. flow accumulation вычисляется заново на canonical receiver graph.

Внутреннее routing по поверхности озера является вычислительным tree, а не физическим руслом внутри воды.

Следствия:

- весь upstream catchment, впавший в lake, выходит через один outlet;
- downstream catchment не теряется и не разделяется между случайными raster exits;
- stream mask внутри accepted lake не материализует скрытые «реки по поверхности озера».

## 8. Stream classification

Основное правило `stream_threshold_km2` сохраняется:

```text
stream cell ⇔ effective accumulation >= stream_threshold_km2
```

но accepted lake cells исключаются из visible channel mask.

Batch B не добавляет новые user-facing lake-count или precipitation parameters. `lake_min_area_km2` и `lake_min_depth_m` пока сохраняют текущую семантику.

Причина: audit выявил несомненный topology/outlet defect, но сам факт 13 озёр на 21 600 км² ещё недостаточен, чтобы вводить новый lake-climate contract. Lake abundance повторно оценивается на hydrology visual checkpoint.

## 9. Semantic river graph

River graph по-прежнему состоит из semantic nodes:

- `source`;
- `confluence`;
- `lake_inflow`;
- `lake_outlet`;
- `domain_outlet`.

Nodes создаются из canonical channel topology, а не из presentation geometry.

Required graph invariants:

1. directed graph acyclic;
2. каждый segment имеет существующие distinct endpoint nodes;
3. source indegree = 0;
4. ordinary confluence indegree >= 2;
5. domain outlet outdegree = 0;
6. lake inflow references accepted lake;
7. accepted internal lake имеет ровно один lake outlet;
8. effective catchment не уменьшается downstream вне специальных lake transitions;
9. no visible stream path silently terminates inside domain outside accepted lake.

`RiverSegmentProperties.catchment_area_km2` сохраняется. Batch B не меняет serialized DomainData version только ради дополнительной hierarchy metadata; stream hierarchy может вычисляться внутренне/диагностически и будет добавлена в public contract отдельным design decision при необходимости.

## 10. Raw channel chain

Между соседними semantic nodes сначала извлекается **raw channel chain** из canonical receiver graph.

Это raster computational object:

```text
(cell_0, cell_1, ..., cell_n)
```

Он используется как constraint/corridor для reconstruction, но не экспортируется как `RiverSegment.centerline`.

Raw chain должен быть:

- downstream ordered;
- cycle-free;
- contiguous по 8-neighborhood;
- anchored к semantic endpoints;
- reproducible.

## 11. River vector reconstruction

### 11.1 Цель

Получить deterministic world-space polyline, который следует тому же channel corridor, но не выглядит как последовательность клеточных центров.

### 11.2 Reconstruction pipeline

Conceptual sequence:

```text
raw channel cells
→ world-space raw polyline
→ remove redundant micro-zigzags / collinear anchors
→ endpoint-preserving continuous reconstruction
→ densify at stable world-space spacing
→ corridor/domain validation
→ RiverSegment.centerline
```

Конкретный curve primitive (например, constrained corner-cutting / spline interpolation) является implementation detail, если выполняются нормативные invariants ниже.

### 11.3 Channel corridor

Для каждого raw chain определяется allowable corridor из traversed raster cells с bounded sub-cell margin.

Final centerline обязана:

- начинаться и заканчиваться точно в semantic node positions;
- оставаться внутри domain;
- оставаться внутри или в нормативно малом buffer исходного channel corridor;
- не пересекать unrelated accepted lake;
- не создавать self-intersection внутри одного segment;
- не перескакивать в соседнюю ветвь сети;
- сохранять downstream order.

Это предотвращает «красивую, но выдуманную» реку, не связанную с hydrology result.

### 11.4 Grid-bias criterion

Final geometry не должна быть ограничена восемью D8 bearing angles.

Для segment с достаточной длиной reconstruction обязана создавать world-space direction samples, не сводимые только к multiples of 45°, кроме случаев, когда geometry действительно остаётся прямой после simplification.

Sharp raster staircase turns должны исчезнуть. Длинный straight channel допускается, если он сохраняется после reconstruction и соответствует corridor; Batch B не добавляет произвольные декоративные меандры только ради картинки.

## 12. Lakes and vector rivers

River/lake geometry obeys explicit boundary semantics:

- inflow centerline заканчивается на lake boundary node;
- outlet centerline начинается на единственном lake outlet node;
- через interior lake area RiverSegment не проводится;
- outflow не обязан визуально продолжать inflow одной линией;
- canonical lake geometry остаётся raster-derived RegionSet в Batch B.

Сглаживание shoreline не входит в этот slice.

## 13. Water depth

`water_depth_m` остаётся canonical raster field.

Lake depth продолжает происходить из physical fill minus terrain.
River depth продолжает быть deterministic function effective accumulation and existing hydrology parameters.

Но после lake-collapse pass downstream river depth использует **effective recomputed accumulation**, поэтому outflow получает catchment всего озера, а не одного случайного raster exit.

## 14. HydrologyState diagnostics

Batch B может расширить internal `HydrologyState` диагностическими структурами без добавления canonical bundle fields, например:

```text
raw_flow_direction
canonical_flow_direction
lake_outlets
raw_channel_chains
```

Если такие поля добавляются, они:

- internal only;
- deterministic;
- не меняют DomainBundle manifest;
- доступны тестам/checkpoint renderer;
- не должны становиться обязательным user-facing API без отдельного contract decision.

## 15. Validation

Hydrology validation v0.2 обязана проверять минимум:

- upstream Terrain exists/finite/grid-complete;
- physical fill >= terrain;
- canonical receiver graph acyclic;
- every non-outlet routable cell has valid receiver;
- one canonical outlet per accepted internal lake;
- all accepted lake cells reach their canonical outlet;
- recomputed accumulation finite and >= cell area;
- stream mask exactly matches effective accumulation threshold outside lake cells;
- river graph topologically complete;
- catchment is non-decreasing downstream;
- segment centerlines finite, in-domain, endpoint-exact;
- no adjacent duplicate vector points;
- reconstructed segment stays within allowed channel corridor;
- deterministic recomputation produces exact same network/rasters;
- renderer/checkpoint generation does not mutate HydrologyState.

## 16. Acceptance fixtures

Batch B добавляет минимум:

```text
H01 single-lake-single-outlet
H02 branching-catchment-confluence
H03 vectorized-long-channel
H04 terrain-v02-representative-hydrology
```

H01 должен специально содержать depression, где raw D8 имеет несколько потенциальных boundary exits, и доказывать collapse до одного canonical lake outlet.

H03 должен содержать длинный raw D8 staircase path и проверять, что final vector geometry:

- не равна raw cell-center chain;
- сохраняет endpoints/topology;
- stays in corridor;
- removes sharp staircase geometry.

## 17. Early visual checkpoint

После implementation Batch B останавливается **до переработки Surface**.

Diagnostic artifact должен показывать на одном и том же accepted terrain:

```text
elevation hillshade / hypsometry
+ accepted lakes
+ final vector rivers
+ semantic source/confluence/lake/outlet markers
```

Дополнительно полезен comparison overlay:

```text
raw D8 channel skeleton (thin neutral line)
vs
final RiverSegment.centerline (blue)
```

Human acceptance questions:

1. Читается ли network как drainage system, а не как набор «молний»?
2. Ушли ли obvious 8-direction staircases и sharp raster corners?
3. Следуют ли реки долинам/низинам принятого terrain, а не пересекают массивы случайно?
4. Есть ли у каждого внутреннего озера максимум один нормальный outlet?
5. Сохраняются ли естественные confluences и downstream hierarchy?
6. Не маскирует ли smoothing неверную topology?

Если ответ на 6 — «маскирует», Batch B не принимается и следующим решением становится routing-backend redesign, а не дополнительное украшение линий.

## 18. Non-goals

Batch B не обещает:

- климатически корректный runoff/discharge;
- seasonal rivers;
- flood plains;
- river erosion/canyon carving;
- deltas;
- braided rivers;
- tidal/coastal hydrology;
- final shoreline smoothing;
- artistic river symbols;
- arbitrary procedural meanders independent of terrain.

## 19. Invariants

INV-001..INV-011 остаются в силе.

Дополнительно для Batch B:

- **INV-HYD-001:** routing representation ≠ canonical river geometry;
- **INV-HYD-002:** один accepted internal lake имеет ровно один semantic outlet;
- **INV-HYD-003:** vector reconstruction не меняет drainage topology;
- **INV-HYD-004:** final river vector остаётся пространственно привязан к raw hydrologic corridor;
- **INV-HYD-005:** presentation/debug renderers не участвуют в выборе routing или geometry.
