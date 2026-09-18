# Low-Bias Contributing Area v0.2

Status: **accepted design gate**  
Target branch: `dev/0.2`  
Supersedes the accumulation/channel-support backend of: `docs/design/continuous-drainage-routing-v0.2.md`  
Operator evidence: rejected H09 checkpoint from PR #72

## 1. Причина нового design gate

Первый H09 checkpoint Continuous Drainage подтвердил, что переход от D8 к continuous local direction существенно улучшает river geometry, но не устраняет систематический lattice imprint.

На representative Terrain 0.2 оператор видит:

- длинные прямые участки без terrain-driven причины;
- прямоугольно-ломаные / ступенчатые участки;
- подозрительно параллельные каналы;
- короткие искусственные ветви;
- тот же паттерн уже в contributing-area diagnostic до final vector rendering.

Следовательно, renderer и post-smoothing не являются корнем проблемы.

Текущая computational chain:

```text
continuous D∞-style local angle
→ at most two raster receivers
→ weighted raster accumulation
→ thresholded channel support
→ continuous vector tracing
```

Операторский REJECT относится к этой chain как к финальной Hydrology 0.2 base.

## 2. Внешняя техническая опора

Этот redesign не строится только на визуальной догадке.

Tarboton D∞ задаёт continuous flow angle, но contributing area обычно всё равно распределяется максимум между двумя adjacent downslope cells.

Prescott et al. (2025), *An evaluation of flow-routing algorithms for calculating contributing area on regular grids*, Earth Surface Dynamics 13, 239–256, DOI 10.5194/esurf-13-239-2025, показывает:

- D∞ может сохранять существенный cardinal/ordinal directional bias;
- классический slope-weighted MFD на ряде analytic и real-terrain tests даёт лучшую rotational invariance;
- для Freeman-style MFD exponent около `p = 1.1` является хорошо обоснованной low-bias точкой.

Это не означает, что MFD автоматически будет принят для Core. Он используется как следующий bounded experiment, который обязан пройти тот же operator-visible checkpoint.

## 3. Scope Batch B2

Меняется только transport/accumulation/channel-support часть Hydrology 0.2.

```text
conditioned elevation
→ low-bias multi-flow flux
→ mass-conserving contributing area
→ accepted lakes as routing supernodes
→ thresholded channel support
→ continuous semantic river tracing
→ H09-B operator checkpoint
```

Не меняются этим slice:

- Terrain 0.2;
- Priority-Flood physical fill semantics;
- public hydrology parameters;
- accepted-lake detection thresholds;
- one canonical spill outlet per accepted lake;
- DomainData river contracts;
- water-depth proxy semantics;
- Surface / Placement;
- artistic renderer.

## 4. Что сохраняется из PR #72

Следующие идеи остаются принятыми для redesign:

1. Continuous world-space direction field нужен и остаётся operator diagnostic.
2. Final RiverSegment geometry не должна быть D8 cell-center path.
3. Accepted lake является routing supernode.
4. Один accepted lake имеет ровно один canonical spill outlet.
5. Diffuse hillslope flow не сериализуется как downstream river bifurcation.
6. H09 diagnostic stack остаётся обязательным acceptance interface.

Rejected:

```text
two-receiver D∞ accumulation
as canonical contributing-area backend
```

## 5. Multi-flow flux field

Для каждого ordinary interior cell вычисляется доля outgoing flux ко всем strictly downslope nearest neighbours.

Fixed neighbour set — существующие 8 Moore-neighbours.

Для каждого neighbour `i`:

```text
drop_i = routing_elevation(current) - routing_elevation(neighbour)
distance_i = cell_size * {1 or sqrt(2)}
slope_i = max(drop_i / distance_i, 0)
weight_i = slope_i ^ p
p = 1.1
```

Если `slope_i == 0`, neighbour не получает flux.

Fractions:

```text
fraction_i = weight_i / Σ weight
```

Normative properties:

