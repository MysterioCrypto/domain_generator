---
id: ARCH-CORE-0.1
kind: architecture
status: active
normative: true
target: core-0.1
---

# Архитектура Core 0.1

## Назначение и граница

`domain_generator` — процедурное ядро, не зависящее от конкретного сеттинга, для генерации ограниченных пространственных регионов мира или карты.

`Domain` означает универсальную ограниченную пространственную область. Это может быть часть планеты, остров, сектор, локальная игровая зона, абстрактный регион или иной кусок пространства, который генерируется как единое целое. Термин не несёт специальной лоровой семантики.

Конкретный мир, сеттинг, кампания, игровая система или приложение являются внешними потребителями Core:

```text
сеттинг / приложение / симуляция
            ↓
      adapter / presets
            ↓
        DomainSpec
            ↓
      domain_generator
            ↓
        DomainData
            ↓
 renderer / exporter / интеграция
```

Core не хранит идентичность сеттинга и не интерпретирует лор конкретной кампании. Каталоги пресетов конкретных сеттингов, adapters и данные мира находятся вне базового Core.

## Главный поток

```text
человек / клиент
    -> DomainSpec
    -> структурная валидация + разрешение presets
    -> компилятор ограничений
    -> GenerationPlan
    -> повторяющиеся детерминированные attempts
         -> LayoutGenerator
         -> LayoutCandidate
         -> поэтапная валидация
         -> Terrain
         -> Hydrology
         -> Surface
         -> размещение зависимых features
         -> финальная валидация / ranking
    -> лучший валидный DomainCandidate
    -> сборка DomainData
    -> renderers / exporters
```

`DomainSpec` — язык намерения пользователя или внешнего потребителя. `GenerationPlan` — неизменяемый разрешённый рецепт. `LayoutCandidate` — конкретный macro-layout одного attempt. `DomainCandidate` — runtime-состояние вычислений. `DomainData` — принятый сгенерированный регион.

## Координаты и grid

Мировая система координат:

- начало координат — юго-запад;
- `+x` направлен на восток;
- `+y` направлен на север;
- единица геометрии — километры.

`DomainSpec` задаёт физический размер и `cell_size_km`; размеры grid выводятся без скрытого округления. Raster `row/column` — внутренняя деталь `Grid`; `row 0` соответствует северной строке растра.

## Идентичность и metadata

Верхнеуровневый `DomainSpec.id` — идентичность domain/document и не входит в RNG namespace.

Feature `id` — стабильный машинный идентификатор для ссылок и RNG namespace. Необязательный `label` — человекочитаемая metadata. Изменение `label` не должно приводить к reroll feature; изменение feature `id` может изменить realization.

`label`, `tags`, `source_preset` сохраняются как provenance/output metadata, но не входят в семантический `plan_fingerprint` и не меняют Core скрытым образом.

Core не требует поля `setting`. Если внешнему приложению нужна идентичность конкретного мира или кампании, она хранится во внешнем contract/manifest layer.

## Feature / preset / operator

Пользовательский `FeatureSpec` содержит `id`, необязательный `label`, `preset`, необязательные переопределения параметров и tags. Preset — проверяемые декларативные данные: family, shape, defaults, схемы параметров, политики sampling, необязательный site profile и универсальный id operator-а. Preset не содержит встроенных скриптов.

После компиляции feature в `GenerationPlan` разделён на:

```text
metadata
layout recipe
  -> mode: geometry | reservation
  -> shape/final_shape
  -> параметры, принадлежащие layout

effect recipe
  -> stage
  -> универсальный operator
  -> параметры effect / site profile
```

Layout и downstream effect не делят один неструктурированный набор параметров.

Core определяет универсальный contract preset-ов и словарь operator-ов. Конкретные каталоги пресетов сеттингов являются внешним слоем контента/расширений и не входят в базовый пакет.

## Параметры

`DomainSpec` задаёт фиксированное значение либо допустимый числовой/enum-диапазон. `min/max` не означает автоматически равномерный sampling. Политика sampling принадлежит preset-у и переносится в соответствующий layout/effect recipe. Конкретное sampled value выбирается только внутри attempt через независимый RNG namespace.

