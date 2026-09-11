---
id: ADR-0007
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
---

# ADR-0007: Staged contracts, dependent placement and validation

## Context

Один объект данных не должен одновременно представлять пользовательское намерение, конкретную попытку layout и окончательный мир. Dependent features нельзя окончательно размещать до появления физической географии, а validation не должна скрытно чинить результат.

## Decision

Используется цепочка:

```text
DomainSpec
-> GenerationPlan
-> LayoutCandidate
-> physical generation
-> dependent feature placement
-> ValidationResult
-> DomainData
```

- `GenerationPlan` хранит resolved recipes, parameter domains и compiled predicates, но не concrete attempt geometry.
- `LayoutCandidate` хранит concrete macro geometry structural features и `PlacementReservation` для dependent features.
- `PlacementReservation` задаёт допустимую область, а окончательная geometry dependent feature выбирается после terrain/hydrology/surface по suitability.
- Если подходящего места нет, candidate отклоняется; terrain/validator не обязаны изменять мир под POI.
- Validation staged: ранние failures отбрасываются до дорогих стадий.
- Engine invariants обязательны; hard constraint failure не компенсируется.
- Soft ranking сначала учитывает худшее effective violation, затем weighted mean.
- Validator только измеряет/оценивает и не модифицирует candidate.

`DomainData` отделён от физического `DomainBundle`; canonical, derived и debug/internal data имеют разные роли.

## Consequences

Причина неудачного результата локализуется по стадии, replay/debug становятся возможны, а требования пользователя не смешиваются со случайно выбранными параметрами конкретной попытки.