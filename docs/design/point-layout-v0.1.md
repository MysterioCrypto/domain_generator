---
id: DESIGN-POINT-LAYOUT-0.1
kind: design
status: accepted
target: core-0.1
---

# Point layout v0.1

Этот документ фиксирует первый исполняемый путь `GenerationPlan -> LayoutCandidate`. Он намеренно ограничен универсальными features с `layout.mode=geometry`, `shape=point`. Названия объектов в иллюстративных примерах ненормативны.

## Генерация

Для каждого resolved feature с point geometry выводится один независимый RNG stream:

```text
attempt_index = current attempt
stage = layout
scope = ["feature", feature_id, "geometry", "point"]
purpose = "position"
```

Из этого stream потребляются ровно два значения `uniform01()`:

```text
u_x = stream.uniform01()
u_y = stream.uniform01()
x_km = domain.width_km * u_x
y_km = domain.height_km * u_y
```

Получившийся `PointGeometry` находится внутри полуоткрытого физического domain `[0,width) x [0,height)`. Порядок обхода features не влияет на stream конкретного feature.

Point layout v0.1 не имеет параметров layout и не выполняет скрытых retries или steering на основе constraints.

## LayoutCandidate

Стадия записывает одну конкретную точку в `geometry_realizations` для каждого поддерживаемого point feature и использует семантический `plan_fingerprint` как `source_plan.fingerprint`.

Этот slice не materializes reservation features. Plan с `layout.mode=reservation` не поддерживается этой стадией до реализации построения reservation.

Аналогично geometry shapes, отличные от `point`, считаются неподдерживаемыми, а не молча аппроксимируются.

## Валидация layout

Генерация и validation являются отдельными операциями. Validation наблюдает candidate и никогда не мутирует и не исправляет его.

Engine invariants этого slice:

- `source_plan.fingerprint` candidate совпадает с семантическим fingerprint переданного plan;
- `attempt_index` candidate совпадает с активным attempt;
- каждый point geometry feature присутствует ровно один раз;
- неизвестные id в `geometry_realizations` отсутствуют;
- каждая реализованная point находится внутри domain или на его границе.

Поддерживаемые измерения hard constraints в этом slice намеренно ограничены:

- `distance`: евклидово расстояние point-to-point;
- `distance`: минимальное евклидово расстояние point-to-axis-aligned-rectangle, равное нулю внутри или на boundary;
- `contained_fraction`: point в rectangle -> `1.0`, иначе `0.0`;
- `overlap_fraction`: point в rectangle -> `1.0`, иначе `0.0`.

Feature selector разрешается только тогда, когда feature имеет point geometry. Для point части `whole` и `center` обе обозначают саму точку.

Неподдерживаемые сочетания evaluator/geometry являются ошибками возможностей engine/pipeline, а не нарушенными пользовательскими constraints.

## Семантика attempt

Сгенерированная point не генерируется заново из-за нарушения hard constraint. Validator сообщает о нарушенном hard constraint, а существующий orchestrator attempt немедленно отклоняет attempt целиком.

Таким образом первая реализация создаёт полный детерминированный путь без скрытого локального поиска:

```text
GenerationPlan
-> semantic RNG streams
-> point geometry realization
-> LayoutCandidate
-> layout ValidationResult
-> ранний pass/reject attempt
```

## Что явно не входит в этот slice

- генерация corridor, band и area;
- boolean operations `RegionSet`;
- materialization placement reservation;
- proposal generation с учётом constraints;
- scoring soft constraints;
- terrain, hydrology, surface и dependent placement.
