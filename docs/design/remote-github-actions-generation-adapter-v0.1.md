---
design: remote-github-actions-generation-adapter-v0.1
status: accepted
implemented: false
scope: integration
---

# Remote GitHub Actions Generation Adapter v0.1

## 1. Назначение

Remote GitHub Actions Generation Adapter предоставляет удалённый способ запуска уже существующего canonical `domain-generator generate` без создания второго generation API и без изменения semantics Core.

Он является transport/execution layer вокруг canonical CLI.

```text
GenerationRequest + optional PresetCatalog
        ↓
GitHub Actions transport
        ↓
exact repository checkout
        ↓
canonical domain-generator CLI exactly once
        ↓
DomainBundle + execution artifacts
```

Core, compiler, pipeline stages, ranking, assembler, bundle export и technical renderer остаются единственными источниками generation semantics.

## 2. Два поддерживаемых trigger path

v0.1 поддерживает два внешних пути запуска одного и того же workflow semantics.

### 2.1 `workflow_dispatch`

Используется человеком, Codex, `gh` или другим клиентом, который умеет явно запускать workflow.

Inputs минимальны:

- `request_path`: repository-relative путь к `GenerationRequest` JSON;
- `presets_path`: optional repository-relative путь к `PresetCatalog` JSON;
- `preview`: boolean, запрашивать ли technical preview.

Workflow inputs НЕ дублируют semantic поля `GenerationRequest`. В workflow не появляются отдельные `seed`, `width`, `height`, hydrology parameters, feature parameters и т. п.

### 2.2 `pull_request` по `remote-requests/**`

Используется для chat/agent-driven remote execution, когда внешний агент умеет создавать branch/file/PR, но не умеет инициировать `workflow_dispatch`.

Workflow запускается на PR только при изменениях под:

```text
remote-requests/**
```

Каждый runnable request хранится в отдельной директории:

```text
remote-requests/<request-id>/request.json
remote-requests/<request-id>/presets.json   # optional
remote-requests/<request-id>/run.json       # adapter manifest
```

`run.json` — transport-only manifest, который указывает, какой request выполнять и нужен ли preview. Он не является Core contract и не содержит дополнительных semantic generation settings.

PR, созданный только ради remote generation, не обязан и обычно не должен merge-иться. Generated output не коммитится в repository.

## 3. Exact revision semantics

Workflow обязан выполнять generation из того же checkout, который является subject конкретного workflow run.

Для PR path это exact PR head SHA. Для manual dispatch это exact ref/SHA, на котором запущен workflow.

Workflow НЕ делает второй checkout `main`, не устанавливает случайную опубликованную версию generator и не подменяет текущую ревизию.

Execution provenance записывает минимум:

- repository;
- workflow run id;
- workflow run attempt;
- exact `github.sha`;
- event name;
- request relative path + SHA-256;
- optional presets relative path + SHA-256;
- preview flag;
- canonical CLI exit code.

Exact replay гарантируется только в рамках существующего version/revision contract Core; cross-version identity не обещается.

## 4. Safe path validation

Transport layer проверяет filesystem paths до вызова CLI.

Допустимый input path:

- относительный;
- после resolve остаётся внутри `GITHUB_WORKSPACE`;
- указывает на существующий regular file;
- имеет ожидаемое `.json` расширение.

Абсолютные пути и traversal (`../`) запрещены.

Это transport safety. Semantic validation JSON по-прежнему выполняют canonical application contracts/compiler.

## 5. Execution rule

После успешной transport validation workflow выполняет canonical CLI ровно один раз:

```text
domain-generator generate <request>
  [--presets <catalog>]
  --output <temporary-output>
  [--preview]
```

Remote adapter не вызывает внутренние generation stages напрямую.

Remote adapter не имеет semantic fallback.

После semantic generation failure он НЕ:

- меняет seed;
- повторяет generation автоматически;
- увеличивает `max_attempts`;
- ослабляет hard constraints;
- удаляет/двигает features;
- редактирует request/presets;
- запускает LLM repair loop.

Новый run после semantic failure требует нового внешнего действия/intent.

## 6. Output artifacts

v0.1 публикует отдельные artifact classes.

### 6.1 `domain-bundle`

Публикуется только после успешной generation.

Содержит canonical output tree, созданный application layer:

```text
bundle/
  domain.json
  manifest.json
  fields/
    elevation.npy
    water_depth.npy
    moisture.npy
    vegetation_density.npy
  preview/
    technical-map.png        # только когда preview=true
```

