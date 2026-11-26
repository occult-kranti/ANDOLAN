# Dust II field inventory for Monsoon Exchange

At the eastern objective in the CS:GO reconstruction, two stacks screen different approaches to a painted site. The screenshots show the paving turn jade under the same stacks, markings, parapet and skyline. The game registers a separate three-dimensional objective trigger there. At Sun Court the ground must show the player where to go, the solids must shape movement and the grounded ritual disk must decide where kindling is legal. Each can be authored independently. The western reference offers a different composition, with a tall panel, a lower obstruction and a court enclosed by walls. Indigo Cistern gives the second rite its own sunken, partly roofed approach. [Matched views](../matched-views.webp) · [Source analysis](source.json) · [YUGA transfer register](../../../../art/monsoon-exchange/design/transfer-register.md)

## Editions and evidence

| Edition | Inputs examined | What the inventory measures |
| --- | --- | --- |
| Valve, Counter-Strike: Global Offensive, legacy Source 1 | App 740, depot 731, manifest `1224088799001669801`. Original `de_dust2.bsp` is VBSP 21 rev. 10535, 325,735,952 bytes. The accompanying native NAV header is version 16.1. The lab also keeps jade copies of both files. | All compiled entities and properties by class, outputs, brush and displacement records, material use, placed static models, navigation and the bytes changed between editions. The original editable Hammer map and Counter-Strike 2 are outside this dataset. [Steam acquisition and identity](../sources-dust.md) · [Format structures](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/bspfile.h) |
| Hanzo, RocketMinsta/Nexuiz, December 2013 | The level’s editable `q3dust2-jb-beta6.map`, its mapinfo, and two fresh Q3Map2-built PK3s using the author’s settings. The published author package and original shipped BSP have separate hashes. | All Radiant source entities, convex brushes, curved patches, material use, mode declarations, control switches, compiled entities/surfaces and the jade surface changes. Its architectural scale, door logic and modes belong to Hanzo’s adaptation. [Author source and readme](https://dl.xonotic.fps.gratis/q3dust2-jb-beta6.pk3) · [Compiler settings, pinned inputs and engine evidence](../remakes-and-alternatives.md) |

The evidence has three levels. **Counted** entries below come directly from the files. A **visual observation** describes a feature visible in the paired views. **Keep** and **transform** are design decisions for Monsoon Exchange. Neither a published gameplay strategy nor the age of a map supplies a travel time, a sightline or a balance result. Dave Johnston’s account gives context for the original level’s development. The present inventory uses the later specific editions identified above. [Designer’s account](https://www.johnsto.co.uk/design/making-dust2/) · [Measured YUGA design](../../../../art/monsoon-exchange/plan/)

## Functions in the Valve level

The BSP has 375 entity records in 32 classes. The following table accounts for every class. Static props use a separate binary game lump and are counted in the architecture section. The companion JSON lists **all key occurrences**, histograms for functional settings, named references, and each output’s emitter, event, target, input, argument, delay and fire limit. A repeated key such as `OnMapSpawn` retains every occurrence. [Valve entity and I/O register](source.json)

| System | Compiled classes and placement counts | What the records do or establish |
| --- | --- | --- |
| Start and objective | `info_player_terrorist` 15, `info_player_counterterrorist` 15, `func_buyzone` 2, `func_bomb_target` 2 | Fifteen start markers per duty. One buy volume each has team 2 or 3. The A objective brush spans 272 × 288 × 96 Source units, B spans 384 × 368 × 96. The native server registered both. The A/B assignment follows the two model bounds and overview markers. |
| Mode-dependent partitions | `func_brush` 25 | Ten brushes share `retake.asite`, ten share `retake.bsite`, and five have no target name. Twenty-one start disabled, four enabled. These counts describe switchable map entities, separate from the ordinary built walls. |
| Visibility | `func_areaportal` 37, `func_occluder` 19 | Every listed portal starts open, every occluder active. They help decide what the renderer needs to draw. A visibility boundary alone supplies no player-sized obstacle. |
| Warmup and events | `logic_script` 5, `trigger_multiple` 12, `filter_activator_team` 2, `info_target` 10, `logic_auto` 1 | Five script entities name the same warmup arena script. Six triggers use each team filter. Two name the teleport script. There are 12 start-touch and ten end-touch output records, plus six map-start tone-mapping settings. These references specify bindings. Actual script execution depends on the host game. |
| Lines and wires | `move_rope` 33, `keyframe_rope` 109 | Endpoint and intermediate records link through `NextKey`. The data supports reusing a spline-and-anchor authoring method for cloth lines or cables. A visible rope grants climbability only if a game separately implements it. |
| Light, sky and post-processing | `light` 10, `light_spot` 6, `light_environment` 1, `env_sun` 1, `env_fog_controller` 1, `env_wind` 1, `env_tonemap_controller` 1, `postprocess_controller` 1, `color_correction` 1, `shadow_control` 1, `sky_camera` 1 | The map declares local illumination, environmental light, sky, wind and image treatment. Six startup outputs set exposure, brightness targets, bloom and adaptation. Source also stores 16 cubemap capture positions. |
| Atmosphere | `env_soundscape` 57 | All start enabled. Eighteen named presets distinguish sites, ramps, entrances, passages and starts. Placed radii range from 76 to 478 Source units. These are ambience selection parameters. Tactical footstep audibility needs separate listener tests. |
| Other interactions and world | `worldspawn` 1, `prop_physics_multiplayer` 1, `func_clip_vphysics` 1, `game_player_equip` 1, `point_clientcommand` 1, `point_worldtext` 1 | The sole dynamic model path is a soccer ball. The clip entity constrains physics. The map also declares global configuration, an equipment helper, a client-command helper and a text marker. An ordinary static crate has no pickup or pushing mechanic simply because the artwork has that shape. |

A native headless load verified starts and site entities for both the baseline and jade editions. No people or bots took part in that smoke test. Twenty-seven particle-library warnings on the minimal server mount remain relevant if a later test depends on original effects. [Server evidence](../server-smoke.json) · [Acquisition, site extents and entity registration](../sources-dust.md)

## Surfaces, structures, visibility and collision

| Counted layer | Records | Architectural reading and reuse |
| --- | --- | --- |
| Built envelope | 43 brush models, 9,852 ordinary faces. Of these, 9,715 belong to the world model and 137 to other brush models. There are 20,912 base vertices and 50,286 edges. | Courtyard floors, wall planes, reveals, parapets, ramps and chamber shells can share a kit. World bounds also enclose nonplayable scenery. Size a new district from its own surveyed floors. |
| Sculpted surfaces | 8,324 displacement grids with 300,832 nominal triangles. Grid powers 2, 3 and 4 occur 7,977, 344 and three times. | Subdividing a wall or rough ground adds contours without adding a new route. Keep walk support stable where paving, relief or erosion changes the visible surface. |
| Materials and markings | 120 BSP material names, 2,360 texture-info records, 90 overlays. Source also uses external materials for props. | Stone/plaster, blended surfaces, trims, signs, game marks and engine tool materials have different jobs. One plaster is assigned to 968 displacement faces. The sky tool occurs on 837 faces. A textured face may delimit the world or render as sky. |
| Physical envelopes | 2,471 brushes with 20,501 sides. 797 carry the solid bit, 1,253 player-clip, 1,253 NPC-clip, 141 block-LOS, 35 grate, 11 window. | Contents are **bit flags**. One brush can occur in several counts. Associate independent player, projectile and decorative roles with each new obstacle and exercise the appropriate query. The numbers alone cannot establish all runtime trace outcomes. |
| Visibility | 3,478 leaves, 1,795 visibility clusters, 19 visibility areas and 75 area-portal records. | Separately track room/portal render partitions and actual opening clearances. Spatial partitions neither prove traversal nor resolve what a standing player's head can see over cover. |
| Placed models | 3,158 placements, 1,258 dictionary slots and 1,257 normalized used static model paths. 1,258 placements request VPhysics solidity and 1,900 have static-prop solidity set to none. | Decorative facades may still have supporting map brushes. A window, door mesh or hanging trim says little by itself about getting through. Review the prop settings and surrounding world collision together. |
| Mounted dependency set | 679 auto-combined model placements are packed. The other 2,479 placements depend on 578 distinct external static models. A separate soccer-ball model adds one unique render-model path. | A BSP download does not make all art available to an editor. The local intake resolves models and their materials from the matching depot. YUGA can reuse its resolver, prop-instancing method and independent mesh check. |

The Valve jade edition reassigns a material field on exactly **260** faces in each lighting table. Comparing all 64 raw lumps leaves 57 byte-identical. The seven that differ contain the texture bindings, matching LDR/HDR faces and packed assets. The NAV copies differ only in the word that records the paired BSP byte size. An independent mesh support test sampled the centers of 1,118 navigation areas. It found 991 on the recolored structural floor, 109 on raised props and 18 without a nearby upward render surface within its 18-unit tolerance. A NAV center under a crate needs its support tested independently from the floor paint. [Native counts](source.json) · [Per-material contributions](source-materials.csv) · [Build receipts and original validation](../README.md)

### What makes the two sites look like places

The repeated model families give an art producer a practical kit list. There are 353 Kasbah placements, 340 window placements, 248 foliage placements, 180 trim, 160 door, 140 crate, 108 doorframe, 87 awning and 80 light placements in their respective model directories. There are also curbs, railings, rooftop silhouettes, cable connectors, sockets, antennas, patched surfaces, pots, carts and service fittings. One wood window model appears 58 times, one crate 51 times and an air conditioner 41 times. Repetition belongs where the player reads a district or building type. A distinct awning line, wheel, planter or broken cornice can identify an actual decision point. [Every placed model path, skin and solidity count](source-props.csv)

An optional prop-origin lookup intersects each origin's XY with native NAV rectangles and checks interpolated floor height within 96 units. It places **242** entries against named areas, 15 against unlabelled areas and leaves 2,901 outside tolerance. Facade models often have pivots in walls or above walkable floors. The result locates a conservative subset and should never be treated as a district-wide prop density or a list of player cover. The screenshot at site B gives better evidence for the relative screen heights than a pivot labelled `BombsiteB`. [Method and counts](source.json) · [Site images](../matched-views.webp)

## How the routes join

Native NAV 16.1 describes 1,118 areas and 4,526 unique directed area links. Seventy-six of those links lack an immediately reciprocal link. There are 509 links crossing place labels and 102 distinct ordered label pairs. The file contains 414 bot hiding records and 17,906 encounter records. Those describe AI metadata. Cover quality, player sightlines and hero clearance require geometry and game tests. The ladder list is empty even though the routes include stairs, sloping approaches and changes in elevation. [Every area count, elevation range and named transition](nav.json) · [Pinned NAV reader](https://github.com/pnxenopoulos/csgonavparse/tree/354c86f749073e351a1e7d5474d9ef3ce9fedfc6)

| Route family and native area labels | Counted connections and structural interpretation | Function kept or transformed in Monsoon Exchange |
| --- | --- | --- |
| Departures. `TSpawn` 127, `TRamp` 25, `CTSpawn` 22 | TSpawn touches OutsideLong, OutsideTunnel, TRamp and TopofMid. CTSpawn touches MidDoors and UnderA. Both have connections to unlabelled areas. | Caravan Yard offers three opening choices. Archive Court gives each rite a return route. Team duties swap. |
| Outer east. `OutsideLong` 40, `LongDoors` 65, `LongA` 73, `Pit` 23, `Side` 18 | OutsideLong connects to LongDoors. LongDoors connects to both Pit and LongA. Pit also connects to Side. The holding pocket and the long approach are legible choices. | Mint Turn breaks the vista before Copper Arcade. Keep an independent outer entry to Sun Court. The arcade ascends past a cover wheel. The source depression is an alternative composition to study. |
| Hinge. `TopofMid` 42, `Middle` 25, `MidDoors` 57 | Middle touches Catwalk, LowerTunnel, MidDoors and TopofMid. MidDoors has distinct links to Middle, BDoors and CTSpawn. | Dye Scales and Weavers’ Gate use a central, screened choice. A permanent gap between loom solids gives a predictable rotation. |
| Inner east. `Catwalk` 13, `ShortStairs` 24, `Short` 3, `ExtendedA` 18 | Catwalk reaches ShortStairs. ShortStairs connects to ExtendedA. Short itself has only an outgoing link to ExtendedA. Callout names alone would suggest a different chain. | Ledger Climb and Ledger Balcony rise toward Seal Gallery. Verify the exposed landing from both directions. |
| Eastern site and return. `ARamp` 23, `Ramp` 6, `BombsiteA` 41, `UnderA` 25 | BombsiteA has outgoing links to ARamp, Ramp, ExtendedA and UnderA. The lowest and highest corners of the BombsiteA NAV cells span about 76.5–129.0 Source units. UnderA has outgoing links to LongA and CTSpawn. | Sun Court has an elevated platform and its own return ramp. Locate actual standing support for each ritual and hero cast. A site name can cover different heights. |
| Covered west. `OutsideTunnel` 81, `UpperTunnel` 63, `TunnelStairs` 32, `LowerTunnel` 7 | UpperTunnel touches OutsideTunnel, TunnelStairs and BombsiteB. LowerTunnel touches TunnelStairs and Middle. This supplies a covered commitment and a lower branch to the hinge. | Sailcloth Yard descends into Dyers’ Passage. Indigo Vault encloses the low route and Sluice Walk offers the alternative approach. Verify headroom and the dry strip at the cistern. |
| Western site. `BDoors` 54, `Hole` 12, `BombsiteB` 125 | BDoors touches Hole and MidDoors. Hole connects to BombsiteB. The site also connects to UpperTunnel and unlabelled areas. | Dye Gate and Indigo Vault reach Indigo Cistern from different directions. Keep alternate exposure. Test grounded approaches with the lowest-mobility hero. |
| Unlabelled areas, 74 | All 74 have distinct area IDs. Grouping them into one strategic hub would introduce fictitious shortcuts. All 26 named labels appear above. | Use separate area IDs even where an author has given multiple polygons one display name or left it blank. |

Elevation is expressed in native Source units, with positive Z up. The Monsoon survey uses metres with a new origin. A directed edge reports a native navigation connection in that direction. The quantities above give level designers a way to check the original interpretation against the records before adapting it. [Callout crosswalk for every label](../../../../art/monsoon-exchange/design/dust-callouts.csv) · [YUGA survey](../../../../art/monsoon-exchange/plan/survey.json)

## What Hanzo rebuilt and added

The editable Radiant file holds **298 entities in 58 classes**. It contains 2,357 convex brushes and 507 Bézier patches. Of these, the world owns 2,342 brushes and all 507 patches. Separate entities own the twelve door brushes, two jail brushes and one ladder brush. The packed IBSP 46 contains 273 entities. The 25 `misc_model` barrel placements from two ASE model paths contribute compiled geometry. Independent reconstruction generated the visibility and lightmaps before producing the jade variant. [Full source and compiled entity catalogs](hanzo.json) · [Original/variant engine images](../remake-engine-views.jpg)

| Hanzo system | Source records | Design use |
| --- | --- | --- |
| Level shell, roof and depth | One `worldspawn`. Curves occur in the world, alongside plane-brush walls, opening surrounds and courtyard floors. The paired engine views visibly show an arch, a lower opening, parapets, a raised square volume, paving and planted edging. | Retain readable negative space at the mouth of an opening. Give an inset water court a bridge, landing and adjacent wall that read independently from above and at player height. |
| Doors, switches and alternate modes | Twelve `func_door` have `wait=10` and `jaildoormode=1`. Two red control points target the six `jail_red` doors, two blue control points target the six `jail_blue` doors. A neutral point has no named door target. One jail volume per side and one ladder are actual brush entities. | Group-by-name switching is a reusable implementation pattern for a practice gate. A competitive passage needs explicit, replicated state if the designers choose to make it move. The canonical Valve BSP has zero `func_door` entities. |
| Starts, cameras and mode infrastructure | Twenty deathmatch starts. Team starts 10/10/6/6. Red and blue each have ten jail spawns, 22 further jail-mode spawn markers and two jail cameras. There are three intermission cameras, two terminals, five domination points and two CTF flags. | Preserve the separation of player starts, camera anchors and objective markers when wiring the YUGA round. Keep moving-door and jail rules as study fixtures. |
| Resource placement | 41 health placements, 37 armor, 19 ammunition, 10 weapon markers, one strength marker, and twelve team buff markers spanning arc, bash, guard, haste, medic and supply. | Redistribute attention through contrast and a recognizable landmark. YUGA’s competitive ritual has its own economy and supported team powers. A pickup in the source does not imply one in the new game. |
| Declared modes | `dm`, `tdm`, `dom`, `ctf`, `rune`, `lms`, `kh`, `jb`. Mapinfo includes parameters for each. | The lab tested engine load, movement and a jump in a local engine session. A declaration alone cannot establish that eight full multiplayer matches succeeded. |

The compiled geometry has 16 models, 30,907 vertices, 2,697 collision brushes, 20,724 brush sides and 1,288 visibility clusters. Of 3,929 draw surfaces, 3,366 are planar, 507 are curve patches, 50 are triangle soups and six are flares. The shader table has 87 slots. Only the shader table and draw-surface lumps changed in the jade comparison. Exactly 175 upward-facing draws changed shader among seven categories covering two brick surfaces, two jail floors, concrete, grass and a grate. Roof, wall, curved silhouette, jail switch bindings and the collision hulls retain their original data in the paired compile. [All source and compiled shader uses](hanzo-materials.csv) · [Compiler evidence and smoke run](../remakes-and-alternatives.md)

## What to borrow in production

1. **Keep the questions players answer.** Which of three departures to take? Where can a player change sites? Which approach is fast and exposed, which is long and independent, and which lets a grounded teammate return? Record the route graph and actual clear widths in the new survey. [Monsoon plan](../../../../art/monsoon-exchange/plan/)
2. **Transform the architecture that answers them.** A screened gate becomes a loom hall. A high east court becomes a sunlit market exchange. A sheltered west opening becomes a vault and dry cistern edge. Use the new floor levels, wall thicknesses and use-specific structures to establish this place. The source grid, UVs, meshes, materials and raw NAV vertices remain local research inputs. [Architectural translation](../../../../art/monsoon-exchange/design/transfer-register.md)
3. **Reuse the code and art that have a clear project role.** The existing BSP/IBSP readers, Radiant compiler workflow, Blender/GLB validator and QA procedures work as reference tools. Atelier and Trident supply separately licensed, editable architecture examples. Retain their specified notices for derivatives and verify material licenses individually. Decide art reuse from the per-file grant. [Open geometry with licenses](../open-geometry.zip) · [Alternative sources and file-specific terms](../remakes-and-alternatives.md)
4. **Give geometry and rules separate tests.** Confirm starts, walking radius, support height and overhead clearance. Test projectile cover and sightlines independently. Show two readable rite sites under both objective and ambience cues. Verify actual player transfers, sound, a legal plant and quench and a side swap in the running game before claiming competitive balance. [YUGA transfer and integration tests](../../../../art/monsoon-exchange/design/transfer-register.md) · [Ritual rules](../../../design/ember-rite-5v5/ROUND_AND_TECH.md)

## Reproduce the inventory

Use Python 3.11 or later, Pillow and Go 1.20 or later. The Python command imports the project’s existing Source and Radiant readers. Go uses the existing module lock and the matching NAV parser license. The local package must contain the following inputs. The original files are identified by SHA-256 in the JSON registers. [Source acquisition](../sources-dust.md) · [Fan rebuild](../remakes-and-alternatives.md) · [NAV reader license](../../../../tools/source-map-lab/nav/LICENSE)

```text
native/original/csgo/maps/de_dust2.{bsp,nav}
native/jade/csgo/maps/de_dust2.{bsp,nav}
radiant/q3dust2-jb-beta6.map
radiant/q3dust2-jb-beta6-{original,jade}.pk3
```

From the repository root, regenerate into a separate directory or compare directly with the six published tables.

```sh
inventory=games/yuga-native/docs/research/dust2-map-lab/inventory
python "$inventory/census.py" /path/to/local/dust2-map-lab --output /tmp/dust-census
python "$inventory/census.py" /path/to/local/dust2-map-lab --check
```

Use `--go /absolute/path/to/go` to select a compiler. The standalone verification script reconciles the aggregate tables with each other. Supplying the local package also checks them against the previous rebuild’s native, navigation and Radiant receipts. All 55 checks passed with the archived package. [Verification receipt and table hashes](verification.json) · [Verifier](verify.py)

```sh
python "$inventory/verify.py"
python "$inventory/verify.py" --local-package /path/to/local/dust2-map-lab
```

The census checks matching NAV headers, precise face-field changes, the native prop dictionary, entity counts and the Radiant variant’s geometry. [Generator](census.py) · [NAV helper](navgraph.go)

| Output | Search or compare |
| --- | --- |
| [Source systems](source.json) | Every entity class, property count, selected settings, all 28 I/O bindings, content masks, model families, geometry and variant identity. |
| [Source props](source-props.csv) | One row per normalized model path with placement total, original model directory, solidity and skins. |
| [Source materials](source-materials.csv) | One row per BSP material with ordinary face, displacement, collision-brush-side and overlay counts, texture-info slots and surface flags. |
| [Navigation](nav.json) | Native version and checksums, area attribute masks, per-place corner heights, hiding and encounter records, within-place and cross-place directed links. |
| [Hanzo systems](hanzo.json) | Source/compiled class comparison, door target groups, modes, actual geometry ownership, surface types, identical/changed structures and file identities. |
| [Hanzo materials](hanzo-materials.csv) | Radiant plane sides/patches and compiled draws, brushes, brush sides and surface/content flags per shader, plus counts of jade surface reassignments. |
