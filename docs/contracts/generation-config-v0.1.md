---
id: CONTRACT-GENERATIONCONFIG-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# GenerationConfig v0.1 — draft

`GenerationConfig` описывает execution policy, а не сам мир. Он разделён на semantic settings и observability settings.

## Корень

```yaml
generation_config_version: "0.1"

semantic:
  max_attempts: 24
  target_valid_candidates: 4

observability:
  debug: false
  save_rejected_attempts: false
  save_validation_details: false
  save_intermediate_fields: false
```

## Semantic settings

`max_attempts >= 1` — максимум независимых attempts с indices `0..max_attempts-1`.

`target_valid_candidates >= 1` и `<= max_attempts` — сколько valid candidates собрать до deterministic ranking. Значение `1` естественно даёт first-valid semantics; отдельный selection mode в Core 0.1 не нужен.

Pipeline прекращает attempts, когда достигнут `target_valid_candidates` либо исчерпан `max_attempts`.

Если valid candidate не найден, generation завершается `GenerationFailure` с diagnostic summary; это не `DomainData`.

Оба semantic поля участвуют в generation semantics и могут изменить accepted attempt, поэтому canonical semantic config fingerprint включает их.

## Observability settings

Observability/debug flags могут расширяться без изменения generation semantics. Они:

- не входят в semantic config fingerprint;
- не потребляют semantic RNG streams;
- не могут менять branch decisions, ranking или accepted result;
- управляют только logs/traces/debug artifacts/previews.

Это прямое следствие INV-008.

## Fingerprint

`generation_config_fingerprint` вычисляется SHA-256 от canonical serialization только `semantic` projection. Он записывается в `DomainData.provenance` для replay diagnostics.

Exact procedural replay Core 0.1 определяется semantic inputs, exact generator version и versioned RNG semantics; observability settings к этому набору не относятся.
