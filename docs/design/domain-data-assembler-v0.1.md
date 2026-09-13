---
id: DESIGN-DOMAIN-DATA-ASSEMBLER-0.1
kind: design
status: accepted
normative: true
target: core-0.1
implemented: false
---

# DomainData Assembler v0.1

Этот документ фиксирует принятую семантику границы между завершённой procedural generation и будущим bundle/export layer.

## 1. Назначение

После выбора принятого `DomainCandidate` generation завершена. Assembler не создаёт новое состояние мира, а детерминированно упаковывает уже полученные semantic/runtime results в:

```text
DomainAssembly
  data: DomainData
  field_payloads:
    elevation
    water_depth
    moisture
    vegetation_density
```

Assembler не является generation stage и не входит в `STAGE_ORDER`.

Запрещены RNG, IO, renderer semantics, reroll, regeneration upstream layers и hidden fallback/correction.

## 2. Public boundary

Core 0.1 фиксирует conceptual API:

```python
assemble_domain(
    *,
    spec: DomainSpec,
    plan: GenerationPlan,
    config: GenerationConfig,
    candidate: DomainCandidate,
) -> DomainAssembly
```

Assembler получает именно выбранный `DomainCandidate`, а не `GenerationRunResult`: selection/ranking уже завершены pipeline orchestration и не повторяются.

`DomainSpec` передаётся явно, потому что `DomainData.identity` должен сохранить user-facing `spec.label`, а текущий `GenerationPlan` намеренно не переносит этот presentation metadata field.

## 3. Preconditions и error boundary

Перед assembly должны выполняться:

- `candidate` является complete valid final candidate;
- его final validation относится к stage `FINAL`;
- engine invariants и hard constraints passed;
- final ranking присутствует;
- `candidate.attempt_index` согласован с runtime state и final validation;
- все required runtime states существуют: layout, terrain, hydrology, surface, placement;
- `domain_spec_fingerprint(spec) == plan.source.spec_fingerprint`;
- `spec.id == plan.source.spec_id`;
- `spec.schema_version == plan.source.spec_schema_version`;
- geometry/runtime feature sets согласованы с `plan.features`;
- raster payloads имеют canonical shape/dtype;
- semantic feature IDs после merge не пересекаются.

Нарушение assembler invariants является explicit `DomainAssemblyError`/capability error. Assembler не исправляет input автоматически.

## 4. Domain identity

```text
DomainData.identity.id    = spec.id
DomainData.identity.label = spec.label
```

Assembler не генерирует display name и не подменяет отсутствующий label.

## 5. Provenance

`DomainData.provenance` строится детерминированно:

```text
spec_schema_version        = plan.source.spec_schema_version
spec_fingerprint           = plan.source.spec_fingerprint
plan_fingerprint           = semantic_plan_fingerprint(plan)
generation_config_fingerprint = semantic_generation_config_fingerprint(config)
root_seed                  = plan.seed
accepted_attempt_index     = candidate.attempt_index
generator.name             = "domain_generator"
generator.version          = plan.source.generator_version
rng_version                = RNG_VERSION
```

### 5.1 Semantic GenerationConfig fingerprint

Canonical generation-config fingerprint включает:

```text
generation_config_version
semantic
```

и **не включает** `observability`.

То есть debug/save flags не меняют canonical `DomainData.provenance`, что соответствует INV-008.

Fingerprint использует тот же canonical JSON discipline и `sha256:` prefix, что spec/plan provenance helpers.

## 6. Domain и grid

Размеры и grid descriptors переносятся из executable plan:

```text
domain.width_km  = plan.domain.width_km
domain.height_km = plan.domain.height_km

grid.cell_size_km = plan.grid.cell_size_km
grid.rows         = plan.grid.rows
grid.columns      = plan.grid.columns
```

Assembler не вычисляет альтернативную resolution и не округляет grid.

## 7. User-declared semantic features

Для каждого `ResolvedFeature` из `plan.features` assembler использует уже materialized final geometry:

```text
structural geometry -> candidate.state.layout.geometry_realizations[id]
deferred point      -> candidate.state.placement.final_points[id]
```

Эти источники обязаны быть disjoint и вместе давать exact feature set `plan.features`.

Metadata:

```text
id     = ResolvedFeature.id
label  = ResolvedFeature.metadata.label
tags   = ResolvedFeature.metadata.tags
source = SpecifiedFeatureSource(preset=ResolvedFeature.metadata.source_preset)
family = ResolvedFeature.family
```

Output contract выбирается по family:

- terrain -> `TerrainFeature`;
- surface -> `SurfaceFeature`;
- poi -> `PoiFeature`.

Geometry обязана быть совместима с output contract. Несовместимость является assembly error, не повод менять family/geometry.

Assembler не повторяет terrain/surface effects: raster fields уже содержат их результат.

## 8. Generated hydro features

Hydrology уже владеет semantic lake materialization:

```text
candidate.state.hydrology.lake_features
```

Assembler переносит готовые `HydroFeature` без повторной vectorization, smoothing или пересчёта properties.

User-declared features и generated hydro features объединяются только после duplicate-ID check.

## 9. Reserved generated hydro ID namespace

Core 0.1 резервирует для generated lakes полный pattern:

```regex
^lake-[0-9]{4,}$
```

User `FeatureSpec.id`, полностью совпадающий с этим pattern, недопустим.

