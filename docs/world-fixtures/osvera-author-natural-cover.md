# Осве́ра / P3-MVP: авторский природный покров

**Не канон:** внешний картографический кандидат, отдельный от Core, не доказанные настоящие леса и болота. [Почему и что проверено](../reviews/p3-mvp-osvera-natural-cover-2026-11-21.md).

Исходный приватный архив A12 содержит файл planet_A12/A12_biome_fields.npz с lat, lon, land и четырьмя сценарными biome_* полями, stable4, wetland_candidate. A12 ось lat идёт ЮГ→СЕВЕР; child DEM — север первой строкой. Скрипт сверяет координаты и не смешивает их по индексам. Сценарная A12 — авторская рабочая модель, не окончательная география мира.

Из checkout PR #103 локально, НИЧЕГО из исходных ZIP не загружая в GitHub:

~~~bash
python scripts/derive_author_natural_cover_v02.py \
  --child-npz /private/child-A/child-terrain-generated.npz \
  --child-manifest /private/child-A/manifest.json \
  --eco-npz /private/A12_biome_fields.npz \
  --profile-json examples/world-fixtures/osvera-working-cover-profile.json \
  --output /private/child-A/cover-candidate
python scripts/render_author_region_atlas_v02.py \
  --child-npz /private/child-A/child-terrain-generated.npz \
  --child-manifest /private/child-A/manifest.json \
  --ledger-json examples/world-fixtures/osvera-first-arc-author-ledger.json \
  --cover-npz /private/child-A/cover-candidate/natural-cover-candidates.npz \
  --cover-manifest /private/child-A/cover-candidate/manifest.json \
  --output /private/child-A/author-atlas-with-cover
~~~

Первая команда создаёт natural-cover-candidates.npz, manifest.json, cover-before-after.png. Вторая — один авторский лист, audit JSON, список известных мест/отношений. Классы 1–5: возможный лес, открытая поверхность, возможные каменистые склоны, **кандидат влажной низины (НЕ вода)**, редкая растительность. Профиль параметров можно менять, но он не становится нормой для всех неземных миров.

Прямой [синтетический визуальный workflow](https://github.com/MysterioCrypto/domain_generator/actions/workflows/author-region-atlas-v02.yml) — только для CI, НЕ карта настоящей Осве́ры. Не подменять модельные леса утверждёнными, не расставлять сюжетные места/дороги без авторского положения, не превращать расстояние по прямой во время путешествия.
