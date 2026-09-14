---
design: guide-renderer-v0.1
status: accepted
implemented: false
scope: downstream-presentation
---

# Guide Renderer v0.1

## 1. Назначение

Guide Renderer создаёт человекочитаемый top-down preview generated world, пригодный для быстрого визуального контроля и как будущая spatial guide-картинка для presentation/image-generation layer.

Он НЕ заменяет Technical Renderer и НЕ становится частью generation semantics.

```text
canonical world
DomainData + canonical field payloads
        │
        ├─ Technical Renderer
        │    → technical-map.png
        │    → инженерная диагностика
        │
        └─ Guide Renderer
             → guide-map.png
             → карта-подобный preview
```

Цель v0.1 — получить изображение, которое с первого взгляда читается как generated terrain preview: земля, рельеф, вода, реки, растительность и POI, а не как набор debug-overlay полос и ячеек.

## 2. Архитектурная граница

Guide Renderer принимает только уже принятую `DomainAssembly` / `DomainData` и canonical field payloads.

Он:

- не вызывает compiler;
- не запускает generation stages;
- не использует RNG;
- не изменяет `DomainData`;
- не изменяет `.npy` fields;
- не влияет на candidate selection/ranking;
- не добавляет или удаляет features;
- не является источником geography.

Таким образом INV-008 сохраняется: наличие/отсутствие guide rendering не меняет semantic result.

## 3. Выход

Guide Renderer создаёт неканонический downstream artifact:

```text
preview/guide-map.png
```

Canonical DomainBundle остаётся прежним:

```text
domain.json
manifest.json
fields/*.npy
```

`guide-map.png` не включается в canonical manifest и не участвует в deterministic world identity.

## 4. Visual grammar v0.1

### 4.1 Terrain base

Базовый цвет карты вычисляется из canonical `elevation` с hypsometric tint:

- низины — зелёно-оливковый диапазон;
- средние высоты — сухой зелёно-коричневый диапазон;
- высокие области — каменно-серый диапазон;
- самые высокие локальные значения — светлый серый.

Нормализация предназначена только для presentation и не меняет canonical elevation.

### 4.2 Hillshade

Поверх terrain tint применяется deterministic hillshade, вычисляемый из canonical `elevation` и canonical grid spacing.

Fixed renderer constants v0.1:

```text
light azimuth = 315°
light altitude = 45°
```

Hillshade не является отдельным world field и не экспортируется как semantic data.

### 4.3 Vegetation / moisture

`vegetation_density` и, ограниченно, `moisture` используются как цветовые модуляторы terrain base:

- высокая vegetation усиливает зелёную составляющую;
- низкая vegetation оставляет более сухой/каменный terrain tint;
- moisture не рисуется отдельной debug-плашкой поверх карты.

Модуляция presentation-only.

### 4.4 Water

Canonical water mask определяется только существующим правилом:

```text
water_depth > 0
```

Вода отображается отдельной синей заливкой поверх terrain.

Renderer может использовать anti-alias/interpolation для визуальной кромки, но не может придумывать воду вне canonical mask как semantic geography.

### 4.5 Rivers

`DomainData.networks["rivers"]` рисуется как непрерывные синие линии по canonical node coordinates.

Line width может зависеть от существующих river segment properties, если они доступны, но v0.1 не выводит новый физический discharge/width model.

### 4.6 POI

Final `poi` features отображаются компактными читаемыми markers.

По умолчанию v0.1 не обязан подписывать каждый POI текстом, чтобы карта не превращалась в debug diagram.

### 4.7 Specified feature geometry

Guide Renderer НЕ рисует aggressive debug overlays вроде широкой оранжевой centerline, sample bars и layout construction geometry.

Эти элементы остаются задачей Technical Renderer.

Guide Renderer показывает прежде всего materialized world state.

## 5. Сглаживание и resolution

Guide Renderer имеет право визуально интерполировать canonical scalar fields при rasterization.

Это разрешено, потому что:

```text
canonical field
→ presentation interpolation
→ pixels
```

не изменяет исходное поле.

v0.1 использует фиксированный target long edge:

```text
1600 px
```

Вторая сторона вычисляется из domain aspect ratio.

Карта не обязана сохранять видимые cell boundaries. Наоборот, цель Guide Renderer — убрать ощущение клеточной/ломаной debug-карты.

## 6. Frame / UI elements

Guide map v0.1:

- не показывает coordinate axes;
- не показывает grid lines;
- показывает north arrow;
- показывает scale bar;
- может иметь компактную unobtrusive legend только для действительно неоднозначных overlays;
- не показывает технические field colorbars по умолчанию.

## 7. Determinism boundary

Для одинаковой `DomainAssembly`, renderer version и rendering environment Guide Renderer должен быть deterministic.

Однако `guide-map.png` SHA НЕ является Core semantic golden и НЕ входит в M11 acceptance baseline.

Допустимы будущие presentation-only изменения visual grammar без изменения generator version, если они не затрагивают canonical world state. Renderer-specific versioning может быть добавлено позднее при необходимости.

