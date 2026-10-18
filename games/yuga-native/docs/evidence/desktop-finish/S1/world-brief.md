# S1 / W4 — Desktop world, courtyard and atlas brief

Status: G0/S1 audit and preparation only. Mobile is deferred. Source observed at `0fb96d108b1d886a4ebf84d3b5140abca3905465` with existing G1/G2 working-tree changes; this is not a source freeze. No runtime edit, import, render, engine change or acceptance claim was made for this brief. Root owns the checkpoint and the five screen / ten integration round schedule.

## Visible evidence and candidate boundary

Directly opened the four original 960×540 G1 images:

- [Title day](../../graphics-six/G1/native/01-title-day.png), SHA-256 `2be1303891e9feb231d7903bd3f86c6811a425d7e6c1c281b026046c63ba73a4`.
- [Title night](../../graphics-six/G1/native/02-title-night.png), SHA-256 `f3e33d674f5e3c3b64d15f6dcabc5eeba0547978c6ebf9dfc026896868ff88c1`.
- [World day](../../graphics-six/G1/native/03-world-day.png), SHA-256 `2cdc03c98387e01e506c0239a8a491ca6beee45fcb4de70c4472415955e922f8`.
- [World night](../../graphics-six/G1/native/04-world-night.png), SHA-256 `6be91153c6a8e7a53f956b296f74ec120432c78b7f51fc33df17cdc1c2fd10fc`.

Reviewed [G1 environment](../../graphics-six/G1/environment.md), [G2 environment](../../graphics-six/G2/environment.md), [G2 source/receipt pins](../../graphics-six/G2/environment-source.json) and [G1 screen review](../../graphics-six/G1/screens.md). G2's nine courtyard materials / fifteen surfaces, transported scalar-map channels, shallow filtered frieze and coherent key/sky treatment are **implemented candidates with headless evidence, not accepted new pixels**. Preserve those sources and failed/accepted receipts. The first useful action after root's checkpoint is a matched G2 render review, not another unobserved finish layer.

## Top three defects and bounded responses

### 1. Title courtyard reads as a pale stage rather than richly finished stone

**Observed:** In title-day, the right half is dominated by an almost uniform pale floor. Arch faces, columns and the bright background occupy a narrow value range; the carved forms do not read strongly behind Rama. Fine black stipple is visible across the floor. Title-night changes the sky and floor temperature but retains the broad light floor and similarly flat stone. The image establishes stipple, not its cause; no claim is made that masonry, shadow bias or a particular renderer pass causes it.

**After checkpoint:** First judge the existing G2 material/lighting candidate at the exact title cameras. If the broad floor remains flat, adjust only the existing courtyard floor/inlay/mortar profiles for readable large stone variation and separation from the arches, while retaining authored albedo, tangent normals and GREEN roughness transport. Keep the subtle vertical treatment subordinate to modeled arches. Coordinate any `production_lighting.gd` / `hero_atmosphere.gd` change with their named owner; do not lower the night visibility floor or retune accepted shadow offsets as an undocumented material fix.

**Acceptance:** Matched day/night title originals plus a brief continuous camera/idle tape must show floor slabs, arch faces and recesses separating at ordinary 960×540 presentation; Rama's face, bow and indigo cloth remain readable. Reject crawling joints, new sparkles, an etched grid stronger than the character, broad gloss or darker stone that hides contact. Retain the stipple as an open finding until a controlled source-bound comparison identifies its source. No new stone shader or extra ornament is required merely to add detail.

### 2. Arrival plaza lacks a clear material hierarchy between travel, court and surrounding city

**Observed:** The day arrival image has a large grey paving field in front of the player. The right foreground wall presents a large coarse block surface; repeated blue/stone facade rows across the horizon compete at similar scale/value. The gold arrival ring is more immediately legible than the route surface. Night separates sky and city more clearly, but the broad grey court and repeated blocks still dominate. These static spawn views do not establish every district, water border or far-enemy visibility.

**After checkpoint:** Use the existing route/court masks and exact named architecture profiles. Give routes and arrival stone distinct broad reflectance/value groups, retain dry stone roughness and a quiet mortar scale, and tune near/mid/far separation through existing profiles before adding geometry. Preserve the single paving union at route intersections and the same paving function in the opaque swamp border. Root capture should include one route intersection, one readable facade, the coast and the west reed court before any ground/water variant is promoted.

