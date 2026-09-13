---
id: DESIGN-TECHNICAL-RENDERER-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Technical Renderer v0.1

Этот документ фиксирует deterministic diagnostic renderer поверх уже принятого semantic world state. Renderer не является стадией generation и не изменяет `DomainData`, raster payloads, features или networks.

## 1. Назначение

Technical Renderer отвечает на вопрос: «что именно сгенерировал Core?».

Он создаёт техническую карту вида сверху, пригодную для:

- визуальной проверки generated geography;
- отладки и regression inspection;
- передачи человеку вместе с canonical bundle;
- использования downstream tools как географического reference artifact.

`technical-map.png` не является canonical world state и не заменяет `domain.json` или `fields/*.npy`.

## 2. Public boundary

Каноническая функция v0.1:

```python
render_technical_map(
    *,
    assembly: DomainAssembly,
    output_path: Path,
) -> RenderedTechnicalMap
```

Renderer получает уже готовый `DomainAssembly` и caller-provided output path.

Он не принимает:

- `DomainSpec`;
- `GenerationPlan`;
- `DomainCandidate`;
- RNG;
- generation configuration;
- setting-specific presentation style.

Runtime result содержит как минимум:

```python
root/path: Path
```

Точный runtime result type может быть минимальным dataclass и не входит в semantic `DomainData` contract.

## 3. Место в pipeline

```text
DomainSpec
   ↓
generation pipeline
   ↓
DomainAssembly
   ├── DomainData
   └── canonical raster payloads
          │
          ├──→ DomainBundle Export
          │
          └──→ Technical Renderer
                    ↓
             technical-map.png
```

Renderer downstream относительно generation/assembly. Его запуск или отсутствие не может влиять на generated world, candidate ranking или provenance.

## 4. Coordinate convention

Renderer использует уже принятую world-space convention:

```text
south-west = (0, 0)
+x = east
+y = north
north = top of image
```

Raster row `0` соответствует северной строке canonical grid и должен отображаться в верхней части карты без semantic inversion.

Оси и distance labels выражаются в километрах.

## 5. Aspect ratio и pixel size

Renderer сохраняет world-space aspect ratio domain.

Базовое правило v0.1:

```text
long side = 1600 px
```

Вторая сторона вычисляется пропорционально `DomainExtent`.

Примеры:

```text
100 × 100 km → 1600 × 1600 px
100 × 50 km  → 1600 × 800 px
50 × 100 km  → 800 × 1600 px
```

Renderer не растягивает domain до заранее заданного 16:9 или другого presentation ratio.

## 6. Базовые raster layers

Основная карта строится из canonical raster payloads.

Порядок базовых raster layers v0.1:

1. `elevation` — основа рельефа;
2. `vegetation_density` — полупрозрачный vegetation overlay;
3. `water_depth > 0` — water mask.

`moisture` существует в canonical data, но не рисуется отдельным overlay на основной technical map v0.1, чтобы не перегружать изображение. Отдельная moisture diagnostic map может быть добавлена позже отдельным design decision.

## 7. Raster resampling

Technical Renderer не должен скрыто придумывать дополнительную географию.

Canonical grid отображается без smoothing/interpolation, меняющих визуальную границу ячеек. Базовый raster interpolation v0.1 — nearest-neighbour / nearest-cell representation.

Renderer не выполняет terrain smoothing, super-resolution, erosion, coastline interpolation или иной semantic post-processing.

## 8. Hydrology layers

Поверх raster water mask отображаются canonical hydrology semantics:

- `HydroFeature` lake geometry как точные `RegionSet` polygons;
- `RiverNetwork` segments по canonical river centerlines;
- river direction может быть показан минимальными directional markers, если это не ухудшает читаемость.

Renderer не пересчитывает lake boundaries, river routing или discharge.

## 9. Semantic feature layers

Feature geometry отображается по существующим contracts:

```text
Point / POI     marker
Corridor        centerline
Area            polygon outline/fill
Surface Area    translucent area overlay
Band            centerline + width indications
HydroFeature    polygonal water feature
```

Для `BandGeometry` v0.1 запрещено самостоятельно создавать semantic polygon footprint, потому что canonical contract содержит centerline + width profile, а не готовый polygon footprint. Renderer показывает имеющиеся данные без hidden geometry synthesis.

## 10. Labels

Если feature имеет `label`, renderer использует его как primary visible label.

Если `label` отсутствует, для technical/debug readability разрешено использовать `feature_id`.

Label placement является presentation concern. v0.1 не обещает sophisticated collision-free cartographic labelling; при конфликте labels предпочтение отдаётся сохранению geography и минимизации визуального шума.

## 11. Legend и orientation aids

Technical map v0.1 содержит минимальные technical aids:

- north indicator;
- distance scale или world-coordinate ticks;
- compact legend для основных layer types;
- domain boundary.