## Ограничения

Пользовательское ограничение:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Примитивные relations Core 0.1:

```text
near
far_from
inside
outside
crosses
overlaps
adjacent
```

`connects` отложен до появления семантики маршрутов и сетей.

Spatial selectors могут ссылаться на feature/part, встроенный domain anchor/region или literal point/region. Семантические relations компилируются в универсальные measurements/evaluators и hard predicate либо soft scoring recipe.

Семантика частей geometry едина для всех модулей:

- point: `whole=center=point`;
- corridor: `whole=polyline`, start/end — первая/последняя точка centerline, center — 50% длины дуги, endpoints — оба конца;
- band: start/end/center/endpoints определяются по centerline, `whole` — footprint band, `boundary` — граница footprint;
- area: `whole` — polygon, `center` — геометрический centroid, `boundary` — граница polygon.

Вес soft constraint: `0 < weight <= 1`, по умолчанию `1.0`.

## LayoutCandidate

Structural features с `layout.mode=geometry` получают конкретную macro geometry (`point`, `corridor`, `band`, `area`). Shape описывает пространственную организацию, а не идеальную геометрическую фигуру.

Базовая geometry-модель Core 0.1:

- corridor/band имеют упорядоченную centerline;
- band `width_km` означает полную ширину, width profile параметризован `t in [0,1]`;
- area — простой внешний polygon без holes/self-intersection;
- canonical outer rings ориентированы против часовой стрелки.

Финальная geometry point и centerline corridor/band находятся внутри или на границе domain. Footprint влияния band может выходить за domain и обрезается при rasterization; это не считается нарушением invariant.

## PlacementReservation

Dependent feature с `layout.mode=reservation` получает векторный `RegionSet` — materialized результат hard layout constraints. Он может содержать несколько несвязанных polygons и holes. Пустой `RegionSet` структурно валиден и приводит к hard validation failure, а не к schema error.

Reservation не хранится как raster mask и не зависит от разрешения ячеек.

Core 0.1 materializes hard layout constraints только относительно geometry, уже существующей к стадии layout. Deferred -> deferred hard dependencies и hard dependency на будущую сгенерированную hydrology network не поддерживаются; compiler отклоняет их до запуска attempts.

## Пригодность места для POI

```text
PlacementReservation
-> hard requirements из SiteProfile
-> допустимые sites
-> внутренние preferences из SiteProfile
-> множество near-best sites
-> детерминированный weighted choice
-> финальная point geometry
```

`SiteProfile` оценивает footprint/окружение, а не одну cell. Если допустимых sites нет, attempt отклоняется. Placement не мутирует terrain/hydrology.

Внутренний score предпочтений `SiteProfile` используется только для выбора site внутри candidate. Пользовательские soft constraints оценивают финальный candidate и участвуют в глобальном ranking; внутренний suitability score сам по себе в глобальный ranking не переносится.

## Базовая модель Terrain

```text
BaseField
+ sum(StructuralTerrainContributions)
= StructuralElevation
-> ShapingOperators
-> CanonicalElevation
```

Аддитивные contributions независимы от порядка features. Shaping operators выполняются отдельной фазой; несовместимые shaping overlaps должны явно валидироваться, а не разрешаться случайным порядком.

## Базовая модель Hydrology

Canonical elevation в Core 0.1 гидрологией не мутируется.

```text
elevation
-> анализ впадин / подготовленная поверхность routing
-> направление стока
-> накопление стока
-> извлечение streams
-> river network + lakes/outlets
-> canonical water_depth
```

Routing surface, flow direction и flow accumulation — derived/internal data. River network, lakes и `water_depth` — canonical result. Граница domain открыта и не считается автоматически морем.

## Базовая модель Surface

```text
elevation + slope + hydrology
-> moisture
-> потенциал vegetation
+ явные surface feature biases
-> vegetation_density
```

`moisture` и `vegetation_density` — canonical continuous world fields. Surface не мутирует elevation/hydrology.

