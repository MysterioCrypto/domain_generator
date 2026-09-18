---
project: domain_generator
target_version: core-0.2
phase: hydrology-redesign
status: in-progress
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
development_branch: dev/0.2
current_milestone: v0.2-batch-b-continuous-drainage-routing
checkpoint: terrain-v0.2-accepted-continuous-drainage-design-accepted
next_topic: finish-hydrology-v0.2-human-checkpoint
working_context: docs/CONTEXT.md
accepted_designs:
  - continuous-terrain-foundation-v0.2
  - continuous-drainage-routing-v0.2
completed:
  - core-0.1-prealpha-infrastructure
  - core-0.1-m11-acceptance-suite
  - core-0.1-local-portability-hardening
  - core-0.1-codex-and-remote-generation-integrations
  - core-0.2-continuous-terrain-foundation
  - core-0.2-domain-provenance-boundary
rejected_or_superseded:
  - core-0.1-world-generation-semantics
  - guide-renderer-as-fix-for-upstream-world-state
  - v0.2-d8-river-reconstruction-experiment-pr70
implemented_integrations:
  - local-model-skill-adapter-v0.1
  - codex-integration-packaging-v0.1
  - remote-github-actions-generation-adapter-v0.1
canonical_documents:
  working_context: docs/CONTEXT.md
  architecture: docs/architecture.md
  glossary: docs/glossary.md
  decisions: docs/decisions/
  contracts: docs/contracts/
  continuous_terrain_v0_2: docs/design/continuous-terrain-foundation-v0.2.md
  continuous_drainage_v0_2: docs/design/continuous-drainage-routing-v0.2.md
historical_documents:
  core_0_1_roadmap: docs/roadmap.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — setting-agnostic procedural Core для генерации региональных/глобальных карт.

Для восстановления текущей работы читать этот файл вместе с `docs/CONTEXT.md`:

- `PROJECT.md` хранит устойчивые границы проекта и текущую линию разработки;
- `docs/CONTEXT.md` — короткое rolling-сжатие активного смыслового контекста: что принято, что отвергнуто, почему и какой следующий checkpoint;
- normative semantics живут в `docs/design/`, `docs/contracts/` и `docs/decisions/`.

`docs/CONTEXT.md` намеренно переписывается при значимых checkpoint'ах и не является changelog.

## Версионная граница

```text
release/0.1-prealpha
└─ 9699c3d8079b8b9710d65eed60ff975158af0ad3
   historical / rejected as world-generation baseline

dev/0.2
└─ active development line
```

Core 0.1 доказал инфраструктуру, deterministic replay, contracts, pipeline, validation/ranking, bundle/API/CLI и интеграции. Первый полноценный visual diagnostic показал, что его world-generation semantics неприемлемы для дальнейшей разработки: terrain начинался с flat zero field, ridge фактически читался как размытая ломаная, а D8 hydrology наследовала grid bias.

Поэтому 0.1 не является release candidate. Он заморожен как историческая pre-alpha линия.

Важно: `main` не является источником истины о текущем состоянии разработки 0.2. Активная линия указана в metadata выше и в `docs/CONTEXT.md`.

## Принятая основа Core 0.2

Terrain 0.2 принят как минимально приемлемая база для дальнейшей разработки.

Он вводит:

```text
continuous multi-scale base elevation
→ smooth semantic Band spine
→ massif-scale ridge modifier
→ blended Area raise/depress
→ TerrainState base/final diagnostics
```

Normative design:

```text
docs/design/continuous-terrain-foundation-v0.2.md
```

## Текущая работа: Hydrology 0.2

Первая попытка сохранить D8 как computational routing backend с последующей vector reconstruction была отвергнута на visual/metric checkpoint: reconstruction уменьшала staircase, но сохраняла систематический grid-lock.

Принят новый design:

```text
Priority-Flood conditioning
→ D∞-style continuous drainage field
→ distributed accumulation
→ lake supernodes / single spill outlet
→ semantic channelization
→ continuous world-space river traces
```

Normative design:

```text
docs/design/continuous-drainage-routing-v0.2.md
```

Implementation существует в отдельном draft PR и не считается принятой, пока не пройдёт обязательный hydrology-only human visual checkpoint. До этого Surface/Placement не продолжаются.

Точная оперативная точка и следующий шаг находятся в `docs/CONTEXT.md`.

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

## Process invariants

INV-001..INV-011 остаются в силе.

Существенные архитектурные изменения документируются до implementation; diagnostics не изменяют semantic result; cross-version world identity не обещается. Human checkpoint, явно предусмотренный design gate, является частью acceptance, а не декоративным этапом.
