# НАЧАТЬ ЗДЕСЬ — domain_generator

**Единая человеческая точка входа.** В случае потери контекста откройте этот файл, а не историю чатов и не main. Принятая линия: [dev/0.2](https://github.com/MysterioCrypto/domain_generator/tree/dev/0.2). Замороженный срез: [release/0.2-prealpha](https://github.com/MysterioCrypto/domain_generator/tree/release/0.2-prealpha).

## Назначение

Параметрически воспроизводимая география **преимущественно неземных миров** для настольных игр и литературных произведений. Процедурный фундамент даёт рельеф, климат, водосборы, воды, природный покров и заданные объекты. Затем собирается вид сверху — **между спутниковой картой и художественной иллюстрацией**. ImageGen может улучшать фактуру, но не должен быть единственным автором географии.

Земная классификация Кёппена–Гейгера и земные названия биомов — только **явно включаемые профили**, не закон для всех миров. Год, орбита, широты, единицы осадков и экология — свойства конкретного мира или адаптера. Магия не вмешивается скрытно в физику.

## Три главные ссылки

- [Product roadmap: что сделано, что делать](docs/PRODUCT_ROADMAP.md)
- [Первый боевой источник: Д’Акхар](docs/world-fixtures/dakhar-first-arc.md)
- [Первый JSON-реестр реальных исходных ограничений](examples/world-fixtures/dakhar-first-arc-anchors.json) — это **не** готовый DomainSpec и **не** утверждённые координаты.

## Где что сейчас (15 ноября 2026)

| Линия | Проверенный статус | Ссылка |
| --- | --- | --- |
| Принятый Core 0.2: Terrain/Hydrology, C1–C3, опциональные C4/C5/H12 | В dev/0.2, базовая процедурная система | [Код](https://github.com/MysterioCrypto/domain_generator/tree/dev/0.2) |
| H13 валовое количество осадков, направленных по MFD | PR #99 **draft/open/unmerged**, не фактический расход рек | [#99](https://github.com/MysterioCrypto/domain_generator/pull/99) |
| Эксперименты мягкости C2 | PR #100 **draft/open/unmerged**; параметр расстояния уже редактируется | [#100](https://github.com/MysterioCrypto/domain_generator/pull/100) |
| Совмещённые PNG-слои, поселения и художественные палитры | PR #101 **draft/open/unmerged**, не настоящий ImageGen | [#101](https://github.com/MysterioCrypto/domain_generator/pull/101) |
| Художественный demo-атлас | Готов в draft #101, но **не замещает** недостающий land cover | [GREEN Actions: два архива PNG](https://github.com/MysterioCrypto/domain_generator/actions/runs/43735595681) |
| Навигация и source-fixture Д’Акхара | Документационная ветка: не меняет runtime | Эта страница |

**Не считать draft PR частью принятого dev/0.2.** Не сливать #99–101 только потому, что тесты зелёные. Main не является текущей линией. Переезд в будущий чистый репозиторий — только позднее и по отдельной инструкции пользователя. Не удалять старые ветки и релизы.

## Актуальные шаги

1. Сверить реальную литературную географию и проверить **найденные** A8/A10/A12 ZIP и геопривязанную подложку (либо явно выбрать новую модель без ложного обещания точного воспроизведения прежней).
2. Проверить **три действительно разных** географических региона с рельефом/реками/озёрами/побережьем, а не три климата на одном seed.
3. Ввести **опциональные** классы природного покрова: лесоподобные сообщества, луга, скалы и т.п. из конкретного world profile. Сейчас C3 — индекс потенциала, а не карта лесов.
4. Построить географически точную подложку сверху с масштабом/масками/геометрией; честно сохранять пределы исходного разрешения.
5. Только затем провести реальный ImageGen-проход и восстановить точные реки, озёра, объекты и подписи из отдельных слоёв.

**Выходной контроль:** один GREEN GitHub Actions с PNG-картами, которые пользователь действительно может оценить. Внутренние вычисления принимаются автоматическими проверками; новые научные модели делать только при существенной видимой пользе.

## Техническое восстановление

[PROJECT.md](PROJECT.md) → [docs/CONTEXT.md](docs/CONTEXT.md) → [docs/PROGRESS.md](docs/PROGRESS.md) → [docs/architecture.md](docs/architecture.md) → принятые docs/design. В длинных канонических файлах встречаются исторические checkpoint: их не выдавать за текущий статус без проверки реальных GitHub HEAD/PR/CI. Замороженный релиз не менять.


**Уточнение о доступности:** архивы A1–A11 и A12, а также PNG-атлас действительно находятся в Drive! Их нашёл **прямой просмотр папок**; поисковый API ошибочно возвращал пустой неполный список. Это не значит, что ZIP уже распакованы или их геометрия импортирована. См. ссылки и статусы в [D’Акхар fixture](docs/world-fixtures/dakhar-first-arc.md).


**P1 — машинная проверка источника:** A8 и A12 ZIP уже локально открыты и проверены: SHA-256 соответствуют архивному README, сетки 600×1200, у A8 строка 0 — **север**, у A12 строка 0 — **юг**. После разворота A8 по широте исходные elevation/land совпадают с A12 **побитово**. Архивы A10/A11 только обнаружены, их содержимое отдельно пока не проверено. В Core ничего не импортировано. См. [отчёт проверки](docs/reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md).


**P1 — A10/A11 также проверены на уровне бинарных источников:** обе ZIP с корректным SHA-256 и CRC; NPZ массивы прочитаны, A10/Q совпадает с копией в A12_inputs. Геопривязка юг→север у A10/A11/A12 против A8 север→юг. A11 — только исследование чувствительности, не утверждённая атмосферная модель. Ссылки в [отчёте](docs/reviews/dakhar-a8-a12-source-alignment-audit-2026-11-15.md).


## P1 planetary macro-geogrid adapter — 2026-11-15, DRAFT #103

- User's non-Earth source A8/A10/A11/A12 archives are verified (SHA/CRC, A8 north-first vs A10/A11/A12 south-first) and kept PRIVATE. Source A8 global D8 is an older research hydrology, not Core 0.2 accepted MFD.
- On an isolated DRAFT [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), external-only script scripts/export_planetary_macro_region_v02.py reads paths of original ZIPs, validates exact A8/A12 shared land/DEM, accepts user-specified planetary radius/year and local km source crop, remaps BOTH endpoints of A8 global flattened D8 downstream indices, and flags rivers exiting crop. It emits source NPZ+manifest+PNG, deliberately NOT DomainData and NOT fake local 1-km elevation.
- Synthetic workflow [GREEN](https://github.com/MysterioCrypto/domain_generator/actions/runs/43742308913) passes 4 targeted tests and writes a demo artifact. No private source ZIP/PNG was committed or uploaded to Actions.
- [CLI instructions and explicit boundaries](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Next meaningful work is source-constrained finer regional terrain and new MFD river generation, followed by non-Earth profile-based land cover; not further parchment filters or full planetary climate science.
- This is a parallel draft branch. PR #99 H13, #100 C2 tests, #101 atlas composer remain DRAFT/UNMERGED. Frozen release c69c1af010a085fb80d248af703a77471fc6c9d7 remains unchanged.

**Новый проверяемый инструмент (ещё не объединён):** [внешний планетарный геоадаптер](https://github.com/MysterioCrypto/domain_generator/pull/103) и [инструкция](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-geogrid-adapter.md). Он корректно вырезает источник, не подменяя старые D8 реки принятой Core MFD сетью.


**P2-A — новый рельеф регионов (draft PR #103):** из найденных исходных A8/A12 созданы модели A/B/C с шагом 1 км и привязкой к исходным высотам. Убраны прямоугольные следы исходной сетки; исходные узлы неизменны. [Метод и границы достоверности](docs/world-fixtures/planetary-child-terrain.md). На GitHub Actions выкладываются только синтетические демонстрации; три реальные карты показываются приватно в чате. **Новая гидрология ещё не рассчитана.**


**P2-B1 — предварительная речная диагностика (16.11.2026):** на отдельном draft [PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103) реализован новый MFD-сток поверх дочернего 1-км рельефа. [Зелёный Actions c PNG](https://github.com/MysterioCrypto/domain_generator/actions/runs/43805052775) (только синтетический пример). [На реальных A/B/C](docs/reviews/p2-b-child-mfd-reference-audit-2026-11-16.md) выявлены глубокие понижения B/C: это блокер для достоверных рек, а не эстетическая проблема. P2-B2: привязка макровыходов, внешний приток и принятые озёрные supernodes. **Реки ещё не приняты как часть карты**.


**Текущий P2-B2.1** — диагностика возможных озёрных бассейнов на детальном рельефе: [отчёт](docs/reviews/p2-b2-1-child-lake-basin-operator-checkpoint-2026-11-20.md), [настраиваемый CLI](docs/world-fixtures/planetary-child-lake-review.md) и [синтетический Actions](https://github.com/MysterioCrypto/domain_generator/actions/runs/44748762996). Пороги 4 км²/2 м или 16 км²/10 м — примеры отбора, а не утверждённая климатология; Core не изменён, #103 остаётся черновиком. Следующий этап — внешние граничные притоки и связанные озёрные переливы P2-B2.2.


### P2-B2.2 — explicit cross-scale river boundary area (2026-11-20, draft PR #103)

- External scripts/condition_planetary_child_boundary_mfd_v02.py: identify directionally INCOMING original A8 D8 macro-river links at a 230km child box; preserve source catchment as UNSAFE_HINT only. With NO explicit scenario, inject **zero** external km2. With a keyed, operator-annotated, positive EXTERNAL_ONLY scenario, run new Core-compatible O((N+E)logN) MFD + geometric lake-supernode area propagation and enforce area-conservation ledger. It is **NOT discharge Q**, a world water balance, actual lake occupancy, an accepted child vector river network or an automatic A8-to-MFD merger. Does not mutate normative Core.
- [Operator audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md) · [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-boundary-inflow.md). [Synthetic GREEN preview and ledger](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925): 35 focused tests, two contrasting maps, no private source uploaded. [Full pytest GREEN 540](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877) on algorithm SHA 35163cd7b6f8c3c9c8c74ea3a5ec24c2aa603dc3; check final documentation SHA again.
- Original PRIVATE A8/A12 data were screened locally for 230×230km A/B/C: OLD D8 crossing counts A **1 IN / 1 OUT**, B **0 IN / 2 OUT**, C **0/0**. A source D8 entry has upstream catchment proxy **86,106.66 km²**, but this is **NOT** verified external-only area and MUST NOT be injected unexamined. No old-source data/real-derived maps in public GitHub.
- **NEXT P2-B2.3:** compute true external-only provenance using original global D8 with re-entry detection, then compare macro basin exits to new actual connected MFD channels and qualify real lake occupancy per world-specific water profile. PR #103 DRAFT/UNMERGED, #99–101 DRAFT/UNMERGED; dev/0.2 and frozen release unchanged.

**Текущая техническая точка P2-B2.2:** [инструкция](docs/world-fixtures/planetary-child-boundary-inflow.md) и [итоговый обзор](docs/reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md). На исходной планете A/B/C: 1/1, 0/2, 0/0 старых пересечений рек (вход/выход). Внешняя площадь не добавляется без явного сценария. Это **ещё не физический расход** и не карта связных локальных рек; следующий шаг P2-B2.3.


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.

**Следующий закрытый исследовательский блок P2-B2.3:** [отчёт о глобальной внешней площади первичного входа A8](docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md), [как запускать приватно](docs/world-fixtures/planetary-a8-first-entry-provenance.md). Макровходы A/B/C **23/12/5**, в том числе большие A8 1/0/0; для главного входа A внешний источник ≈86 106,657 км² по A8. Эти данные **не** являются автоматически внесённым MFD стоком или расходом. Следующее P2-B2.4 — связные локальные русла и проверка выходов.


### P2-B2.4 (2026-11-20): old A8 macro river exits vs CONNECTED CHILD Core MFD dominant channels — DRAFT #103

- New read-only external script scripts/compare_planetary_child_mfd_outlets_v02.py: directionally **INSIDE→OUTSIDE** old major A8 D8 links (distinct from earlier inlet provenance), accepted Core Priority Flood+MFD, Core dominant-channel area+terrain-aware initiation, positive-fraction adjoining channel edges traced to actual region boundary, and explicitly NONPHYSICAL jumps across geometrical lake proxy supernodes. Generates georeferenced-local-km masks/edge pairs + three-panel diagnostic PNG and manifest. This is NOT accepted Core RiverNetwork, physical water Q or proof of perennial lakes.
- Thresholds `stream_threshold_km2=30` and `matching_tolerance_km=30` are editable **demo** parameters, not immutable Earth/world rules. Matches only same boundary side within spatial tolerance, unique one-to-one, always tagged GEOMETRICALLY_NEAR_ONLY_NOT_SAME_WATERSHED; unmatched stays UNMATCHED, no terrain correction or A8→MFD forced merge.
- [Operator evidence](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-child-mfd-outlet-review.md). [GREEN synthetic map](https://github.com/MysterioCrypto/domain_generator/actions/runs/44797653499) with 49 focused tests: toy A8 has **1 major macro exit**, new connected MFD cartoon has **19 terminal edge cells**, **1 same-side within-30km purely spatial match**. The discrepancy is exposed, not patched. Old source A/B/C major EXITS known A=1, B=2, C=0, but **actual real private A/B/C CHILD MFD outlet matching was NOT yet run**, do not invent distances.
- The CI demonstration is SYNTHETIC ONLY; original private literary planet A8/A12 and derived real maps have not been committed to public GitHub. Full pytest is to be confirmed at FINAL branch SHA; earlier source version had 554 tests passed. PR #103 DRAFT/UNMERGED. PR #99–101 remain drafts. dev/0.2 and frozen release untouched.
- **NEXT P2-B2.5**: run real private A/B/C matching, then specifically condition coarse river corridors and watershed boundaries on real source at 1km without changing original macro-station heights; recompute MFD and compare before/after. Land cover P3 and ImageGen only after credible river continuity.

**Новая текущая диагностика P2-B2.4:** [сравнение старых A8 выходов с новыми связными MFD-трассами](docs/reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md), [CLI](docs/world-fixtures/planetary-child-mfd-outlet-review.md). Синтетическая карта (не Д’Акхар): 1 A8 крупный выход, 19 граничных MFD терминалов, 1 только геометрически близкая пара. Это ещё НЕ полноценная сеть рек. Следующий P2-B2.5 — запуск на настоящих A/B/C и ограниченное согласование макро-русел с рельефом.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.

**ТЕКУЩАЯ ИТЕРАЦИЯ P2-B2.5:** [отрицательный результат реального A/B/C](docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) и [необязательный source-preserving CLI](docs/world-fixtures/planetary-river-corridor-trial.md). Из независимого приватного теста видно, что принудительное вырезание коридора способно ухудшить крупные выходы; изменения НЕ приняты в Core. Следующий этап — проверка настоящих lake supernodes B/C вместо «прорезания» старых русел.
