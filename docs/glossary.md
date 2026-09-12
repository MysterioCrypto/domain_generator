---
id: GLOSSARY-CORE-0.1
kind: glossary
status: active
normative: true
---

# Словарь терминов

## Domain

Ограниченная пространственная область мира или карты, которая генерируется как единое целое. Термин не зависит от конкретного сеттинга: `Domain` может быть частью планеты, островом, сектором, локальной игровой зоной, абстрактным регионом или иной ограниченной пространственной областью. Он не обозначает специальную лоровую сущность и не предполагает конкретный жанр, кампанию или игровую систему.

## DomainSpec

Публичный входной контракт. Описывает намерение пользователя: физический размер, seed, features, переопределения параметров и constraints. Не содержит raster indices, идентичность сеттинга и внутренних алгоритмических деталей.

## GenerationPlan

Внутренний неизменяемый сериализуемый разрешённый рецепт. Presets раскрыты в metadata + layout recipe + effect recipe; семантические constraints — в evaluators/predicates/scoring recipes. Конкретные значения, зависящие от attempt, ещё не выбраны.

## LayoutCandidate

Конкретный macro-layout одного attempt. Structural features уже имеют macro geometry; dependent features имеют materialized `PlacementReservation`.

## PlacementReservation

Векторная допустимая область (`RegionSet`), полученная из hard layout constraints. Определяет, где dependent feature может искать финальное размещение после появления физической географии.

## RegionSet

Внутреннее векторное представление допустимой области: ноль или больше polygons, каждый с outer ring и необязательными holes. Может состоять из несвязанных частей; пустой `RegionSet` означает пространственно недопустимый candidate, но не malformed contract.

## DomainCandidate

Runtime-realization одного attempt, которая последовательно получает terrain, hydrology, surface и dependent placements. Не является canonical output, пока не прошла validation/ranking и не выбрана победителем.

## ValidationResult

Неизменяемый диагностический результат одной стадии validation: engine invariants, измерения hard/soft constraints и необязательные ranking metrics. Validator не мутирует candidate.

## DomainData

Самодостаточный canonical structured result принятой генерации: identity/provenance, descriptors полей, networks, финальные features и validation summary. Крупные raster fields хранятся отдельно.

## DomainBundle

Физический набор файлов результата: manifest, metadata domain, canonical/derived arrays, необязательные debug artifacts и previews.

## Feature ID

Стабильный машинный идентификатор feature внутри `DomainSpec`. Используется для ссылок и RNG namespace. Косметическое переименование не должно менять `id`.

## Label

Необязательное человекочитаемое имя domain/feature. Не участвует в procedural RNG identity или semantic plan fingerprint.

## Layout recipe

Часть resolved feature в `GenerationPlan`, отвечающая за macro geometry либо placement reservation и только за параметры, принадлежащие layout.

## Effect recipe

Часть resolved feature, отвечающая за downstream stage/operator (`terrain`, `surface`, `dependent_placement`) и параметры/site profile, принадлежащие effect.

## Field

Значение, определённое в пространстве domain: `elevation`, `water_depth`, `moisture`, `vegetation_density` и т. п.

## Network

Связная graph/linear structure, прежде всего направленная river network; позже — дороги и другие сети.

## Feature

Универсальный семантический пространственный объект, заданный через preset и constraints. Resolved feature имеет family, metadata, layout recipe и effect recipe. Смысл конкретного сеттинга может назначаться внешним consumer-ом, но не является частью примитивной семантики Core.

## Spatial primitive

Топологический geometry type: `point`, `area`, `corridor`, `band`. Не означает идеальную геометрическую фигуру.

## Preset

Декларативная человекоосмысленная конфигурация универсального operator-а: family, shape, defaults, схемы параметров, политики sampling и необязательный site profile. Preset не содержит встроенных скриптов. Contract preset-а в Core универсален; каталоги пресетов конкретных сеттингов относятся к внешнему extension/content layer.

## Operator

Универсальный Python-механизм, применяемый к geometry/fields: например ridge, depress, flatten или suitability placement.

## SiteProfile

Разрешённые правила физической пригодности места для dependent feature: footprint, hard site requirements и внутренние weighted preferences. Используется placement operator после физической генерации.

## Constraint

Отношение между spatial selectors. `hard` обязательно; нарушение отклоняет candidate. `soft` оценивает финальный candidate и влияет на глобальный ranking.

## SpatialSelector

Ссылка на geometry, участвующую в constraint: feature/part, domain anchor/region, literal point/region.

## Attempt

Одна независимая детерминированная realization неизменяемого `GenerationPlan`, идентифицируемая `attempt_index`. Скрытые локальные retries внутри стадий в Core 0.1 запрещены.

## RNG namespace

Стабильный семантический адрес дочернего RNG stream, выводимый из root seed, attempt index, stage, scope и purpose. Не зависит от порядка Python-вызовов или соседних random draws.

## GenerationConfig

Политика исполнения. Semantic section Core 0.1 содержит `max_attempts` и `target_valid_candidates`; observability section управляет debug/logging и не меняет результат.

## Spec fingerprint

SHA-256 canonical normalized source `DomainSpec`. Может отражать metadata документа.

## Plan fingerprint

SHA-256 canonical executable projection `GenerationPlan`. Metadata только для presentation/provenance (`label`, `tags`, `source_preset`, `spec_id`) исключается.

## Generation config fingerprint

SHA-256 canonical semantic projection `GenerationConfig`. Настройки observability исключаются.

## Canonical data

Данные, изменение которых означает изменение самого domain: итоговые `elevation`, `water_depth`, `moisture`, `vegetation_density`, semantic features/networks.

## Derived data

Пересчитываемые представления canonical data: binary water mask, slope, flow direction, flow accumulation и другие caches.

## Debug/Internal data

Временные masks, distance fields, noise layers, routing surfaces и другие детали алгоритма. Не входят в контракт мира.

## Coherent noise

Пространственно коррелированный шум, где соседние точки имеют связанные значения. Используется для естественной нерегулярности, а не для определения всей композиции карты.

## Influence field

Поле силы воздействия feature/operation на пространство, например вклад горного пояса в elevation.

## Setting-specific extension

Внешний слой, который переводит понятия конкретного мира, кампании, жанра или игровой системы в универсальные contracts/presets `domain_generator`. Такой слой не является частью Core и не должен скрыто изменять примитивную семантику.

## Normative document

Нормативный документ, содержащий обязательные правила проекта.

## Illustrative example

Иллюстративный пример для объяснения или проверки идеи. Сам по себе не создаёт требований и не должен обобщаться в правила Core.