**Acceptance:** At the same spawn/camera/phase and comparable army time, a reviewer can identify the walkable route and arrival court without using the gold ring or text. Near/mid/far silhouettes remain distinct in day/night; normal details do not become distant line noise. A slow strafe must show no slab shimmer, frieze crawl, pool rectangle, horizon discontinuity or material popping. Keep collision, route IDs, lane widths, traversal decks and target geometry unchanged. This is a surface/composition correction; new decorative nodes are outside the first pass.

### 3. Atlas spends scarce space on repeated keys while omitting native raised-platform footprints

**Observed:** In both G1 world images, the upper-right route plot is small relative to the tall card and four-line static legend. At spawn, the white hero/heading marker crowds the Sun core/label. Sun/Moon are named at the cores and repeated in the legend. The separate relay panel contains useful named state and must not be discarded simply because relay markers also exist on the map.

**Source-confirmed mismatch:** `world_atlas.gd::_draw()` paints only the eight `authority_collision_boxes`. The current manifest additionally has eight `traversal.native_collision_boxes`, which `confluence_world.gd::_build_traversal_landmarks()` builds as native landing decks. Tether diamonds do not communicate those platform footprints. This is a desktop-native map issue; it does not request new multiplayer/elevation rules.

**After checkpoint:** Make the plot rectangle and footer allocation explicit while preserving the existing anisotropic heading projection and Sun/Moon orientation. Distinguish existing raised deck footprints from base blockers with a restrained outline/pattern, then keep anchors and the hero above the static geometry layer. Resolve spawn/core/heading crowding through marker/label offsets rather than falsifying positions. Coordinate a compact key/expanded-Help treatment and any `AtlasLegend` layout change with the screen owner of `confluence_world.gd`; retain access to tether/siege/relay meanings and remapped overview binding. Cache one privately owned panel style instead of creating a new StyleBox on every atlas redraw.

**Acceptance:** Actual 960×540, 1280×720 and 1366×768 captures at both spawns, a relay and a raised deck show clear hero, core, faction, siege, tether and relay states. Map heading remains correct at cardinal/diagonal directions despite anisotropic scale. Raised footprints match manifest/world projection without becoming new collision or authority. Core labels, plot and legend never overlap/clamp out; contested state remains understandable without hue alone. Repeated redraws reuse the owned style and preserve current map/HUD contrast and nonoverlap checks. Existing projection, semantic markers and useful relay status survive the polish.

## Ownership and resource contract

W4's proposed runtime ownership after root releases the checkpoint is `scripts/environment_surface_finish.gd`, `scripts/world_lighting.gd`, `scripts/world_ground.gdshader`, `scripts/world_ground_common.gdshaderinc`, `scripts/world_water.gdshader` and `scripts/world_atlas.gd`. `assets/environment-finish/masonry.gdshader` requires explicit coordination with root and renderer diagnosis before alteration. Shared courtyard lighting/atmosphere and `confluence_world.gd` legend callers are serialized owner handoffs, not concurrent edits.

First-pass limits: zero added meshes/lights/colliders, no imported/shared material mutation, no new dependencies or texture imports, existing twelve-material per-world finish cap, fixed cached phase resources and existing opaque-water restrictions. Any necessary exception needs a concrete visual reason and root ownership assignment. Existing G2 counts are baseline receipts, not a promise that every scene binds the same number of surfaces.

The masonry source currently contains four texture samplers, uniform-controlled optional map/frieze/window branches and derivative normal construction. It has no loop, screen/depth read or vertex displacement. This inventory does not establish compiler cost or stall causality; a uniform flag is not evidence of an independent compiled shader variant. `ui_06_acceptance` owns ShaderRD first-draw diagnosis and CPU 0/1; no W4 capture/import competes with it. Retain exact G2 shader bytes for any controlled renderer comparison.

## Checkpoint and acceptance sequence

1. Root publishes the source checkpoint and confirms whether existing G2 pixels can be reviewed. Until then, W4 has changed this brief only.
2. Review matched G1/G2 originals before selecting one bounded courtyard/world revision; avoid stacking unseen material changes.
3. Implement the agreed atlas correction separately from surface tuning so a map regression cannot hide inside a material review. Agree shared caller/API changes first.
4. Run only affected existing headless gates after the capture owner releases CPU/resources: G2 environment cases, world lighting, atmosphere/production lighting when touched, theme-map consistency, world presentation/objective/HUD geometry. Preserve meaningful failures; exact counts belong to the new run.
5. Root's serialized actual-render lane captures frozen source. W6 independently checks the three visible outcomes, motion artifacts and regressions. Source tests alone do not close any of these art gates or establish hardware FPS.

Current disposition: three concrete desktop defects scoped; existing G2 candidate preserved; runtime implementation and new-pixel acceptance wait for root's checkpoint/capture lane.
