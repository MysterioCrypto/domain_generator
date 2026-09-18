---
id: ROADMAP-CORE-0.1-HISTORICAL
kind: roadmap
status: historical
normative: false
target: core-0.1-prealpha
---

# Исторический план развития Core 0.1

> Этот документ не описывает текущую development line. Для текущего состояния сначала читать корневой `PROJECT.md`, затем `PROJECT.md` и `docs/CONTEXT.md` на указанной active development branch.

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

## M11 — Acceptance suite — ЗАВЕРШЕНО

Normative design: `docs/design/m11-acceptance-suite-v0.1.md`.

Implementation merged through PR #57 after separate acceptance. Final implementation CI: `357 passed in 12.47s`.

M11 фиксирует семь representative worlds:

- A01 minimal;
- A02 terrain-ridge;
- A03 hydrology-lake-river;
- A04 surface;
- A05 dependent-poi;
- A06 constraints-ranking;
- A07 complex-mixed.

Каждый case проверяет exact replay и semantic properties одновременно. Baseline хранится компактно через `expected.json`, fingerprints/digests и case-specific assertions вместо обязательных больших binary golden files.

M11 также проверяет canonical DomainBundle path и deterministic provenance. Technical preview не является Core binary golden.

Acceptance suite обнаружил production defect на границе Layout/soft constraints. Он был исправлен отдельным PR #58 с regression test и только после этого acceptance baseline A06 был зафиксирован.

Release gate сейчас green:

```text
full unit/integration suite
A01..A07 acceptance worlds
exact replay all cases
canonical bundle acceptance
engine/hard invariants
provenance/fingerprints/digests
```

Таким образом Core 0.1 готов к короткому release-candidate review / hardening без добавления новых generation semantics.

# Параллельный integration track вне Core — ЗАВЕРШЁН ДЛЯ 0.1

Реализованы:

```text
Local Model Skill / Adapter v0.1
→ Codex Integration Packaging v0.1
→ Remote GitHub Actions Generation Adapter v0.1
```

Все слои используют canonical `GenerationRequest` / `PresetCatalog` / CLI или Python application boundary и не создают альтернативный generation pipeline.

Отдельный downstream presentation track:

```text
Presentation / ImageGen Guide Renderer
→ imagegen-guide.png
→ artistic map generation
```

Этот слой не изменяет semantic world state и не блокирует Core 0.1.

# После M11 — исторически планировалось, но было отменено visual audit

Ниже сохранён старый план release-candidate review. Он не является текущей задачей.

Первоначально планировался:

```text
Core 0.1 release-candidate review / hardening
→ package/version/release metadata
→ documentation consistency
→ known-blocker review
→ final clean CI checklist
→ Core 0.1 release candidate declaration
```

Любое semantic изменение, найденное на этом этапе, снова проходит обычный design gate и отдельный implementation acceptance.

# Вне Core 0.1

Дорожные сети, полноценная human geography, художественная стилизация, ImageGen, battlemap, экономика, NPC, полноценная climate/biome model, physical river width/discharge, advanced erosion, deferred-to-deferred placement graph и setting/game-specific extensions реализуются позже или внешними слоями.