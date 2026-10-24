# W4 — source-derived west reed court candidate

Built from `8e0f7ca21638cd39198606a3301b6c90afd1bdcb` on
`game/yuga-native-production`. Four reviewed bank features are now integrated
by default in offline Confluence. The root and independent reviewer accepted
this bounded source reuse after viewing all six matched originals. The original
map manifest, eight authority solids, eight decks and ten anchors are unchanged.
The existing army receives four additional private ground footprints. A finished
wet district, normal-input water-court journey and physical-GPU qualification
remain open.

The user asked to reuse existing assets and code rather than build another
primitive map library. This work selects **29 whole existing components** from
the original CC0 courtyard: one 19-component carved corner-column assembly and
one 10-component brass diya assembly. The two immutable prototypes are placed
twice each on the banks of the already-existing shallow west reed court. The
three visual families are carved vertical markers, low warm brass diyas, and
existing reeds/lotus. There is no second giant gate, wall across the crossing,
new generated mesh, water plane, foliage duplication or point light.

## Placement and physical contract

| Element | World base position (m) | Original source assembly |
| --- | --- | --- |
| North bank marker | `(-62.5,0,5)` | Courtyard corner column centered `(18,0,20)` |
| South bank marker | `(-62.5,0,-5)` | Same immutable source resources |
| North bank diya | `(-59.8,0,5.2)` | Courtyard lantern centered `(12.7,0,20)` |
| South bank diya | `(-59.8,0,-5.2)` | Same immutable source resources |

All placements are rigid metre/Y-up translations. UVs, normals, tangents,
materials and whole triangles remain from the source. Column height is 3.31 m;
its ground base is 1.2 × 1.2 m. The diya's structural base is 0.48 × 0.48 m and 1.075 m
high; its decorative upper crown has the original source's non-colliding policy.
One collision body per instance uses exact selected `COL_` source triangles.
There are no filled AABBs across the space between columns.

The existing water plane at `(-60,.012,0)` is a cosmetic wet film over the same
flat y0 ground. It already shows a dry cross-mid walking strip; this module does
not invent deep water, swimming, elevation or a new step. Existing reeds/lotus,
water shader/material and the floor body retain their identities. The candidate
preserves a four-metre crossing at z[-2,2], actual hero radius 0.65 m, and a 4 m camp
clearance ring around `(-54,0,0)`.

The shared helper defaults off and requires explicit opt-in plus an identity-transform
parent. The reviewed production caller now opts in during normal world setup. Source root/cluster/collider transforms must remain unchanged when
preparing army footprints. Four conservative source ground footprints are added
to a deep copy of the caller's already-prepared native manifest; earlier gate
and relay additions must be retained. This uses the existing planar army API,
not a new 3D authoritative collision model. Shared meshes, materials and shapes
are immutable; instance nodes/bodies remain private.

## Measured candidate costs

- Native scene: 3,474,458 bytes, SHA-256
  `69cebe64d18b6acadc16c5b43c2d4fd4ae069793590a909f2b636ba81cc64dd0`.
- 2,688 visible triangles and 760 actual collision triangles across four instances.
- 14 mesh instances, 7 shared mesh resources, 5 material resources, 2 shared immutable
  collision shapes and 4 private static bodies.
- Bundled native scene with zero external resource dependencies. No whole
  courtyard GLTF parse during opt-in mounting.
- No added light, water plane, texture source, foliage or new LOD. Native export
  contains selected source textures; “zero source bytes copied” describes intake
  links/selection, not zero derived-cache output bytes.

These are static resource counts, not measured GPU memory/frame-time results.
The small repeated prototypes intentionally share resources; resource sharing
alone does not establish lower draw-call count.

## Executed evidence and remaining review

`evidence/selection.json` pins source component IDs/region and provenance.
`evidence/bake.json` records actual native load/cache export.
`evidence/mount-probe.json` records 17/17 focused cache/copy/placement checks.
`evidence/preflight-r2.json` records 34/34 full-world headless checks: 225 actual hero
capsules, 73 camp-ring samples, 18 real floor rays, 90 spring-camera sweeps, all three
lanes/rotations plus wet crossing, actual column/low-diya cover, existing 35 army
boxes plus four candidate footprints, exact previous body identities, and
injected broad-blocker/copy/hash/duplicate controls.

The first full-world preflight failed 33/34. Its broad-blocker negative exposed a
fixture error: the manifest cross-mid route ends at x-54, while this wet crossing
extends west to x-66; Godot `cast_motion` also does not report initial overlaps.
The corrected fixture includes the explicit wet crossing and pairs an initial
`intersect_shape` query with each cast. The failed receipt and exact failed
capture source are retained. No geometry was changed to make the test pass.

