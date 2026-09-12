---
id: ROADMAP-CORE-0.1
kind: roadmap
status: active
normative: true
target: core-0.1
---

# План развития Core 0.1

`domain_generator` развивается как процедурное ядро, не зависящее от конкретного сеттинга. Конкретные миры, кампании, игровые системы, каталоги пресетов сеттингов и пакеты контента не являются частью плана развития Core и подключаются внешними слоями-потребителями.

## M0 — Основание проекта — ЗАВЕРШЕНО

Зафиксировать память проекта, архитектурные границы, glossary, ADR и правила совместной работы.

**Критерий:** новый чат или агент может восстановить состояние проекта из репозитория без чтения старого диалога.

## M1 — Контракты данных — ЗАВЕРШЕНО

Определить `DomainSpec v0.1`, `GenerationPlan v0.1`, `LayoutCandidate v0.1`, `PlacementReservation`, `ValidationResult v0.1`, `GenerationConfig v0.1`, `DomainData v0.1`, базовые роли geometry/data, domains параметров и поэтапную модель validation/ranking.

Принято и согласовано:

- физический contract domain/grid и мировая система координат;
- стабильные идентификаторы features, labels и граница metadata;
- модель preset/operator/parameter;
- spatial selectors и реестр примитивных relations;
- явное владение layout/effect в `GenerationPlan`;
- конкретная macro geometry + векторные reservations `RegionSet`;
- `SiteProfile` POI и граница dependent placement;
- attempts, semantic `GenerationConfig`, ranking и validation results;
- семантические RNG namespaces и границы replay/versioning;
- разделение canonical/derived/debug в `DomainData` / `DomainBundle`;
- базовые canonical поля `elevation`, `water_depth`, `moisture`, `vegetation_density`;
- граница реализации Pydantic/dataclass/NumPy;
- итоговая проверка согласованности контрактов (ADR-0009).

**Критерий выполнен:** contracts согласованы, имеют черновые serialized forms/examples и достаточны для начала реализации без скрытых архитектурных решений.

## M2 — Детерминированный pipeline — В РАБОТЕ

Сначала реализовать минимальный Python package и Pydantic v2 contracts/value models, соответствующие M1. Затем ввести независимые RNG streams, семантические fingerprints, жизненный цикл attempt и минимальный skeleton pipeline.

## M3 — Пространственная основа

Мировая система координат, преобразования `Grid`, masks, distances, continuous fields и первый debug renderer.

## M4 — Движок ограничений и layout

Универсальные geometry primitives `point`, `area`, `corridor`, `band`; `RegionSet`; `SpatialSelector`; evaluators/predicates для distance, containment, crossing, adjacency/overlap; generation of `LayoutCandidate` and `PlacementReservation`.

## M5 — Elevation v0.1

Базовое поле, аддитивные terrain contributions, фаза shaping, coherent/ridged noise, mountains/hills/plains/gorges без scenario-specific special cases.

## M6 — Hydrology v0.1

Анализ впадин, подготовленная поверхность routing, flow direction, flow accumulation, catchments, извлечение streams, направленная river network, lakes и canonical `water_depth`. Canonical elevation не изменяется; граница domain открыта и не считается автоматически морем.

## M7 — Surface v0.1

Непрерывные canonical fields `moisture` и `vegetation_density` на основе terrain/hydrology плюс явные surface-feature biases. Полноценная модель temperature/climate/biome не входит в v0.1.

## M8 — Универсальное размещение зависимых features

Suitability-based финальное размещение point POI/dependent features внутри `PlacementReservation` после физической географии с hard requirements из `SiteProfile` и внутренними preferences. Пользовательские soft constraints остаются сигналами глобального ranking candidates.

## M9 — Validation и ranking

Поэтапные engine invariants; hard constraints отклоняют candidate; soft constraints участвуют в ranking через worst effective violation и weighted mean; детерминированный tie-break — меньший `attempt_index`.

## M10 — Стабильные outputs

Стабильные `manifest.json`, `domain.json`, хранение canonical/derived arrays и debug/preview outputs. Preview не является источником истины.

## M11 — Acceptance suite

Набор фиксированных specs/seeds: minimal domain, random domain, изолированные capability tests и несколько ненормативных сложных examples. Примеры могут иллюстрировать разные жанры, но не создают зависимостей Core от конкретного сеттинга.

# Вне Core 0.1

Дорожные сети, полноценная human geography, художественная стилизация, ImageGen, battlemap, экономика, NPC, полноценная climate/biome model, граф deferred-to-deferred placement и расширения, специфичные для сеттинга/кампании/игровой системы, откладываются или реализуются внешними слоями.
