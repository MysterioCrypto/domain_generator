# Первый боевой источник — Д’Акхар / «Хроника Игдрасиля»

**Source-grounded, но НЕ утверждённая географическая спецификация.** 15 ноября 2026. [Навигация](../../START_HERE.md) · [JSON-протокол](../../examples/world-fixtures/dakhar-first-arc-anchors.json).

## Прочитанные источники и граница канона

- [Актуальная авторская справка, 11.11.2026](https://drive.google.com/file/d/1xYRLhm4R1GzgQWW6D_Ap190QTnjgNaZd/view): действующие авторские факты и правила статусов; приоритет позднего решения автора над ранним, действующей рукописи над рабочей моделью.
- [Миростроение 0.1 — сводный атлас, 08.11.2026](https://drive.google.com/file/d/1eT5odktS2L9SBbSLhXT2KDDf5vmMaQsq/view): рабочие модельные гипотезы A/B/C; сам документ прямо говорит **НЕ КАНОН**.
- [README архива A1–A12](https://drive.google.com/file/d/1q5XUropEnHpIozppSaTQeFZgCFXh_c4n/view) и папки пользователя: [«Карты и модель планеты»](https://drive.google.com/drive/folders/1m01nGXJv8RMoi2c3svnWczY_3TFM2Nez), [«99_Служебное»](https://drive.google.com/drive/folders/1nLu24wOQ3TDowVZwJVtCxd5DDLgUTWVq).
- Актуальные [справка и рукопись](https://drive.google.com/drive/folders/1gPlMD-zBeIBEF6e2240JipWqAfLXJtcA) находятся также в родительской папке вне архива. Не переписывать их из разработки инструмента.

### Доступность оригинальных численных данных

**Исправление ошибки источников:** поиск Google Drive по parent вернул неполный список, но прямой **fetch папок** обнаружил все ZIP A1–A11 в подпапке архива, **A12 ZIP** в главной папке, а также готовую **геопривязанную PNG-подложку**, карты биомов/лесов/речных регионов. Файлы доступны по ID и размеру, однако содержимое **A8/A10/A11/A12** теперь прочитано из ZIP, SHA-256 и CRC проверены; модельные Q у A10 и A12_inputs совпадают **точно**, но это одна и та же модельная величина, не два независимых подтверждения. Никакие эти массивы пока не импортированы в Core. **Ничего не импортировано в Core**. Поэтому неверно говорить «архивов нет»; столь же неверно говорить «мы уже воспроизвели географию A12».

Исходные данные для следующего технического шага:
- [A8 — водоразделы / речная топология, ZIP ~15,9 МБ](https://drive.google.com/file/d/1WvMG9A2kmwBKBvaSTOY0XERElmka6r1s/view)
- [A10 — водный баланс, ZIP ~46,1 МБ](https://drive.google.com/file/d/1C0bklcAIRmlWSHoYIVONuyse_63xBMkH/view)
- [A11 — перенос влаги, ZIP ~66,6 МБ](https://drive.google.com/file/d/1BiIFbCz1UkbxXAtCQYmp_u0BpjJhe9Cu/view)
- [A12 — полные данные планеты, ZIP ~48,3 МБ](https://drive.google.com/file/d/1uPTSaGcynBnsWKF0Mfn-Ykw_0ko3a1mF/view)
- [Геопривязанная основа планетарного атласа, PNG](https://drive.google.com/file/d/1eBUkCDwlDMK85nJjWdBrULnhnPDrXwdK/view)
- [A12 — природные зоны](https://drive.google.com/file/d/1n7Ox_77dnuSvQcU3GgtpB8nPz_3h6pvW/view), [A12 — леса, реки, потенциальные регионы](https://drive.google.com/file/d/16_e6FW6XGE60LTlCF6vi3yMS7Oyv68Mq/view).

## Авторские пространственные опоры (КАНОН / НАПИСАНО)

Влажный лесной скально-предгорный речной бассейн; древняя переправа/руины; погоня к реке; уединённая резиденция мага на выносе над обрывом **около водопада**; лаборатория отводит тепло проточной водой; регулярно обслуживаемая защищённая дорога с ночлегом/почтовым маршрутом и отдельный укреплённый город. Маг живёт **на отшибе**, нельзя ставить под особняком город. Защищённый маршрут не делает все дикие земли безопасными.

Точные координаты города, дома, водопада и переправы **не утверждены**. Не назначать сущностям геоположение исключительно ради красивой карты.

## Географические модельные варианты, НЕ КАНОН

| Вариант | Координаты модели | Температура за модельный год | Осадки **за планетный год** | Модельная среда |
| --- | --- | --- | --- | --- |
| A (предпочтён в черновике) | 46,95° ю.ш., 97,95° з.д. | ≈15,2 °C | ≈848 мм | влажный умеренный лес |
| B | 20,55° ю.ш., 103,65° в.д. | ≈18,5 °C | ≈1232 мм | горный лес |
| C | 18,15° с.ш., 136,65° в.д. | ≈19,1 °C | ≈1401 мм | сезонно-влажный тропический лес |

A12: рабочий радиус планеты ≈7008,1 км; модельный год ≈202,755 **земных суток**, наклон оси ≈29°; звёздная модель тесной пары K+K. Эти параметры — рабочая модель, не обязательный закон Core и не окончательный авторский канон.

Атлас предлагает в варианте A четыре макроячейки вдоль речной системы для особняка, ночлега, города и старой переправы. При сетке **1200×600 с шагом 0,3°** локальное разрешение в этом районе ≈25–37 км: такой расчёт **не может локализовать** порог, водопад, дом, мост или дорогу внутри ячейки. Путь через ночлег около 44 + 44 км и около 89 км по прямой в модели — не уже утверждённая дорога.

## Чего нельзя автоматически делать при переносе в Core

1. **Календарь:** мм за планетный год (≈202,755 земных суток) нельзя подставлять в Core mm/year как год земного образца без определения реального временного базиса и пересчёта/интерпретации.
2. **Геометрия:** текстовая таблица центров не равна георастру A8/A12. Если исходные растры невозможно прочитать или они не позволяют детализировать регион, **только тогда** генерируем **новый** вариант рельефа по сюжетным ограничениям, явно помеченный как новый.
3. **Биомы:** Earth-derived Köppen C5 опционален, C3 означает растительный потенциал, а не «хвойный лес». Биосфера Д’Акхара имеет особые ареалы и магобиологию: классы задаёт внешний профиль сеттинга.
4. **Размещение:** текущие preset/constraint достаточно для широких предпочтительных районов, но не обещают готовую точную фиксацию водопада/дома по координатам, которых в каноне нет.
5. **Авторство:** не изменять рукопись, не утверждать названия стран/городов и конкретные топонимы, не объявлять новый регион литературным каноном без решения автора.

## Следующий инженерный шаг

Распаковать и проверить **уже найденные** A8/A10/A12 (сетки, переменные, CRS, хэши, привязка PNG) и определить, какая геометрия должна быть сохранена при региональной детализации; только при невозможности использовать их явно выбрать режим «новая интерпретация авторского региона»; создать внешний World Profile с годом/масштабом/необходимыми ограничениями; определить масштаб двух связанных карт (планетарная макрокарта и детальная долина); получить **трёхрегиональный рельеф/гидрографию** для визуального выбора. Затем спроектировать не-земной opt-in land-cover profile.

Привязка к текущему Core — **внешняя и добровольная**, этот файл не меняет stage/contract. Файлы в examples/world-fixtures — не DomainSpec и не валидные входные request.json.


## Машинная проверка архивов A8/A12 — 15.11.2026

[Отдельный QA-отчёт](../reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md) подтверждает реальные NumPy-массивы и проблему осей: A8 lat **descending** (север → юг), A12 lat **ascending** (юг → север). При одинаковой долготе сетки и ровно одном реверсе широты A8 elevation/land идентичны A12. 0.3° → масштаб около 25–37 км здесь, поэтому район рассказа не разрешает водопад/мост/дорогу как отдельную геометрию. Данные A12 локально прочитаны, но остаются внешними рабочими моделями, не принятым DomainData.


**А10/А11 дополнительно верифицированы:** А10 задаёт эмпирический сезонный водный баланс (в том числе Q, сток, потенциальные сезонные/постоянные реки); A11 — сценарную чувствительность переноса влаги, а **не проверенную физическую глобальную циркуляцию**. A10/A11/A12 идут юг→север, A8 север→юг. Полное описание и SHA: [аудит источников](../reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md).


## P2-A child terrain evidence (not canon)

Three private-source original planet areas A/B/C were modeled at 230×230 km on new 1-km grids. The original model DEM macro stations have been preserved exactly (63/49/49 points respectively). The child valleys and hills between them are NEW procedural interpretations; the old A8 D8 rivers and author-proposed mansion/night stop/town/crossing have not yet been converted into connected local MFD geography. The source-derived PNG comparisons remain private in this ChatGPT conversation. [Method](planetary-child-terrain.md).


## P2-B1 source-grounded child drainage (NOT accepted rivers)

After P2-A terrain, provisional Core-style 1km MFD was calculated over the three private A/B/C working-model areas. A8 D8 macro river edges are only orange comparison lines. Large virtual fills in B/C (up to ~88.5m and ~60m) imply unresolved lake/outlet handling. Locally generated water area is conserved, but the crop does not know upstream contributions from outside. This is **not an approved river network or a placed waterfall/ford**. [Technical and visual audit](../reviews/p2-b-child-mfd-reference-audit-2026-11-16.md).


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.


### P2-B2.4 (2026-11-20): old A8 macro river exits vs CONNECTED CHILD Core MFD dominant channels — DRAFT #103

- New read-only external script scripts/compare_planetary_child_mfd_outlets_v02.py: directionally **INSIDE→OUTSIDE** old major A8 D8 links (distinct from earlier inlet provenance), accepted Core Priority Flood+MFD, Core dominant-channel area+terrain-aware initiation, positive-fraction adjoining channel edges traced to actual region boundary, and explicitly NONPHYSICAL jumps across geometrical lake proxy supernodes. Generates georeferenced-local-km masks/edge pairs + three-panel diagnostic PNG and manifest. This is NOT accepted Core RiverNetwork, physical water Q or proof of perennial lakes.
- Thresholds `stream_threshold_km2=30` and `matching_tolerance_km=30` are editable **demo** parameters, not immutable Earth/world rules. Matches only same boundary side within spatial tolerance, unique one-to-one, always tagged GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED; unmatched stays UNMATCHED, no terrain correction or A8→MFD forced merge.
- [Operator evidence](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-mfd-outlet-review.md). [GREEN synthetic map](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499) with 49 focused tests: toy A8 has **1 major macro exit**, new connected MFD cartoon has **19 terminal edge cells**, **1 same-side within-30km purely spatial match**. The discrepancy is exposed, not patched. Old source A/B/C major EXITS known A=1, B=2, C=0, but **actual real private A/B/C CHILD MFD outlet matching was NOT yet run**, do not invent distances.
- The CI demonstration is SYNTHETIC ONLY; original private literary planet A8/A12 and derived real maps have not been committed to public GitHub. Full pytest is to be confirmed at FINAL branch SHA; earlier source version had 554 tests passed. PR #103 DRAFT/UNMERGED. PR #99–101 remain drafts. dev/0.2 and frozen release untouched.
- **NEXT P2-B2.5**: run real private A/B/C matching, then specifically condition coarse river corridors and watershed boundaries on real source at 1km without changing original macro-station heights; recompute MFD and compare before/after. Land cover P3 and ImageGen only after credible river continuity.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.
