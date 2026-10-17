# MYTH10 UI control evidence

The final headless invocation panel suite passed **62/62 checks** on Godot 4.6.3. `invocation-ui.json` contains every assertion, actual control rectangles, the source hashes sampled before execution and an unchanged-source gate. `invocation-ui.log.txt` records the engine result. This evidence accepts the bounded control/layout/settings contract, not visual art or operating-system input.

Exact command, run from `/workspace/ANDOLAN`:

```sh
godot --headless --path games/yuga-native \
  --script res://tests/invocation_ui_cases.gd \
  -- --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/mythic-batch2/ui/invocation-ui.json \
  > /workspace/ANDOLAN/games/yuga-native/docs/evidence/mythic-batch2/ui/invocation-ui.log.txt 2>&1
```

All fourteen detail selections were laid out at both 960×600 and 1280×720. The test checks actual card/control bounds and minimum hit areas. Page Down advances a genuinely overflowing detail at 960×600 before a session refresh; the positive offset is retained. Preview and confirmation request never mutate accepted selection or the 12-second shared cooldown. All nineteen controls are visited exactly once in a Tab cycle. Settings tests use an isolated user config and preserve unrelated sections and malformed original bytes.

The rejected second run is retained under `rejected-r2/`: seven of sixty checks failed after a programmatic preview diverged from keyboard focus. Navigation and Enter were using the preview ID instead of the real focused button, producing the wrong request and subsequent close/focus failures. The fix uses the actual focused roster button. The final test also adds real-overflow scrolling and external-settings reload synchronization, giving sixty-two checks. These failed results are not acceptance evidence.

Root owns the shared packaged native-window screenshots and XTest input review after all runtime owners freeze. Those artifacts must be reviewed separately before claiming readable screens or OS interaction. The panel's long “Art direction” paragraph is a creative brief; native troop payload and counterplay are the rules-backed sections. This packet does not accept fourteen production avatars, online play or commercial visual parity.
