# Remote generation через GitHub Actions

Normative design: `docs/design/remote-github-actions-generation-adapter-v0.1.md`.
Guide Renderer extension: `docs/design/guide-renderer-v0.1.md`.

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
- `preview` — нужен ли diagnostic `technical-map.png`;
- `guide_preview` — нужен ли человекочитаемый `guide-map.png`.

Оба preview-флага presentation-only и не меняют semantic generation result.

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
  "preview": true,
  "guide_preview": false
}
```

`guide_preview` optional и для старых manifests по умолчанию считается `false`.

После открытия PR изменение под `remote-requests/**` запускает generation workflow. Для одного generation PR должен изменяться ровно один `remote-requests/**/run.json`.

## Artifacts

Успешный run может публиковать:

```text
domain-bundle
generation-diagnostics
technical-preview        # когда создан preview/technical-map.png
guide-preview            # когда создан preview/guide-map.png
```

`domain-bundle` содержит canonical DomainBundle. Preview artifacts являются downstream copies для удобного скачивания и не входят в canonical manifest/world identity.

При ошибке `generation-diagnostics` всё равно публикуется, а workflow остаётся failed.

Artifacts имеют retention 7 дней в v0.1.

## Exact revision

Для PR workflow явно checkout-ит `pull_request.head.sha`; для manual dispatch используется SHA/ref самого run. Secondary checkout `main` не выполняется.

`remote-execution.json` записывает exact generator commit, raw `GITHUB_SHA`, run id/attempt, event name, hashes input files, preview flags и canonical CLI exit code.

## No hidden reroll

Один workflow run вызывает canonical CLI максимум один раз. Workflow не меняет seed, constraints, `max_attempts`, features или request после semantic failure. Guide rendering не создаёт дополнительный semantic generation run.

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

## Examples

Repository содержит transport examples:

```text
remote-requests/example/
remote-requests/visual-example/
```

А representative map-like Guide Renderer world хранится отдельно как обычный example input:

```text
examples/guide-renderer/demo-region/request.json
examples/guide-renderer/demo-region/presets.json
```

Generated PNG/bundle для demo не коммитятся в repository.
