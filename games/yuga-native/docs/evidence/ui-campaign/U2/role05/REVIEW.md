# U2-05 — Controls ownership, saved bindings and nested navigation

Product: native YUGA. Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. This distinct assignment followed completion of U2-04. It changed only `scripts/controls_overlay.gd`, added `tests/ui_controls_lifecycle_cases.gd`, and wrote this role's evidence. SCREEN_CAMPAIGN.json and both U1-04/U1-05 reviews informed the work.

Actually viewed historical `docs/evidence/traversal-armies-window-r2/03-controls.png`: the scrollable mapping list, fixed-control hint and footer establish the baseline interaction. Its older teal styling and labels are historical evidence, not a rendering of this source. Current controls use the shared semantic theme, primary Done action, utility Cancel action and 44px minimum targets.

The modal explicitly runs while paused. Godot allows that mode to bypass an explicitly disabled ancestor, which matters when the loader isolates its caller. The overlay now checks visibility through the entire hierarchy and explicit disabled ancestors before handling input or taking initial/capture focus. Hiding or disabling its owner cancels pending capture without restoring mapping focus. Normal paused input remains available; the caller continues to own pause and focus restoration through the existing `closed` signal. Coordinated this contract with the loading owner.

Closing no longer focuses a soon-hidden mapping and is idempotent. Reset defaults retains Reset's keyboard focus instead of jumping back to the captured mapping. The fixed-control hint now obtains key labels from InputBindings and includes the existing abilities action. Stable node names support independent interaction checks. No additional navigation or gameplay state is invented, and bindings still persist immediately through the existing settings implementation.

## Executed checks

Exact commands, exit statuses and result counts are in `execution.json`; the adjacent JSON reports and logs retain assertions and source pins. Godot 4.6.3 ran headless on CPU 0 with one worker thread. No import or renderer was run for this role.

| Suite | Passed | Evidence |
|---|---:|---|
| ui_controls_lifecycle_cases | 14 | Hidden/disabled-owner isolation, recovery focus, paused remapping and persistence, nested Escape, idempotent close, saved labels, Reset focus, 960×540/1280×720 focused-row containment and paused focus wrapping |
| ui_controls_state_cases | 19 | Complete modal focus loop, active capture navigation, conflicts, errors, Reset/Done, long labels and shared target sizes |
| input_binding_cases | 44 | Existing binding validation/persistence and actual courtyard settings/help/pause integration |

**77/77 checks pass**, all final processes exit 0, and final logs contain no engine errors or warnings. Inputs are native Godot key events dispatched through the headless viewport; this is not OS-level keyboard or pixel acceptance.

An initial lifecycle fixture read the default settings path instead of its isolated test path. The resulting missing section aborted the script, and its owned process was terminated. `controls-lifecycle-rejected-r1.log` and `execution-rejected-r1.json` preserve that test-authoring error. The fixture now reads its explicit path, and the affected suite passed on a fresh isolated data directory with a bounded process timeout. No product behavior or assertions were weakened to resolve it.

Final production source: `38f94e4d4c5cb2226b006c4d9db9b869da3ac98716c6adff96b33078ee593194`. New lifecycle fixture: `6a13b8530b2484c627acd07989668d33e4cd8e829e40c0683ab62b161b8c8caf`. Full source and historical image hashes are in `source-hashes.json`. Final reports used the root-owned bundled-font theme at `39e43f426e65475fd134fd9bd9515d1505edc90b6969394017995b641693abc4`; earlier U2-04 receipts retain their original theme identity.

Production sources were frozen and communicated to the loading/verification owner before integrated capture. Current-window appearance, 2× scale, OS input, loader pixels, physical GPU and Windows behavior remain outside this role's checks. Role06 owns the current integrated review. No courtyard, launch, loader, boot, world, shared theme or shared campaign ledger edits were made by this assignment.
