# R5 independent encounter and collision review

Task **YUGA-HERO-6R**, native offline Confluence. Reviewer `hero_combat`;
map owner `hero_ui`; integration/capture owner root. Base commit
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, dirty `work/yuga-studio`.
This is a source/physics review of the proposed Sangam district. It is not
acceptance of its unrendered art, full matches, hardware performance or online
navigation. Combat runtime remains frozen at the R3 receipt.

## Concrete findings

The four proposed cover footprints at X ±8, Z ±60, size 3 × 6 m, leave a 13 m
central opening. Real `lane_army.configure` accepts them and its three routes;
the full central segment Z -70 to +70 remains clear with 0.65 m margin.
This adds lateral cover without narrowing the existing ±4 m central lane band.
The cover can break cross-lane fire and create a retreat/peek decision; it does
not by itself add a new objective, elevated combat or a complete encounter.

Two actual counterexamples constrain the design:

1. At Y 2 m a native ray passes over the proposed 1.4 m solid, but the same
   segment is blocked by the army's planar line test. A Y 1 m ray hits the real
   solid. Keeping a visibly low planter would make arrows disappear in empty
   space. Root has approved a **2.7 m solid civic monument** on the same 3 × 6 m
   footprint. Review the whole actual grounded muzzle band after import.
2. Adding the Y 8 m overhead connector to `native_collision_boxes` makes real
   army configuration reject the central lane. Army movement, projectile wall
   sweeps and line-of-sight use XZ only. Gallery/eave collision belongs solely
   to native physics. Only the four grounded cover footprints enter the derived
   army manifest. Raised-floor abilities remain rejected by the current kit.

The independent probe passed **6/6**:

```sh
godot --headless --path games/yuga-native \
  --script res://docs/research/hero-six-rounds/combat/map_counterexamples.gd \
  -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/round5/map-proposal-counterexamples.json
```

See [counterexample report](round5/map-proposal-counterexamples.json) for source
hashes. These are deliberately proposed-geometry probes, not instantiated
district checks. Their expected negative outcomes are evidence of constraints.

## Acceptance criteria for the authored candidate

| Surface or route | Required observation | Failure that blocks promotion |
| --- | --- | --- |
| Eight base blocks | Original eight positions, sizes and IDs remain; new masonry visibly closes the occupied space | Decorative doorway implies a route through a solid; new stone contains an uncollided gap |
| Block 2 frontage | Its currently detailed concave collision is compared to new art, or an explicitly tested replacement is installed | Hiding the old frontage while silently retaining a different collision profile |
| Central avenue | Actual radius 0.65 m, height 1.8 m hero capsule sweeps all lane segments, both directions, below galleries at Z ±28 | Overhead triangles/boxes enter ground travel or army route checks |
| Cover | Four rendered bases, four collision footprints and four army boxes match; arrows at actual grounded muzzle heights and grazing radius stop at visible stone | Projectile blocked above empty space, or a visually solid corner permits traversal/fire |
| Peek/retreat | Ground approach each cover from both ends; view/shoot from all four corners; Step toward cover stops before it, Step parallel clears it | Step crosses stone, camera pops through it, hidden shooter gains an invisible firing lane |
| Guardian field | Place on each side and across cover; protection and LOS agree with current kit; warning stays legible on the new stone/paving palette | Protection crosses the planar barrier while UI claims obstruction, or field disappears against materials |
| Volley/Pierce | Fixed ground targets behind cover remain blocked; three pending warning lanes still retire only on release; clear lane works | Map adapter changes combat timing/radius/release authority, or art hides a warning |
| Canopies | Actual camera sphere (0.18 m), spring arm length 3.5 m/offset 0.65 m/margin 0.20 m; walk, turn and aim along all lower eaves | Camera is forced into the hero or wall for a sustained usable route, or shows the roof underside through collision |
| Traversal | Existing 8 decks and 10 anchors stay reachable; connector top/roof has true native collision; ceiling remains 24 m | New roof traps a tether landing, clips the flight path without visible stone, or suggests usable elevated attacks |
| Relay and rotations | Both spawns, three lanes, center loop and cross-mid route remain accessible; each relay/camp can be approached/retreated from | Architecture blocks the center rotation, creates an unescapable pocket or occludes objective feedback |
| Boundary vistas | Stay beyond actor limits X ±68 and Z ±128, with the actual 0.65 m radius accounted for | A facade invites a route through the invisible world clamp or camera enters an unmodeled backside |
| Day/night populations | Same actual play camera with troops, siege, field and projectile effects; targets retain outline/value separation | Warm stone masks warm warnings; dense trim competes with enemy silhouette or health bars |

