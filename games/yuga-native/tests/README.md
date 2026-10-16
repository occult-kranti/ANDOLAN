# Native acceptance scenarios

Run with Godot 4.6.3 after a project import. The headless renderer checks simulation and imported animation transforms; it does not assess graphics quality or frame rate.

```sh
godot --headless --path games/yuga-native --editor --import
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/native_acceptance.gd
```

In the managed cloud environment, use the writable XDG directories documented in the native setup instructions. An alternative report location can be supplied after `--`, for example `-- --report=/tmp/yuga-native-acceptance.json`.

The runner uses real Godot character collision, physics ray casts, timers and imported Skeleton3D animation evaluation. It deliberately injects Godot action state and builds labelled isolated collision fixtures. This is reproducible scripted QA, **not evidence of physical keyboard/mouse input**, a full match, commercial-game parity, visual polish, or multiplayer synchronization.

The scenarios cover input registration; entering training; pause and held-input neutrality; restart and menu safety; all nine Rama animation clips at five sample times; forward/diagonal movement; wall collision and dash; jumping and landing; fire cooldown, magazine and reload; high-speed projectile damage, defeat and timed target restoration; and world occlusion.

A nonzero exit code or a report containing `passed: false` fails acceptance. Preserve failed reports when fixing a defect. A separate rendered-window check is required to judge art, readability, animation appearance and actual OS input.

The recorded final-art run passed 16 checks, including unchanged source hashes across the scenarios. The collision check also verifies that a living target blocks character movement and a defeated target allows passage. The first run is preserved in `evidence/native-acceptance-before-pause-fix.json`: 14 of the original 15 checks passed, but resuming after held movement caused 0.425 m of unintended coasting. The runtime now clears horizontal velocity and active dash on pause; the final run records 0 m of post-resume drift with the original assertion intact. One additional evidence-integrity check was added afterward. The earlier passing run before the final courtyard art import is retained as `evidence/native-acceptance-before-final-art.json`. No renderer or performance conclusion follows from the short fixed-step headless execution time.
