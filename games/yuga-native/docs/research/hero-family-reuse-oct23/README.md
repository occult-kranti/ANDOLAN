# Rama-base roster production path

The implemented pilot is an **editable Arjuna authoring template using Rama's current appearance**. It establishes a reusable production starting point, not another finished hero. The accepted Rama rig, 23-clip runtime library, PBR material roles, single-skeleton LOD machinery, computed sockets, facial owner and bounded secondary motion are reused through shared resources.

The generated Rama source and both recent binding attempts remain rejected. None is used here. Canonical roster, game scripts, source assets and runtime selection remain unchanged.

## Implemented sources

| Resource | Role |
| --- | --- |
| [Source-pinned manifest](rama-family-manifest.json) | Fourteen catalog profiles; exact accepted source hashes, skeleton/rest/bind contract, materials, face, masks, sockets and LOD constraints |
| [Arjuna intake](pilot/arjuna-template.json) | Template status, shared resource references, required unique art and open gates |
| [Arjuna Godot scene](pilot/arjuna-template.tscn) | Actual external reference to the canonical complete Rama GLB; no model copy |
| [Arjuna Blender scaffold](pilot/arjuna-rig-authoring-template.blend) | Actual small rig-only editable file, no mesh/image copies; records pinned geometry reimport location |
| [Blender save/reopen evidence](blender-save-reopen.json) | One 164-bone rig, unchanged rest/embedded actions, source preservation and eight executed checks |
| [Reusable tooling](../../../tools/hero-family-reuse/README.md) | Intake, template creation, shared runtime setup, meaningful failures and reproduction commands |

Executed checks pass: **20/20 focused tests and 13/13 native template checks**. Local tests include twelve actual malformed-GLB counterexamples plus real incompatible source/catalog cases. Independent review additionally passes 24/24 retained candidate/request cases, 19/19 individual source-pin drift cases and 10/10 shared-resource/lifecycle checks. The rig-only Blender scaffold passes eight owner save/reopen checks and six independent reopen checks. See the [independent receipt](independent-review/receipt.json), [review explanation](independent-review/README.md), [local verification](local-verification.json) and [exact test log](intake-tests.log).

These checks accept the authoring infrastructure and unchanged-donor template. Structural compatibility does not accept a new hero's visual quality, contacts, licensing or playable behavior; those require their separate gates. No new hero or roster promotion is accepted.

The canonical near GLB is SHA-256 `db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e`; the runtime library is `1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8`. The manifest pins 19 direct source files, including mid/far GLBs, catalog, component scripts, the secondary shader and five additional roughness maps. A changed source is a review event, not a reason to silently regenerate an approval. CI should run `validate` against the committed manifest; it must not run `audit` to bless changed inputs.

The accepted GLB embeds nine actions. The runtime library independently contains 23: aim, circle_draw, circle_release, dash, death, draw, fall, flight, grapple, hit, idle, jump, land, piercing_draw, piercing_release, ready_draw, release, respawn, run, sprint, volley_draw, volley_release and walk. Blender inheritance is **nine embedded actions plus an external reference to the 23-clip Godot library**.

## Reuse boundaries across all fourteen heroes

| Hero | Family | Safe starting reuse | Unique work still required |
| --- | --- | --- | --- |
| Rama | Current donor | Existing source and runtime contracts | Its remaining quality/release gates remain separate |
| Arjuna | Human archer template pilot | Exact rig, locomotion, bow setup and authoring infrastructure | Lean diagonal silhouette, original face, angular bow, off-centre quiver/scarf, pivot/volley choreography |
| Karna | Conditional human archer | Same infrastructure after Arjuna pipeline review | Broader proportions, original face, shoulder discs, bow and deliberate heavy draw |
| Meghnad | Conditional human archer | Same infrastructure after Arjuna pipeline review | Original face, compact bow, crest/cloud scarf and oblique movement |
| Ravana | Humanoid/chakram seed | Humanoid motion and material tooling | Chakram grip, dynamics, release/recovery and ten-facet crown; catalog currently uses one head |
| Duryodhana | Humanoid/mace seed | Basic humanoid locomotion tooling | Heavy two-hand grip, swing/recovery, hit contacts and silhouette |
| Hanuman | Unique appendage anatomy | Selected humanoid processes | Tail rig/physics, original anatomy/face, mace grip, flight/landing and contact choreography |
| Bhima | Humanoid/mace seed | Basic humanoid processes | Broad body/face, heavy weapon inertia, contact and recovery |
| Sita | Humanoid/staff seed | Tools, selected locomotion after fitting | Original anatomy/face/mantle, staff grips and protective gestures |
| Draupadi | Humanoid/staff seed | Tools, selected locomotion after fitting | Original anatomy/face, five-panel cloth, staff and command gestures |
| Subhadra | Humanoid/spear seed | Tools, selected locomotion after fitting | Original anatomy/face, spear/pennant, command gestures and grip changes |
| Hidimbi | Broad humanoid/spear seed | Tools and selected motion principles | Original broad silhouette/face, leaf mantle, spear and grounded movement |
| Chitrangada | Humanoid/spear seed | Tools and selected locomotion | Original anatomy/face, spear hand transfers, crossing footwork and segmented mantle |
| Ulupi | Humanoid/staff seed | Tools and selected locomotion | Original anatomy/face, circular staff grips and water/garment motion; catalog keeps humanoid legs |