Grounded cover tests must use actual kit projectile sweeps, not only a central
ray. Physics ray tests are useful counterexamples but do not prove the radius
of a projectile is supported. Add repeated cast/cancel/reset and a generation
change to ensure map attachment does not duplicate footprints or mutate the
base manifest. Do not fix a renderer/readability problem by widening collision.

## Integration and identity requirements

- Preserve canonical `art/world/confluence-map.json` and staged
  `assets/world/confluence-map.json` byte equality, exact eight base boxes,
  eight native decks and ten anchors. The raw map digest remains
  `d39043bfaabd9c3e173f03d68423269b5308b60c6906968315405690f844d77c`.
- Chain private derivation **gate → garden → district**; deep-copy the input,
  retain prior boxes and reject malformed/nonfinite/negative/duplicate/moved
  footprints. A transformed district must not retain stale world boxes.
- Pin source script, GLB, editable blend, companion geometry spec and adapter
  hashes, plus the effective derived collision set in the integration receipt.
  The unchanged base map digest does not identify the new effective geometry.
- Keep imported/art-only colliders out unless intentionally built from exact
  visible faces. Confirm collision group counts and do not inflate historical
  `native_platforms == 8` by putting every new solid in that group.
- The current `world_scene_cases.gd` deliberately disables gate/garden and pins
  Block 2's reviewed detailed frontage. Preserve its historical oracle with an
  explicit district-disabled fixture; add a candidate integration suite that
  exercises default gate, garden, district and actual army together. Do not
  blindly replace the old hash or geometry expectations to get green tests.
- Native contract revision 8 pins selected authority sources; it does not
  attest every new visual. Verify whether edited runtime files are catalogued
  before deciding a revision migration is required. Reuse real export/package
  admission, include newly loaded resources, and verify the frozen export
  input did not change. Root owns this shared decision.

Useful existing coverage: `world_map_cases.py`, `world_plan_cases.py`,
`world_scene_cases.gd`, `world_flow_cases.gd`, `world_presentation_cases.gd`,
`desktop_world_route_parity_cases.gd`, `desktop_world_frontage_cases.gd`,
`desktop_world_render_resources_cases.gd`, `traversal_cases.gd`,
`traversal_army_stress.gd`, `rama_ability_cases.gd`,
`rama_hero_integration_cases.gd`, `native_contract_cases.gd` and
`native_contract_package_cases.py`. Select the relevant suites after the
candidate is frozen; this list is not a claim they were run in R5.

## Remaining evidence and next owner

### Imported candidate check, 16 November

After root's serialized import and default-world integration, the independent
[encounter suite](round5/sangam-encounter-r3.json) passed **60/60** with no warning
or error in its verbose log. It instantiated the real district, retained gate,
garden and relay geometry, and verified all lane/rotation capsule segments in
both directions. Native cover rays at 1.0/1.9/2.6 m, four covers × three actual
bow abilities against live staged receivers, Guardian rejection, planned Step
endpoints, native gallery underside at 8 m, ground camera-sphere passage and
raised-cast rejection passed. These checks do not inspect rendered camera
composition or execute Step through ordinary input.

The actual effective army includes **43 boxes**: 16 inherited base/deck boxes,
10 gate, four garden, four district and **nine existing relay plinth shapes**.
Initial R1/R2 reports passed 58/59 because the independent identity fixture had
omitted the relay session's post-configuration addition. The corrected oracle
derives those nine boxes from actual instantiated physics shapes and still
requires exact array equality. The failed reports remain. Two process frames
after teardown remove the initial probe's exit-time object warning.

```sh
godot --headless --verbose --path games/yuga-native \
  --script res://docs/research/hero-six-rounds/combat/sangam_encounter_cases.gd \
  -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/round5/sangam-encounter-r3.json
```

Source review confirmed `confluence_world.gd` chains gate → garden → district
before army configuration, then existing relay construction adds its plinths.
The new `sangam_paving` switch is set through shared `_configure_paving` for
the floor and swamp overlay; coastal water retains its own treatment. The
normal relief changes shading, not floor elevation. New source and shader
hashes are pinned in the R3 encounter report. Actual map renders and warm
ordinary hero input remain root's next evidence.

UI owns the correction, adapter and candidate tests. Root serializes import,
freeze, package and original advancing capture. Combat reviewer then checks
actual imported cover/roof/camera queries and original hero/map captures.
Full vertical combat, browser/shared authority, human balance and physical-GPU
performance remain outside the implemented offline planar combat contract.
