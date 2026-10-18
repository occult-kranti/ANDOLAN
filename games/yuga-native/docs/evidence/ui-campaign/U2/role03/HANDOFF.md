# U2-03 — lightweight initial boot

The configured main scene is now `res://scenes/boot.tscn`. It mounts native controls, a YUGA wordmark, the shared theme and the existing transition component before requesting courtyard resources. It has no world/hero preload or 3D child. The main-scene setting was changed only after the small fixture gate passed; real existing-import startup then passed as well.

Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Exact accepted source hashes are in `native/receipt.json`, and were compared against the final files after all runs. No courtyard, Confluence, combat-film, shared-theme or roadmap file was edited by this role.

## Behavior and contracts

Boot calls the new `SceneTransition.ensure_for_tree(tree)` helper. It finds or creates exactly `/root/YugaSceneTransitionLayer/SceneTransition`, with CanvasLayer 100 and always-processing mode, matching U2-01's courtyard integration. The layer and loader survive scene replacement and are reused. Hosts may adopt this helper in place of their equivalent existing singleton lookup.

Initial loading uses `begin(&"courtyard", boot, boot.open_button)`. A failure keeps Retry and Back in the loader. Back or cancellation returns to the boot screen with Open YUGA/Retry and Quit controls and keyboard focus; it cannot leave a blank viewport without an action. A failed boot can retry after its scene becomes available. The boot's automatic start, retries, reentry and source disposal obey the same duplicate and cancellation guards as other transitions.

The loader now contains the shared wordmark. It retains genuine ResourceLoader progress only for the resource phase, followed by an unnumbered “Preparing the scene” phase. Courtyard instantiation and its procedural `_ready()` world construction remain synchronous. There is no total-game percentage or claim that this removes that main-thread work. The initial source screen is lightweight; actual initial pixels and perceived startup responsiveness still need the capture owner's review.

OS user arguments are untouched. Native courtyard `--autostart` and `--smoke` handling runs in its original `_ready()`. The loader remembers a focus-loss event while it owns a transition and clears that memory on focus gain. After the replacement mounts, it forwards a still-applicable focus-loss event to the new scene's existing window handler. Scene-specific pause policy, including the smoke exception, stays in the scene. No scene is automatically resumed on focus gain.

## Executed verification

All runs used official Godot 4.6.3 and CPU affinity 0,1. No heavy import, editor startup or rendered capture was run.

```sh
taskset -c 0,1 python3 games/yuga-native/docs/evidence/ui-campaign/U2/role03/run-fixture.py --output /tmp/yuga-u2-boot-r2
taskset -c 0,1 python3 games/yuga-native/docs/evidence/ui-campaign/U1/role03/run-fixture.py --output /tmp/yuga-u2-loader-regression-r1
```

- Boot fixtures: **29 passed, 0 failed**. Real threaded small PackedScenes cover absent scene, repaired retry, Back, queued cancellation, reentry, caller disposal, singleton boot/title/world/title reuse, exactly-once completion, unchanged arguments and observed focus-loss/gain delivery.
- Separate actual Quit action: executed from the missing-scene recovery screen; process exited 0, marker retained in `fixtures/quit-run.log`.
- Existing loader regression: **33 passed, 0 failed**. Its deliberately malformed resource still produces only the two expected parse/load errors; no ObjectDB leak warning. See `loader-regression/`.

Real imported native startup ran with each of the following argument sets, using `--script res://tests/ui_boot_cases.gd -- --native`: normal title, `--autostart`, and `--autostart --smoke`. Each passed **13 checks**, exit 0, with no engine error or warning. These confirm the real courtyard reaches ready with imported hero/environment, its title/training state matches the arguments, it adopts the persistent boot loader, and its focus-pause policy remains correct. Exact commands and per-run reports are in `native/`.

The actual configured-main-scene path was also executed without a test script:

```sh
taskset -c 0,1 godot --headless --path games/yuga-native --quit-after 360 -- --smoke
```

It logged `YUGA_NATIVE_BOOT_READY` → `YUGA_NATIVE_READY` → `YUGA_NATIVE_TRAINING_STARTED` in order, then exited 0 without errors or warnings. This uses the existing `.godot` imports and does not qualify fresh package imports, screenshots, physical GPU performance or Windows execution.

## Return-routing work for the root owner

Confluence and combat film still call synchronous `change_scene_to_file("res://scenes/courtyard.tscn")` in their existing `return_to_courtyard()` methods. This role did not edit those files. Route both through `SceneTransition.ensure_for_tree(get_tree()).begin(&"courtyard", self, return_opener)` to use the persistent loader in both directions. The existing courtyard implementation is the reference for isolation and recovery.

For Confluence, snapshot and disable its explicit `world` and `ui` process modes after `begin()` accepts; the caller's disabled mode alone does not disable these explicitly configured children. Keep the pre-navigation pause/overview/player state available. Release held gameplay actions, and restore those explicit modes and opener focus in a scene-bound `cancelled` handler. Do not clear the tree's pause state before `begin()`, because the loader snapshots it for Back. Defer destructive presentation clearing until success, so a cancelled return remains playable.

For the film, save its existing `playing` state before pausing playback, and restore that state in its scene-bound cancellation handler. Guard duplicate return actions before altering playback. Avoid lambda callbacks retaining a disposed scene; connect bound scene methods, which Godot disconnects when that scene is freed. The new helper retains the same singleton names and does not require changing the boot scene on ordinary title returns.

Next owner: root for world/film return routing; capture owner for boot, loading, failure/Back, and final title input/pixel review. No shared campaign status or commit was changed by this role.
