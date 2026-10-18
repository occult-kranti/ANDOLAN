# U3-03 — restart, defeat and transition disposal

Implemented and verified two lifecycle repairs against actual native training/world scenes. Source base remains `0437ea91edf6989ff78c1eeadb3661f4825b60f2`; `final-cpu-receipt.json` pins the tested working files and confirms they did not change during the final run.

1. Disposing an active loader restored its direct caller but previously skipped the host's cancellation handler. Confluence's explicitly processing world/UI children could therefore stay disabled. Loader disposal now emits the cancellation notification after invalidating the attempt, releasing ownership and restoring the caller. The host restores its recorded explicit child modes, and a subsequent return recreates one loader under the existing persistent layer.
2. Training F5 after defeat reset vitals to alive while leaving `player.active` false. The independent lifecycle test found this actual defect in `lifecycle-r1.json` (16 passed, 1 failed). With root's localized ownership authorization, `courtyard.reset_training()` now recomputes activity from `started`, actual tree pause, and valid alive runtime state after the army reset. Paused resets retain inactive input and suspended clocks; title resets stay inactive. Normal resume remains responsible for reactivation after a paused reset.

The related U2 return routing preserves caller pause state, film playback and recoverable world state. Cancellation also forwards a still-applicable observed window focus loss after restoration, so a cancelled return does not resume film playback while the window is unfocused. No renderer, authority, damage rules, respawn delay or ability clock was changed.

Executed final command, CPU 0,1 and Godot 4.6.3:

```sh
taskset -c 0,1 godot --headless --path games/yuga-native \
  --script res://tests/ui_transition_lifecycle_cases.gd -- \
  --report=/tmp/yuga-ui-final-cpu-r1/ui_transition_lifecycle_cases.json
```

**20 passed, 0 failed**, exit 0, no engine errors or warnings. The final report covers actual training defeat and F5; paused reset, suspended clocks and resume; inactive title reset; three repeated launch/cancel attempts; world defeat; cancelled return preserving paused defeat and army time; respawn through the normal three-second simulation timer; world F5; active-loader disposal; restored explicit process modes; singleton recreation; and a completed return to a usable title. Damage is applied through the configured offline receiver as an explicit test fixture; navigation and reset/pause also use real engine keyboard dispatch. No new overlay is created by defeat, reset or respawn.

The final independent U2 flow suite also passes 25/25 on the same unchanged source set. This role does not claim rendered acceptance. These CPU runs used the existing imported assets; the three raw hero GLBs require refreshed imports in the separate U2 visual snapshot before visual qualification. The failure and intermediate corrected report are retained, along with the final source-pinned report and raw output.

Changed implementation: `scripts/scene_transition.gd` disposal/focus cancellation behavior and the authorized `courtyard.reset_training()` activation line. New focused test: `tests/ui_transition_lifecycle_cases.gd`. Other Confluence/film return changes and observer tooling are documented by U2-06. No commit or shared campaign ledger was changed.

A later U2 font-only correction and isolated fresh import were also checked: `refreshed-receipt.json` records 175 matching raw/import MD5s, no authored-source changes during import, and 87 passed assertions across font (7), launch geometry (35), independent flow (25) and lifecycle (20). The refreshed lifecycle report and output are retained here. Actual 3D acceptance remains the U2-06 capture responsibility.