The focused 17-check successor also refuses moved root, rotated parent, moved
source cluster/body, shifted footprint metadata and nonfinite values, then
proves restoration and copy isolation. These changes were requested by independent
review; the earlier 34-check preflight retains its earlier mount source pin.
The six actual 960 × 540 originals in `views/` passed 46/46 capture/physics/state
checks in 52.667 seconds on the qualified two-thread llvmpipe runtime. They are
three baseline/candidate pairs: ordinary west day/night and a north-bank detail.
Both reviewers accepted the four features and clear crossing. They did not accept
a finished district or commercial art parity. These R1 views held the old spawn
HUD label and Golden-hour status during staging; they are geometry comparisons,
not current gameplay screenshots. The exact rendered capture and reviewed mount
sources are retained as `.gd.txt` files and hash-match the original receipts.

The current implementation lives in `scripts/lanka_water_garden.gd`; the tool's
mount file is a two-line wrapper, not another implementation. Production appends
four garden footprints after the existing ten gate footprints, and the existing
relay setup appends nine, for 39 total army boxes (8 authority + 8 decks + 10 gate
+ 4 garden + 9 relay). No source manifest or army script is edited.

Current frozen integration checks:

| Check | Result | Evidence |
| --- | --- | --- |
| Actual garden opt-out and fresh production caller; full paths/cover/copy negatives | 31/31 | `evidence/integrated-r1.json` |
| Existing gate integration with new default garden preserved | 23/23 | `evidence/gate-combined-r1.json` |
| Unchanged strict world resource suite | 40/40 | `evidence/resources-r1.json` |
| Retained legacy floor-envelope suite, explicit gate/garden opt-out | 29/29 | `evidence/legacy-physics-r1.json` |

Frozen world SHA: `6869d536495760ad1b97e2ecde22547be31255aeace0e09e6adbc5943c368b77`.
Canonical helper SHA: `84f306a9caf021c1bbf602d0059abbd42129d20e49cc62df775aa04ba023dfde`.
Later root-composed proofs must name their own source; older receipts are not
relabeled. The integration test checks the actual default world and original
identities, while the legacy floor oracle deliberately retains its prior scope.

The three-view integrated correction uses the actual existing UI owner
`scene._process(.13)` after staged hero/phase changes and checks district, minimap
and status against real values. Its headless preparation passed 18/18. The three actual integrated originals
in `views/integrated-r1/` passed 24/24 image/state/UI checks on the later composed
world `178e73e34ec538180709e358824c45b71edd56a4484f86d118e828b7763d0f60`.
The root's new camera-helper source is separately pinned in
`evidence/integrated-camera-pin.json`.

**That corrected capture failed its process-exit deadline.** The engine printed
completion after scene teardown and eight process frames, then remained alive
until the 240-second wrapper stopped its owned processes. The actual originals
and successful in-engine checks are retained alongside the failed wrapper; this
is not a passing end-to-end execution. No script error or causal code defect was
established. The successful six-view capture used the same teardown order. The
root prioritizes the separate normal-input Quit gate; no speculative sleep,
forced-success exit or runtime edit was added.

- [Current staged day view](views/integrated-r1/integrated-ordinary-west-day.png)
- [Current staged night view](views/integrated-r1/integrated-ordinary-west-night.png)
- [Current bank detail](views/integrated-r1/integrated-north-bank-detail.png)

These images are suitable as labeled staged visual evidence, with the shutdown
failure disclosed. They do not qualify a downloadable executable or hardware
performance.

## Reproduce and next owner

[Tool commands](../../../../tools/lanka-water-garden/README.md) and
[licence distinctions](NOTICE.md) own the reproducible procedure. The root must
serialize heavy native captures with hero/W2 work. The capture helper reuses
existing matched-view machinery and retains actual ordinary shoulder-camera
coordinates; scene callbacks and water animation are held explicitly. These
views are staged diagnostics, not real input.

Next gates: resolve or bound the software-render exit failure; ordinary hero input and combat
around the wet court; placement/contact/readability with live units; combined
package inclusion and execution. Do not repeat this small module over entire
districts. Distance/motion/material coherence and physical-GPU costs remain
unmeasured. The broader N4 district and full-game milestone remain open.

## Next duplication reduction

`evidence/texture-reuse-r1.json` compares exact decoded source-image contents in
the existing self-contained gate and garden scenes. Each scene contains the same
12 distinct images: 9,437,184 decoded bytes overlap. Per-instance garden sharing
is proven, but cross-module image sharing is not implemented. A later shared
texture/palette resource pass should retain exact pixels, material channels,
collision and appearance, then verify live resource identity and package size.
This count is not physical-GPU memory or timing evidence. The frozen accepted
runtime is unchanged by the diagnostic.
