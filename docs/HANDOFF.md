# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
4. Прочитать `docs/design/domain-bundle-export-v0.1.md`.
5. Прочитать `docs/design/technical-renderer-v0.1.md`.
6. Прочитать `docs/design/canonical-cli-python-entrypoint-v0.1.md`.
7. Не менять архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

Базовый `main` принятого canonical entrypoint design:

```text
0eaf1b0269afd39089be0975c504601df5f28685
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33/#34 HydroFeature / Lake Materialization design + implementation — merged;
- PR #35/#36 DomainData Assembler design + implementation — merged;
- PR #37/#38 DomainBundle Export design + implementation — merged;
- PR #39 post-merge exporter status sync — merged;
- PR #40 Technical Renderer v0.1 normative design — merged;
- PR #41 Technical Renderer v0.1 implementation — accepted and merged;
- PR #42 post-merge Technical Renderer status sync — merged.

Последний принятый implementation checkpoint — `Technical Renderer v0.1`. Полный CI implementation PR #41: `290 passed`.

## Текущий design checkpoint

`Canonical CLI / Python Application Entrypoint v0.1` принят пользователем.

Normative design:

```text
docs/design/canonical-cli-python-entrypoint-v0.1.md
```

Design фиксирует:

```text
GenerationRequest JSON
+ external PresetCatalog JSON
        ↓
PresetRegistry + CORE_OPERATOR_IDS
        ↓
generate_domain(...)
        ↓
Compiler
→ fixed Core stages
→ deterministic selection
→ DomainData Assembler
        ↓
DomainAssembly
        ↓
DomainBundle Export
        ↓
optional Technical Renderer
        ↓
atomic application output
```

## Канонический Python API

```python
generate_domain(
    *,
    spec: DomainSpec,
    config: GenerationConfig,
    registry: PresetRegistry,
) -> DomainAssembly
```

`generate_domain()` не выполняет filesystem IO/rendering и не предоставляет caller-у переставлять canonical stage order.

Фиксированный order:

```text
layout_stage
→ terrain_stage
→ hydrology_stage
→ surface_stage
→ placement_stage
→ final_stage
```

## Serialized application inputs

`GenerationRequest v0.1`:

```json
{
  "request_version": "0.1",
  "domain_spec": { "...": "DomainSpec" },
  "generation_config": { "...": "GenerationConfig" }
}
```

`PresetCatalog v0.1`:

```json
{
  "preset_catalog_version": "0.1",
  "presets": [ { "...": "PresetDefinition" } ]
}
```

Preset catalog остаётся внешним reusable input и не является built-in setting catalog Core. В v0.1 serialized baseline — JSON; YAML позже может быть adapter-ом.

Пользовательский catalog не задаёт `operator_ids`. Core application использует canonical capability set текущей версии:

```text
raise
depress
ridge
flatten
moisture_bias
vegetation_bias
suitability_placement
```

## CLI semantics

Основной запуск:

```text
domain-generator generate <request.json> --output <directory>
```

При features:

```text
domain-generator generate <request.json> --presets <presets.json> --output <directory>
```

Technical preview:

```text
domain-generator generate <request.json> --presets <presets.json> --output <directory> --preview
```

Mandatory `input/`, `requests/` или `output/` directories отсутствуют. Пути задаёт caller. Existing output target не перезаписывается.

Requested result публикуется atomic application-level: bundle и requested preview сначала создаются внутри temporary sibling root, затем весь root получает final name.

Stable exit classes:

```text
0 success
2 invalid CLI arguments
3 request/catalog parse or validation error
4 compile/generation/capability/attempt exhaustion
5 assembly/export/render/filesystem failure
70 internal invariant or unexpected application failure
```

Success stdout — один machine-readable JSON object; diagnostics идут в stderr.

## Граница renderer / imagegen

`technical-map.png` остаётся diagnostic non-canonical artifact. Будущий artistic flow отделён:

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

Он не входит в canonical entrypoint implementation checkpoint.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.

## Следующий порядок

Сейчас нужно завершить и merge-ить docs-only PR принятого `Canonical CLI / Python Application Entrypoint v0.1` после зелёного CI.

После docs merge:

```text
canonical CLI / Python application entrypoint — implementation PR
→ отдельное пользовательское принятие
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide renderer остаётся отдельной downstream задачей.
