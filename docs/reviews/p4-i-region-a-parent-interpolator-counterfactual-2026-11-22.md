# P4-I — source-station-preserving parent interpolator counterfactual (NOT CANONICAL rivers)

**Дата:** 2026-11-22. **PR:** [#103](https://github.com/MysterioCrypto/domain_generator/pull/103), Draft/Open/Unmerged. **Режим:** read-only derived diagnostic. Accepted `dev/0.2`, `release/0.2-prealpha`, original A8/A12, author POIs не изменялись.

## Что изолируем

P4-H показал, что parent-only Hermite DEM уже даёт 98.49% model channel edges в однородно направленных цепочках длиной ≥8 рёбер. Было не ясно, в какой степени эта регулярность создаётся интерполятором, а не структурой самого макроисточника A8.

Эксперимент заменяет **только родительский интерполятор**: существующий `_c1_cubic` (Hermite C1) против `_bilinear` из того же `condition_planetary_child_terrain_v02.py`. Макро DEM, исходные source elevation stations, child domain 231×231, планетный радиус/проекция, coastline, source `new_local_relief_m` внутри каждого варианта и порог 30 км² остаются неизменными. Подмена `accepted Core` отсутствует.

На новых кандидатах снова независимо вызывается `connected_mfd_channel_projection` (MFD+1-receiver). Три прежние исходные проекции P4-F воспроизведены **бит-в-бит по всем массивам**; предыдущий P4-H JSON предоставляет точные SHA-256 source. Отдельный нулевой контроль родительской поверхности не включает никакой local detail.

**Правило fail-closed:** если изменились source-station heights, source coastline, количество опор, source SHA, эталонные проекции, numerical mass balance либо source axes, CLI завершается ошибкой. Даже при неизменных source anchors нельзя объявлять сохранённой outlet topology.

## Проверенные высотные инварианты

| Проверка | Наблюдение |
|---|---:|
| Исходные height stations внутри региона | **63** |
| Абсолютная ошибка Hermite на source stations | **0 м** |
| Абсолютная ошибка bilinear на тех же stations | **0 м** |
| Replay исходного float32 parent raster относительно Hermite | **≤ 3.06×10⁻⁵ м** |
| Разность bilinear − Hermite, минимум | **−49.00 м** |
| Разность, максимум | **+52.68 м** |
| RMS разности | **9.335 м** |
| Смена знака суша/море, перекрытие land mask | **нет** |

Следовательно, разные DEM существуют при идентичных наблюдаемых высотах в 63 узлах; совпадение узлов **не означает** совпадения склонов и водосборов между узлами.

## Независимые новые model-channel маршруты

Порог во всех случаях **30 км²** — площадь для извлечения модели, а не расход Q. Каналы/озёра/физическая постоянность НЕ установлены.

| Relief strength | Model edge proportion in runs ≥8: Hermite | Bilinear | Channel mask IoU | Model channel boundary outlets Hermite → bilinear |
|---|---:|---:|---:|---:|
| 0.0, отрицательный parent-only контроль | 98.49% | 99.06% | 89.39% | **7 → 2** |
| 0.5 | 47.67% | 51.78% | 43.37% | **22 → 20** |
| 1.25 | 17.95% | 18.86% | 60.10% | **20 → 17** |
| 2.0 | 15.78% | 14.80% | 65.71% | **25 → 22** |

**Каждый из четырёх случаев меняет множество boundary endpoint pixels**, хотя координаты и опорные высоты не изменяются. Для точного pixel совпадения dominant terminal по всем model cells: 2.17% / 64.10% / 95.92% / 94.76% соответственно (0 / 0.5 / 1.25 / 2). Доля совпадения *стороны* границы ≥99.0% для всех четырёх, но совпадение стороны **не является** сохранением топологии.

На исторической P4-C1 reference-cell [220,224] точный модельный endpoint сохранился для 0.5/1.25/2.0, изменился для parent-only. Это отдельная локальная наблюдаемость, не подтверждение речной идентичности.

**Инженерный вывод:** bilinear НЕ является улучшением по исследуемой прямолинейности при 0/0.5/1.25, а при 2.0 улучшение небольшое, с изменившимися outlet sets. Сохранение C1 Hermite на текущем этапе рационально; **не принимать** альтернативу. Это подтверждённый отрицательный результат, а не «проблема только в интерполяторе».

## Границы вывода

- Контролируемая замена позволяет измерить чувствительность модели к интерполятору **при фиксированном данном A8 макроисточнике**. Она **не** отделяет географическую достоверность A8 от его масштаба и не доказывает, какой новый источник был бы лучше.
- Bilinear непрерывен по высоте (C0), но имеет разрывы производной на границах исходных клеток. Для русловой геометрии это потенциальный grid-lock механизм, не повод объявлять C1 правдой.
- Длинные прямые runs — свойство выбранных модельных 8-neighbor ребёр; физически непрерывный MFD и water discharge отличаются.
- Исходный frozen P4-E P3 фон используется **лишь** для визуального сравнения двух *пересчитанных сетей*; цветной фон **не пересчитан** под bilinear и не должен считаться согласованной новой картой.
- Не добавлена площадь извне из A8 D8. MFD float64 ledger сохраняется, accepted parent/source bytes не переписаны.
- Все рассчитанные поля в ZIP — **производные и неконанические**.

## Архив / воспроизводимость

- [Сравнение 2×3: модельные скелеты Hermite vs bilinear](https://drive.google.com/file/d/1V46y7uZIhz35XcO75aSdubdlm78riVq1/view).
- [Parent height difference heatmap](https://drive.google.com/file/d/1JOGnRG1J94IskN29mCDXBk7lzF0LaAkk/view).
- [PRIVATE derived ZIP: два PNG, 4 NPZ, JSON/CSV, SHA provenance](https://drive.google.com/file/d/1Fa8OiUgD_yJaK3NZ7hXWJiSxxuLZMp16/view). Исходные A8/A12 ZIP и персональные авторские данные в архив не добавлялись.
- [Предыдущий P4-H](reviews/p4-h-parent-only-negative-control-directional-bias-2026-11-22.md); прежние source P4-B/E/F/H сохранены отдельно в Google Drive.
- Исходный скрипт `scripts/compare_region_parent_interpolants_v02.py`, blob SHA-1 `42659d78afda050fb7e3dc94deffa508a14423e8`. Синтетические тесты `tests/test_region_parent_interpolants_v02.py`, blob SHA-1 `8be655351321e3e4b6d5967d539af4dc6f295ddf`. **15 toy tests**, включая полный независимый Core reroute, проверку 25 anchor узлов в synthetic, источник SHA tamper, immutable detail и byte-identical CLI output. Географический CI включает обязательный toy и условный FULL P4-I на synthetic fixture, если присутствуют upstream inlet-specific артефакты.

## Следующий малый шаг — P4-J

Не продолжать слепой перебор DEM interpolants. В изолированном cartographic-layer proof построить и оценить **геометрическую генерализацию уже выбранного model graph** при строгом сохранении исходных node IDs, confluence connections, endpoint locations и географической привязки. Сравнить читаемость на одной карте региона A и явно проверить maximum spatial displacement, self-intersections, segment crossings. Любая новая water/river placement — отдельный operator decision; не использовать ImageGen для утверждения геометрии без машинной проверки. Это display-only гипотеза, никакой Core DomainData mutation.
