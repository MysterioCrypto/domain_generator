---
id: DESIGN-END-TO-END-RUNTIME-BUNDLE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# Сквозная архитектура runtime и bundle v0.1

Этот документ фиксирует внешнюю границу исполнения `domain_generator`: один и тот же детерминированный Core должен запускаться локально и в удалённом runner-е без двух разных реализаций generation.

## 1. Один Core, один процесс

`domain_generator` является Python package. Внутренние stages вызываются как функции в одном Python process и передают runtime objects/NumPy arrays в памяти.

```text
DomainSpec
  -> Compiler
  -> GenerationPlan
  -> Layout
  -> Terrain
  -> Hydrology
  -> Surface
  -> Dependent Placement
  -> Final Validation
  -> DomainData Assembly
```

Core не строится как цепочка subprocess scripts и не использует filesystem как внутреннюю шину между stages.

## 2. Каноническая граница запуска

Локальное и удалённое исполнение должны вызывать один и тот же public entrypoint с одинаковой семантикой CLI:

```text
domain-generator generate <request> --output <directory>
```

Конкретное имя CLI может быть реализовано позже; архитектурное требование — один entrypoint generation поверх того же API package.

Внутри application/API допустим эквивалентный вызов Python-функции:

```text
generate_domain(spec, config) -> DomainAssembly / DomainBundle-ready result
```

CLI, локальный skill, GitHub workflow и другие adapters не имеют права повторно реализовывать алгоритмы Core.

## 3. Input adapters

Канонический семантический input после parsing — `DomainSpec` + semantic `GenerationConfig`.

Contracts Core не зависят от формата файла. JSON является естественным базовым сериализованным input. YAML может быть внешним adapter-ом, преобразующим данные в те же Pydantic contracts.

```text
JSON ----\
          -> parser/adapter -> DomainSpec + GenerationConfig -> Core
YAML ----/
```

Загрузка и parsing файлов не являются стадией generation.

## 4. Локальный режим исполнения

Основной быстрый режим:

```text
human / model
    -> local adapter or skill
    -> validated request
    -> local CLI / Python API
    -> domain_generator
    -> local output bundle
```

Целевая среда runtime:

- Python 3.11+;
- NumPy;
- Pydantic;
- Shapely;
- CPU + RAM; GPU не является обязательной dependency Core 0.1.

Локальный skill/prompt может объяснять модели schema, команду запуска и правила чтения output, но остаётся внешним adapter-ом и не входит в Core.

## 5. Удалённый режим исполнения

Машинонезависимое исполнение использует тот же entrypoint generation в ephemeral runner-е.

Эталонный поток GitHub:

```text
model / client
    -> commit request JSON under input/requests/
    -> GitHub Actions workflow
    -> checkout exact generator revision
    -> install package
    -> run canonical generate entrypoint
    -> upload generated bundle as workflow artifact
```

Generated binaries/rasters не обязаны коммититься обратно в Git repository. Repository хранит request/provenance; generated output предпочтительно передаётся как workflow artifact.

GitHub Actions является adapter-ом исполнения и CI infrastructure, а не dependency Core.

## 6. Воспроизводимость между средами исполнения

При одинаковых поддерживаемых semantic inputs, точной версии generator и версии RNG локальное и удалённое исполнение должны давать один семантический результат.

Место исполнения, logging, debug flags и transport artifacts не должны влиять на generated world.

Удалённое исполнение может использоваться как независимая проверка воспроизводимости локального результата.

## 7. Граница DomainAssembly

После выбора принятого `DomainCandidate` generation заканчивается. Assembly не генерирует новое состояние мира.

Предлагаемая граница в памяти:

```text
DomainAssembly
  data: DomainData
  field_payloads:
    elevation
    water_depth
    moisture
    vegetation_density
```

`field_payloads` содержат canonical NumPy arrays. `DomainData.fields` содержит descriptors будущих persisted artifacts.

Assembler:

