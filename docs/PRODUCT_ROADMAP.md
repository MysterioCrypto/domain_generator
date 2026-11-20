# Product roadmap — карты неземных миров

Статус: **рабочая продуктовая программа**, не нормативный договор о физических алгоритмах. [Навигация](../START_HERE.md). Дата: 2026-11-15.

## Что мы строим

Внешний авторский World Profile (мир, планетный год, климатические настройки, локальные правила, источники географии, явные исключения) → универсальный DomainSpec + presets → принятый Core 0.2 Terrain/Hydrology/Climate/Surface/Placement → опциональный **world-defined land cover** → карта-подложка с точной геометрией → опциональный ImageGen → финальная географически контролируемая иллюстрация с возвращёнными рекой/озёрами/населёнными пунктами/подписями.

**Не** обещать, что адаптер World Profile, land cover или автоматизированный ImageGen уже реализованы. Кёппен, земные лесные сообщества и 365-дневный год не должны быть обязательными.

## Контрольные пакеты работ

| Шаг | Что делаем | Условие завершения |
| --- | --- | --- |
| P0 — навигация / provenance (сейчас) | Единый START_HERE, карта PR, реестр источников, различение канона и моделей | В проект можно войти по 1 ссылке |
| P1 — боевой fixture Д’Акхара | Исходные ZIP A8/A10/A12 **найдены в Drive**, далее проверяем архивы/георастры/хэши, планетное время и проекцию; либо делаем явно новую интерпретацию | Не выдумана каноничная координата, есть воспроизводимая региональная спецификация |
| P2 — разнообразие рельефа/реки | Три различных **географических** региона: ущелье и верховья, большой речной бассейн, островной/прибрежный рельеф | GREEN Actions с осмысленными различиями hillshade, высот, рек |
| P3 — природный покров | Опциональный внешний набор классов и предпочтений по климату/высоте/влаге, пространственная связность и экотоны | Поля, из которых различимы лес/луга/скалы/берега; не просто зелёный градиент |
| P4 — спутниково-картографическая подложка | Совмещённые elevation, water, river, cover, source ID, projection/scale; без искусственного умножения географического разрешения | Карта похожа на реальный вид сверху до ImageGen |
| P5 — изображение | ImageGen добавляет детальность/фактуру; проверяем маски и возвращаем точные источники | Художественная карта, верная ключевой географии |
| P6 — новая чистая репа | Лишь позднее: аудит PR, версий, контента, лицензий, контрактов; репу создаёт пользователь | Миграция контролируется пользователем, не происходит сейчас |

## Настоящие технические границы

- Принято: многомасштабные высоты, MFD, региональные и потенциальные реки, озёра, опциональный морской берег, годовая и опционально сезонная климатология, C2 индекс влаги, C3 индекс растительности, ограниченное размещение POI.
- **Не реализовано:** полноценные категории живого покрова и биомов (C3 не значит лес), точная физика стока/долговечности рек, почвы, планетарный климатический адаптер, автоматическая художественная перерисовка.
- H13 #99 технически работает только в черновой ветке и показывает **валовое распределение атмосферных осадков**, а не реальный расход рек; не считать его необходимой предпосылкой лесной карты.
- C2 #100 — полезный научно-художественный эксперимент, не команда изменить общий default; в DomainSpec уже есть редактируемый water_moisture_decay_km.
- Composer #101 — работающий подготовительный экспорт, но до полноценного land cover результат неизбежно декоративный/абстрактный.
- Планета Д’Акхара в A12 приблизительно 202,755 земных суток на один **планетный** год. Показатель осадков за такой год нельзя молча интерпретировать как земные mm/year при обмене между моделями.
- Размер пикселя экспортируемого PNG не равен физическому разрешению исходного поля. Пример A8/A12 — около 25–37 км между центрами в исследуемой широте, пример текущего DomainSpec — 1 км клетка.

## Приоритеты и стоп-правила

Не добавлять механистическую эрозию, атмосферную циркуляцию, почвенную биохимию и десятки типов леса только для научного впечатления. Перепроверять источник, затем создавать карту и оценивать **визуальную полезность**. Если дефекта нет — оставлять принятый компонент неизменным.

Зелёные тесты обязательны, но не равны разрешению на merge. По прежним PR #99/100/101 требуется интеграционная проверка, не слепое соединение. Замороженная ветка release/0.2-prealpha сохраняется.


