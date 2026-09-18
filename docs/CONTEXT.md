# Rolling Context / Backlog

Этот файл — сжатая рабочая память проекта, а не журнал событий.

## Правило ведения

Переписывать только при смене смысловой точки проекта. Не вести commit-by-commit/CI историю. Оставлять прошлое только если оно ограничивает текущие решения или нужно для правильного следующего шага.

## Текущая опорная точка

```text
active:
  dev/0.2
  Terrain 0.2: ACCEPTED
  Hydrology 0.2: redesign in progress

kept hydrology base:
  Priority-Flood
  MFD p=1.1 contributing area
  continuous MFD vector field
  lake supernodes / single canonical outlet
  dominant one-downstream thin channel skeleton

latest experiment:
  H09-D terrain-aware source initiation
  first calibration: FAILED / over-strict
```

`main` не является active development truth.

## Что уже отвергнуто

- D8 canonical routing: сильный lattice imprint.
- Two-receiver D∞ accumulation: grid bias остался в accumulation.
- Direct MFD threshold-mask channelization: 353 sources / 408 segments, множество параллельных дубликатов.

## Что дал H09-C

Thin dominant skeleton решил over-fragmentation:

```text
H09-C:
  sources / confluences: 14 / 3
  segments: 30
  total river length: ~533 km
  final grid-lock 1°: 9.66%
  raw MFD support cells: 679
  skeleton cells: 409
```

Операторская оценка: структура существенно лучше, но вероятно слишком редкая. Поэтому skeleton и MFD сохраняются; следующий вопрос — только channel initiation.

## H09-D: terrain-aware initiation

Accepted design:

`docs/design/terrain-aware-channel-initiation-v0.2.md`

Первый вариант заменил fixed-area source criterion на:

```text
A = unique dominant-graph contributing area
S = conditioned local slope
convergence = incoming MFD fraction sum

score = A * (S / 0.05)^1
source ⇔ score >= 250 km² AND convergence > 1
```

Implementation и diagnostics работают; pytest/H09 workflow green. Но критерий семантически провалился на representative world:

```text
max initiation score: 146.93 km²
required threshold:    250 km²
eligible normal cells: 0

result:
  normal sources:      0
  normal confluences:  0
  river segments:      13
  all starts are lake outlets
  total river length:  ~277 km
```

То есть H09-D в этой калибровке не является кандидатом на acceptance: он удалил нормальные headwaters вместо их восстановления.

## Почему провалился первый H09-D

Проблема не в convergence gate: H09-C fixed-area source cells в основном имеют convergence > 1.

Проблема — absolute slope normalization `S_ref = 0.05`.

На 1 км regional grid типичные slope values существенно ниже field-scale channel-head gradients:

```text
all terrain slope:
  p50 0.0067
  p90 0.0596

convergent cells:
  p50 0.0065
  p90 0.0502

H09-C source examples:
  many slopes ~0.0007–0.016
  unique areas ~250–360 km²
```

Поэтому multiplying the whole baseline criterion by `S / 0.05` уничтожило уже существующие H09-C branches.

## Диагностический вывод: terrain-aware rule должен быть additive

Не следует снова заменять fixed-area baseline.

Следующая конструкция должна быть:

```text
base source eligibility:
  unique_area >= 250 km²

OR terrain-aware promotion:
  unique_area < 250
  AND convergent
  AND steep enough
  AND area-slope promotion reaches threshold
```

То есть H09-C branches не удаляются. Terrain-aware rule может только продвинуть начало существующей/новой ветви выше по крутому convergent headwater.

Это соответствует цели итерации: H09-C был слишком sparse, а не fundamentally wrong.

## Calibration sweep (diagnostic only)

Без изменения production semantics прогнана матрица additive promotion на том же мире.

```text
S_ref   alpha   promoted cells   sources   confluences   skeleton cells
0.005   1.00          218            39         21            853
0.005   1.65         1465           373        278           3225
0.005   2.00         2015           505        368           4100

0.010   1.00           62            17          6            609
0.010   1.65          305            65         42           1231
0.010   2.00          782           227        172           2376

0.020   1.00            7            11          4            432
0.020   1.65           37            16          6            610
0.020   2.00           74            25         12            760

0.050   any             0            10          4            409
```

Эти числа — не acceptance и не выбор победителя. Они только сужают разумную область следующего experiment.

Наиболее bounded кандидаты для visual A/B сейчас:

```text
A: S_ref=0.010, alpha=1.00  → 17 sources / 6 confluences
B: S_ref=0.020, alpha=1.65  → 16 sources / 6 confluences
```

Оба дают умеренное расширение сети вместо возврата к H09-B explosion.

## Научная оговорка

Field literature подтверждает inverse drainage-area / local-slope relation, но абсолютная calibration зависит от process, climate, substrate и measurement scale. Montgomery & Dietrich field relations измерялись на существенно меньшем spatial scale и не могут напрямую задавать `S_ref` для нашего 1 км procedural raster.

Поэтому literature определяет форму зависимости, а Core calibration всё равно должна пройти representative operator checkpoints.

## Acceptance principle

```text
semantic implementation
→ automated guards
→ representative diagnostics/render
→ explicit operator ACCEPT / REJECT
```

Surface/Placement заблокированы до Hydrology ACCEPT.

## Следующий bounded task

```text
1. Не принимать первый H09-D.
2. Зафиксировать additive source-promotion amendment:
   fixed-area H09-C baseline OR terrain-aware promotion.
3. Выбрать одну bounded calibration для следующего visual experiment,
   не sweep-тюнить картинку до красивого результата.
4. Render same 180×120 km world.
5. Compare H09-C vs revised H09-D.
6. Show operator and obtain ACCEPT / REJECT.
```
