---
project: domain_generator
target_version: core-0.1
phase: data-contracts
status: in-progress
current_milestone: M1-data-contracts
checkpoint: M1-contracts-checkpoint-2
next_topic: layout-candidate-v0.1
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
  - poi-suitability-v0.1
  - attempt-model-v0.1
  - deterministic-rng-namespaces-v0.1
  - versioning-and-replay-v0.1
  - core-stage-dependency-dag
  - python-data-model-v0.1
  - domain-spec-v0.1-design
  - generation-plan-v0.1-design
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в исполняемый план и создаёт детерминированный структурированный результат.

## Текущее состояние

`M0 — Project foundation` завершён и принят.

`M1 — Data contracts` продолжается. Второй checkpoint фиксирует принятые решения до точной проработки `LayoutCandidate v0.1`; реализация генератора ещё не начата.

По смыслу уже закрыты дизайн `DomainSpec v0.1` и `GenerationPlan v0.1`, POI suitability, attempts, RNG namespaces, replay/versioning, dependency DAG и граница Python-моделей. Контрактные документы остаются `draft` до закрытия M1 и реализации схем.

## Следующий вопрос

`LayoutCandidate v0.1`: точный сериализуемый формат macro geometry (`point`, `corridor`, `band`, `area`) и `PlacementReservation` для deferred features.

После него: точный `DomainData v0.1`, затем закрытие M1 и первая реализация Python contracts.

## Что ещё не сделано

- точный `LayoutCandidate v0.1`;
- окончательная сверка `DomainData v0.1`;
- JSON Schema контрактов;
- Python package и runtime-модели;
- deterministic RNG implementation;
- генераторы terrain/hydrology/surface/placement;
- tests, renderers и GitHub Actions.

## Инварианты

- **INV-001:** Core независим от ChatGPT/OpenAI, GitHub Actions, конкретного чата, лора Вальхаллы и renderer.
- **INV-002:** `DomainSpec` описывает намерение; `GenerationPlan` — resolved recipe; `DomainData` — итоговый мир.
- **INV-003:** одинаковые поддерживаемые semantic inputs при одной версии генератора дают воспроизводимый результат.
- **INV-004:** illustrative examples ненормативны и не могут молча становиться правилами Core.
- **INV-005:** Core использует generic fields, networks, features, geometry primitives и constraints вместо campaign-specific special cases.
- **INV-006:** существенные архитектурные изменения сначала объясняются и обсуждаются; документация обновляется до реализации.
- **INV-007:** RNG streams адресуются стабильными семантическими namespace и не зависят от порядка выполнения или random draws соседних подсистем.
- **INV-008:** logging, debug export, instrumentation и preview generation не влияют на семантический результат.
- **INV-009:** exact procedural replay определяется точной версией генератора; стабильность generated world между версиями не гарантируется.
- **INV-010:** каждая стадия Core читает только явно объявленные upstream outputs и не мутирует результаты предыдущих стадий.
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей стадии, а не скрытым side effect позднего объекта.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
