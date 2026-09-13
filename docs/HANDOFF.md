# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/hydrofeature-lake-materialization-v0.1.md`.
4. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
5. Не менять архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

`main` после merge PR #34:

```text
d9c6145f6e49df351fb86372f05ffc6f953ea85b
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33 HydroFeature / Lake Materialization design v0.1 — merged;
- PR #34 HydroFeature / Lake Materialization implementation v0.1 — merged.

Hydrology теперь materializes accepted lakes как exact canonical `RegionSet` semantic features и сохраняет единый `lake-NNNN` identity protocol для network/water/features.

Последний подтверждённый implementation suite PR #34:

```text
266 passed
```

## DomainData Assembler v0.1 — design accepted

Canonical design: `docs/design/domain-data-assembler-v0.1.md`.

Design принят пользователем; implementation ещё не считается выполненным или merged.

Принятая граница:

```text
DomainSpec
GenerationPlan
GenerationConfig
selected DomainCandidate
        ↓
DomainData Assembler
        ↓
DomainAssembly
  data: DomainData
  field_payloads:
    elevation
    water_depth
    moisture
    vegetation_density
```

Ключевые решения:

- assembler получает только выбранный `DomainCandidate`, не занимается ranking/selection;
- `DomainSpec` передаётся отдельно, чтобы сохранить `identity.label` и проверить spec↔plan provenance;
- generation-config fingerprint включает version + semantic config и исключает observability;
- specified final features собираются из layout + placement geometry без повторной generation;
- готовые hydrology `lake_features` переносятся без повторной vectorization;
- generated hydro namespace `^lake-[0-9]{4,}$` резервируется и запрещается для user feature IDs;
- duplicate semantic feature ID — explicit error, silent overwrite запрещён;
- network `rivers` присутствует всегда, даже если пустой;
- canonical fields: elevation, water_depth, moisture, vegetation_density;
- field payloads обязаны быть exact expected shape + float32;
- assembler делает независимые read-only copies canonical arrays для защиты accepted candidate от downstream mutation;
- `ValidationSummary` строится из уже успешного final validation/ranking;
- никаких RNG, IO, renderer, reroll, re-ranking или скрытой regeneration.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.
- Иллюстративные примеры ненормативны.

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
      DomainData
          ↓
 renderer / exporter / integration
```

Core знает generic geometry, terrain, hydrology, fields, networks, constraints, procedural features и placement rules. Core не знает конкретный сеттинг, кампанию, game-system rules, lore, LLM provider, GitHub как обязательный runtime, UI или renderer.

## End-to-End target

```text
DomainSpec JSON/YAML-adapter
        ↓
canonical Python/CLI entrypoint
        ↓
Core pipeline
        ↓
DomainAssembly
        ↓
DomainBundle
  domain.json
  manifest.json
  fields/*.npy
  preview/technical-map.png   # non-canonical
```

Локальный и remote режимы используют один Core entrypoint. GitHub Actions — adapter/infrastructure, не Core dependency. Technical PNG и художественная стилизация downstream и не меняют world state.

## Следующий порядок

```text
DomainData Assembler implementation v0.1
→ DomainBundle Export v0.1 design
→ DomainBundle Export implementation
→ Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
