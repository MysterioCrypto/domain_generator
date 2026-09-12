---
id: DESIGN-DEPENDENT-PLACEMENT-CANDIDATE-FILTERING-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Фильтрация candidates для dependent placement v0.1

Этот checkpoint реализует первую половину runtime dependent placement после materialized `PlacementReservation` и Site Metrics v0.1.

В область действия входят:

```text
PlacementReservation
+ recipe feature dependent-placement
+ TerrainState
+ HydrologyState
+ SurfaceState
-> deterministic world-space candidate lattice
-> reservation containment
-> canonical candidate order
-> site metrics
-> hard requirements SiteProfile
-> valid sites
```

Scoring preferences, фильтрация near-best, финальный weighted selection и `PlacementState.final_points` не входят в этот checkpoint.

## Шаг сетки candidates

Operator dependent-placement обязан иметь resolved semantic parameter:

```text
candidate_spacing_km
```

Он должен разрешаться в конечный float `> 0`.

Sampling использует стандартный namespace parameter:

```text
stage   = placement
scope   = ("feature", feature_id, "parameter", "candidate_spacing_km")
purpose = "sample"
```

Параметр не выводится из размера raster cell и не является скрытой константой.

## Повернутая квадратная lattice

Для feature `<id>` используются два независимых streams:

```text
stage = placement
scope = ("feature", id, "site-candidates")
purpose = "rotation"

stage = placement
scope = ("feature", id, "site-candidates")
purpose = "phase"
```

Пусть `s = candidate_spacing_km`.

Stream rotation делает один draw:

```text
theta = uniform01 * (pi / 2)
```

Периода `pi/2` достаточно для square lattice: повороты на 90 градусов задают ту же решётку.

Stream phase делает ровно два draw:

```text
phase_u = uniform01 * s
phase_v = uniform01 * s
```

В повернутых координатах points lattice:

```text
u = phase_u + i*s
v = phase_v + j*s
```

Мировые координаты:

```text
x = cos(theta)*u - sin(theta)*v
y = sin(theta)*u + cos(theta)*v
```

`i` и `j` — все integers, необходимые для покрытия axis-aligned rectangle domain. Для конечного enumeration углы domain переводятся обратным rotation в `(u,v)`, после чего диапазоны integers вычисляются через `ceil`/`floor`.

Retries, jitter, clamping, snapping или adaptive density отсутствуют.

## Фильтрация по domain и reservation

После enumeration lattice остаются только точки, удовлетворяющие:

```text
0 <= x <= domain.width_km
0 <= y <= domain.height_km
```

Затем candidate должен лежать внутри или на:

```text
PlacementReservation.allowed_region
```

Containment использует polygonal semantics `covers`: outer boundary разрешена, boundary hole не считается interior hole и также покрывается boundary semantics backend-а.

Пустой reservation даёт пустое множество candidates.

Core не создаёт fallback point и не ослабляет reservation.

## Канонический порядок

После filtering points candidates сортируются по точным runtime doubles:

```text
(x_km, y_km)
```

Duplicates удаляются по точной паре `(x_km, y_km)` до сортировки.

Порядок iteration при enumeration lattice не является семантическим.

## Оценка candidate

Каждый оставшийся candidate оценивается через `Dependent Placement Site Metrics v0.1` с:

```text
feature.effect.site_profile.footprint_radius_km
```

`SiteMetricContext` уровня attempt создаётся один раз и переиспользуется всеми candidates.

## Hard requirements

Core 0.1 поддерживает только:

```text
less_or_equal
greater_or_equal
```

Requirement:

```text
metric evaluator value
```

применяется к registry metrics Site Metrics v0.1.

Неизвестный id metric или evaluator — явный placement capability error.

Семантика:

```text
less_or_equal:    metric <= value
greater_or_equal: metric >= value
```

IEEE `+inf` для `distance_to_water` сохраняет обычные comparisons. Поэтому при domain без воды:

```text
+inf <= finite -> false
+inf >= finite -> true
```

Candidate валиден только если проходят все requirements.

Если requirements отсутствуют, все оставшиеся candidates валидны.

## Пустое множество валидных sites

Пустое множество valid sites является семантической ошибкой placement, а не capability error и не вызывает скрытый retry.

В этом checkpoint runtime helper возвращает пустой tuple. Последующая полная стадия placement переводит это состояние в отклонение attempt.

## Runtime representation

Только runtime:

```text
EvaluatedSite
  point: PointGeometry
  metrics: dict[str, float]
```

Он не является сериализуемым контрактом Core и не попадает в `DomainData`.

## Что не входит в этот checkpoint

- scoring preferences;
- maximize/minimize/preferred_range;
- composite suitability;
- фильтрация near-best;
- финальный weighted choice;
- `PlacementState`;
- adaptive lattice spacing;
- Poisson-disc/blue-noise placement;
- взаимозависимые deferred POI;
- deferred geometry, отличная от point;
- генерация candidates по центрам raster cells.