- не использует RNG;
- не выполняет IO;
- не меняет принятый candidate;
- не пересчитывает terrain/hydrology/surface;
- не выполняет rendering.

## 8. Физическая структура DomainBundle

Эталонная структура bundle:

```text
output/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
  preview/
    technical-map.png        # optional presentation artifact
  debug/                     # optional observability artifacts
```

Канонический источник истины разделён:

- `domain.json` — structured semantic metadata, features, networks, descriptors fields и provenance;
- `fields/*.npy` — canonical числовые payloads raster;
- preview/debug files — non-canonical derived/presentation artifacts.

Exporter отвечает за физическую запись bundle и semantics atomic/path/error. Exporter не меняет семантический результат.

## 9. Владение raster-данными

Канонические сохраняемые rasters Core 0.1:

```text
elevation.npy             float32 meters
water_depth.npy           float32 meters
moisture.npy              float32 normalized [0,1]
vegetation_density.npy    float32 normalized [0,1]
```

`domain.json` не встраивает эти массивы как огромные JSON lists; он хранит относительные descriptors (`path`, `dtype`, `shape`, `unit`).

Renderer и downstream tools читают rasters через эти descriptors.

## 10. Граница renderer

Technical renderer — отдельный downstream component:

```text
DomainData + raster payloads
    -> deterministic technical renderer
    -> technical-map.png
```

Technical preview должен отражать canonical geography, но PNG не является состоянием мира.

Renderer не изменяет `DomainData`/rasters и может быть заменён без reroll generation.

## 11. Граница представления и image generation

Художественная генерация карты находится ещё дальше от Core:

```text
technical-map.png
+ presentation/style brief
    -> image generation / artistic transform
    -> campaign-map.png
```

`campaign-map.png` является artifact представления, а не canonical map data. Image generation не имеет права незаметно менять underlying generated world.

Допустимы разные варианты представления одного `DomainBundle` — GM/player/parchment и т. п. — без повторной procedural generation.

## 12. Интеграция с моделью

LLM/agent работает на уровне intent и orchestration:

```text
natural-language request
    -> external model adapter
    -> DomainSpec / GenerationConfig
    -> canonical generator entrypoint
    -> DomainBundle + summary + technical preview
    -> model/user
```

Модель не управляет внутренними stages напрямую и не генерирует вручную values raster cells.

Локальный skill и удалённый GitHub adapter могут иметь разный UX, но оба работают через один contract Core.

## 13. Роль GitHub Actions

GitHub Actions допустим для:

- pytest/CI;
- детерминированных проверок reference generation;
- удалённых requests generation;
- загрузки bundle artifact;
- проверок release/package.

Он не является каноническим runtime requirement. Core должен выполняться без GitHub.

## 14. Разделение ответственности

```text
Core generation
  -> world semantics

Final Validation
  -> candidate validity/ranking

Assembler
  -> accepted runtime state -> DomainData + payload references

Exporter
  -> filesystem bundle

Renderer
  -> deterministic technical image

Presentation adapter / image generation
  -> artistic derivative

Local skill / GitHub workflow
  -> execution/orchestration surfaces
```

Ни один downstream layer не должен скрыто изменять семантику мира.

## 15. Последовательность реализации

После принятия этой архитектурной базы реализация идёт отдельными ограниченными checkpoints:

1. Final Validation v0.1;
2. Soft Constraint Compilation & Scoring v0.1;
3. HydroFeature / materialization lake v0.1;
4. DomainData Assembler v0.1;
5. DomainBundle Export v0.1;
6. Technical Renderer v0.1;
7. canonical CLI / Python application entrypoint;
8. local model skill/adapter;
9. remote GitHub Actions generation adapter.

Порядок может уточняться только явным design decision; Core и adapters исполнения остаются разделены.

## Что не определяет этот документ

- конкретный художественный стиль campaign map;
- конкретного LLM provider;
- presets конкретного сеттинга;
- production web service;
- cloud database;
- визуальный язык renderer;
- GitHub как обязательный backend;
- скрытую генерацию через image model.
