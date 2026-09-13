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

`main` после merge design PR #33:

```text
b50fed2b8f24a660cdf37e5739d08511f2800d9f
```

### Уже в main

- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33 HydroFeature / Lake Materialization design v0.1 — merged.

### Текущий implementation checkpoint

PR #34 `Implement HydroFeature / Lake Materialization v0.1` открыт и **не должен merge-иться без отдельного принятия пользователя**.

Implementation branch:

```text
impl/m2-hydrofeature-lake-materialization-v0.1
```

Реализовано:

```text
LakeCandidate.cells
→ exact world-space cell squares
→ exact GEOS union
→ canonical RegionSet
→ HydroFeature
```

- `HydroFeature.geometry` — `RegionSet`;
- holes и D8 diagonal multipart geometry сохраняются точно;
- smoothing/simplification/marching-squares отсутствуют;
- `lake_feature_id()` задаёт единый `lake-NNNN` protocol для network/water/materializer;
- `LakeProperties` содержит `max_depth_m`;
- `HydrologyState` содержит materialized `lake_features`;
- hydrology generation materializes lakes до river-reference validation;
- lake geometry area проверяется против `candidate.area_km2`;
- river lake references проверяются против materialized features;
- `DomainData` schema snapshot обновлён под `RegionSet` и `max_depth_m`;
- synthetic `HydrologyState` fixtures сохраняют совместимость через empty default, но production hydrology validation требует exact materialization при наличии lake candidates.

Последний подтверждённый code/schema CI до status-doc sync:

```text
266 passed
```

После изменения status docs требуется проверить CI финального PR head заново.

## Soft Constraint Compilation & Scoring v0.1 — complete

Canonical design: `docs/design/soft-constraint-compilation-scoring-v0.1.md`.

- soft relations компилируются в `CompiledScoring`;
- scoring recipes: `linear_increasing`, `linear_decreasing`, `positive`;
- hard/soft используют один canonical spatial measurement boundary;
- Final сначала применяет hard gate, затем soft scoring;
- `effective_violation = (1-score)*weight`;
- ranking: min worst violation → max weighted mean → min attempt index;
- deferred-to-deferred soft допустим при поддерживаемой final geometry pair;
- `SiteProfile.preferences` не входят в global user-soft ranking.

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

## Следующий порядок после принятия и merge PR #34

```text
DomainData Assembler v0.1 design
→ DomainData Assembler implementation
→ DomainBundle Export v0.1
→ Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
