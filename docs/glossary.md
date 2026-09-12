---
id: GLOSSARY-CORE-0.1
kind: glossary
status: active
normative: true
---

# Glossary

## Domain

Ограниченная пространственная область мира/карты, которая генерируется как единое целое. Термин setting-agnostic: Domain может быть частью планеты, островом, сектором, локальной игровой зоной, абстрактным регионом или иным bounded spatial region. Он не обозначает специальную лоровую сущность и не предполагает конкретный жанр, кампанию или игровую систему.

## DomainSpec

Публичный входной контракт. Описывает намерение пользователя: physical size, seed, features, parameter overrides и constraints. Не содержит raster indices, setting identity и внутренних алгоритмических деталей.

## GenerationPlan

Внутренний immutable serializable resolved recipe. Presets раскрыты в metadata + layout recipe + effect recipe; semantic constraints — в evaluators/predicates/scoring recipes. Concrete attempt-specific values ещё не выбраны.

## LayoutCandidate

Concrete macro-layout одного attempt. Structural features уже имеют macro geometry; dependent features имеют materialized `PlacementReservation`.

## PlacementReservation

Vector allowed region (`RegionSet`), полученный из hard layout constraints. Определяет, где dependent feature может искать final placement после появления physical geography.

## RegionSet

Внутреннее vector-представление допустимой области: zero or more polygons, каждый с outer ring и optional holes. Может быть disconnected; empty RegionSet означает spatially invalid candidate, но не malformed contract.

## DomainCandidate

Runtime realization одного attempt, которая последовательно получает terrain, hydrology, surface и dependent placements. Не является canonical output, пока не прошла validation/ranking и не выбрана победителем.

## ValidationResult

Immutable diagnostic result одной validation stage: engine invariants, hard/soft constraint measurements и optional ranking metrics. Validator не мутирует candidate.

## DomainData

Self-contained canonical structured result принятой генерации: identity/provenance, field descriptors, networks, final features и validation summary. Крупные raster fields хранятся отдельно.

## DomainBundle

Физический набор файлов результата: manifest, domain metadata, canonical/derived arrays, optional debug artifacts и previews.

## Feature ID

Stable machine identity feature внутри DomainSpec. Используется references и RNG namespace. Косметическое переименование не должно менять `id`.

## Label

Optional human-readable имя domain/feature. Не участвует в procedural RNG identity или semantic plan fingerprint.

## Layout recipe

Часть resolved feature в `GenerationPlan`, отвечающая за macro geometry либо placement reservation и только за layout-owned parameters.

## Effect recipe

Часть resolved feature, отвечающая за downstream stage/operator (`terrain`, `surface`, `dependent_placement`) и effect-owned parameters/site profile.

## Field

Значение, определённое в пространстве domain: `elevation`, `water_depth`, `moisture`, `vegetation_density` и т. п.

## Network

Связная graph/linear structure, прежде всего directed river network; позже дороги и другие сети.

## Feature

Generic semantic spatial object, заданный через preset и constraints. Resolved feature имеет family, metadata, layout recipe и effect recipe. Setting-specific смысл может назначаться внешним consumer-ом, но не является частью primitive Core semantics.

## Spatial primitive

Топологический geometry type: `point`, `area`, `corridor`, `band`. Не означает идеальную геометрическую фигуру.

## Preset

Декларативная человекоосмысленная конфигурация generic operator: family, shape, defaults, parameter schemas, sampling policies и optional site profile. Preset не содержит embedded scripting. Core contract для preset generic; setting-specific preset catalogs относятся к внешнему extension/content layer.

## Operator

Generic Python-механизм, применяемый к geometry/fields: например ridge, depress, flatten или suitability placement.

## SiteProfile

Resolved physical suitability rules dependent feature: footprint, hard site requirements и intrinsic weighted preferences. Используется placement operator после physical generation.

## Constraint

Отношение между spatial selectors. `hard` обязательно; нарушение отклоняет candidate. `soft` оценивает final candidate и влияет на global ranking.

## SpatialSelector

Ссылка на geometry, участвующую в constraint: feature/part, domain anchor/region, literal point/region.

## Attempt

Одна независимая deterministic realization одного immutable `GenerationPlan`, идентифицируемая `attempt_index`. Hidden stage-local retries Core 0.1 запрещены.

## RNG namespace

Stable semantic address child RNG stream, выводимый из root seed, attempt index, stage, scope и purpose. Не зависит от Python call order или neighboring random draws.

## GenerationConfig

Execution policy. Semantic section Core 0.1 содержит `max_attempts` и `target_valid_candidates`; observability section управляет debug/logging и не меняет result.

## Spec fingerprint

SHA-256 canonical normalized source DomainSpec. Может отражать metadata документа.

## Plan fingerprint

SHA-256 canonical executable projection GenerationPlan. Presentation/provenance-only metadata (`label`, `tags`, `source_preset`, `spec_id`) исключается.

## Generation config fingerprint

SHA-256 canonical semantic projection GenerationConfig. Observability settings исключаются.

## Canonical data

Данные, изменение которых означает изменение самого domain: итоговые `elevation`, `water_depth`, `moisture`, `vegetation_density`, semantic features/networks.

## Derived data

Пересчитываемые представления canonical data: binary water mask, slope, flow direction, flow accumulation и другие caches.

## Debug/Internal data

Временные masks, distance fields, noise layers, routing surfaces и другие детали алгоритма. Не входят в world contract.

## Coherent noise

Пространственно коррелированный шум, где соседние точки имеют связанные значения. Используется для естественной нерегулярности, а не для определения всей композиции карты.

## Influence field

Поле силы воздействия feature/operation на пространство, например вклад горного пояса в elevation.

## Setting-specific extension

Внешний слой, который переводит понятия конкретного мира, кампании, жанра или игровой системы в generic contracts/presets `domain_generator`. Такой слой не является частью Core и не должен изменять primitive semantics скрытым образом.

## Normative document

Документ, содержащий обязательные правила проекта.

## Illustrative example

Пример для объяснения или проверки идеи. Сам по себе не создаёт требований и не должен обобщаться в правила Core.
