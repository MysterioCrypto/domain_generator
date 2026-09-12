# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические архитектурные решения остаются в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/soft-constraint-compilation-scoring-v0.1.md`.
4. Проверить состояние PR #32 перед любыми новыми изменениями.
5. Не придумывать новую архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

### Уже в main

- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #30 Final Validation hard-complete v0.1 — merged;
- `main` перед PR #32: `c793878644f80091bb772f0f640d9dcc135dd903`.

Final Validation уже имеет production hard gate, final geometry view и neutral ranking для hard-only plans.

### PR #32 — Soft Constraint Compilation & Scoring v0.1

- URL: https://github.com/MysterioCrypto/domain_generator/pull/32
- branch: `impl/m2-soft-constraint-scoring-v0.1`;
- design принят пользователем до implementation;
- canonical design: `docs/design/soft-constraint-compilation-scoring-v0.1.md`;
- compiler принимает soft variants существующих relations;
- scoring recipes: `linear_increasing`, `linear_decreasing`, `positive`;
- soft evaluation использует тот же canonical spatial measurement boundary, что и hard evaluation;
- Final сначала применяет hard gate, затем оценивает soft constraints и строит ranking;
- deferred-to-deferred soft constraints допустимы, если существующий evaluator поддерживает final geometry pair;
- hard deferred-to-deferred dependency остаётся запрещённой;
- `SiteProfile.preferences` не входят в global user-soft ranking;
- новые spatial relations/evaluators этим checkpoint не добавляются.

Scoring:

```text
effective_violation = (1 - score) * weight

worst_effective_violation = max(effective_violation_i)
weighted_mean_score = sum(score_i * weight_i) / sum(weight_i)
```

Global candidate ordering остаётся:

```text
1. min worst_effective_violation
2. max weighted_mean_score
3. min attempt_index
```

Если soft constraints отсутствуют:

```text
worst_effective_violation = 0.0
weighted_mean_score = 1.0
```

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала объяснить design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- Только после принятия обновить документацию и затем реализацию.
- Implementation PR не merge-ить без явного принятия пользователем соответствующего checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.
- Иллюстративные примеры ненормативны и не могут становиться Core rules без отдельного решения.

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

Technical PNG — точная downstream визуализация canonical data. Художественная image-generation стилизация находится ещё дальше downstream и не меняет world state.

## Следующий порядок после принятия PR #32

```text
merge Soft Constraint Compilation & Scoring v0.1
→ HydroFeature / lake materialization v0.1
→ DomainData Assembler v0.1
→ DomainBundle Export v0.1
→ Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

HydroFeature/lake materialization требует отдельного design checkpoint. Нельзя молча решать representation lake geometry или менять `HydroFeature.geometry` без обсуждения.

Обновлять этот handoff при крупных checkpoint-ах, но не использовать его вместо нормативных design/ADR документов.
