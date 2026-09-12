---
id: DESIGN-TERRAIN-AREA-RAISE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Базовый Terrain / Area Raise v0.1

Этот документ фиксирует первый численный вертикальный slice terrain Core 0.1.

## Область действия

Slice materialize-ит canonical raster elevation из уже существующего `LayoutCandidate`.

Поддерживается только terrain feature с:

- конкретной `AreaGeometry`;
- effect stage `terrain`;
- operator `raise`;
- единственным effect parameter `height_m`.

Не входят: ridge, depress, flatten, blend, noise, terrain effects point/corridor/band, slope, hydrology, surface и placement.

## TerrainState

Runtime state, а не serialized contract:

```text
TerrainState
  elevation_m: numpy.ndarray
```

`elevation_m`:

- shape `(plan.grid.rows, plan.grid.columns)`;
- canonical dtype `float32`;
- unit = meter;
- только конечные values.

Поздний assembler `DomainData` сохраняет это поле как canonical elevation field.

## Mapping grid/world

Мировая система координат остаётся:

- начало на юго-западе;
- +x на восток;
- +y на север.

Raster:

- row 0 = north;
- column 0 = west.

Center cell `(row, column)`:

```text
x_km = (column + 0.5) * cell_size_km
y_km = domain.height_km - (row + 0.5) * cell_size_km
```

Преобразование world/raster должно находиться в единственном grid adapter. Operators terrain не изобретают собственную convention.

## Базовое поле

Базовая модель terrain Core 0.1 этого slice:

```text
BaseField = 0.0 m everywhere
```

Нулевая elevation — datum, а не семантика water/sea. Water определяется только будущей стадией hydrology.

## Rasterization Area

`AreaGeometry` rasterize-ится по **включению center cell**.

Cell считается внутри feature, если center находится внутри polygon или на его boundary по принятой semantics point containment area.

Polygon area не мутируется и не snap-ится к grid.

## Operator raise

Обязательный effect parameter:

```text
height_m
```

Parameter должен иметь numeric float recipe и при sampling разрешаться в конечное `height_m > 0`.

Для каждой cell:

```text
inside/on AreaGeometry -> contribution = height_m
outside                 -> contribution = 0.0
```

`raise` является additive structural operator. Отрицательные или нулевые значения не переинтерпретируются как `depress`/no-op.

## RNG effect parameter

Resolved effect parameters sample-ятся для конкретного attempt через RNG v1:

```text
stage = terrain
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

RNG namespaces layout не меняются.

## Аддитивное накопление

Каждый поддерживаемый terrain feature концептуально создаёт отдельный float64 contribution.

Structural elevation:

```text
float64 BaseField
+ contributions in sorted(feature.id) order
= float64 StructuralElevation
```

Порядок features во входе не является семантическим.

В этом slice shaping phase отсутствует, поэтому:

```text
CanonicalElevation = StructuralElevation.astype(float32)
```

Финальный cast в float32 выполняется ровно один раз после всех additive contributions.

## Поведение при неподдерживаемых конструкциях

Stage terrain выдаёт явный capability error, если для terrain feature:

- layout geometry не materialized;
- geometry не `AreaGeometry`;
- effect stage не `terrain`;
- operator не `raise`;
- набор parameters отличается от ровно `{height_m}`;
- `height_m` имеет неподдерживаемый type/sampler/result.

Ни один terrain feature нельзя молча игнорировать.

Features не из family terrain не являются работой terrain stage и пропускаются.

## Validation Terrain

`ValidationResult(stage=terrain)` содержит engine invariants:

- upstream layout существует;
- `attempt_index` layout равен текущему attempt;
- `TerrainState` существует;
- shape elevation равен `(rows, columns)`;
- dtype elevation ровно `float32`;
- все values elevation конечны;
- множество поддерживаемых terrain features применено полностью и каждый feature ровно один раз.

Hard constraints terrain в этом slice отсутствуют. Поэтому `HardConstraintGroup` всегда пуст и по контракту имеет `passed=true`; итоговая валидность terrain stage определяется engine invariants.

Проверка полного применения features использует runtime trace IDs, собранный тем же stage handler; standalone validator не должен молча подменять этот trace ожидаемым множеством features.

Validation не модифицирует state.

## Причинность стадий

```text
GenerationPlan + LayoutCandidate
        ↓
terrain_stage
        ↓
TerrainState
```

Terrain stage читает layout и plan, записывает только `CandidateState.terrain` и не мутирует layout.

## Детерминированность

Результат определяется:

- plan/grid/domain;
- конкретной area geometry layout;
- attempt index;
- root seed + RNG namespace parameters terrain;
- отсортированными id terrain features;
- фиксированным соглашением о centers raster cells;
- accumulation float64 с одним финальным cast в float32.

Observability/debug paths не участвуют в численных вычислениях.
