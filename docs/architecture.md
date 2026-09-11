---
id: ARCH-CORE-0.1
kind: architecture
status: active
normative: true
target: core-0.1
---

# Архитектура Core 0.1

## Главный поток

```text
Human / client
    -> DomainSpec
    -> Constraint Compiler
    -> GenerationPlan
    -> deterministic Pipeline
    -> Validator / Scoring
    -> DomainData
    -> Renderers / exporters
```

`DomainSpec` хранит намерение и ограничения. `GenerationPlan` — конкретизированный пространственный план для одного запуска. `DomainData` — фактически сгенерированный мир.

## Представление мира

Core использует гибрид из трёх семейств данных:

- **Fields** — непрерывные или дискретные поля: elevation, moisture, temperature, vegetation density и т. п.
- **Networks** — связные структуры: rivers, roads, другие линейные сети.
- **Features** — семантические объекты: mountain range, lake, gorge, POI, settlement site и т. п.

Физическая география строится преимущественно через поля. Сети и features выводятся из полей или накладывают заранее объявленные constraints.

## Управляемая случайность

RNG не должен независимо рандомить клетки карты. Случайность выбирает параметры, формы и допустимые варианты. Coherent noise создаёт пространственно коррелированную нерегулярность. Constraints ограничивают множество допустимых решений.

## Pipeline Core 0.1

```text
layout constraints
  -> spatial layout
  -> elevation
  -> hydrology
  -> simple surface / vegetation
  -> generic POI placement
  -> validation
  -> DomainData
```

Каждая стадия должна быть заменяемой и тестируемой отдельно.

## Граница Core

Core не знает о ChatGPT, GitHub, конкретной кампании или художественном renderer. Интеграции находятся снаружи. Renderer читает `DomainData`, но не является источником истины и не должен менять географию.
