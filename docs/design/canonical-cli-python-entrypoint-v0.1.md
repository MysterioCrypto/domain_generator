---
id: DESIGN-CANONICAL-CLI-PYTHON-ENTRYPOINT-0.1
kind: design
status: accepted
normative: true
target: core-0.1
implemented: true
---

# Canonical CLI / Python Application Entrypoint v0.1

Этот документ фиксирует единую application-level границу запуска `domain_generator` поверх уже реализованных compiler, generation pipeline, assembler, bundle exporter и technical renderer.

## 1. Цель

Локальный запуск, будущий local model adapter и будущий remote GitHub Actions adapter должны использовать одну и ту же orchestration semantics. CLI не повторяет algorithms Core и не создаёт альтернативный generation pipeline.

Canonical flow:

```text
DomainSpec + GenerationConfig + PresetRegistry
        ↓
compile_domain_spec(...)
        ↓
GenerationPlan
        ↓
run_generation(...)
        ↓
selected DomainCandidate
        ↓
assemble_domain(...)
        ↓
DomainAssembly
```

Filesystem application layer может затем экспортировать bundle и опционально построить technical preview.

## 2. Канонический Python API

Public semantic orchestration API v0.1:

```python
generate_domain(
    *,
    spec: DomainSpec,
    config: GenerationConfig,
    registry: PresetRegistry,
) -> DomainAssembly
```

`generate_domain()`:

- использует текущий `domain_generator.__version__` как `generator_version`;
- вызывает compiler;
- запускает фиксированный Core pipeline;
- выбирает candidate только через существующий `run_generation()`;
- передаёт `run.selected` в `assemble_domain()`;
- не выполняет filesystem IO;
- не экспортирует bundle;
- не рендерит PNG;
- не подменяет stage semantics.

## 3. Фиксированный stage order

Canonical application использует ровно следующие handlers и их существующий порядок:

```text
layout_stage
→ terrain_stage
→ hydrology_stage
→ surface_stage
→ placement_stage
→ final_stage
```

CLI и adapters не получают параметр для перестановки, пропуска или подмены stages. Low-level Python APIs остаются доступны для tests и разработки, но canonical application entrypoint имеет фиксированный pipeline.

## 4. GenerationRequest v0.1

Базовый serialized input — JSON contract:

```json
{
  "request_version": "0.1",
  "domain_spec": { "...": "DomainSpec" },
  "generation_config": { "...": "GenerationConfig" }
}
```

`GenerationRequest` содержит только semantic/execution input generation. Он не содержит:

- output directory;
- absolute filesystem paths;
- GitHub-specific fields;
- renderer output paths;
- platform-specific settings.

Один request должен быть переносим между Windows, Linux и remote runner.

## 5. PresetCatalog v0.1

Preset definitions не встраиваются в каждый `GenerationRequest` и не зашиваются в setting-agnostic Core.

Базовый serialized catalog:

```json
{
  "preset_catalog_version": "0.1",
  "presets": [
    { "...": "PresetDefinition" }
  ]
}
```

Catalog является внешним reusable input. Setting/project-specific catalogs могут жить вне репозитория Core.

В v0.1 поддерживается JSON. YAML допускается позже только как внешний adapter к тем же contracts.

## 6. Registry и capability set

`PresetRegistry` остаётся runtime compiler dependency. Application строит registry из validated `PresetCatalog` и versioned capability set самого Core.

Пользовательский catalog не задаёт `operator_ids`.

Canonical supported operator ids v0.1 соответствуют реально реализованным operators:

```text
raise
depress
ridge
flatten
moisture_bias
vegetation_bias
suitability_placement
```

Если catalog ссылается на operator вне capability set текущей версии, registry construction завершается explicit error.

Это не гарантирует, что любой произвольный preset с разрешённым operator корректен: compiler/stage capability validation по-прежнему остаётся authoritative.

## 7. Filesystem application API

Поверх semantic API определяется application orchestration:

```python
generate_domain_bundle(
    *,
    request: GenerationRequest,
    registry: PresetRegistry,
    output_dir: Path,
    render_preview: bool = False,
) -> GenerateApplicationResult
```

Его задача:

```text
GenerationRequest
→ generate_domain(...)
→ DomainAssembly
→ DomainBundle Export
→ optional Technical Renderer
→ publish final application output
```

Application не меняет semantic world state.

## 8. Atomic application output

Если запрошен preview, успешным считается только полный requested result.

Application создаёт temporary sibling root и внутри него выполняет export + optional render. После успешного завершения весь application result публикуется final rename.

```text
validate inputs
→ generate DomainAssembly
→ create temporary sibling application root
→ export canonical bundle into temporary root
→ if requested: render preview/technical-map.png
→ final rename temporary root → output_dir
```

Если export или requested renderer завершается ошибкой, final `output_dir` не должен выглядеть успешно опубликованным.

Обычные исключения вызывают best-effort cleanup temporary tree. Power loss/SIGKILL могут оставить recognisable temporary directory, но не final target.

## 9. Existing target и parent semantics

Core 0.1 application сохраняет консервативное no-overwrite правило:

```text
output_dir already exists → explicit error
```

