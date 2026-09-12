---
id: DESIGN-GENERATION-BASELINE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Базовая модель генерации Core 0.1

Этот документ фиксирует принятые алгоритмические решения. Они ещё не реализованы полностью.

## Layout

Structural features получают конкретную macro geometry (`point`, `area`, `corridor`, `band`). Shape означает топологическую организацию, а не идеальную геометрическую фигуру.

Dependent features получают materialized vector `PlacementReservation` (`RegionSet`), если их финальное placement зависит от terrain/hydrology/surface. Reservation строится только из hard spatial constraints относительно geometry, уже существующей на стадии layout.

Полная ширина band хранится как width profile по normalized parameter centerline `t in [0,1]`. Influence band может выходить за domain и обрезается при rasterization; centerline остаётся внутри или на boundary.

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
- geometry строится в мировых координатах;
- masks выводятся из distance fields, falloff и coherent boundary noise;
- coherent/ridged noise добавляет естественную нерегулярность, но не определяет макрокомпозицию.

Примеры универсальных operator-ов: `ridge`, `raise`, `depress`, `flatten`.

## Hydrology

```text
canonical elevation
-> анализ впадин
-> подготовленная поверхность routing
-> направление стока
-> накопление стока
-> извлечение streams
-> river network + lakes
-> canonical water_depth
```

- canonical elevation Core 0.1 гидрологией не изменяется;
- мелкие artifacts впадин могут исправляться только в routing surface;
- крупные depressions анализируются как потенциальные lakes;
- flow accumulation представляет upstream catchment;
- thresholds rivers по возможности выражаются в физических единицах, например km² catchment, а не в количестве cells;
- boundary domain открыта и не считается автоматически морем;
- flow direction/accumulation — derived data;
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

- `moisture` и `vegetation_density` — непрерывные canonical fields;
- явные forest-like features модифицируют field, а не бинарно закрашивают cells;
- terrain и surface presets разделяются;
- гибриды вроде `forested_hills` выражаются как terrain feature + surface feature + constraint;
- полноценная climate/biome model не входит в Core 0.1.

## Размещение dependent features / пригодность места для POI

```text
PlacementReservation
-> hard requirements SiteProfile
-> valid sites
-> intrinsic preferences SiteProfile
-> near-best set
-> deterministic weighted selection
-> final geometry
```

- глобальные hard spatial constraints формируют reservation;
- внутренние requirements preset фильтруют физически недопустимые sites;
- site metrics оценивают footprint вокруг точки, а не только одну cell;
- внутренние preferences определяют suitability места внутри одного candidate;
- Core 0.1 не обязан выбирать абсолютный argmax: deterministic weighted choice выполняется среди near-best sites;
- пользовательские soft constraints не смешиваются с внутренним site score: они оценивают уже получившийся candidate для глобального ranking;
- если допустимых sites нет, attempt отклоняется;
- Core 0.1 реализует dependent placement прежде всего для point features.

## Модель attempt

Один `attempt_index` означает одну независимую realization неизменяемого `GenerationPlan`.

- скрытые локальные retries внутри стадий запрещены;
- stochastic stages используют независимые RNG streams конкретного attempt;
- deterministic stages не обязаны получать RNG;
- ранняя validation может остановить attempt;
- поздний hard failure отклоняет весь attempt;
- attempts не обучаются на предыдущих failures;
- бюджет исполнения задаётся semantic `GenerationConfig`;
- `target_valid_candidates=1` означает поведение «первый валидный»; большее значение собирает несколько валидных candidates для ranking.

## Базовая модель RNG

Дочерний RNG stream адресуется versioned semantic key:

```text
root seed + attempt + stage + scope + purpose
```

и выводится через стабильный cryptographic derivation. Глобального mutable RNG и Python `hash()` как persistence contract нет. Identity feature и scopes parameter/purpose стабильны; имена module/function в namespace не входят.

## Validation и ranking

Validation выполняется по стадиям. Engine invariants и hard constraints обязательны. Soft scores нормализуются в `[0,1]`; `0 < weight <= 1`.

```text
effective_violation = (1 - score) * weight
```

Валидные candidates ранжируются: минимальный `worst_effective_violation`, затем максимальный `weighted_mean_score`, затем меньший `attempt_index`. При отсутствии soft constraints используются neutral values `0.0` и `1.0`. Validator не модифицирует candidate.

## Причинность между стадиями

Стадии образуют upstream-only DAG и не мутируют предыдущие outputs. Если поздний object должен формировать ранний слой мира, это выражается отдельным feature/constraint соответствующей стадии, а не скрытым side effect.
