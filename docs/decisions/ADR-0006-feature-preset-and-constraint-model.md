---
id: ADR-0006
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
---

# ADR-0006 — Модель feature, preset и constraint

## Контекст

Core должен поддерживать разные типы географии без специальных веток под конкретные кампании или названия объектов.

## Решение

`FeatureSpec v0.1` содержит только:

- `id`;
- `preset`;
- необязательный `parameters`;
- необязательный `tags`.

`family`, `shape` и `operator` следуют из preset после resolution. Shape задаёт топологический тип (`point`, `area`, `corridor`, `band`), а не идеальную фигуру.

Preset — декларативные данные: defaults, schema параметров, политика sampling и ссылка на универсальный operator. Preset не содержит исполняемого кода. В Core 0.1 один preset использует один operator.

Constraints отделены от feature и имеют модель:

```text
relation + SpatialSelector(subject) + SpatialSelector(target)
```

Selectors могут выбирать `whole` / `center` / `start` / `end` / `endpoints` / `boundary` либо domain anchors/regions/literal geometry. Семантические relations компилируются в универсальные evaluators/predicates.

`hard` и `soft` используют одни и те же измерители; различается реакция на результат. Hard failure всегда отклоняет candidate.

Параметр `min/max` описывает допустимый domain, а не автоматически равномерное случайное распределение. Политика sampling определяется definition preset/operator.

## Следствия

Новые content presets обычно можно добавлять без изменения Python. Новое поведение требует осознанного добавления универсального operator/evaluator, а не скрытого специального случая.
