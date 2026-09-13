# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/soft-constraint-compilation-scoring-v0.1.md`.
4. Прочитать `docs/design/hydrofeature-lake-materialization-v0.1.md`.
5. Не менять архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

`main` после merge PR #32:

```text
c20fe0705c90e2faec6557378ad0daccedb6bb5b
```

### Уже в main

- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged.

Final Validation имеет production hard gate и полный user-soft global ranking для поддерживаемых canonical spatial measurements.

## Soft Constraint Compilation & Scoring v0.1 — complete

Canonical design: `docs/design/soft-constraint-compilation-scoring-v0.1.md`.

Реализовано:

- soft variants существующих spatial relations компилируются в `CompiledScoring`;
- scoring recipes: `linear_increasing`, `linear_decreasing`, `positive`;
- hard/soft используют один canonical spatial measurement boundary;
- Final сначала применяет hard gate, затем soft scoring;
- `effective_violation = (1-score)*weight`;
- ranking: min worst violation → max weighted mean → min attempt index;
- deferred-to-deferred soft допустим, если final geometry pair поддерживается evaluator-ом;
- hard deferred-to-deferred dependency остаётся запрещённой;
- `SiteProfile.preferences` не входят в global user-soft ranking.

## HydroFeature / Lake Materialization v0.1 — design accepted

Canonical design: `docs/design/hydrofeature-lake-materialization-v0.1.md`.

Принято:

```text
LakeCandidate.cells
→ exact world-space cell squares
→ exact GEOS union
→ canonical RegionSet
→ HydroFeature
```

Основные решения:

- `HydroFeature.geometry` становится `RegionSet`;
- smoothing/simplification/marching-squares в semantic materialization запрещены;
- holes и D8 diagonal multipart geometry сохраняются точно;
- IDs сохраняют существующий protocol `lake-0001`, `lake-0002`, ...;
- один helper должен использоваться network/water/materializer;
- `LakeProperties` получает уже вычисляемый `max_depth_m`;
- `HydrologyState` получает `lake_features: dict[str, HydroFeature]`;
- lake materialization принадлежит hydrology layer, а не будущему assembler;
- river lake references обязаны разрешаться в materialized lake features;
- materializer не использует RNG/IO/renderer.

Design branch:

```text
design/m2-hydrofeature-lake-materialization-v0.1
```

Implementation ещё не должен считаться принятым или merged до отдельного checkpoint пользователя.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала объяснить design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия зафиксировать normative docs до runtime implementation.
- Implementation вести отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем соответствующего checkpoint.
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
HydroFeature / lake materialization implementation v0.1
→ DomainData Assembler v0.1
→ DomainBundle Export v0.1
→ Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
