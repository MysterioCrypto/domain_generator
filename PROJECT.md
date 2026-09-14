---
project: domain_generator
target_version: core-0.2
phase: terrain-redesign
status: in-progress
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
development_branch: dev/0.2
current_milestone: v0.2-batch-a-continuous-terrain-foundation
checkpoint: v0.1-visual-audit-complete
next_topic: implement-continuous-terrain-foundation-v0.2
completed:
  - core-0.1-prealpha-infrastructure
  - core-0.1-m11-acceptance-suite
  - core-0.1-local-portability-hardening
  - core-0.1-codex-and-remote-generation-integrations
accepted_designs:
  - continuous-terrain-foundation-v0.2
implemented_integrations:
  - local-model-skill-adapter-v0.1
  - codex-integration-packaging-v0.1
  - remote-github-actions-generation-adapter-v0.1
canonical_documents:
  architecture: docs/architecture.md
  roadmap: docs/roadmap.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  continuous_terrain_v0_2: docs/design/continuous-terrain-foundation-v0.2.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — setting-agnostic procedural Core для генерации региональных/глобальных карт. Core 0.1 сохранён как pre-alpha snapshot в `release/0.1-prealpha`. Новая разработка идёт в `dev/0.2`.

## Почему начат Core 0.2

Core 0.1 успешно проверил инфраструктуру: contracts, deterministic RNG, pipeline stages, constraints, attempts/ranking, DomainData/DomainBundle, CLI, Codex и remote GitHub execution. M11 доказал exact replay и стабильность реализации.

Первый полноценный visual diagnostic выявил ограничение самой модели мира:

```text
flat elevation = 0
+ sparse terrain feature contributions
→ visually sparse / line-like terrain
```

`ridge` Core 0.1 фактически моделировался как размытая polyline, а downstream hydrology работала по такому elevation. Поэтому Core 0.1 не объявляется release candidate; он остаётся исторической pre-alpha точкой.

## Версионная граница

```text
release/0.1-prealpha
└─ 9699c3d8079b8b9710d65eed60ff975158af0ad3

dev/0.2
└─ начинается с того же snapshot
```

Exact 0.1 behavior хранится в release branch. 0.2 имеет право намеренно менять generated world semantics по INV-009.

## Текущий пакет

**v0.2 Batch A — Continuous Terrain Foundation**

Normative design: `docs/design/continuous-terrain-foundation-v0.2.md`.

```text
continuous base elevation
→ smooth Band spine
→ massif-scale ridge modifier
→ blended Area raise/depress
→ TerrainState base/final diagnostics
→ 0.2 acceptance recalibration
→ early terrain-only visual checkpoint
```

Pipeline order остаётся прежним:

```text
Layout → Terrain → Hydrology → Surface → Placement → Final
```

Batch A не переписывает Hydrology/Surface/Placement. Их качество будет переоценено после принятия нового terrain foundation.

## Что сохраняется из 0.1

```text
contracts/compiler architecture
deterministic semantic RNG namespaces
attempt pipeline
constraints + hard/soft validation
ranking
GridAdapter
Shapely geometry foundation
dependent placement
DomainData / DomainBundle
canonical API / CLI
Codex integration
GitHub remote generation
exact replay infrastructure
```

## Что меняется первым

```text
DomainSpec 0.2 gains required TerrainSpec
Terrain no longer starts from zeros
Band centerline becomes smoothed semantic spine
ridge modifies a continuous background as a massif
raise/depress gain smooth transition zones
TerrainState exposes base_elevation_m internally
```

## Quality gate

После implementation Batch A работа останавливается на human visual review elevation. Hydrology Batch B не начинается, пока terrain не выглядит как связный непрерывный рельеф, а ridge — как 2D массив, а не размытая линия.

## Branch hygiene

После уборки repository держит только долгоживущие `main`, `release/0.1-prealpha`, `dev/0.2` плюс текущую короткоживущую PR branch. После merge/abandon рабочие branches удаляются сразу.

## Invariants

INV-001..INV-011 remain unchanged. Архитектурные изменения документируются до implementation; diagnostics не изменяют semantic result; cross-version world identity не обещается.
