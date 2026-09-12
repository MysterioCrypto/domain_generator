---
id: ADR-0001
kind: architecture-decision
status: accepted
normative: true
scope: core
---

# ADR-0001 — Границы Core

## Контекст

`domain_generator` должен быть самостоятельным процедурным ядром, пригодным для разных миров, жанров, кампаний, игровых систем, приложений и способов визуализации. Если procedural logic зависит от конкретного сеттинга, campaign lore, ruleset, UI, renderer, LLM или orchestration service, генератор становится трудно тестировать, переносить и переиспользовать.

Термин `Domain` в проекте используется только в общем пространственном смысле: ограниченная область мира/карты, которая генерируется как единое целое. Он не обозначает лоровую сущность какого-либо конкретного мира.

## Решение

Core принимает формальные setting-agnostic данные и возвращает формальные setting-agnostic данные.

Внутри Core допустимы generic spatial concepts: geometry, terrain, hydrology, continuous fields, networks, constraints, procedural features и placement rules.

За границей Core находятся:

- конкретные сеттинги и campaign lore;
- конкретные игровые системы и их rulesets;
- setting-specific preset catalogs и world data;
- LLM/agent orchestration;
- GitHub/CI orchestration;
- UI, renderer, artistic styling и presentation logic.

Setting-specific consumer может компилировать собственные понятия в публичные generic contracts Core, но Core не должен знать имя или семантику этого consumer-а.

## Следствия

- Один и тот же Core можно использовать для fantasy, science fiction, survival, strategy, simulation и других world-generation contexts без изменения алгоритмов.
- Конкретный setting/campaign является consumer-ом `domain_generator`, а не архитектурным родителем Core.
- Setting-specific presets, adapters и content packages должны жить вне базового пакета Core либо в явно внешнем extension layer.
- В Core не добавляется поле `setting` только ради идентификации внешнего мира: если такая metadata нужна приложению, она принадлежит внешнему слою.
- Интеграционные слои могут меняться независимо.
- Renderer не является источником истины о мире.
