---
id: ADR-0009
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
implemented: false
---

# ADR-0009 — Contract ownership and M1 consistency

## Context

Перед реализацией Pydantic contracts была проведена сквозная проверка `DomainSpec -> GenerationPlan -> LayoutCandidate -> ValidationResult/GenerationConfig -> DomainData`. Основные роли были согласованы, но оставались неоднозначности ownership параметров, semantic fingerprinting, geometry parts, dependent placement и output provenance.

## Decision

### Layout и effect разделены в GenerationPlan

Resolved feature содержит отдельные `layout` и `effect` recipes. Layout parameters управляют macro geometry/reservation; effect parameters принадлежат terrain/surface/dependent-placement operator. Pipeline не выводит ownership параметра из имени.

### Metadata сохраняется, но не влияет на procedural identity

`label`, `tags`, `source_preset` сохраняются в Plan metadata и могут переноситься в DomainData. Они не участвуют в RNG namespace и исключаются из semantic `plan_fingerprint`.

`spec_fingerprint` отражает normalized source spec, а `plan_fingerprint` — canonical executable projection Plan.

### Relation registry Core 0.1 ограничен определённой семантикой

Primitive relations: `near`, `far_from`, `inside`, `outside`, `crosses`, `overlaps`, `adjacent`. `connects` отложен до появления явной route/network semantics.

Geometry `part` имеет единое нормативное значение для point/corridor/band/area; downstream modules не переопределяют `center`, `start`, `end`, `endpoints`, `boundary` локально.

### LayoutCandidate материализует macro geometry

Structural geometry сериализуется как `point`, `corridor`, `band` или simple `area`. `PlacementReservation` хранит vector `RegionSet`, полученный из hard layout constraints. RegionSet может быть disconnected, иметь holes и быть пустым; пустота означает well-formed candidate с hard validation failure, а не schema error.

Dependent layout-hard constraints могут ссылаться только на geometry, существующую к layout stage. Core 0.1 не вводит ordering/backtracking graph для deferred -> deferred dependencies.

### Domain boundary не обрезает semantic structure заранее

Point final geometry и corridor/band centerlines находятся внутри/on domain boundary, но band influence footprint может выходить наружу и клиппится при вычислении raster effects. Сам факт выхода influence за границу не является engine invariant failure.

### Site suitability и global ranking разделены

Intrinsic `SiteProfile.preferences` выбирают physical site внутри одного candidate. User soft constraints оценивают получившийся candidate и участвуют в global ranking. Intrinsic site score сам по себе не переносится в global candidate score.

Soft constraint weight: `0 < weight <= 1`; `effective_violation = (1 - score) * weight`.

### DomainData — self-contained accepted world

DomainData хранит domain identity/labels, provenance, final feature geometries, canonical field descriptors и network topology. Canonical water representation Core 0.1 — `water_depth` (`float32`, meters, `>=0`); binary water mask является derived view.

## Consequences

- contract ownership можно напрямую выразить типами Pydantic;
- cosmetic metadata edits не ломают semantic Plan identity;
- constraint engine получает единые geometry-part semantics;
- placement не требует hidden retries/backtracking в v0.1;
- downstream consumers не обязаны загружать source spec/plan для отображаемых labels и размеров мира;
- некоторые будущие use cases (`connects`, deferred dependency graph, arbitrary area holes as user features) сознательно отложены.
