# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
4. Прочитать `docs/design/domain-bundle-export-v0.1.md`.
5. Прочитать `docs/design/technical-renderer-v0.1.md`.
6. Не менять архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

`main` до merge design PR Technical Renderer:

```text
901be6c39fed43d1756253d95d1b653ece1a6bc8
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33/#34 HydroFeature / Lake Materialization design + implementation — merged;
- PR #35/#36 DomainData Assembler design + implementation — merged;
- PR #37/#38 DomainBundle Export design + implementation — merged;
- PR #39 post-merge exporter status sync — merged.

Последний принятый implementation checkpoint — `DomainBundle Export v0.1`.

`Technical Renderer v0.1` design принят пользователем; normative semantics находятся в `docs/design/technical-renderer-v0.1.md`. Runtime implementation ещё отсутствует и должен идти отдельным PR после merge design docs.

Подтверждённый полный CI PR #38:

```text
281 passed
```

## Реализованная сквозная граница

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
  -> DomainData Assembler
  -> DomainAssembly
  -> DomainBundle Export
  -> persisted bundle
```

Canonical persisted bundle v0.1:

```text
<caller-provided-output>/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
```

`BundleManifest v0.1` хранит SHA-256 и размеры canonical persisted files. Exporter не использует RNG, не изменяет semantic world state, не поддерживает overwrite и публикует final directory только после успешной записи temporary sibling tree.

## Technical Renderer v0.1 — accepted design

Renderer получает `DomainAssembly` и caller-provided PNG path, строит deterministic diagnostic top-down map и не меняет semantic world state.

Базовые semantics:

```text
elevation
→ vegetation overlay
→ water mask
→ lake polygons
→ river centerlines
→ semantic features
→ labels / north / scale / legend
```

- north сверху;
- world-space aspect ratio сохраняется;
- baseline long side = 1600 px;
- raster cells отображаются без semantic smoothing;
- BandGeometry не получает скрыто синтезированный polygon footprint;
- renderer dependency остаётся optional (`render` extra), target implementation — headless Matplotlib/Agg;
- output existing target отклоняется, final PNG публикуется через temporary sibling + rename;
- renderer не использует RNG и не влияет на generation/validation.

`technical-map.png` — diagnostic artifact, а не canonical world state и не гарантированно оптимальный reference для image-generation model.

Для будущей художественной карты зафиксирована отдельная downstream boundary:

```text
DomainData + rasters + vectors
        ↓
Presentation / imagegen guide renderer
        ↓
imagegen-guide.png
        ↓
image generation / artistic transform
        ↓
campaign-map.png
```

Этот guide renderer пока не спроектирован. Его задача будет сохранить canonical geography, но представить её image model в более подходящем визуальном виде, чем nearest-neighbour technical grid.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.

## Главная граница Core

`domain_generator` — setting-agnostic procedural Core.

```text
world / setting / application
          ↓
   adapter / presets
          ↓
      DomainSpec
          ↓
   domain_generator
          ↓
      DomainData / DomainBundle
          ↓
 renderer / integration
```

## Следующий порядок

```text
Technical Renderer v0.1 implementation
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide renderer остаётся отдельной downstream задачей и не блокирует canonical CLI.

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
