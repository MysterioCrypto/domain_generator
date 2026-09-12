---
id: ADR-0010
kind: architecture-decision
status: accepted
normative: true
scope: core
---

# ADR-0010 — RNG protocol v1

## Контекст

ADR-0003 зафиксировал независимые RNG-потоки по semantic namespace, но не определил byte encoding namespace, derivation hash, инициализацию состояния, алгоритм PRNG и семантику примитивных операций sampling. Без этого точный replay остаётся зависимым от деталей конкретной библиотеки.

## Решение

Core 0.1 использует versioned RNG protocol `rng_version = 1`.

### Корневой seed

`root_seed` интерпретируется как unsigned 64-bit integer:

```text
0 <= root_seed < 2^64
```

RNG implementation отвергает значения вне диапазона. До появления compiler это является runtime boundary `RngFactory`; compiler должен отклонять неподдерживаемый seed до generation.

### RngKey

Один логически независимый random stream адресуется структурой:

```text
attempt_index : uint64
stage         : semantic stage id
scope         : tuple[str, ...]
purpose       : str
```

Семантические id стадий v1:

```text
global
layout
terrain
hydrology
surface
placement
```

`scope` содержит хотя бы один непустой UTF-8 component. `purpose` непустой. Feature ids, имена parameters и другие машинные идентификаторы могут входить в scope; labels/tags/presentation metadata не входят.

### Каноническое кодирование namespace

Вход hash кодируется без JSON и без строк, соединённых separator-ом.

Порядок bytes:

```text
MAGIC                     = UTF-8 bytes `domain-generator-rng` + NUL
rng_version               = uint16 big-endian
root_seed                 = uint64 big-endian
attempt_index             = uint64 big-endian
stage                     = encoded_string
scope_count               = uint32 big-endian
scope[0..n-1]             = encoded_string...
purpose                   = encoded_string
```

`encoded_string`:

```text
byte_length               = uint32 big-endian
payload                   = exact UTF-8 bytes
```

RNG v1 не выполняет Unicode normalization: точная последовательность code points является частью машинной идентичности.

### Derivation

Bytes namespace хэшируются:

```text
BLAKE2b
  digest_size = 32 bytes
  person      = ASCII `dg-rng-v1`
```

Digest является 256-bit initial state material.

### PRNG

Конкретный генератор stream: `xoshiro256**`.

32-byte digest делится на четыре последовательных 8-byte слова, каждое читается как unsigned uint64 big-endian:

```text
s0 = digest[0:8]
s1 = digest[8:16]
s2 = digest[16:24]
s3 = digest[24:32]
```

Если все четыре слова равны нулю, нормативный fallback:

```text
s3 = 0x9E3779B97F4A7C15
```

Все операции xoshiro выполняются modulo `2^64`.

### Примитивные операции sampling

Базовый низкоуровневый primitive:

```text
next_u64() -> 0 .. 2^64-1
```

Uniform float `[0,1)`:

```text
uniform01 = (next_u64() >> 11) / 2^53
```

`uniform(a,b)` использует один `uniform01` и mapping:

```text
a + (b - a) * u
```

Целочисленный включительный диапазон `[a,b]` использует rejection sampling; modulo bias запрещён.

`choice(sequence)` использует `integer_uniform(0, len(sequence)-1)`.

Алгоритмы sampling являются частью `rng_version`. Их изменение требует новой версии RNG protocol даже при неизменном public API.

### Гранулярность streams

Отдельный stream создаётся для логически независимой random task, а не для каждого draw.

Хорошо:

```text
(feature, mountain-01, parameter, width_km) / sample
(feature, mountain-01, geometry, centerline) / control-points
(feature, fort-01) / site-selection
```

Плохо:

```text
all-layout / every feature
```

Порядок draws внутри одного локального stream является частью реализации этой random task, но не влияет на соседние namespaces.

### Независимость от значения parameter

Resolved bounds/values parameter не входят в namespace. Если диапазон параметра меняется, тот же stream variate отображается в новый domain; это сохраняет причинную стабильность.

### Граница observability

Logging/debug/export/preview code не должен потреблять semantic RNG streams. Observability не влияет на branch decisions или принятый результат.

## Требование golden vector

Implementation должна иметь fixed test vector, фиксирующий минимум:

- canonical namespace bytes;
- BLAKE2b-256 digest;
- initial xoshiro state;
- первые несколько `next_u64()`;
- первые несколько `uniform01()`.

Любое изменение этих значений при `rng_version = 1` является несовместимым изменением.

## Следствия

- RNG replay не зависит от `random.Random`, defaults NumPy generator или порядка выполнения независимых подсистем.
- Изоляция feature/parameter проверяется тестами.
- Новый PRNG/hash/encoding/sampling mapping требует `rng_version = 2`.
- ADR-0003 остаётся общим архитектурным принципом; этот ADR определяет его точный protocol v1.
