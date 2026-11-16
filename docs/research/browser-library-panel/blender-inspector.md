# MIT Blender source-asset inspector

16 November 2026. This bounded tool implements the useful asset-authoring
candidate from INXANITY's linked public toolkit. It is separate from game
runtime sources and changes no production asset. The original field shop was
completed and frozen before this tool continuation.

## Source and terms

The transformed-eight-corner bounds/camera-heading approach is adapted from
[universal-modder](https://github.com/rehan-remade/universal-modder/tree/3c4ac6c38e411b8c543bce217eae197039516bfc),
commit `3c4ac6c38e411b8c543bce217eae197039516bfc`:

| Exact upstream file | SHA-256 |
| --- | --- |
| `um/blender/render_sprites.py` | `358dc36a2712f640b02da6d5ce28ef48cc54daebc5a4760c790997fb2e27bd71` |
| `um/render3d.py` | `7352f7cf80f2d8b8b30e1627ba8b2786bc9c21315b89c2f55258c5b62767dfa9` |
| `LICENSE` | `db6cfa2ad2c44f73080440c866c4a3a078749d84ba40b4dfa27d50f18a525543` |

Copyright (c) 2026 Rehan and universal-modder contributors. The complete MIT
notice is retained in the tool header and
[`tools/studio/NOTICE/universal-modder-MIT.txt`](../../../tools/studio/NOTICE/universal-modder-MIT.txt).
The CLI also copies that notice to every actual inspection output. No full
toolkit installation, paid service, MCP registration or foreign game data is
required. Blender is an existing external GPL application; its license does
not change the upstream helper's MIT terms or confer rights to game assets.

## Interface and measurable output

```sh
python tools/studio/inspect-source-asset.py \
  --input games/yuga-native/assets/world/studio-relay-foundry.glb \
  --output /absolute/fresh/inspection --blender blender4.3
```

The default performs a real Blender import, census and camera fit with no
render. Add `--render --threads 8 --width 480 --height 360 --samples 8` for three
fixed Cycles CPU stills. Root schedules that render lane alongside native
captures. The input must be an embedded GLB2, no larger than 64 MiB; external
buffer/texture URIs are rejected. The output directory must not exist, including
an empty directory or symlink. A 300-second default wall limit retains partial
logs and a failed receipt; `--timeout` permits 1–600 seconds.

The tool preserves imported object transforms and metre scale. It evaluates the
importer's default pose at frame1, collects all eight world-space bound-box
corners per evaluated mesh and records mesh/triangle/material/image/armature/
action counts plus object transforms. Blender import coordinates use +Z up;
the receipt does not relabel them as native +Y coordinates.

Front oblique, rear oblique and overhead cameras are fit independently from
the actual Blender camera frame and all transformed corners. Their matrices,
orthographic scale, clips and projected corner extrema are recorded. Every
corner must fit within a 5% image border and camera clipping interval. The tool
does not normalize the asset, move its root, fabricate walking/lunging/death
motion or claim a contact review.

`config.json`, `blender.log`, `inspection.json`, `receipt.json` and the complete
MIT notice bind exact input/tool/upstream hashes. Rendered outputs additionally
bind each PNG's dimensions/bytes/hash. A zero Blender exit without an inspection
receipt is a failure. Input hash changes are failures. Existing evidence is
never overwritten by a repeat run.

## Validation status

The [initial preflight/test record](asset-spike/validation-r1.json) records 22
passing pure-Python tests and static validation of the actual original Relay
Foundry GLB. Independent review then found that an empty worker JSON with exit0
could falsely pass. The [reproduced failing test](asset-spike/review-counterexample-r1.log)
is preserved; schema/camera/PNG validation repairs it. The [successor record](asset-spike/validation-r4.json)
records 28 passing tests. Tests cover mirrored/nonuniform/rotated box corners, landscape/portrait
and asymmetric camera fit, nonfinite/degenerate geometry, malformed headers,
external dependencies, import caps, existing/symlink outputs, missing worker
evidence, retained worker failures/timeouts and the exact MIT notice hash.

The executed test command was:

```sh
python -m unittest discover -s tools/studio/tests -p 'test_inspect_source_asset.py' -v
```

Four [actual CLI rejection cases](asset-spike/preflight-cli-r1.json) also exit2:
existing evidence directory, existing symlink, malformed GLB and external
buffer. Previous evidence and the owned source GLB remain unchanged; these
commands do not launch Blender.

Root then granted the serialized render lane. One actual eight-thread
Blender4.3.2/Cycles CPU job completed with exit0 and three 480 × 360 PNGs at 8 samples.
The [actual receipt](asset-spike/render-r1/receipt.json),
[geometry/camera report](asset-spike/render-r1/inspection.json) and
[visual review](asset-spike/render-r1/visual-review.json) retain its evidence.
The exact executed command was:

```sh
python tools/studio/inspect-source-asset.py \
  --input games/yuga-native/assets/world/studio-relay-foundry.glb \
  --output /workspaces/ANDOLAN/docs/research/browser-library-panel/asset-spike/render-r1 \
  --blender blender4.3 --render --threads 8 --width 480 --height 360 --samples 8 --timeout 300
```

The unchanged 644,556-byte input hash is
`468448f03984fdaadc1be3563ed0ace75b3d635cc5c546bd321c364ae55e84cf`.
Actual measured geometry has 163 mesh objects, 14,949 evaluated vertices,
12,588 triangles, 8 materials and no armature/action. Its Blender XYZ size is
133 × 190 × 13.4000004 m. All projected corners fit the required 5% border/clips.
The post-render image census includes Blender's `Render Result`/`VIEWER`
buffer; that is not an imported texture.

All three originals were viewed: [front oblique](asset-spike/render-r1/front-oblique.png),
[rear oblique](asset-spike/render-r1/rear-oblique.png), and
[top](asset-spike/render-r1/top.png). They show the full map base and boundary,
four raised blocks, crossing/deck and opposing stations without visible border
clipping. The top view has generous side margins; small labels remain illegible
at this inspection resolution. The symmetrical oblique views are close in
appearance but use opposite camera positions and have distinct image hashes.
This is still a simple map study, not final environment art.

These checks cannot accept collision, traversal, rig deformation, combat timing,
contact, native integration, production art or hardware FPS.
Object/vertex caps are enforced after import; the 64 MiB file cap is not a
peak-memory guarantee for arbitrary complex inputs. The actual input is the
stable original 630 KiB Relay Foundry model, not hostile unknown content.

Owner: `/root/reuse_build_panel`. Baseline commit
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, shared `work/yuga-studio` checkout.
Next owner: root for native integration/art acceptance after the isolated tool
receipt and stills are reviewed. Existing exports remain untouched.
