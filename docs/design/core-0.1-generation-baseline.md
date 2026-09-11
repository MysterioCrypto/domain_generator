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

- moisture и vegetation density являются continuous semantic fields;
- explicit forest-like features модифицируют поле, а не бинарно закрашивают клетки;
- terrain и surface presets разделяются;
- гибриды вроде `forested_hills` предпочтительно выражать как terrain feature + surface feature + constraint;
- полноценная климатическая/биомная модель не входит в Core 0.1.

## Dependent feature placement / POI suitability

```text
PlacementReservation
-> hard site requirements
-> valid sites
-> intrinsic preferences + soft spatial constraints
-> suitability scores
-> near-best set
-> deterministic weighted selection
-> final geometry
```

- global hard spatial constraints формируют/сужают reservation;
- intrinsic preset requirements (например water fraction, buildable fraction) фильтруют sites;
- site metrics могут оценивать footprint вокруг точки, а не одну cell;
- intrinsic preferences и soft constraints дают score;
- Core 0.1 не обязан всегда выбирать абсолютный argmax: выбор выполняется детерминированно среди near-best sites с preference к более высоким scores;
- если valid sites нет, attempt отклоняется;
- Core 0.1 реализует dependent placement прежде всего для point features.

## Attempt model

Один `attempt_index` означает одну независимую realization одного immutable `GenerationPlan`.

- hidden stage-local retries запрещены;
- stochastic stages используют attempt-specific independent RNG streams;
- deterministic stages не обязаны получать RNG;
- early validation может остановить attempt до downstream stages;
- late hard failure отклоняет весь attempt;
- attempts не обучаются на предыдущих failures;
- несколько valid candidates могут быть сгенерированы для ranking;
- execution budget задаётся `GenerationConfig`, не `DomainSpec`.

## RNG baseline

Child RNG stream адресуется versioned semantic key:

```text
root seed + attempt + stage + scope + purpose
```

и выводится stable cryptographic derivation. Никакого global mutable RNG и Python `hash()` как persistence contract. Feature identity и parameter/purpose scopes стабильны; module/function names в namespace не входят.

## Validation

Validation выполняется по стадиям. Engine invariants и hard constraints обязательны. Soft constraints используются для ranking: сначала минимизируется худшее значимое weighted violation, затем учитывается weighted mean. Validator не модифицирует candidate.

## Stage causality

Stages образуют upstream-only DAG и не мутируют предыдущие outputs. Если поздний object должен формировать ранний слой мира, это выражается отдельным feature/constraint соответствующей стадии, а не скрытым side effect.
