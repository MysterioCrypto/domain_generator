# Rolling Context / Backlog

Этот файл — сжатая рабочая память проекта, а не журнал событий.

Он отвечает только на пять вопросов:

1. где сейчас находится разработка;
2. что уже принято;
3. что было отвергнуто и почему это всё ещё важно;
4. какой checkpoint активен;
5. что делать следующим шагом.

## Правило ведения

Файл **переписывается**, а не бесконечно дополняется.

Обновлять его нужно только когда меняется смысловая точка проекта, например:

- принят или отвергнут human checkpoint;
- завершён/отклонён implementation, меняющий активную базу;
- принят новый design gate;
- изменена development line или следующий bounded task.

Не обновлять ради каждого коммита, CI run, мелкого bugfix или refactor, если смысловая точка не изменилась.

При обновлении:

- удалять детали, которые больше не нужны для правильного продолжения работы;
- оставлять старое решение только если оно ограничивает текущую работу или объясняет, почему нельзя повторять прежний путь;
- не копировать сюда историю commits/PR целиком;
- для археологии давать короткий anchor на design/PR, а историю оставлять Git;
- не дублировать normative contracts и алгоритмы, если достаточно ссылки на design doc;
- если файл начинает превращаться в хронику, сжать его заново.

Цель — размер порядка нескольких экранов, а не зеркало разговора.

## Текущая опорная точка

```text
historical line:
  release/0.1-prealpha
  9699c3d8079b8b9710d65eed60ff975158af0ad3
  status: archived / world-generation semantics rejected

active integration line:
  dev/0.2
  status: terrain accepted, hydrology redesign in progress

active implementation:
  PR #72 — Implement Core 0.2 Continuous Drainage Routing
  branch: impl/v0.2-hydrology-river-geometry
  observed head during context recovery: fe0f43eba1bd8fd4273d9bff9c96546c2b7183a2
  status: draft, unmerged, implementation not yet human-accepted
```

Не выводить текущее состояние разработки из `main`: на этой стадии `main` сохраняет 0.1 baseline и не отражает активную 0.2 работу.

## Что принято

### Terrain 0.2

Terrain 0.2 принят как минимально приемлемая основа для дальнейшей разработки.

Причина перехода с 0.1: visual diagnostic показал upstream world-state problem, который нельзя исправить presentation layer.

Принятая смена semantics:

```text
0.1:
flat elevation
+ sparse feature contributions
+ raw Band polyline ridge

0.2:
continuous multi-scale base elevation
+ smooth Band semantic spine
+ ridge as broad 2D massif modifier
+ blended natural Area modifiers
```

Normative design:

`docs/design/continuous-terrain-foundation-v0.2.md`

Terrain checkpoint пройден; возвращаться к его redesign без нового конкретного дефекта не нужно.

### Continuous drainage design

После terrain checkpoint старая hydrology была проверена поверх Terrain 0.2.

Попытка сохранить D8 routing и реконструировать только финальную river geometry была отвергнута. Эксперимент PR #70 улучшил lake semantics, но сохранил выраженный grid bias:

```text
raw D8 grid-locked direction fraction      = 1.000
reconstructed vector grid-locked fraction ~= 0.593
```

Из эксперимента сохранена полезная идея: accepted lake должен иметь один canonical spill outlet и агрегировать lake catchment.

D8 как canonical backend для Core 0.2 отвергнут.

Принят design:

```text
conditioned elevation
→ D∞-style continuous drainage
→ distributed accumulation
→ lake supernodes
→ channelization
→ single-downstream semantic river topology
→ continuous world-space river traces
```

Normative design:

`docs/design/continuous-drainage-routing-v0.2.md`

## Что сейчас реализовано, но ещё не принято

PR #72 содержит текущую реализацию continuous drainage:

- continuous two-receiver routing field;
- distributed accumulation;
- Core 0.2 hydrology dispatch;
- channel support / semantic channelization;
- confluence/channel graph normalization;
- anti-grid-bias tests.

На восстановленном head CI был green. Это означает только то, что автоматическая проверка проходит; это **не заменяет** обязательный human visual checkpoint и не делает PR принятой базой.

Часть разговора между принятием design #71 и последними implementation commits #72 была потеряна при переполнении старого чата. Не восстанавливать отсутствующие мотивы свободными выводами: опираться на design, code/tests и новые явные решения пользователя.

## Активный checkpoint

Следующая задача — не Terrain и не Surface.

Нужно завершить Hydrology 0.2 checkpoint, предусмотренный design:

```text
H05–H08 automated invariants
+ exact replay
+ single-outlet lake semantics
+ no ordinary downstream bifurcation/dead-end
+ H09 representative 180×120 km visual checkpoint
→ human review
```

H09 должен показать минимум:

```text
continuous drainage field diagnostic
channel support
final vector rivers
raw/support vs final overlay
lake outlets
statistics.json
```

После просмотра возможны только две ветки:

```text
checkpoint accepted
→ merge implementation into dev/0.2
→ update this file to the next bounded task

checkpoint rejected
→ redesign/fix routing or channelization
→ do not hide defect renderer smoothing
```

Surface/Placement остаются заблокированы до этого решения.

## Ложные точки продолжения, которых нужно избегать

Не делать автоматически следующее:

- не продолжать Core 0.1 release-candidate review;
- не считать `main` активной 0.2 линией;
- не начинать заново Terrain 0.2 — его checkpoint уже принят;
- не считать PR #72 принятой только из-за green CI;
- не переходить к Surface/Placement до hydrology visual gate;
- не возвращаться к D8 + decorative reconstruction как к canonical 0.2 решению;
- не лечить upstream grid bias только renderer/post-smoothing.

## Следующий bounded task

```text
1. Проверить фактическое состояние PR #72 относительно accepted design.
2. Доделать недостающий H09 checkpoint tooling/artifacts.
3. Запустить representative Terrain 0.2 hydrology world.
4. Показать diagnostic + final river structure пользователю.
5. Зафиксировать явное ACCEPT / REJECT.
6. Только после этого обновить PROJECT.md при необходимости и переписать этот CONTEXT.md.
```
