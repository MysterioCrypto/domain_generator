# Continuous Drainage Routing v0.2

Status: **accepted design gate**  
Target branch: `dev/0.2`  
Supersedes routing/geometry parts of: `docs/design/hydrology-river-geometry-v0.2.md`  
Experimental evidence: rejected implementation PR #70, preserved head `943efa776aed8190ba1e777e7465796bb00a3fe0`

## 1. Причина нового design gate

Предыдущий Batch B доказал, что проблема речной сети состоит из двух разных слоёв.

Lake/catchment semantics исправляются успешно:

```text
13 accepted lakes
23 lake_outlet nodes  →  13 canonical lake_outlet nodes
```

Но D8 остаётся систематическим источником grid bias. На representative Terrain 0.2 checkpoint:

```text
raw D8 grid-locked direction fraction       = 1.000
reconstructed vector grid-locked fraction  ~= 0.593
```

Constrained smoothing уменьшил staircase corners, но не устранил длинные horizontal / vertical / 45° runs. Это означает, что geometry reconstruction уже упёрлась в неправильную computational routing representation.

По stop-rule исходного Batch B дальнейшее декоративное smoothing запрещено. Меняется сам drainage backend.

## 2. Scope

Новый bounded slice:

```text
conditioned elevation
→ continuous low-bias drainage field
→ distributed flow accumulation
→ accepted lakes as routing supernodes
→ canonical single lake spill outlet
→ channelization support
→ deterministic semantic river topology
→ continuous world-space river traces
→ hydrology-only visual checkpoint
```

Pipeline order остаётся прежним:

```text
Layout → Terrain → Hydrology → Surface → Placement → Final
```

Новая generation stage не добавляется.

Не входят в slice:

- erosion simulation;
- rainfall/runoff climate model;
- hydraulic width/discharge simulation;
- deltas / braided rivers;
- ocean/coast model;
- shoreline smoothing;
- artistic cartography;
- Surface redesign.

## 3. Главная архитектурная граница

Core 0.2 больше не использует single-receiver D8 как canonical hydrology routing backend.

Нормативное разделение:

```text
Terrain elevation
      ↓
Priority-Flood conditioning
      ↓
continuous drainage field
      ↓
distributed accumulation field
      ↓
channelization / semantic topology
      ↓
continuous vector river geometry
```

**INV-HYD-012:** canonical 0.2 drainage direction не ограничена восемью D8 bearings.

**INV-HYD-013:** semantic river topology и RiverSegment geometry не могут реконструироваться из legacy D8 cell-center path как authoritative source.

D8 может существовать только как legacy 0.1 path или diagnostic comparison. Он не участвует в semantic 0.2 result.

## 4. Conditioning сохраняется

Существующий Priority Flood сохраняется как depression-conditioning mechanism.

Разделение остаётся:

- `fill_elevation_m` — physical depression-fill surface для lake detection;
- `routing_elevation_m` — техническая strictly-draining surface.

Terrain elevation не мутируется ради гидрологии.

## 5. Continuous routing backend

Canonical backend v0.2 — deterministic **D∞-style facet routing**.

Для каждой не-lake interior cell определяется непрерывный downslope angle по локальным triangular facets conditioned raster surface.

Результат cell routing содержит:

```text
flow_angle_rad
receiver_a + fraction_a
receiver_b + fraction_b   # optional
```

где:

```text
0 < fraction <= 1
fraction_a + fraction_b = 1
```

Если направление точно попадает на один neighboring receiver, второй receiver отсутствует и fraction = 1.

Edge cells могут быть terminal domain exits.

Tie-breaking facet/elevation cases фиксируется детерминированно через stable facet order и grid-coordinate order. Iteration order не влияет на результат.

**INV-HYD-014:** каждый positive flow fraction идёт только к strictly lower conditioned routing elevation либо в canonical lake supernode/domain exit.

## 6. Distributed accumulation

Catchment accumulation считается на directed acyclic weighted graph:

```text
A(cell) = cell_area + Σ A(upstream) * flow_fraction(upstream → cell)
```

Поэтому contributing area может быть fractional float64 и больше не обязана быть целым числом raster cells.

Required properties:

- finite;
- `>= cell_area` для ordinary cells;
- exact deterministic replay;
- total outgoing fraction ordinary routable cell = 1;
- mass conservation внутри numerical tolerance;
- no directed cycles.

`stream_threshold_km2` продолжает означать contributing area threshold. User-facing hydrology contract не получает новый routing-mode parameter в этом slice.

## 7. Lakes становятся routing supernodes

