---
design: codex-integration-packaging-v0.1
status: accepted
implementation: false
scope: integration
---

# Codex Integration Packaging v0.1

## 1. Цель

Сделать `domain_generator` удобным для использования непосредственно из OpenAI Codex без повторного ручного объяснения архитектуры и правил authoring в каждом запросе.

Этот слой не меняет Core semantics и не добавляет OpenAI API/provider dependency. Codex выступает как внешний агент, который читает repository instructions, использует специализированный skill и вызывает уже существующую canonical application boundary.

```text
user intent
    ↓
Codex
    ├─ AGENTS.md
    └─ domain-generator-authoring skill
            ↓
GenerationRequest + external PresetCatalog
            ↓
domain-generator generate ...
            ↓
DomainBundle + optional technical preview
```

## 2. Граница ответственности

Codex integration находится вне procedural Core.

Не допускается:

- импортировать OpenAI/Codex SDK в Core generation modules;
- давать Codex специальный обход canonical compiler/application API;
- позволять skill напрямую вызывать `layout_stage`, `terrain_stage`, `hydrology_stage`, `surface_stage`, `placement_stage` или `final_stage`;
- редактировать canonical `.npy`/`domain.json` как способ изменения мира;
- вводить отдельные Codex-only generation semantics.

Codex должен пользоваться теми же публичными `GenerationRequest`, `PresetCatalog` и CLI/application semantics, что и другие callers.

## 3. Два уровня инструкций

### 3.1 Корневой `AGENTS.md`

В корне repository появляется короткий `AGENTS.md`.

Его назначение — постоянная карта проекта, а не полный prompt генератора.

Он должен:

- указать `PROJECT.md` как первую статусную точку входа;
- сослаться на canonical architecture/design documents;
- закрепить INV-006: design/docs before implementation для архитектурных изменений;
- напомнить, что implementation PR merge требует отдельного пользовательского принятия;
- направлять задачи authoring/generation к skill `domain-generator-authoring`;
- запрещать обход canonical application boundary;
- указывать базовую проверку `python -m pytest` для code changes.

`AGENTS.md` не должен дублировать все contracts/preset semantics. Его задача — routing и project workflow.

### 3.2 Codex skill

Repository поставляет skill:

```text
.codex/skills/domain-generator-authoring/
  SKILL.md
```

`SKILL.md` должен использовать Codex-compatible YAML frontmatter только с обязательными полями:

```yaml
---
name: domain-generator-authoring
description: ...
---
```

`description` является главным trigger metadata и должен явно перечислять случаи использования: создание региона по natural-language intent, изменение существующего `GenerationRequest`, validation/preflight troubleshooting и запуск генерации/preview через `domain_generator`.

Body skill загружается только после trigger и содержит procedural guidance.

## 4. Связь с Local Model Adapter

Codex integration не заменяет `Local Model Skill / Adapter v0.1`.

Есть два supported orchestration mode:

```text
Programmatic local model
    ↓
LocalModelHost
    ↓
Local Model Adapter
    ↓
canonical application API
```

и:

```text
Codex interactive agent
    ↓
AGENTS.md + Codex skill
    ↓
canonical CLI/application boundary
```

Оба режима обязаны соблюдать одинаковую semantic policy:

- base request сохраняет technical defaults;
- available capabilities берутся из реального PresetCatalog;
- неизвестные presets/operators/parameters не выдумываются;
- technical repair ограничен;
- successful request запускается один semantic generation раз;
- generation failure не вызывает hidden semantic reroll;
- technical preview не используется для автономного эстетического reroll loop.

Existing reference artifact `docs/skills/local-model-authoring-v0.1.md` остаётся provider-neutral подробным описанием authoring policy. Codex skill должен ссылаться на него, а не создавать вторую независимую версию semantics.

## 5. Codex authoring workflow

При задаче вида:

```text
"Сделай регион 40×30 км: горный хребет на севере,
река к югу и поселение возле реки."
```

skill должен вести Codex по следующему пути:

```text
1. Определить base GenerationRequest.
2. Определить canonical PresetCatalog.
3. При наличии — прочитать PresetGuideCatalog/проектные пояснения.
4. Сформировать или изменить GenerationRequest.
5. Не менять protected technical defaults без явного intent.
6. Выполнить validation/compiler preflight доступным public API/CLI способом.
7. При технической ошибке — максимум 2 исправления после initial draft.
8. После успешного preflight — один generation run.
9. Вернуть пользователю output path, accepted attempt и preview path при наличии.
```

Если отсутствует необходимый base request или preset catalog и его нельзя однозначно определить из repository context, Codex должен сообщить, какой конкретно artifact нужен, вместо выдумывания capabilities.

## 6. Запуск generation

Предпочтительная user-facing command boundary:

```text
domain-generator generate <request.json> \
  --presets <presets.json> \
  --output <output-dir> \
  --preview
```

Если features отсутствуют, `--presets` может быть опущен согласно existing canonical CLI semantics.

Skill может использовать публичный Python API для preflight/validation, когда это удобнее, но semantic generation должен оставаться эквивалентным canonical application entrypoint.

## 7. Installation/discovery contract

Repository-local canonical copy skill хранится в `.codex/skills/domain-generator-authoring/`.

Для Codex environment, где требуется user-level installation, тот же skill может быть установлен в `$CODEX_HOME/skills` через Codex `$skill-installer` по GitHub directory URL. После установки Codex может потребовать restart для повторного discovery skills.

Инструкция установки должна находиться в отдельной пользовательской integration note, а не раздувать `AGENTS.md`.

## 8. Implementation artifacts v0.1

Implementation PR должен добавить:

```text
AGENTS.md
.codex/skills/domain-generator-authoring/SKILL.md
docs/integrations/codex.md
tests/test_codex_packaging.py
```

`tests/test_codex_packaging.py` должен статически проверять минимум:

- наличие root `AGENTS.md`;
- наличие canonical skill folder;
- YAML frontmatter `SKILL.md` содержит `name` и `description` и не содержит случайных custom metadata fields;
- skill name соответствует directory/expected id;
- ссылки из `AGENTS.md` и skill на repository artifacts существуют;
- skill упоминает canonical `domain-generator generate` boundary;
- skill не инструктирует вызывать internal stages напрямую;
- integration note содержит repo-local и `$skill-installer` installation paths.

Не требуется сетевой test против Codex/OpenAI API.

## 9. Out of scope v0.1

- OpenAI API client/backend;
- `CodexHost(LocalModelHost)`;
- API key management;
- MCP server;
- Codex plugin с собственным tool server/UI;
- автоматическая публикация skill в внешний marketplace/catalog;
- autonomous image evaluation/reroll;
- изменение Core generation semantics;
- Remote GitHub Actions Generation Adapter.

## 10. Compatibility notes

Codex-specific packaging следует актуальной модели OpenAI: `AGENTS.md` предоставляет scoped repository instructions; skill представляет собой folder с обязательным `SKILL.md`, YAML `name`/`description` и optional bundled resources. User-level skills устанавливаются под `$CODEX_HOME/skills`; `$skill-installer` умеет устанавливать skill из GitHub repository path.

Эти внешние Codex conventions являются integration compatibility layer. Если Codex packaging convention изменится, должен меняться этот adapter/package layer, а не Core contracts.

## 11. Следующий шаг

После принятого design и green docs CI:

```text
Codex Integration Packaging v0.1 — implementation PR
    ↓
implementation acceptance
    ↓
Remote GitHub Actions Generation Adapter — next design gate
```
