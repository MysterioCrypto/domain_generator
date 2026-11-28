# P4-O — full native hydrology on imported DEM (2026-11-25)

**Experimental, not canon; PR #103 draft.** Author correction of 2026-11-25 applies: draft geography is freely revisable; Chapter 1 geography and planetary atmosphere are the binding author constraints. P4-M terrain is a convenient controlled input, not a fixed author map. Previous HEAD 947956ee all three CI GREEN.

## Experiment
Use SHA-verified P4-M 461×461 / 500 m inland DEM, 230.5 km full-cell extent. Compile a real 0.2 GenerationPlan without features/constraints; import TerrainState into generate_hydrology_v02, then run the actual validate_hydrology_v02. The mandatory unused terrain/climate spec values are technical placeholders, not author profile. Same area threshold 30 km², lake threshold 16 km² / 10 m. This is a hydrology-stage experiment, not complete DomainData generation. No accepted Core code edits. Native generation produces both regional and potential networks. Native regional validation fails; rebuild the regional graph using the existing build_continuous_river_network with normalize_false_confluences=True, rebuild corresponding stream mask/water depth, revalidate experimental state. No force-fit to old raster graph.

## Evidence
| Metric | Native regional | Normalized regional |
|---|---:|---:|
| Core hydrology invariants | 18/19 | 19/19 |
| Nodes | 966 | 871 |
| Segments | 936 | 841 |
| Sources | 483 | 483 |
| Confluences | 452 | 357 |
| False confluences (indegree <2) | 94 | 0 |
| Domain outlets | 25 | 25 |
| Lake inflow/outlet | 5/1 | 5/1 |
| Length km | 7131.551 | 7058.239 |
| Individually non-simple segments | 0 | 0 |

Native regional failed only hydrology-v02-river-network-invariants. Existing normalizer removes 95 confluence descriptors including cascade; normalized candidate passes all 19 existing invariants. Potential: 2147 nodes, 2088 segments, 1221 sources, 866 confluences, 46 domain outlets, 13 lake inflows, one lake outlet, 11006.620 km, zero false confluences and non-simple segments. Lake raster support 181.75 km², max modeled depth 10.2036m. One lake, not actual water permanence. Full spatial pair intersection/overlap audit exceeded time budget on first attempt and was omitted on completed run; null metric, not zero. Archived P4-M MFD array did not exactly match the native float64 array (archive stores float32); reason not fully isolated, no claim of equal accumulation values. Same DEM and extraction settings, not proven identical intermediate fields. Map uses identical DEM/background, common geometric lake fill and comparable width classes (catchment proxy, NOT discharge). Right panel substantially less angular; terrain still needs more expressive regional morphology. Chapter 1 compatibility not verified. No automatic acceptance.

## Reproduction
4 local synthetic tests pass (plan dimensions, invalid input, actual generation/normalization and immutable source). Script blob 2765e7646bcf69c10736804386f8b526a537d64b; tests 08632b0d55bf1f0f8f69b5f4549b9e22f5262a36; CI integrated. [Private archive](https://drive.google.com/file/d/1vIsm_2-toDzA1d3ZhXl150tHgSrQSL61/view) SHA-256 65b46da8789f8adc9f8d4c36e5b940ad64bb0021c25c30344fa71c03574d9ab6 contains comparison PNG, native/normalized/potential network JSON, lakes and audit; no private DEM in repo. Core dev/0.2 and release not modified in this iteration, not a prohibition on future improvements.

## Next P4-P
Address the actual native regional assembly problem as one meaningful slice: bounded regression and spatial overlap/crossing audit on the normalized candidate; determine whether the existing normalizer can be made the standard regional assembly behavior with explicit compatibility testing, not silently change accepted software. If graph overlap prevents a usable map, fix that mechanism; no obsolete graph preservation requirement. Then prioritize representative cartographic geography rather than further isolated smoothing. Before author map acceptance, extract Chapter 1 actual hard spatial constraints from private source; draft terrain can be regenerated. No merge without explicit acceptance.
