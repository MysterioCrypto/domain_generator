# Rolling Context / Backlog

Этот файл — сжатая рабочая память проекта, а не журнал событий.

## Правило ведения

Переписывать только при смене смысловой точки проекта. Не вести commit-by-commit/CI историю. Оставлять прошлое только если оно ограничивает текущие решения или нужно для правильного следующего шага.

## Текущая опорная точка

```text
historical:
  release/0.1-prealpha
  status: archived; world-generation semantics rejected

active:
  dev/0.2
  Terrain 0.2: ACCEPTED
  Hydrology 0.2: redesign in progress

latest operator checkpoint:
  H09-B / PR #72
  MFD accumulation: KEEP as current experimental base
  semantic river network: REJECTED
```

Не выводить состояние проекта из `main`; active development line — `dev/0.2`.

## Что сохраняется

### Terrain 0.2

Принят как минимально приемлемая база.

`docs/design/continuous-terrain-foundation-v0.2.md`

### Hydrology foundation

Сохраняем:

- Priority-Flood conditioning;
- MFD p=1.1 contributing-area transport;
- MFD-derived continuous vector field;
- accepted lakes as routing supernodes;
- один canonical spill outlet на accepted lake;
- continuous world-space river geometry как цель;
- operator diagnostics: flow vectors, accumulation, raw support, final rivers.

MFD был введён после отклонения two-receiver D∞ accumulation. На H09-B он заметно уменьшил directional grid-lock и сделал accumulation field визуально более плавным.

## Что отвергнуто

### D8 canonical routing

Отвергнут: сильный 0°/45°/90° lattice imprint.

### Two-receiver D∞ accumulation

Отвергнут на первом H09: grid bias оставался уже в accumulation/channel skeleton.

### Прямая channelization широкого MFD support

H09-B показал новую ошибку:

```text
MFD accumulation
→ broad threshold support
→ множество соседних threshold-crossing cells
→ сотни semantic sources
→ параллельные/дублирующие реки
```

Representative 180×120 км checkpoint:

```text
H09-B:
  routing grid-lock within 1°: 8.70%
  final vector grid-lock:       10.97%
  nodes / segments:             636 / 408
  sources / confluences:        353 / 42
```

Операторская оценка: идея MFD была полезной, но итоговая сеть неприемлема. Проблема локализована в channel extraction, а не в renderer.

## Принятый следующий design

`docs/design/channel-skeleton-extraction-v0.2.md`

Идея:

```text
MFD contributing area
→ raw threshold support as diagnostic only
→ deterministic dominant single-downstream channel projection
→ unique source-initiation catchment area
→ one-cell-wide merge-only semantic skeleton
→ semantic sources / confluences
→ continuous world-space tracing
→ H09-C
```

Ключевая граница:

```text
diffuse hillslope transport != semantic channel graph
```

Для channel source threshold используется уникальная площадь бассейна на dominant projection, чтобы соседние MFD cells не считали один и тот же fractional catchment множеством независимых истоков.

MFD accumulation остаётся canonical hydrology diagnostic и источником catchment-area magnitude для итоговых river segments.

## Acceptance principle

Для spatial-generation слоёв:

```text
implementation
→ automated guardrails
→ representative operator-visible render
→ explicit ACCEPT / REJECT
```

Green CI не заменяет operator acceptance.

## Заблокировано

До принятия Hydrology 0.2:

- Surface redesign;
- Placement continuation;
- merge PR #72;
- cosmetic smoothing вместо исправления upstream semantics.

## Текущий implementation checkpoint

Accepted channel-skeleton design реализован в активной ветке PR #72.

```text
MFD accumulation
→ dominant single-downstream channel projection
→ unique source-initiation catchment area
→ one-cell-wide merge-only skeleton
→ continuous world-space tracing
```

Representative H09-C на том же мире 180×120 км сгенерирован.

Автоматический статус:

```text
pytest: green
H09-C workflow: green
engine invariants: green
```

Диагностические числа до operator verdict:

```text
H09-B direct MFD support:
  nodes / segments:       636 / 408
  sources / confluences:  353 / 42
  final river length:     ~3320 km
  final grid-lock 1°:     10.97%

H09-C thin skeleton:
  nodes / segments:       52 / 30
  sources / confluences:  14 / 3
  final river length:     ~533 km
  final grid-lock 1°:     9.66%
  raw support cells:      679
  skeleton cells:         409
```

Эти числа не являются ACCEPT. Они показывают, что over-fragmentation резко подавлена, но оператор должен решить, не перешли ли мы в противоположную крайность — слишком редкую/обрезанную сеть.

## Следующий bounded task

```text
1. Показать H09-C оператору.
2. Сравнить H09-B vs H09-C: final rivers, accumulation, raw support/skeleton.
3. Получить explicit ACCEPT / REJECT.
4. Если REJECT:
   - при слишком редкой сети → разбирать source initiation / threshold topology;
   - при grid-like skeleton → переходить к continuous ridge/flow-tube extraction;
   - при trace/skeleton mismatch → чинить их согласование.
5. Не переходить к Surface / Placement до Hydrology ACCEPT.
```
