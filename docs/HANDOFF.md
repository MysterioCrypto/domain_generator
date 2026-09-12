# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические архитектурные решения остаются в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Проверить состояние PR #31 и PR #30 перед любыми изменениями.
4. Не придумывать новую архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-12

Репозиторий: `MysterioCrypto/domain_generator`.

### PR #31 — Documentation Language Cleanup v0.1

- URL: https://github.com/MysterioCrypto/domain_generator/pull/31
- branch: `docs/russian-language-cleanup-v0.1`
- head на момент handoff: `ad0a64d5c8590b09070ce75cf1e0d17c3c6ac0fd` до добавления этого файла;
- docs-only;
- CI до добавления handoff: 235/235 tests passed;
- переводит объяснительную документацию на русский;
- `PROJECT.md` намеренно не менялся в PR #31, потому что он уже меняется в PR #30.

Принятое языковое правило:

- объяснительный текст, заголовки, README, ADR, contracts и design docs — по-русски;
- буквальные технические идентификаторы остаются английскими: типы, функции, поля, enum, имена файлов, CLI-команды, serialized keys/values и формулы;
- Python code и JSON Schema этим правилом не переводятся.

### PR #30 — Final Validation v0.1 hard-complete

- URL: https://github.com/MysterioCrypto/domain_generator/pull/30
- branch: `impl/m2-final-validation-hard-v0.1`
- open, not merged;
- реализует production `FINAL` stage для текущего hard-only compiler slice;
- до документационного cleanup CI был 241/241;
- branch нужно актуализировать относительно нового `main` после merge PR #31 и повторно проверить CI.

Final Validation:

```text
LayoutCandidate
+ TerrainState
+ HydrologyState
+ SurfaceState
+ PlacementState
+ GenerationPlan
        ↓
final geometry view
        ↓
all compiled hard constraints
        ↓
ValidationResult(stage=final)
```

Для поддерживаемых hard-only plans ranking нейтральный:

```text
worst_effective_violation = 0.0
weighted_mean_score = 1.0
```

Soft constraints пока не игнорируются: их наличие является explicit capability error до отдельного soft-scoring checkpoint.

## Точный следующий порядок действий

```text
принять PR #31
→ merge документационного cleanup
→ актуализировать PR #30 относительно нового main
→ проверить CI
→ merge Final Validation после принятия
→ перейти к Soft Constraint Compilation & Scoring v0.1
```

Не менять этот порядок молча.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала объяснить design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- Только после принятия реализовать.
- Новый implementation PR не merge-ить без явного принятия пользователем соответствующего checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.
- Illustrative examples ненормативны и не могут становиться Core rules без отдельного решения.

## Главная граница Core

`domain_generator` — полностью setting-agnostic procedural Core.

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

Core знает generic geometry, terrain, hydrology, continuous/surface fields, networks, constraints, procedural features и placement rules.

Core не знает конкретный сеттинг, кампанию, игровую систему, lore, LLM provider, GitHub как обязательный runtime, UI или renderer.

## End-to-End target

Один и тот же Core должен исполняться локально и удалённо:

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

Локальный режим: быстрый запуск Python/CLI/API или model skill на машине пользователя.

Удалённый режим: request JSON в repository → GitHub Actions → тот же canonical entrypoint → workflow artifact. GitHub Actions является adapter/infrastructure, не dependency Core.

Technical PNG — точная downstream визуализация canonical data. Художественная image-generation стилизация campaign map находится ещё дальше downstream и не меняет world state.

## После Final Validation

Следующий design checkpoint: `Soft Constraint Compilation & Scoring v0.1`.

После soft scoring в принятой end-to-end последовательности остаются:

1. HydroFeature / lake materialization v0.1;
2. DomainData Assembler v0.1;
3. DomainBundle Export v0.1;
4. Technical Renderer v0.1;
5. canonical CLI / Python application entrypoint;
6. local model skill/adapter;
7. remote GitHub Actions generation adapter.

Обновлять этот handoff при крупных checkpoint-ах, но не использовать его вместо нормативных design/ADR документов.
