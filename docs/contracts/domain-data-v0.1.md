---
id: CONTRACT-DOMAINDATA-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# DomainData v0.1 — draft

`DomainData` описывает уже принятый мир. Он не хранит recipe generation, reservations, rejected attempts или обязательную debug history.

## Корень

```yaml
domain_data_version: "0.1"

identity:
  id: example-domain-01
  label: Пример пограничного домена

provenance:
  spec_schema_version: "0.1"
  spec_fingerprint: "sha256:..."
  plan_fingerprint: "sha256:..."
  generation_config_fingerprint: "sha256:..."
  root_seed: 123456
  accepted_attempt_index: 7
  generator:
    name: domain_generator
    version: "0.1.0"
  rng_version: 1

domain:
  width_km: 120.0
  height_km: 100.0

grid:
  cell_size_km: 0.25
  rows: 400
  columns: 480

fields: {}
features: {}
networks: {}
validation: {}
```

`DomainData` самодостаточен для downstream consumers: renderer/exporter не обязан загружать GenerationPlan только ради размеров мира или final feature metadata.

## Provenance

Provenance позволяет определить exact generation context принятого результата. `accepted_attempt_index` — выигравший valid attempt. Rejected attempts остаются optional debug artifacts.

`generation_config_fingerprint` вычисляется только из semantic execution settings; observability/debug settings туда не входят.

## DomainData и DomainBundle

`DomainData` — логическая модель `domain.json`. `DomainBundle` — физический набор файлов:

```text
output/
├── manifest.json
├── domain.json
├── fields/
│   ├── elevation.npy
│   ├── water_depth.npy
│   ├── moisture.npy
│   └── vegetation_density.npy
├── cache/
│   └── slope.npy              # optional derived
└── debug/
    ├── generation-plan.json   # optional
    ├── layout.json            # optional
    └── validation.json        # optional
```

Preview/debug files не являются source of truth.

## Fields

Крупные raster arrays не встраиваются в JSON. `domain.json` содержит descriptors:

```yaml
fields:
  elevation:
    role: canonical
    format: npy
    path: fields/elevation.npy
    dtype: float32
    shape: [400, 480]
    unit: m

  water_depth:
    role: canonical
    format: npy
    path: fields/water_depth.npy
    dtype: float32
    shape: [400, 480]
    unit: m

  moisture:
    role: canonical
    format: npy
    path: fields/moisture.npy
    dtype: float32
    shape: [400, 480]
    unit: normalized

  vegetation_density:
    role: canonical
    format: npy
    path: fields/vegetation_density.npy
    dtype: float32
    shape: [400, 480]
    unit: normalized
```

Canonical baseline Core 0.1:

- `elevation`: meters relative to internal domain datum;
- `water_depth`: meters, `>= 0`; binary water mask is derived as `water_depth > 0`;
- `moisture`: normalized `[0,1]`, abstract ecological moisture, не precipitation units;
- `vegetation_density`: normalized `[0,1]`.

Persisted canonical continuous fields используют `float32`. Runtime implementation может считать с большей precision.

Derived fields вроде `slope`, `flow_direction`, `flow_accumulation` optional и помечаются `role: derived`. Debug/internal masks/noise layers не входят в `DomainData`.

Field paths:

- relative only;
- POSIX separators `/`;
- no absolute paths;
- no `..` traversal.

Canonical numeric data и serialized coordinates/properties не допускают `NaN`, `+inf`, `-inf`.

## Features

Final semantic feature хранит identity/metadata, family, final geometry, source и typed properties:

```yaml
features:
  fort-01:
    label: Пограничный форт
    tags: []
    source:
      type: specified
      preset: fort
    family: poi
    geometry:
      type: point
      x_km: 63.2
      y_km: 29.7

  lake-004:
    source:
      type: generated
      system: hydrology
    family: hydro
    geometry:
      type: area
      boundary: [...]
    properties:
      area_km2: 8.7
      surface_elevation_m: 312.5
```

`source.type` различает explicit/spec-driven (`specified`) и emergent (`generated`) objects. Output family registry может быть шире пользовательских preset families; Core 0.1 допускает как минимум `terrain`, `surface`, `poi`, `hydro`.

`operator` не сохраняется как свойство мира: это generation provenance уровня Plan. `properties` не arbitrary metadata bag; их schema определяется конкретным output feature/network type и версией DomainData.

Structural macro geometry сохраняется рядом с точными fields, потому что они описывают разные уровни одного мира: feature geometry — semantic extent/organization, field — точное raster state.

## River network

Hydrology topology хранится отдельно от обычных features:

```yaml
networks:
  rivers:
    type: directed
    nodes:
      river-node-001:
        kind: confluence
        position: {x_km: 41.2, y_km: 63.7}
      river-node-002:
        kind: domain_outlet
        position: {x_km: 120.0, y_km: 22.3}
        boundary_side: east

    segments:
      river-segment-001:
        from: river-node-001
        to: river-node-002
        centerline:
          - {x_km: 41.2, y_km: 63.7}
          - {x_km: 120.0, y_km: 22.3}
        properties:
          catchment_area_km2: 310.4
```

`from -> to` всегда upstream -> downstream. Lakes остаются semantic area features; river nodes могут ссылаться на lake feature ids для inflow/outflow topology.

## Validation summary

Полный `ValidationResult` является optional diagnostic artifact. `DomainData` хранит компактный summary:

```yaml
validation:
  engine_invariants_passed: true
  hard_constraints_passed: true
  soft:
    worst_effective_violation: 0.08
    weighted_mean_score: 0.87
```

## Canonical ordering

Canonical serialization не зависит от Python dict insertion order:

- feature/network/node/segment ids сериализуются в deterministic lexical order;
- object key ordering задаётся canonical serializer;
- порядок geometry vertices/centerline points сохраняется как semantic sequence.

## Что не входит в DomainData

- `PlacementReservation`;
- sampler recipes;
- rejected attempts;
- GenerationPlan как обязательная dependency;
- intermediate masks/noise/routing surfaces;
- full validation trace;
- renderer/previews.

После принятия candidate reservations и generation recipes свою роль выполнили и остаются только optional debug/provenance artifacts.
