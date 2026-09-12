---
id: DESIGN-SOFT-CONSTRAINT-COMPILATION-SCORING-0.1
kind: design
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Soft Constraint Compilation & Scoring v0.1

Этот документ фиксирует принятую семантику компиляции и оценки пользовательских `soft` spatial constraints в Core 0.1.

## 1. Назначение

`hard` constraint отвечает на вопрос: допустим ли candidate. Нарушение hard constraint отклоняет attempt.

`soft` constraint отвечает на вопрос: насколько хорошо уже валидный complete candidate удовлетворяет пользовательскому предпочтению. Soft constraint не делает candidate невалидным и участвует только в global ranking valid attempts.

```text
final geometry
    -> canonical spatial measurement
    -> hard predicate -> pass/reject
    -> soft scoring   -> score [0,1]
    -> ranking valid attempts
```

Soft scoring не вводит альтернативную геометрическую семантику: hard и soft variants одной relation используют один и тот же canonical spatial evaluator.

## 2. Контракт `CompiledScoring`

`GenerationPlan.CompiledScoring` использует:

- `type` — тип scoring function;
- `ideal` — measurement, начиная с которого preference получает `score = 1` в направлении улучшения;
- `worst` — measurement, начиная с которого preference получает `score = 0` в направлении ухудшения.

Для монотонных scoring recipes Core 0.1 использует линейную интерполяцию между `ideal` и `worst` и saturation вне этого диапазона.

### 2.1. Чем больше, тем лучше

При `ideal > worst`:

```text
score = clamp((measurement - worst) / (ideal - worst), 0, 1)
```

### 2.2. Чем меньше, тем лучше

При `ideal < worst`:

```text
score = clamp((worst - measurement) / (worst - ideal), 0, 1)
```

`clamp(x, 0, 1)` гарантирует normalized `score`.

## 3. Degenerate threshold: `ideal == worst`

Равные границы допустимы и не требуют epsilon.

Для decreasing semantics:

```text
measurement <= ideal -> 1
measurement >  ideal -> 0
```

Для increasing semantics:

```text
measurement >= ideal -> 1
measurement <  ideal -> 0
```

Отдельный special case существует только для strict-positive crossing, описанного ниже.

## 4. Компиляция relations Core 0.1

Soft relation компилируется в тот же `CompiledEvaluator`, что и hard relation, но вместо `CompiledPredicate` получает `CompiledScoring` и `weight`.

| relation | evaluator | scoring direction | ideal | worst |
|---|---|---|---:|---:|
| `near` | `distance` | меньше лучше | `0 km` | `max_distance_km` |
| `far_from` | `distance` | больше лучше | `min_distance_km` | `0 km` |
| `inside` | `contained_fraction` | больше лучше | `1.0` | `0.0` |
| `outside` | `overlap_fraction` | меньше лучше | `0.0` | `1.0` |
| `overlaps` | `overlap_fraction` | больше лучше | `minimum_fraction` | `0.0` |
| `adjacent` | `distance` | меньше лучше | `0 km` | `max_gap_km` |
| `crosses` | `crossing_length` | больше лучше | `minimum_crossing_length_km` | `0 km` |

Для `near` параметр `max_distance_km` в soft mode является scale ухудшения preference: `0 km -> 1`, `max_distance_km -> 0`, большее расстояние остаётся `0`.

Для `far_from` значение `min_distance_km` является границей полного удовлетворения: `0 km -> 0`, `min_distance_km -> 1`, большее расстояние остаётся `1`.

Для `overlaps` `minimum_fraction` является границей полного удовлетворения, а не hard threshold.

## 5. `crosses` при нулевом minimum

Hard relation уже различает strict crossing от `>= 0`: если `minimum_crossing_length_km` отсутствует или равен `0`, crossing существует только при положительной длине.

Soft Core 0.1 сохраняет эту семантику отдельным scoring recipe:

```text
type = positive
measurement > 0 -> 1
measurement = 0 -> 0
```

Если `minimum_crossing_length_km > 0`, используется обычный increasing linear scoring:

