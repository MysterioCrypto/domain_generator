# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-14

Core 0.1 M0–M11 завершены. Integration track (`Local Model Adapter`, `Codex Integration Packaging`, `Remote GitHub Actions Generation Adapter`) также реализован и проверен end-to-end.

**M11 Acceptance Suite v0.1 принят и смержен через PR #57.** Функциональный release gate Core 0.1 сейчас green.

Accepted implementation head:

```text
6580046bcf13f38960ad75a8697e79a9594c881c
```

Merge commit:

```text
cd0a79b337f5e16e6336e36d843e8cba42251ca7
```

Final CI:

```text
357 passed in 12.47s
```

## M11 acceptance worlds

```text
A01 minimal
A02 terrain-ridge
A03 hydrology-lake-river
A04 surface
A05 dependent-poi
A06 constraints-ranking
A07 complex-mixed
```

Каждый case имеет fixed request/catalog/seed и проверяет:

```text
exact replay
+
compact deterministic baseline
+
semantic correctness
```

Baselines хранят canonical DomainData digest, field digests/shape/dtype/ranges, fingerprints, accepted attempt и validation summary. Они не переписываются автоматически.

## Representative results

### A03 Hydrology

Фиксированный hydrology world создаёт:

```text
lake-0001
72 river nodes
36 river segments
```

### A05 Dependent Placement

Проверяется stage boundary:

```text
Layout: reservation есть, final point нет
Placement: final point есть
```

### A06 Ranking

Фиксированный ranking case выполняет:

```text
16 attempts
2 hard-valid candidates: 8, 7
разные soft scores
winner = attempt 8
```

То есть acceptance действительно проверяет hard rejection и soft deterministic ranking, а не только тривиальный attempt 0.

### A07 Complex Mixed

Representative world объединяет terrain + hydrology + surface bias + deferred POI + hard/soft constraints + ranking + assembly + DomainBundle export. Baseline выбирает attempt 1 из двух valid candidates и содержит generated lake/river network.

## Production defect discovered by M11

A06 выявил дефект stage boundary: Layout пытался hard-валидировать structural soft constraint.

Исправление было вынесено отдельным PR #58, а не спрятано в acceptance implementation:

```text
PR #58
→ regression test
→ 342 tests green
→ separately accepted
→ merged cd15b986e9a68f62fb7f8b80bd266e897125062b
```

После этого A06 прошёл и baseline был зафиксирован.

## Core 0.1 release gate

Green:

```text
full unit/integration suite
A01..A07
exact replay all cases
compact deterministic baselines
canonical bundle checks
engine/hard invariants
provenance/fingerprints/digests
remote GitHub generation E2E
```

## Следующий bounded step

Следующий этап не должен добавлять новые generation semantics. Нужен короткий **Core 0.1 release-candidate review / hardening**:

```text
package/version metadata
release-facing documentation consistency
known-blocker review
final clean CI/release checklist
→ Core 0.1 release candidate declaration
```

Любое обнаруженное semantic изменение снова проходит обычный design gate и не маскируется как release cleanup.

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track и не блокирует Core 0.1.