---
id: DESIGN-PYTHON-DATA-MODEL-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Модель данных Python v0.1

Этот документ фиксирует принятую границу между сериализуемыми contracts и runtime computational state.

## Сериализуемые и стабильные модели

Использовать Pydantic v2 для:

- `DomainSpec`;
- `GenerationPlan`;
- `LayoutCandidate`;
- `ValidationResult`;
- `DomainData`;
- value models geometry;
- definitions preset;
- declarative schemas parameters/constraints/site-profile.

Для завершённых compiled/debug contracts, где это применимо, модели должны быть immutable/frozen после создания.

Pydantic отвечает за структурную validation и serialization, но не за generation, lookup preset или semantic compilation.

Рекомендуемая граница ошибок:

- parse/structural errors — некорректная структура или types документа;
- semantic/compiler errors — неизвестные presets/operators, некорректные references, несовместимые selector parts, невозможный compiled recipe;
- failures generation — attempts exhausted / no valid candidate;
- errors engine invariant — внутренняя ошибка Core или нарушение invariant.

Неизвестные input fields должны отклоняться, а не молча игнорироваться (`extra='forbid'` для canonical contracts).

## Runtime/computational models

Использовать typed dataclasses для изменяемого состояния стадий, например:

```text
CandidateState
TerrainState
HydrologyState
SurfaceState
PlacementState
```

Runtime state не является file contract и может постепенно заполняться orchestrator-ом в рамках одного attempt.

Числовые raster/field data хранятся в NumPy arrays, а не непосредственно внутри Pydantic `DomainData`.

Концептуальная граница:

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

Сериализуемая geometry должна использовать discriminated value models:

- point;
- corridor;
- band;
- area.

Например point хранит мировые координаты; corridor — centerline; band — centerline + width profile; area — closed boundary. Для immutable sequences после parsing предпочтительны tuples.

## Стабильные tokens

Повторно используемые стабильные concepts могут быть `StrEnum`; локальные закрытые варианты могут быть `Literal`. Не следует создавать inheritance hierarchy вроде `MountainFeature -> TerrainFeature -> Feature`.

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

Definitions preset типизируют базовые kinds parameters Core 0.1:

- float;
- integer;
- boolean;
- enum.

Overrides `DomainSpec` остаются компактными — fixed/range/one_of; compiler сопоставляет override с definition parameter preset и создаёт полностью разрешённый typed recipe Plan.

## Граница DomainData

Pydantic `DomainData` не содержит большие `np.ndarray` как embedded JSON values. Он хранит structured metadata/descriptors/references на внешние files arrays. Runtime arrays сохраняются отдельно exporter/assembler-ом.

## Антипаттерны

Contracts не должны содержать методы вроде:

```text
spec.generate()
feature.resolve_preset()
constraint.evaluate(world)
```

Алгоритмы принадлежат modules `compiler`, `geometry`, `terrain`, `hydrology`, `surface`, `poi`, `validation`, `pipeline`; contracts остаются данными.
