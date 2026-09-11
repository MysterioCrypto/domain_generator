---
id: ROADMAP-CORE-0.1
kind: roadmap
status: active
normative: true
target: core-0.1
---

# Roadmap Core 0.1

## M0 — Project foundation

Зафиксировать память проекта, архитектурные границы, glossary, ADR и правила совместной работы.

**Готово, когда:** новый чат может восстановить состояние проекта из репозитория без чтения старого диалога.

## M1 — Data contracts

Определить `DomainSpec v0.1`, `GenerationPlan v0.1`, `DomainData v0.1`, базовые типы `Field`, `Network`, `Feature`, `Constraint` и схемы валидации.

## M2 — Deterministic pipeline

Ввести стадии генерации и независимые RNG-потоки, производные от root seed и stage id.

## M3 — Spatial foundation

Координаты домена, расчётная сетка, маски, расстояния, непрерывные поля и первый debug renderer.

## M4 — Constraint / layout engine

Общие примитивы `point`, `area`, `corridor`, `band` и отношения `near`, `inside`, `crosses`, `connects`, `endpoint_near`, `preferred_region`.

## M5 — Elevation v0.1

Базовый рельеф, influence fields, coherent/ridged noise, горы, холмы, равнины и ущелья без сценарных special cases.

## M6 — Hydrology v0.1

Depression handling, flow direction, flow accumulation, ручьи/реки, озёра, море/выход с карты и простое углубление русел.

## M7 — Surface v0.1

Простые поля влажности, температуры и растительности без полной климатической модели.

## M8 — Generic POI placement

Suitability-based размещение абстрактных POI после физической географии с учётом constraints.

## M9 — Validation and scoring

Hard constraints должны либо выполняться, либо отклонять candidate. Soft constraints влияют на score. Повторные attempts детерминированы.

## M10 — Stable outputs

Стабильные `manifest.json`, `domain.json`, статистика и debug PNG-слои.

## M11 — Acceptance suite

Набор фиксированных specs/seeds: минимальный домен, случайный домен, искусственные тесты отдельных возможностей и несколько ненормативных комплексных примеров.

# Вне Core 0.1

Дороги, полноценная человеческая география, художественная стилизация, ImageGen, battlemap, экономика, NPC и campaign-specific extensions откладываются на последующие версии.
