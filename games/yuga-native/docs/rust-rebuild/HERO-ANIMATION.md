# Hanuman's Rust asset pipeline

The Rust build carries Hanuman's existing Blender skin, teeth, face, articulated tail, gada, jewelry and cloth into the browser. In the native trial, a second motion library replaces five animations after the model loads. Shipping the original GLB alone plays earlier versions of all five attacks. The Rust exporter resolves those replacements into a single portable GLB. The rig retains its 167 joints, 105,848 triangles, 17 draw surfaces, 17 materials, 14 embedded images and all 11 clip names. The mesh faces +Z with +Y up. [Source character and build recipe](../../art/hanuman/README.md) · [Native motion library](../../assets/heroes/hanuman/hanuman-ability-motion.tres) · [Rust exporter](../../../yuga-rust/src/hero.rs)

## Five panel decisions

| Round | Question from the moderator | Result |
| --- | --- | --- |
| 1 · Discovery | Which inputs already ship? | Located the visual GLB, editable Blender scene, the native trial's separate action overrides, and MakeHuman donor provenance. Located three Rust game-format projects and two reusable Rust engine libraries. |
| 2 · Source trace | Which code or data belongs in the playable build? | Selected YUGA's own mesh, rig, clips and marker data. Selected the gltf-rs binary parser and validator. Recorded applicable techniques and terms for the other libraries below. |
| 3 · Implementation | Can a portable mesh reproduce the native action contract? | Implemented a native Rust packer that binds channels to named joints and rewrites the five action definitions in place. All six remaining clip definitions and the original visual bytes survive the transformation. |
| 4 · Cross-engine challenge | Does the actual browser animation sampler produce the same poses? | Compared every joint against independent Godot AnimationPlayer captures. Long wrist rotations drifted by up to 9.10 mm under PlayCanvas component interpolation. The packer now subdivides only large quaternion arcs on their spherical path. |
| 5 · Acceptance | Can another contributor repeat the result and detect wrong inputs? | Recorded the exact source and export digests, 82,164 independent joint comparisons, malformed-source checks, deterministic output and an exact visual preservation check. |

## Why these Rust sources were selected

