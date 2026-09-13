# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-13

M0–M10 Core 0.1 функционально завершены. `Local Model Skill / Adapter v0.1`, `Codex Integration Packaging v0.1` и `Remote GitHub Actions Generation Adapter v0.1` реализованы и смержены.

Следующий release gate — **M11 Acceptance Suite / Core 0.1 hardening**.

## Remote GitHub Actions Generation Adapter v0.1 — complete

Implementation merged through PR #52.

Generation path:

```text
workflow_dispatch / PR remote-requests/**
        ↓
exact checkout revision
        ↓
safe path validation
        ↓
canonical domain-generator CLI exactly once
        ↓
domain-bundle + technical-preview + generation-diagnostics
```

Generation workflow имеет `contents: read`. Cleanup write permission находится только в отдельном `pull_request: closed` workflow и применяется только к same-repository branches `remote-generation/*`.

Implementation suite на acceptance checkpoint: `341 passed`.

## Real post-merge E2E

Полный lifecycle проверен отдельным временным PR #54:

```text
remote-generation/cleanup-e2e-20260913
→ remote request files
→ PR-triggered generate-domain success
→ artifacts produced
→ PR closed without merge
→ cleanup-remote-generation success
→ temporary branch deleted
```

Повторный branch lookup подтвердил, что temporary branch больше не существует.

## Visual remote smoke

PR #53 добавил отдельный `remote-requests/visual-example/` с real ridge preset, larger grid и preview=true.

Полученное technical preview показывает уже не пустой мир, а инженерную абстракцию generated terrain: ridge/elevation, water, vegetation/surface overlay, scale/north and feature geometry. Это диагностическая карта, а не player-facing rendering.

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track.

## Следующий bounded slice: M11 Acceptance Suite

M11 должен не добавлять новые generation capabilities, а закрепить уже реализованный Core 0.1 representative acceptance cases.

Ожидаемые категории из текущего roadmap/context:

```text
minimal
ridge / terrain
hydrology / lake / river
surface
POI dependent placement
constraints / ranking
complex mixed domain
```

Acceptance checks должны быть semantic и deterministic: фиксированные specs/seeds, fingerprints, topology/feature properties, hard/soft validation outcomes и replay expectations. Большие binary golden files не являются обязательной стратегией.

Согласно INV-006 сначала нужен отдельный M11 design gate; implementation suite после этого идёт отдельным PR и требует отдельного явного принятия до merge.

После M11:

```text
Core 0.1 hardening
→ Core 0.1 release candidate
```