Reject должен происходить на input validation/compile boundary до procedural generation. Assembler дополнительно проверяет duplicate IDs и никогда не выполняет silent overwrite.

Существующий generated protocol остаётся:

```text
lake-0001
lake-0002
...
lake-10000
```

Резервирование namespace является частью assembler correctness, потому что `DomainData.features` использует общий ID namespace для specified и generated semantic features.

## 10. River network

Canonical network packaging Core 0.1:

```python
networks = {
    "rivers": candidate.state.hydrology.river_network,
}
```

Ключ `rivers` присутствует всегда, даже если network пустой. Это отличает canonical empty network от отсутствующего assembly result.

Assembler не перестраивает topology и не создаёт/удаляет river nodes/segments.

Все lake node `feature_id` должны разрешаться в уже объединённом `DomainData.features` как `HydroFeature`; существующий `DomainData` validator остаётся последней serialized-contract проверкой.

## 11. Canonical field descriptors

Assembler создаёт ровно четыре canonical field descriptors Core 0.1:

```text
elevation
  source: TerrainState.elevation_m
  path: fields/elevation.npy
  dtype: float32
  unit: m

water_depth
  source: HydrologyState.water_depth_m
  path: fields/water_depth.npy
  dtype: float32
  unit: m

moisture
  source: SurfaceState.moisture
  path: fields/moisture.npy
  dtype: float32
  unit: normalized

vegetation_density
  source: SurfaceState.vegetation_density
  path: fields/vegetation_density.npy
  dtype: float32
  unit: normalized
```

Все descriptors имеют `role = canonical`, `format = npy`, `shape = (plan.grid.rows, plan.grid.columns)`.

Routing/fill elevation, flow direction, accumulation, stream mask, lake candidates и другие intermediate hydrology arrays не входят в canonical `DomainAssembly` v0.1. Они могут использоваться observability/debug layer отдельно.

## 12. Field payload ownership

`DomainAssembly.field_payloads` содержит четыре NumPy arrays по тем же canonical IDs.

До упаковки assembler требует:

- exact expected 2D shape;
- `dtype == numpy.float32`;
- finite/canonical invariants уже гарантированы upstream validators.

Assembler не выполняет implicit dtype cast или resize.

Для отделения accepted runtime state от downstream exporter assembler создаёт независимые copies payload arrays и помечает их read-only. Значения при этом не пересчитываются.

Таким образом downstream mutation не может изменить уже принятый `DomainCandidate` через alias.

## 13. ValidationSummary

В `DomainData.validation` сохраняется итоговая canonical summary:

```text
engine_invariants_passed = true
hard_constraints_passed  = true
soft                     = candidate.ranking
```

Assembler не запускает Final Validation повторно и не включает detailed stage validation traces в canonical `domain.json`.

Подробные validation/debug данные относятся к observability artifacts будущего exporter layer.

## 14. Deterministic ordering

Assembler создаёт canonical mappings в детерминированном порядке:

```text
fields        -> fixed canonical order
specified features -> ascending feature.id
hydro features     -> ascending feature.id
networks      -> fixed key "rivers"
```

Canonical semantic equality не должна зависеть от traversal order исходных runtime dicts.

## 15. DomainAssembly contract

`DomainAssembly` является in-memory Core boundary, не serialized root contract:

```python
@dataclass(frozen=True, slots=True)
class DomainAssembly:
    data: DomainData
    field_payloads: Mapping[str, np.ndarray]
```

Concrete implementation может использовать readonly mapping wrapper/эквивалентную immutable boundary, но consumer не должен иметь mutable structural access к assembly mapping.

`DomainData` остаётся serialized semantic root; NumPy arrays сериализуются будущим exporter-ом отдельно.

## 16. Invariants

Assembler v0.1 обязан обеспечивать:

1. assembly выполняется только после successful Final Validation;
2. никакого RNG;
3. никакого IO;
4. никакого rendering;
5. никакого reroll/re-ranking;
6. никакой повторной hydrology lake materialization;
7. никакого повторного применения terrain/surface effects;
8. никакого silent feature overwrite;
9. `DomainSpec` и `GenerationPlan` provenance согласованы;
10. observability config не влияет на canonical semantic config fingerprint;
11. canonical field payloads exact float32 + expected shape;
12. downstream payload mutation не мутирует accepted candidate;
13. output feature/network references проходят `DomainData` validation.

## 17. Implementation checkpoint

В implementation v0.1 входят:

- `DomainAssembly` in-memory boundary;
- `DomainAssemblyError`;
- semantic `GenerationConfig` fingerprint helper;
- reserved generated lake ID validation;
- specified final feature materialization в output feature contracts;
- merge specified + hydro semantic features;
- canonical river network packaging;
- canonical four field descriptors;
- readonly copied field payloads;
- provenance/identity/validation summary assembly;
- deterministic ordering;
- unit/integration tests и schema regeneration только если serialized schema действительно меняется.

Не входят:

- filesystem export;
- manifest format;
- atomic directory write;
- technical renderer;
- debug bundle structure;
- CLI/application entrypoint;
- YAML loader;
- local/remote model adapters;
- additional derived fields;
- new generation algorithms.

## 18. Следующий checkpoint

После принятой и merged implementation этого design следующий bounded design gate:

```text
DomainBundle Export v0.1
```

Exporter получает готовый `DomainAssembly` и отвечает только за persisted bundle/manifest/path/atomic-write semantics.