- every positive receiver is strictly lower on conditioned routing surface;
- fractions finite and non-negative;
- ordinary routable interior cell has sum(fractions) = 1;
- edge cells remain terminal domain exits;
- no RNG;
- traversal order cannot alter fractions;
- direction ordering is fixed and canonical;
- `p = 1.1` is fixed internal Core 0.2 semantics in this slice, not a new user-facing knob.

### Почему не adaptive exponent сейчас

Variable-exponent MFD может уменьшать dispersion в steep terrain, но одновременно снова меняет orientation bias.

Batch B2 намеренно проверяет простой, bounded и literature-backed baseline `p = 1.1`.

Если он визуально пере-диспергирует drainage, это будет основанием для следующего design gate, а не для скрытого tuning внутри implementation.

## 6. Continuous direction derived from flux

Canonical tracing direction должен быть согласован с тем же flux field, который создаёт accumulation.

Для cell:

```text
vx = Σ fraction_i * unit_dx_i
vy = Σ fraction_i * unit_dy_i
flow_angle = atan2(vy, vx)
```

Если resultant norm numerically collapses, используется deterministic fallback к neighbour с максимальной fraction; tie-break — fixed direction order.

Это сохраняет operator-visible continuous vector field, но больше не требует, чтобы canonical trace direction приходила из отдельного two-receiver D∞ representation.

Existing D∞ facet angle разрешается временно сохранять только как diagnostic comparison during H09-B; он не должен управлять accepted B2 accumulation.

## 7. Internal routing representation

Conceptual internal state:

```text
MultiFlowRoutingField
  fractions: float64[rows, columns, 8]
  flow_angle_rad: float64[rows, columns]
```

Receiver coordinates не обязаны сериализоваться: fixed direction index однозначно задаёт neighbour.

HydrologyState продолжает хранить canonical contributing-area raster:

```text
flow_accumulation_km2
channel_support_mask
river_network
```

Новый routing field internal-only и не расширяет DomainBundle contract.

## 8. Accumulation

Contributing area считается на weighted DAG.

Каждый ordinary cell получает собственную площадь:

```text
cell_area = cell_size_km²
```

и передаёт весь накопленный area downstream по MFD fractions.

```text
A(target_i) += A(current) * fraction_i
```

Required:

- exact deterministic replay;
- finite float64;
- mass conservation within numerical tolerance;
- no directed cycles;
- every ordinary cell area >= own cell area;
- no hidden renormalization based on domain-local output range.

## 9. Lakes

Accepted lake semantics из предыдущего redesign сохраняется.

Lake component:

- поглощает весь входящий MFD flux;
- агрегирует contributing area;
- не содержит semantic channel network внутри воды;
- имеет один canonical spill outlet;
- выпускает 100% aggregated catchment через этот outlet.

Outlet selection сохраняет existing physical saddle + deterministic tie-break semantics, если новый flux field не выявит конкретный invariant defect.

Return-flow fraction из outlet receiver обратно в ту же lake component запрещается и renormalizes remaining downstream fractions, аналогично текущей anti-cycle semantics.

## 10. Channel support

Initial channel support остаётся threshold-based:

```text
support(cell) ⇔ contributing_area_km2 >= stream_threshold_km2
```

Accepted lake interiors исключаются.

Важно: threshold semantics и units не меняются. Нельзя "исправлять картинку" простым изменением representative threshold без отдельной причины.

## 11. Semantic channel graph

Source/confluence candidate extraction должна использовать **тот же MFD flux graph**, который создал contributing area.

Weighted support indegree:

```text
number of supported upstream cells with positive MFD fraction into this supported cell
```

Это computational candidate layer, не serialized truth.

Final semantic graph по-прежнему обязан иметь:

- no ordinary downstream bifurcation;
- confluence indegree >= 2;
- no internal land dead end;
- one lake outlet per accepted lake;
- DAG topology.

