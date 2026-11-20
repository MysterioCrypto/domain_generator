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
