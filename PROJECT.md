---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-dependent-placement-site-selection-design-v0.1
next_topic: terrain-state-canonical-elevation
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
  - generic-resolved-parameter-sampling-v0.1
  - triangular-sampler-rng-v1-mapping
  - corridor-layout-generation-v0.1
  - corridor-layout-validation-v0.1
  - band-layout-generation-v0.1
  - band-width-profile-v0.1
  - band-layout-validation-v0.1
  - area-layout-generation-v0.1
  - area-layout-validation-v0.1
  - area-point-spatial-evaluators-v0.1
  - shapely-geos-boolean-backend-v0.1
  - canonical-region-set-conversion-v0.1
  - placement-reservation-materialization-v0.1
accepted_designs:
  - dependent-placement-site-selection-v0.1
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
  placement_reservations: docs/design/placement-reservation-materialization-v0.1.md
  dependent_placement: docs/design/dependent-placement-site-selection-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Базовая canonical layout geometry Core 0.1 покрывает point, corridor, band и area. Поверх concrete geometry реализован `PlacementReservation` для deferred point POI. Семантика финального dependent placement принята и документирована, но runtime implementation отложена до появления upstream terrain/hydrology/surface states.

### Layout + PlacementReservation

- point — deterministic point inside domain;
- corridor — ordered polyline с isolated start/end/control-point RNG streams;
- band — corridor-like centerline + deterministic full-width profile;
- area — simple CCW polygon без holes, generated через radial construction, но serialized только как boundary;
- reservation — canonical `RegionSet` для deferred point POI через hard `inside/outside/near/far_from` semantics.

Boolean geometry backend — exact pinned `shapely==2.1.2` / GEOS 3.13.1. Shapely objects не входят в contracts или serialized artifacts.

### Dependent placement site selection — accepted design, not implemented

Normative semantics: `docs/design/dependent-placement-site-selection-v0.1.md`.

Принято:

- candidate sites строятся в world coordinates через rotated lattice, а не как raster-cell centers;
- `candidate_spacing_km` и `near_best_delta` — semantic resolved operator parameters;
- отдельные placement RNG streams для lattice rotation, phase и final weighted choice;
- candidates canonical-сортируются по `(x_km, y_km)`;
- `SiteProfile.footprint_radius_km` задаёт circular site footprint;
- hard requirements фильтруют invalid sites;
- intrinsic preferences дают score `[0,1]` через `maximize/minimize/preferred_range`;
- composite suitability — weighted mean preference scores;
- near-best set: `suitability >= best - near_best_delta`;
- final point выбирается deterministic weighted choice из near-best;
- отсутствие valid sites отклоняет весь attempt без hidden retry;
- final geometry хранится в runtime `PlacementState`, а не мутирует `LayoutCandidate`.

Implementation placement намеренно блокируется до фиксации numerical semantics upstream fields и site metrics.

## Следующий шаг

Следующий реализуемый bounded vertical slice — **TerrainState + canonical elevation baseline**.

До кода нужно отдельно принять:

- runtime representation `TerrainState`;
- baseline elevation field semantics и units;
- cell-center world coordinate mapping;
- минимальный первый terrain operator;
- additive contribution ordering/combination;
- terrain validation invariants;
- какие RNG streams нужны terrain operator'у, а какие операции deterministic.

Цель первого terrain slice — получить реальный canonical `elevation` field из `GenerationPlan + LayoutCandidate`, не переходя пока к hydrology, surface или dependent placement.

## Ещё не сделано

- dependent placement final point selection runtime;
- terrain/hydrology/surface generators;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators;
- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
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
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей стадии, а не hidden side effect позднего объекта.

## Правило совместной работы

Перед существенным изменением архитектуры сначала объяснить предлагаемое изменение, затрагиваемые решения и последствия; после принятия обновить документацию и только затем реализацию.

В конце каждого milestone или значимого checkpoint обновлять: что принято, что реализовано, что остаётся открытым и какой вопрос следующий.
