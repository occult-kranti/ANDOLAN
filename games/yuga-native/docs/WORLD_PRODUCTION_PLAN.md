# Confluence world production plan

This packet builds an original **140 × 170 metre native traversal and art-review scene** from the current authority's map. It advances the world tasks in the accepted full-game roadmap without changing the accepted game-design or roadmap documents. A complete environment assembly is not an online native match; authoritative actors, dynamic structures, full combat and production 6v6 rules remain separate integrations.

The canonical layout is [confluence-map.json](../art/world/confluence-map.json), schema 1. Layout revision is separate from schema version. Geometry and textures are authored for YUGA. The source map and simulation hashes identify the exact baseline whose coordinates were copied.

## Frozen interface

| Field | Contract |
| --- | --- |
| Coordinates | Metres, +Y up, +Z forward. Positive yaw rotates +Z toward +X. Placement position is the base centre. Ground is y=0. |
| Bounds | Nominal x[-70,70], z[-85,85]. Authority movement uses x[-68,68], z[-82,82], contracted by actor radius; current review hero radius is 0.65m. Art can extend to x[-100,100], z[-105,105]. |
| Lanes | Exact current points and centre x values -40,0,40. These are strategic paths, not declarations that a player can walk through a living tower. |
| Static collision | Eight `authority_collision_boxes`, copied exactly from `SOLIDS`; position is base centre, size is [width,height,depth]. Only these boxes and the outer boundary block review movement. |
| Dynamic objectives | Current three towers per team and two cores are visual anchors in this review. The authority separately blocks living structures with circles. Native multiplayer must add and remove those colliders from live state; static scene agreement alone is incomplete. |
| Prop transform | `{id,kit,preset,position:[x,y,z],yaw_degrees,scale:[width,height,depth],collision}`. Normalized kit root bounds are [-.5,0,-.5] to [.5,1,.5]. Scale first, yaw second, then translate. |
| Kit assets | `kit_sources[].asset` is a runtime GLB path. `manifest` is authoring provenance under `art/world/`, not a runtime package requirement. Preset names identify GLB root nodes. Ground inlays are explicit native procedural presets. |
| Collision ownership | Props never independently generate a second collider. `collision:'authority'` associates a visual block with one canonical collision box. `collision:'none'` remains decorative. |
| Lighting | `lights` contains desired fixture positions, kind, priority, colour, day/night energy and range. Lighting chooses at most 12 actual unshadowed point lights; other fixture meshes remain emissive. |
| Water | `waters` gives centre position, `size_xz`, coast/swamp style and explicit traversal description. Sea lies outside authority bounds. Interior swamp is a thin wet-ground overlay over the same y=0 collision plane. No swimming or depth mechanic is implied. |

Runtime must package the single canonical JSON explicitly or copy it to a declared runtime data path with the same hash. Do not require the whole authoring directory in the executable. Missing external GLB kits may use a clearly reported procedural fallback while integrating; a fallback does not close the final art gate.

## Whole-map composition

**Lanka coast and ghats, west.** The left lane reads as a long warm stone promenade. Existing sandstone blockers become continuous terrace/temple bodies, ensuring the visible walls explain the full collision footprint. Far coastal shikharas and watchtowers form a staggered skyline outside movement bounds. The sea occupies the western visual margin, with a clear land edge; it does not pretend to be a playable swimming route.

**Temple avenue, centre.** The central lane keeps a quiet aiming backdrop and a long sightline between its current towers. Lotus and sun/moon ground inlays orient the player without raised curb blockers. Off-axis temple roofs belong to existing building volumes. The centre has fewer small ornaments than the edges so projectile and ability telegraphs stay legible.

**Modern transit gardens, east.** Stepped contemporary blocks, indigo transit motifs and planted roofs contrast with the west while keeping equivalent collision. The architecture is an original mixture of urban design references, not an exact model of any named city. Rooftops are decorative in this flat revision. Distant towers sit outside the legal actor footprint.

**Reed courts and jungle.** Existing Naga camp anchors remain at x±54,z0, with a four-metre clear review circle. Low lotus and narrow reeds are placed deliberately beyond camp and crossing clearances; larger roots, shrine silhouettes and rock islands remain outside movement bounds. Grove Yaksha and Cloudwing anchors at x±20,z0 retain clear approaches. No dense foliage is placed across the cross-mid aiming route.

**Bases.** Sun and Moon arrival courts cover the full north/south playable width. Medallions, warm/cool identity and distant architecture orient spawning players toward the lanes. Spawn positions remain z±69; cores remain z±75. Current tower anchors stay at x[-40,0,40],z±37. Future inner towers are reserved as a design feature but absent from this baseline scene.

