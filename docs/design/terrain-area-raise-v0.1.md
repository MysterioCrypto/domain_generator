---
id: DESIGN-TERRAIN-AREA-RAISE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
---

# Terrain Baseline / Area Raise v0.1

Этот документ фиксирует первый числовой terrain vertical slice Core 0.1.

## Scope

Slice материализует canonical elevation raster из уже существующего `LayoutCandidate`.

Поддерживается только terrain feature с:

- concrete `AreaGeometry`;
- effect stage `terrain`;
- operator `raise`;
- единственным effect parameter `height_m`.

Не входят: ridge, depress, flatten, blend, noise, point/corridor/band terrain effects, slope, hydrology, surface и placement.

## TerrainState

Runtime state, не serialized contract:

```text
TerrainState
  elevation_m: numpy.ndarray
```

`elevation_m`:

- shape `(plan.grid.rows, plan.grid.columns)`;
- canonical dtype `float32`;
- unit = meter;
- finite values only.

Поздний DomainData assembler сохраняет это поле как canonical elevation field.

## Grid/world mapping

World coordinate system остаётся:

- origin southwest;
- +x east;
- +y north.

Raster:

- row 0 = north;
- column 0 = west.

Cell center `(row, column)`:

```text
x_km = (column + 0.5) * cell_size_km
y_km = domain.height_km - (row + 0.5) * cell_size_km
```

World/raster conversion должен находиться в единственном grid adapter. Terrain operators не изобретают собственную convention.

## Base field

Core 0.1 terrain baseline этого slice:

```text
BaseField = 0.0 m everywhere
```

Нулевая elevation — datum, а не water/sea semantic. Water определяется только будущей hydrology stage.

## Area rasterization

`AreaGeometry` rasterize-ится по **cell-center inclusion**.

Cell считается внутри feature, если center находится внутри polygon или на его boundary по принятой area point-containment semantics.

Area polygon не мутируется и не snap-ится к grid.

## raise operator

Required effect parameter:

```text
height_m
```

Parameter должен иметь numeric float recipe и при sampling разрешаться в finite `height_m > 0`.

Для каждого cell:

```text
inside/on AreaGeometry -> contribution = height_m
outside                 -> contribution = 0.0
```

`raise` является additive structural operator. Отрицательные/нулевые значения не переинтерпретируются как `depress`/no-op.

## Effect-parameter RNG

Resolved effect parameters sample-ятся attempt-locally через RNG v1:

```text
stage = terrain
scope = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Layout RNG namespaces не меняются.

## Additive accumulation

Каждый supported terrain feature концептуально создаёт отдельный float64 contribution.

Structural elevation:

```text
float64 BaseField
+ contributions in sorted(feature.id) order
= float64 StructuralElevation
```

Feature input order не является semantic.

В этом slice shaping phase отсутствует, поэтому:

```text
CanonicalElevation = StructuralElevation.astype(float32)
```

Final cast в float32 выполняется ровно один раз после всех additive contributions.

## Capability behavior

Terrain stage обрабатывает только features с `family=terrain`.

Для terrain feature explicit capability error, если:

- layout geometry не materialized;
- geometry не `AreaGeometry`;
- effect stage не `terrain`;
- operator не `raise`;
- parameter set отличается от ровно `{height_m}`;
- `height_m` имеет неподдерживаемый type/sampler/result.

Ни один terrain feature нельзя silently ignore.

Non-terrain features не являются terrain-stage work и пропускаются.

## Terrain validation

Terrain `ValidationResult(stage=terrain)` содержит engine invariants:

- upstream layout существует;
- layout `attempt_index` равен текущему attempt;
- TerrainState существует;
- elevation shape равна `(rows, columns)`;
- elevation dtype ровно `float32`;
- все elevation values finite;
- supported terrain feature set применён полностью и каждый feature ровно один раз.

Terrain hard constraints в этом slice отсутствуют. Поэтому `HardConstraintGroup` всегда пуст и по контракту имеет `passed=true`; итоговая валидность terrain stage определяется engine invariants.

Проверка complete feature application использует runtime trace IDs, собранный тем же stage handler; standalone validator не должен молча подменять этот trace ожидаемым feature set.

Validation не модифицирует state.

## Stage causality

```text
GenerationPlan + LayoutCandidate
        ↓
terrain_stage
        ↓
TerrainState
```

Terrain stage читает layout и plan, записывает только `CandidateState.terrain` и не мутирует layout.

## Determinism

Результат определяется:

- plan/grid/domain;
- concrete layout area geometry;
- attempt index;
- root seed + terrain parameter RNG namespace;
- sorted terrain feature ids;
- fixed raster center convention;
- float64 accumulation followed by one float32 cast.

Observability/debug paths не участвуют в numeric computation.
