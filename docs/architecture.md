---
id: ARCH-CORE-0.1
kind: architecture
status: active
normative: true
target: core-0.1
---

# Архитектура Core 0.1

## Назначение и граница

`domain_generator` — setting-agnostic procedural core для генерации ограниченных пространственных регионов мира/карты.

`Domain` означает generic bounded spatial region. Это может быть часть планеты, остров, сектор, локальная игровая зона, абстрактный регион или иной кусок пространства, который генерируется как единое целое. Термин не несёт специальной лоровой семантики.

Конкретный world/setting/campaign/game system является внешним consumer-ом Core:

```text
setting / application / simulation
            ↓
      adapter / presets
            ↓
        DomainSpec
            ↓
      domain_generator
            ↓
        DomainData
            ↓
 renderer / exporter / integration
```

Core не хранит setting identity и не интерпретирует campaign-specific lore. Setting-specific preset catalogs, adapters и world data находятся вне базового Core.

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
         -> staged validation
         -> Terrain
         -> Hydrology
         -> Surface
         -> dependent feature placement
         -> final validation / ranking
    -> best valid DomainCandidate
    -> DomainData assembly
    -> Renderers / exporters
```

`DomainSpec` — язык намерения пользователя/consumer-а. `GenerationPlan` — immutable resolved recipe. `LayoutCandidate` — concrete macro-layout одного attempt. `DomainCandidate` — runtime computational state. `DomainData` — принятый generated region.

## Координаты и grid

World coordinates:

- origin southwest;
- `+x` east;
- `+y` north;
- geometry units km.

`DomainSpec` задаёт physical size и `cell_size_km`; grid dimensions выводятся без silent rounding. Raster `row/column` — внутренняя деталь `Grid`; `row 0` соответствует северной raster row.

## Identity и metadata

Top-level `DomainSpec.id` — identity domain/document и не входит в RNG namespace.

Feature `id` — stable machine identity для references и RNG namespace. Optional `label` — human-readable metadata. Смена `label` не должна reroll'ить feature; смена feature `id` может изменить realization.

`label`, `tags`, `source_preset` сохраняются как provenance/output metadata, но не входят в semantic `plan_fingerprint` и не меняют Core скрытым образом.

Core не требует поля `setting`. Если внешнему приложению нужна identity конкретного мира/кампании, она хранится во внешнем contract/manifest layer.

## Feature / preset / operator

User `FeatureSpec` содержит `id`, optional `label`, `preset`, optional parameter overrides и tags. Preset — validated declarative data: family, shape, defaults, parameter schemas, sampling policies, optional site profile и generic operator id. Preset не содержит embedded scripting.

После compilation feature в `GenerationPlan` разделён на:

```text
metadata
layout recipe
  -> mode: geometry | reservation
  -> shape/final_shape
  -> layout-owned parameters

effect recipe
  -> stage
  -> generic operator
  -> effect-owned parameters / site profile
