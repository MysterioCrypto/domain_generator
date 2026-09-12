---
id: DESIGN-FINAL-VALIDATION-HARD-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Final Validation v0.1 — hard-complete slice

Этот checkpoint реализует production `FINAL` stage для реально поддерживаемого compiler slice: планы без user soft constraints.

## 1. Назначение

Final Validation является observer последнего runtime state одного attempt. Он ничего не генерирует, не мутирует upstream outputs и не использует RNG.

```text
LayoutCandidate
TerrainState
HydrologyState
SurfaceState
PlacementState
        +
GenerationPlan
        ↓
final geometry view
        ↓
user hard constraints
        ↓
ValidationResult(stage=final)
```

## 2. Final geometry view

Structural features уже имеют concrete geometry в:

```text
LayoutCandidate.geometry_realizations[id]
```

Deferred point features имеют final geometry в:

```text
PlacementState.final_points[id]
```

Final stage создаёт временный read-only geometry view:

```text
final_geometries = structural geometries ∪ deferred final points
```

Он не записывается обратно в `LayoutCandidate` и не становится новым serialized contract.

Для supported plan множество final geometry ids должно в точности совпадать с `GenerationPlan.features[*].id`.

## 3. Upstream completeness invariants

Final stage проверяет как минимум:

- layout существует;
- terrain существует;
- hydrology существует;
- surface существует;
- placement существует;
- `layout.attempt_index` совпадает с текущим attempt;
- final feature geometry set complete и не содержит лишних ids.

Если upstream state неполон, это обычный rejected attempt:

- engine invariant group fails;
- hard results не вычисляются;
- ranking = null.

Это не capability error.

## 4. Hard constraint evaluation

Если engine invariants прошли, Final повторно оценивает все compiled hard constraints из `GenerationPlan.constraints` против final geometry view.

Зачем повторная проверка нужна даже для structural-only constraints:

- Final является независимой итоговой проверкой accepted candidate;
- deferred feature constraints впервые могут быть оценены против concrete final point;
- assembler получает candidate, который прошёл единый final hard gate.

Constraint measurement/predicate semantics не дублируются. Final использует тот же canonical spatial evaluator, что и Layout.

Supported evaluator/predicate combinations остаются ровно теми, которые поддерживает current shared spatial evaluator. Неподдерживаемый evaluator/predicate является capability error, а измеренный predicate=false — normal candidate rejection.

Hard results упорядочиваются детерминированно по `constraint.id`.

## 5. Soft constraints

Current compiler slice явно не компилирует user soft constraints.

Поэтому Final Validation v0.1 hard-complete НЕ делает вид, что soft scoring реализован.

Если `GenerationPlan` вручную содержит constraint со `strength=soft`, Final stage поднимает `FinalValidationCapabilityError`.

Soft compilation/scoring будет отдельным design checkpoint.

## 6. Ranking

Для всех поддерживаемых hard-only plans soft constraint set пуст.

Если engine invariants и hard constraints прошли:

```text
soft_constraints.results = ()
ranking.worst_effective_violation = 0.0
ranking.weighted_mean_score = 1.0
```

Это canonical neutral ranking, уже принятый generation baseline.

Если Final rejected:

```text
ranking = null
```

## 7. RNG и mutation

Final Validation:

- не получает semantic random draws;
- не reroll-ит geometry;
- не исправляет constraint violations;
- не меняет Layout/Terrain/Hydrology/Surface/Placement;
- не создаёт DomainData;
- не делает IO.

## 8. Capability errors vs rejection

Normal rejection:

- missing upstream state;
- incomplete final geometry set;
- hard predicate measured and not satisfied.

Capability error:

- soft constraint присутствует в plan до implementation soft-scoring slice;
- spatial evaluator/predicate construct structurally valid, но не поддерживается current Core capability.

## 9. Non-goals

Не входят:

- soft constraint compilation;
- soft scoring curves;
- DomainData assembly;
- HydroFeature/lake materialization;
- export/rendering;
- повторная procedural generation;
- new spatial relation semantics.
