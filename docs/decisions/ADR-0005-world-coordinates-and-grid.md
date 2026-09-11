---
id: ADR-0005
kind: architecture-decision
status: accepted
normative: true
target: core-0.1
---

# ADR-0005: World coordinates and raster grid

## Context

Пользовательские spatial constraints должны читаться как обычная карта, а raster storage не должен протекать в публичный контракт.

## Decision

- world origin: southwest;
- `+x`: east;
- `+y`: north;
- пользовательская геометрия задаётся в километрах или normalized coordinates;
- `DomainSpec` использует `width_km`, `height_km`, `cell_size_km`;
- raster использует `row/column` только внутри Grid/field layer;
- `row 0` соответствует северной строке raster;
- world ↔ raster conversion централизован в Grid;
- размеры домена в Core 0.1 должны делиться на `cell_size_km` без остатка.

## Consequences

Human-facing directions остаются естественными (`southwest -> northeast` означает диагональ вверх-вправо), а NumPy/image indexing изолируется как техническая деталь.