# domain_generator

Детерминированное процедурное ядро для генерации ограниченных пространственных регионов мира/карты с управляемой случайностью.

`Domain` здесь означает generic bounded spatial region. Это технический термин проекта, а не сущность какого-либо конкретного сеттинга.

## С чего начать

- [`PROJECT.md`](PROJECT.md) — текущее каноническое состояние проекта и архитектурные инварианты.
- [`docs/roadmap.md`](docs/roadmap.md) — этапы разработки Core 0.1.
- [`docs/architecture.md`](docs/architecture.md) — актуальная архитектура.
- [`docs/glossary.md`](docs/glossary.md) — общий словарь терминов.
- [`docs/decisions/`](docs/decisions/) — принятые архитектурные решения и причины их принятия.

## Граница проекта

Core intentionally setting-agnostic. Он знает о generic concepts вроде geometry, terrain, hydrology, fields, networks, constraints, procedural features и placement rules, но не знает о конкретном мире, кампании, игровой системе, UI или renderer-е.

Внешние проекты могут использовать `domain_generator` как библиотеку/движок и преобразовывать собственные setting-specific понятия в публичные generic contracts Core. Setting-specific preset catalogs, adapters и world data должны жить вне базового Core.

## Основной поток

```text
external client / world project
        ↓
    DomainSpec
        ↓
 deterministic Core
        ↓
    DomainData
        ↓
 renderer / exporter / game integration
```

LLM, agent orchestration, GitHub Actions и presentation tooling не являются частью procedural semantics.

## Состояние разработки

M0 и M1 завершены. M2 — deterministic pipeline — находится в реализации. Уже реализованы contracts/schema layer, deterministic RNG, layout primitives, placement reservations, terrain, hydrology, canonical water depth, base moisture/vegetation fields и GitHub Actions pytest CI.

Актуальный checkpoint и следующий bounded design всегда фиксируются в [`PROJECT.md`](PROJECT.md).

## Правило документации

Нормативные документы проекта используют машиночитаемый YAML front matter и человекочитаемый Markdown. Иллюстративные примеры не создают implicit rules Core и не должны молча превращаться в требования.
