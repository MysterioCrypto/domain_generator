# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/roadmap.md`.
3. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
4. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
5. Прочитать `docs/design/domain-bundle-export-v0.1.md`.
6. Прочитать `docs/design/technical-renderer-v0.1.md`.
7. Прочитать `docs/design/canonical-cli-python-entrypoint-v0.1.md`.
8. Соблюдать INV-006: существенные изменения сначала обсуждаются и документируются.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

Текущий `main` после принятого merge PR #44:

```text
f5efd8cc88fca28713d000d7112f3caa59292ad5
```

PR #44 `Canonical CLI / Python Application Entrypoint v0.1` принят пользователем и merged. CI merge commit — success; implementation checkpoint проходил полный suite `312 passed`.

### Уже в main

- Final Validation hard gate;
- Soft Constraint Compilation & Scoring;
- HydroFeature / Lake Materialization;
- DomainData Assembler v0.1;
- DomainBundle Export v0.1;
- Technical Renderer v0.1;
- GenerationRequest v0.1;
- PresetCatalog v0.1;
- canonical `generate_domain()`;
- application-level `generate_domain_bundle()`;
- installed CLI `domain-generator generate`;
- GitHub Actions pytest CI.

M0–M10 Core 0.1 фактически завершены. Следующий Core release gate — M11 Acceptance Suite. Выбранный следующий integration design gate — `Local Model Skill / Adapter v0.1`.

## Текущий end-to-end flow

```text
GenerationRequest
  ├─ DomainSpec
  └─ GenerationConfig
        +
external PresetCatalog
        ↓
PresetRegistry + CORE_OPERATOR_IDS
        ↓
generate_domain(...)
        ↓
Compiler
→ Layout
→ Terrain
→ Hydrology
→ Surface
→ Dependent Placement
→ Final Validation
→ deterministic selection
→ DomainData Assembler
        ↓
DomainAssembly
   ├─ DomainBundle Export
   └─ optional Technical Renderer
        ↓
atomic application output
```

CLI:

```text
domain-generator generate <request.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir>
domain-generator generate <request.json> --presets <catalog.json> --output <dir> --preview
```

## Следующий bounded design gate

```text
Local Model Skill / Adapter v0.1
```

Его задача — дать локальной LLM/agent оболочке управлять generator-ом через уже существующий canonical application boundary, а не через внутренние Core stages.

Желаемый flow:

```text
natural-language request
        ↓
Local Model Adapter
        ↓
validated GenerationRequest
+ existing PresetCatalog/capability view
        ↓
canonical application entrypoint
        ↓
DomainBundle + optional technical preview
```

В design нужно решить:

1. какие inputs получает модель;
2. в каком строгом формате она возвращает generation intent;
3. как ей предъявляется доступный preset catalog и capability set;
4. разрешена ли автоматическая техническая коррекция request;
5. сколько repair attempts допустимо;
6. какие ошибки считаются repairable, а какие требуют возврата пользователю;
7. как запретить скрытый semantic reroll и бесконечный поиск «красивой» карты;
8. вызывает ли local adapter Python API или CLI и где находится filesystem boundary;
9. что логируется для воспроизводимости/audit;
10. как этот же contract затем переиспользует remote GitHub Actions adapter.

До принятия design никакой runtime implementation adapter-а не начинать.

## Важная граница ответственности

LLM не должна напрямую вызывать `terrain_stage`, `hydrology_stage`, `placement_stage` или редактировать `.npy`/`DomainData` после generation. Она формулирует request и использует canonical application API.

Technical validation/repair не должен превращаться в скрытый semantic reroll. Если request валиден, но пользователь хочет другой мир, это новый explicit generation intent/запуск.

## Следующие этапы после Local Model Adapter

```text
Local Model Skill / Adapter v0.1
→ Remote GitHub Actions Generation Adapter
→ M11 Acceptance Suite / Core 0.1 hardening
→ Core 0.1 release candidate
```

Presentation/ImageGen Guide Renderer остаётся отдельным downstream track и не блокирует integration/release hardening.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без отдельного `Принято.` пользователя.
- GitHub Actions pytest — каноническая execution-проверка.