```text
0 -> 0
minimum_crossing_length_km -> 1
выше minimum -> 1
```

## 6. Weight и individual result

Каждый soft constraint имеет `weight` в `(0,1]`; default равен `1.0`.

Для результата:

```text
effective_violation = (1 - score) * weight
```

`SoftConstraintResult` хранит:

- `constraint_id`;
- `score`;
- `weight`;
- `effective_violation`;
- canonical `measurement`.

Soft results сериализуются в canonical lexical order по `constraint_id`.

## 7. Aggregate ranking

Только complete candidate, прошедший engine invariants и все hard constraints, получает ranking.

Если soft constraints есть:

```text
worst_effective_violation = max((1 - score_i) * weight_i)

weighted_mean_score =
    sum(score_i * weight_i) / sum(weight_i)
```

Если soft constraints отсутствуют, сохраняется neutral ranking:

```text
worst_effective_violation = 0.0
weighted_mean_score = 1.0
```

Global candidate ordering не меняется:

1. меньше `worst_effective_violation`;
2. при равенстве больше `weighted_mean_score`;
3. при полном равенстве меньше `attempt_index`.

Таким образом сначала минимизируется худшее взвешенное нарушение, затем оптимизируется среднее качество.

## 8. Deferred-to-deferred soft constraints

Soft constraint между двумя deferred features разрешён, если их финальные геометрии доступны в Final Validation и существующий canonical spatial evaluator поддерживает соответствующую пару geometry/reference.

Это не создаёт generation dependency: обе финальные реализации сначала материализуются независимо, затем Final Validation только измеряет готовую geometry.

Hard deferred-to-deferred dependency остаётся запрещённой текущим compiler slice, поскольку hard constraint может требоваться для построения reservation до materialization обоих объектов.

## 9. Capability boundary

Soft scoring не добавляет новых spatial measurements.

Если relation/evaluator/reference combination не поддерживается существующим canonical spatial evaluator, compilation или Final Validation завершается explicit capability error. Запрещены:

- silent ignore;
- скрытая замена evaluator-а;
- approximate fallback с иной семантикой;
- второй независимый distance/overlap/crossing implementation только для soft mode.

## 10. Граница с `SiteProfile.preferences`

`SiteProfile.preferences` и user soft constraints имеют разную область действия.

```text
SiteProfile.preferences
    -> выбор site внутри одного attempt

user soft constraints
    -> сравнение complete valid attempts между собой
```

Intrinsic placement suitability не превращается автоматически в global soft result и не входит повторно в `RankingResult`.

## 11. Stage semantics

Soft scoring выполняется только в Final Validation, после сборки temporary final geometry view.

Final Validation:

1. проверяет upstream completeness и engine invariants;
2. вычисляет все hard constraints;
3. если hard gate пройден, вычисляет все soft constraints;
4. строит `RankingResult`;
5. не использует RNG, IO и mutation.

При hard rejection soft evaluation не требуется, потому что rejected candidate не участвует в ranking.

## 12. Детерминизм

Scoring является чистой функцией от:

- compiled constraint;
- canonical final geometry measurement.

Он не использует RNG и не зависит от evaluation order. Canonical output order определяется `constraint_id`.

## 13. Scope implementation checkpoint

Implementation v0.1 включает:

- compiler support для soft variants существующих relations;
- `CompiledScoring` recipes `linear_increasing`, `linear_decreasing`, `positive`;
- shared soft evaluator поверх canonical spatial measurement boundary;
- Final Validation soft results;
- aggregate `RankingResult`;
- deferred-to-deferred soft evaluation, когда geometry evaluator поддерживает пару;
- tests на boundaries, saturation, equal thresholds, weight, aggregate ranking, canonical ordering и capability errors.

Не входят:

- новые spatial relations;
- новые geometry evaluators;
- nonlinear curves;
- пользовательские custom scoring functions;
- изменение attempt-selection protocol;
- включение `SiteProfile.preferences` в global ranking;
- DomainData assembly, exporter или renderer.
