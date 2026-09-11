---
id: ADR-0008
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
implemented: false
---

# ADR-0008 — Deterministic execution and stage boundaries

## Context

Core должен воспроизводить procedural result, позволять ранний reject кандидатов, поддерживать независимые stochastic subsystems и оставаться отлаживаемым при росте pipeline. Global mutable RNG, hidden retries и backward mutation делают результат зависимым от порядка вызовов и трудно воспроизводимым.

## Decision

### Stable identities

- top-level `DomainSpec.id` не участвует в RNG;
- feature `id` — stable machine identity для references и RNG namespace;
- cosmetic naming используется через optional `label`;
- смена `label` не должна менять RNG realization, смена feature `id` может.

### Attempt semantics

Один `attempt_index` — одна независимая realization immutable `GenerationPlan`.

- hidden stage-local retries запрещены в Core 0.1;
- early hard failure прекращает текущий attempt;
- late hard failure отклоняет весь attempt;
- attempts не адаптируются на основании предыдущих failures;
- execution budget (`max_attempts`, `target_valid_candidates`) находится в semantic `GenerationConfig`.

### RNG derivation

Child RNG streams выводятся независимо из versioned semantic namespace:

```text
root_seed
+ attempt_index
+ stable stage id
+ stable scope
+ stable purpose
-> rng derivation v1
-> local child seed / RNG
```

Requirements:

- никакого global mutable RNG;
- никакого Python `hash()` как persistence contract;
- module/function names не входят в namespace;
- unrelated random draws и порядок features не сдвигают соседние streams;
- parameter values не включаются в namespace; sampler отображает тот же deterministic variate в текущий allowed domain;
- debug/logging/preview не потребляют semantic RNG и не меняют result.

### Replay/versioning

Exact procedural replay требует одинаковых:

```text
DomainSpec semantics
+ root seed
+ semantic GenerationConfig
+ exact generator version
```

Стабильность generated world между разными generator versions не гарантируется. Старый результат сохраняется как `DomainData`; историческая regeneration выполняется старым tagged release. `rng_version` версионируется отдельно от generator/schema contracts.

### Stage causality

Core stages образуют upstream-only DAG. Stage читает только объявленные upstream outputs и не мутирует outputs предыдущих stages.

Запрещены скрытые зависимости вида:

- Surface -> mutate Terrain;
- POI placement -> mutate Terrain/Hydrology;
- Validator -> mutate Candidate;
- Hydrology -> silently regenerate Terrain;
- Renderer -> mutate DomainData;
- Compiler -> inspect generated world.

Если поздний semantic object должен влиять на ранний слой мира, эффект выражается отдельным feature/constraint соответствующей стадии.

## Consequences

Плюсы:

- воспроизводимые independent streams;
- добавление нового unrelated random draw не reroll'ит весь мир;
- attempts легко replay/debug;
- stage tests можно запускать на фиксированных upstream inputs;
- будущая incremental execution может использовать тот же DAG без изменения semantics.

Цена:

- Core 0.1 иногда пересоздаёт полный downstream candidate после позднего failure вместо локального retry;
- feature IDs становятся частью stable procedural identity;
- exact replay требует фиксации generator/runtime versioning.

## Added invariants

- **INV-007:** RNG streams адресуются стабильными семантическими namespace и не зависят от порядка выполнения или random draws соседних подсистем.
- **INV-008:** observability, logging, debug export и preview generation не влияют на semantic generation result.
- **INV-009:** exact procedural replay определяется точной версией generator; стабильность generated world между generator versions не гарантируется.
- **INV-010:** stage читает только явно объявленные upstream outputs и не мутирует результаты предыдущих stages.
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей стадии, а не hidden side effect позднего объекта.