## Модель attempts

Один `attempt_index` — одна независимая realization неизменяемого `GenerationPlan`.

- скрытые локальные retries внутри стадий запрещены;
- ранний hard failure останавливает attempt;
- поздний hard failure отклоняет весь attempt;
- attempts не адаптируются на основе прошлых failures;
- `max_attempts` и `target_valid_candidates` находятся в semantic `GenerationConfig`;
- `target_valid_candidates=1` даёт семантику «первый валидный», отдельный selection mode в v0.1 не нужен.

## Модель RNG

Глобального mutable RNG нет. Дочерний stream:

```text
root seed
+ attempt index
+ stable stage id
+ stable scope
+ stable purpose
-> versioned cryptographic derivation
-> local RNG
```

Python `hash()` и имена module/function не являются persistence contract. Несвязанные random draws, порядок обхода features и observability instrumentation не сдвигают соседние streams.

## Fingerprints, versioning и replay

Различаются:

- `spec_fingerprint` — нормализованный исходный `DomainSpec`;
- `plan_fingerprint` — canonical executable projection `GenerationPlan`, исключающая metadata только для presentation/provenance;
- `generation_config_fingerprint` — canonical semantic projection `GenerationConfig`.

Точный procedural replay требует согласованных semantic inputs и точных версий generator/RNG. Стабильность сгенерированного мира между версиями generator не гарантируется; для исторического воспроизведения используется tagged old release.

Версии контрактов `DomainSpec`, plan, layout, validation, generation config, `DomainData`, bundle и RNG независимы друг от друга.

## Dependency DAG и границы мутации

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

Каждая stage читает только объявленные upstream outputs и не мутирует outputs предыдущих стадий. Validator — наблюдатель, а не исправляющий механизм. Renderer читает `DomainData`, но не изменяет состояние мира.

## Validation и ranking

Validation разделяет engine invariants, пользовательские hard constraints и пользовательские soft constraints.

Нарушение hard constraint или invariant всегда отклоняет candidate. Soft score нормализован в `[0,1]`:

```text
effective_violation = (1 - score) * weight
```

Валидные candidates сравниваются:

1. меньшее `worst_effective_violation`;
2. затем большее `weighted_mean_score`;
3. при полном равенстве — меньший `attempt_index`.

При отсутствии soft constraints используется neutral ranking: worst violation `0.0`, weighted mean `1.0`.

## DomainData и bundle

`DomainData` — самодостаточный canonical structured result принятой генерации. Он содержит identity/provenance, metadata domain/grid, descriptors canonical/derived fields, semantic features, networks и компактный validation summary.

Базовые canonical continuous fields Core 0.1:

- `elevation` (`float32`, m);
- `water_depth` (`float32`, m, >=0); binary water mask является derived;
- `moisture` (`float32`, normalized 0..1);
- `vegetation_density` (`float32`, normalized 0..1).

Крупные arrays хранятся отдельными `.npy`; `domain.json` содержит descriptors/references. Semantic lakes остаются area features; river network хранит явную направленную topology upstream -> downstream.

`PlacementReservation`, sampler recipes, rejected attempts и debug traces не входят в `DomainData`.

## Python data model

Граница реализации:

- Pydantic v2 — serialized/stable contracts и declarative schemas;
- immutable/frozen Pydantic models — завершённые Plan/Layout/Validation/Data value contracts там, где это применимо;
- typed dataclasses — изменяемое runtime-состояние вычислений;
- NumPy arrays — числовые поля.

Pydantic выполняет структурную валидацию и сериализацию, но не generation, registry lookup или semantic compilation.

## Граница Core

Core независим от конкретных сеттингов, кампаний, игровых систем, LLM/agent tooling, GitHub/CI orchestration, UI и renderer-ов. Иллюстративные примеры ненормативны.

Любой смысл, специфичный для конкретного сеттинга, должен поступать через внешний adapter/content layer и компилироваться в универсальные публичные контракты Core. Core не должен содержать special cases, названные в честь конкретного мира, фракции, локации, игровой системы или кампании.
