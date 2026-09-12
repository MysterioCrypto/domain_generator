---
id: CONTRACT-DOMAINDATA-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# DomainData v0.1 — черновик

`DomainData` описывает уже принятый мир. Он не хранит recipe генерации, reservations, rejected attempts или обязательную историю debug.

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

`DomainData` самодостаточен для downstream consumers: renderer/exporter не обязан загружать `GenerationPlan` только ради размеров мира или финальной metadata features.

## Provenance

Provenance позволяет определить точный контекст генерации принятого результата. `accepted_attempt_index` — выигравший валидный attempt. Rejected attempts остаются необязательными debug artifacts.

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

Preview/debug files не являются источником истины.

## Поля

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

Базовые canonical fields Core 0.1:

- `elevation`: метры относительно внутреннего datum domain;
- `water_depth`: метры, `>= 0`; binary water mask является derived и определяется как `water_depth > 0`;
- `moisture`: нормализованное `[0,1]` абстрактное экологическое увлажнение, а не единицы precipitation;
- `vegetation_density`: нормализованное `[0,1]`.

Сохраняемые canonical continuous fields используют `float32`. Runtime implementation может выполнять расчёты с большей точностью.

Derived fields вроде `slope`, `flow_direction`, `flow_accumulation` необязательны и помечаются `role: derived`. Debug/internal masks/noise layers не входят в `DomainData`.

Пути к fields:

- только относительные;
- разделители POSIX `/`;
- абсолютные пути запрещены;
- переходы `..` запрещены.

Canonical numeric data и serialized coordinates/properties не допускают `NaN`, `+inf`, `-inf`.

## Features

Финальный semantic feature хранит identity/metadata, family, финальную geometry, source и типизированные properties:

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

`source.type` различает явно заданные/spec-driven (`specified`) и возникшие в результате генерации (`generated`) objects. Реестр output families может быть шире пользовательских preset families; Core 0.1 допускает как минимум `terrain`, `surface`, `poi`, `hydro`.

`operator` не сохраняется как свойство мира: это generation provenance уровня Plan. `properties` не является произвольным metadata bag; его schema определяется конкретным типом output feature/network и версией `DomainData`.

Structural macro geometry сохраняется рядом с точными fields, потому что они описывают разные уровни одного мира: geometry feature — semantic extent/organization, field — точное raster state.

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

`from -> to` всегда означает upstream -> downstream. Lakes остаются semantic area features; river nodes могут ссылаться на id lake features для topology inflow/outflow.

## Краткий результат validation

Полный `ValidationResult` является необязательным diagnostic artifact. `DomainData` хранит компактный summary:

```yaml
validation:
  engine_invariants_passed: true
  hard_constraints_passed: true
  soft:
    worst_effective_violation: 0.08
    weighted_mean_score: 0.87
```

## Канонический порядок

Canonical serialization не зависит от Python dict insertion order:

- id features/networks/nodes/segments сериализуются в детерминированном лексикографическом порядке;
- порядок object keys задаётся canonical serializer;
- порядок vertices geometry и points centerline сохраняется как семантическая последовательность.

## Что не входит в DomainData

- `PlacementReservation`;
- sampler recipes;
- rejected attempts;
- `GenerationPlan` как обязательная dependency;
- промежуточные masks/noise/routing surfaces;
- полный validation trace;
- renderer/previews.

После принятия candidate reservations и generation recipes свою роль выполнили и остаются только необязательными debug/provenance artifacts.
