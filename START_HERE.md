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
