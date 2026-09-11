---
id: CONTRACT-DOMAINDATA-0.1
kind: contract-draft
status: draft
normative: false
target: core-0.1
---

# DomainData v0.1 — draft

`DomainData` описывает принятый сгенерированный мир. Он не обязан хранить историю всех попыток и внутренние детали алгоритмов.

## DomainData и DomainBundle

`DomainData` — логическая структурная модель результата.

`DomainBundle` — физический набор файлов, например:

```text
output/
├── manifest.json
├── domain.json
├── fields/
│   ├── elevation.npy
│   ├── water.npy
│   ├── moisture.npy
│   └── vegetation_density.npy
├── cache/
│   ├── slope.npy
│   ├── flow_direction.npy
│   └── flow_accumulation.npy
└── debug/
    ├── generation-plan.json
    ├── layout.json
    └── validation.json
```

Крупные raster fields не должны встраиваться как огромные JSON-массивы. `domain.json` хранит metadata и ссылки на array-файлы.

## Категории данных

### Canonical

Изменение этих данных означает изменение самого домена. Для baseline Core 0.1 сюда относятся:

- elevation;
- water;
- moisture;
- vegetation density;
- semantic/vector features;
- river network;
- lakes как semantic features;
- окончательная geometry dependent features.

### Derived

Можно пересчитать из canonical data без изменения идентичности домена:

- slope;
- flow direction;
- flow accumulation;
- другие public caches.

### Debug/Internal

Алгоритмические промежуточные структуры, не являющиеся частью мира:

- feature masks;
- distance fields;
- noise layers;
- temporary basin/routing masks;
- attempt-local intermediate fields.

## Fields, networks, features

`DomainData` объединяет три представления:

- fields — численные пространственные данные;
- networks — связные структуры, прежде всего river network;
- features — семантически значимые объекты.

Одно явление может иметь несколько представлений. Например lake одновременно участвует в canonical water field и существует как semantic area feature с boundary/properties.

## Source of truth

`domain.json` + referenced canonical arrays являются источником истины. PNG previews/debug images только отображают данные и не могут переопределять мир.

`GenerationPlan`, rejected candidates и подробные traces могут входить в debug bundle, но не являются частью канонического `DomainData`.