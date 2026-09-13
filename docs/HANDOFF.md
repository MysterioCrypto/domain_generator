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

`main` после merge PR #41:

```text
e050dc8c609f01c70ebfc7c2fe79e9c4b425ff6a
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
- PR #41 Technical Renderer v0.1 implementation — accepted and merged.

Последний принятый implementation checkpoint — `Technical Renderer v0.1`.

Подтверждённый полный CI PR #41:

```text
290 passed
```

В suite входят 9 renderer-specific tests: output dimensions/aspect, deterministic PNG bytes, no mutation, current geometry/network coverage, existing-target protection, parent semantics, field mismatch, PNG suffix и temp cleanup при failure.

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
     ├-> DomainBundle Export -> persisted bundle
     └-> Technical Renderer -> technical-map.png
```

`technical-map.png` остаётся non-canonical diagnostic artifact. Renderer использует optional `render` dependency, headless Matplotlib/Agg, сохраняет north-up/world aspect ratio, отображает canonical raster/vector semantics без semantic smoothing и не использует RNG/не мутирует `DomainAssembly`.

## Граница будущей художественной карты

`technical-map.png` не считается оптимальным control image для image-generation model. Зафиксирована отдельная downstream идея:

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

Guide renderer пока не спроектирован. Его задача — сохранять canonical geography, но представлять её image model в более подходящем виде, чем nearest-neighbour technical grid. Не рассчитывать на raw `.npy`/JSON как на надёжный прямой spatial interface к image-generation model.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.

## Следующий bounded design gate

```text
canonical CLI / Python application entrypoint
```

Нужно спроектировать единый application-level вызов, который связывает уже готовые stages для local и remote execution: request input, output path, compile/generate/assemble/export/render orchestration, ошибки и exit codes, Python API и CLI boundary.

После него:

```text
local model skill/adapter
→ remote GitHub Actions generation adapter
```

Presentation/imagegen guide renderer остаётся отдельной downstream задачей и не блокирует canonical CLI.

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
