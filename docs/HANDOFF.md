# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
4. Прочитать `docs/design/domain-bundle-export-v0.1.md`.
5. Не менять архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

`main` после merge PR #38:

```text
5b665487695bdf45c802c1ac6b9a67c05caff816
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33/#34 HydroFeature / Lake Materialization design + implementation — merged;
- PR #35/#36 DomainData Assembler design + implementation — merged;
- PR #37/#38 DomainBundle Export design + implementation — merged.

Последний принятый implementation checkpoint — `DomainBundle Export v0.1`.

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

Input path и output path не привязаны к обязательным repository folders. Будущий CLI должен получать их параметрами. Internal bundle paths остаются relative POSIX paths; filesystem target работает через `pathlib.Path`, поэтому архитектура рассчитана на Windows и POSIX environments.

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

## Следующий bounded design gate

```text
Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Technical Renderer ещё не спроектирован и не должен реализовываться до отдельного принятия design semantics.

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
