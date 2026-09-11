---
id: ARCH-CORE-0.1
kind: architecture
status: active
normative: true
target: core-0.1
---

# Архитектура Core 0.1

## Главный поток

```text
Human / client
    -> DomainSpec
    -> structural validation + preset resolution
    -> Constraint Compiler
    -> GenerationPlan
    -> repeated deterministic attempts
         -> LayoutGenerator
         -> LayoutCandidate
         -> Terrain
         -> Hydrology
         -> Surface
         -> dependent feature placement
         -> staged validation / ranking
    -> best valid DomainCandidate
    -> DomainData assembly
    -> Renderers / exporters
```

`DomainSpec` — язык намерения пользователя. `GenerationPlan` — immutable serializable resolved recipe. `LayoutCandidate` — concrete macro-layout одной попытки. `DomainCandidate` — runtime candidate, дошедший до соответствующей стадии. `DomainData` — принятый мир.

## Координаты и grid

World-space соглашение:

- origin: southwest;
- `+x`: east;
- `+y`: north;
- geometry units: km.

`DomainSpec` задаёт physical size и `cell_size_km`. Raster indices (`row`, `column`) являются внутренней деталью `Grid`; geometry и user constraints ими не оперируют. `row 0` соответствует северной строке raster. Grid dimensions выводятся без silent rounding.

## Feature identity

Top-level `DomainSpec.id` — document/domain identity и не участвует в RNG.

Feature `id` — стабильная machine identity, используемая references и RNG namespace. Косметическое имя находится в optional `label`. Смена `label` не должна reroll'ить feature; сознательная смена feature `id` может изменить realization.

## Представление мира

Core использует три семейства данных:

- **Fields** — elevation, water, moisture, vegetation density и другие spatial values;
- **Networks** — river network и будущие связные структуры;
- **Features** — semantic spatial objects.

Spatial primitives описывают топологическую организацию, а не идеальные фигуры: `point`, `area`, `corridor`, `band` могут иметь органическую procedural geometry.

## Feature / preset / operator

Пользовательский `FeatureSpec` содержит stable `id`, optional `label`, `preset`, optional parameter overrides и tags. `family`, `shape`, `operator`, sampler и lifecycle следуют из preset и появляются после resolution.

Preset — validated data, а не embedded scripting. Он задаёт defaults, parameter schema, sampling policy, site profile и generic operator id. Один preset Core 0.1 использует один operator. Tags — metadata only.

## Parameters

DomainSpec задаёт fixed value либо allowed numeric/enum domain. `min/max` не означает автоматически uniform random. Sampling policy принадлежит preset definition и переносится в `GenerationPlan`. Concrete value выбирается только при realization соответствующей стадии.

## Constraints

User constraint:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Selectors могут ссылаться на feature/part, built-in domain anchor/region или literal point/region. Semantic relations компилируются в generic measurements/evaluators и hard predicate либо soft scoring recipe.

`hard` constraint нельзя компенсировать score. `soft` участвует в ranking с weight.

## Structural и dependent features

Structural features получают concrete macro geometry в `LayoutCandidate`.

Features, зависящие от physical geography, получают на layout-stage `PlacementReservation`; окончательная geometry выбирается позже. Core 0.1 реализует dependent placement прежде всего для `point` features, сохраняя архитектурную возможность других geometry types в будущем.

### POI suitability

```text
PlacementReservation
-> hard site requirements
-> valid sites
-> intrinsic preferences + soft spatial constraints
-> suitability field
-> near-best candidate set
-> deterministic weighted choice
-> final point geometry
```

Site metrics оценивают footprint/окружение, а не только одну raster cell. Если valid sites нет, весь attempt отклоняется; placement не заставляет terrain/hydrology тайно меняться.

## Terrain baseline

```text
BaseField
+ sum(StructuralTerrainContributions)
= StructuralElevation
-> ShapingOperators
-> CanonicalElevation
```

Additive operators создают отдельные contributions; feature order не должен менять additive result. Shaping operators выполняются отдельной фазой. Geometry определяет where, operator/noise parameters — how.

## Hydrology baseline

Canonical elevation Core 0.1 гидрологией не мутируется.

```text
elevation
-> depression analysis / routing conditioning
-> flow direction
-> flow accumulation
-> streams / river network
-> lakes / outlets
-> canonical water
```

Routing elevation, flow direction и flow accumulation — derived/internal. River network, lakes и water — canonical result. Край domain — open boundary, а не автоматически sea.

## Surface baseline

```text
elevation + slope + hydrology
-> moisture
-> vegetation potential
+ explicit surface feature bias
-> vegetation density
```

Explicit forest-like features модифицируют continuous fields. Terrain и surface responsibilities разделены. `moisture` и `vegetation_density` считаются semantic world data Core 0.1.