Эксперимент #70 подтвердил полезность single-outlet lake semantics, поэтому эта часть предыдущего design сохраняется, но внутренний D8 tree больше не нужен.

Accepted lake component является routing supernode:

1. любой D∞ flow, входящий в lake cells, поглощается lake supernode;
2. internal lake surface не содержит semantic channel routing;
3. весь accumulated catchment lake component агрегируется;
4. lake имеет ровно один canonical physical spill outlet;
5. 100% lake outflow продолжает routing через этот outlet.

Canonical outlet выбирается по physical spill saddle, conditioned downstream elevation и stable coordinate tie-break.

**INV-HYD-015:** один accepted internal lake → ровно один semantic `lake_outlet` и один downstream outflow path.

Таким образом сохраняется успешный результат #70 без искусственного raster tree внутри воды.

## 8. Channelization: diffuse flow и river topology — разные вещи

D∞ intentionally допускает split flow на hillslope. Это правильно для accumulation, но обычная semantic river network не должна автоматически превращаться в branching-downstream graph.

Поэтому вводится отдельный internal channelization pass.

### 8.1 Channel support

Initial channel support:

```text
channel_support(cell) ⇔ distributed_accumulation_km2 >= stream_threshold_km2
```

Accepted lake interiors исключаются.

### 8.2 Single downstream semantic continuation

После channelization каждый ordinary semantic channel trace имеет **ровно одно downstream continuation** до:

- confluence;
- lake inflow;
- lake outlet continuation;
- domain outlet.

Diffuse D∞ split не сериализуется как river bifurcation.

Конкретный deterministic projection weighted drainage field → single semantic continuation является implementation detail, но обязан выполнять следующие нормативные условия:

1. не использовать nearest D8 bearing как authoritative direction;
2. использовать continuous `flow_angle_rad` как geometric direction source;
3. не создавать ordinary downstream river bifurcations;
4. не создавать internal dead ends;
5. сохранять drainage order и lake semantics;
6. не зависеть от traversal order;
7. быть rotation/oblique-slope tolerant по acceptance fixtures.

Это оставляет implementation свободу выбрать facet-streamline tracing / deterministic channel capture без повторного contract design, пока invariants выполняются.

## 9. Continuous river tracing

RiverSegment.centerline строится непосредственно в world-space из continuous drainage field.

Нормативная схема:

```text
semantic start node
→ integrate deterministic downslope trace through routing facets
→ channel-support / topology anchors
→ semantic end node
```

Final centerline:

- endpoint-exact;
- finite;
- ordered downstream;
- inside domain;
- не проходит через unrelated lake;
- lake inflow заканчивается на lake boundary;
- lake outflow начинается на canonical outlet;
- no self-intersection;
- no adjacent duplicate points;
- не обязана проходить через raster cell centers;
- не ограничена multiples of 45°.

Post-smoothing допускается только как bounded numeric cleanup уже continuous trace. Оно не может менять topology и не является средством скрыть routing bias.

## 10. Semantic graph

Сохраняются node kinds:

- `source`;
- `confluence`;
- `lake_inflow`;
- `lake_outlet`;
- `domain_outlet`.

Graph invariants:

- DAG;
- every segment references existing distinct nodes;
- source indegree = 0;
- confluence indegree >= 2;
- ordinary land channel outdegree <= 1;
- domain outlet outdegree = 0;
- lake references valid accepted lakes;
- exactly one lake outlet per accepted lake;
- no visible channel silently terminates inside ordinary land;
- catchment does not decrease downstream along semantic continuation beyond numerical tolerance.

Braided rivers/deltas deliberately remain unsupported.

## 11. Internal state

0.2 implementation должна иметь explicit continuous routing diagnostics. Conceptually:

```text
ContinuousRoutingField
  flow_angle_rad: float64[rows, columns]
  receiver_a
  receiver_b
  fraction_a
  fraction_b
  distributed_accumulation_km2

HydrologyState
  fill_elevation_m
  routing_elevation_m
  continuous_routing
  channel_support_mask
  lake_candidates
  lake_outlets
  river_network
  water_depth_m
```

Точный Python container layout является implementation detail.

Legacy `flow_direction` может оставаться в 0.1 implementation path, но **не должен masquerade as canonical 0.2 routing state**.

Новые diagnostics internal-only и не требуют изменения DomainBundle manifest.

## 12. Water depth

Lake depth остаётся `fill - terrain`.

River depth proxy остаётся deterministic function of semantic/effective contributing area and existing hydrology parameters.

После lake supernode outflow использует catchment всего lake basin.

