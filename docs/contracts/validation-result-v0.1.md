---
id: CONTRACT-VALIDATIONRESULT-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# ValidationResult v0.1 — draft

`ValidationResult` — immutable serializable diagnostic result одной validation stage. Validator измеряет и оценивает candidate, но не модифицирует его.

## Корень

```yaml
validation_version: "0.1"
attempt_index: 7
stage: final

engine_invariants:
  passed: true
  results: []

hard_constraints:
  passed: true
  results: []

soft_constraints:
  results: []

ranking:
  worst_effective_violation: 0.08
  weighted_mean_score: 0.87
```

`stage` Core 0.1: `layout`, `terrain`, `hydrology`, `surface`, `placement`, `final`.

## Engine invariants

Engine invariants — обязательные внутренние требования Core, не происходящие из DomainSpec:

```yaml
engine_invariants:
  passed: false
  results:
    - id: no-nonfinite-elevation
      passed: false
      measured:
        invalid_cell_count: 14
      message: elevation contains non-finite values
```

Примеры stable invariant ids: field shape consistency, finite numeric data, valid river topology, valid final point location. Structural band footprint не обязан целиком помещаться внутри domain; его centerline остаётся внутри/on boundary, а effect клиппится domain.

## Hard constraints

```yaml
hard_constraints:
  passed: false
  results:
    - constraint_id: fort-near-gorge
      satisfied: false
      measurement:
        type: distance
        value: 4.8
        unit: km
      predicate:
        type: less_or_equal
        threshold: 3.0
```

Любой failed hard constraint отклоняет candidate. Hard results не имеют compensating score.

## Soft constraints

```yaml
soft_constraints:
  results:
    - constraint_id: mountains-near-center
      score: 0.82
      weight: 0.5
      effective_violation: 0.09
      measurement:
        type: distance
        value: 7.2
        unit: km
```

`score` нормализован в `[0,1]`. Soft `weight` находится в `(0,1]`, default `1.0`.

```text
effective_violation = (1 - score) * weight
```

Intrinsic `SiteProfile.preferences` используются для выбора site внутри одного candidate и не становятся автоматически global soft constraints.

## Ranking

Для valid complete candidate:

```yaml
ranking:
  worst_effective_violation: 0.09
  weighted_mean_score: 0.84
```

Порядок сравнения:

1. меньше `worst_effective_violation`;
2. при равенстве больше `weighted_mean_score`;
3. при полном равенстве меньше `attempt_index`.

Если soft constraints отсутствуют, neutral ranking: `worst_effective_violation = 0.0`, `weighted_mean_score = 1.0`.

Если candidate hard-failed или нарушил engine invariant, `ranking: null`.

Отдельное поле `status: accepted/rejected` не хранится: допустимость выводится из invariant/hard results и stage context.
