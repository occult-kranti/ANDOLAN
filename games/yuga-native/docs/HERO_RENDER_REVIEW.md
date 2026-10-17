# Actual-render hero review

`tools/capture-hero.gd` builds an explicitly staged Godot studio and saves actual rendered PNGs of an imported hero. It is an art inspection tool, separate from gameplay and native-window input review. It does not generate a replacement concept image or claim a commercial game's graphical quality.

The default asset is `res://assets/heroes/rama-production.glb`. The scene uses the existing authored mesh, skeleton, materials and animations. It does not alter the asset. A neutral studio floor, warm key, cool fill, rim light and Filmic tonemapping expose silhouette and material relationships. Bloom is disabled for surface inspection.

## Run after the final asset import

Use an owned real display and renderer. In this cloud environment, root manages Xvfb with MIT-SHM disabled and the task-local Mesa Vulkan driver. Software Vulkan produces actual rendered pixels, but it is not evidence of hardware performance.

```sh
export XDG_DATA_HOME=/workspace/tooling/native-render/xdg/data
export XDG_CONFIG_HOME=/workspace/tooling/native-render/xdg/config
export XDG_CACHE_HOME=/workspace/tooling/native-render/xdg/cache
godot --headless --path games/yuga-native --editor --import --quit

# DISPLAY must identify the already-started, owned X server.
# Preserve its configured Vulkan/Mesa environment when running this command.
timeout 300s godot --path games/yuga-native \
  --display-driver x11 --rendering-method forward_plus \
  --audio-driver Dummy --resolution 960x960 \
  --disable-vsync --script res://tools/capture-hero.gd -- \
  --output=/tmp/yuga-production-hero-review-v2 --timeout=240
```

The capture tool deliberately rejects `--headless`. It checks the GLB import stamp against both the original source and imported scene, preventing a newer source hash from being attached to an older cached model. It waits for real `RenderingServer.frame_post_draw` signals from a deferred asynchronous capture sequence. It never captures from `_process()`.

Use a **new output directory for each review attempt**. The cooperative timeout is checked between rendered frames; the external `timeout` also bounds a stalled renderer. Supported tool arguments after `--` are:

- `--asset=res://assets/heroes/rama-production.glb`
- `--output=/absolute/path`
- `--width=960` and `--height=960`, each constrained to 480–1600 pixels
- `--timeout=240`, constrained to 10–600 seconds
- `--fractions=/absolute/pose-fractions.json` for explicit animation sample overrides

## Captures and framing

The tool produces 13 frames: full-body front, rear, side and 33-degree front three-quarter idle views, followed by one sampled pose for each of the nine clips. Front and rear use identical camera height, target and distance. The camera distance is 5.1 metres at a 32-degree vertical field of view; the earlier 4.3-metre framing clipped the bow in root's first actual-render review and is superseded.

The current pose samples are equation-guided selections from the retained animation source, not measured curve extrema:

| Clip | Fraction of duration | Inspection purpose |
|---|---:|---|
| idle | 0.25 | Rest silhouette and attachment placement |
| fire | 0.25 | Release plateau / bow grip |
| cast1 | 0.25 | Primary cast release plateau |
| cast | 0.50 | Raised-arm pose |
| cast2 | 0.50 | Forward lean |
| cast3 | 0.6625 | First authored volley pulse candidate |
| run | 0.25 | Opposing limb travel |
| jump | 0.50 | Tucked airborne pose |
| defeat | 0.88 | Late defeat pose |

For an additional contact-pose review, pass a JSON override such as `{"jump": 0.0}` and use another output directory. A frozen jump-start pose is still distinct from a physics landing test. The files report the exact sampled time and duration regardless of the descriptive purpose.

## Evidence and acceptance

`hero-render-review.json` records completion, source GLB SHA-256 before/after, verified import checksums, imported scene SHA-256, tool SHA-256, Godot version, renderer, graphics adapter, display server, camera settings, animation times, finite sampled bone transforms and every PNG hash. Each image contains a visible staged-review label. A nonzero exit or `complete: false` preserves a failed/partial attempt; it must not be described as a complete review.

Root's first production capture demonstrated that the tool rendered, but showed bow framing defects. Preserve those frames as an earlier attempt. Final acceptance must use the corrected camera, the final grip-corrected model hash and a fresh import.

Visual inspection should check:

1. Full crown, bow, feet and mantle remain inside the frame without overlapping labels.
2. Cobalt cloth, ivory fabric, warm skin and gold remain distinguishable without clipped highlights.
3. Front and rear silhouettes reveal bow grip, quiver, shoulder asymmetry and mantle tails.
4. Every sampled pose has readable joint placement, intact attachments and no obvious cloth/weapon/body intersections.
5. The rendered result matches the requested art direction; finite transforms alone do not establish that result.

Thirteen stills do **not** establish animation continuity, every transition, gameplay responsiveness, all lighting conditions or all viewing angles. Continuous animation review and actual native input tests remain separate gates. No frame-rate or AAA-parity claim follows from these captures.

## Native mouse review

The separate `tools/native-window-review.py` still accepts the original coordinate click command. It additionally supports a held button without warping the captured pointer:

```json
{"action":"click","move":false,"seconds":1.0}
```

`move` defaults to `true`, and `seconds` defaults to `0.15`. Durations are finite and bounded to 0.05–5 seconds. This supports slower software-rendered input review while recording the actual hold duration. It injects XTest mouse events into the owned game window; it does not inject game state.
