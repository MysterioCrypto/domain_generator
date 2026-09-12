---
id: DESIGN-TERRAIN-STRUCTURAL-FLATTEN-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Завершение structural terrain + Flatten v0.1

Этот документ фиксирует завершение первой structural phase terrain и первый shaping operator Core 0.1.

## Семантика pipeline

Terrain теперь имеет две явные фазы:

```text
BaseField = 0 m
  + additive structural contributions
  = StructuralElevation (float64)
  -> shaping operators reading one frozen StructuralElevation snapshot
  = CanonicalElevation
  -> one final float32 cast
  = TerrainState.elevation_m
```

Structural phase в этом checkpoint поддерживает:

- `AreaGeometry + raise(height_m)`;
- `AreaGeometry + depress(depth_m)`;
- `BandGeometry + ridge(...)`.

Shaping phase поддерживает:

- `AreaGeometry + flatten(target_elevation_m, blend_width_km)`.

Отдельный универсальный operator `blend` в v0.1 не вводится.

## Structural `depress`

`depress` является additive structural operator и симметричен `raise`.

Точный обязательный набор effect parameters:

```text
depth_m
```

`depth_m` должен быть float resolved parameter и после sampling обязан быть конечным `> 0`.

Contribution:

```text
inside/on AreaGeometry -> -depth_m
outside                -> 0.0
```

Rasterization использует ту же canonical semantics включения center cell, что `raise`.

`depress` не означает water/lake. Он изменяет только terrain elevation; hydrology позднее сама интерпретирует depressions.

## Structural accumulation

Все structural features применяются в детерминированном порядке отсортированных `feature.id`:

```text
StructuralElevation = BaseField
                    + raise contributions
                    + depress contributions
                    + ridge contributions
```

Каждый contribution вычисляется в float64. Порядок features во входе не является семантическим.

После structural accumulation создаётся frozen float64 snapshot. Shaping operators не читают результаты друг друга.

## Область действия `flatten`

`flatten` в Core 0.1 поддерживается только с concrete `AreaGeometry`.

Точный обязательный набор effect parameters:

```text
target_elevation_m
blend_width_km
```

После sampling:

- `target_elevation_m` — любой конечный float, unit meters; отрицательная absolute elevation допустима;
- `blend_width_km` — конечный float `>= 0`.

`target_elevation_m` — абсолютная финальная высота, а не contribution.

## Influence flatten и blend

Flatten не влияет на cells, center которых находится вне `AreaGeometry`.

Для center внутри или на polygon определяется Euclidean distance `d` до outer polygon boundary.

Если:

```text
blend_width_km = 0
```

то для любой interior cell используется:

```text
w = 1
```

Boundary имеет measure zero; если center численно лежит ровно на boundary, `w=0`, чтобы внешний рельеф непрерывно оставался нетронутым на границе shaping region.

Если:

```text
blend_width_km > 0
```

то:

```text
w = clamp(d / blend_width_km, 0, 1)
```

Следовательно:

- на boundary `w=0`;
- на расстоянии `blend_width_km` и глубже внутрь Area `w=1`;
- transition происходит только **внутрь** Area;
- вне Area всегда `w=0`.

Финальная shaped elevation для cell:

```text
result = StructuralElevation * (1-w) + target_elevation_m * w
```

Shaping computation выполняется в float64.

## Frozen structural snapshot

Каждый `flatten` читает один и тот же неизменяемый snapshot `StructuralElevation`.

Запрещена последовательная семантика вида:

```text
flatten A -> flatten B reads A -> flatten C reads B
```

Для совместимых shaping regions результат не зависит от порядка features во входе.

## Conflict overlap shaping

В Core 0.1 два features `flatten` не могут иметь пересечение interior областей положительной площади.

Концептуально:

```text
interior(flatten A) ∩ interior(flatten B) has positive area
-> shaping conflict
-> terrain validation fails
-> whole attempt rejected
```

Точное касание boundaries polygons разрешено, поскольку на boundary `w=0` и ни один operator фактически не изменяет elevation там.

Detection conflict выполняется в world-vector geometry, а не по raster cells, чтобы результат не зависел от `cell_size_km`.

Overlap shaping — геометрическая несовместимость уровня attempt, а не `TerrainCapabilityError`. Скрытого reroll или automatic priority нет.

При обнаруженном conflict implementation может оставить runtime terrain state как детерминированный structural snapshot для диагностики, но `ValidationResult` terrain обязан отклонить attempt, и downstream semantic stages не должны использовать этот invalid state.

## Порядок обработки features

Terrain features сначала разделяются по semantics operator-а:

Structural:

```text
raise
depress
ridge
```

Shaping:

```text
flatten
```

Внутри structural group обработка выполняется детерминированно по отсортированному feature id.

Shaping geometries/parameters также resolve-ятся детерминированно по sorted feature id; conflict-check выполняется до финальной shaping composition.

## RNG parameters

Все effect parameters используют существующий namespace parameters terrain:

```text
stage = terrain
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

`flatten` не использует дополнительный geometry/noise RNG.

## Поведение при неподдерживаемых конструкциях

Явный `TerrainCapabilityError`, если:

- `depress`/`flatten` используется не с `AreaGeometry`;
- набор effect parameters не совпадает с required set;
- recipe parameter не float или sampler unsupported;
- sampled parameter non-finite;
- `depth_m <= 0`;
- `blend_width_km < 0`.

Overlap двух валидных regions flatten — validation failure, а не capability error.

## Дополнения validation

Validation terrain дополнительно содержит engine invariant:

```text
terrain-shaping-regions-compatible
```

Он имеет `passed=true` только если список shaping conflicts пуст.

Остальные существующие invariants — причинность layout, shape, dtype, finite, полная обработка features — сохраняются.

## Что не входит

- самостоятельный operator `blend`;
- priority/order пересекающихся shaping;
- flatten для band/corridor/point;
- target elevation, выводимая из neighborhood;
- slope-aware или erosion-aware smoothing;
- hydrology;
- автоматическое создание lake;
- расширение shaping region за пределы `AreaGeometry`.
