---
project: domain_generator
target_version: core-0.2
phase: hydrology-redesign
status: in-progress
historical_release_branch: release/0.1-prealpha
historical_release_commit: 9699c3d8079b8b9710d65eed60ff975158af0ad3
development_branch: dev/0.2
current_milestone: v0.2-batch-b3-channel-skeleton-extraction
checkpoint: h09-c-channel-skeleton-ready-for-operator-review
next_topic: operator-review-h09-c
working_context: docs/CONTEXT.md
accepted_designs:
  - continuous-terrain-foundation-v0.2
  - continuous-drainage-routing-v0.2
  - low-bias-contributing-area-v0.2
  - channel-skeleton-extraction-v0.2
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
  - v0.2-two-receiver-dinf-accumulation-h09-pr72
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
  low_bias_contributing_area_v0_2: docs/design/low-bias-contributing-area-v0.2.md
  channel_skeleton_extraction_v0_2: docs/design/channel-skeleton-extraction-v0.2.md
historical_documents:
  core_0_1_roadmap: docs/roadmap.md
invariants: [INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011]
---

# Состояние проекта

`domain_generator` — setting-agnostic procedural Core для генерации региональных/глобальных карт.

Для восстановления текущей работы читать этот файл вместе с `docs/CONTEXT.md`:

- `PROJECT.md` хранит устойчивые границы проекта и текущую линию разработки;
- `docs/CONTEXT.md` — короткое rolling-сжатие активного смыслового контекста;
- normative semantics живут в `docs/design/`, `docs/contracts/` и `docs/decisions/`.

`docs/CONTEXT.md` переписывается на значимых checkpoint'ах и не является changelog.

## Версионная граница

```text
release/0.1-prealpha
└─ historical / rejected as world-generation baseline

dev/0.2
└─ active development line
```

Core 0.1 доказал инфраструктуру и exact replay, но visual diagnostic показал неприемлемые world-generation semantics. Он не является release candidate.

## Принятая основа Core 0.2

Terrain 0.2 принят как минимально приемлемая база:

```text
continuous multi-scale base elevation
→ smooth semantic Band spine
→ massif-scale ridge modifier
→ blended Area raise/depress
```

Normative design: `docs/design/continuous-terrain-foundation-v0.2.md`.

## Hydrology 0.2: текущая граница

D8 canonical routing был отвергнут ранее. Следующий Continuous Drainage design ввёл continuous direction field, distributed accumulation, lake supernodes и vector river tracing.

Первый операторский H09 checkpoint этой реализации также **отклонён как финальная hydrology base**. Причина: несмотря на заметное улучшение относительно D8, accumulation/channel skeleton сохраняет выраженный lattice imprint — длинные прямые или ступенчатые cardinal/ordinal участки, необоснованные параллельные каналы и искусственная мелкая фрагментация.

При этом сохраняются как полезные:

```text
Terrain 0.2
continuous direction-field concept / diagnostics
single canonical lake outlet semantics
operator diagnostic views (flow vectors, accumulation, channel support, final rivers)
```

Не принимается как финальная форма:

```text
two-receiver D∞-style raster accumulation
→ current thresholded channel support
→ current H09 final river network
```

Следующий bounded design должен исправлять accumulation/channel skeleton, а не маскировать результат smoothing/renderer.

Точная оперативная точка — в `docs/CONTEXT.md`.

## Process invariants

INV-001..INV-011 остаются в силе.

Для пространственно-генеративных изменений автоматические проверки являются необходимыми предохранителями, но не заменяют operator-visible checkpoint. Если design требует human visual review, слой считается принятым только после явного ACCEPT оператора.