Source: current `assets/design/hero-codex.json` and independent read-only source inspection. These are authoring compatibility judgments; mythology does not require identical bodies or motion. Current catalog motifs are original game adaptations. No extra heads or serpent body are silently introduced into existing catalog contracts.

## Shared contracts that artists must preserve or deliberately replace

`rama_motion.gd` requires 164 bones, exact order/parents and rest transforms within 0.0001 of the runtime library metadata. LOD binding additionally requires compatible skin bind order/poses, material names and transforms. One live skeleton owns all levels; only body and bow come from mid/far, while the near face remains the single facial/morph owner. LOD thresholds are 420/160 projected pixels with 15% hysteresis and a 0.15-second hold.

Sockets are computed from bones, not imported named nodes: bow grip and muzzle use wrist.R; string nock uses bowstring; draw hand uses wrist.L; head uses head. Their exact offsets are in the manifest. Unknown sockets are rejected by the new wrapper; the underlying Rama controller otherwise defaults unknown names to grip.

Cloth/hair motion depends on semantic vertex-alpha masks and material roles. Current bounds are 0.075 m cloth and 0.018 m hair, using bounded shader displacement. This is not a physical cloth simulation. The face contract includes required blink morphs, an optional paired half-blink set and at most 8,000 face vertices. Changing body proportions, hand grips, cloth silhouette, facial geometry or bone lengths requires new measured contact, deformation, LOD and animation review. Exact compatible rest transforms are a reuse path, not permission to hide anatomical mismatch.

## Next ten rounds, six coordinated roles

The roles are production/source engineer, character artist, rig/animation artist, material/VFX artist, physics/gameplay engineer and independent reviewer. Each round has a concrete artifact and gate. The [machine-readable task board](roadmap.json) provides six scoped queues per round. Round one has an implemented pilot; later art and integration rounds remain open.

| Round | Concrete output | Exit gate |
| --- | --- | --- |
| 1 | Accepted-source inventory, strict intake and one shared-resource Arjuna template | Actual source reload, save/reopen and incompatible-case checks; no new hero promotion |
| 2 | Fourteen-hero identity sheets and an approved Arjuna turnaround/weapon/contact brief | Each hero has a distinct silhouette, face, weapon and gameplay read; reuse plan names every unique element |
| 3 | One authored Arjuna source mesh/outfit/bow/quiver/scarf fitted to the donor contract | Multiple-view art review; explicit asymmetric landmarks and garment/skin boundaries; no low-quality recolor substitution |
| 4 | Arjuna skin/face/mask binding on the reused rig, plus documented exceptions | Original source→REST and continuous posed deformation/contact gates pass; no forearm/leg leakage or hidden repose damage |
| 5 | Inherited locomotion plus unique Arjuna pivot, volley and counter choreography | Smooth 30/60/120 Hz transitions, authoritative release/cancel behavior, hands/string/feet continuous contacts |
| 6 | Unique Arjuna materials and socket-bound abilities with shared lifecycle code | Readable telegraphs/counters, no unbounded allocations, correct reduced-motion behavior and measured overdraw |
| 7 | Bow/arrow/scarf/quiver contact and bounded motion; separate Hanuman tail and heavy-weapon design contracts | Honest physics model, collision authority and contact clearance; unique anatomy does not get forced onto Rama |
| 8 | Reviewed near/mid/far geometry, facial owner, masks and shared materials | One live rig, matching rest/skins, continuous posed LOD changes and measured memory/frame budgets |
| 9 | Isolated Arjuna gameplay adapter, bots/network lifecycle and all-screen presentation | Reconnect/cancel/death/respawn/teleport stress checks plus readable map/day/night/swamp encounters; no authority duplication |
| 10 | Independent native hero slice review and reproducible release candidate | Actual render/gameplay comparison, target-hardware profiles and open-defect disposition before any canonical promotion |

Only after this first hero passes should Karna and Meghnad use the same reviewed authoring process, with their own faces, shapes, weapons and choreography. Mace, staff, spear, chakram and tail work proceed through their respective unique contracts; a shared production framework is not a bulk hero generator. Ten planning rounds are not a claim that ten art rounds have been completed or that an AAA roster exists.

## Reference discipline

The implementation builds on this repository's accepted Rama production work and current catalog. Useful format/tool references are the [glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html), [Godot Skeleton3D documentation](https://docs.godotengine.org/en/4.6/classes/class_skeleton3d.html), [Godot AnimationLibrary documentation](https://docs.godotengine.org/en/4.6/classes/class_animationlibrary.html), and [Blender 4.3 Python API](https://docs.blender.org/api/4.3/). These links document the tools; they do not establish that new character art or commercial-game quality has been achieved. Catalog mythology citations and existing asset licensing/provenance remain authoritative for borrowed inputs.