## Attempt model

Один `attempt_index` — одна независимая realization одного `GenerationPlan`.

- Plan, root seed, resolved ranges и compiled constraints между attempts неизменны;
- stochastic layout/terrain/placement realization меняется через attempt-specific RNG namespace;
- stage-local hidden retries в Core 0.1 запрещены;
- attempt может быть rejected рано и не выполнять дорогие downstream stages;
- late hard failure отвергает весь attempt;
- attempts не адаптируются на основании предыдущих failures;
- valid candidates ранжируются после generation.

Execution budget (`max_attempts`, `target_valid_candidates`) принадлежит semantic `GenerationConfig`, а не DomainSpec/Plan.

## RNG model

Никакого global mutable RNG. Child stream выводится из versioned semantic namespace:

```text
root seed
+ attempt index
+ stable stage id
+ stable scope
+ stable purpose
-> stable cryptographic derivation (rng v1)
-> local child seed / RNG
```

Scope использует stable feature identity и parameter/purpose paths, а не Python module/function names. Python `hash()` не является частью reproducibility contract. Порядок features, добавление unrelated random draws и debug instrumentation не должны сдвигать соседние streams.

Parameter values не входят в namespace: один random variate может быть детерминированно отображён в новый allowed domain после изменения параметров.

## Versioning и replay

Exact procedural replay требует совпадения:

```text
DomainSpec semantics
+ root seed
+ semantic GenerationConfig
+ exact generator version
```

Разные версии отвечают на разные вопросы:

- `DomainSpec.schema_version` — входной формат;
- `plan_version` — GenerationPlan contract;
- `domain_data_version` — result contract;
- `bundle_version` — bundle structure;
- `rng_version` — derivation algorithm;
- `generator_version` — конкретный набор generation algorithms.

Patch/minor generator update может изменить generated world. Исторический replay выполняется через tagged old release, а не через накопление legacy branches внутри новой версии.

`GenerationPlan` получает canonical SHA-256 fingerprint. Cross-platform bit-identical arrays пока не являются гарантией Core 0.1; supported runtime dependencies должны быть pinned, а numerical determinism тестируется отдельно.

При ranking полный tie разрешается детерминированно, например меньшим `attempt_index`.

## Dependency DAG и mutation boundary

Core организован как upstream-only DAG:

```text
DomainSpec
  -> Compiler
  -> GenerationPlan
  -> Layout
  -> Terrain -> slope/derived fields
  -> Hydrology
  -> Surface
  -> Dependent Placement
  -> Final Validation
  -> DomainData Assembly
```

Stage читает только явно объявленные upstream outputs и не мутирует output предыдущих stages. В частности запрещены:

- Surface -> mutate Terrain;
- POI -> mutate Hydrology/Terrain;
- Validator -> mutate Candidate;
- Hydrology -> silently regenerate Terrain;
- Renderer -> mutate DomainData;
- Compiler -> inspect generated world.

Если поздний semantic object должен формировать ранний слой мира, это выражается отдельным ранним feature/constraint (например plateau + city), а не скрытым side effect.

## Validation и ranking

Validation выполняется по стадиям. Engine invariants и user hard constraints обязательны. Validator только измеряет/оценивает.

Soft ranking не сводится к одному компенсирующему среднему: сначала минимизируется худшее weighted violation, затем учитывается weighted mean. Hard failure всегда reject.

## DomainData и bundle

`DomainData` — логическая структурная модель результата. Крупные raster fields хранятся отдельными array-файлами (Core 0.1 baseline: `.npy`), а `domain.json` содержит descriptors/references. Vector features/networks остаются structured data. PNG preview/debug не source of truth.

Роли данных:

- canonical — часть самого домена;
- derived — пересчитываемы из canonical;
- debug/internal — детали алгоритма и не входят в world contract.

## Python data model

Граница реализации Core 0.1:

- Pydantic v2 — serialized/stable contracts и internal declarative schemas (`DomainSpec`, `GenerationPlan`, `LayoutCandidate`, `ValidationResult`, `DomainData`, preset definitions, geometry value models);
- immutable/frozen Pydantic models для завершённых compiled/debug contracts где применимо;
- typed dataclasses — mutable runtime computational state (`CandidateState`, terrain/hydrology/surface state);
- NumPy arrays — numerical fields.

Pydantic отвечает за structural validation/serialization, но не выполняет generation, registry lookup или semantic compilation. Semantic validation живёт в compiler/validator modules.

## Граница Core

Core не знает о ChatGPT, GitHub, конкретной кампании или художественном renderer. Renderer читает `DomainData`, но не изменяет geography и не является source of truth.
