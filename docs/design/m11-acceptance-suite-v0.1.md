---
design: m11-acceptance-suite-v0.1
status: accepted
implemented: false
scope: core-release-gate
---

# M11 Acceptance Suite v0.1

## 1. Назначение

M11 — release gate Core 0.1. Он не добавляет новые generation capabilities, а доказывает, что уже реализованный canonical pipeline воспроизводимо работает целиком на небольшом наборе representative worlds.

Acceptance suite проходит тот же semantic path, который используют реальные consumers:

```text
GenerationRequest + PresetCatalog
        ↓
canonical application/compiler boundary
        ↓
Layout → Terrain → Hydrology → Surface
→ Dependent Placement → Final Validation / ranking
→ DomainData Assembly
→ DomainBundle Export
```

M11 не является заменой unit/integration tests. Unit tests доказывают локальные свойства modules; acceptance worlds доказывают совместную работу системы.

## 2. Acceptance worlds

Core 0.1 фиксирует семь обязательных cases:

```text
A01 minimal
A02 terrain-ridge
A03 hydrology-lake-river
A04 surface
A05 dependent-poi
A06 constraints-ranking
A07 complex-mixed
```

Каждый case имеет fixed semantic inputs и fixed seed.

Рекомендуемая структура:

```text
tests/acceptance/
  cases/
    a01-minimal/
      request.json
      presets.json        # только если нужен
      expected.json
    a02-terrain-ridge/
      ...
    ...
    a07-complex-mixed/
      ...
  conftest.py
  support.py
  test_cases.py
  test_replay.py
```

Case inputs являются test data, а не production built-in presets и не setting content.

## 3. Два уровня acceptance assertions

Каждый case обязан проверять одновременно:

1. **exact replay / baseline identity**;
2. **semantic meaning** результата.

Наличие только hashes недостаточно: ошибочно обновлённый baseline не должен скрывать бессмысленный world state.

Наличие только high-level semantic assertions также недостаточно: M11 должен ловить непреднамеренные изменения deterministic output.

## 4. Exact replay contract

Для одного и того же case в рамках одной exact generator revision/version выполняются минимум два независимых generation runs.

Ожидается exact equality для canonical semantic outputs:

- accepted attempt index;
- `DomainData` canonical JSON representation;
- canonical field arrays:
  - `elevation`;
  - `water_depth`;
  - `moisture`;
  - `vegetation_density`;
- canonical bundle manifest/hashes;
- semantic fingerprints/provenance, кроме значений, которые нормативно являются host/execution metadata и не входят в canonical world state.

Это проверяет INV-003, INV-007, INV-008 и INV-009 в пределах exact generator version.

Cross-version identity не обещается. Осознанное semantic изменение generator может потребовать отдельного review/update acceptance baselines.

## 5. Compact golden strategy

Repository не обязан хранить большие `.npy` binary goldens.

`expected.json` хранит компактные ожидаемые свойства и cryptographic digests canonical outputs. Например:

```json
{
  "case_version": "0.1",
  "accepted_attempt_index": 0,
  "spec_fingerprint": "sha256:...",
  "plan_fingerprint": "sha256:...",
  "generation_config_fingerprint": "sha256:...",
  "domain_data_sha256": "sha256:...",
  "fields": {
    "elevation": {
      "sha256": "sha256:...",
      "min": 0.0,
      "max": 350.0
    }
  },
  "semantic": {
    "...": "case-specific assertions"
  }
}
```

Field digests должны вычисляться по canonical array bytes/dtype/shape contract либо переиспользовать canonical DomainBundle manifest hashes, если это однозначно соответствует экспортированному `.npy` payload.

Большие binary golden files допускаются только отдельным будущим решением; baseline M11 v0.1 на них не зависит.

## 6. Canonical JSON digest

Для compact `domain_data_sha256` test harness обязан использовать один явно определённый deterministic JSON encoding:

- model dump в JSON-compatible form;
- UTF-8;
- sorted object keys;
- compact separators;
- без whitespace-dependent semantics.

Test helper является единственным местом, где реализуется этот acceptance digest algorithm.

Digest не становится новым production contract/API. Это test baseline mechanism.

## 7. Case A01 — Minimal

Цель: доказать базовый end-to-end pipeline без specified features.

Минимальные semantic assertions:

- request/compiler/application path проходит успешно;
- final validation проходит;
- accepted candidate существует;
- specified features отсутствуют;
- canonical field set содержит ровно обязательные Core 0.1 fields;
- arrays имеют ожидаемые shape/dtype и finite values;
- `water_depth >= 0`;
- moisture/vegetation находятся в `[0, 1]`;
- DomainBundle export успешен;
- exact replay успешен.

