---
id: DESIGN-TERRAIN-STRUCTURAL-FLATTEN-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Terrain Structural Completion + Flatten v0.1

Этот документ фиксирует завершение первой structural terrain phase и первый shaping operator Core 0.1.

## Pipeline semantics

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

Отдельный generic `blend` operator в v0.1 не вводится.

## Structural `depress`

`depress` является additive structural operator и симметричен `raise`.

Required effect parameters ровно:

```text
depth_m
```

`depth_m` должен быть float resolved parameter и после sampling обязан быть finite `> 0`.

Contribution:

```text
inside/on AreaGeometry -> -depth_m
outside                -> 0.0
```

Rasterization использует ту же canonical cell-center inclusion semantics, что `raise`.

`depress` не означает water/lake. Он изменяет только terrain elevation; hydrology позднее сама интерпретирует depressions.

## Structural accumulation

Все structural features применяются в deterministic sorted `feature.id` order:

```text
StructuralElevation = BaseField
                    + raise contributions
                    + depress contributions
                    + ridge contributions
```

Каждый contribution вычисляется в float64. Feature input order не semantic.

После structural accumulation создаётся frozen float64 snapshot. Shaping operators не читают результаты друг друга.

## `flatten` scope

`flatten` в Core 0.1 поддерживается только с concrete `AreaGeometry`.

Required effect parameters ровно:

```text
target_elevation_m
blend_width_km
```

После sampling:

- `target_elevation_m` — любой finite float, unit meters; отрицательная абсолютная elevation допустима;
- `blend_width_km` — finite float `>= 0`.

`target_elevation_m` — абсолютная финальная высота, а не contribution.

## Flatten influence and blend

Flatten не влияет на cells, center которых находится вне AreaGeometry.

Для center внутри/on polygon определяется Euclidean distance `d` до outer polygon boundary.

Если:

```text
blend_width_km = 0
```

то для любого interior cell используется:

```text
w = 1
```

Boundary имеет measure zero; если center numerically лежит ровно на boundary, `w=0`, чтобы внешний рельеф непрерывно оставался нетронутым на границе shaping region.

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
- outside Area всегда `w=0`.

Final shaped elevation для cell:

```text
result = StructuralElevation * (1-w) + target_elevation_m * w
```

Shaping computation выполняется в float64.

## Frozen structural snapshot

Каждый `flatten` читает один и тот же immutable StructuralElevation snapshot.

Запрещён sequential semantics вида:

```text
flatten A -> flatten B reads A -> flatten C reads B
```

Для совместимых shaping regions результат не зависит от feature input order.

## Shaping overlap conflict

В Core 0.1 два `flatten` features не могут иметь пересечение interior областей положительной площади.

Conceptually:

```text
interior(flatten A) ∩ interior(flatten B) has positive area
-> shaping conflict
-> terrain validation fails
-> whole attempt rejected
```

Точное касание polygon boundaries разрешено, поскольку на boundary `w=0` и ни один operator фактически не изменяет elevation там.

Conflict detection выполняется в world-vector geometry, а не по raster cells, чтобы результат не зависел от `cell_size_km`.

Shaping overlap — attempt-level geometric incompatibility, а не `TerrainCapabilityError`. Никакого hidden reroll или automatic priority нет.

При обнаруженном conflict implementation может оставить runtime terrain state как deterministic structural snapshot для диагностики, но terrain ValidationResult обязан отвергнуть attempt, и downstream semantic stages не должны использовать этот invalid state.

## Feature processing order

Terrain features сначала partition-ятся по operator semantics:

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

Внутри structural group processing deterministic by sorted feature id.

Shaping geometries/parameters также resolve-ятся deterministic by sorted feature id, conflict-check выполняется до final shaping composition.

## Parameter RNG

Все effect parameters используют существующий terrain parameter namespace:

```text
stage = terrain
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

`flatten` не использует дополнительный geometry/noise RNG.

## Capability behavior

Explicit `TerrainCapabilityError`, если:

- `depress`/`flatten` используется не с `AreaGeometry`;
- effect parameter set не совпадает с required set;
- parameter recipe не float или sampler unsupported;
- sampled parameter non-finite;
- `depth_m <= 0`;
- `blend_width_km < 0`.

Overlap двух valid flatten regions — validation failure, не capability error.

## Validation additions

Terrain validation дополнительно содержит engine invariant:

```text
terrain-shaping-regions-compatible
```

Он passed только если shaping conflict list пуст.

Остальные существующие invariants (layout causality, shape, dtype, finite, complete feature processing) сохраняются.

## Non-goals

Не входят:

- standalone `blend` operator;
- overlapping shaping priority/order;
- flatten для band/corridor/point;
- target elevation inferred from neighborhood;
- slope-aware or erosion-aware smoothing;
- hydrology;
- automatic lake creation;
- shaping region expansion outside AreaGeometry.