**Source discovery correction 2026-11-15:** прямой folder fetch показывает ZIP A1–A11 в архивной подпапке и A12 ZIP плюс подложку и карты биомов в главной папке. Предыдущий Drive search по parent вернул неполную выборку. Статус P1: **A8/A12 CONTENT PARSED AND VERIFIED, A10/A11 SOURCE ARRAYS + HASH VERIFIED; GEOGRAPHIC IMPORT PENDING, CORE IMPORT PENDING**; не надо заменять реальную географию случайным новым материком из-за ошибки поиска.


**Проверенная осевая ловушка:** A8 lat идёт с севера на юг, A12 lat с юга на север. Без точного разворота A8 строк матрицы рек/водосборов и климатические/экологические поля A12 совмещаются неверно. Проверено: A8 elevation[::-1] == A12 elevation и A8 land[::-1] == A12 land **exact**. Это не физическая проблема, а критическая ошибка геопривязки на стыке двух исторических моделей. Детальный отчёт: [A8/A12 source alignment](reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md).


## P1 planetary macro-geogrid adapter — 2026-11-15, DRAFT #103

- User's non-Earth source A8/A10/A11/A12 archives are verified (SHA/CRC, A8 north-first vs A10/A11/A12 south-first) and kept PRIVATE. Source A8 global D8 is an older research hydrology, not Core 0.2 accepted MFD.
- On an isolated DRAFT [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), external-only script scripts/export_planetary_macro_region_v02.py reads paths of original ZIPs, validates exact A8/A12 shared land/DEM, accepts user-specified planetary radius/year and local km source crop, remaps BOTH endpoints of A8 global flattened D8 downstream indices, and flags rivers exiting crop. It emits source NPZ+manifest+PNG, deliberately NOT DomainData and NOT fake local 1-km elevation.
- Synthetic workflow [GREEN](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913) passes 4 targeted tests and writes a demo artifact. No private source ZIP/PNG was committed or uploaded to Actions.
- [CLI instructions and explicit boundaries](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Next meaningful work is source-constrained finer regional terrain and new MFD river generation, followed by non-Earth profile-based land cover; not further parchment filters or full planetary climate science.
- This is a parallel draft branch. PR #99 H13, #100 C2 tests, #101 atlas composer remain DRAFT/UNMERGED. Frozen release c69c1af010a085fb80d248af703a77471fc6c9d7 remains unchanged.

**Прогресс P1:** source-only A8/A10/A12 geogrid adapter реализован на draft #103, четыре синтетических теста GREEN. Сохранены реальные source Q и оригинальные границы. Это не означает, что уже есть детальный дочерний регион, Core-инъекция высот или независимая проверка старого A10 стока. P2 остаётся задачей настоящей региональной детализации.


**P2-A, draft PR #103: региональный рельеф из исходной планеты готов в виде внешнего эксперимента** (трёхрегиональные карты A/B/C по 230×230 км, 1 км на пиксель, 63/49/49 исходных высот сохранены точно). Новая локальная форма построена процедурно; старый источник 0,3° остаётся макрореальностью, не картой малых рек. Поправлены видимые прямоугольники билинейной интерполяции гладким C1 Hermite. **Следующая работа P2-B — гидрологическая связность** новых MFD водотоков с макровыходами A8. [Пределы](world-fixtures/planetary-child-terrain.md).


**P2-B1 (16.11, draft #103):** новый MFD по дочернему рельефу и консервативная граница локального водосбора проверены в CI, 19 тестов GREEN; A8 D8 используется как отдельный исходный ориентир. Реальные A/B/C выявили глубокие замкнутые понижения (B≈88,5м, C≈60м) и ложную веерообразную картину предварительной гидрологии. P2-B2 обязан сначала корректно учесть озёрные supernodes и входящие/выходящие крупные водосборы; простого рисования речных линий или масштабирования A8 недостаточно. [Аудит](reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).


### P2-B2.1 — geometric lake basin review (2026-11-20, PR #103 DRAFT)

- [Visual synthetic QA](https://github.com/MysterioCrypto/domain_generator/actions/runs/44748762996) and [operator review](reviews/p2-b2-1-child-lake-basin-operator-checkpoint-2026-11-20.md): external read-only `scripts/audit_planetary_child_lakes_v02.py`, Core Priority Flood/extract_lake_candidates/choose_lake_outlets, bounded nested hierarchy, Core lake-supernode conservation on SMALL bowl only. Proposed basin ≠ actual water occupancy; no universal Earth-specific thresholds, no external inflow, no source-D8 substitution.
- 27 focused tests GREEN; full algorithmic SHA pytest 532 GREEN; final docs SHA must have new CI. Private A/B/C sensitivity screening performed locally using independently interpolated DEM, not an exact PR P2-A regression; resulting numerical/visual data stay in conversation only.
- P2-B2.2 next: source-macro boundary inflows/outflows and constrained MFD+lake supernode routing, before asserting credible river/ford/waterfall geometry. Keep PR #103, #99–101 draft/unmerged. Frozen `release/0.2-prealpha` unchanged.


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.

**P2-B2.2 / NEXT P2-B2.3:** теперь имеются внешние направленные A8 входы, явный сценарий внешней-only площади и проверенный консервативный MFD с геометрическими supernodes. Реальные A/B/C входы A=1, B=0, C=0; ни одно старое значение водосбора не вводится автоматически. Следующий P2-B2.3 — доказать внешнюю-only площадь по глобальному A8 и перейти к действительно связной новой сети русел, затем P3 world-specific биомы. [Отчёт](reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md).


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.

**P2-B2.3 source macro water provenance implemented:** an exact old A8 global-graph first-entry exterior source partition, including reentry non-double-counting, supports safe downstream integration. Real A/B/C old input links all=23/12/5, old major=1/0/0; one large A source basin ≈86,107km² is now independently counted as macro EXTERIOR. Still no local MFD injection; **P2-B2.4 next**: compare accepted MFD terminal/basin geometry to major original A8 outlets and build connected local channels. [Detailed evidence](reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md).


### P2-B2.4 (2026-11-20): old A8 macro river exits vs CONNECTED CHILD Core MFD dominant channels — DRAFT #103

- New read-only external script scripts/compare_planetary_child_mfd_outlets_v02.py: directionally **INSIDE→OUTSIDE** old major A8 D8 links (distinct from earlier inlet provenance), accepted Core Priority Flood+MFD, Core dominant-channel area+terrain-aware initiation, positive-fraction adjoining channel edges traced to actual region boundary, and explicitly NONPHYSICAL jumps across geometrical lake proxy supernodes. Generates georeferenced-local-km masks/edge pairs + three-panel diagnostic PNG and manifest. This is NOT accepted Core RiverNetwork, physical water Q or proof of perennial lakes.
- Thresholds `stream_threshold_km2=30` and `matching_tolerance_km=30` are editable **demo** parameters, not immutable Earth/world rules. Matches only same boundary side within spatial tolerance, unique one-to-one, always tagged GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED; unmatched stays UNMATCHED, no terrain correction or A8→MFD forced merge.
- [Operator evidence](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-mfd-outlet-review.md). [GREEN synthetic map](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499) with 49 focused tests: toy A8 has **1 major macro exit**, new connected MFD cartoon has **19 terminal edge cells**, **1 same-side within-30km purely spatial match**. The discrepancy is exposed, not patched. Old source A/B/C major EXITS known A=1, B=2, C=0, but **actual real private A/B/C CHILD MFD outlet matching was NOT yet run**, do not invent distances.
- The CI demonstration is SYNTHETIC ONLY; original private literary planet A8/A12 and derived real maps have not been committed to public GitHub. Full pytest is to be confirmed at FINAL branch SHA; earlier source version had 554 tests passed. PR #103 DRAFT/UNMERGED. PR #99–101 remain drafts. dev/0.2 and frozen release untouched.
- **NEXT P2-B2.5**: run real private A/B/C matching, then specifically condition coarse river corridors and watershed boundaries on real source at 1km without changing original macro-station heights; recompute MFD and compare before/after. Land cover P3 and ImageGen only after credible river continuity.

**P2-B2.4 экспериментальный контроль русловой связности:** диагностические связные пути на детальном MFD с Core terrain-aware threshold и сравнение с крупными старой A8 речными ВЫХОДАМИ. Новая сеть может отличаться, даже когда 0.3° глобальный водосбор известен. Синтетический пример обнаруживает 1/19 выходов (A8/MFD) и одну только геометрически близкую пару; auto-correction запрещена. [Отчёт](reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md). Следующее P2-B2.5 — настоящие A/B/C и source-conditioned поправки; далее P3 природный покров и P4 художественная карта.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.

**P2-B2.5 — отрицательный эксперимент полезен:** первичная реальная приватная (независимая от Core lake) проверка A/B/C показывает, что выходы старой A8 и новых рельефно обусловленных MFD рек A/B уже близки. Пробная коррекция -15м вдоль крупных макро-рек A ухудшила совпадение с 0.028 до 11.972км; B не улучшила; C не имеет крупного исходящего A8 для метрики. На Core ничего не применено. [Отчёт](reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md). Следующее P2-B2.6 — реальные геометрические озёрные чаши и lake supernodes B/C, затем P3 покров и P4 визуализация.
