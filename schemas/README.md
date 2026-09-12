# Снимки JSON Schema — Core 0.1

Этот каталог содержит сгенерированные снимки JSON Schema для шести корневых сериализуемых контрактов:

- `DomainSpec`
- `GenerationPlan`
- `LayoutCandidate`
- `ValidationResult`
- `GenerationConfig`
- `DomainData`

Перегенерировать их можно командой:

```bash
python -m domain_generator.schema_export
```

Файлы используют JSON Schema Draft 2020-12 и генерируются из моделей Pydantic v2 с включёнными aliases. Снимки записываются в компактном детерминированном JSON, чтобы diff отражал изменения схемы, а не форматирования.

Важная граница: JSON Schema описывает только структурные ограничения, которые умеет выразить генератор схем Pydantic. Межполевые проверки, реализованные через `model_validator` — например точная делимость grid, согласованное агрегированное состояние validation или требования к canonical fields в `DomainData` — по-прежнему требуют проверки Python-моделью контракта/Core. Поэтому committed snapshots являются схемами обмена и документации, а не заменой валидации Core.
