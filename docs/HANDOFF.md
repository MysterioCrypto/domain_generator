# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
4. Прочитать `docs/design/domain-bundle-export-v0.1.md`.
5. Прочитать `docs/design/technical-renderer-v0.1.md`.
6. Прочитать `docs/design/canonical-cli-python-entrypoint-v0.1.md`.
7. Соблюдать INV-006: существенные изменения сначала обсуждаются и документируются.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

Базовый `main` PR #44:

```text
8a6fec23ddf14d2e64ac6153c841c1f6b05bbe1d
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup — merged;
- PR #32 Soft Constraint Compilation & Scoring — merged;
- PR #33/#34 HydroFeature / Lake Materialization design + implementation — merged;
- PR #35/#36 DomainData Assembler design + implementation — merged;
- PR #37/#38 DomainBundle Export design + implementation — merged;
- PR #39 exporter status sync — merged;
- PR #40/#41 Technical Renderer design + implementation — merged;
- PR #42 renderer status sync — merged;
- PR #43 Canonical CLI / Python Application Entrypoint normative design — merged.

Последний принятый implementation checkpoint в `main` — `Technical Renderer v0.1`.

## Текущий implementation checkpoint

PR #44 `Implement Canonical CLI / Python Application Entrypoint v0.1` открыт и **не должен merge-иться без отдельного принятия пользователя**.

Implementation branch:

```text
impl/m2-canonical-cli-python-entrypoint-v0.1
```

Подтверждённый полный functional CI до финального status-doc sync:

```text
312 passed
```

## Что реализовано в PR #44

### Application contracts

- `GenerationRequest v0.1` = `DomainSpec + GenerationConfig`;
- `PresetCatalog v0.1` = reusable tuple `PresetDefinition`;
- committed JSON Schema snapshots для обоих;
- schema-export теперь содержит 9 root contracts;
- duplicate preset ids запрещены.

### Core capability boundary

Canonical `CORE_OPERATOR_IDS`:

```text
raise
depress
ridge
flatten
moisture_bias
vegetation_bias
suitability_placement
```

Catalog не может объявлять произвольные capabilities. Registry строится application layer-ом из catalog + этого набора.

### Canonical Python API

```python
generate_domain(
    *,
    spec: DomainSpec,
    config: GenerationConfig,
    registry: PresetRegistry,
) -> DomainAssembly
```

Fixed stage order:

```text
layout_stage
→ terrain_stage
→ hydrology_stage
→ surface_stage
→ placement_stage
→ final_stage
```

`generate_domain()` использует installed package `__version__`, existing compiler, `run_generation()` и `assemble_domain()`; filesystem IO и rendering внутри отсутствуют.

### Filesystem application API

```python
generate_domain_bundle(
    *,
    request: GenerationRequest,
    registry: PresetRegistry,
    output_dir: Path,
    render_preview: bool = False,
) -> GenerateApplicationResult
```

Публикация atomic на application level:

```text
generate DomainAssembly
→ temporary sibling application root
→ DomainBundle Export
→ optional preview/technical-map.png
→ final rename to output_dir
```

Existing target не перезаписывается. Normal failure очищает staging best-effort.

### CLI

Installed console script:

```text
domain-generator
```

Команды:

```text
domain-generator generate <request.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir> --preview
```

При непустом feature set отсутствие `--presets` — input error. Если features пусты, catalog может отсутствовать.

Exit classes:

```text
0 success
2 invalid CLI arguments
3 input parse/validation
4 compile/generation/capability/attempt exhaustion
5 assembly/export/render/filesystem
70 internal invariant/unexpected failure
```

Success stdout — один JSON object; diagnostics — stderr.

## Platform/path semantics

Mandatory `input/`, `requests/`, `output/` directories отсутствуют. Caller передаёт paths; implementation использует `pathlib.Path`. Canonical persisted descriptors остаются POSIX-relative, поэтому bundle переносим между Windows и Linux.

## Technical Renderer / ImageGen boundary

`--preview` вызывает существующий optional Technical Renderer и создаёт diagnostic non-canonical `preview/technical-map.png`. Это не финальная художественная карта.

Будущий отдельный flow:

```text
DomainData + canonical rasters + vectors
        ↓
Presentation / imagegen guide renderer
        ↓
imagegen-guide.png
        ↓
image generation
        ↓
campaign-map.png
```

Он не входит в PR #44.

## Tests

Новые tests покрывают:

- request/catalog JSON parsing;
- contract/schema round trips;
- explicit operator capability boundary;
- full canonical empty-feature pipeline;
- installed package version in provenance;
- canonical bundle publication;
- preview publication;
- existing-target protection;
- cleanup после renderer failure;
- missing output parent;
- missing preset catalog при features;
- unknown preset generation error;
- duplicate preset ids;
- unsupported catalog operator;
- argparse exit 2;
- structured stdout и preview relative path.

Полный suite: `312 passed` до финального status-doc commit.

## Рабочий процесс

- Design v0.1 уже принят и merged через PR #43.
- Implementation PR #44 сейчас проходит финальный CI.
- PR #44 не merge-ить без отдельного `Принято.` пользователя.

После принятия/merge следующий bounded design gate:

```text
local model skill/adapter
```

Затем:

```text
remote GitHub Actions generation adapter
```

Presentation/imagegen guide renderer остаётся отдельной downstream задачей.
