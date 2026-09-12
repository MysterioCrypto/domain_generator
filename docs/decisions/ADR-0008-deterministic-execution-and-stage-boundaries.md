---
id: ADR-0008
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
implemented: false
---

# ADR-0008 — Детерминированное исполнение и границы стадий

## Контекст

Core должен воспроизводить процедурный результат, позволять раннее отклонение кандидатов, поддерживать независимые стохастические подсистемы и оставаться отлаживаемым по мере роста pipeline. Глобальный mutable RNG, скрытые retries и обратная мутация делают результат зависимым от порядка вызовов и трудно воспроизводимым.

## Решение

### Стабильные идентификаторы

- верхнеуровневый `DomainSpec.id` не участвует в RNG;
- feature `id` — стабильный машинный идентификатор для references и RNG namespace;
- косметическое имя задаётся необязательным `label`;
- смена `label` не должна менять RNG realization, смена feature `id` может.

### Семантика attempt

Один `attempt_index` — одна независимая realization неизменяемого `GenerationPlan`.

- скрытые локальные retries внутри стадий запрещены в Core 0.1;
- ранний hard failure прекращает текущий attempt;
- поздний hard failure отклоняет весь attempt;
- attempts не адаптируются на основании предыдущих failures;
- бюджет исполнения (`max_attempts`, `target_valid_candidates`) находится в semantic `GenerationConfig`.

### Вывод RNG

Дочерние RNG streams выводятся независимо из versioned semantic namespace:

```text
root_seed
+ attempt_index
+ stable stage id
+ stable scope
+ stable purpose
-> rng derivation v1
-> local child seed / RNG
```

Требования:

- никакого глобального mutable RNG;
- никакого Python `hash()` как persistence contract;
- имена module/function не входят в namespace;
- несвязанные random draws и порядок features не сдвигают соседние streams;
- значения parameters не включаются в namespace; sampler отображает тот же deterministic variate в текущий допустимый domain;
- debug/logging/preview не потребляют semantic RNG и не меняют результат.

### Replay и versioning

Точный procedural replay требует одинаковых:

```text
семантика DomainSpec
+ root seed
+ semantic GenerationConfig
+ exact generator version
```

Стабильность generated world между разными версиями generator не гарантируется. Старый результат сохраняется как `DomainData`; историческая regeneration выполняется старым tagged release. `rng_version` версионируется отдельно от generator/schema contracts.

### Причинность между стадиями

Стадии Core образуют upstream-only DAG. Каждая stage читает только объявленные upstream outputs и не мутирует outputs предыдущих стадий.

Запрещены скрытые зависимости вида:

- Surface -> mutate Terrain;
- POI placement -> mutate Terrain/Hydrology;
- Validator -> mutate Candidate;
- Hydrology -> silently regenerate Terrain;
- Renderer -> mutate DomainData;
- Compiler -> inspect generated world.

Если поздний semantic object должен влиять на ранний слой мира, эффект выражается отдельным feature/constraint соответствующей стадии.

## Следствия

Плюсы:

- воспроизводимые независимые streams;
- добавление нового несвязанного random draw не приводит к reroll всего мира;
- attempts легко replay/debug;
- тесты стадий можно запускать на фиксированных upstream inputs;
- будущая incremental execution может использовать тот же DAG без изменения семантики.

Цена:

- Core 0.1 иногда пересоздаёт полный downstream candidate после позднего failure вместо локального retry;
- feature IDs становятся частью стабильной procedural identity;
- точный replay требует фиксации версий generator/runtime.

## Добавленные инварианты

- **INV-007:** RNG streams адресуются стабильными семантическими namespace и не зависят от порядка выполнения или random draws соседних подсистем.
- **INV-008:** observability, logging, debug export и preview generation не влияют на семантический результат генерации.
- **INV-009:** точный procedural replay определяется точной версией generator; стабильность generated world между версиями generator не гарантируется.
- **INV-010:** stage читает только явно объявленные upstream outputs и не мутирует результаты предыдущих стадий.
- **INV-011:** воздействие feature на более ранний слой мира выражается отдельным feature/constraint соответствующей стадии, а не скрытым side effect позднего объекта.
