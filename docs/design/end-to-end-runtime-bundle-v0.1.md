---
id: DESIGN-END-TO-END-RUNTIME-BUNDLE-0.1
kind: design-baseline
status: accepted
normative: true
target: core-0.1
implemented: false
---

# End-to-End Runtime & Bundle Architecture v0.1

Этот документ фиксирует внешний execution boundary `domain_generator`: один и тот же deterministic Core должен запускаться локально и в удалённом runner-е без двух разных generation implementations.

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

## 2. Canonical executable boundary

Local и remote execution должны вызывать один и тот же public entrypoint / CLI semantics:

```text
domain-generator generate <request> --output <directory>
```

Конкретное имя CLI может быть реализовано позже; архитектурное требование — один generation entrypoint поверх того же package API.

Внутри application/API допустим equivalent вызов Python-функции:

```text
generate_domain(spec, config) -> DomainAssembly / DomainBundle-ready result
```

CLI, local skill, GitHub workflow и другие adapters не имеют права повторно реализовывать algorithms Core.

## 3. Input adapters

Canonical semantic input после parsing — `DomainSpec` + semantic `GenerationConfig`.

Core contracts не зависят от формата файла. JSON является естественным baseline serialized input. YAML может быть внешним adapter-ом, преобразующим данные в те же Pydantic contracts.

```text
JSON ----\
          -> parser/adapter -> DomainSpec + GenerationConfig -> Core
YAML ----/
```

File loading/parsing не является generation stage.

## 4. Local execution mode

Основной быстрый режим:

```text
human / model
    -> local adapter or skill
    -> validated request
    -> local CLI / Python API
    -> domain_generator
    -> local output bundle
```

Target runtime:

- Python 3.11+;
- NumPy;
- Pydantic;
- Shapely;
- CPU + RAM; GPU не является обязательной dependency Core 0.1.

Local skill/prompt может объяснять модели schema, команду запуска и правила чтения output, но остаётся внешним adapter-ом и не входит в Core.

## 5. Remote execution mode

Machine-independent execution использует тот же generation entrypoint в ephemeral runner-е.

Reference GitHub flow:

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

GitHub Actions является execution adapter и CI infrastructure, а не dependency Core.

## 6. Reproducibility across execution surfaces

При одинаковых supported semantic inputs, exact generator version и RNG version local и remote execution должны давать один semantic result.

Execution location, logging, debug flags и artifact transport не должны влиять на generated world.

Remote execution может использоваться как independent reproducibility check локального result.

## 7. DomainAssembly boundary

После выбора accepted `DomainCandidate` generation заканчивается. Assembly не генерирует новый world state.

Предлагаемый in-memory boundary:

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
- не меняет accepted candidate;
- не пересчитывает terrain/hydrology/surface;
- не делает rendering.

## 8. DomainBundle physical layout

Reference bundle layout:

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

Canonical source-of-truth разделён:

- `domain.json` — structured semantic metadata, features, networks, field descriptors and provenance;
- `fields/*.npy` — canonical raster numeric payloads;
- preview/debug files — non-canonical derived/presentation artifacts.

Exporter отвечает за физическую запись bundle и atomic/path/error semantics. Exporter не меняет semantic result.

## 9. Raster ownership

Core 0.1 canonical persisted rasters:

```text
elevation.npy             float32 meters
water_depth.npy           float32 meters
moisture.npy              float32 normalized [0,1]
vegetation_density.npy    float32 normalized [0,1]
```

`domain.json` не встраивает эти массивы как огромные JSON lists; он хранит relative descriptors (`path`, `dtype`, `shape`, `unit`).

Renderer и downstream tools читают rasters через эти descriptors.

## 10. Renderer boundary

Technical renderer — отдельный downstream component:

```text
DomainData + raster payloads
    -> deterministic technical renderer
    -> technical-map.png
```

Technical preview должен отражать canonical geography, но PNG не является world state.

Renderer не изменяет DomainData/rasters и может быть заменён без reroll generation.

## 11. Presentation / image-generation boundary

Artistic map generation находится ещё дальше от Core:

```text
technical-map.png
+ presentation/style brief
    -> image generation / artistic transform
    -> campaign-map.png
```

`campaign-map.png` является presentation artifact, а не canonical map data. Image generation не имеет права незаметно менять underlying generated world.

Допустимы разные presentations одного DomainBundle (GM/player/parchment/etc.) без повторной procedural generation.

## 12. Model integration

LLM/agent работает над уровнем intent и orchestration:

```text
natural-language request
    -> external model adapter
    -> DomainSpec / GenerationConfig
    -> canonical generator entrypoint
    -> DomainBundle + summary + technical preview
    -> model/user
```

Модель не управляет внутренними stages напрямую и не генерирует вручную raster cell values.

Local skill и remote GitHub adapter могут иметь разные UX, но оба работают через одинаковый Core contract.

## 13. GitHub Actions role

GitHub Actions допустим для:

- pytest/CI;
- deterministic reference-generation checks;
- remote generation requests;
- bundle artifact upload;
- release/package checks.

Он не является canonical runtime requirement. Core должен выполняться без GitHub.

## 14. Separation of responsibilities

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

Ни один downstream layer не должен скрыто изменять world semantics.

## 15. Implementation sequence

После принятия этого architecture baseline implementation идёт отдельными bounded checkpoints:

1. Final Validation v0.1;
2. HydroFeature / lake materialization v0.1;
3. DomainData Assembler v0.1;
4. DomainBundle Export v0.1;
5. Technical Renderer v0.1;
6. canonical CLI / Python application entrypoint;
7. local model skill/adapter;
8. remote GitHub Actions generation adapter.

Порядок может уточняться только явным design decision; Core и execution adapters остаются разделены.

## Non-goals

Этот документ не определяет:

- конкретную campaign-map art style;
- конкретный LLM provider;
- setting-specific presets;
- production web service;
- cloud database;
- renderer visual language;
- GitHub как обязательный backend;
- скрытую генерацию через image model.
