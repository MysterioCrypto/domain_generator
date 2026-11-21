# Осве́ра — первый авторский атлас: карта для непротиворечивости арок

**Версия продукта: ранний P3/author-first прототип, не литературный канон.** Планета **Осве́ра** — рабочее название без окончательного утверждения автора. **Д’Акхар — главный герой**, ксенолог, а не топоним, регион или название планеты.

## Ради чего существует продукт

Автору нужна воспроизводимая география: где находятся места действия, какие реки/горы/дороги встречаются по пути, насколько далеко один сюжетный объект от другого, что персонаж может увидеть, где проходит граница опасной местности и не перескакивает ли география между арками. Возможная читательская карта — необязательный побочный результат. Пакет диагностических карт по наукообразной гидрологии НЕ является продуктом.

**Условие необходимой достаточности:** не дорабатывать бесконечно P2-B2, если уже достаточно рельефа и корректной связности для авторского карты-черновика. При локальной неразрешённой котловине честно помечать неопределённость и возвращаться к расчёту, когда это влияет на сюжет/маршрут.

## Первый работающий прототип

- [Скрипт формирования авторского листа](../../scripts/render_author_region_atlas_v02.py) объединяет уже существующий child DEM 1 км и реестр сюжетных мест в одной читаемой схеме. Не создаёт новых координат. Дополнительно может показать **отдельно рассчитанную** модельную маску MFD каналов, но не выдаёт её за подтверждённые реки.
- [Реестр первой арки Осве́ры](../../examples/world-fixtures/osvera-first-arc-author-ledger.json) содержит 5 известных из текста мест с **НЕУСТАНОВЛЕННЫМИ** координатами и 2 известных по смыслу, но геометрически не заданных отношения маршрута. Никаких фиктивных расстояний.
- Выход: **author-atlas-sheet.png** (одна карта и список известных мест), **author-atlas-audit.json** (машинные причины неопределённости/известные метрики), **author-atlas-notes.md** (человекочитаемый журнал мест/маршрутов).
- Публичный [Actions с синтетической картой](https://github.com/MysterioCrypto/domain_generator/actions/workflows/author-region-atlas-v02.yml) создаёт **не** географию Осве́ры, а демонстрацию визуального продукта с заведомо вымышленным DEM. Настоящая география и исходные архивы остаются приватными.
- Ранее технический файл [dakhar-first-arc-anchors.json](../../examples/world-fixtures/dakhar-first-arc-anchors.json) содержит исторический идентификатор по *имени героя*. Он не должен трактоваться как название географического региона, и его нельзя молча переименовывать, ломая проверки/ссылки.

### Запуск на рабочем районе A

Сначала — приватно и локально — подготовить в одном checkout [child-terrain-generated.npz](planetary-child-terrain.md) из старых архивов A8/A12. Реестр привязан к модельному центру A `-47.25°/-98.25°`, что является **неутверждённым** вариантом размещения первой арки.

```bash
python scripts/render_author_region_atlas_v02.py \
  --child-npz /private/child-A/child-terrain-generated.npz \
  --child-manifest /private/child-A/manifest.json \
  --ledger-json examples/world-fixtures/osvera-first-arc-author-ledger.json \
  --output /private/child-A/author-atlas
```

Опционально: `--channels-npz /private/child-A/macro-vs-MFD-outlets/connected-MFD-channel-reference.npz` — канал остаётся только **модельным кандидатом**.

Если пользователь сам зафиксирует географию, в конкретной записи можно указать `position: [east_km, north_km]`, `position_status: AUTHOR_FIXED`, `position_source: <идентифицируемый авторский источник>`. Для гипотезы вместо AUTHOR_FIXED указать MODEL_PROPOSAL. Без координат и источника запись остаётся UNPLACED.

Для маршрутов есть два разных результата: **по прямой — только нижняя граница длины, не путь**, по явно начерченной полилинии — длина *модельного* пути. Время в дороге, состояние перевалов и скорость перемещения программа не придумывает.

## Что намеренно ещё НЕ сделано

1. **Природный покров** — лесные массивы, открытые пространства, болота/скалы не выводятся только из высоты; нужен профиль мира и базовый климат/влажность.
2. **Авторски утверждённые координаты/дороги** — для пяти мест первого арка пока нет; карта не должна подменять решение автора.
3. **Рисование полноценного маршрута по местности** — нельзя считать прямую линию реальной дорогой и выводить скорость/время из воздуха.
4. **Реальные пригодные для чтения картографические ландшафты** — это следующий продуктовый этап: объединить рельеф, модельный природный покров, водоёмы и ориентиры с легендой и масштабом. ImageGen — только позже и только при защите географии.

## Следующий продуктовый шаг

**P3-MVP:** сделать ограниченный, настраиваемый по миру генератор *правдоподобного* природного покрова для модельной территории A и собрать одну цельную карту с лесами/полянами/каменистыми местами и обозначенными **неразмещёнными** местами сюжета. Две карты — модельный рельеф и собранный авторский вид — достаточны для оценки; массивные графики остаются внутренними проверками.

Если P2-B2.7 показывает существенное отличие реальной B/C lake-supernode сети, применить его локально, но не останавливать весь продукт ради бесконечного уточнения численных методов. Исходная география 0,3° не подтверждает мосты/водопады в 1-км пикселях.


## Первое приватное воспроизведение — реальный модельный район A

**21 ноября 2026:** исходные приватные A8/A12 ZIP считаны локально; сначала точный GH-скрипт макроэкспорта, затем точный `condition_planetary_child_terrain_v02.py` дал **231×231** с шагом 1 км на площади **230×230 км**, **63** исходные высотные точки без ошибки, новые модельные высоты от ~232,85 до 834,25 м. Новый авторский лист показывает пять достоверных по тексту, но не размещённых по координатам мест, два необозначенных реальной дорогой маршрута, масштаб и рельеф. Палитра рельефа приглушена, с горизонталями; **цвет не доказывает наличие леса**. Реальные данные, изображение и компактный авторский архив переданы в приватной беседе и НЕ загружены в GitHub. [Полный операторский отчёт](../reviews/osvera-first-private-author-atlas-2026-11-21.md).



## P3-MVP 2026-11-21 — source-conditioned noncanonical author natural cover

**Problem:** A visually useful author continuity map requires actual forest/open/rock/wetland candidate patterns; C3 vegetation potential and A12 source-biome code alone do not supply observed local cover. Endless lake-correction P2-B2 tests without a location conflict do not increase author usefulness. **Decision:** stop automatic hydrology deepening after P2-B2.6 for A, keep P2-B2.7 exact-Core private B/C validation as a targeted debt, implement ONE opt-in external visual land-cover source adapter in DRAFT PR #103.

**Code:** scripts/derive_author_natural_cover_v02.py with explicit editable examples/world-fixtures/osvera-working-cover-profile.json + tests/test_author_natural_cover_v02.py, integrated optional --cover-npz/--cover-manifest to scripts/render_author_region_atlas_v02.py. Source A12 latitude south-first, child north-first. Four source scenario votes blended spatially without source-grid rectangular nearest neighbor blocks; deterministic world-coordinate patch geometry; steep slope rock candidates, forest/open mosaic, WET LOWLAND only with original A12 wetland candidate AND locally lower terrain AND gentle slope. **Rejected:** directly treating broad A12 wetland_candidate mask as real swamp/water (early private candidate miscolored 65% of A as wet). Result is not canonical biome, measured forest, groundwater, permanent water or terrain mutation; no chosen landmark coordinates or travel times inferred.

**PRIVATE source real Osvera A:** independent cubic source-interpolated 231² region 230×230 km from original private A12, original source stations exactly reproduced numerically; candidate artist map ~71.9% woodland, ~16.2% open, ~11.9% potential lowland, zero forced rock. This private preview is NOT an exact current PR #103 P2-A/Core DEM replay, nor a claim of actual Osvera ecosystems; original source ZIP and derived map kept in ChatGPT, not public GitHub. [Review](reviews/p3-mvp-osvera-natural-cover-2026-11-21.md), [offline private runbook](world-fixtures/osvera-author-natural-cover.md). [Synthetic author-map CI](https://github.com/MysterioCrypto/domain_generator/actions/runs/44887608102) **16 focused tests GREEN**; check final SHA full pytest after docs.

**NEXT:** run P3 on EXACT source-conditioned child-A from this same PR #103 checkout using original private A12, inspect ONE author-facing complete cover map, not technical heatmaps. Then optional river topology/author landmark/route placement with explicit approvals and distance semantics; ImageGen only after geographic stabilization. **Planet working name Осве́ра, protagonist Д’Акхар** (not a toponym). PR #103 DRAFT/UNMERGED, dev/0.2 and frozen release untouched.
