# G1 / worker 05 — units and props

G1 implements a new original infantry assembly and refines the existing siege vehicles. Runtime source is frozen for the central G1 render. The 122 headless checks pass; candidate pixel and continuous-motion acceptance remain pending. Start source: `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c`.

The actual baseline originals opened were the final Linux package's `08-package-world-live.png`, the historical army engagement original, and the historical siege frame90. Their exact hashes are in [units-source.json](units-source.json). In the current package image, nearby troops have cylindrical chests, straight dark lower legs, plain circular shields and sharply segmented bows. These are baseline observations, not new candidate acceptance.

`scripts/lane_infantry_art.gd` builds fitted chest/waist profiles, pleated wraps, layered sashes and lamellar plates, shaped forearms/calves, sandals, wrapped headwear, brows/noses/moustaches, domed studded shields, and leaf-headed spears. Archers have a continuous recurve bow, quiver/fletching, a nocked arrow and two string segments that meet the draw hand. Commanders retain an elevated split standard and gain a crown silhouette. Two-bone arm placement keeps the hands attached through bow draw and spear lunge. The existing army clock supplies all pose samples; there is no new clock or gameplay authority.

`scripts/lane_vehicle_art.gd` now uses beveled eight-spoke wheels, individual joined deck boards in one mesh, turned bronze cannon bands, rail straps/fasteners and a royal rosette. Vehicle recoil, wheel rolling, suspension/contact and radius constraints remain under the existing pose contract. No relay, hero, world, UI, physics, wave or combat-rule source was changed.

`scripts/lane_minion.gd` only changes the infantry art preload/handle and replaces inline infantry poses with the new helper call. Source comparison proves every other function, the stats table and collision-setup block are byte-identical; the entire `lane_army.gd` is unchanged. Its whole-file contract pin necessarily changes. Root owns the content 7 migration and package inclusion of the new script; the old `lane_unit_art.gd` remains untouched.

| Resource census, per assembled unit | Mesh instances | Material surfaces | Triangles |
| --- | ---: | ---: | ---: |
| Spearman | 17 | 38 | 10,140 |
| Bow guard | 19 | 42 | 8,644 |
| Commander | 20 | 42 | 10,752 |
| Cannon cart | 28 | — | 3,768 |
| Royal chariot | 33 | — | 5,296 |

Both teams and all infantry roles together warm exactly 32 assembled meshes, 49 primitive/profile meshes and 10 materials. Repeated construction of 96 units does not grow those caches, and disposal returns the node count to entry. Pose sampling allocates no new mesh or material resources. Existing vehicle gates remain at 40 meshes / 7,000 triangles maximum. Infantry's declared G1 ceiling is 24 mesh instances, 65 surfaces and 15,000 triangles per role. Counts bound resources; they do not establish GPU performance or final visual quality. Geometry uses no texture downloads, lights, imported assets or normal maps. Near-only trim uses an explicit 42 m visibility cutoff with 4 m hysteresis; it does not claim an alpha fade.

Executed on Godot 4.6.3, headless, CPU 2, with existing project resources and no imports/renders:

```sh
taskset -c 2 godot --headless --path games/yuga-native \
  --script res://tests/graphics_infantry_cases.gd -- --report=/absolute/fresh/infantry.json
taskset -c 2 godot --headless --path games/yuga-native \
  --script res://tests/lane_vehicle_art_cases.gd -- --report=/absolute/fresh/vehicles.json
taskset -c 2 godot --headless --path games/yuga-native \
  --script res://tests/lane_army_cases.gd -- --report=/absolute/fresh/army.json
```

- [Infantry 53/53](units-checks/infantry-r2.json): finite geometry, no art colliders, bounded resources, repeated-clock freeze, nonfinite input rejection, root-transform ownership, exact draw-hand/nock/string contact, release/death visibility, rewind, 96-unit cache/disposal and actual receiver/collider invariance.
- [Vehicle 48/48](units-checks/vehicles-r1.json): geometry bounds, recoil/reset, wheel contact, shared caches, draw-string endpoints and existing 20-minute pose stress.
- [Army 21/21](units-checks/army-r1.json): actual 30-unit spawn, mirrored composition, damage/gold/status/lifecycle, 72 live / 24 corpse / 96 total caps, waves/core arrivals, all-lane engagement and existing 20-minute fixed-step soak.
- [Rule-source comparison](units-checks/rule-source-invariance.json): only `_ready` and `update_pose` changed, with the collision prefix and all rule functions exact.

All final logs contain no engine errors or warnings. The first infantry result, 50/53, is retained: the new test compared a float32 collider radius with literal 0.39 using exact equality. It now uses `is_equal_approx`; runtime bytes did not change between those two runs. Raw logs and portable text copies are retained alongside the reports.

One known presentation risk remains deliberately frozen: the inherited minion flying-arrow tracer is visible during the windup while the new nocked arrow draws. This can show two arrows before the actual 0.26 s authority impact. Root requested G1 pictures first and assigns G2 a bounded draw/release/travel correction with unchanged authority timing. The 53 passing headless checks do not close this visual timing issue.

Central render questions: compare both teams/all three infantry roles at roughly 5 m and the ordinary 15–25 m camera, in day and night; inspect the shaped chest, dhoti folds, archer distinction and shield readability. Record actual march→attack→death and pause/resume to assess foot support, hand contact and weapon timing. Cross 38–46 m in both directions to inspect the detail-cutoff transition. For siege, inspect wheel-ground contact, plank gaps, banded barrel and royal silhouette at close and ordinary distances. No extra cinematic camera or changed gameplay setup is needed to claim the ordinary view.

Frozen runtime SHA256:

```text
80ae046d364a737cf2c33fd43b325d4fd189573eccd795358eb9d589e7868edb  scripts/lane_infantry_art.gd
823903af51605272e73b7ec9a5d3b1aea6fa7a55243b3937bed7004aa79ff665  scripts/lane_minion.gd
ac78ef11354adecb60fabf0b7e9b060585be42168eac184cc67c09b9b36e0fb1  scripts/lane_vehicle_art.gd
```

No owned engine processes remain. Root/central capture owns the next pixel review; worker 05 stops at G1 and waits for the G2 assignment. No commits or shared ledger changes were made.
