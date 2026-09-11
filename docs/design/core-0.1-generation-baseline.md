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

Dependent features получают materialized vector `PlacementReservation` (`RegionSet`), если их final placement зависит от terrain/hydrology/surface. Reservation строится только из hard spatial constraints относительно geometry, уже существующей на layout stage.

Band full width хранится как width profile по normalized centerline parameter `t in [0,1]`. Band influence может выходить за domain и клиппится при rasterization; centerline остаётся inside/on boundary.

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
-> canonical water_depth
```

- canonical elevation Core 0.1 гидрологией не изменяется;
- мелкие depression artifacts могут исправляться только в routing surface;
- крупные depressions анализируются как potential lakes;
- flow accumulation представляет upstream catchment;
- river thresholds выражаются по возможности в physical units (например km² catchment), а не cell counts;
- domain edge — open boundary, не автоматически море;
- flow direction/accumulation — derived;
- river network/lakes/`water_depth` — canonical result;
- binary water mask — derived view `water_depth > 0`.

## Surface

```text
elevation + slope + hydrology
-> moisture
-> vegetation potential
+ explicit surface-feature bias
-> vegetation_density
```

- `moisture` и `vegetation_density` — continuous canonical fields;
- explicit forest-like features модифицируют field, а не бинарно закрашивают cells;
- terrain и surface presets разделяются;
- гибриды вроде `forested_hills` выражаются как terrain feature + surface feature + constraint;
- полноценная climate/biome model не входит в Core 0.1.

## Dependent feature placement / POI suitability

```text
PlacementReservation
-> hard SiteProfile requirements
-> valid sites
-> intrinsic SiteProfile preferences
-> near-best set
-> deterministic weighted selection
-> final geometry
```

- global hard spatial constraints формируют reservation;
- intrinsic preset requirements фильтруют physically invalid sites;
- site metrics оценивают footprint вокруг точки, а не только одну cell;
- intrinsic preferences определяют site suitability внутри одного candidate;
- Core 0.1 не обязан выбирать абсолютный argmax: deterministic weighted choice выполняется среди near-best sites;
- user soft constraints не смешиваются с intrinsic site score: они оценивают уже получившийся candidate для global ranking;
- если valid sites нет, attempt отклоняется;
- Core 0.1 реализует dependent placement прежде всего для point features.

## Attempt model

Один `attempt_index` означает одну независимую realization immutable `GenerationPlan`.

- hidden stage-local retries запрещены;
- stochastic stages используют attempt-specific independent RNG streams;
- deterministic stages не обязаны получать RNG;
- early validation может остановить attempt;
- late hard failure отклоняет весь attempt;
- attempts не обучаются на предыдущих failures;
- execution budget задаётся semantic `GenerationConfig`;
- `target_valid_candidates=1` означает first-valid behavior; большее значение собирает несколько valid candidates для ranking.

## RNG baseline

Child RNG stream адресуется versioned semantic key:

```text
root seed + attempt + stage + scope + purpose
```

и выводится stable cryptographic derivation. Никакого global mutable RNG и Python `hash()` как persistence contract. Feature identity и parameter/purpose scopes стабильны; module/function names в namespace не входят.

## Validation и ranking

Validation выполняется по стадиям. Engine invariants и hard constraints обязательны. Soft scores нормализуются в `[0,1]`; `0 < weight <= 1`.

```text
effective_violation = (1 - score) * weight
```

Valid candidates ранжируются: минимальный worst effective violation, затем максимальный weighted mean score, затем меньший `attempt_index`. При отсутствии soft constraints используются neutral values `0.0` и `1.0`. Validator не модифицирует candidate.

## Stage causality

Stages образуют upstream-only DAG и не мутируют предыдущие outputs. Если поздний object должен формировать ранний слой мира, это выражается отдельным feature/constraint соответствующей стадии, а не hidden side effect.
