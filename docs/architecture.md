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
    -> validation + preset resolution
    -> Constraint Compiler
    -> GenerationPlan
    -> LayoutGenerator
    -> LayoutCandidate
    -> Terrain
    -> Hydrology
    -> Surface
    -> dependent feature placement
    -> staged validation / ranking
    -> DomainData
    -> Renderers / exporters
```

`DomainSpec` — язык намерения пользователя. `GenerationPlan` — сериализуемый resolved recipe с диапазонами, generic operators и compiled predicates. `LayoutCandidate` — конкретная макрогеометрия одной попытки. `DomainData` — принятый мир.

## Координаты и grid

Пользовательское/world-space соглашение:

- origin: southwest;
- `+x`: east;
- `+y`: north;
- единицы геометрии: километры.

`DomainSpec` задаёт `width_km`, `height_km`, `cell_size_km`. Raster indices (`row`, `column`) являются внутренней деталью `Grid`; geometry и пользовательские constraints ими не оперируют. `row 0` соответствует северной строке raster.

## Представление мира

Core использует три семейства данных:

- **Fields** — elevation, water, moisture, vegetation density и другие пространственные значения.
- **Networks** — river network и будущие связные линейные структуры.
- **Features** — семантически значимые spatial objects.

Spatial primitives описывают топологическую организацию, а не идеальные фигуры: `point`, `area`, `corridor`, `band` могут иметь органическую процедурную геометрию.

## Feature / preset / operator

Пользовательский `FeatureSpec` содержит `id`, `preset`, optional parameter overrides и tags. `family`, `shape` и `operator` следуют из preset и появляются после resolution.

Preset — данные, а не код. Он задаёт defaults, parameter schema, sampling policy и ссылку на generic Python operator. Один preset Core 0.1 использует один operator. Operator определяет механизм; preset — человекоосмысленную конфигурацию этого механизма.

Tags не влияют на генерацию скрытым образом.

## Parameters

Параметр DomainSpec задаёт фиксированное значение либо допустимый диапазон/набор. `min/max` означает allowed domain, а не автоматически uniform random. Sampling policy принадлежит preset/operator definition и переносится в `GenerationPlan`. Конкретное значение выбирается только при realization соответствующей стадии.

## Constraints

Constraint состоит из:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Selectors могут ссылаться на feature, его `part`, встроенный `domain_anchor`, `domain_region` или literal point/region. Semantic relations компилируются в generic evaluators/predicates: distance, containment, intersection и т. п.

`hard` constraint нельзя компенсировать score. `soft` constraint участвует в ranking с weight.

## Structural и dependent features

Structural features получают concrete macro geometry в `LayoutCandidate`.

Features, зависящие от уже созданной физической географии, получают на layout-stage `PlacementReservation`; окончательная геометрия выбирается позже по suitability. Если подходящей позиции нет, candidate отклоняется; validator и terrain не обязаны тайно чинить мир под POI.

## Terrain baseline

```text
BaseField
+ sum(StructuralTerrainContributions)
= StructuralElevation
-> ShapingOperators
-> CanonicalElevation
```

Structural/additive operators создают отдельные elevation contributions; shaping operators работают отдельной фазой. Feature order не должен молча менять additive result.

## Hydrology baseline

Canonical elevation не изменяется гидрологией Core 0.1. Для routing создаётся отдельная conditioned surface.

```text
elevation
-> depression analysis / routing conditioning
-> flow direction
-> flow accumulation
-> streams / river network
-> lakes / outlets
-> canonical water
```

Мелкие depression artifacts могут исправляться только в routing surface; крупные depressions являются кандидатами в lakes. Flow direction/accumulation — derived data; river network/lakes/water — результат мира.

## Surface baseline

```text
elevation + slope + hydrology
-> moisture
-> vegetation potential
+ explicit surface feature bias
-> vegetation density
```

Explicit forest-like features модифицируют непрерывные поля, а не бинарно закрашивают raster. Terrain и surface responsibilities разделены.

## Validation

Validation выполняется по стадиям. Ранние невозможные candidates отбрасываются до дорогих стадий.

- Engine invariants обязательны всегда.
- Любой failed hard constraint отвергает candidate.
- Soft constraints используются для ranking; сначала минимизируется худшее значимое нарушение, затем учитывается weighted mean.
- Validator измеряет и оценивает, но не модифицирует мир.

## DomainData и bundle

`DomainData` — логическая структурная модель результата. Крупные raster fields хранятся отдельными array-файлами; `domain.json` ссылается на них. Vector features/networks остаются структурированными данными. Preview/debug PNG не являются source of truth.

Данные различаются по роли:

- canonical — часть самого домена;
- derived — пересчитываемы из canonical;
- debug/internal — детали алгоритма и не входят в контракт мира.

## Граница Core

Core не знает о ChatGPT, GitHub, конкретной кампании или художественном renderer. Renderer читает `DomainData`, но не изменяет географию и не является источником истины.
