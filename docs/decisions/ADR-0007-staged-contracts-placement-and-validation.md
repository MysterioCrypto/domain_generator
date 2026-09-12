---
id: ADR-0007
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
---

# ADR-0007 — Поэтапные контракты, dependent placement и validation

## Контекст

Один объект данных не должен одновременно представлять пользовательское намерение, конкретную попытку layout и окончательный мир. Dependent features нельзя окончательно размещать до появления физической географии, а validation не должна скрыто исправлять результат.

## Решение

Используется цепочка:

```text
DomainSpec
-> GenerationPlan
-> LayoutCandidate
-> физическая генерация
-> размещение dependent features
-> ValidationResult
-> DomainData
```

- `GenerationPlan` хранит resolved recipes, domains параметров и compiled predicates, но не concrete geometry конкретного attempt.
- `LayoutCandidate` хранит конкретную macro geometry structural features и `PlacementReservation` для dependent features.
- `PlacementReservation` задаёт допустимую область, а окончательная geometry dependent feature выбирается после terrain/hydrology/surface по suitability.
- Если подходящего места нет, candidate отклоняется; terrain/validator не обязаны изменять мир под POI.
- Validation выполняется по стадиям: ранние failures отбрасываются до дорогих стадий.
- Engine invariants обязательны; нарушение hard constraint не компенсируется.
- Soft ranking сначала учитывает худшее `effective_violation`, затем weighted mean.
- Validator только измеряет и оценивает, но не модифицирует candidate.

`DomainData` отделён от физического `DomainBundle`; canonical, derived и debug/internal data имеют разные роли.

## Следствия

Причина неудачного результата локализуется по стадии, replay/debug становятся возможны, а требования пользователя не смешиваются со случайно выбранными параметрами конкретного attempt.
