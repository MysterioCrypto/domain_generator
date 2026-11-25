# P4-L — slope-aligned local relief counterfactual (2026-11-25)

**NONCANONICAL, negative product result, PR #103 draft/open/unmerged.** P4-K HEAD 9be57779cb5c5d258acc1433eb68f26bb0e57df5 all three CI GREEN. Accepted dev/0.2, frozen release, A8/A12 sources and author geography unchanged.

## Hypothesis and controls
Use the original PRIVATE Region A 231×231, 1 km, relief_strength=2.0, threshold=30 km². Rebuild the original analytic source terrain and require all six source arrays bit-exact; verify original child/projected archive SHA against P4-K, independently replay every original channel projection array, then independently reroute the alternate terrain using existing Core. The intervention smooths the original local detail along the interpolated parent slope orientation with five offsets [-4,-2,0,2,4] km and fixed weights [1,4,6,4,1]/16. Remove the bilinearly interpolated filtered value at macro stations so the continuous candidate detail vanishes at those stations. Use an 8 km smoothstep boundary blend to the original detail and the source coastal taper. Solve one gain for exact equal whole-land detail RMS (gain 1.069372346), not optimized on network outcome. Guard 60 m maximum height change, exact raster boundary elevation/detail, exact original land sign, continuous station heights within 1e-6 m. No A8 D8 carving, no flow-network input to terrain shaping.

The slope direction is from interpolated source-station gradients in the same metric chart, not a physical erosion trajectory. This is local crop-only, not an overlap-seamless planetary generator. Directional roughness is a 2 km bilinearly sampled increment RMS on identical interior cells, not a measured valley-connectivity or geological validation. Strict raw pits are cells strictly below all eight immediate neighbors, not a count of real lakes. Original macro/child boundary provenance verified through replay and P4-K, source hashes recorded in output. The experiment region is entirely land, so preservation of its land mask does not prove coastal behavior on a coastal fixture.

## Real Region A results
| Metric | Original | Candidate |
|---|---:|---:|
| Whole-land detail RMS, m | 7.492951 | 7.492951 |
| 2 km along-slope detail increment RMS, m | 2.669617 | 1.885787 |
| 2 km across-slope detail increment RMS, m | 2.879653 | 2.652337 |
| Strict raw interior pits | 476 | 182 |
| Ordinary channel edges | 5868 | 5992 |
| Model channel cells | 5893 | 6019 |
| Ordinary raw nondescending edges | 1076 | 737 |
| Fraction of edges in maximal same-heading runs >=8 (P4-H partition) | 15.7805% | 27.6202% |
| Max run length in edges | 29 | 29 |
| Boundary endpoint count | 25 | 27 |

63 continuous macro elevation anchors: 0 m absolute error. Raster boundary elevation and local detail bit-exact. Maximum height change 9.158976 m, RMS height change 1.303756 m. 21 common boundary endpoints, channel mask IoU 32.0474%, so unchanged boundary elevations do not imply unchanged outlet topology. No lake proxies in either model. Area ledger balances to ~1.1e-10 km²; no external area injected. Source fields and accepted routing not edited.

**Decision: reject slope-aligned smoothing as the new terrain generator.** Lower pits and fewer nondescending raw channel steps are favorable diagnostics, but longer coherent directions reinforce the grid-aligned artificial regional morphology. The trade-off persists with equal detail RMS, unlike a simple amplitude sweep. Not all anisotropic terrains or erosion methods are rejected by this one example. The maps are model-channel diagrams with common relief color scale and identical rendering settings; no physical water/permanence/Q/accepted terrain. No author POI/route placement.

## Evidence
[Private derived ZIP: comparison PNG, two candidate NPZ, audit JSON with SHA](https://drive.google.com/file/d/1YlngHFHwaYiZnF9IRgBU_R6N5Bfl7A84/view). No private arrays in GitHub. Public script scripts/compare_region_anisotropic_detail_v02.py blob 0197173e5350523c55015f1b0a49f2e6f81b2ee1, tests/test_region_anisotropic_detail_v02.py blob 6c25e72d032c425a8c2e0521e99a5953353746d1. 8 local tests passed including continuous source anchor checks, equal RMS, frozen boundary and arrays, tamper rejection, independent Core reroute and bit-identical CLI on synthetic fixture. Geographic workflow explicitly includes these tests. Remote CI separate.

## Next P4-M
Do not start another blind noise/anisotropy sweep. Test one controlled spatial-resolution counterfactual: sample the SAME original analytic Hermite + local detail terrain at 1 and 0.5 km on identical extent, fixed source anchors, physical extraction threshold, same Core. Verify nested height samples and area ledger; compare physical-length straight chains (not equal number of links), outlet shifts in km, and actual map appearance at the same scale. This separates sampling/one-receiver quantization from the continuous relief hypothesis before considering erosion. A change of resolution does not establish physical rivers or approved geography. No canonical Core change or merge.
