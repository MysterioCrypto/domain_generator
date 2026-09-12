---
id: DESIGN-FINAL-VALIDATION-HARD-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Финальная валидация v0.1 — полная поддержка hard-ограничений

Этот checkpoint реализует production-стадию `FINAL` для реально поддерживаемого compiler slice: планов без пользовательских soft-ограничений.

## 1. Назначение

Финальная валидация наблюдает итоговое runtime-состояние одного attempt. Она ничего не генерирует, не мутирует результаты предыдущих стадий и не использует RNG.

```text
LayoutCandidate
TerrainState
HydrologyState
SurfaceState
PlacementState
        +
GenerationPlan
        ↓
представление финальной геометрии
        ↓
пользовательские hard-ограничения
        ↓
ValidationResult(stage=final)
```

## 2. Представление финальной геометрии

Structural features уже имеют конкретную геометрию в:

```text
LayoutCandidate.geometry_realizations[id]
```

Deferred point features имеют финальную геометрию в:

```text
PlacementState.final_points[id]
```

Стадия `FINAL` создаёт временное read-only представление:

```text
final_geometries = structural geometries ∪ deferred final points
```

Оно не записывается обратно в `LayoutCandidate` и не становится новым serialized contract.

Для поддерживаемого плана множество id финальных геометрий должно в точности совпадать с `GenerationPlan.features[*].id`.

## 3. Инварианты полноты входных данных

Стадия `FINAL` проверяет как минимум:

- существует `layout`;
- существует `terrain`;
- существует `hydrology`;
- существует `surface`;
- существует `placement`;
- `layout.attempt_index` совпадает с текущим attempt;
- множество финальных геометрий полно и не содержит лишних id.

Если upstream state неполон, это обычное отклонение attempt:

- группа engine invariants не проходит;
- hard results не вычисляются;
- `ranking = null`.

Это не capability error.

## 4. Проверка hard-ограничений

Если engine invariants прошли, стадия `FINAL` повторно оценивает все compiled hard constraints из `GenerationPlan.constraints` относительно финальной геометрии.

Повторная проверка нужна даже для ограничений, относящихся только к structural features:

- `FINAL` является независимой итоговой проверкой accepted candidate;
- ограничения deferred features впервые могут быть проверены относительно конкретной финальной точки;
- assembler получает candidate, прошедший единый финальный hard gate.

Семантика измерений и predicates не дублируется. `FINAL` использует тот же canonical spatial evaluator, что и `Layout`.

Поддерживаются ровно те комбинации evaluator/predicate, которые умеет текущий общий spatial evaluator. Неподдерживаемый evaluator/predicate является capability error, а измеренный `predicate=false` — обычным отклонением кандидата.

Hard results детерминированно упорядочиваются по `constraint.id`.

## 5. Soft-ограничения

Текущий compiler slice явно не компилирует пользовательские soft-ограничения.

Поэтому Final Validation v0.1 не делает вид, что soft scoring уже реализован.

Если в `GenerationPlan` вручную передан constraint со `strength=soft`, стадия `FINAL` поднимает `FinalValidationCapabilityError`.

Компиляция и scoring soft-ограничений будут отдельным design checkpoint.

## 6. Ranking

Для всех поддерживаемых hard-only plans множество soft constraints пусто.

Если engine invariants и hard constraints прошли:

```text
soft_constraints.results = ()
ranking.worst_effective_violation = 0.0
ranking.weighted_mean_score = 1.0
```

Это canonical neutral ranking, уже принятый generation baseline.

Если стадия `FINAL` отклонила candidate:

```text
ranking = null
```

## 7. RNG и мутация состояния

Final Validation:

- не получает semantic random draws;
- не делает reroll геометрии;
- не исправляет нарушения constraints;
- не изменяет `Layout` / `Terrain` / `Hydrology` / `Surface` / `Placement`;
- не создаёт `DomainData`;
- не выполняет IO.

## 8. Capability error и обычное отклонение

Обычное отклонение кандидата:

- отсутствует обязательное upstream state;
- множество финальных геометрий неполно;
- hard predicate был измерен и не выполнен.

Capability error:

- в plan присутствует soft constraint до реализации soft-scoring slice;
- конструкция spatial evaluator/predicate структурно корректна, но ещё не поддерживается текущими возможностями Core.

## 9. Что не входит в этот checkpoint

Не входят:

- компиляция soft constraints;
- soft scoring curves;
- сборка `DomainData`;
- materialization `HydroFeature` / lakes;
- export / rendering;
- повторная procedural generation;
- новые spatial relation semantics.