```

Layout и downstream effect не делят один неструктурированный parameter bag.

Core определяет generic preset contract и operator vocabulary. Конкретные setting-specific preset catalogs являются внешним content/extension layer и не входят в базовый пакет.

## Parameters

DomainSpec задаёт fixed value либо allowed numeric/enum domain. `min/max` не означает автоматически uniform sampling. Sampling policy принадлежит preset и переносится в соответствующий layout/effect recipe. Concrete sampled value выбирается только внутри attempt через независимый RNG namespace.

## Constraints

User constraint:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Primitive relations Core 0.1:

```text
near
far_from
inside
outside
crosses
overlaps
adjacent
```

`connects` отложен до появления route/network semantics.

Spatial selectors могут ссылаться на feature/part, built-in domain anchor/region или literal point/region. Semantic relations компилируются в generic measurements/evaluators и hard predicate либо soft scoring recipe.

Geometry-part semantics едины для всех modules:

- point: `whole=center=point`;
- corridor: `whole=polyline`, start/end first/last centerline point, center at 50% arc length, endpoints both ends;
- band: start/end/center/endpoints по centerline, `whole` — band footprint, `boundary` — footprint boundary;
- area: `whole` — polygon, `center` — geometric centroid, `boundary` — polygon boundary.

Soft constraint weight: `0 < weight <= 1`, default `1.0`.

## LayoutCandidate

Structural features с `layout.mode=geometry` получают concrete macro geometry (`point`, `corridor`, `band`, `area`). Shape описывает spatial organization, а не идеальную геометрическую фигуру.

Core 0.1 geometry baseline:

- corridor/band имеют ordered centerline;
- band `width_km` означает full width, width profile параметризован `t in [0,1]`;
- area — simple outer polygon без holes/self-intersection;
- canonical outer rings counter-clockwise.

Point final geometry и corridor/band centerline находятся inside/on domain boundary. Band influence footprint может выходить за domain и клиппится при rasterization; это не invariant failure.

## PlacementReservation

Dependent feature с `layout.mode=reservation` получает vector `RegionSet` — materialized результат hard layout constraints. Он может содержать несколько disconnected polygons и holes. Пустой RegionSet структурно валиден и приводит к hard validation failure, а не schema error.

Reservation не хранится raster mask и не зависит от cell resolution.

Core 0.1 materializes layout-hard constraints только относительно geometry, уже существующей к layout stage. Deferred -> deferred hard dependencies и hard dependency на будущую generated hydrology network не поддерживаются; compiler отклоняет их до attempts.

## POI suitability

```text
PlacementReservation
-> hard SiteProfile requirements
-> valid sites
-> intrinsic SiteProfile preferences
-> near-best site set
-> deterministic weighted choice
-> final point geometry
```

SiteProfile оценивает footprint/окружение, а не одну cell. Если valid sites нет, attempt отклоняется. Placement не мутирует terrain/hydrology.

Intrinsic SiteProfile preference score используется только для выбора site внутри candidate. User soft constraints оценивают final candidate и участвуют в global ranking; intrinsic suitability score сам по себе не переносится в global ranking.

## Terrain baseline

```text
BaseField
+ sum(StructuralTerrainContributions)
= StructuralElevation
-> ShapingOperators
-> CanonicalElevation
```

Additive contributions независимы от feature order. Shaping operators выполняются отдельной фазой; несовместимые shaping overlaps должны быть явно валидированы, а не разрешаться случайным порядком.

## Hydrology baseline

Canonical elevation Core 0.1 гидрологией не мутируется.

```text
elevation
-> depression analysis / conditioned routing surface
-> flow direction
-> flow accumulation
-> stream extraction
-> river network + lakes/outlets
-> canonical water_depth
```

Routing surface, flow direction и flow accumulation — derived/internal. River network, lakes и `water_depth` — canonical result. Domain edge — open boundary, не автоматически море.

## Surface baseline

```text
elevation + slope + hydrology
-> moisture
-> vegetation potential
+ explicit surface feature bias
-> vegetation_density
```

`moisture` и `vegetation_density` — canonical continuous world fields. Surface не мутирует elevation/hydrology.

## Attempt model

Один `attempt_index` — одна независимая realization immutable `GenerationPlan`.

- hidden stage-local retries запрещены;
- early hard failure останавливает attempt;
- late hard failure отклоняет весь attempt;
- attempts не адаптируются на основе прошлых failures;
- `max_attempts` и `target_valid_candidates` находятся в semantic `GenerationConfig`;
- `target_valid_candidates=1` даёт first-valid semantics, отдельный selection mode v0.1 не нужен.

## RNG model

Никакого global mutable RNG. Child stream:

```text
root seed
+ attempt index
+ stable stage id
+ stable scope
+ stable purpose
-> versioned cryptographic derivation
-> local RNG
```

Python `hash()` и module/function names не являются persistence contract. Unrelated random draws, feature iteration order и observability instrumentation не сдвигают соседние streams.

## Fingerprints, versioning, replay

Различаются:

- `spec_fingerprint` — normalized source DomainSpec;
- `plan_fingerprint` — canonical executable projection GenerationPlan, исключающая presentation/provenance-only metadata;
- `generation_config_fingerprint` — canonical semantic projection GenerationConfig.

Exact procedural replay требует согласованных semantic inputs и exact generator/RNG version. Generated world stability между generator versions не гарантируется; historical regeneration использует tagged old release.

Contract versions: DomainSpec schema, plan, layout, validation, generation config, DomainData, bundle и RNG versioning независимы.

## Dependency DAG и mutation boundary

```text
DomainSpec
  -> Compiler
  -> GenerationPlan
  -> Layout
  -> Terrain -> derived slope
  -> Hydrology
  -> Surface
  -> Dependent Placement
  -> Final Validation
  -> DomainData Assembly
```

Stage читает только declared upstream outputs и не мутирует outputs предыдущих stages. Validator — observer, не fixer. Renderer читает DomainData, но не изменяет world state.

## Validation и ranking

Validation разделяет engine invariants, user hard constraints и user soft constraints.

Hard/invariant failure всегда reject. Soft score нормализован в `[0,1]`:

```text
effective_violation = (1 - score) * weight
```

Valid candidates сравниваются:

1. меньше worst effective violation;
2. затем больше weighted mean score;
3. полный tie — меньше attempt index.

При отсутствии soft constraints neutral ranking: worst violation `0.0`, weighted mean `1.0`.

## DomainData и bundle

`DomainData` — self-contained accepted generated region. Он содержит identity/provenance, domain/grid metadata, canonical/derived field descriptors, semantic features, networks и compact validation summary.

Canonical continuous fields Core 0.1 baseline:

- `elevation` (`float32`, m);
- `water_depth` (`float32`, m, >=0); binary water mask derived;
- `moisture` (`float32`, normalized 0..1);
- `vegetation_density` (`float32`, normalized 0..1).

Крупные arrays хранятся отдельными `.npy`; `domain.json` содержит descriptors/references. Semantic lakes остаются area features; river network хранит explicit directed topology upstream -> downstream.

`PlacementReservation`, sampler recipes, rejected attempts и debug traces не входят в DomainData.

## Python data model

Implementation boundary:

- Pydantic v2 — serialized/stable contracts и declarative schemas;
- immutable/frozen Pydantic models — completed Plan/Layout/Validation/Data value contracts where applicable;
- typed dataclasses — mutable runtime computational state;
- NumPy arrays — numerical fields.

Pydantic выполняет structural validation/serialization, но не generation, registry lookup или semantic compilation.

## Граница Core

Core независим от конкретных сеттингов, кампаний, игровых систем, LLM/agent tooling, GitHub/CI orchestration, UI и renderer-ов. Illustrative examples ненормативны.

Любой setting-specific смысл должен поступать через внешний adapter/content layer и компилироваться в generic public contracts Core. Core не должен содержать special cases, названные в честь конкретного мира, фракции, локации, игровой системы или кампании.