`--force` / overwrite отсутствуют.

Parent `output_dir.parent` должен существовать и быть directory. Application не создаёт произвольную отсутствующую parent chain.

Внутренний immediate `preview/` directory разрешено создать только внутри temporary application root.

## 10. Canonical CLI

Package устанавливает console script:

```text
domain-generator
```

Основная команда:

```text
domain-generator generate <request.json> --output <directory>
```

С внешним catalog:

```text
domain-generator generate <request.json> \
  --presets <presets.json> \
  --output <directory>
```

С technical preview:

```text
domain-generator generate <request.json> \
  --presets <presets.json> \
  --output <directory> \
  --preview
```

Mandatory `input/`, `requests/` или `output/` directories не существуют. Пути задаются caller-ом.

Relative paths разрешаются обычными правилами `pathlib.Path` относительно current working directory.

## 11. Preset catalog requirement

Если `DomainSpec.features` пуст, `--presets` может отсутствовать; application строит пустой registry с canonical Core operator capability set.

Если `DomainSpec.features` непуст и `--presets` не указан, CLI завершает запуск explicit input/configuration error до compiler execution.

Никакого скрытого built-in setting catalog или угадывания preset по id нет.

## 12. Preview dependency

Canonical bundle generation не требует Matplotlib.

`--preview` требует установленный optional extra:

```text
domain-generator[render]
```

Если preview requested, но renderer dependency отсутствует, application завершает output failure до final publication.

`--preview` не является частью `GenerationConfig.semantic` и не влияет на generation fingerprint/world semantics.

## 13. Output layout

Без preview:

```text
<output_dir>/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
```

С preview:

```text
<output_dir>/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
  preview/
    technical-map.png
```

Preview остаётся non-canonical derived artifact и не входит в `BundleManifest.canonical_files`.

## 14. Exit codes

Stable CLI exit classes v0.1:

```text
0   success
2   invalid CLI arguments
3   request / preset catalog parse or validation error
4   compile / unsupported generation capability / attempts exhausted
5   assembly / export / render / filesystem failure
70  internal invariant violation or unexpected application failure
```

CLI не должен выбрасывать traceback как нормальный пользовательский protocol. Diagnostic message идёт в stderr; unexpected/internal failure может дополнительно показывать traceback только в explicit debug/development mode, если такой режим будет добавлен отдельно.

## 15. Structured stdout

На success stdout содержит один JSON object, пригодный для adapter/automation parsing.

Минимальные поля:

```json
{
  "status": "ok",
  "domain_id": "north-region",
  "accepted_attempt_index": 3,
  "output_dir": "./generated/north",
  "technical_preview": "preview/technical-map.png"
}
```

Если preview не создавался, `technical_preview` = `null`.

Человекоориентированный progress/logging не смешивается с structured stdout; diagnostics идут в stderr.

## 16. Generator version

CLI не принимает пользовательский `--generator-version`.

Compiler получает version из установленного package:

```text
domain_generator.__version__
```

Это защищает provenance от произвольного spoofing через CLI flag.

## 17. GenerationConfig

`GenerationConfig` находится внутри `GenerationRequest`, потому что `max_attempts` и `target_valid_candidates` являются semantic execution settings и могут изменить selected candidate.

Observability settings остаются частью existing contract и не должны менять semantic result согласно INV-008.

Application presentation options (`--preview`) не включаются в semantic config fingerprint.

## 18. Error boundary Python API

`generate_domain()` не скрывает существующие typed Core errors за одним generic exception. Python callers могут различать compiler/generation/capability/assembly failures.

Filesystem application layer может вводить собственный `ApplicationInputError` / `ApplicationOutputError` для file parsing, publication и adapter-level failures, сохраняя исходное exception через chaining.

CLI переводит эти exception classes в stable exit code classes.

## 19. Platform portability

Implementation использует `pathlib.Path` и не хранит host absolute paths внутри canonical `DomainData`/bundle descriptors.

Target environments:

```text
Windows 10+
Linux Mint / generic Linux
Ubuntu GitHub Actions runner
Python 3.11+
```

Filesystem metadata не является semantic output.

## 20. Out of scope v0.1

Не входят:

- YAML input;
- built-in Valhalla или другие setting-specific presets;
- interactive prompts;
- web UI/service;
- GitHub Actions generation workflow;
- local LLM skill;
- ImageGen / campaign-map generation;
- overwrite/force;
- resume;
- parallel attempts;
- remote API;
- production generic preset catalog.

## 21. Implementation checkpoint после docs merge

После merge этого принятого design реализация отдельным PR включает:

- `GenerationRequest` typed contract;
- `PresetCatalog` typed contract и JSON loaders;
- generated JSON Schema snapshots для новых serialized contracts;
- `CORE_OPERATOR_IDS`;
- `generate_domain()`;
- `generate_domain_bundle()` + atomic publication;
- console script `domain-generator`;
- `generate` command;
- `--presets`, `--output`, `--preview`;
- stable exit code mapping и structured stdout;
- tests Windows/POSIX-independent path semantics на уровне `pathlib`;
- status docs.

Implementation PR не merge-ится без отдельного пользовательского принятия checkpoint.
