---
project: domain_generator
target_version: core-0.1
phase: data-contracts
status: in-progress
current_milestone: M1-data-contracts
checkpoint: M1-contracts-checkpoint-1
next_topic: poi-suitability-v0.1
completed:
  - M0-project-foundation
accepted_m1_topics:
  - domain-size-and-grid
  - world-coordinate-convention
  - feature-preset-model
  - constraint-and-spatial-selector-model
  - parameter-domain-and-sampling-model
  - preset-registry-boundary
  - generation-plan-role
  - layout-candidate-role
  - placement-reservations
  - domain-data-bundle-model
  - canonical-derived-debug-data
  - staged-validation-and-ranking
  - terrain-generation-baseline
  - hydrology-generation-baseline
  - surface-generation-baseline
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в исполняемый план и создаёт детерминированный структурированный результат.

## Текущее состояние

`M0 — Project foundation` завершён и принят.

`M1 — Data contracts` продолжается. Текущий checkpoint фиксирует уже принятые решения, но не закрывает M1. Реализация генератора ещё не начата.

Приняты базовые роли `DomainSpec`, `GenerationPlan`, `LayoutCandidate`, `PlacementReservation` и `DomainData`; модель presets/constraints; координаты мира и grid; базовые решения Terrain/Hydrology/Surface; staged validation и ranking.

## Следующий вопрос

`POI suitability v0.1`: hard site requirements, preference fields и детерминированный выбор конкретного места внутри `PlacementReservation`.

## Что ещё не сделано

- JSON Schema контрактов;
- Python package и runtime-модели;
- `POI suitability v0.1`;
- окончательное закрытие `DomainSpec v0.1`, `GenerationPlan v0.1`, `DomainData v0.1`;
- deterministic RNG implementation;
- генераторы terrain/hydrology/surface;
- tests, renderers и GitHub Actions.

## Инварианты

- **INV-001:** Core независим от ChatGPT/OpenAI, GitHub Actions, конкретного чата, лора Вальхаллы и renderer.
- **INV-002:** `DomainSpec` описывает намерение; `GenerationPlan` — resolved recipe; `DomainData` — итоговый мир.
- **INV-003:** одинаковые поддерживаемые `DomainSpec + root seed + generator version` дают одинаковый результат.
- **INV-004:** illustrative examples ненормативны и не могут молча становиться правилами Core.
- **INV-005:** Core использует generic fields, networks, features, geometry primitives и constraints вместо campaign-specific special cases.
- **INV-006:** существенные архитектурные изменения сначала объясняются и обсуждаются; документация обновляется до реализации.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
