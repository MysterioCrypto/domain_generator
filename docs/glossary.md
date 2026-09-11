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

Внутренний сериализуемый resolved recipe. Presets раскрыты в generic geometry/operator definitions, semantic constraints — в generic evaluators/predicates. Диапазоны ещё не обязаны быть реализованы в конкретные значения.

## LayoutCandidate

Конкретная макрогеометрия одной детерминированной попытки layout. Structural features уже имеют geometry; dependent features могут иметь только `PlacementReservation`.

## PlacementReservation

Допустимая область/множество областей, внутри которых dependent feature должен искать финальное размещение после появления физической географии.

## DomainData

Канонический структурированный результат принятой генерации: fields, networks, features, metadata и validation summary. Крупные raster fields могут храниться отдельными array-файлами.

## DomainBundle

Физический набор файлов результата: manifest, domain metadata, canonical/derived arrays, optional debug artifacts и previews.

## Field

Значение, определённое в пространстве домена: elevation, water, moisture, vegetation density и т. п.

## Network

Связная графовая/линейная структура: прежде всего river network; позже дороги и другие сети.

## Feature

Семантически значимый spatial object, заданный через preset и constraints. Внутренний resolved feature имеет family, shape, operator и parameters.

## Spatial primitive

Топологический тип geometry: `point`, `area`, `corridor`, `band`. Не означает идеальную геометрическую фигуру.

## Preset

Декларативная человекоосмысленная конфигурация generic operator: family, shape, defaults, parameter schema и sampling policy. Preset не содержит исполняемого кода.

## Operator

Generic Python-механизм, применяемый к geometry/fields: например ridge, depress, flatten или suitability placement.

## Constraint

Отношение между spatial selectors. `hard` обязательно; его нарушение отклоняет candidate. `soft` влияет на ranking через score и weight.

## SpatialSelector

Ссылка на geometry, участвующую в constraint: feature или его part, domain anchor/region, literal point/region.

## Candidate

Одна детерминированная попытка получить допустимый мир при заданных plan/seed/attempt.

## Canonical data

Данные, изменение которых означает изменение самого домена: например итоговая elevation, water, semantic features/networks.

## Derived data

Пересчитываемые представления canonical data: например slope, flow direction, flow accumulation.

## Debug/Internal data

Временные маски, distance fields, noise layers и другие детали работы алгоритма. Не входят в контракт мира.

## Coherent noise

Пространственно коррелированный шум, где соседние точки имеют связанные значения. Используется для естественной нерегулярности, а не для определения всей композиции карты.

## Influence field

Поле силы воздействия feature/operation на пространство, например вклад горного пояса в elevation.

## Normative document

Документ, содержащий обязательные правила проекта.

## Illustrative example

Пример для объяснения или проверки идеи. Сам по себе не создаёт требований и не должен обобщаться в правила Core.
