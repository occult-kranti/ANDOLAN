# Rama: one coherent native hero

This milestone replaces the default native avatar with a new smooth-skinned Rama and replaces disconnected primary/pulse/invocation controls with one five-part kit. It follows the user's October 17 request to concentrate on one complete character, actual rendered quality, animation and consistent screens. The previous Mythic release remains an immutable historical build.

This is animated 3D in Godot 4.6.3, authored with Blender 4.3.2. It does not establish Deadlock/Overwatch visual parity, native multiplayer, a complete roster, or physical-GPU performance. A generated concept image is the direction; it is not used as evidence of the mesh.

## Play and controls

The title presents the actual skinned character. Enter Confluence for lanes and armies or choose the courtyard for target practice. Both use the same kit and bindings:

| Input | Action | Commitment and counterplay |
| --- | --- | --- |
| LMB | Kodanda | A short drawn shot; movement remains available. One arrow is reserved for an accepted request. |
| Q | Piercing Dawn | A committed draw followed by an arrow that can hit several troops. Solid cover stops it. |
| E | Measured Step | A brief movement in the movement direction, or forward when stationary. Collision still applies. |
| C | Guardian Circle | A fixed field protects and heals Rama and allied troops inside it with clear line of sight. |
| X | Dawn Volley | Three deliberately paced firing lanes with visible preparation. |
| R | Reload | Restores the twelve-arrow quiver after its timer; cannot start over an accepted action. |
| F / G | Flight / grapple | Existing traversal remains available outside committed ground casts. |
| F2 / F3 | Controls / Rama guide | Bindings are saved; the guide reads the actual ability data. |
| Escape / F5 | Pause / reset practice | Pause freezes combat. Reset retires casts and restores the current practice. |

Ground casts still use the native lane simulation's planar receiver geometry. Raised-deck and airborne combat remain work for the elevation/authority roadmap. Enemy siege blasts now damage Rama; ordinary lane troops still target other troops. The courtyard's bullseyes are practice targets and do not attack. Defeat returns Rama to the arrival position after three simulation seconds.

## Ownership and timing

`rama_hero_runtime.gd` connects the same `rama_ability_kit.gd`, `rama_vitals.gd`, `rama_ability_effects.gd` and `rama_motion.gd` in both scenes. The kit owns damage, cooldowns, release timing and receipts on the 20 Hz army clock. Pause preserves an accepted ground step, including when the engine emits its own pause notification; flight and tether cancellation cannot silently consume that action. A 0.18-second draw therefore releases at the first eligible tick, normally 0.20 seconds. Rendering and animation cannot release damage early.

`player.gd` owns the collision body and camera. The single Rama skeleton modifier owns locomotion, aim, contacts and action blending; the older carry/traversal modifiers are retained for historical assets and tests. Primary fire allows moving legs. Committed abilities remain locked until the kit's recovery receipt, even if rendering or physics runs ahead. Release samples the actual bow socket once. Pose and effects read the accepted result.

`rama_practice_army.gd` and `rama_practice_target.gd` adapt courtyard bullseyes to the same receiver contract. They retain the existing hit/defeat callbacks and replace the old independent target respawn timer with explicit practice reset.

`hero_ui_theme.gd`, `rama_hero_panel.gd` and `rama_hero_hud.gd` provide consistent native screens. Five visible ability slots read current cooldowns, arrows, health and shield. Old fourteen-invocation research components remain accessible separately and are not presented as fourteen finished heroes.

## Art and motion source

The editable hero and generator live in `art/hero-rama/`; the new runtime asset is `assets/heroes/rama-hero.glb`. The older `rama-production.glb` remains unchanged for historical film and comparisons. New clothing, ornaments, hair, weapon geometry and woven textures are original work over the retained CC0 anatomy inputs. See `NOTICE/RAMA-HERO-PROVENANCE.json` for hashes and source/license separation.

The authored motion library, generator and capture driver live in `art/hero-rama-motion/` and `assets/animations/rama_hero_motion.tres`. Actual skin checks supplement bone/socket tests: they inspect planted soles, fingertips against the grip/string and transitions under repeated input. Passing those measurements does not itself establish expressive or production-ready animation.

## Evidence and remaining gates

The independent checklist is [RAMA_HERO_ACCEPTANCE.md](RAMA_HERO_ACCEPTANCE.md). The research record is [RAMA_HERO_DESIGN_STUDY.md](research/RAMA_HERO_DESIGN_STUDY.md), with its pinned source ledger. It studies 41 complete candidate four-slot kits in accessible Deadlock text, not all live-playable characters or inaccessible wiki/video footage.

Current-source evidence is collected under [evidence/rama-hero](evidence/rama-hero/). Independent R7 world integration passes [138 assertions](evidence/rama-hero/qa/final-review/expiry-regression/summary.json), including all fifteen ability/phase pause-reset cases, repeated real reloads, actual siege damage/death/respawn, stale-event rejection, 100 reset cycles and exact Guardian expiry. Native/legacy compatibility adds 198 assertions; the focused combat suite passes [85](evidence/rama-hero/combat-expiry/). Motion/contact checks pass 39 and the migrated traversal suite passes 34. These are functional and numerical results, not an art score.

The [final source snapshot](evidence/rama-hero/source/final/review.json) records 352 runtime files with aggregate SHA-256 `5aaeec270783a727cb06095e2c541628069eeb20e6d6443060e62a25f4ad2b86`. The earlier source snapshot and 135/59-check reports remain historical. The [expiry correction archive](evidence/rama-hero/combat-expiry/manifest.json) preserves the rejected decorative hard cut, failed regressions and final source files. R2 subsequently exposed a one-frame warning-boundary error and a throttled HUD expiry update. The current correction uses authority age for field validity and refreshes critical vitals every render. The strengthened 138-case integration regression and 9 HUD cases pass; the normal-clock Guardian probe independently passes exact expiry and fade review. Full R3 recording and a new package remain pending.

[Watch the actual staged animation reel](evidence/rama-hero/motion/rama-motion.mp4). The corrected 539-frame staged animation take covers 22.46 simulation seconds at 24 Hz, including locomotion, all five actions, flight/grapple, rapid bow retriggers and reactions. Final gameplay recording, packaged OS-input review and publication are still pending at this source checkpoint. The archive separates current R7 evidence from rejected R6 cloth deformation and earlier preview findings.

The current hero has 450,084 triangles, 164 bones, 13 material surfaces and 18 embedded texture maps; import-generated LOD is enabled, but authored production LODs and a full-match draw/skin budget remain open. These counts describe the asset, not a quality or performance achievement. Hair is broadly sculpted and the long sash remains stiff. The roadmap’s full production sculpt, expressive secondary cloth/hair, physical-GPU profiling and multiplayer gates remain open.
