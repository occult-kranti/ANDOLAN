# Agentic cinematography: source review and YUGA camera study

This packet records the supplied Sirio/Fable/Seedance suggestion, a local test of a public editor copy, and a separate camera study made with Sirio Berati's independently published camera-control engine. It is a **previsualization experiment**. No generated clip is a rigged character, gameplay animation, map or playable-game feature. [YUGA camera reference clip](preview/YUGA01-MountainPulse.mp4) · [Start, middle and end stills](preview/) · [Video and captions research](VIDEO_RESEARCH.md) · [Next production work](../../docs/design/five-round-panel-2026/NEXT.md)

## What we could verify

| Item | Source and status | Relevance to YUGA |
| --- | --- | --- |
| **Seedance 3D Blockout Editor** | A public [third-party copy](https://github.com/cbunseng/seedance-blockout-editor-private/tree/da359cd49837b76c2a26b768b66d26a0bf251b62) describes the editor and carries an Apache-2.0 license and Sirio Berati copyright notice. The latest commit names Sirio as author. The copy belongs to another GitHub account, so its distribution provenance and whether it is the exact post described by the user are not independently confirmed. | In an isolated local checkout, its bundled 20-shot example passed its camera check. We opened the editor with outside requests and its helper blocked, dismissed the tour, and added a camera key. [Check output](evidence/mirror-check.txt) · [Contact sheet](evidence/mirror-contact-shots.png) · [Editor test](evidence/mirror-editor-test.json) · [Editor screenshot](evidence/mirror-editor.png) |
| **Sirio's camera-control pipeline** | [Creator-owned GitHub project](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/tree/602aa2348b0ae67589ce533fff571adced724811), MIT licensed. Its README describes a three.js/Remotion reference-film workflow with placeholder actors and camera templates. | We adapted a four-second orbit for a YUGA Mountain Pulse shot and rendered the reference locally. This is a related published tool, not proof that the editor above came from that repository. |
| **Claude Fable 5.2** | [Anthropic describes it](https://www.anthropic.com/claude/fable) as an AI model for technical and coding work. The supplied claim that this particular editor was built with it has not been independently checked. | A coding assistant could help author a shot. Fable itself is not identified in the primary source as a 3D rendering engine. No Claude model was invoked in this test. |
| **Seedance 2.5** | [ByteDance describes it](https://seed.bytedance.com/en/seedance2_5) as an audio-video generation model. [Sirio's Tein instructions](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/blob/602aa2348b0ae67589ce533fff571adced724811/docs/tein-endpoint.md) describe a separate account and API/MCP key for generation. | Optional future cinematic drafts. Provider access, cost, terms, input rights and the actual API response need their own review. We sent no assets or requests to Tein or Seedance and generated no AI video. |

The editor copy's CLI sample was tested with its bridge blocked. For the separate interactive smoke test we served its static files on loopback, blocked all other requests, skipped the tour and used **Set key**. The key count changed from zero to one and the browser reported no page exceptions. The blocked helper means project persistence, agent controls and Generate were not tested. The screenshots depict that editor's example scene, not YUGA assets. We did not verify the supplied OpenPose and exact feature claims exhaustively. The copy's [Apache license](LICENSE-EDITOR-APACHE-2.0.txt) and [notice](NOTICE-EDITOR.txt) are retained alongside its test images.

## Local YUGA shot

The [shot source](yuga-mountain.ts) uses the creator's orbit rig: a 35 mm full shot moves from 20° to 110° over four seconds. It shows a striped placeholder in the upstream neutral lab and contains no attack, facial performance, Hanuman rig or impact effect. The title identifies the intended future shot; the authority's release at tick 14 and impact at tick 23 are not animated in this clip. Use it to discuss camera framing, not to judge finished art.

The 480 × 270, 24 fps clip contains 96 video frames. It was rendered with local Chromium/SwiftShader, not a physical GPU, and decoded with FFmpeg. The video SHA-256 is `ea147aee2afa75e3d662b67927c78513429d66e2352161b8bab515620d1d2414`. The render reported 281 seconds on this cloud instance; that is one run, not a device benchmark. [Render output](evidence/local-render.txt) · [Individual stills](evidence/local-stills.txt)

The original upstream type check reported two `TS2352` casts in `cameras.ts`. Our [compatibility patch](compatibility.patch) adds the missing optional type fields, registers the new shot, and points the renderer at a configurable local Chromium using `swangle`. A fresh sparse checkout with the included lockfile passed `npm run check` and reproduced all three stills byte for byte on the same machine. It is an adaptation of the MIT-licensed upstream project, not an upstream fix. [License](LICENSE-SIRIO-MIT.txt) · [Original type errors](evidence/upstream-typescript-failure.txt) · [Fresh preparation](evidence/repro-prepare.txt) · [Fresh stills](evidence/repro-stills.txt)

## Reproduce the camera study

Use Node 22.12 or newer, Git, npm, a Chromium executable and a WebGL-capable setup. The preparation script creates a **new** directory, checks out the pinned upstream commit, checks/applies the patch, copies the shot and lockfile, installs dependencies with lifecycle scripts disabled, and runs TypeScript checking. It refuses to overwrite an existing path. No API key is needed for these steps.

```sh
packet=games/yuga-native/art/agentic-cinematography-2026
"$packet/prepare.sh" /tmp/yuga-sirio-checkout
CHROMIUM_BIN=/usr/bin/chromium "$packet/render.sh" /tmp/yuga-sirio-checkout /tmp/yuga-sirio-output stills
CHROMIUM_BIN=/usr/bin/chromium "$packet/render.sh" /tmp/yuga-sirio-checkout /tmp/yuga-sirio-output video
```

`YUGA_GL` can override the default Remotion `swangle` backend. A different Chromium or graphics stack can produce different pixels. The pinned source and dependency lockfile, commands, original attribution and output hashes let a later worker repeat the study. The separate third-party editor copy is not installed by these scripts.

## Proposed adoption gates

1. Obtain the creator's original editor link or files, verify provenance, version and distribution terms, and audit its code before using the copy for production.
2. Export a camera path or shot sheet and test its timing against an existing Hanuman Blender scene. Match coordinate axes, lens, frame rate and authoritative action beats; validate collisions, visibility and contact on the actual model.
3. Review a local reference and its cost/privacy terms before any optional external generation. Establish authorized inputs and provider access; never put keys in the project or silently upload assets.
4. Compare generated cinematic takes for character consistency, camera adherence and temporal artifacts. A successful video is a reference for artists, not evidence of a game-ready mesh, rig, animation or runtime performance.
5. Promote an asset only after the existing rig/export, ability timing, multiplayer readability, licensing and target-device tests pass. [Motion production plan](../../docs/design/five-round-panel-2026/NEXT.md)
