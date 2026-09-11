---
id: ADR-0006
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
---

# ADR-0006: Feature, preset and constraint model

## Context

Core должен поддерживать разные типы географии без special-case веток под конкретные кампании или названия объектов.

## Decision

`FeatureSpec v0.1` содержит только:

- `id`;
- `preset`;
- optional `parameters`;
- optional `tags`.

`family`, `shape` и `operator` следуют из preset после resolution. Shape задаёт топологический тип (`point`, `area`, `corridor`, `band`), а не идеальную фигуру.

Preset — декларативные данные: defaults, parameter schema, sampling policy и ссылка на generic operator. Preset не содержит исполняемого кода. В Core 0.1 один preset использует один operator.

Constraints отделены от feature и имеют модель:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Selectors могут выбирать whole/center/start/end/endpoints/boundary или domain anchors/regions/literal geometry. Semantic relations компилируются в generic evaluators/predicates.

`hard` и `soft` используют одни и те же измерители; различается реакция на результат. Hard failure всегда отклоняет candidate.

Parameter `min/max` описывает allowed domain, а не автоматически uniform random. Sampling policy определяется preset/operator definition.

## Consequences

Новые content presets обычно можно добавлять без изменения Python. Новое поведение требует осознанного добавления generic operator/evaluator, а не скрытого special case.