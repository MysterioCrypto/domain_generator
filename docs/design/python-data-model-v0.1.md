---
id: DESIGN-PYTHON-DATA-MODEL-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Python data model v0.1

Этот документ фиксирует принятую границу между serialized contracts и runtime computational state.

## Serialized/stable models

Использовать Pydantic v2 для:

- `DomainSpec`;
- `GenerationPlan`;
- `LayoutCandidate`;
- `ValidationResult`;
- `DomainData`;
- geometry value models;
- preset definitions;
- declarative parameter/constraint/site-profile schemas.

Для завершённых compiled/debug contracts, где применимо, модели должны быть immutable/frozen после создания.

Pydantic отвечает за structural validation и serialization, но не за generation, preset lookup или semantic compilation.

Рекомендуемая граница ошибок:

- parse/structural errors — invalid document shape/types;
- semantic/compiler errors — unknown presets/operators, bad references, incompatible selector parts, impossible compiled recipe;
- generation failures — attempts exhausted / no valid candidate;
- engine invariant errors — internal Core bug/invariant violation.

Unknown input fields должны отклоняться, а не silently игнорироваться (`extra='forbid'` для canonical contracts).

## Runtime/computational models

Использовать typed dataclasses для mutable stage state, например:

```text
CandidateState
TerrainState
HydrologyState
SurfaceState
PlacementState
```

Runtime state не является file contract и может постепенно заполняться orchestrator'ом в рамках одного attempt.

Числовые raster/field data хранятся в NumPy arrays, а не непосредственно внутри Pydantic `DomainData`.

Пример conceptual boundary:

```text
Pydantic contracts / value objects
---------------------------------
DomainSpec
GenerationPlan (immutable)
LayoutCandidate (immutable)
ValidationResult (immutable)
DomainData
PresetDefinition
Geometry

Runtime
---------------------------------
CandidateState (mutable dataclass)
TerrainState
HydrologyState
SurfaceState
PlacementState
NumPy ndarray fields
```

## Geometry

Serializable geometry должна использовать discriminated value models:

- point;
- corridor;
- band;
- area.

Например point хранит world coordinates; corridor — centerline; band — centerline + width profile; area — closed boundary. Для immutable sequences предпочтительны tuples после parsing.

## Stable tokens

Повторно используемые stable concepts могут быть `StrEnum`; локальные закрытые варианты могут быть `Literal`. Не создавать inheritance hierarchy вроде `MountainFeature -> TerrainFeature -> Feature`.

Content presets остаются data-driven:

```text
ResolvedFeature
  family
  shape
  operator id
  parameters
  lifecycle
```

а не отдельными Python subclasses для каждого типа контента.

## Parameters

Preset definitions типизируют базовые parameter kinds Core 0.1:

- float;
- integer;
- boolean;
- enum.

DomainSpec overrides остаются компактными (fixed/range/one_of); compiler сопоставляет override с preset parameter definition и создаёт fully resolved typed Plan recipe.

## DomainData boundary

Pydantic `DomainData` не содержит большие `np.ndarray` как embedded JSON values. Он хранит structured metadata/descriptors/references на внешние array files. Runtime arrays сохраняются exporter/assembler'ом отдельно.

## Anti-patterns

Contracts не должны содержать методы вроде:

```text
spec.generate()
feature.resolve_preset()
constraint.evaluate(world)
```

Алгоритмы принадлежат modules `compiler`, `geometry`, `terrain`, `hydrology`, `surface`, `poi`, `validation`, `pipeline`; contracts остаются данными.
