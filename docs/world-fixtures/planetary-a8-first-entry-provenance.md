# P2-B2.3 — проверка ВНЕШНЕЙ части водосбора по глобальному A8

Этот внешний диагностический инструмент принимает пользовательский **полный original A8 ZIP** и проверяет геометрию входящих D8-связей до новой дочерней карты. См. [аудит и реальные результаты A/B/C](../reviews/p2-b2-3-global-a8-first-entry-2026-11-20.md).

## Входные данные

Получить original A8 ZIP в личном хранилище (не коммитить в публичный GitHub). Сначала выполнить [внешний экспорт макрорегиона](planetary-geogrid-adapter.md) и [создание дочернего рельефа](planetary-child-terrain.md). Нужны full A8 ZIP, macro-region-source.npz, child-terrain-generated.npz, child manifest.json.

```bash
python scripts/trace_a8_external_first_entry_v02.py \
  --global-a8 /private/planet_A8_prototype.zip \
  --macro-npz /private/source-A/macro-region-source.npz \
  --child-npz /private/child-A/child-terrain-generated.npz \
  --child-manifest /private/child-A/manifest.json \
  --output /private/child-A/a8-first-entry-audit
```

В `manifest.json` отражены **все** направленные входящие связи D8 и отдельно те, которые были классифицированы original `river_mask` как большие реки. Каждая `entries[]` хранит `source_link_key`, историческую полную площадь `old_A8_total_upstream_catchment_km2_UNSAFE_HINT` и независимую величину `A8_external_macro_land_source_area_km2_FIRST_ENTRY_ONLY`. Код восстанавливает личность звена в глобальной сетке, проверяет соответствие crop, исключает дважды учтённые orig source-клетки при повторном входе и проверяет отсутствие циклов в глобальном D8-графе.

Дополнительно формируется `a8-first-entry-preview-crop.npz` с минимальной вырезкой индексов происхождения для самостоятельной картографической проверки. **Полный оригинальный массив не копируется в публичный репозиторий.**

## Не путать с вводом воды в MFD

Результат является **доказанной топологией лишь старой A8**, а не реальным количеством воды, расходом Q, физически достоверным водосбором дочерней модели или законченными руслами. После отчёта **автоматически вводится 0 км²** в новую MFD: перенос любого географического источника в детальную сеть требует отдельного теста размещения и связности, а не копирования чисел.

Для ручного экспериментального сравнения без претензии на канон см. [предыдущий P2-B2.2 с внешними сценариями](planetary-child-boundary-inflow.md). Автоматическая передача значений из этого отчёта в P2-B2.2 пока **не реализована намеренно**.

**CI:** [source geogrid Actions](https://github.com/MysterioCrypto/domain_generator/actions/workflows/non-earth-geogrid-source-adapter-v02.yml), тесты синтетические, архивы литературного мира не загружаются. **Следующее P2-B2.4:** сверка крупных выходов A8 с терминалами новой MFD и создание географически согласованных, действительно связных русел.