| Project and verified license | Source inspected | Decision for YUGA |
| --- | --- | --- |
| gltf-rs 1.4.1, MIT or Apache-2.0 | The version in Cargo.lock exposes the JSON and binary chunks through `Glb`, serializes chunk lengths and padding, and validates the resulting typed glTF document. | **Compiled into the native packer.** Existing mesh and texture buffer ranges survive export. The runtime downloads the resulting GLB. Crate archives record the linked revision in `.cargo_vcs_info.json`. [Binary reader/writer](https://github.com/gltf-rs/gltf/blob/0f1e94f5e2307de7336be6d3a65c38c4d34aea08/src/binary.rs) · [Document validation](https://github.com/gltf-rs/gltf/blob/0f1e94f5e2307de7336be6d3a65c38c4d34aea08/src/lib.rs) · [Manifest and terms](https://github.com/gltf-rs/gltf/blob/0f1e94f5e2307de7336be6d3a65c38c4d34aea08/Cargo.toml) |
| xc3_lib / xc3_model, Xenoblade-format tools, MIT | The exporter converts source frames to seconds, shares time accessors, resolves bone index/hash/name and samples the source skeleton in local space. Its glTF node mapping assumes contiguous joint IDs. | Adopted the shared-time-accessor approach for YUGA's irregular authored key times. Resolve joints by the original skin's actual node IDs. The original game reader and Nintendo game assets are outside this build. [Animation export](https://github.com/ScanMountGoat/xc3_lib/blob/3e47cf2f20bc4bee35d804058f659507208e2d01/xc3_model/src/gltf/animation.rs#L6-L97) · [Skeleton and animation transforms](https://github.com/ScanMountGoat/xc3_lib/blob/3e47cf2f20bc4bee35d804058f659507208e2d01/xc3_model/src/animation.rs#L182) · [License](https://github.com/ScanMountGoat/xc3_lib/blob/3e47cf2f20bc4bee35d804058f659507208e2d01/LICENSE) |
| ssbh_wgpu, *Super Smash Bros. Ultimate* format renderer, MIT | Its evaluator separates local sampling, parent transforms, scale compensation, endpoint handling, aim/orient constraints and skin matrices. Its Criterion fixture independently stresses multi-root and deep-chain rigs. | Used as a reference for measuring the whole animated joint hierarchy. Profile the long spine-to-hand and tail chains before considering its constraint approach for procedural follow-through. YUGA's glTF joint order and scale rules remain authoritative. [Skeleton update and looping](https://github.com/ScanMountGoat/ssbh_wgpu/blob/4982d806cfd70b8ba328be53e2ece2e52e173fe7/ssbh_wgpu/src/animation.rs#L176-L256) · [Constraint implementation](https://github.com/ScanMountGoat/ssbh_wgpu/blob/4982d806cfd70b8ba328be53e2ece2e52e173fe7/ssbh_wgpu/src/animation/constraints.rs#L16) · [Benchmarks](https://github.com/ScanMountGoat/ssbh_wgpu/blob/4982d806cfd70b8ba328be53e2ece2e52e173fe7/ssbh_wgpu/benches/animate_skel.rs#L22) · [License](https://github.com/ScanMountGoat/ssbh_wgpu/blob/4982d806cfd70b8ba328be53e2ece2e52e173fe7/LICENSE) |
| Eurochef, Eurocom EngineX tools, MIT | Its Rust reader documents uncertain skin fields. The CLI has platform gates, extracts images from EDBs, constructs output scenes and has a game/version-specific support matrix. | Useful if a separately distributable EngineX fixture needs conversion. No YUGA asset uses EDB. Adding the CLI to this build would introduce an asset dependency without improving Hanuman. [Skin layout](https://github.com/eurotools/eurochef/blob/71dca6b7b6f673e7c3027d7f88579b8b7d6c3f61/eurochef-edb/src/anim.rs#L12) · [Importer](https://github.com/eurotools/eurochef/blob/71dca6b7b6f673e7c3027d7f88579b8b7d6c3f61/eurochef/cli/src/edb/animations.rs#L22) · [Support matrix](https://github.com/eurotools/eurochef/blob/71dca6b7b6f673e7c3027d7f88579b8b7d6c3f61/README.md) · [License](https://github.com/eurotools/eurochef/blob/71dca6b7b6f673e7c3027d7f88579b8b7d6c3f61/LICENSE) |
| Bevy 0.17.2, MIT or Apache-2.0 | An example assigns different footstep times to individual bones. The transition system separately advances active clips and removes finished fades. | Reference for the next desktop renderer and event-only footfalls, dust and mace trails. Damage, ward protection and physical landing continue to use authoritative combat ticks. [Targeted animation events](https://github.com/bevyengine/bevy/blob/566358363126dd69f6e457e47f306c68f8041d2a/examples/animation/animated_mesh_events.rs#L142-L175) · [Transition system](https://github.com/bevyengine/bevy/blob/566358363126dd69f6e457e47f306c68f8041d2a/crates/bevy_animation/src/transition.rs#L78-L147) · [MIT terms](https://github.com/bevyengine/bevy/blob/566358363126dd69f6e457e47f306c68f8041d2a/LICENSE-MIT) |

The actual media donor is the project's existing MakeHuman CC0 geometry, targets, joint definitions and weights, alongside YUGA-authored surfaces, textures and motion. The repository pins the original MakeHuman revision and inputs. The code licenses of game-format utilities cover those utilities. Their source trees do not grant a license to commercial character models. [Character provenance](../../art/hanuman/NOTICE.md) · [Source manifest](../../art/hanuman/manifest.json) · [REA and independent Rust rebuild inventory](REA-AND-REBUILDS.md)

## Playback and export contract

The packer checks the source model hash stored by the motion authoring step. Each Godot `position_3d` or `rotation_3d` track resolves to one skin node. The source uses 73 rotation and three position tracks per revised action, including fourteen nearest-neighbor samplers. The other 62 tracks per action use linear translation or spherical rotation in the native player. Source and target share skeleton-local coordinates. Pose comparison includes the root, finger joints, tail and all descendants.

| Action | Track | Authored duration | Release fraction | Later contact fraction |
| --- | --- | ---: | ---: | ---: |
| Vajra Gada | `fire` | 0.7333 s | 0.26 | At release |
| Vajra Kavacha | `cast2` | 1.0333 s | 0.50 | At release |
| Maruti Udayana | `cast1` | 1.0333 s | 0.08 | 0.72 at physical landing |
| Lanka Dahan | `tail_sweep` | 1.0333 s | 0.50 | At release |
| Mountain Pulse | `mountain_pulse` | 1.3333 s | 0.55 | 0.78 at payload impact |

The exporter places durations and normalized phase markers in `animations[i].extras.yuga`. Combat reads the same authoring source at compile time. On each display frame, the browser seeks the action to `active.motion_phase_normalized × track.duration`. Windup ends at release, travel ends at physical contact and recovery ends at 1.0. A shortened vault reaches its landing pose at the detected collision. Only run and idle loop. A continuing burn field retains its cast ID separately after the action releases the actor. [Native stage transitions](../../scripts/hanuman_actor.gd) · [Rust timing](../../../yuga-rust/src/combat.rs) · [Browser animation consumer](../../../yuga-rust/web/scene.ts) · [Combat details and tests](COMBAT.md)

The exporter normalizes each source quaternion, checks increasing key times and ensures every action spans its declared duration. For a linear quaternion sampler it computes the shortest angular path between keys and inserts intermediate spherical samples if a span exceeds 0.12 radians. This bounds the discrepancy when PlayCanvas performs normalized component interpolation. The fourteen step channels retain their exact discontinuities. The previous model's 425 other channels per replaced clip sampled as bind-pose constants at the stored keys. The old six locomotion and ancillary clip definitions, every preceding accessor and buffer view, all visual JSON fields and the entire 7,912,960-byte original BIN chunk pass preservation checks. The new file occupies 9,212,156 bytes. [Packer](../../../yuga-rust/src/hero.rs) · [Exact preservation and malformed-input checks](../../../yuga-rust/tools/check_hero_export.py)

## Cross-engine acceptance

Godot 4.6.3 sampled its existing trial GLB and the five native override clips through the actual AnimationPlayer. PlayCanvas 2.23.3 loaded the exported glTF node graph and original animation accessor bytes through its production parser, evaluator, binder and scene transform code. The CPU probe omits render resources from the in-memory parsing fixture. Each clip was checked at 97 evenly spaced instants plus its authored markers. Across 167 joints and 492 sampled poses, the maximum position difference was **0.00711 mm** and the maximum Euclidean difference between corresponding unit-basis columns was **0.00001684**. Acceptance limits are 0.2 mm and 0.0002 respectively. The probe records per-clip maxima and the worst-position bone and time. [Native sampler](../../../yuga-rust/tools/verify_hero_motion.gd) · [PlayCanvas sampler](../../../yuga-rust/tools/check_hero_pose.mjs) · [Machine-readable evidence](HERO-POSE-EVIDENCE.json)

A trial comparison that reimported both GLBs through Godot's default 30 Hz importer produced up to 101 mm of apparent divergence on steep curves. That second import resamples the exported channels and measures a different playback path. The retained test uses the original native AnimationPlayer on one side and PlayCanvas's real glTF evaluator on the other. This test establishes joint-transform agreement on the five sampled attacks. New skin topology, facial expression controls, costume collision, GPU frame time and transitions under network reconciliation require separate visual or hardware tests.

### Reproduce from the repository root

Install the root npm lockfile dependencies, the repository's Rust toolchain, Python 3 and Godot 4.6.3. Use fresh scratch paths. The capture file is about 20 MB and is generated locally.

```sh
game=games/yuga-rust
hero=games/yuga-native/assets/heroes/hanuman
work=$(mktemp -d)
mkdir "$work/native"
printf 'config_version=5\n[application]\nconfig/name="Hero pose oracle"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n' > "$work/native/project.godot"
cp "$hero/hanuman.glb" "$work/native/base.glb"
cp "$hero/hanuman-ability-motion.tres" "$work/native/motion.tres"
cargo test --locked --manifest-path "$game/Cargo.toml" --lib hero::tests
cargo run --locked --manifest-path "$game/Cargo.toml" --bin hero_export -- \
    "$hero/hanuman.glb" "$hero/hanuman-ability-motion.tres" "$work/hero.glb"
python3 "$game/tools/check_hero_export.py" "$game/target/debug/hero_export"
godot --headless --path "$work/native" --import
godot --headless --path "$work/native" --script "$PWD/$game/tools/verify_hero_motion.gd" -- "$work/native.json"
node "$game/tools/check_hero_pose.mjs" "$work/hero.glb" "$work/native.json"
```

### Next hero and desktop milestones

1. Select the next YUGA hero from a ledger entry with an editable rig, original visual GLB, media terms and a clip-to-ability manifest. Measure facing, model units, bind pose and joint naming before planning a Hanuman retarget. Reserve the existing mace, grasp and tail channels for characters with compatible anatomy.
2. Replace the Hanuman-specific clip list and Godot path prefix with per-hero manifest data when a second rig is ready. Extend the TRES subset only for tracks that the second source actually uses. Check unmatched joints, remapped abilities, scale keys, additive layers, IK and clips with missing end samples.
3. Bind effects to named source sockets. Capture native transforms and projected silhouettes at windup, contact and recovery for at least two remote-actor camera distances. Include defeat, cancel, repeated-cast, crossfade and physical landing cases in the online renderer.
4. Profile actual full-team scenes and hardware. Measure skinning/upload time, animation evaluation, draw surfaces, texture residency and costume intersections on the target GPU. Use the existing artist-authored close-up as the reference when deciding LOD thresholds or texture compression. [Original studio reference and outstanding visual work](../../art/hanuman/README.md)
