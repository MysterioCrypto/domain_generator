---
id: ROADMAP-CORE-0.1
kind: roadmap
status: active
normative: true
target: core-0.1
---

# План развития Core 0.1

`domain_generator` развивается как процедурное ядро, не зависящее от конкретного сеттинга. Конкретные миры, кампании, игровые системы, каталоги пресетов сеттингов и пакеты контента не являются частью Core и подключаются внешними слоями-потребителями.

## M0 — Основание проекта — ЗАВЕРШЕНО

Зафиксированы память проекта, архитектурные границы, glossary, ADR и правила совместной работы.

## M1 — Контракты данных — ЗАВЕРШЕНО

Определены `DomainSpec v0.1`, `GenerationPlan v0.1`, `LayoutCandidate v0.1`, `PlacementReservation`, `ValidationResult v0.1`, `GenerationConfig v0.1`, `DomainData v0.1` и базовые geometry/data contracts.

## M2 — Детерминированный pipeline — ЗАВЕРШЕНО

Реализованы package/runtime skeleton, semantic fingerprints, RNG protocol v1, attempts, deterministic candidate selection и canonical fixed stage pipeline.

## M3 — Пространственная основа — ЗАВЕРШЕНО

Реализованы world/grid convention, `GridAdapter`, masks/distances/continuous raster fields и Technical Renderer v0.1.

## M4 — Движок ограничений и layout — ЗАВЕРШЕНО ДЛЯ CORE 0.1

Реализованы `point`, `area`, `corridor`, `band`, `RegionSet`, spatial selectors, hard/soft relations, `LayoutCandidate` и `PlacementReservation`.

Некоторые расширенные geometry evaluators остаются будущим развитием и не блокируют Core 0.1.

## M5 — Elevation v0.1 — ЗАВЕРШЕНО

Реализованы базовое elevation field, area raise/depress, band ridge, flatten shaping и deterministic world-space noise.

## M6 — Hydrology v0.1 — ЗАВЕРШЕНО

Реализованы routing surface, priority flood, D8 flow, accumulation, stream/lake classification, `RiverNetwork`, `HydroFeature` lake materialization и canonical `water_depth`.

## M7 — Surface v0.1 — ЗАВЕРШЕНО

Реализованы canonical `moisture` и `vegetation_density`, slope-derived vegetation response и explicit surface feature biases.

Полноценная temperature/climate/biome model не входит в Core 0.1.

## M8 — Универсальное размещение зависимых features — ЗАВЕРШЕНО

Реализованы site metrics, hard candidate filtering, preferences, near-best deterministic weighted selection и `PlacementState` для deferred point features.

## M9 — Validation и ranking — ЗАВЕРШЕНО

Реализованы engine invariants, hard rejection, soft scoring, final validation и deterministic candidate ranking.

## M10 — Стабильные outputs — ЗАВЕРШЕНО

Реализованы `DomainData Assembler v0.1`, canonical `DomainBundle Export v0.1`, `manifest.json` с hashes, canonical `.npy` fields, Technical Renderer v0.1, `GenerationRequest`, `PresetCatalog`, canonical Python entrypoint и CLI `domain-generator generate`.

Preview остаётся non-canonical и не является источником истины.

## M11 — Acceptance suite — СЛЕДУЮЩИЙ RELEASE GATE CORE 0.1

Нужен набор фиксированных specs/seeds, проверяющий систему целиком, а не только отдельные modules:

- minimal domain;
- representative terrain;
- hydrology/lake/river case;
- surface fields;
- dependent POI placement;
- constraints/ranking;
- complex mixed-domain example;
- stable application/bundle output assertions.

Acceptance suite должен проверять semantic properties, provenance/fingerprints и topology/metrics там, где это устойчивее хранения больших binary golden files.

После прохождения M11 можно формировать Core 0.1 release candidate.

# Параллельный integration track вне Core

После появления canonical application entrypoint внешние consumers могут развиваться независимо от release hardening Core:

```text
Local Model Skill / Adapter v0.1
→ Remote GitHub Actions Generation Adapter
```

Оба слоя обязаны использовать canonical `GenerationRequest` / `PresetCatalog` / CLI или Python application boundary и не создавать альтернативный generation pipeline.

Отдельный downstream presentation track:

```text
Presentation / ImageGen Guide Renderer
→ imagegen-guide.png
→ artistic map generation
```

Этот слой не изменяет semantic world state.

# Вне Core 0.1

Дорожные сети, полноценная human geography, художественная стилизация, ImageGen, battlemap, экономика, NPC, полноценная climate/biome model, physical river width/discharge, advanced erosion, deferred-to-deferred placement graph и setting/game-specific extensions реализуются позже или внешними слоями.
