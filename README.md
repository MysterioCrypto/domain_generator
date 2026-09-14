# domain_generator

Детерминированное процедурное ядро для генерации ограниченных пространственных регионов мира или карты с управляемой случайностью.

`Domain` здесь означает универсальную ограниченную пространственную область. Это технический термин проекта, а не сущность какого-либо конкретного сеттинга.

## С чего начать

- [`PROJECT.md`](PROJECT.md) — текущее каноническое состояние проекта и архитектурные инварианты.
- [`docs/roadmap.md`](docs/roadmap.md) — этапы разработки Core 0.1.
- [`docs/architecture.md`](docs/architecture.md) — актуальная архитектура.
- [`docs/glossary.md`](docs/glossary.md) — общий словарь терминов.
- [`docs/decisions/`](docs/decisions/) — принятые архитектурные решения и причины их принятия.

## Локальная установка

Требуется Python 3.11 или новее. Для обычной разработки рекомендуется stable Python 3.11+ и отдельный virtual environment.

Пример для bash/zsh:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,render]"
python -m pytest
```

Для fish активация отличается:

```fish
source .venv/bin/activate.fish
```

Core 0.1 намеренно ограничивает NumPy диапазоном `>=2.0,<2.4`. Начиная с NumPy 2.4 официальные x86-64 wheels используют более новый CPU baseline; на старых x86_64 CPU это может завершаться `Illegal instruction` ещё при импорте NumPy. Проверенный совместимый вариант для старого x86_64 — NumPy 2.3.x.

Локальные virtual environments, test-generation outputs, editable-install metadata и Python caches игнорируются `.gitignore`.

## CLI

После установки доступен canonical application entrypoint:

```bash
domain-generator generate request.json \
  --presets presets.json \
  --output ./generated/map01 \
  --preview
```

`--presets` может быть опущен для request без preset-driven features. `--preview` создаёт диагностический `technical-map.png`; это инженерная визуализация world state, а не player-facing карта.

## Граница проекта

Core намеренно не зависит от конкретного сеттинга. Он знает об универсальных понятиях: геометрии, рельефе, гидрологии, полях, сетях, ограничениях, процедурных объектах и правилах размещения, но не знает о конкретном мире, кампании, игровой системе, интерфейсе или presentation renderer-е.

Внешние проекты могут использовать `domain_generator` как библиотеку или движок и преобразовывать собственные понятия в публичные универсальные контракты Core. Каталоги пресетов конкретного сеттинга, adapters и данные мира должны жить вне базового Core.

## Основной поток

```text
внешний клиент / проект мира
        ↓
    DomainSpec
        ↓
 детерминированный Core
        ↓
    DomainData
        ↓
 renderer / exporter / интеграция с игрой
```

LLM, orchestration агентов, GitHub Actions и инструменты представления не являются частью процедурной семантики.

## Состояние разработки

M0–M11 завершены. Core 0.1 функционально закрыт Acceptance Suite и находится в коротком release-hardening / release-candidate review. Актуальный checkpoint и следующий bounded шаг всегда фиксируются в [`PROJECT.md`](PROJECT.md).

## Язык документации

Объяснительный текст, заголовки, ADR, design-документы, README и проектные заметки пишутся по-русски. Английскими остаются имена типов, функций, полей, enum, файлов, CLI-команд, serialized values и другие буквальные технические идентификаторы, которые должны совпадать с кодом или контрактом.

## Правило документации

Нормативные документы проекта используют машиночитаемый YAML front matter и человекочитаемый Markdown. Иллюстративные примеры не создают неявных правил Core и не должны молча превращаться в требования.
