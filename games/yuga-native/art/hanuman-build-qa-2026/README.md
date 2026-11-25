# Hanuman facial study · playable preview

The separate [sculpt-preview ZIP](../../../yuga-rust/downloads/yuga-rust-hanuman-sculpt-preview.zip?raw=true) embeds the [V1 facial candidate](../hanuman-facial-refinement-2026/README.md) in the existing Rust/Wasm game. Its facial change is small. It does **not** include the rejected V2 contact fit or the separate skin-material study. The ordinary Confluence download and its baseline model remain unchanged. Both packages retain private 5v5 hero-only rooms and no soldier waves.

## What was checked

| Check | Result and scope |
| --- | --- |
| Packaged source | ZIP SHA-256 `60e971ccf925a23cda480d56bd7046270ae5657e06c55e4319eb1dfa9b8bc966`; embedded candidate SHA-256 `257ff4daf8694d682acc4dbfd171729ed2d5575225cfa9259533c1e9eb113abf`. [Build manifest](build-v1.json) · [release check](release-check-v1.json) |
| glTF | [Khronos validator](gltf-validation-v1.json): zero errors and the same one pre-existing skinned-mesh parent warning as the baseline; both have 143,432 triangles. |
| Actual browser | [39 checks](browser-practice-v1.json) in headless Chromium/SwiftShader exercised the packaged practice with Hanuman's five abilities, keyboard/mouse input, pose visibility, mute, pause, reset, resize and WebGL fallback. [Gameplay frame](browser-practice-v1.png) · [completion frame](browser-complete-v1.png). |
| Five-person teams | [Ten WebSocket peers](five-team-rooms-v1.json) joined the extracted package's local Wasm room host, five per team, with nine remote heroes in each authority view and no wave units. A separate [Chromium client with nine peers](five-team-browser-v1.json) rendered nine heroes and accepted keyboard movement. [Screenshot](five-team-browser-v1.png). These tests did not render ten browser clients or test a public network. |
| Rig and geometry | [Independent rig checks](../hanuman-rig-qa-2026/README.md) compare all joint/animation data and 20 evaluated poses. [Matched visual review](../hanuman-visual-qa-2026/README.md) found the V1 change subtle and rejected the V2 mouth contact fit for its profile. |

These checks do not establish a realistic finished face, competitive balance, human animation acceptance, WAN performance or target-GPU performance. An image-generated [turnaround](../hanuman-turnaround-2026/README.md) is a visual reference rather than the actual mesh.

## Rebuild and compare

From the repository root, use the normal Rust and Node prerequisites in the [game build guide](../../../yuga-rust/README.md). The optional model argument preserves the normal build's default asset and records the exact embedded model hash.

```sh
python3 games/yuga-rust/tools/build_web.py \
  --hanuman-model games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-candidate.glb \
  --output /tmp/yuga-hanuman-preview
node games/yuga-rust/tools/test_hanuman_release.mjs \
  --zip /tmp/yuga-hanuman-preview/yuga-rust-confluence.zip \
  --hanuman-model games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-candidate.glb
```

The verifier rejects a mismatched supplied model by digest. The GLB selection is not a substitute for rights, rig, motion or visual review. For additional authoring, use the [anatomy and geometry notes](../../docs/design/hanuman-anatomy-geometry-2026/README.md), the [skill-pack review](../../docs/research/gamedev-agent-skills-2026/README.md) and the [existing artist handoff](../hanuman-hero-finish/HANDOFF.md).
