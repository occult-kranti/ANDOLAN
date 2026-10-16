# Deadlock video access and public tooling study

Checked 2026-10-16T17:13:21.209142+00:00. This is a source-pinned tool/documentation study. No Deadlock footage was watched, game binary opened, replay parsed or commercial asset extracted in this pass.

## Video access ledger

| Target | Actual result | Observation status |
| --- | --- | --- |
| [Official Deadlock home](https://www.playdeadlock.com/) | CONNECT tunnel rejected with HTTP403 by the configured environment network path | Not watched; no page/video content received |
| [Official Steam listing/API](https://store.steampowered.com/api/appdetails?appids=1422450) | CONNECT tunnel rejected with HTTP403 | Could not discover its current trailer URLs |
| [YouTube gameplay search](https://www.youtube.com/results?search_query=deadlock+official+gameplay) | CONNECT tunnel rejected with HTTP403 | No search results or individual video timestamps retrieved |

`ffmpeg` and `ffprobe` exist at `/usr/bin/ffmpeg` and `/usr/bin/ffprobe`. Their availability does not mean a video was downloaded or inspected. There are no timestamped visual observations to report. Network/TLS policy was preserved; no alternate proxy or certificate bypass was used.

## Accessible licensed tools

| Repository and pinned revision | License | What was actually inspected | What it could support with an appropriate lawful input |
| --- | --- | --- | --- |
| [ValveResourceFormat/ValveResourceFormat](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/8be8f9387a894281da6251a091253e00e229f335/README.md) · `8be8f9387a894281da6251a091253e00e229f335` | MIT | README, MIT license, format-support guide, AnimationController and glTF animation/skeleton exporter source | Model/skeleton inspection and per-frame animation export; compiled-resource reconstruction is different from recovering original game source. |
| [saul/demofile-net](https://github.com/saul/demofile-net/blob/fd59701a998cf30a46adc4942e063d90de73c07a/README.md) · `fd59701a998cf30a46adc4942e063d90de73c07a` | MIT | README support table and tick/entity examples; repository license metadata | DeadlockDemoParser, event/entity updates, tick-level position analysis and seeking. README examples may target CS2 and must not be silently treated as Deadlock results. |
| [Rupas1k/source2-demo](https://github.com/Rupas1k/source2-demo/blob/48fbddc0939d8a7963c4dd9df00b96a6ea5c7d98/README.md) · `48fbddc0939d8a7963c4dd9df00b96a6ea5c7d98` | Apache-2.0 | README Deadlock feature and anonymization example; repository license metadata | A Rust replay parsing path with the deadlock feature, plus entity/message inspection. |
| [pnxenopoulos/boon](https://github.com/pnxenopoulos/boon/blob/0c7663f17aa24a65374925b022fd4d98aaa47477/README.md) · `0c7663f17aa24a65374925b022fd4d98aaa47477` | MIT | README dataset tables and lazy-loading examples; repository license metadata | Player position/health, damage, ability cooldown/use, objectives and opt-in lane trooper datasets for measured replay analysis. |

These are public-source capabilities, not executed extraction results. No commercial game data was supplied. The software licenses describe the tools; they do not transfer rights to third-party game assets. The YUGA model pipeline uses its separately documented MakeHuman CC0 foundation and authored hero assets.

## Five practical YUGA checks informed by the sources

| Lesson / testable change | Evidence basis | YUGA acceptance gate |
| --- | --- | --- |
| Inspect the posed mesh, not merely a clip name. | The [VRF controller](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/8be8f9387a894281da6251a091253e00e229f335/Renderer/Animation/AnimationController.cs) maintains decoded frame, playback time and flattened bone poses; the [exporter](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/8be8f9387a894281da6251a091253e00e229f335/ValveResourceFormat/IO/Gltf/GltfModelExporter.Anim.cs) writes per-frame local transforms. | All14 real GLBs must load, bind weights must be finite/normalized, and all9 clips receive sampled skinned-vertex checks plus native browser state transitions. |
| Treat root motion separately from authoritative movement. | The exporter explicitly handles root movement separately from bone frames and bakes it into root bones when exporting. | YUGA actor translation remains simulation-owned; exported armature/root translation stays stationary within1mm. Run/cast/jump transitions are checked for visual drift. |
| Preserve attack timing and state independently of cosmetics. | [Boon's documented datasets](https://github.com/pnxenopoulos/boon/blob/0c7663f17aa24a65374925b022fd4d98aaa47477/README.md) distinguish ability ticks/use, damage events and player state. This describes an analysis method, not an observed Deadlock combat sequence. | Record cast-start, release, hit and recovery from authoritative YUGA snapshots; a dodge must move out before release and prevent the corresponding damage. Test windup telegraphs and result cues at native input speed. |
| Test materials, cloth and collision separately after interchange. | [VRF format support](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/8be8f9387a894281da6251a091253e00e229f335/docs/guides/format-support.md) documents additive-animation/glTF differences, flattened materials, missing hitboxes and constraint/cloth limitations; it also labels some Deadlock shading work in progress. | Do not infer collider correctness, cloth quality or appearance from a successful GLB load. Inspect weapon grip, clothing penetration and low/high rendering; keep gameplay hit rules on the shared simulator. |
| Measure lane pressure and objectives from events before changing balance. | Boon documents objectives and opt-in trooper state per tick; demofile-net documents tick/entity inspection. | For YUGA, report role-specific lane progress, siege arrival, objective damage, duration, KDA and support outcomes across mirrored seeded matches. Separate bot-policy bias from human balance and keep optional counters readable in the HUD. |

These are proposed design/QA lessons grounded in inspected tooling, not claims about footage, proprietary implementation, exact Deadlock timing or game balance. A genuine future video study needs a reachable public clip, its exact URL, timestamps, captured frames and observations separated from interpretations.

## Relation to REA

REA and decompiler/viewer tools can make available evidence easier to inspect. Without a game binary or replay they cannot establish the original netcode, animation graph, hit rules or balance constants. The Deadlock-specific portion above used GitHub documentation and source reads only. Existing YUGA mechanics remain original implementations; this work does not claim that Deadlock was reverse engineered.

## Executed REA study of licensed open shooter aiming

The existing REA6.5.0 installation actually analyzed two files from the MIT-licensed [Mugen87/dive shooter AI showcase](https://github.com/Mugen87/dive/tree/7176136cf6c29eddfd620df2bf0d09a532680763), pinned to `7176136cf6c29eddfd620df2bf0d09a532680763`. Its JavaScript analyzer received `src/core/TargetSystem.js` and `src/core/WeaponSystem.js`, a256MiB worker heap limit and30s per-source timeout. Exit0 produced Evidence `ev_7b62bd19d270f937a89b3940e35171aaf674053d842b6b63a2df684b544054c7`: two parsed files,46 findings,2338 semantic nodes and1635 relations. Coverage remains **unknown**, with909 unresolved items and no retained call-flow relations. Successful parsing is not a complete reconstruction of the game's execution.

Manual reading of those same pinned sources establishes a narrower useful distinction: [TargetSystem](https://github.com/Mugen87/dive/blob/7176136cf6c29eddfd620df2bf0d09a532680763/src/core/TargetSystem.js#L30) can retain a remembered hidden opponent, but its separate `isTargetShootable()` check requires visibility. [WeaponSystem](https://github.com/Mugen87/dive/blob/7176136cf6c29eddfd620df2bf0d09a532680763/src/core/WeaponSystem.js#L539) requires a shootable target, completed rotation and elapsed reaction delay before the bot's firing branch. Looking toward a memory is distinct from permission to shoot it.

REA also executed `import-reference-source` on selected GPL-2.0 [Quake III source](https://github.com/id-Software/Quake-III-Arena/blob/dbe4ddb10315479fc00086f08e25d968b4b43c49/code/game/ai_dmq3.c), pinned to `dbe4ddb10315479fc00086f08e25d968b4b43c49`. That operation hashed/inventoried the source and license as a historical reference; **it did not parse C semantics**. Manual reading of `BotAimAtEnemy` and `BotCheckAttack` identified separate configurable reaction/accuracy, projectile prediction, visibility, firing-cone, world-trace and teammate-obstruction checks. The old bot implementation also has remembered-position and challenge-mode behavior; it is not a specification for YUGA's optional player assistance.

The original YUGA acceptance rules derived from this study are: keep target selection separate from authoritative hit resolution; reject cover and invalid targets before showing a lock cue; clear assistance when a menu or manual aim takes control; and measure bounded camera turning independently of actual projectile collision. No reference source, constants or assets were copied into the game, and neither reference game was executed. Exact command, source/license hashes, result hashes and limitations are recorded in [rea-open-shooter-aim.json](../docs/evidence/rea-open-shooter-aim.json).