Remote adapter не переписывает canonical files.

### 6.2 `technical-preview`

Когда `preview=true` и generation успешна, `technical-map.png` дополнительно публикуется отдельным небольшим artifact для удобного retrieval агентом/человеком.

Это копия downstream technical preview, а не отдельный world state.

### 6.3 `generation-diagnostics`

Публикуется при success и failure (`if: always()`).

Содержит noncanonical execution evidence:

```text
execution/
  remote-execution.json
  request.json
  presets.json        # когда был catalog
  stdout.txt
  stderr.txt
```

`request.json`/`presets.json` здесь являются snapshot входов конкретного run.

Diagnostics не являются частью canonical DomainBundle.

## 7. Failure semantics

Если transport validation, input validation, compiler, generation, assembly, export или render завершается ошибкой:

1. execution evidence сохраняется настолько полно, насколько возможно;
2. `generation-diagnostics` загружается через artifact upload;
3. job остаётся failed;
4. `domain-bundle` не публикуется как успешный result.

Нельзя маскировать CLI non-zero exit code успешным workflow status только ради artifact upload.

## 8. Permissions и repository writes

Workflow использует минимальные permissions:

```yaml
permissions:
  contents: read
```

Workflow не выполняет `git push`, не создаёт commits/releases и не записывает generated outputs обратно в repository.

GitHub Actions artifact storage — единственный v0.1 publication mechanism.

## 9. Chat/agent remote-generation flow

Поддерживаемый agent-driven сценарий:

```text
user intent
  ↓
agent/Codex authors request files
  ↓
temporary branch
  ↓
remote-requests/<id>/...
  ↓
PR
  ↓
PR-triggered GitHub Actions run
  ↓
artifact retrieval
  ↓
DomainBundle / technical preview / diagnostics
```

После retrieval временный PR может быть закрыт без merge.

Способ отображения downloaded PNG inline в конкретном chat host является downstream UI concern и не входит в adapter semantics. Adapter обязан сделать preview легко извлекаемым отдельным artifact.

## 10. Local Codex path сохраняется

Remote adapter не заменяет repository-local Codex integration.

Оба пути существуют параллельно:

```text
Codex local checkout
  → AGENTS.md + skill
  → canonical CLI locally
```

и

```text
Codex/chat/client
  → GitHub Actions transport
  → exact checkout
  → canonical CLI remotely
```

Оба используют один application/CLI contract.

## 11. Implementation slice v0.1

Implementation PR должен добавить минимум:

```text
.github/workflows/generate-domain.yml
scripts/remote_generation.py
docs/integrations/github-actions-generation.md
remote-requests/example/
tests/test_github_actions_generation_adapter.py
```

`scripts/remote_generation.py` допустим как repository integration helper, но он не входит в `src/domain_generator` и не становится Core API. Его обязанности ограничены path safety, execution metadata, CLI invocation orchestration и diagnostics packaging.

## 12. Tests

Минимальный test coverage:

- workflow имеет `workflow_dispatch` и PR path filter `remote-requests/**`;
- workflow permissions — `contents: read`;
- semantic inputs не дублируются отдельными workflow parameters;
- exact checkout/revision используется без secondary checkout `main`;
- helper rejects absolute/traversal/out-of-workspace paths;
- helper вызывает canonical CLI максимум один раз;
- optional presets корректно поддерживается;
- success создаёт bundle/preview/diagnostics layout;
- CLI failure сохраняет diagnostics и остаётся failure;
- workflow использует `actions/upload-artifact@v4`;
- нет `git push`, semantic reroll/repair loop или direct internal-stage execution.

Network GitHub API test не обязателен для unit/static suite. Первый реальный merged workflow должен быть отдельно проверен end-to-end test run через temporary `remote-requests/**` PR.

## 13. Out of scope v0.1

- LLM внутри GitHub Actions;
- automatic semantic repair/reroll;
- parallel/batch generation;
- artifact attestations;
- Releases/S3/Pages publication;
- long-running service/API server;
- repository commits generated world data;
- Presentation/ImageGen Guide Renderer;
- изменение Core contracts/pipeline semantics.

## 14. Acceptance boundary

Design принят до implementation согласно INV-006.

После docs merge implementation идёт отдельным PR и не merge-ится без отдельного явного принятия implementation checkpoint.