## 8. API boundary

Новый downstream API v0.1:

```python
render_guide_map(
    assembly: DomainAssembly,
    output_path: Path,
) -> GuideRenderResult
```

`GuideRenderResult` должен содержать минимум:

- output path;
- width_px;
- height_px.

Renderer живёт рядом с presentation/rendering modules, но не импортируется generation stages.

Matplotlib остаётся optional `render` dependency; новый обязательный Core dependency не добавляется.

## 9. Application / CLI integration

Canonical generation semantics не меняются.

Application publication получает отдельную optional ветку:

```text
generate
→ DomainAssembly
→ canonical DomainBundle
→ optional technical preview
→ optional guide preview
```

CLI добавляет отдельный flag:

```text
--guide-preview
```

Существующий:

```text
--preview
```

сохраняет прежнее значение: technical preview.

Примеры:

```bash
domain-generator generate request.json \
  --presets presets.json \
  --output ./generated/map01 \
  --guide-preview
```

или оба одновременно:

```bash
domain-generator generate request.json \
  --presets presets.json \
  --output ./generated/map01 \
  --preview \
  --guide-preview
```

Output:

```text
preview/
  technical-map.png   # только --preview
  guide-map.png       # только --guide-preview
```

## 10. Remote GitHub integration

Remote adapter расширяется backward-compatible transport field:

```json
{
  "guide_preview": true
}
```

`workflow_dispatch` получает отдельный boolean `guide_preview`.

При successful generation + guide preview создаётся отдельный artifact:

```text
guide-preview
└─ guide-map.png
```

Существующие artifacts остаются без изменения:

```text
domain-bundle
technical-preview
generation-diagnostics
```

Remote wrapper по-прежнему вызывает canonical CLI ровно один раз. Добавление guide preview не разрешает reroll/replanning.

## 11. Demo region v0.1

Implementation обязан добавить отдельный representative demo input, предназначенный именно для визуального smoke-test:

```text
examples/guide-renderer/demo-region/
  request.json
  presets.json
```

Demo должен использовать только существующие Core capabilities и включать минимум:

- один выраженный ridge;
- один basin/lake-capable terrain feature;
- hydrology с наблюдаемой водой/river network;
- surface variation;
- минимум один dependent POI, если это остаётся устойчивым и не делает demo хрупким.

Рекомендуемый порядок масштаба:

```text
~48 × 32 км
cell size ~0.5 км
```

Это не acceptance baseline и не setting-specific content. Его задача — дать понятный visual smoke world.

## 12. Tests

Минимальные tests v0.1:

- renderer принимает `DomainAssembly` и создаёт PNG;
- output dimensions сохраняют domain aspect ratio и long edge 1600 px;
- rendered image non-uniform;
- water-present world содержит ненулевую water-colored area;
- hillshade/terrain path работает для flat и non-flat elevation;
- POI rendering не меняет assembly;
- repeated render одной assembly даёт deterministic pixels в текущем test environment;
- `--guide-preview` создаёт `preview/guide-map.png`;
- `--preview` сохраняет прежнее technical-only поведение;
- оба flags могут использоваться одновременно;
- remote wrapper принимает optional `guide_preview` и всё ещё вызывает canonical CLI один раз;
- GitHub workflow публикует `guide-preview` artifact;
- generation semantics/fingerprints/fields не меняются из-за guide rendering.

PNG hash не становится release-gating Core golden.

## 13. Реальный visual checkpoint

После implementation PR и green CI выполняется реальный remote demo run.

Проверка считается успешной только после человеческого просмотра `guide-map.png`:

```text
вид сверху читается как terrain map
ridge визуально воспринимается как форма рельефа
lake/water читается сразу
river network читается как река, а не набор debug cells
vegetation/terrain образуют цельную поверхность
нет dominant debug construction overlays
```

Это presentation acceptance, а не semantic Core acceptance.

Implementation PR НЕ merge-ится до отдельного явного пользовательского принятия этого visual checkpoint.

## 14. Out of scope v0.1

- художественная fantasy-карта;
- ImageGen/LLM внутри renderer;
- texture synthesis;
- buildings/roads/settlement footprints;
- biome simulation;
- physical river width/discharge model;
- contour-label cartography;
- interactive map UI;
- WebGL/3D rendering;
- mutation canonical fields ради более красивого preview;
- autonomous aesthetic reroll loop.

## 15. Будущий ImageGen track

Guide Renderer специально проектируется как подходящий spatial reference для будущего слоя:

```text
canonical world
→ guide-map.png
→ optional masks/references later
→ image generation / artistic transform
→ player-facing campaign map
```

Но ImageGen integration не входит в Guide Renderer v0.1 и не блокирует его.

## 16. Acceptance boundary

Design принят до implementation согласно INV-006.

Docs design merge разрешён после green CI. Runtime implementation идёт отдельным PR и требует отдельного явного принятия после реального visual demo.