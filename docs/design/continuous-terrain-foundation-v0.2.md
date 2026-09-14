# Continuous Terrain Foundation v0.2

Status: **accepted design gate**  
Target branch: `dev/0.2`  
Historical baseline: `release/0.1-prealpha` at `9699c3d8079b8b9710d65eed60ff975158af0ad3`

## 1. Причина изменения

Визуальный аудит Core 0.1 показал не presentation-only дефект, а ограничение модели мира:

```text
flat elevation = 0
+ sparse feature contributions
→ hydrology
→ surface
```

В такой модели `ridge` фактически является функцией расстояния до ломаной `Band.centerline`, а реки наследуют дискретную геометрию D8 routing. Дальнейшее улучшение renderer не исправляет исходный world state.

Core 0.2 меняет terrain semantics намеренно. Exact replay для Core 0.1 сохраняется только на `release/0.1-prealpha`; cross-version equality не требуется по INV-009.

## 2. Scope Batch A

Batch A реализует один крупный bounded slice:

```text
continuous base elevation
→ smooth semantic Band spine
→ natural terrain modifiers
→ TerrainState diagnostics
→ recalibrated 0.2 acceptance
→ terrain-only visual checkpoint
```

В Batch A **не перерабатываются** hydrology routing, river geometry, climate/moisture model, vegetation, dependent placement или final artistic renderer. Они остаются downstream consumers нового elevation и будут переоценены после terrain checkpoint.

Pipeline order не меняется:

```text
Layout → Terrain → Hydrology → Surface → Placement → Final
```

Новая stage не добавляется.

## 3. Version boundary

Core 0.2 является breaking pre-alpha line.

- `DomainSpec.schema_version` становится `0.2`.
- `GenerationRequest.request_version` становится `0.2`.
- `GenerationConfig` format в Batch A не меняется.
- `PresetCatalog` format в Batch A не меняется.
- `DomainData`/`DomainBundle` schema в Batch A не меняется.
- package release number меняется отдельно на release-hardening этапе 0.2; Batch A не обязан объявлять релиз.

Core 0.2 не обязан принимать Core 0.1 requests. Для exact 0.1 поведения используется замороженная release branch.

## 4. TerrainSpec v0.2

`DomainSpec` получает обязательную terrain-секцию.

Conceptual contract:

```json
"terrain": {
  "base_elevation_m": 120.0,
  "noise_layers": [
    {"id": "macro",    "scale_km": 120.0, "amplitude_m": 320.0},
    {"id": "regional", "scale_km": 40.0,  "amplitude_m": 130.0},
    {"id": "detail",   "scale_km": 12.0,  "amplitude_m": 35.0}
  ]
}
```

Normative rules:

1. `base_elevation_m` finite.
2. `noise_layers` contains at least one layer.
3. layer `id` is non-empty and unique within terrain config.
4. `scale_km > 0`.
5. `amplitude_m >= 0` and at least one layer has `amplitude_m > 0`.
6. layer order is not RNG identity; RNG namespace uses layer `id`.
7. domain-local min/max normalization is forbidden.

Последнее правило важно: одинаковая world-space точка при одинаковом semantic namespace не должна менять значение только потому, что изменились границы domain.

## 5. Base Field Synthesis

Terrain stage начинается не с нулевого массива, а с continuous world-space field:

```text
E_base(x,y) = base_elevation_m
            + Σ amplitude_i * N_i(x,y, scale_i)
```

`N_i` использует существующий deterministic world-space noise machinery.

Canonical RNG namespace для слоя:

```text
attempt_index
stage = terrain
scope = ("field", "base-elevation", "layer", layer.id)
purpose = "value"
```

Изменение порядка sibling layers не должно менять их отдельные random fields.

Sampling выполняется в canonical grid cell centers через `GridAdapter`.

## 6. TerrainState v0.2

Internal state расширяется:

```text
TerrainState
├── base_elevation_m : float32[rows, columns]
└── elevation_m      : float32[rows, columns]
```

`base_elevation_m` — диагностический upstream raster и не становится новым canonical DomainBundle field в Batch A.

`elevation_m` остаётся canonical terrain output для Hydrology и DomainData.

## 7. Semantic meaning of terrain features

Core 0.1 фактически делал geometry feature почти буквальной формой elevation.

Core 0.2 фиксирует другую модель:

```text
feature geometry = semantic skeleton / region of influence
terrain operator = modification of an already continuous terrain field
```

Feature не заменяет background world и не обязан визуально повторять свою vector geometry.

## 8. Smooth Band geometry

`Band` остаётся semantic geometry для горных систем и constraints, но sharp control polyline больше не является финальной centerline.

Generation sequence:

```text
start/end + deterministic control points
→ raw control polyline
→ fixed endpoint-preserving Chaikin smoothing
→ densified centerline
→ BandGeometry
```

Normative rules:

1. smoothing deterministic;
2. smoothing не зависит от raster `cell_size_km`;
3. endpoints сохраняются;
4. generated points остаются внутри domain because Chaikin points are convex combinations of existing in-domain points;
5. width profile остаётся parameterized по normalized arc length `[0,1]` smooth centerline;
6. no adjacent duplicate points in a non-degenerate band.

Batch A применяет smoothing к `Band`; `Corridor` не меняется этим design slice.

