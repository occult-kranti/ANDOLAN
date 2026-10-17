# Rama UI — final R7 headless review

17 October 2026. Native YUGA working tree based on `e765a23264cf3c3c38fab1ded677832a24fdd64e`. The frozen R7 hero is `assets/heroes/rama-hero.glb`, SHA-256 `667f3a215a7b868e3bdbcde880a73d42b68b29af1303db4e1d99b93f73cf2b50`.

All **135 assertions passed**, with five exit codes of 0 and no engine errors or warnings. The suites ran sequentially using Godot 4.6.3, `--headless --fixed-fps 60`, and separate user-data directories. [summary.json](summary.json) records the exact executed commands, engine hash, report/log hashes and forty tested source hashes; every reported source hash was checked against the working tree after the runs. The source commit alone does not identify these uncommitted milestone changes.

| Suite | Passed | Evidence |
| --- | ---: | --- |
| Title, abilities, Help, settings and training transitions | 30/30 | [screens.json](screens.json), [log](screens.log) |
| Bindings, migration and settings persistence | 44/44 | [input.json](input.json), [log](input.log) |
| HUD bounds, peer separation and projected actor clearance | 9/9 | [hud-layout.json](hud-layout.json), [log](hud-layout.log) |
| World geometry, focus, real kit releases and traversal resets | 27/27 | [world-scene.json](world-scene.json), [log](world-scene.log) |
| Siege UI, pause, focus, reset and real vitals guidance | 25/25 | [siege-ui.json](siege-ui.json), [log](siege-ui.log) |

Screen checks cover 960 × 600, 1280 × 720 and 1920 × 1080. HUD checks start at the default 1280 × 720 to exercise initial layout, then check 960 × 600 and 1920 × 1080. Historical missing-model and initial-layout failures remain described in [RAMA_SCREEN_DESIGN.md](../../../RAMA_SCREEN_DESIGN.md); this clean repeat supersedes them for these bounded assertions.

The native-window helper also passes [eight CLI/input-bound tests](native-window-review.log), including default and explicit dimensions, rejection outside 960–1920 × 600–1080, click-edge bounds at all three sizes, and Guardian/Help keys. These tests do not launch X11 or a renderer.

## Native-window handoff

Run `tools/native-window-review.py` with an engine, pack and fresh output directory, then send newline-delimited JSON on its open stdin. `--width 960 --height 600` is the default; use a separate run/output/display for `--width 1280 --height 720`. The dimensions apply to Xvfb, the game and click bounds. `input-review.json` records `resolutionRequested`; capture events record the actual PNG dimensions.

```json
{"action":"capture","name":"01-title"}
{"action":"key","key":"Return","seconds":0.15}
{"action":"key","key":"c","seconds":0.15}
{"action":"key","key":"Page_Down","seconds":0.15}
{"action":"motion","dx":120,"dy":0}
{"action":"click","x":400,"y":300,"seconds":0.15}
{"action":"click","move":false,"seconds":0.15}
{"action":"quit"}
```

The startup message means the game process was launched; wait for its actual window and first frame before sending commands. Capture names must be unique. Mouse motion is bounded to ±720/±480 pixels; key/click holds are clamped to 0.05–5 seconds. `move:false` fires at captured aim without relocating the pointer. Help supports `Page_Up`, `Page_Down`, `Home` and `End`. There is no wait, resize or simultaneous-key chord command.

Actual native-window input and rendered review remain pending with the root reviewer. These headless checks do not establish rendered art quality, animation contact, listening quality, physical-GPU performance or Windows behavior.
