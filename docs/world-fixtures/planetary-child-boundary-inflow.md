# P2-B2.2 — источник A8 и явно задаваемые входящие водосборы на MFD

**Экспериментальная внешняя реализация** [draft #103](https://github.com/MysterioCrypto/domain_generator/pull/103). Важно: это диаграмма маршрутизации ПЛОЩАДИ, а не вычисление реального Q, не утверждённые реки и не настоящие озёра. [Мотивировка и результаты](../reviews/p2-b2-2-boundary-inflow-lake-mfd-audit-2026-11-20.md).

## Предыдущие шаги

1. Приватно получить оригинальную [макрогеографию A8/A12](planetary-geogrid-adapter.md) через export_planetary_macro_region_v02.py. Должны быть source_river_mask_D8, source_catchment_km2_D8 и local_downstream_index с корректной ориентацией по широте.
2. [Подробный рельеф P2-A](planetary-child-terrain.md) через condition_planetary_child_terrain_v02.py с тем же центром/планетой/годом. Здесь необходимы child-terrain-generated.npz и manifest.json.
3. Опционально [геометрическая диагностика озёр P2-B2.1](planetary-child-lake-review.md) для понимания потенциальных глубоких котловин.

## Без внешнего ввода

Команда из корня репозитория:

    python scripts/condition_planetary_child_boundary_mfd_v02.py \
      --child-npz /private/child-A/child-terrain-generated.npz \
      --child-manifest /private/child-A/manifest.json \
      --macro-npz /private/source-A/macro-region-source.npz \
      --lake-min-area-km2 16 --lake-min-depth-m 10 \
      --output /private/child-A/boundary-no-external

Пороги 16/10 — только выбранный **геометрический** обзор; не утверждённая гидрология планеты. Локальная площадь учитывается Core MFD; старые входы A8 помечаются как кандидаты, но **+0 км² автоматически**.

## С явно гипотетическим внешним вводом

Сначала откройте отчёт manifest.json в boundary-no-external и найдите требуемый boundary_source_A8_D8_candidates[].key. Это зарегистрированный уникальный старый направленный D8 сегмент; не придумывайте строковый ключ.

Отдельный JSON-файл эксперимента (ЗАПОЛНЯТЬ только после ознакомления с зарегистрированными ключами; значение площади — явно модельная гипотеза, а НЕ копия A8 catchment):

    {
      "schema": "P2_B2_2_EXPLICIT_A8_INFLOW_SCENARIO",
      "inflows": [
        {
          "source_link_key": "PUT_THE_OBSERVED_A8_LINK_KEY_HERE",
          "external_area_km2": 250.0,
          "area_semantics": "EXTERNAL_ONLY_AREA_EXCLUDING_CHILD",
          "operator_note": "Research assumption: hypothetical distinct upstream area, not author canon"
        }
      ]
    }

Пример с +250 км² — строго синтетический QA, не реальная величина для Д’Акхара. Невалидные/повторные ключи, отрицательные значения или попытка использовать полную площадь A8 вместо внешней будут отвергнуты либо помечены как **НЕ верифицированные**.

    python scripts/condition_planetary_child_boundary_mfd_v02.py \
      --child-npz /private/child-A/child-terrain-generated.npz \
      --child-manifest /private/child-A/manifest.json \
      --macro-npz /private/source-A/macro-region-source.npz \
      --inflows-json /private/child-A/hypothetical-external.json \
      --lake-min-area-km2 16 --lake-min-depth-m 10 \
      --output /private/child-A/boundary-inflow-hypothesis

Вывод: boundary-routing-diagnostic.npz с local MFD area и отдельным числовым кодом **геометрических** озёрных supernodes; manifest.json с граничным ledger; boundary-routing-preview.png с исходной высотой, MFD площадью и старой речной геометрией A8 (оранжевые точки), без подмены локальной русловой сети.

## Верификация, ограничения и дальнейшая цель

[Зелёный синтетический Actions + две сравнительные карты](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283925), в архиве non-earth-geogrid-synthetic-demo. 35 специальных тестов, в том числе прямое сравнение с НЕИЗМЕНЁННЫМ Core на малой котловине; [весь pytest 540 passed](https://github.com/MysterioCrypto/domain_generator/actions/runs/44758283877).

- A8 старый грубый D8, новая маршрутизация — MFD. Они **не могут считаться одной утверждённой сетью**.
- Геометрический кандидат lake supernode — НЕ доказанное постоянное озеро.
- При неразрешённой геометрии перелива отчёт маркирует UNRESOLVED; маршрут без lakes в этом случае тоже остаётся диагностическим.
- Ввод area_semantics EXTERNAL_ONLY… пока контролируется семантическим подтверждением оператора, но **не физически проверяется** глобальным графом. Его автоматическая верификация — следующий P2-B2.3.
- Не публикуйте оригинальные приватные ZIP, исходный массив планеты или производные настоящие карты в публичный GitHub без разрешения автора.

**Предел этапа:** нет физического Q м³/с, осадков, грунтовых вод и изображения постоянных рек. Не тратить время на глобальное научное моделирование ради выразительных НРИ карт, но и не рисовать старые реки поверх несвязанного рельефа.


### P2-B2.3 · 2026-11-20: global A8 FIRST-ENTRY source partition (DRAFT #103)

- The original PRIVATE global A8 600×1200 D8 graph (not a crop) was inspected. New external script scripts/trace_a8_external_first_entry_v02.py computes the partition of **each original EXTERIOR LAND SOURCE cell** by the FIRST directed downstream entry into each 230km child rectangle. This prevents source-area duplication on exit/re-entry: only own new exterior source area is allocated to later entries. Full graph must be acyclic; macro/crop links must match exact global A8 lat/lon/receiver indices; A8 source cell area uses world radius and cos(latitude), NOT Earth constants.
- Original privately checked working model A/B/C: all directed A8 entry LINKS **23 / 12 / 5**; subset tagged old major river mask **1 / 0 / 0**. All-source EXTERIOR first-entry areas A ≈297,336.828km² / B ≈87,705.114km² / C ≈11,515.098km². A's ONE major river has A8 external first-entry area ≈**86,106.657km²**, matching old total source catchment ≈86,106.65625km² within rounding. No inside-upstream reentry in these specific scenes; a synthetic exit→reentry case is tested explicitly.
- A8 first-entry provenance is NOT physically verified 1km CHILD MFD drainage, river discharge Q or author canon. **No auto injection into child MFD.** Old D8 river_mask ignores numerous smaller old macro incoming links; B/C "zero major" DOES NOT mean no rivers. Private source ZIPs and actual region imagery are NOT committed to public GitHub.
- [P2-B2.3 audit](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md) and [CLI](https://github.com/MysterioCrypto/domain_generator/blob/feature/v0.2-planetary-geogrid-source-adapter/docs/world-fixtures/planetary-a8-first-entry-provenance.md). Synthetic tests cover reentry, unequal latitude row areas, cycle and source mismatch; current CI status must be confirmed at latest final SHA.
- **NEXT P2-B2.4:** match source A8 MACRO outlets with actual CHILD MFD edge-terminal geography and connected river lines, then explicit world-specific hydrologic semantics; neither A8 D8 nor newly rendered detail is authoritative. PR #103 remains DRAFT/UNMERGED; #99–101 drafts and dev/0.2/frozen release unchanged.


## New P2-B2.3 — проверенная площадь первичного входа по ORIGINAL A8

[Приватный глобальный аудит](planetary-a8-first-entry-provenance.md) проверяет именно исходные глобальные A8 клетки, а не просто старый scalar catchment. Он не переносит найденную площадь в новую MFD автоматически: это лишь отдельная степень достоверности **исторической** географической модели. Даже проверенные 86,1 тыс. км² для главного входа A не превращаются сами собой в реальные Q или в правильный дочерний речной коридор. Далее требуется P2-B2.4.