False confluence normalization из PR #72 может быть сохранена, если tests/H09-B не показывают новый defect.

## 12. Continuous vector tracing

Final river geometry интегрируется в world space по bilinear interpolation нового flux-derived `flow_angle_rad`.

Это принципиально:

```text
accumulation flux
and
vector tracing direction
```

больше не должны происходить из двух несовместимых directional models.

Post-smoothing не используется как средство убрать grid bias.

Если final trace систематически покидает high-accumulation valley skeleton, это считается implementation defect и не лечится renderer.

## 13. Diagnostics

H09 diagnostic views становятся постоянным hydrology acceptance interface:

1. terrain + final rivers;
2. continuous flow-vector field;
3. raw contributing-area field;
4. channel support vs final rivers;
5. lake cells + canonical outlets;
6. statistics.json.

Для H09-B дополнительно нужен side-by-side с rejected PR #72 checkpoint на том же:

```text
180 × 120 km
seed 2026091402
cell size 1 km
same Terrain 0.2 request/presets
same hydrology thresholds
```

Без side-by-side нельзя считать визуальное улучшение доказанным.

## 14. Minimal automated gates

Автотесты остаются guardrails, а не acceptance substitute.

Нужны минимум:

### F01 — planar low-bias flux

Oblique plane, например 23°.

Проверяет:

- positive MFD flow distributed to all applicable downslope neighbours;
- fractions sum to 1;
- resultant angle близок analytic downslope direction;
- no D8-only quantization.

### F02 — rotational accumulation stability

Synthetic landform запускается в нескольких non-45° orientations.

Сравнивается contributing-area distribution в physically equivalent sample zones.

Gate должен ловить сильную cardinal/ordinal sensitivity, а не требовать bitwise equality rotated rasters.

### F03 — lake supernode

Сохраняет один outlet, aggregated catchment и отсутствие internal lake channel routing.

### F04 — branching valley

Два tributary valleys формируют confluence без downstream semantic split.

## 15. Operator acceptance gate H09-B

Implementation не принимается только потому, что F01–F04 green.

Оператору показывается same-world comparison:

```text
REJECTED two-receiver H09
vs
new MFD-flux H09-B
```

Primary visual questions:

1. Исчезли ли длинные lattice-driven cardinal/ordinal streaks из accumulation?
2. Стали ли tributary merges похожи на terrain-driven dendritic structure?
3. Остались ли необъяснимые parallel channels?
4. Остались ли rectangular/step-like runs без structural terrain cause?
5. Согласуется ли final vector river с bright accumulation corridor?
6. Не стала ли MFD сеть чрезмерно diffuse / "размазана"?

Only explicit operator `ACCEPT` allows implementation merge.

## 16. Stop rules

Если H09-B всё ещё grid-biased:

- не добавлять decorative smoothing;
- не подбирать p по одной representative картинке;
- следующий design рассматривает более continuous transport:
  - triangular MFD;
  - flow-tube / decomposed flux;
  - либо более physical iterative water-surface routing.

Если H09-B слишком diffuse:

- не возвращаться автоматически к D∞;
- сначала локализовать, diffusion возникает в flux, thresholding или semantic channel extraction.

## 17. Compatibility

- `release/0.1-prealpha` не меняется;
- Terrain 0.2 не меняется;
- public request schema в этом slice не меняется;
- DomainData / DomainBundle contracts не меняются;
- exact replay сохраняется within exact generator version;
- cross-version world identity не обещается.

## 18. Implementation boundary

После explicit design acceptance:

1. merge this docs-only design into `dev/0.2`;
2. synchronize implementation branch;
3. replace two-receiver accumulation backend;
4. preserve/reuse H09 tooling;
5. run minimal automated gates;
6. render H09-B same world;
7. stop for operator review.

Design explicitly accepted by operator on 2026-09-18. Production implementation may proceed in the implementation branch, but final Hydrology 0.2 acceptance still requires H09-B operator review.
