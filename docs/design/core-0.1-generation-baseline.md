---
id: DESIGN-GENERATION-BASELINE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Generation baseline Core 0.1

Этот документ фиксирует принятые алгоритмические решения. Они ещё не реализованы.

## Layout

Structural features получают concrete macro geometry (`point`, `area`, `corridor`, `band`). Shape означает топологическую организацию, а не идеальную геометрическую фигуру.

Dependent features получают `PlacementReservation`, если их окончательное размещение зависит от terrain/hydrology/surface.

## Terrain

```text
BaseField
+ sum(StructuralTerrainContributions)
= StructuralElevation
-> ShapingOperators
-> CanonicalElevation
```

- additive features создают отдельные contributions;
- contributions суммируются независимо от порядка features;
- shaping operators работают отдельной фазой;
- geometry строится в world coordinates;
- masks выводятся из distance fields, falloff и coherent boundary noise;
- coherent/ridged noise добавляет естественную нерегулярность, но не определяет макрокомпозицию.

Generic operator examples: `ridge`, `raise`, `depress`, `flatten`.

## Hydrology

```text
canonical elevation
-> depression analysis
-> conditioned routing surface
-> flow direction
-> flow accumulation
-> stream extraction
-> river network + lakes
-> canonical water
```

- canonical elevation Core 0.1 гидрологией не изменяется;
- мелкие depression artifacts могут исправляться только в routing surface;
- крупные depressions анализируются как potential lakes;
- flow accumulation представляет сбор стока из upstream catchment;
- river thresholds должны по возможности выражаться в физических единицах, например km² catchment, а не в числе клеток;
- край домена является open boundary, а не автоматически морем;
- flow direction/accumulation — derived, river network/lakes/water — canonical result.

## Surface

```text
elevation + slope + hydrology
-> moisture
-> vegetation potential
+ explicit surface-feature bias
-> vegetation density
```

- moisture и vegetation density являются continuous fields;
- explicit forest-like features модифицируют поле, а не бинарно закрашивают клетки;
- terrain и surface presets разделяются;
- гибриды вроде `forested_hills` предпочтительно выражать как terrain feature + surface feature + constraint;
- полноценная климатическая/биомная модель не входит в Core 0.1.

## Dependent feature placement

Layout задаёт допустимую область, а post-physical stage выбирает финальную geometry по suitability. Если допустимого места нет, candidate отклоняется; terrain/validator не обязаны скрытно исправлять мир под POI.

## Validation

Validation выполняется по стадиям. Engine invariants и hard constraints обязательны. Soft constraints используются для ranking: сначала минимизируется худшее значимое нарушение, затем учитывается weighted mean. Validator не модифицирует candidate.