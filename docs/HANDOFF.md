# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## Текущее состояние на 2026-09-14

Core 0.1 сохранён как pre-alpha snapshot:

```text
release/0.1-prealpha
9699c3d8079b8b9710d65eed60ff975158af0ad3
```

Новая development line:

```text
dev/0.2
9699c3d8079b8b9710d65eed60ff975158af0ad3
```

`main` административно выровнен на тот же snapshot перед началом 0.2.

Старые рабочие branches очищены; долгоживущие refs: `main`, `release/0.1-prealpha`, `dev/0.2`.

## Почему 0.2

Core 0.1 доказал работоспособность инфраструктуры и exact replay, но visual diagnostic показал, что world-generation semantics слишком примитивны:

```text
Terrain starts from flat zeros
+ sparse feature masks
ridge ≈ blurred Band polyline
river geometry ≈ raw D8 cell path
```

Guide Renderer experiment был закрыт без merge: улучшение presentation не решает upstream world-state problem.

## Текущий design gate

**v0.2 Batch A — Continuous Terrain Foundation**

Normative design:

```text
docs/design/continuous-terrain-foundation-v0.2.md
```

Accepted scope:

```text
required TerrainSpec v0.2
multi-scale deterministic base elevation
stable RNG namespace per noise-layer id
no per-domain min/max normalization
smooth endpoint-preserving Band spine
ridge as 2D massif influence
smooth Area raise/depress transition
TerrainState.base_elevation_m + final elevation_m
0.2 acceptance migration
early human-reviewed terrain visual checkpoint
```

Hydrology, river geometry, climate/surface, placement и final artistic renderer не перерабатываются в Batch A.

## Development process 0.2

Шаги стали крупнее, но INV-006 сохраняется:

```text
accepted design batch
→ docs-only PR into dev/0.2
→ merge after green CI
→ one implementation PR for the whole batch
→ tests + real elevation world
→ visual checkpoint
→ explicit human acceptance
→ merge
```

После merge/abandon короткоживущую branch удаляем сразу.

## Следующий checkpoint

После реализации Batch A нужен terrain-only visual review на representative world. Проверяем не красоту финальной карты, а сам elevation state:

```text
continuous background relief
broad massif instead of line-shaped ridge
multi-scale relief
smooth Area integration
absence of obvious grid/corner artifacts
```

Hydrology Batch B начинается только после явного принятия этого terrain checkpoint.
