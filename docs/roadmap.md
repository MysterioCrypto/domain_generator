---
id: ROADMAP-CORE-0.1
kind: roadmap
status: active
normative: true
target: core-0.1
---

# Roadmap Core 0.1

`domain_generator` развивается как setting-agnostic procedural core. Конкретные миры, кампании, игровые системы, setting-specific preset catalogs и content packages не являются частью roadmap Core и подключаются внешними consumer layers.

## M0 — Project foundation — DONE

Зафиксировать память проекта, архитектурные границы, glossary, ADR и правила совместной работы.

**Критерий:** новый чат или агент может восстановить состояние проекта из репозитория без чтения старого диалога.

## M1 — Data contracts — DONE

Определить `DomainSpec v0.1`, `GenerationPlan v0.1`, `LayoutCandidate v0.1`, `PlacementReservation`, `ValidationResult v0.1`, `GenerationConfig v0.1`, `DomainData v0.1`, базовые geometry/data roles, parameter domains и staged validation/ranking model.

Принято и согласовано:

- physical domain/grid contract и world coordinates;
- stable feature identities, labels и metadata boundary;
- preset/operator/parameter model;
- spatial selectors и primitive relation registry;
- explicit layout/effect ownership в GenerationPlan;
- concrete macro geometry + vector RegionSet reservations;
- POI SiteProfile и dependent placement boundary;
- attempts, semantic GenerationConfig, ranking and validation results;
- semantic RNG namespaces/replay/versioning boundaries;
- DomainData/DomainBundle canonical/derived/debug split;
- canonical `elevation`, `water_depth`, `moisture`, `vegetation_density` baseline;
- Pydantic/dataclass/NumPy implementation boundary;
- final cross-contract consistency review (ADR-0009).

**Критерий выполнен:** contracts согласованы, имеют draft serialized forms/examples и достаточны для начала реализации без скрытых архитектурных решений.

## M2 — Deterministic pipeline — IN PROGRESS

Сначала реализовать минимальный Python package и Pydantic v2 contracts/value models, соответствующие M1. Затем ввести independent RNG streams, semantic fingerprints, attempt lifecycle и минимальный pipeline skeleton.

## M3 — Spatial foundation

World coordinates, Grid conversion, masks, distances, continuous fields и первый debug renderer.

## M4 — Constraint / layout engine

Generic geometry primitives `point`, `area`, `corridor`, `band`; `RegionSet`; SpatialSelector; evaluators/predicates для distance, containment, crossing, adjacency/overlap; generation of `LayoutCandidate` and `PlacementReservation`.

## M5 — Elevation v0.1

Base field, additive terrain contributions, shaping phase, coherent/ridged noise, mountains/hills/plains/gorges без scenario-specific special cases.

## M6 — Hydrology v0.1

Depression analysis, conditioned routing surface, flow direction, flow accumulation, catchments, stream extraction, directed river network, lakes и canonical `water_depth`. Canonical elevation не изменяется; domain edge — open boundary, не автоматически море.

## M7 — Surface v0.1

Continuous canonical fields `moisture` и `vegetation_density` из terrain/hydrology плюс explicit surface-feature biases. Полноценная temperature/climate biome model не входит в v0.1.

## M8 — Generic dependent feature placement

Suitability-based final placement point POI/dependent features внутри `PlacementReservation` после physical geography с hard SiteProfile requirements и intrinsic preferences. User soft constraints остаются global candidate ranking signals.

## M9 — Validation and ranking

Staged engine invariants; hard constraints reject; soft constraints ranking via worst effective violation and weighted mean; deterministic tie-break by lower `attempt_index`.

## M10 — Stable outputs

Stable `manifest.json`, `domain.json`, canonical/derived array storage и debug/preview outputs. Preview не source of truth.

## M11 — Acceptance suite

Набор fixed specs/seeds: minimal domain, random domain, isolated capability tests и несколько ненормативных complex examples. Examples могут иллюстрировать разные жанры, но не создают setting dependencies Core.

# Вне Core 0.1

Road networks, full human geography, artistic styling, ImageGen, battlemap, economy, NPC, full climate/biome model, deferred-to-deferred placement graph и setting/campaign/game-system-specific extensions откладываются или реализуются внешними слоями.
