# Handoff: продолжение разработки `domain_generator`

Этот файл — ненормативная оперативная точка входа для нового чата/агента. Канонические решения находятся в `PROJECT.md`, `docs/architecture.md`, `docs/decisions/` и `docs/design/`.

## С чего начинать новый чат

1. Прочитать `PROJECT.md`.
2. Прочитать `docs/design/end-to-end-runtime-bundle-v0.1.md`.
3. Прочитать `docs/design/hydrofeature-lake-materialization-v0.1.md`.
4. Прочитать `docs/design/domain-data-assembler-v0.1.md`.
5. Не менять архитектуру без обсуждения: действует INV-006.

## Текущее состояние на 2026-09-13

Репозиторий: `MysterioCrypto/domain_generator`.

`main` после merge design PR #35:

```text
7cbd089d4530ff3db8238710edf988bbc6b1dd17
```

### Уже в main

- PR #30 Final Validation hard-complete v0.1 — merged;
- PR #31 Documentation Language Cleanup v0.1 — merged;
- PR #32 Soft Constraint Compilation & Scoring v0.1 — merged;
- PR #33 HydroFeature / Lake Materialization design v0.1 — merged;
- PR #34 HydroFeature / Lake Materialization implementation v0.1 — merged;
- PR #35 DomainData Assembler design v0.1 — merged.

### Текущий implementation checkpoint

PR #36 `Implement DomainData Assembler v0.1` открыт и **не должен merge-иться без отдельного принятия пользователя**.

Implementation branch:

```text
impl/m2-domain-data-assembler-v0.1
```

Реализовано:

- `DomainAssembly` in-memory boundary;
- `assemble_domain(spec, plan, config, candidate)` без RNG/IO/rerank;
- semantic `GenerationConfig` fingerprint без observability;
- reserved generated hydro IDs `^lake-[0-9]{4,}$` на `DomainSpec` validation boundary;
- specified features из final layout/placement geometry;
- merge specified + ready hydrology `HydroFeature` с collision guard;
- canonical network `rivers`;
- canonical descriptors для elevation/water_depth/moisture/vegetation_density;
- exact float32/shape checks;
- independent read-only payload copies;
- identity/provenance/final validation summary;
- deterministic feature/field/network ordering;
- explicit `DomainAssemblyError` boundary.

Подтверждённый push CI текущей code semantics:

```text
272 passed
```

Serialized `DomainData` schema не менялась, поэтому schema snapshot regeneration не требуется.

## Рабочий процесс

- Один bounded архитектурный вопрос за раз.
- Сначала design и последствия.
- Пользователь принимает/изменяет/отклоняет.
- После принятия normative docs фиксируются до runtime implementation.
- Implementation ведётся отдельным PR.
- Implementation PR не merge-ить без явного принятия пользователем checkpoint.
- GitHub Actions pytest — каноническая execution-проверка.

## Главная граница Core

`domain_generator` — setting-agnostic procedural Core.

```text
world / setting / application
          ↓
   adapter / presets
          ↓
      DomainSpec
          ↓
   domain_generator
          ↓
      DomainData
          ↓
 renderer / exporter / integration
```

## End-to-End target

```text
DomainSpec JSON/YAML-adapter
        ↓
canonical Python/CLI entrypoint
        ↓
Core pipeline
        ↓
DomainAssembly
        ↓
DomainBundle
  domain.json
  manifest.json
  fields/*.npy
  preview/technical-map.png   # non-canonical
```

## Следующий порядок после принятия и merge PR #36

```text
DomainBundle Export v0.1 design
→ DomainBundle Export implementation
→ Technical Renderer v0.1
→ canonical CLI / Python application entrypoint
→ local model skill/adapter
→ remote GitHub Actions generation adapter
```

Обновлять этот handoff при крупных checkpoint-ах, но не использовать вместо нормативных design/ADR документов.
