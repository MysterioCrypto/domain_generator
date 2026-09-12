---
id: ADR-0009
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
implemented: false
---

# ADR-0009 — Владение контрактами и согласованность M1

## Контекст

Перед реализацией Pydantic contracts была проведена сквозная проверка `DomainSpec -> GenerationPlan -> LayoutCandidate -> ValidationResult/GenerationConfig -> DomainData`. Основные роли были согласованы, но оставались неоднозначности владения параметрами, семантического fingerprinting, geometry parts, dependent placement и output provenance.

## Решение

### Layout и effect разделены в GenerationPlan

Resolved feature содержит отдельные `layout` и `effect` recipes. Параметры layout управляют macro geometry/reservation; параметры effect принадлежат operator-ам terrain/surface/dependent-placement. Pipeline не выводит владельца параметра из его имени.

### Metadata сохраняется, но не влияет на процедурную идентичность

`label`, `tags`, `source_preset` сохраняются в metadata Plan и могут переноситься в `DomainData`. Они не участвуют в RNG namespace и исключаются из семантического `plan_fingerprint`.

`spec_fingerprint` отражает нормализованный исходный spec, а `plan_fingerprint` — canonical executable projection Plan.

### Реестр relations Core 0.1 ограничен определённой семантикой

Примитивные relations: `near`, `far_from`, `inside`, `outside`, `crosses`, `overlaps`, `adjacent`. `connects` отложен до появления явной семантики route/network.

Geometry `part` имеет единое нормативное значение для point/corridor/band/area; downstream modules не переопределяют `center`, `start`, `end`, `endpoints`, `boundary` локально.

### LayoutCandidate материализует macro geometry

Structural geometry сериализуется как `point`, `corridor`, `band` или простой `area`. `PlacementReservation` хранит векторный `RegionSet`, полученный из hard layout constraints. `RegionSet` может состоять из несвязанных частей, иметь holes и быть пустым; пустота означает корректно сформированный candidate с hard validation failure, а не schema error.

Hard constraints dependent layout могут ссылаться только на geometry, существующую к стадии layout. Core 0.1 не вводит ordering/backtracking graph для deferred -> deferred dependencies.

### Граница domain не обрезает semantic structure заранее

Финальная geometry point и centerlines corridor/band находятся внутри или на границе domain, но footprint влияния band может выходить наружу и обрезается при вычислении raster effects. Сам факт выхода influence за границу не является engine invariant failure.

### Site suitability и глобальный ranking разделены

Внутренние `SiteProfile.preferences` выбирают физическое место внутри одного candidate. Пользовательские soft constraints оценивают получившийся candidate и участвуют в глобальном ranking. Внутренний site score сам по себе не переносится в глобальный candidate score.

Вес soft constraint: `0 < weight <= 1`; `effective_violation = (1 - score) * weight`.

### DomainData — самодостаточный принятый мир

`DomainData` хранит identity/labels domain, provenance, финальные geometries features, descriptors canonical fields и topology network. Canonical water representation Core 0.1 — `water_depth` (`float32`, meters, `>=0`); binary water mask является derived view.

## Следствия

- владение contract-ами можно напрямую выразить типами Pydantic;
- изменения косметической metadata не ломают семантическую идентичность Plan;
- constraint engine получает единые semantics частей geometry;
- placement не требует скрытых retries/backtracking в v0.1;
- downstream consumers не обязаны загружать исходный spec/plan для отображаемых labels и размеров мира;
- некоторые будущие сценарии (`connects`, deferred dependency graph, arbitrary area holes as user features) сознательно отложены.
