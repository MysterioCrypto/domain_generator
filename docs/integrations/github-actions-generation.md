# Remote generation через GitHub Actions

Normative design: `docs/design/remote-github-actions-generation-adapter-v0.1.md`.

## Что это такое

Remote workflow не является вторым генератором. Он checkout-ит точную repository revision, устанавливает generator из этого checkout и один раз вызывает canonical CLI:

```text
domain-generator generate ...
```

Локальный Codex path (`AGENTS.md` + `domain-generator-authoring` skill) продолжает работать независимо.

## Ручной запуск

Workflow `generate-domain` поддерживает `workflow_dispatch`.

Inputs:

- `request_path` — repository-relative путь к `GenerationRequest` JSON;
- `presets_path` — optional repository-relative путь к `PresetCatalog` JSON;
- `preview` — нужен ли `technical-map.png`.

Пример существующего request:

```text
remote-requests/example/request.json
```

Для него `presets_path` оставляется пустым.

## Chat/agent запуск через PR

Когда клиент не умеет `workflow_dispatch`, используется временная branch:

```text
remote-generation/<request-id>
```

В неё добавляется один runnable unit:

```text
remote-requests/<request-id>/request.json
remote-requests/<request-id>/presets.json   # optional
remote-requests/<request-id>/run.json
```

`run.json` содержит только transport configuration:

```json
{
  "run_version": "0.1",
  "request_path": "remote-requests/example/request.json",
  "presets_path": null,
  "preview": true
}
```

После открытия PR изменение под `remote-requests/**` запускает generation workflow. Для одного generation PR должен изменяться ровно один `remote-requests/**/run.json`.

## Artifacts

Успешный run публикует:

```text
domain-bundle
technical-preview        # если preview был создан
generation-diagnostics
```

`domain-bundle` содержит canonical DomainBundle. `technical-preview` — отдельная копия `preview/technical-map.png` для удобного скачивания. `generation-diagnostics` содержит snapshot входов, execution metadata, stdout и stderr.

При ошибке `generation-diagnostics` всё равно публикуется, а workflow остаётся failed.

Artifacts имеют retention 7 дней в v0.1.

## Exact revision

Для PR workflow явно checkout-ит `pull_request.head.sha`; для manual dispatch используется SHA/ref самого run. Secondary checkout `main` не выполняется.

`remote-execution.json` записывает `GITHUB_SHA`, run id/attempt, event name, hashes input files и canonical CLI exit code.

## No hidden reroll

Один workflow run вызывает canonical CLI максимум один раз. Workflow не меняет seed, constraints, `max_attempts`, features или request после semantic failure.

## Temporary branch cleanup

Generation branch не должна оставаться в repository после завершения теста.

```text
artifact retrieval
→ close generation PR without merge
→ cleanup-remote-generation workflow
→ delete remote-generation/<id>
```

Generation workflow имеет только `contents: read`.

Отдельный `cleanup-remote-generation` workflow получает `contents: write`, но запускается только на `pull_request: closed` и удаляет только same-repository branches с prefix `remote-generation/`. PR из fork и любые обычные branches не подходят под условие cleanup.

Удаление temporary branch не удаляет workflow run/artifacts. Artifact lifetime определяется Actions retention policy; удаление самого workflow run удаляет связанные artifacts.

## Example

Repository содержит non-semantic example transport request:

```text
remote-requests/example/request.json
remote-requests/example/run.json
```

Он нужен как проверяемый reference format, а не как setting-specific preset.
