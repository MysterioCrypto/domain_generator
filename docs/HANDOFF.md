# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-14

M0–M10 Core 0.1 функционально завершены. Integration track (`Local Model Adapter`, `Codex Integration Packaging`, `Remote GitHub Actions Generation Adapter`) реализован и проверен end-to-end.

Текущий release gate — **M11 Acceptance Suite v0.1**. Design принят; следующий шаг — отдельный implementation PR.

Normative design:

```text
docs/design/m11-acceptance-suite-v0.1.md
```

## Acceptance worlds

Обязательные representative cases:

```text
A01 minimal
A02 terrain-ridge
A03 hydrology-lake-river
A04 surface
A05 dependent-poi
A06 constraints-ranking
A07 complex-mixed
```

Каждый case использует fixed request/catalog/seed и проверяет два слоя:

```text
exact replay / compact golden identity
+
semantic correctness
```

## Baseline strategy

Repository не хранит большие `.npy` goldens как обязательную основу M11.

Для каждого case ожидается `expected.json` с compact metadata/digests и semantic expectations. Exact replay дополнительно сравнивает два независимых generation run внутри одной generator revision/version.

Canonical checks включают:

- accepted attempt index;
- DomainData deterministic digest/equality;
- four canonical field payloads;
- fingerprints/provenance;
- DomainBundle manifest/hashes;
- case-specific semantic assertions.

Technical PNG не является Core release-gating binary golden.

## Special acceptance cases

### A05 Dependent POI

Final result обязан содержать materialized POI point, satisfying SiteProfile requirements. Test-only stage harness дополнительно проверяет:

```text
Layout → reservation exists, final point absent
Placement → final point exists
```

Нового production API для этого не создаётся.

### A06 Constraints / Ranking

Case должен реально различать attempts/candidates и доказать canonical winner ordering:

```text
lower worst effective violation
→ higher weighted mean score
→ lower attempt index
```

Hard-invalid candidate никогда не принимается.

### A07 Complex Mixed

Главный representative world объединяет terrain, hydrology, surface bias, dependent POI, hard/soft constraints, validation/ranking, assembly and bundle export.

## Bug policy

Если acceptance implementation обнаруживает production defect:

```text
red acceptance case
→ separate bugfix PR
→ green acceptance case
```

Нельзя тихо менять Core behavior внутри M11 implementation только ради обновления baseline.

`expected.json` также не переписывается автоматически при test failure.

## Release gate

До Core 0.1 release candidate должны быть green:

```text
full unit/integration suite
A01..A07
exact replay all cases
canonical bundle checks
engine/hard invariants
provenance/fingerprints/digests
```

## Следующий implementation slice

```text
tests/acceptance/cases/a01-minimal/...
tests/acceptance/cases/a02-terrain-ridge/...
tests/acceptance/cases/a03-hydrology-lake-river/...
tests/acceptance/cases/a04-surface/...
tests/acceptance/cases/a05-dependent-poi/...
tests/acceptance/cases/a06-constraints-ranking/...
tests/acceptance/cases/a07-complex-mixed/...
tests/acceptance/conftest.py
tests/acceptance/support.py
tests/acceptance/test_cases.py
tests/acceptance/test_replay.py
```

Implementation PR требует отдельного явного принятия перед merge.

После green/accepted M11:

```text
Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.