Minimal case не обязан иметь реки/озёра/POI.

## 8. Case A02 — Terrain Ridge

Цель: representative terrain generation.

Case содержит deterministic `Band` feature с `ridge` effect.

Минимальные assertions:

- final feature materialized как terrain band;
- band geometry валидна и находится в domain bounds;
- elevation не является constant base field;
- expected max/min/range elevation свойства выполняются;
- ridge materially affects cells around its generated centerline;
- hard validation проходит;
- field/hash baseline совпадает;
- exact replay успешен.

Acceptance не требует художественно гладкого рельефа.

## 9. Case A03 — Hydrology / Lake / River

Цель: доказать end-to-end hydrology materialization на заранее подобранном deterministic terrain/seed.

Case обязан гарантированно создавать наблюдаемый hydrology result; тест вида «река может появиться» недопустим.

Минимальные assertions:

- canonical `water_depth` неотрицателен;
- canonical water mask эквивалентен `water_depth > 0`;
- существует минимум один generated `HydroFeature` lake;
- lake properties/geometry internally consistent;
- `rivers` network существует и содержит ожидаемое ненулевое число nodes/segments;
- каждый river segment ссылается на существующие nodes;
- directed topology internally consistent;
- accumulation/depth semantics, доступные через final output/contracts, удовлетворяют invariant expectations;
- exact replay и digest baseline успешны.

Case seed/terrain подбираются implementation-ом один раз и затем фиксируются.

## 10. Case A04 — Surface

Цель: canonical surface fields и feature bias.

Case содержит deterministic surface feature/bias и воду либо иной deterministic water context, достаточный для проверки water forcing.

Минимальные assertions:

- `moisture` и `vegetation_density` finite и в `[0, 1]`;
- water cells имеют `moisture == 1`;
- water cells имеют `vegetation_density == 0`;
- surface feature geometry существует;
- feature bias materially changes target-area field statistics относительно подходящей deterministic reference/expected property;
- overlap/order semantics не зависят от input sibling ordering там, где это уже гарантировано Core;
- exact replay и digests успешны.

## 11. Case A05 — Dependent POI

Цель: проверить deferred placement целиком.

Case содержит reservation-based POI preset с non-trivial `SiteProfile`.

Final semantic assertions:

- final POI materialized как `PointGeometry`;
- point находится внутри domain и разрешённой placement region;
- все hard SiteProfile requirements выполнены;
- expected local suitability/preference outcome соответствует baseline;
- final hard validation проходит;
- exact replay успешен.

Дополнительно acceptance harness может сделать bounded stage-boundary assertions без изменения production API:

```text
Layout: reservation существует, final point ещё отсутствует
Placement: final point существует
```

Эти assertions выполняются test-only harness через уже существующие stage/application functions и не создают новый runtime path.

## 12. Case A06 — Constraints / Ranking

Цель: доказать, что attempts, hard rejection, soft scoring и deterministic ranking совместно выбирают ожидаемого кандидата.

Case должен быть подобран так, чтобы ranking действительно участвовал в выборе, а не всегда тривиально побеждал attempt 0.

Минимальные assertions:

- генерируется больше одного relevant attempt/candidate;
- хотя бы один candidate отличается по hard validity или soft score от другого;
- hard-invalid candidate не может быть принят;
- soft score использует canonical ordering rules;
- winner соответствует tuple semantics:
  1. lower worst effective violation;
  2. higher weighted mean score;
  3. lower attempt index as final tie-break;
- `accepted_attempt_index` равен fixed expected value;
- replay выбирает тот же candidate.

Если implementation обнаружит, что существующий public application API не предоставляет достаточно observability для доказательства ranking mechanics, test-only harness может выполнить pipeline functions напрямую. Это не меняет production application boundary и не допускает альтернативной generation semantics.

## 13. Case A07 — Complex Mixed

Цель: главный representative Core 0.1 world.

Case объединяет минимум:

- terrain shaping;
- hydrology;
- surface feature/bias;
- deferred POI;
- hard constraints;
- soft constraints;
- multiple attempts/ranking, если это не делает case чрезмерно хрупким;
- generated lake/river where deterministic;
- DomainData assembly;
- DomainBundle export.

Assertions:

- все expected specified/generated feature families присутствуют;
- final validation проходит;
- topology/reference integrity проходит;
- canonical fields имеют expected finite/range properties;
- POI/site constraints выполняются;
- expected soft validation summary совпадает;
- fingerprints/digests/accepted attempt соответствуют baseline;
- exact replay успешен.

