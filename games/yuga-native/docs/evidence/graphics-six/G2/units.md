# G2 / worker 05 — infantry shape, finish and bow timing

G2 source is frozen after 64/64 focused headless checks. This round narrows and layers the infantry silhouette and removes the duplicated nocked/flying arrow. Combat authority, damage commitment, movement, colliders, army caps and vehicle source are unchanged. Candidate G2 pixel and continuous-motion review belongs to the central capture.

I directly opened the actual G1 [day original](/tmp/yuga-g1-native-r1/03-world-day.png) and [night original](/tmp/yuga-g1-native-r1/04-world-night.png). Their hashes are retained in [units-source.json](units-source.json). The near day troops have fuller volume than the old cylinders, but broad red tunics and round gold shoulder caps still dominate; fine chest detail contributes little at the ordinary camera. The night troops are farther away because simulation advanced, so these two originals do not establish a matched-distance day/night comparison. Both retain a segmented, stylized appearance; G1 is a bounded silhouette improvement, not finished character-art acceptance.

The new geometry narrows chest, waist and shoulder spacing, replaces shoulder balls with tapered overlapping guards, and adds convex beveled armour plates on both front and back. The following gameplay camera primarily sees the soldiers' backs, so those surfaces now receive raised straps and three curved lamellae. Pleated cloth remains visible below the belt. Melee soldiers gain shaped helmets and cheek guards; archers retain cloth headwraps, rolled sleeves and leather protection. Metal, leather, skin and cloth use distinct roughness values instead of one common matte treatment. Shared coloured material resources retain Sun ochre/rust and Moon blue/steel identity. These are original procedural shapes with no downloaded textures or assets.

The arrow's cosmetic sequence is now 0.12 seconds of draw followed by 0.14 seconds of travel, ending at the unchanged 0.26-second committed hit. The nock and flying tracer are mutually exclusive. Travel begins at the actual drawn shaft centre and ends at the committed target point. `lane_minion.gd` delegates this presentation to `lane_infantry_art.gd`; the helper uses the supplied remaining attack time without timers, callbacks, damage calls or history from previous frames. Pause, death and recreation therefore cannot leave a second arrow behind. Actual army execution still uses its existing fixed-step schedule; the visual code does not alter the attack receiver or resolve a new hit.

| Current assembled infantry | Mesh instances | Surfaces | Triangles |
| --- | ---: | ---: | ---: |
| Spearman | 19 | 45 | 10,704 |
| Bow guard | 20 | 44 | 8,560 |
| Commander | 22 | 49 | 11,316 |

Both teams/all roles warm 44 assembled meshes, 58 primitive/profile meshes and 12 materials. The existing G1 caps remain unchanged: 24 instances, 65 surfaces and 15,000 triangles per role; 45 shared assembled meshes, 80 primitives and 12 materials overall. Ninety-six concurrent assemblies reuse the warmed resources; pose sampling creates no mesh/material resources, and disposal returns node counts to entry. Broad armour layers remain at normal unit visibility distance; the smaller collar/face/shield trim retains the documented 42 m cutoff with hysteresis. These counts do not establish hardware performance.

Executed using Godot 4.6.3, headless on CPU 2, with no imports or renderer:

```sh
taskset -c 2 godot --headless --path games/yuga-native \
  --script res://tests/graphics_infantry_cases.gd -- --report=/absolute/fresh/infantry.json
taskset -c 2 godot --headless --path games/yuga-native \
  --script res://tests/graphics_infantry_timing_cases.gd -- --report=/absolute/fresh/timing.json
```

[Geometry/resource/receiver 53/53](units-checks/infantry-r1.json) preserves the existing finite geometry, cap, cache, disposal, clock freeze, invalid-input, hand/string contact and receiver/collider gates. [New timing/material 11/11](units-checks/timing-r1.json) samples both sides of release and impact boundaries, proves no duplicate arrows, checks release-centre continuity and travel endpoints, holds the same clock for 120 samples, applies actual lethal damage, and recreates eight units across 24 attacks. It also checks actual shared material finish values. All final engine logs are clean; no failed G2 execution was discarded. These are explicit presentation samples on real unit receivers, not a claim that an actual rendered combat sequence was viewed.

The [source comparison](units-checks/rule-source-invariance.json) proves the original stats, collision setup, all rule functions and complete `lane_army.gd` remain byte-identical. Only `_ready` and `update_pose` differ from the pre-campaign minion source. Root was notified of the new whole-file minion hash and owns the intentional unreleased content 7 pin update; this worker did not edit manifests.

Full-scale render questions for the next owner: at the ordinary following camera, do the narrower back/waist, raised straps, shoulder guards and cloth separation read without becoming glittering detail? Compare both teams and all three roles in one mixed group at near and ordinary distances. Verify archer versus shield infantry versus commander identification with HUD bars ignored, then inspect the same stationary group in day and night. A real march→attack→death clip should show one arrow through draw/release/impact, correct hand contact, stable pause, no persistent dead arrow, and clear reentry after reset. The 38–46 m bidirectional detail-cutoff witness remains open. No high-quality-hero or commercial-art parity claim is made.

Frozen SHA256:

```text
a64b4cc283dc7b5c4eb28391ec362928a9fb3126e2a1d41ae5cc27e0a67ae6f2  scripts/lane_infantry_art.gd
90fe2d84f5c408b4b99779b00c11e59e850c1bb4f88dafb42a8a5aba74cc119c  scripts/lane_minion.gd
ac78ef11354adecb60fabf0b7e9b060585be42168eac184cc67c09b9b36e0fb1  scripts/lane_vehicle_art.gd (unchanged from G1)
```

CPU 2 is released to the motion worker; no owned engines remain. G2 stops here for rendered feedback. No commit, shared ledger, hero, world, UI or motion-owner source edits were made.
