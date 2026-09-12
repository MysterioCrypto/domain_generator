---
id: CONTRACT-GENERATIONCONFIG-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# GenerationConfig v0.1 — черновик

`GenerationConfig` описывает политику исполнения, а не сам мир. Он разделён на semantic settings и observability settings.

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

## Семантические настройки

`max_attempts >= 1` — максимум независимых attempts с индексами `0..max_attempts-1`.

`target_valid_candidates >= 1` и `<= max_attempts` — сколько валидных candidates собрать до детерминированного ranking. Значение `1` естественно даёт семантику «первый валидный»; отдельный selection mode в Core 0.1 не нужен.

Pipeline прекращает запуск attempts, когда достигнут `target_valid_candidates` либо исчерпан `max_attempts`.

Если валидный candidate не найден, generation завершается `GenerationFailure` с diagnostic summary; это не `DomainData`.

Оба semantic поля участвуют в семантике generation и могут изменить принятый attempt, поэтому canonical semantic config fingerprint включает их.

## Настройки observability

Флаги observability/debug могут расширяться без изменения семантики generation. Они:

- не входят в semantic config fingerprint;
- не потребляют semantic RNG streams;
- не могут менять branch decisions, ranking или принятый результат;
- управляют только logs/traces/debug artifacts/previews.

Это прямое следствие INV-008.

## Fingerprint

`generation_config_fingerprint` вычисляется как SHA-256 от canonical serialization только проекции `semantic`. Он записывается в `DomainData.provenance` для диагностики replay.

Точный procedural replay Core 0.1 определяется semantic inputs, точной версией generator и versioned RNG semantics; observability settings к этому набору не относятся.
