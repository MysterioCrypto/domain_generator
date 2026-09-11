---
id: ROADMAP-CORE-0.1
kind: roadmap
status: active
normative: true
target: core-0.1
---

# Roadmap Core 0.1

## M0 — Project foundation — DONE

Зафиксировать память проекта, архитектурные границы, glossary, ADR и правила совместной работы.

**Критерий:** новый чат может восстановить состояние проекта из репозитория без чтения старого диалога.

## M1 — Data contracts — IN PROGRESS

Определить `DomainSpec v0.1`, `GenerationPlan v0.1`, `LayoutCandidate`, `PlacementReservation`, `DomainData v0.1`, базовые типы `Field`, `Network`, `Feature`, `Constraint`, parameter domains и staged validation model.

Текущий checkpoint: приняты координаты/grid, feature/preset/operator model, spatial selectors/constraints, plan/layout/data roles, placement reservations, validation ranking и design baselines Terrain/Hydrology/Surface. Следующий открытый вопрос: `POI suitability v0.1`.

**Готово, когда:** контракты согласованы, имеют draft schemas/пример и достаточны для начала реализации без скрытых архитектурных решений.

## M2 — Deterministic pipeline

Ввести стадии генерации и независимые RNG-потоки, производные от root seed, stage, feature/purpose и attempt.

## M3 — Spatial foundation

World coordinates, Grid conversion, маски, расстояния, continuous fields и первый debug renderer.

## M4 — Constraint / layout engine

Общие geometry primitives `point`, `area`, `corridor`, `band`; SpatialSelector; generic evaluators/predicates для distance, containment, intersection, adjacency/overlap и related constraints; generation of `LayoutCandidate` и `PlacementReservation`.

## M5 — Elevation v0.1

Base field, additive terrain contributions, shaping phase, coherent/ridged noise, горы, холмы, равнины и ущелья без scenario-specific special cases.

## M6 — Hydrology v0.1

Depression analysis, conditioned routing surface, flow direction, flow accumulation, catchments, stream extraction, river network и lakes. Canonical elevation в v0.1 гидрологией не изменяется; край домена — open boundary, а не автоматически море.

## M7 — Surface v0.1

Простые continuous fields `moisture` и `vegetation_density` из terrain/hydrology плюс explicit surface-feature biases. Полноценная температура/климатические биомы не входят в v0.1.

## M8 — Generic dependent feature placement

Suitability-based окончательное размещение POI/dependent features внутри `PlacementReservation` после физической географии с учётом hard site requirements и preferences.

## M9 — Validation and ranking

Staged engine invariants; hard constraints либо выполняются, либо отклоняют candidate; soft constraints ранжируются через worst effective violation и weighted mean. Повторные attempts детерминированы.

## M10 — Stable outputs

Стабильные `manifest.json`, `domain.json`, canonical/derived array storage и debug/preview outputs. Preview не является source of truth.

## M11 — Acceptance suite

Набор фиксированных specs/seeds: минимальный домен, случайный домен, искусственные тесты отдельных возможностей и несколько ненормативных комплексных examples.

# Вне Core 0.1

Дороги, полноценная человеческая география, художественная стилизация, ImageGen, battlemap, экономика, NPC, полноценная climate/biome model и campaign-specific extensions откладываются на последующие версии.