# Hanuman Trial handoff

**Current playable Hanuman.** The new Rust Confluence release ships the compact muzzle, swept mane, surfaced costume, Mountain Pulse recovery and five-technique practice coach. Artists and engineers continuing that edition should use the current studio handoff. The Godot trial below remains available as an earlier playable reference. [Current release](../art/hanuman-hero-finish/README.md) · [Editable scene and rebuild](../art/hanuman-hero-finish/HANDOFF.md) · [Next rounds](../art/hanuman-hero-finish/ROADMAP.md)

The offline trial on `game/yuga-hanuman-trial` includes the five revised Blender motions, projected ability marks and event-driven sound. The portable preview uses gameplay from [`d7aedae8`](https://github.com/occult-kranti/ANDOLAN/commit/d7aedae888ccbb49d726877bd9ad5ce46ce7446c). The playable rig and the detailed temple scene share action data. They have different meshes and materials. [Linux and Windows downloads](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-hanuman-abilities-2026-11-25) · [Watch the gameplay reel](../art/hanuman/reels/hanuman-abilities.mp4) · [Open the editable actions](../art/hanuman/abilities/hanuman-ability-actions.blend) · [Animation and package evidence](research/hanuman-ability-production/README.md)

## Open and play

Run from the repository root with Godot 4.6.3. Import assets on a fresh checkout, launch the game, then choose **Hanuman → Begin Hanuman Trial → Begin practice**. Use the displayed bindings for the gada, ward, vault, embers and Mountain Pulse. Esc pauses. F5 resets the trial.

```sh
godot --headless --path games/yuga-native --editor --import --quit
godot --path games/yuga-native
```

Open the studio file in Blender 4.3 or later for the editable 167-joint rig, eleven actions and packed textures. The separate dusk look contains the packed ImageGen board and uses the generated madder swatch on the cloth color input. Its studio material choices are separate from the playable GLB. [Studio Blender file](../art/hanuman/hanuman.blend) · [Dusk Blender file](../art/hanuman/lookdev/hanuman-lookdev.blend) · [Dusk render and rebuild command](../art/hanuman/lookdev/README.md) · [Playable GLB](../assets/heroes/hanuman/hanuman.glb)

The GitHub archive preserves the exact 35,824,106-byte bundle, including local capture originals and render receipts. A fresh GitHub download matched the archive SHA-256 `044d7760770d2aa181716e61aaf6837dda85f431ca5351ad7658e1904cc09cc2` and all 50 internal payload hashes. [Download ZIP](https://raw.githubusercontent.com/occult-kranti/ANDOLAN/ecd4eb58f069c602bb81f8c56b74f39c0e1a0e34/YUGA-Hanuman-Studio-and-Trial.zip) · [GitHub archive](https://github.com/occult-kranti/ANDOLAN/tree/archive/yuga-hanuman-studio-2026-11-25)

The packed temple court scene advances the generated keyframe through a new sculpt, groom, wardrobe, pose and physical environment. The current pass includes the paired muzzle and nostril sculpt, a closed belt-side fist, fluted gada and fitted gold-thread drapery. Use the posted comparison and the symmetry and contact receipts to pick the next editable surface. Keep gameplay changes tied to a separately imported and tested export. [Temple court scene and rebuild recipe](../art/hanuman/match/README.md) · [Verified Blender sources and LoopTools](research/hanuman-match-sources.md) · [Body-region review skill](../../../.agents/skills/yuga-anatomy-review/SKILL.md)

## Temple art and ground presentation

Open the packed Blender master to review the projected temple relief, facial sculpt, and corrected tail bend. The trial’s actor still uses its qualified gameplay rig. To see the new runtime presentation, start practice, use Lanka Dahan’s rear sweep or Mountain Pulse, vault, then watch the floor as Hanuman lands. Compare the contact shadow with the directional shadow setting on and off. [Blender outputs](../art/hanuman/match/README.md) · [Source study and coverage](research/HANUMAN_INDIE_RENDER_TECHNIQUES.md) · [Project history and preserved early studies](PROJECT_HISTORY_LIBRARY.md)

See the [shadow comparison](research/hanuman-indie-runtime/shadow-verification.json) and [Mountain Pulse capture](research/hanuman-indie-runtime/ground-mountain.png) for the actual trial output.

Run the dedicated native checks from the project root.

```sh
godot --headless --path games/yuga-native --script res://tests/hanuman_contact_shadow_cases.gd
godot --headless --path games/yuga-native --script res://tests/hanuman_ground_field_cases.gd
```

## Verification to carry forward

| Verified work | Evidence |
| --- | --- |
| Final R5 imported rig and motion | 15/15 rig checks and 15/15 tail checks. The four-joint secondary motion reacts to run, sprint, turn and landing. It fades into the authored sweep and pulse before impact. [Rig](research/hanuman-nov25/final/rig.json) · [Tail](research/hanuman-nov25/final/tail.json) |
| Actual trial and five profile-driven actions | 30/30 final launcher checks and 20/20 presentation checks. The earlier R3 ordinary input run reached all five impacts and exited normally. The separate combat suite passed 39/39. [Launcher](research/hanuman-nov25/final/launcher.json) · [Presentation](research/hanuman-nov25/final/effects-owner.json) · [Ordinary route](research/hanuman-nov25/native-r2/receipt.json) · [Combat](research/hanuman-nov25/native-r2/combat.json) |
| Reviewed motion and effects | The studio reel has 120 rendered frames. The original native reel has 112 rendered frames and uses scripted input in the actual trial. Both are silent at 16 frames per second. [Studio reel](../art/hanuman/reels/hanuman-motion.mp4) · [Native reel](../art/hanuman/reels/hanuman-gameplay.mp4) · [Independent review](research/hanuman-nov25/independent-rounds-4-5.md) |

For the temple court art pass, Godot 4.6.3 reran the existing trial's combat (39), presentation (20), and launcher (30) checks with zero failures. The art master still needs a baked game export, in-engine material review and frame-time measurements before it can replace the playable mesh.

For a runtime edit, reimport and rerun the relevant commands. The rig probes print machine-readable results. Keep a new receipt for the changed source, rendered sequence and normal input route. [Rig commands and acceptance details](../tools/hanuman-rig/README.md) · [Ordinary X11 capture](../tools/hanuman-capture/ordinary.py) · [Five-round panel record](research/hanuman-nov25/PANEL.md)

```sh
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tools/hanuman-rig/probe.gd
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tools/hanuman-rig/probe_tail.gd
godot --headless --path games/yuga-native --script res://tests/hanuman_combat_cases.gd
godot --headless --path games/yuga-native --script res://tests/hanuman_presentation_cases.gd
godot --headless --path games/yuga-native --script res://tests/ui_launch_integration_cases.gd
```

## Next panel assignments

- **Character artist and animator:** Improve groom breakup, facial expression, and garment volume on the existing rig. Swap after the first reviewed pass. Check grip, feet and cloth through moving casts and landings before promoting a new export. [Model recipe and provenance](../art/hanuman/README.md)
- **Combat designer and verifier:** Compare the effect timeline against target receipts and camera readability. Keep tuning in the ability, presentation and tail response profiles. For the browser route, verify that a late parse or first-render callback after cancellation cannot activate an old scene. [Ability design and play script](HANUMAN_GAME_DESIGN.md) · [Browser acceptance cases](research/hanuman-nov25/web-reference-patterns.md)
- **Lead:** Assign one writer per file, queue renders and imports, and pin the exact package tested. Complete visual LOD and physical GPU measurements before making performance or production-quality claims. Keep newer native branch integration and online qualification independently tracked. [Rotating panel roadmap and reuse boundaries](HANUMAN_SWARM_ROADMAP.md)
