---
id: DESIGN-HYDROLOGY-ROUTING-CORE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Ядро routing Hydrology v0.1

Этот документ фиксирует первый вертикальный slice hydrology: детерминированный drainage routing поверх canonical terrain без изменения canonical elevation.

## Область действия

Pipeline:

```text
TerrainState.elevation_m
        ↓ copy to float64
Priority-Flood conditioning
        ↓
RoutingSurface
        ↓
deterministic D8 receivers
        ↓
flow accumulation (km²)
        ↓
HydrologyState
```

В этот slice не входят extraction streams, `water_depth`, lakes, vector rivers, river width/discharge, модель runoff/climate, erosion или surface moisture.

`stream_threshold_km2` намеренно отложен: это semantic parameter hydrology, но `GenerationPlan v0.1` пока не имеет принятого contract recipe hydrology. Скрытая константа запрещена.

## Неизменяемость upstream

Hydrology читает canonical `TerrainState.elevation_m` и никогда его не мутирует.

Все corrections depressions происходят только в runtime `routing_elevation_m`.

## Runtime HydrologyState

```text
HydrologyState
├── routing_elevation_m       float64 [rows, columns]
├── flow_direction            int8    [rows, columns]
└── flow_accumulation_km2     float64 [rows, columns]
```

Коды `flow_direction`:

```text
-1 = outlet / leaves domain
 0 = N
 1 = NE
 2 = E
 3 = SE
 4 = S
 5 = SW
 6 = W
 7 = NW
```

Соглашение grid остаётся каноническим: row 0 находится на севере, +column направлен на восток.

## Открытая граница

Каждая edge cell является outlet и имеет `flow_direction = -1`.

Граница domain не является водой или океаном. Она означает, что поток может покинуть моделируемый domain.

Priority-Flood использует каждую edge cell как seed с canonical terrain elevation.

## Conditioning Priority-Flood

Входной terrain преобразуется в float64 без изменения числовых значений.

Используется min-heap с порядком:

```text
(routing_elevation_m, row, column)
```

Все edge cells вставляются ровно один раз. Neighbors — 8-connected grid neighbors в каноническом порядке D8.

Когда непосещённый neighbor достигается из processed cell `current`:

```text
if terrain[neighbor] > routing[current]:
    routing[neighbor] = terrain[neighbor]
else:
    routing[neighbor] = nextafter(routing[current], +infinity)
```

Это минимальный представимый положительный gradient, а не произвольная epsilon-константа.

Следствия:

- depressions повышаются только в routing surface;
- заполненные flats получают детерминированный бесконечно малый drainage gradient к outlet;
- canonical terrain остаётся неизменным;
- `routing_elevation_m - terrain_elevation_m` сохраняет информацию о potential depression/fill для будущего extraction lakes.

RNG не используется.

## Routing D8

Каждая non-edge cell выбирает одного из 8 neighbors по routing elevation.

Канонический порядок neighbors и кодов:

```text
0 N  = (-1,  0)
1 NE = (-1, +1)
2 E  = ( 0, +1)
3 SE = (+1, +1)
4 S  = (+1,  0)
5 SW = (+1, -1)
6 W  = ( 0, -1)
7 NW = (-1, -1)
```

Для каждого neighbor со строго меньшей routing elevation:

```text
slope = (routing[current] - routing[neighbor]) / distance_km
```

где orthogonal distance равен `cell_size_km`, а diagonal distance — `cell_size_km * sqrt(2)`.

Выбирается максимальный положительный slope. Точное равенство разрешается в пользу более раннего направления из канонического списка выше.

Корректная conditioned interior cell обязана иметь хотя бы одного neighbor со строго меньшим значением. Нарушение является invariant/capability failure hydrology и никогда не вызывает RNG retry.

## Flow accumulation

Core v0.1 предполагает пространственно равномерный unit runoff только для учёта catchment area. Поэтому accumulation представляет площадь contributing area, а не discharge.

Каждая cell изначально вносит ровно:

```text
cell_area_km2 = cell_size_km²
```

Implementation аккумулирует **integer upstream cell counts** по графу receivers D8, затем один раз преобразует:

```text
flow_accumulation_km2 = upstream_cell_count * cell_area_km2
```

Это избегает floating-order drift и сохраняет физические единицы.

Cells обрабатываются в детерминированном порядке убывания routing elevation с tie-break по `(row, column)`. Поскольку каждый non-outlet receiver строго ниже, граф ацикличен.

## Граница runtime / canonical

`routing_elevation_m`, `flow_direction` и `flow_accumulation_km2` являются runtime/derived data hydrology в этом slice.

Они ещё не объявлены финальными canonical outputs rivers/lakes в `DomainData`.

Следующие slices hydrology используют их для получения:

```text
candidate depressions -> lakes / water_depth
catchment threshold -> stream graph -> vector RiverNetwork
```

## Validation

Validation hydrology v0.1 проверяет:

- существует upstream `TerrainState`;
- shape terrain совпадает с grid и значения конечны;
- существует `HydrologyState`;
- все arrays совпадают с shape grid;
- routing имеет dtype float64 и конечные значения;
- routing elevation никогда не ниже canonical terrain;
- `flow_direction` имеет dtype int8 и коды в `[-1,7]`;
- все edge cells являются outlets;
- каждая interior cell имеет допустимое direction receiver;
- каждый направленный receiver строго ниже по routing elevation;
- accumulation имеет dtype float64, конечна и не меньше площади одной cell везде.

Hydrology не использует RNG в этом slice.

## Что не входит

- хранение/выбор threshold streams;
- stream mask;
- water depth;
- lakes;
- vectorization rivers/topology network;
- coefficients precipitation/runoff;
- flow discharge;
- erosion;
- мутация terrain;
- routing D-infinity или multiple-flow-direction.