## 9. Ridge becomes massif influence

`ridge` больше не означает «размытая линия».

`Band.centerline` задаёт spine, `width_profile` — characteristic massif width. Для cell center определяется nearest position на smooth spine, локальная ширина и distance-to-spine.

Base uplift использует smooth compact envelope:

```text
u = distance / local_half_width
u >= 1 → envelope = 0
u < 1  → smooth envelope from 1 at spine to 0 at edge
```

Внутри envelope uplift дополнительно модулируется deterministic low-frequency terrain noise и local relief noise. Модуляция обязана оставаться bounded и не создавать отрицательный «анти-хребет» вместо uplift.

Existing ridge semantic parameters сохраняются где возможно:

- `height_m` — characteristic uplift amplitude;
- `profile_power` — envelope concentration;
- `roughness` — fraction of bounded internal relief;
- `roughness_scale_km` — characteristic scale of internal relief.

Их смысл меняется с literal blurred-polyline profile на massif modifier. Cross-version equality не обещается.

Required behavior:

```text
final elevation = existing continuous background + massif contribution
```

а не:

```text
final elevation = flat zero + line-shaped ridge
```

## 10. Natural Area modifiers

`raise` и `depress` Core 0.1 создают полный step на polygon boundary. В 0.2 natural modifiers получают обязательную transition zone.

Effect parameters:

```text
raise:   height_m + blend_width_km
depress: depth_m  + blend_width_km
```

Для cell внутри Area contribution определяется distance to Area boundary:

```text
0 at boundary
→ smooth transition
→ full magnitude at distance >= blend_width_km
```

Если Area уже transition width, contribution может не достигнуть full magnitude; это корректно.

Outside Area contribution = 0.

`flatten` сохраняет отдельную shaping semantics и не переписывается Batch A.

## 11. Composition order

Terrain v0.2 строится в фиксированном порядке:

```text
A. synthesize base_elevation_m
B. add structural natural modifiers in canonical feature-id order
   - raise
   - depress
   - ridge
C. apply shaping operators
   - flatten
D. cast final elevation to float32
```

Natural feature contributions складываются с background terrain, а не заменяют его.

## 12. Validation

Terrain validation v0.2 обязана проверять минимум:

- `base_elevation_m` exists, shape matches grid, dtype float32, finite;
- `elevation_m` exists, shape matches grid, dtype float32, finite;
- deterministic recomputation matches state exactly;
- all terrain features applied exactly once;
- no unsupported shaping conflict;
- request with no terrain features still produces spatially non-constant base elevation for the fixed acceptance fixture;
- renderer/logging/diagnostics do not mutate either terrain raster.

Unit tests additionally cover:

- semantic RNG independence by noise-layer id/order;
- world-space consistency under domain crop/extension for shared cell centers;
- Band smoothing endpoint preservation and lack of sharp raw-control corners on fixed fixtures;
- ridge contribution spans a 2D massif area and preserves background relief;
- raise/depress transition is continuous across the polygon boundary at grid resolution.

## 13. Acceptance migration

M11 Core 0.1 baselines are historical and remain available in `release/0.1-prealpha`.

On `dev/0.2` the existing acceptance suite is migrated to schema 0.2 and explicit terrain configuration. Exact hashes are recalibrated only after semantic assertions pass.

At minimum the 0.2 suite must include:

```text
T01 continuous-base
T02 massif-ridge
T03 smooth-area-modifier
```

Existing end-to-end A01..A07 coverage may be retained/recalibrated where useful, but no test may preserve a 0.1 behavior merely to keep an old hash green.

## 14. Early visual checkpoint

Batch A stops for human review immediately after a representative elevation world is generated.

Review artifact must expose elevation without relying on Hydrology/Surface quality. The checkpoint may be produced downstream from canonical `elevation.npy`; it is not a new world-state field and does not change generation.

Minimum reviewer visualization:

```text
hypsometric elevation
+ hillshade
+ optional contour lines
```

Human acceptance questions:

1. Does the background read as one continuous terrain rather than empty plane + blobs?
2. Does a ridge read as a broad massif rather than a blurred polyline?
3. Are large and small elevation structures simultaneously visible?
4. Are natural Area modifiers blended into the surrounding terrain?
5. Is there any obvious grid-/corner-driven geometry that should be fixed before Hydrology work?

Hydrology Batch B does not start until this checkpoint is explicitly accepted.

## 15. Non-goals

Batch A does not promise:

- physically simulated plate tectonics;
- hydraulic/thermal erosion;
- final realistic river geometry;
- climate zones;
- biome classification;
- coast/ocean generation;
- artistic map output;
- backward input compatibility with Core 0.1.

These may be future v0.2 batches after the continuous terrain foundation is visually and semantically accepted.

## 16. Invariants

INV-001..INV-011 remain in force.

Especially:

- INV-003 exact replay applies to the exact supported generator version;
- INV-006 this document precedes implementation;
- INV-007 every new random field uses stable semantic namespaces;
- INV-008 diagnostics/preview cannot alter semantic output;
- INV-009 no cross-version generated-world identity guarantee;
- INV-010 Terrain continues to read only declared upstream Layout/Plan state;
- INV-011 terrain influence remains in Terrain rather than hidden later side effects.
