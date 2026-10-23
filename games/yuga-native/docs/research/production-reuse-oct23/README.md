# Reuse-first production stage: one material, existing hero and existing world

23 October 2026. This stage extends the [existing reuse guide](../../REUSE_ADOPTION_GUIDE.md), [character intake](../CHARACTER_REUSE_AUDIT.md) and [next six owners](../../evidence/desktop-finish/continuation-oct18b/NEXT_SIX_OWNERS.md). It does not restart the game, replace Godot/Blender/glTF, or equate a reconstructed engine with permission to copy commercial artwork.

## Actual intake and execution

Downloaded **one** material from the official Poly Haven service: [Sandstone Blocks 05 by Rob Tuytel](https://polyhaven.com/a/sandstone_blocks_05). Its three unmodified 1K PNGs total **6,220,633 bytes**, with publisher sizes/MD5 matching and locally recorded SHA-256. The asset's official metadata gives a 3 × 3 m tile. [The source kit](../../../art/source-kits/production-reuse-oct23/sandstone-blocks-05/README.md) carries the full CC0 legal text, original files, manifest and a ready Godot material fixture.

The [official license excerpt](evidence/polyhaven-license-excerpt.md) establishes the asset grant. [API terms pinned at `2fd1796d`](https://github.com/Poly-Haven/Public-API/blob/2fd1796dc3506dfa8269439aac8e6f5c65876bd1/ToS.md) allow free commercial access and require an identifying user-agent/referer for integrated software. After inspecting these terms, metadata was re-requested with the `YUGA-Production-Reuse/1.0` user-agent; asset downloads used it too. The initial bounded research requests used curl's default user-agent and remain identified in the source ledger. No live API is needed by the game or dashboard once these maps are self-hosted.

An isolated **Godot 4.6.3 import and material-binding check passed**: three decoded 1,024 × 1,024 Texture2D resources, StandardMaterial3D, enabled normal map and red-channel roughness. [Commands, output and hashes](evidence/godot-intake.json) are retained. This is no rendered-art or runtime-promotion claim. The native-art worker has the frozen maps for a separate actual Blender composition using the existing Rama/courtyard/diya pipeline; that worker owns its image evidence.

The existing static-world optimizer was also exercised against the generated diya. Its canonical dependencies were absent in this restored cloud, so the exact adapter/lockfile were copied to scratch and `npm ci --ignore-scripts` restored **26 locked packages** without changing the project tool. [The corrected run](evidence/diya-static-preflight-qualified.json) **refused `EXT_texture_webp`**, as the current adapter's contract requires. No derivative candidate was written and source bytes stayed unchanged. The original dependency failure and successful isolated installation are retained. This is useful negative evidence: do not silently remove extension guards or claim optimization because a library exists.

## What is reused, and where

| Resource | Actual decision | Existing destination / next gate |
| --- | --- | --- |
| Poly Haven Sandstone Blocks 05, CC0 | **Downloaded and decoded.** One coherent material, not an asset library dump. API metadata is mutable; recorded response/file hashes identify this intake, not an invented Git revision. | Source kit and isolated Blender look-development. A new native material requires its own matched-image and resource-budget gate. |
| Existing YUGA Rama GLBs, original effects, authored motion and current courtyard | **Retain.** Reuse the currently identified source, not an old rejected hero or a newly substituted mannequin. | `assets/hero-rama*`, `assets/environment/lanka_courtyard.glb`, `scripts/rama_motion.gd`, `scripts/rama_ability_effects.gd`, `art/build_courtyard.py`. Inspect the exact asset selected by the native-art receipt. |
| Existing Godot TPS intake / CC-BY 3.0 motion study | **Reuse existing audited transfer path**, not a second download or a new rig. Its 145-joint robot and 56 animation entries are already inventoried; helper entries are not 56 production clips. | `art/motion/bake_tps_motion.gd`, `assets/animations/tps_rama_motion_library.tres`; one motion/contact comparison before expansion. Preserve its existing notices. |
| glTF-Transform 4.3.0 and meshoptimizer 0.24.0, MIT | **Re-exercised existing bounded adapter; current diya refused.** Exact lock and source copied outside checkout; no source edits. | `tools/reuse-art/static-world-preflight.mjs`. Future extension support needs metadata/texture preservation counterexamples and independent review before optimization. |
| Poly Haven asset-browser add-on at `1e1e1633` | **Defer installation.** README and GPL-3.0 license inspected. Its documented initial library fetch is around 3.3 GB and purchased distribution is promoted; no paid package or bulk library is needed for this 6.22 MB intake. | Optional artist convenience after measured need. The add-on's software license is separate from CC0 asset rights; no add-on code was copied or executed. |
| Khronos Sponza at `8f492390` | **Reject as a permissive shortcut.** Current per-model [license](evidence/sponza-model-LICENSE.md) and [metadata](evidence/sponza-metadata.json) identify a Cryengine Limited License, not CC0 or the metadata's CC-BY 4.0. No Sponza model/texture was downloaded. | Architecture study alone adds no reusable geometry here. Select an explicitly compatible kit rather than generalizing from the repository's name. |
| REA/Ghidra, OpenLara/OpenMW, Source SDK and Dota/Deadlock replay tools | **Retain prior bounded studies**, not another broad download. No commercial client/replay was supplied. Source SDK's mod restrictions remain separate from MIT/BSD tool licenses. | Existing [reuse systems](../REUSABLE_GAME_SYSTEMS.md) and [character audit](../CHARACTER_REUSE_AUDIT.md). A real selected input and explicit engineering question precede new native analysis. |

## Five stages for the next six-role production round

These are dependencies and acceptance checks, not completed rounds or a promise of commercial-game parity. The [machine-readable stage list](stages.json) is suitable for the progress dashboard. Desktop counts remain owned by the unchanged production ledger; Android stays deferred.

1. **Source intake — material artist + provenance reviewer.** This material's transfer/hash/decode gate is complete. Keep source kit and notices together. Judge the actual Blender result separately; no implication that every source is suitable for every city/temple surface.
2. **One composed look-development view — artist + lighting owner.** Reuse the current Rama, courtyard, new diya and this one coherent material in an isolated scene. Deliver an editable source, frozen input hashes and actual day/night images. Art direction should make the hero silhouette, grounded feet, city hierarchy and effect readable before detail multiplication. The native-art worker owns this stage's execution/evidence.
3. **One playable wind-court pilot — map owner + physics reviewer.** Follow the existing W4 task: preserve the 8 m footprint, landing plane/ring/routes, use the current material family and author a base/piers/crown with truthful collision. This material look-development does not override that no-new-texture gate. Require matched player/close/landing views, lateral motion and ray/capsule/roof support checks.
4. **One continuous hero-action sequence — motion owner + hero artist.** Keep existing skeleton and action authority, use the audited transfer pipeline for one clip, and compare root/feet/hand/bow contact through anticipation, release and recovery. Do not reopen rejected hair cap/cord/ellipse loops or claim acceptance from a mesh metric. Hair remains the existing artist-controlled cage/sculpt task.
5. **Integrate only accepted results — build owner + independent reviewer.** Run targeted authoring/import tests, verify resource/LOD/collision budgets, record full source/output identities and play the exact candidate. Finish native authority/two-client integration and FG06 full 3v3 before expanding to 6v6 or the full roster. Physical-GPU/human quality gates remain separate from CPU renders and static source checks.

For every stage, assign exclusive paths, render one heavy job at a time, retain failed attempts, and update real job state only from the owning process/result. `running` must expire when a process or heartbeat does. The dashboard is an observer, not evidence that a job was executed.

## Reproduce and inspect

[source-ledger.json](source-ledger.json) records successful and failed source requests, exact pins, hashes and retained/raw scopes. [verify_intake.py](verify_intake.py) rechecks the maps and fixture against their recorded hashes without network or rendering:

```sh
python3 games/yuga-native/docs/research/production-reuse-oct23/verify_intake.py
```

No full game was cloned, no commercial model was extracted, no asset-browser purchased, no login bypassed and no provider preview render copied. Actual downloaded art remains 6.22 MB, below the bounded intake limit. Tool dependencies are isolated scratch state. The source kit is ready for deliberate art use; final hero/map graphics quality remains an actual-image, motion and play gate.
