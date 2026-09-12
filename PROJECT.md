---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-point-layout-v0.1
next_topic: corridor-layout-semantics
completed:
  - M0-project-foundation
  - M1-data-contracts
implemented_m2:
  - minimal-python-package
  - serialized-contract-layer-v0.1
  - generated-json-schema-v0.1
  - deterministic-rng-protocol-v1
  - xoshiro256starstar-v1
  - attempt-pipeline-skeleton-v0.1
  - deterministic-candidate-ranking-v0.1
  - typed-preset-definition-v0.1
  - in-memory-preset-registry-boundary
  - deterministic-domain-spec-compiler-slice
  - semantic-plan-fingerprint
  - point-layout-generation-v0.1
  - point-layout-validation-v0.1
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

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Уже реализованы serialized Pydantic contracts, JSON Schema snapshots, deterministic RNG v1, attempt orchestrator, deterministic candidate ranking и минимальный compiler/preset-registry boundary.

Первый настоящий procedural vertical slice — generic point layout — зафиксирован в `docs/design/point-layout-v0.1.md` и реализует:

- `GenerationPlan -> LayoutCandidate` для `layout.mode=geometry`, `shape=point`;
- независимый RNG stream на feature с namespace `feature/<id>/geometry/point`, purpose `position`;
- ровно два `uniform01()` draw на concrete `(x_km, y_km)`;
- отсутствие hidden retries и constraint-aware steering;
- semantic `plan_fingerprint` в `LayoutCandidate.source_plan`;
- layout engine invariants для plan fingerprint, attempt index, полного набора point features и domain bounds;
- hard point-to-point distance;
- hard point-to-rectangle distance;
- point-in-rectangle `contained_fraction` / `overlap_fraction`;
- `ValidationResult(stage=layout)` и StageHandler adapter для существующего attempt orchestrator.

Geometry shapes кроме point и placement reservations пока явно unsupported, а не аппроксимируются. Soft constraint scoring также пока не реализован.

## Следующий шаг

Перед реализацией второй procedural geometry path отдельно определить deterministic semantics для `corridor`: как выбираются endpoints/control points, какие layout parameters действительно нужны и где проходит granularity RNG streams. После принятия подключить corridor к существующему layout generator/validator без специальных content rules.

## Ещё не сделано

- corridor/band/area layout generation;
- placement reservation materialization и RegionSet boolean operations;
- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
- terrain/hydrology/surface/dependent-placement generators;
- DomainData assembler/export bundle;
- renderer и GitHub Actions.

## Инварианты

- **INV-001:** Core независим от ChatGPT/OpenAI, GitHub Actions, конкретного чата, лора Вальхаллы и renderer.
- **INV-002:** `DomainSpec` описывает намерение; `GenerationPlan` — resolved recipe; `DomainData` — итоговый мир.
- **INV-003:** одинаковые поддерживаемые semantic inputs при одной версии генератора дают воспроизводимый результат.
- **INV-004:** illustrative examples ненормативны и не могут молча становиться правилами Core.
- **INV-005:** Core использует generic fields, networks, features, geometry primitives и constraints вместо campaign-specific special cases.
- **INV-006:** существенные архитектурные изменения сначала объясняются и обсуждаются; документация обновляется до реализации.
- **INV-007:** RNG streams адресуются стабильными semantic namespaces и не зависят от порядка выполнения или random draws соседних подсистем.
- **INV-008:** logging, debug export, instrumentation и preview generation не влияют на semantic result.
- **INV-009:** exact procedural replay определяется exact generator version; стабильность generated world между generator versions не гарантируется.
- **INV-010:** каждая stage читает только declared upstream outputs и не мутирует результаты предыдущих stages.
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей stage, а не hidden side effect позднего объекта.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
