# P2-B2.4 — сравнение выходов A8 и связных трасс дочернего MFD

**Статус:** внешний картографический и численный аудит, [draft PR #103](https://github.com/MysterioCrypto/domain_generator/pull/103), НЕ утверждённые литературные реки и НЕ замена норм Core. [Мотивировка и контрольные результаты](../reviews/p2-b2-4-macro-exits-vs-child-mfd-2026-11-20.md).

## Что требуется

Предварительно приватно запустить [макрогеографический источник](planetary-geogrid-adapter.md) и [моделирование детального рельефа](planetary-child-terrain.md). Для нового этапа достаточно созданных macro-region-source.npz, child-terrain-generated.npz и child manifest.json; глобальная исходная A8 ZIP нужна лишь для отдельного [аудита площадей первого входа](planetary-a8-first-entry-provenance.md).

Из корня репозитория:

    python scripts/compare_planetary_child_mfd_outlets_v02.py \
      --macro-npz /private/source-A/macro-region-source.npz \
      --child-npz /private/child-A/child-terrain-generated.npz \
      --child-manifest /private/child-A/manifest.json \
      --stream-threshold-km2 30 \
      --matching-tolerance-km 30 \
      --output /private/child-A/macro-vs-mfd

**Пороги 30 км² и 30 км** — лишь редактируемые демонстрационные параметры. Первое число определяет плотность локального речного скелета по принятому Core dominant-channel area и terrain-aware initiation; второе — максимально допустимую пространственную близость старого выхода A8 и новой граничной точки MFD на **одной стороне** карты. Эти значения не универсальны для других миров и не фиксируют авторский канон.

## Что выйдет

- macro-vs-child-outlets.png: отдельно поле площади MFD, связные локальные каналы, выходы старых крупных A8 рек (ромбы) и терминалы дочерних MFD каналов (кружки). Возможные геометрические озёрные узлы показаны отдельно от собственно речных линий.
- connected-MFD-channel-reference.npz: маска обычных местных каналов, downstream индексы, положительные смежные Core MFD связи и **отдельные не-физические** переходы через candidate lake proxy. Полная суммарная площадь в км² — не расход Q м³/с.
- manifest.json: все ориентированные старые A8 выходы, найденные локальные терминалы, one-to-one spatial matches и UNMATCHED, отсутствие автоматических внешних притоков, допущения и неопределённости.

Видимый в PNG совпадающий ромб и кружок означает **только геометрическую близость**, не совпадение водосбора, не годовой расход и не утверждённую реку. При расхождении алгоритм намеренно НЕ подправляет рельеф автоматически.

## Проверка в GitHub Actions

[Графический контрольный запуск](https://github.com/MysterioCrypto/domain_generator/actions/workflows/non-earth-geogrid-source-adapter-v02.yml): артефакт non-earth-geogrid-synthetic-demo, раздел macro-vs-MFD-outlets. Он содержит только небольшую **синтетическую** планету, никогда не исходные ZIP литературного мира. Тесты синтетической связности, правильных downstream направлений, отказа от фальшивых гидрологических совпадений находятся в tests/test_planetary_child_mfd_outlet_alignment_v02.py.

Для A/B/C исходные большие D8 выходы пока известны из старой модели, но сам P2-B2.4 MFD **не выполнялся на приватных реальных детализированных A/B/C**. Не утверждать чисел гидрологического сопоставления для литературных территорий без повторного запуска.

## Следующая итерация

P2-B2.5: source-conditioned работа с ключевыми водосборами и речными коридорами на реальных A/B/C, с контролем сохранения исходных высот макроузлов и повторным Core MFD-routing. Нельзя произвольно протягивать речные линии по поверхности или подменять MFD исходной D8 сетью. До этого этапа итоговые карты остаются диагностикой.



### P2-B2.5, 2026-11-20 — REAL PRIVATE A/B/C preliminary MFD check and NEGATIVE river-carving result

- Local PRIVATE original A8/A12 ZIPs used for independent 231×231 child DEM and Core-like Freeman MFD dominant-channel reconstruction **WITHOUT full current PR lake-supernode routing** (not byte-exact PR #103). Old major A8 exits vs same-side near new modeled terminals (30km): A=1 old exit / 1 near (0.028km), B=2 old / 2 near (1.078 and 3.682km), C=0 old / no verifiable exit matches. New independent channel-edge terminal counts 36/40/63. Source elevation anchors are mathematically fixed; PNG/JSON kept PRIVATELY in ChatGPT, never published to GitHub. This is *preliminary evidence only*, not a production PR reproducibility claim.
- New opt-in external `scripts/propose_planetary_river_corridor_v02.py` performs bounded negative excavation beside old A8 coarse river segments, preserving every original macro DEM station analytically, child boundary cells, land/sea sign; reevaluates after with actual connected Core MFD. It **NEVER automatically updates Core/child terrain**, and is marked NONCANONICAL and NOT_SEAMLESS across changing crop origins. A separate private independent A/B/C trial at -15m cap: A exit worsened from 0.028km to ~11.972km; B did not improve; C no old major exit to judge. **DO NOT APPLY THIS TRIAL** to real planet as-is; counterexample to global source-carving assumption.
- [Operator negative result](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-5-real-region-corridor-negative-checkpoint-2026-11-20.md) · [optional CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-river-corridor-trial.md) · [synthetic GREEN 57 focused tests](https://github.com/MysterioCrypto/domain_generator/actions/runs/44800639967). Need check full pytest on final documentation SHA.
- **NEXT P2-B2.6:** compare true current Core lake-supernode routing on real B/C vs independent no-lake channels; diagnose 80m/55m virtual Priority Flood fill, verify basin shape/spills and decide whether topography needs targeted changes or world-defined lake/water rules. No false Earthlike norms; do not overbuild physics. PR #103 DRAFT/UNMERGED, #99–101 drafts, dev/0.2 and release/0.2-prealpha unchanged.
