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

`main` после merge design PR #40:

```text
58600a6696bccc6da2a2e66c259713e81c465ec1
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33/#34 HydroFeature / Lake Materialization design + implementation — merged;
- PR #35/#36 DomainData Assembler design + implementation — merged;
- PR #37/#38 DomainBundle Export design + implementation — merged;
- PR #39 post-merge exporter status sync — merged;
- PR #40 Technical Renderer v0.1 normative design — merged.

Последний принятый implementation checkpoint на `main` — `DomainBundle Export v0.1`.

## Текущий implementation checkpoint

PR #41 `Implement Technical Renderer v0.1` открыт и **не должен merge-иться без отдельного принятия пользователя**.

Implementation branch:

```text
impl/m2-technical-renderer-v0.1
```

Реализовано:

- `render_technical_map(assembly, output_path)`;
- optional `render` package extra;
- headless Matplotlib/Agg;
- elevation / vegetation / water raster composition;
- exact lake RegionSet outlines;
- river centerlines и minimal direction markers;
- Point/POI, Corridor, Band width samples, Area/Surface geometry;
- labels, north marker, scale, legend, domain boundary;
- 1600 px long-side baseline с сохранением domain aspect ratio;
- nearest-neighbour raster visualization без semantic smoothing;
- caller-provided PNG path;
- immediate parent creation only;
- existing-target rejection;
- temporary sibling file + PNG validation + final rename;
- renderer не использует RNG, не reroll-ит и не мутирует `DomainAssembly`.

Подтверждённый полный CI текущей implementation semantics:

```text
290 passed
```

В suite входят 9 renderer-specific tests: output dimensions/aspect, deterministic PNG bytes, no mutation, current geometry/network coverage, existing-target protection, parent semantics, field mismatch, PNG suffix и temp cleanup при failure.

## Реализованная сквозная граница до renderer

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

В PR #41 добавляется downstream diagnostic branch:

```text
DomainAssembly
  -> Technical Renderer
  -> technical-map.png
```

`technical-map.png` остаётся non-canonical artifact.

## Technical Renderer v0.1 semantics

Normative design: `docs/design/technical-renderer-v0.1.md`.

Базовый visual stack:

```text
elevation
→ vegetation overlay
→ water mask
→ lake outlines
→ river centerlines
→ semantic features
→ labels / north / scale / legend
```

North сверху, world-space aspect ratio сохраняется, raster cells не проходят semantic smoothing, BandGeometry не получает скрыто синтезированный polygon footprint.

## Граница будущей художественной карты

`technical-map.png` — diagnostic artifact, а не оптимальный control image для image-generation model.

Зафиксирована отдельная downstream идея:

```text
DomainData + canonical rasters + vectors
        ↓
Presentation / imagegen guide renderer
        ↓
imagegen-guide.png
        ↓
image generation / artistic transform
        ↓
campaign-map.png
```

Guide renderer пока не спроектирован. Его задача — сохранять canonical geography, но представлять её image model в более подходящем виде, чем nearest-neighbour technical grid.

Не рассчитывать на raw `.npy`/JSON как на надёжный прямой spatial interface к image-generation model.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.

## Следующий порядок

Сейчас требуется отдельное принятие PR #41.

После принятия/merge:

```text
canonical CLI / Python application entrypoint — design gate
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide renderer остаётся отдельной downstream задачей и не блокирует canonical CLI.

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