**Circular rotations.** A rounded, closed middle circuit connects the outer lanes around the central open area using z≈±13 and x≈±44. The route stays in the free gap between the current central blocks. A straight cross-mid connection at z0 links both Naga courts, all lanes and the two interior camps. The circuit is readable through low ground treatment and landmarks rather than newly inserted collision walls. It does not convert the rectangular authority into a different physical boundary.

The layout is deterministic: no runtime scatter or random placement can put a tree, lamp, shrine or decorative wall into a playable route. New placements must pass the footprint/route checks before artists or runtime builders consume them.

## Parallel work and integration order

| Owner | Exclusive artifact | Handoff |
| --- | --- | --- |
| World plan | `art/world/confluence-map.json`, this plan, `tests/world_plan_cases.py` | Canonical coordinates, transform contract, district/route/readability checks and stable revision |
| Architecture artist | Architecture builder, `assets/world/architecture.glb`, `art/world/architecture-manifest.json` | Eight normalized presets, exact bounds/provenance, export report |
| Nature artist | Nature builder, `assets/world/nature.glb`, `art/world/nature-manifest.json` | Reeds, roots, lotus, lamps, shrine and rock presets with +Z facing and exact bounds |
| Native engine | Native confluence scene/controller/builder | Load manifest once, instance kit nodes, canonical collision, radius-aware movement bounds, scene summary |
| Lighting artist | World lighting and water shader | Bounded day/night lights and original water response; no hidden geometry or gameplay changes |
| Independent world QA | `tests/world_map_cases.py`, `tests/world_scene_cases.gd` | Execute current TypeScript authority, compare anchors, flood routes with living objective blockers, test actual native physics and bad fixtures |
| Root | Menu entry, exact asset import/freeze, actual captures and packaging | Inspect the assembled map at spawn, lane, jungle, coast and overview; preserve version/hash and limitations |

Initial schema is saved before asset work so agents can build in parallel. Art kits use normalized bounds rather than private world positions. World layout remains the sole placement owner; artists do not add independent random scene geometry. The eight boxes, base coordinates and lane points are frozen during this packet.

## Four-round review record

**Round1 — source and schema.** Read the actual current `map.ts` and structure constructor. Saved schema1 with three lanes, eight exact static boxes, eight current objectives, four camps, seven districts and two middle routes. Declared flat y=0 traversal and reserved a separate future stacked-deck test; no production vertical mechanics were assumed.

**Round2 — placement correction and artist coordination.** Review found initial lamp/light origins hidden inside opaque building blocks, and negative-height swamp planes hidden below the floor. Lamps now sit on side facades above 1.9m with at most 0.22m projection, inside the 0.65m actor exclusion envelope. Lights move outward. Swamp water becomes an explicit shallow film at y=0.012. Added deterministic soft vegetation outside camp/route clearances and hard nature silhouettes outside movement bounds. Confirmed actual kit manifest paths and +Z lamp facing with artists. Recorded living structure circles as a separate authority requirement.

**Round3 — tests and independent challenge.** Planning tests cover district coverage, deterministic IDs/transforms, rotation clearance, mounted fixture envelopes, hard-art containment and soft vegetation/camp visibility. Independent QA compares actual TypeScript authority and actual native collision. Each suite includes deliberately invalid variants so the checks demonstrate rejection rather than just echoing accepted constants. The final planning run passed nine checks: the canonical layout plus eight deliberately invalid variants. Evidence is `tests/evidence/world-plan-validation.json`, pinning the manifest and test hashes. Independent native/authority results are separate; a pending or failed report leaves its gate open.

**Round4 — integration handoff and assembled review.** Reading the initial native builder exposed a visual support gap: the main floor covers only 140×170m while external skyline and nature extend beyond it. The native owner was asked to add a non-colliding background apron from the existing art bounds below the main floor and sea; no layout or authority change is required. Root imports the frozen kits and records actual day/night spawn, lane, coast, swamp and overview views, then traverses the map and checks camera clearance. Screenshots must identify missing kits/fallbacks, source hashes and any rejected view. This round remains open until those actual captures and traversal checks exist; a successfully generated GLB or a passing layout test is insufficient.

## Acceptance and next steps

The planning packet passes when the schema/authority positions agree, route and placement checks pass, artist/runtime consumers use the same contract and missing features remain explicit. The environment art packet additionally needs actual assembled views, traversal/camera review and measured resource counts. Physical-GPU performance, complete combat, dynamic structure collision, navigation for all units, multiplayer and the full requested visual quality remain later gates in the accepted roadmap.

The next world production steps are a shared native/server elevation contract, complete dynamic objective/army presentation, authored cover and traversable height only after that contract passes, and representative twelve-hero combat profiling. None requires rewriting the accepted design to call this review scene a complete game.