A07 должен оставаться достаточно маленьким для обычного CI и не является benchmark/performance test.

## 14. Bundle acceptance

Минимум A01 и A07 обязаны проходить через canonical bundle publication path в temporary directory.

Проверяется:

- `domain.json` существует и соответствует assembly data;
- `manifest.json` существует;
- четыре canonical `.npy` files существуют;
- manifest hashes соответствуют actual files;
- повторный generation run создаёт semantic-equivalent canonical bundle;
- output overwrite/atomicity semantics не обходятся acceptance harness-ом.

Suite не должен напрямую писать bundle internals вручную вместо canonical exporter/application path.

## 15. Technical preview policy

Technical Renderer остаётся downstream diagnostic layer.

M11 может проверить:

- preview успешно создаётся для representative case;
- файл является валидным PNG;
- dimensions соответствуют renderer contract;
- repeated render одной assembly детерминирован в рамках текущей renderer implementation.

`technical-map.png` SHA НЕ является Core release-gating golden. Визуальное изменение renderer, не меняющее canonical world state, не должно требовать обновления всех Core acceptance baselines.

Presentation/ImageGen Guide Renderer не входит в M11.

## 16. Baseline review policy

`expected.json` нельзя автоматически перезаписывать во время обычного test run.

Baseline update всегда является явным code-review событием.

Допустимая причина update:

- осознанное semantic изменение generator version;
- исправление подтверждённого Core bug;
- исправление ошибочного acceptance expectation.

Недопустима схема «тест красный → автоматически принять текущие hashes».

Если acceptance case обнаруживает production bug, M11 implementation PR не должен тихо менять Core behavior. Дефект исправляется отдельным bugfix PR, после чего acceptance implementation rebases/continues.

## 17. Performance / CI boundary

Все семь cases обязаны быть достаточно малы для обычного GitHub Actions pytest suite.

M11 v0.1 не является load/performance benchmark. Нельзя использовать огромные domains только для реалистичного вида карты.

Acceptance suite должен запускаться обычным `pytest` вместе с repository suite. Отдельный optional marker `acceptance` допустим для локальной фильтрации, но CI release gate не должен случайно пропускать эти tests.

## 18. Test-only support code

Допустимы:

```text
tests/acceptance/conftest.py
tests/acceptance/support.py
```

Они могут:

- загружать case files;
- строить registry из canonical PresetCatalog;
- вызывать canonical application API;
- для bounded intermediate assertions вызывать существующие pipeline stages;
- считать test-only digests/statistics;
- сравнивать `expected.json`.

Они НЕ могут:

- реализовывать alternate terrain/hydrology/placement logic;
- обходить compiler semantics;
- менять request/seed автоматически после failure;
- копировать production algorithms в tests;
- становиться новым production API.

## 19. Release gate

Core 0.1 может перейти к release-candidate declaration только когда одновременно выполняются:

```text
[green] full unit/integration suite
[green] A01..A07 acceptance worlds
[green] exact replay for all acceptance worlds
[green] canonical bundle acceptance
[green] no engine/hard invariant violation
[green] deterministic provenance/fingerprints/digests
```

Remote GitHub Actions E2E уже проверен отдельным integration track и не дублируется как обязательная часть каждого M11 case.

## 20. Out of scope

M11 v0.1 не включает:

- новые operators/features;
- изменение hydrology/surface/ranking semantics;
- production preset catalogs;
- setting-specific worlds;
- performance benchmarking;
- huge binary goldens;
- visual golden testing technical PNG;
- Presentation/ImageGen Guide Renderer;
- remote workflow redesign;
- automatic baseline regeneration.

## 21. Implementation slice

После merge design docs отдельный implementation PR должен добавить:

```text
tests/acceptance/cases/a01-minimal/...
tests/acceptance/cases/a02-terrain-ridge/...
tests/acceptance/cases/a03-hydrology-lake-river/...
tests/acceptance/cases/a04-surface/...
tests/acceptance/cases/a05-dependent-poi/...
tests/acceptance/cases/a06-constraints-ranking/...
tests/acceptance/cases/a07-complex-mixed/...
tests/acceptance/conftest.py
tests/acceptance/support.py
tests/acceptance/test_cases.py
tests/acceptance/test_replay.py
```

Implementation PR может обнаружить Core bugs. Такие production fixes оформляются отдельно и не маскируются внутри acceptance implementation.

## 22. Acceptance boundary

Этот design принят до implementation согласно INV-006.

Implementation PR M11 не merge-ится без отдельного явного пользовательского принятия после green CI и представления фактических acceptance results.