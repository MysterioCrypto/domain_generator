# Rolling Context / Backlog

Этот файл — сжатая рабочая память проекта, а не журнал событий.

Он должен позволить продолжить разработку без восстановления всей переписки: где мы находимся, что принято, что отвергнуто, почему это важно и какой следующий bounded task.

## Правило ведения

Файл **переписывается**, а не бесконечно дополняется.

Обновлять только когда меняется смысловая точка: принят/отклонён human checkpoint, принят design gate, завершён implementation slice, изменена active line или следующий bounded task. Не вести здесь commit-by-commit/CI историю.

Оставлять прошлое только если оно:
- ограничивает текущие решения;
- объясняет, почему нельзя повторять уже отвергнутый путь;
- нужно для корректного восстановления следующего шага.

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
  PR #72 H09 on representative 180×120 km world
  status: REJECTED as final hydrology base
```

Не выводить состояние проекта из `main`; active development line — `dev/0.2`.

## Что принято и сохраняется

### Terrain 0.2

Принят как минимально приемлемая база. Не возвращаться к его redesign без нового конкретного дефекта.

`docs/design/continuous-terrain-foundation-v0.2.md`

### Hydrology concepts, которые прошли текущую итерацию

Сохраняем:

- continuous direction-field concept и flow-vector diagnostic;
- Priority-Flood conditioning;
- accepted lakes as routing supernodes;
- один canonical spill outlet на accepted lake;
- continuous world-space river geometry как цель;
- H09 diagnostic views:
  - terrain + final rivers;
  - continuous flow vectors;
  - accumulation field;
  - channel support vs final rivers;
  - lake outlets.

Оператор отдельно отметил, что flow-vector и "призрачное" accumulation отображение полезны именно как симуляционный diagnostic: по ним видно, на каком слое появляется артефакт.

## Что отвергнуто

### D8 canonical routing

Отвергнут ранее: выраженный 0°/45°/90° grid-lock. Не возвращаться к D8 + decorative reconstruction.

### PR #72, первый H09 Continuous Drainage checkpoint

Реализация была значительно лучше D8, но оператор её **не принял**.

Наблюдаемые проблемы:

- длинные прямые участки без читаемой физической причины;
- прямоугольно-ломаные/ступенчатые траектории;
- странные короткие ветви/сегменты;
- несколько рек, идущих подозрительно параллельно там, где terrain не даёт очевидного структурного объяснения;
- lattice pattern виден уже в accumulation field, то есть проблема возникает upstream от final renderer.

Важный вывод:

```text
smooth/continuous-looking local direction
→ two-neighbour raster transport
→ grid-imprinted accumulation ridges
→ thresholded channel support
→ vector tracing поверх уже дискретного skeleton
```

Поэтому следующий шаг — не smoothing финальных рек.

## Внешнее исследование, поддерживающее redesign

После REJECT был проверен literature/reference context.

- D∞ действительно распределяет поток между двумя соседними cells по continuous angle.
- Современная сравнительная работа (Earth Surface Dynamics, 2025) отдельно показывает, что D∞ accumulation может сохранять значимую cardinal/ordinal orientation bias.
- В той же работе классический slope-weighted MFD с exponent около 1.1 показывает существенно лучшую rotational invariance на ряде analytic/real-terrain tests.

Это **аргумент для следующего design gate**, а не автоматически принятая реализация.

## Принятый следующий design

Оператор принял docs-only design gate `docs/design/low-bias-contributing-area-v0.2.md`.

Следующая bounded implementation:

```text
conditioned elevation
→ low-bias multi-flow flux (all downslope neighbours; slope-weighted)
→ mass-conserving contributing area
→ lake supernodes / single outlet
→ channel support
→ continuous vector tracing consistent with flux
→ same H09 operator checkpoint
```

Design gate принят. Implementation теперь разрешена по INV-006, но сама Hydrology 0.2 остаётся непринятой до нового H09-B operator checkpoint.

## Acceptance principle

Для генеративных spatial layers:

```text
implementation
→ минимально необходимые automated guards
→ representative render / diagnostics
→ показать оператору
→ explicit ACCEPT / REJECT
```

Green CI не является human acceptance. Красивый render также не заменяет invariants. Нужны оба слоя проверки.

## Заблокировано

До принятия Hydrology 0.2:

- не переходить к Surface redesign;
- не продолжать Placement;
- не считать PR #72 accepted base;
- не лечить lattice imprint renderer/post-smoothing.

## Следующий bounded task

```text
1. Слить accepted low-bias design в dev/0.2.
2. Синхронизировать implementation branch.
3. Реализовать только transport/accumulation slice.
4. Сохранить lake semantics и H09 diagnostics.
5. Перерендерить тот же 180×120 км representative world.
6. Сравнить side-by-side с rejected H09.
7. Получить operator ACCEPT / REJECT.
```
