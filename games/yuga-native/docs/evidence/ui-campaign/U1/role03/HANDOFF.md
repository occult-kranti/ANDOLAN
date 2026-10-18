# U1-03 — loading and recovery

Implemented the reusable `scripts/scene_transition.gd` Control and real threaded-resource fixture suite. Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. This is the component contract and functional gate; courtyard/world integration belongs to U2-03, and actual rendered/input review belongs to the capture owner.

## Integration contract

Mount one instance outside the scene being replaced, preferably under a persistent root `CanvasLayer` above other UI. The module rejects being a child of its `caller`, and a root metadata lease rejects competing instances while a transition or recovery dialog owns navigation.

```gdscript
const SceneTransition = preload("res://scripts/scene_transition.gd")
var loader := SceneTransition.new()
# transition_layer is a persistent CanvasLayer under get_tree().root.
transition_layer.add_child(loader)
loader.begin(&"confluence", self, explore_button)
```

- `begin(id: StringName, caller: Node = null, return_focus: Control = null) -> bool` accepts only `courtyard`, `confluence`, and `combat_film`. IDs map to the existing three local `.tscn` paths. Unknown IDs, arbitrary paths, detached controls, duplicate begins and competing owners return false without changing the caller. An error dialog requires `retry()` or `cancel()` before another `begin()`.
- `is_busy() -> bool`, `retry() -> bool`, `cancel() -> bool`, and `snapshot() -> Dictionary` support host and test integration.
- `phase_changed(phase: StringName, message: String, resource_progress: float)` reports `queued`, `loading`, `constructing`, `error`, `done`, or `cancelled`. `resource_progress == -1.0` means no numeric resource progress is available. Only validated values returned by `ResourceLoader.load_threaded_get_status` appear on the resource progress bar.
- `completed(destination: StringName)` fires once per successful attempt, after `SceneTree.scene_changed` confirms the new scene. `failed(destination, message)` fires once per failed attempt. `cancelled(destination)` fires once per accepted Back/cancel action.

`begin()` immediately shows status, captures the caller's process mode, tree pause state, mouse mode and opener focus, then disables caller processing. Loading remains usable while the tree was paused. Hosts should release held gameplay actions as part of their navigation command. The overlay owns its Retry/Back keyboard cycle and Escape handling. Existing child nodes using their own explicit process mode should be reviewed during integration.

A failure keeps the recovery dialog active and the caller isolated. Retry starts a fresh attempt. Back/cancel hides the dialog and restores the caller's previous processing, pause, mouse and focus state. This avoids gameplay behind an interactive error dialog. A host wanting its own error surface can handle `failed` by calling `cancel()` and presenting its own error state. Success leaves input/focus to the new scene.

Cancellation cannot stop Godot's background resource worker. It invalidates navigation, consumes late resource results without changing scenes, and permits safe reuse. Disposal transfers pending loads to a root-owned result janitor, which has no scene-navigation callbacks. Once synchronous scene replacement begins, Back is disabled and cancellation is rejected until the atomic replacement completes.

Resource loading and scene construction are distinct. The overlay gives each message time to paint before starting its work. Instantiation and scene `_ready()` still run synchronously on the main thread. In this product, procedural world construction may dominate startup after resource loading completes. No total-load percentage, fully asynchronous world creation, or hardware frame-rate claim is made. Existing courtyard startup before the launch screen is not changed by this standalone component.

## Verification

Executed with official Godot `4.6.3.stable.official.7d41c59c4`:

```sh
python3 games/yuga-native/docs/evidence/ui-campaign/U1/role03/run-fixture.py --output /tmp/yuga-u1-transition-r8
```

Result: **33 passed, 0 failed**, exit 0. The runner stages only the loader, shared theme, test script and small real PackedScene fixtures in a fresh directory outside the product. It refuses a product-directory output, checks the runner's exit status, checks that all expected assertions ran, and rejects unexpected engine errors or ObjectDB leaks. The suite also refuses to modify scenes without its dedicated fixture-project setting.

Coverage includes unknown/arbitrary paths, caller ownership, immediate queued status, duplicate and competing loaders, pause/mouse/focus restoration, missing-file failure and repaired retry, actual scene replacement, exactly-once completion, cancellation after a real threaded request and before construction, safe reuse, malformed scene resources, recovery focus/Tab cycle, viewport containment, active loader disposal, late-result cleanup, and distinct construction status without a percentage.

The intentionally malformed `combat_film.tscn` fixture produces exactly two expected Godot errors: its parse error and its resource-load failure. The final log has no script error or ObjectDB leak warning. Early retained scratch runs exposed missing-metadata diagnostics, a failed-resource request token leak and a too-early layout assertion; these were corrected before this receipt. No heavy asset import or renderer was run by this role, and no screenshot was reviewed. Real display/input, resize variety and full-world timing remain U2/later capture gates.

Exact accepted bytes are pinned in `receipt.json`:

- Loader SHA-256: `d3a3442dbe5f9fa71e640082def023e171c96b362b1a60a62a458018142083fd`
- Tests SHA-256: `e95d14f118b8026d4317a99b8f44322cb3f3014cccd4e7db89c17ea8250a3fd9`
- Shared-theme dependency SHA-256 is also recorded there.

Changed files are only `scripts/scene_transition.gd`, `tests/scene_transition_cases.gd`, and this role's evidence directory. Next owner: root/U2-03 for courtyard/world wiring, coordinated with launch-shell ownership; capture owner for actual loading/error/recovery frames.
