---
id: GLOSSARY-CORE-0.1
kind: glossary
status: active
normative: true
---

# Glossary

## Domain

Один генерируемый пространственный регион. Не предполагается, что он является частью обычной планеты или глобальной карты.

## DomainSpec

Публичный входной контракт. Описывает намерение пользователя: размер домена, seed, features, parameter overrides и constraints. Не содержит raster indices и внутренних алгоритмических деталей.

## GenerationPlan

Внутренний immutable serializable resolved recipe. Presets раскрыты в generic geometry/operator definitions, semantic constraints — в evaluators/predicates/scoring recipes. Concrete attempt-specific values ещё не выбраны.

## LayoutCandidate

Concrete macro-layout одной попытки. Structural features уже имеют macro geometry; dependent features могут иметь только `PlacementReservation`.

## PlacementReservation

Допустимая область или набор областей, внутри которых dependent feature ищет финальное размещение после появления physical geography.

## DomainCandidate

Runtime realization одного attempt, которая может последовательно получить terrain, hydrology, surface и dependent placements. Не является canonical output, пока не прошла validation/ranking и не выбрана победителем.

## DomainData

Канонический structured result принятой генерации: fields, networks, features, metadata и validation summary. Крупные raster fields хранятся отдельно и описываются descriptors/references.

## DomainBundle

Физический набор файлов результата: manifest, domain metadata, canonical/derived arrays, optional debug artifacts и previews.

## Feature ID

Stable machine identity feature внутри DomainSpec. Используется references и RNG namespace. Косметическое переименование не должно менять `id`.

## Label

Optional human-readable имя domain/feature. Не участвует в procedural RNG identity.

## Field

Значение, определённое в пространстве домена: elevation, water, moisture, vegetation density и т. п.

## Network

Связная графовая/линейная структура: прежде всего river network; позже дороги и другие сети.

## Feature

Semantic spatial object, заданный через preset и constraints. Resolved feature имеет family, shape, lifecycle, operator и parameter recipes.

## Spatial primitive

Топологический тип geometry: `point`, `area`, `corridor`, `band`. Не означает идеальную геометрическую фигуру.

## Preset

Декларативная человекоосмысленная конфигурация generic operator: family, shape, defaults, parameter schema, sampling policy и optional site profile. Preset не содержит исполняемого scripting.

## Operator

Generic Python-механизм, применяемый к geometry/fields: например ridge, depress, flatten или suitability placement.

## SiteProfile

Resolved правила physical suitability dependent feature: footprint, hard site requirements и weighted preferences. Используется placement operator после physical generation.

## Constraint

Отношение между spatial selectors. `hard` обязательно; нарушение отклоняет candidate. `soft` влияет на ranking через scoring/weight.

## SpatialSelector

Ссылка на geometry, участвующую в constraint: feature/part, domain anchor/region, literal point/region.

## Attempt

Одна независимая deterministic realization одного `GenerationPlan`, идентифицируемая `attempt_index`. Hidden stage-local retries в Core 0.1 не считаются отдельной моделью и запрещены.

## RNG namespace

Stable semantic address child RNG stream, выводимый из root seed, attempt index, stage, scope и purpose. Не зависит от Python call order или neighboring random draws.

## GenerationConfig

Execution policy генерации, например `max_attempts` и `target_valid_candidates`. Semantic параметры GenerationConfig могут влиять на выбранный result, но не являются частью DomainSpec.

## Observability config

Logging/debug/export/preview settings, которые не должны влиять на semantic generation result.

## Canonical data

Данные, изменение которых означает изменение самого домена: например итоговая elevation, water, moisture, semantic features/networks.

## Derived data

Пересчитываемые представления canonical data: например slope, flow direction, flow accumulation.

## Debug/Internal data

Временные masks, distance fields, noise layers и другие детали работы алгоритма. Не входят в world contract.

## Coherent noise

Пространственно коррелированный шум, где соседние точки имеют связанные значения. Используется для естественной нерегулярности, а не для определения всей композиции карты.

## Influence field

Поле силы воздействия feature/operation на пространство, например вклад горного пояса в elevation.

## Normative document

Документ, содержащий обязательные правила проекта.

## Illustrative example

Пример для объяснения или проверки идеи. Сам по себе не создаёт требований и не должен обобщаться в правила Core.
