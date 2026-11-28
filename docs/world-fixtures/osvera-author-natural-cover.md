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


## P3 exact-checkout: одна сборка от A8/A12 макросетки до карты

Новая команда связывает существующие P2-A, P3 и atlas без независимой повторной реализации. Принимает экспорт P1 (macro-region-source.npz и manifest.json) и ОРИГИНАЛЬНЫЙ A12_biome_fields.npz с глобальными lat/lon/elevation_m/land и сценарными полями. Проверяет точное совпадение координат, высот и маски суши в исходных макроузлах (учитывает противоположную ориентацию широт). При несовпадении останавливается, не выдумывая пространственное соответствие. Центр региона берётся из ledger и должен совпасть с P1 manifest.

Из корня ТОГО ЖЕ checkout PR #103, не загружая приватные исходники в GitHub:

~~~bash
python -m scripts.build_author_atlas_v02 \
  --macro-npz /private/source-A/macro-region-source.npz \
  --macro-manifest /private/source-A/manifest.json \
  --eco-npz /private/A12_biome_fields.npz \
  --ledger-json examples/world-fixtures/osvera-first-arc-author-ledger.json \
  --profile-json examples/world-fixtures/osvera-working-cover-profile.json \
  --half-width-km 115 --half-height-km 115 \
  --spacing-km 1 --seed 1406 --relief-strength 2 \
  --output /private/osvera-region-A-exact-p3
~~~

В выходной директории: child/child-terrain-generated.npz и manifest, cover/natural-cover-candidates.npz и manifest, cover/cover-before-after.png, atlas/author-atlas-sheet.png, atlas/author-atlas-audit.json, atlas/author-atlas-notes.md, общий build-audit.json. Общий аудит содержит SHA-256 пяти входных файлов, число исходных высотных опор, максимальную ошибку, доли классов природного покрова и число неизвестных сюжетных мест/маршрутов. Хеши фиксируют воспроизводимость исходных байт, но не научную достоверность. Выходная директория должна быть пустой.

CI проверяет цепочку на ИСКУССТВЕННОЙ планете, несовпадающие высоты/сушу/координаты, ориентации A12, неизменность входов и отсутствие выдуманных маршрутов. Публичные Actions НЕ содержат приватные A8/A12. Следующий продуктовый шаг — выполнить эту же команду на приватном исходнике региона A, сверить аудит и показать ОДИН авторский лист для визуального решения. До этого текущие приватные доли классов нельзя выдавать за точный результат нового конвейера. PR #103 остаётся DRAFT/UNMERGED, Core и freeze без изменений.


## P3.2 — one command directly from ORIGINAL private A8/A12 ZIP

**Preferred private operator route** from the same PR #103 checkout: no manual extraction, preliminary macro-NPZ export, or P1 command needed. P1 whole-world archive validation checks the A8/A12 axes, DEM and land identity before any rendering. Original uncropped A12 provides the P3 scenario fields. An automatic one-source-station *interpolation halo* expands the P1 source crop, NOT the requested 230×230 km child map. Radius and planetary calendar remain explicit.

~~~bash
python -m scripts.build_author_atlas_v02 \
  --a8-zip /private/original-A8.zip \
  --a12-zip /private/original-A12.zip \
  --planet-radius-km 7008.1 --planet-year-earth-days 202.755 \
  --ledger-json examples/world-fixtures/osvera-first-arc-author-ledger.json \
  --profile-json examples/world-fixtures/osvera-working-cover-profile.json \
  --half-width-km 115 --half-height-km 115 --spacing-km 1 \
  --seed 1406 --relief-strength 2 \
  --output /private/osvera-region-A-exact-p3
~~~

Optional SHA-256 pins: --expected-a8-sha256 / --expected-a12-sha256 reject wrong archives before building. Original ZIP bytes are not copied; only private derived source/macro-region-source.npz + source/manifest.json are written to the user-chosen private output. build-audit.json reports four input SHA-256 values and input_mode=ORIGINAL_PRIVATE_A8_A12_ZIP. The former 5-input exported-NPZ mode remains available; neither mode modifies its inputs. Public tests use SYNTHETIC ZIPs, never the owner's originals.

**Unfinished acceptance:** run this command on the real private ZIPs, inspect audit and one atlas sheet. No real-world author or Core hydro acceptance is implied.
