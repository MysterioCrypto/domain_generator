---
id: DESIGN-SURFACE-FEATURE-BIAS-0.1
kind: design
status: accepted
normative: true
target: core-0.1
---

# Biases surface features v0.1

## Область действия

Core 0.1 добавляет два универсальных operator-а surface поверх конкретной `AreaGeometry`:

- `moisture_bias`;
- `vegetation_bias`.

Эти operators являются числовыми modifiers fields и не зависят от конкретного сеттинга. Они не кодируют forest, wetland, biome, climate, soil или другую предметно-специфичную семантику.

## Upstream inputs

Генерация Surface читает неизменяемые upstream outputs:

```text
LayoutCandidate
TerrainState
HydrologyState
GenerationPlan
```

Surface никогда не мутирует layout, terrain или hydrology.

В этом slice обрабатываются только features с `family=surface`. Каждый такой feature обязан использовать `effect.stage=surface`, иметь конкретную geometry в `LayoutCandidate.geometry_realizations` и использовать поддерживаемую комбинацию operator/geometry. Неподдерживаемые конструкции являются явными capability errors и никогда не пропускаются молча.

## Поддерживаемые operators

### moisture_bias

Точный обязательный набор effect parameters:

```text
{"delta_moisture"}
```

`delta_moisture` разрешается в одно конечное float-значение из `[-1, 1]`.

Для каждой raster cell, world-space center которой находится внутри или на `AreaGeometry` feature, feature вносит этот signed delta в contribution field moisture. Другие cells получают нулевой contribution.

### vegetation_bias

Точный обязательный набор effect parameters:

```text
{"delta_vegetation"}
```

`delta_vegetation` разрешается в одно конечное float-значение из `[-1, 1]`.

Для каждой raster cell, world-space center которой находится внутри или на `AreaGeometry` feature, feature вносит этот signed delta в contribution field vegetation. Другие cells получают нулевой contribution.

## Rasterization

Rasterization area использует существующее каноническое правило world-coordinate centers cells:

```text
cell center inside/on AreaGeometry -> feature applies
otherwise                         -> feature does not apply
```

Edge smoothing, sub-cell coverage, sampling renderer или мутация polygon в v0.1 не вводятся.

## Sampling parameters и RNG

Effect parameters surface feature используют существующий универсальный механизм sampling resolved parameters.

RNG key:

```text
stage   = surface
scope   = ("feature", feature_id, "parameter", parameter_name)
purpose = "sample"
```

Изменение порядка обхода features или несвязанных features не должно менять sampled value другого feature.

Rasterization и accumulation contributions не потребляют RNG.

## Аддитивная и независимая от порядка композиция

Каждый поддерживаемый surface feature materialize-ит собственное float64 contribution field.

Features обрабатываются в каноническом возрастающем порядке `feature.id`. Signed contributions аккумулируются в float64. Overlap разрешён и не считается conflict.

Clamp после каждого feature запрещён.

### Moisture

```text
BaseMoisture64
+ sum(MoistureBiasContribution64)
= BiasedMoisture64
-> clamp once to [0, 1]
-> canonical water cells forced to 1
= Moisture64
```

Таким образом bias moisture также влияет на downstream terrestrial vegetation, потому что potential vegetation выводится из финального moisture.

### Vegetation

```text
slope_factor = clamp(1 - slope_deg / vegetation_slope_zero_deg, 0, 1)
VegetationPotential64 = Moisture64 * slope_factor

VegetationPotential64
+ sum(VegetationBiasContribution64)
= BiasedVegetation64
-> clamp once to [0, 1]
-> canonical water cells forced to 0
= Vegetation64
```

Canonical water определяется только как `water_depth_m > 0`.

Только после завершения всей композиции и water overrides canonical fields один раз приводятся к float32.

## Приоритет water

Biases surface не могут переопределить canonical semantics water:

```text
water_depth_m > 0 -> moisture = 1
water_depth_m > 0 -> vegetation_density = 0
```

Это не позволяет универсальным terrestrial surface effects создавать сухие water cells или terrestrial vegetation на canonical water.

## Validation

Validation Surface проверяет как минимум:

- upstream layout существует и attempt index совпадает;
- terrain и hydrology существуют и совпадают с shape grid;
- surface state существует, использует float32, имеет конечные значения в `[0,1]`;
- canonical water overrides выполняются точно;
- каждый ожидаемый surface feature применён ровно один раз;
- детерминированный recomputation точно совпадает с сохранённым `SurfaceState`.

Ожидаемые id surface features — все `GenerationPlan.features` с `family=surface`.

## Capability errors

Attempt явно завершается ошибкой для неподдерживаемой или некорректной semantics surface feature, включая:

- family surface с effect stage, отличной от surface;
- отсутствующую materialized geometry;
- reservation layout вместо конкретной geometry;
- geometry, отличную от `AreaGeometry`;
- неподдерживаемый surface operator;
- неправильный точный набор effect parameters;
- resolved parameter recipe не типа float;
- неподдерживаемый sampler parameter;
- sampled value, которое не является числовым или конечным;
- delta вне `[-1,1]`.

## Что не входит в v0.1

- binary masks forest/wetland/biome;
- climate, temperature, precipitation или seasonality;
- simulation soil;
- multiplicative или priority-based biases;
- shaping operators surface;
- falloff/feathering границ;
- влияние Surface для Band/Corridor;
- aquatic vegetation;
- surface types или vocabulary preset конкретного сеттинга.

Presets конкретного сеттинга могут внешним образом разрешаться в эти универсальные operators, но такой vocabulary не является частью semantics Core.
