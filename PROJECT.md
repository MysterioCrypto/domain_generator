---
project: domain_generator
target_version: core-0.1
phase: implementation
status: in-progress
current_milestone: M2-deterministic-pipeline
checkpoint: M2-placement-reservation-materialization-v0.1
next_topic: dependent-placement-site-selection
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
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  design_baseline: docs/design/core-0.1-generation-baseline.md
  placement_reservations: docs/design/placement-reservation-materialization-v0.1.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

Этот файл — короткая каноническая точка входа для нового чата или агента.

## Цель

Создать независимое процедурное ядро генерации доменов с управляемой случайностью. Пользователь описывает намерение и ограничения; Core компилирует их в executable plan и создаёт детерминированный structured result.

## Текущее состояние

`M0 — Project foundation` и `M1 — Data contracts` завершены. `M2 — Deterministic pipeline` находится в реализации.

Базовая canonical layout geometry Core 0.1 покрывает все четыре primitive: point, corridor, band и area. Поверх concrete geometry теперь добавлен первый deferred-layout слой — `PlacementReservation` для point POI.

### Point / corridor / band / area

- point — deterministic point inside domain;
- corridor — ordered polyline с isolated start/end/control-point RNG streams;
- band — corridor-like centerline + deterministic full-width profile;
- area — simple CCW polygon без holes, generated через radial construction, но serialized только как boundary.

Подробные normative semantics лежат в `docs/design/*-layout-v0.1.md`.

### Parameter sampling

Runtime sampler поддерживает `fixed`, float `uniform`, inclusive `integer_uniform`, `categorical` и float `triangular`. Triangular inverse-CDF mapping является частью RNG v1 semantics.

### PlacementReservation

Normative semantics зафиксированы в `docs/design/placement-reservation-materialization-v0.1.md`.

Реализовано:

- reservation только для deferred POI с final point shape;
- initial allowed region = весь rectangular domain;
- hard `inside` -> intersection;
- hard `outside` -> difference;
- hard `near` -> intersection с fixed-semantics buffer;
- hard `far_from` -> difference fixed-semantics buffer;
- targets: literal point/rectangle, point feature, corridor whole/start/end/center, area whole/boundary/center, band start/end/center;
- `band.whole`/`band.boundary` остаются capability errors до footprint materialization;
- deferred feature как constraint target не поддержан в Core 0.1;
- constraints применяются deterministic order по id;
- `source_constraints` хранит реально применённые hard constraint ids;
- empty RegionSet структурно валиден, но layout validation отклоняет attempt;
- soft constraints не изменяют reservation;
- reservation materialization не использует RNG.

### Boolean geometry backend

Внутренний backend — exact pinned `shapely==2.1.2` / GEOS. Shapely objects не входят в contracts или serialized artifacts.

Buffer semantics явно фиксированы (`quad_segs=8`, round caps/joins), а результат преобразуется в собственный canonical `RegionSet`:

- outer CCW;
- holes CW;
- deterministic ring start;
- deterministic hole/polygon ordering;
- empty geometry -> empty RegionSet;
- lower-dimensional overlay remnants отбрасываются.

Никакого precision snapping/rounding в v0.1 нет.

### Layout stage

Новый `layout_stage` объединяет:

```text
concrete geometry generation
-> placement reservation materialization
-> unified layout validation
```

Старый `geometry_layout_stage` сохраняется как узкий concrete-geometry handler/regression boundary.

## Следующий шаг

После materialized reservation следующий bounded слой — **dependent placement site selection**: как из `allowed_region` и `SiteProfile` строятся valid sites, как оцениваются requirements/preferences и каким deterministic RNG stream выбирается одна финальная point position.

Перед реализацией нужно отдельно зафиксировать site candidate representation/resolution, metric evaluators и near-best weighted selection semantics. Нельзя молча привязывать placement к raster cell centers или конкретной sampling density.

## Ещё не сделано

- dependent placement final point selection;
- band polygon footprint materialization;
- general area↔area polygon boolean evaluators;
- YAML/file preset loader и production preset catalog;
- soft constraint scoring compilation;
- terrain/hydrology/surface generators;
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