## 13. Determinism

Все routing decisions полностью детерминированы.

RNG для самого D∞ routing не требуется. Если implementation channel capture всё же нуждается в tie resolution, он обязан использовать stable semantic RNG namespace Hydrology и не зависеть от sibling draw order; предпочтение отдаётся deterministic geometric tie-break без RNG.

Exact replay обещается только в пределах exact generator version по INV-009.

## 14. Validation

Hydrology validation v0.2 обязана проверять минимум:

- continuous routing arrays finite where applicable;
- angles normalized to canonical interval;
- receiver indices valid;
- fractions finite, non-negative, sum to 1 for routable ordinary cells;
- every positive receiver is strictly downstream on conditioned routing surface;
- weighted routing graph acyclic;
- distributed accumulation finite and mass-conserving;
- channel support follows threshold semantics outside lakes;
- accepted lake supernode has exactly one outlet;
- lake outflow carries complete aggregated lake catchment;
- semantic river graph has no ordinary bifurcation or internal dead end;
- all centerlines endpoint-exact, finite and in-domain;
- exact replay reproduces routing field, accumulation and RiverNetwork;
- diagnostic rendering does not mutate semantic state.

## 15. Acceptance fixtures

Новый implementation PR обязан включать минимум следующие fixtures.

### H05 — oblique planar slope

Synthetic plane с аналитическим downslope bearing, который не кратен 45° (например 17°–30°).

Проверяет:

- continuous routing follows analytic direction;
- final river centerline не staircase;
- direction samples не collapse к D8 bearings;
- no internal dead ends.

### H06 — rotated basin equivalence

Один и тот же analytic basin генерируется в исходной ориентации и после non-45° rotation.

После обратного преобразования major drainage geometry/topology должна оставаться близкой в tolerance, выраженном в cell sizes, а не резко менять basin structure из-за ориентации grid.

Это главный автоматический anti-grid-bias test.

### H07 — lake catchment on continuous routing

Oblique basin + accepted lake.

Проверяет:

- multiple fractional inflows допустимы;
- один canonical lake outlet;
- полный catchment выходит через него;
- no semantic river through lake interior.

### H08 — branching catchment / confluence

Two upstream valleys merge into one trunk.

Проверяет:

- semantic confluence;
- no downstream split;
- downstream catchment monotonic;
- continuous centerlines remain topology-consistent.

### H09 — representative Terrain 0.2 visual checkpoint

Тот же 180×120 км representative terrain используется для честного before/after comparison с rejected #70 result.

Checkpoint содержит минимум:

```text
continuous drainage field diagnostic
channel support
final vector rivers
raw/support vs final overlay
lake outlets
statistics.json
```

Human review обязателен до merge implementation PR.

## 16. Grid-bias quality gate

На synthetic oblique fixtures hard acceptance строится не на субъективной красоте, а на analytic/rotation tests.

Representative-domain metric `grid_locked_fraction` остаётся diagnostic, а не универсальным physics invariant: реальная долина действительно может идти почти north/south/east/west.

Однако implementation PR не принимается, если representative visual checkpoint всё ещё демонстрирует систематические длинные 0°/45°/90° raster runs, аналогичные rejected #70.

Иными словами:

```text
synthetic anti-bias tests = automated hard gate
representative map       = human visual gate
```

## 17. Compatibility

- `release/0.1-prealpha` не меняется;
- 0.1 exact replay не переписывается;
- public DomainSpec/GenerationPlan hydrology parameters пока не расширяются;
- DomainData river node/segment contracts сохраняются;
- DomainBundle fields сохраняются;
- изменение generated world semantics допустимо в 0.2 по INV-009.

## 18. Implementation boundary

После acceptance этого design implementation выполняется отдельным PR.

Rejected experimental code #70 не cherry-pick-ается целиком. Разрешено заново перенести только доказанную semantics:

- canonical single lake outlet;
- lake catchment aggregation idea;
- hydrology-only checkpoint tooling/tests,

но D8 canonical routing, D8 lake interior tree и corridor-constrained reconstruction не считаются принятыми implementation решениями.

## 19. Stop condition

После implementation работа снова останавливается на hydrology-only checkpoint.

Surface/Placement не продолжаются, пока одновременно не выполнены:

1. H05–H08 automated invariants;
2. exact replay;
3. single-outlet lake semantics;
4. no ordinary downstream river bifurcation/dead-end;
5. representative human visual review показывает исчезновение систематического D8/grid-lock pattern.

Если это не выполнено, следующий шаг снова redesign routing/channelization, а не renderer smoothing.