Эти элементы не являются semantic world data.

## 12. Rendering dependency

Предлагаемая implementation dependency — Matplotlib с headless `Agg` backend.

Renderer dependency не должна становиться обязательной dependency чистого procedural Core.

Целевой packaging boundary:

```text
pip install domain-generator
```

— generation без renderer dependency.

```text
pip install domain-generator[render]
```

— generation + technical rendering.

Точная совместимая версия Matplotlib фиксируется implementation PR в `pyproject.toml`.

## 13. Platform independence

Renderer должен работать в поддерживаемых Python environments без desktop GUI:

- Windows 10+;
- Linux / Linux Mint / Ubuntu-like systems;
- GitHub Actions Linux runner.

`Agg`/headless rendering не должно требовать X11, Tk или desktop session.

Filesystem paths обрабатываются через `pathlib.Path`.

## 14. Output path и directory semantics

Имя `preview/technical-map.png` является рекомендуемым bundle placement, но public API принимает arbitrary caller-provided `output_path`.

Renderer может создать непосредственную parent directory для requested image, например:

```text
bundle/
  preview/
    technical-map.png
```

Он не должен создавать произвольные внешние project trees вне requested output path.

## 15. Existing target semantics

v0.1 не поддерживает silent overwrite.

Если `output_path` уже существует, renderer завершает работу explicit render error.

Overwrite/force mode может быть добавлен позже отдельным design decision.

## 16. Atomic visibility

Renderer пишет изображение во временный sibling path и публикует final PNG только после успешной render/write операции.

Концептуально:

```text
validate input
→ ensure immediate parent directory
→ render to temporary sibling
→ verify completed PNG write
→ rename temporary file → final output_path
```

Normal failure вызывает best-effort cleanup temporary artifact.

Crash/OS failure может оставить recognisable temporary file; он не считается completed technical map.

## 17. Determinism boundary

При одинаковом `DomainAssembly`, renderer version и поддерживаемом dependency/runtime environment renderer должен выдавать один и тот же визуальный результат.

Technical image не входит в semantic reproducibility identity generated world.

Byte-identical PNG между произвольными будущими версиями Matplotlib/Pillow/font stack/platform не гарантируется. INV-009 применяется к exact supported implementation/version boundary.

## 18. Mutation и RNG запрещены

Technical Renderer:

- не мутирует `DomainData`;
- не мутирует raster arrays;
- не использует Core RNG;
- не вызывает generation stages;
- не reroll-ит candidate;
- не меняет validation/ranking;
- не создаёт новые semantic features;
- не исправляет canonical geography;
- не становится источником истины для дальнейшей simulation.

INV-008 сохраняется: наличие/отсутствие preview не влияет на semantic result.

## 19. Отношение к image generation / художественной карте

`technical-map.png` — diagnostic artifact, а не обещание оптимального control image для image-generation model.

Нельзя полагаться на то, что downstream image model надёжно прочитает raw `.npy` payloads или semantic JSON/vector contracts как точную spatial instruction. Canonical data остаётся машинным источником истины, но image-generation adapter должен получать специально подготовленный визуальный reference/control artifact.

Также не следует считать nearest-neighbour technical raster идеальным входом для художественной стилизации: image model может буквально наследовать клеточную структуру reference image.

Поэтому будущая presentation architecture может иметь отдельный производный слой:

```text
DomainData + canonical rasters + vectors
        ↓
Presentation / imagegen guide renderer
        ↓
imagegen-guide.png
        ↓
image-generation / artistic transform
        ↓
campaign-map.png
```

`imagegen-guide.png` должен сохранять canonical geography, но может использовать presentation-oriented continuous shading, vector masks, coast/river overlays и другие способы сделать spatial structure понятной image model без изменения world semantics.

Этот presentation/imagegen guide renderer НЕ входит в Technical Renderer v0.1 и требует отдельного design decision.

## 20. Что не входит в v0.1

- художественный parchment/fantasy style;
- neural image generation;
- `imagegen-guide.png`;
- 3D terrain;
- interactive map/UI;
- tiles;
- SVG/GeoTIFF export;
- cartographic contour generation;
- sophisticated label placement;
- setting-specific icons;
- political borders;
- player/GM visibility variants;
- semantic smoothing или world modification.

## 21. Implementation scope после docs merge

После merge принятой normative design documentation отдельный implementation PR должен содержать только bounded renderer slice:

- optional `render` dependency;
- technical renderer module/API;
- deterministic layer composition;
- safe/atomic PNG output;
- tests orientation/aspect/layer presence/no-mutation/path semantics;
- status documentation.

Implementation PR не merge-ится без отдельного явного принятия пользователя.

## 22. Следующий основной checkpoint

После implementation и отдельного принятия `Technical Renderer v0.1` основной roadmap продолжится:

```text
canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide layer остаётся отдельной downstream задачей и не блокирует canonical CLI.
