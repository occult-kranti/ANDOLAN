# U3-01 coherent title and pause navigation

**17 focused checks and25 existing end-to-end checks pass.** Baseline had four
independent navigation failures (8/12); initial corrected12/12 was extended with
focus-loss, invalid-opener, slider-opener and visible-header cases. Final reports
are `final.json` and `end-to-end-final.json`.

Courtyard Tab navigation now skips disabled buttons and read-only sliders.
Returning to a modal validates both the remembered opener and fallback. Losing
window focus during a training-origin help/hero dialog keeps that dialog open
and changes its eventual return to pause. Actual tree pause and runtime
suspension remain the authority; no action/rules/timing/reset route changed.

World child dialogs restore the actual pause opener, including F3 from the
volume slider, with one caller responsible for focus. Invalid, hidden, replaced
or read-only targets fall back to the active primary action. The existing
Restart lane practice action is beside Continue. A real completed army round
makes Restart primary/default and labels the other action Return to world.
Restart uses the existing reset route, and ordinary Continue presentation
returns after it clears the terminal authority. The read-only RoundOutcome
component is preserved.

Independent inspection of U2 original03-world-pause.png confirmed that automatic
focus scrolling clipped the title/eyebrow above Continue. The deferred reveal
now keeps scroll0 for default Continue/Restart when the primary fits below its
heading; returned lower controls still scroll into view. Tests explicitly
require ordinary and terminal headers to remain at scroll0. This fixes the
source behavior; U3 rasterized visual acceptance belongs to the capture lane.

A failed extended probe overrequired `courtyard.player.active == false` while
paused. The actual courtyard contract uses tree pause plus runtime suspension;
the corrected test verifies those actual authorities. The failed report is
retained. Separately, real courtyard teardown exposed HUD get_tree access after
detachment; UI02 fixed that owned HUD path. Final focused runs have no script
errors. End-to-end intentional missing-scene errors exercise the loader's
recoverable failure path, and all25 checks pass.

Changed scope: pause/focus/menu portions of `scripts/courtyard.gd` and
`scripts/confluence_world.gd`; added `tests/ui_pause_navigation_cases.gd`.
No reset_training, title-return, world-return, loader, gameplay authority,
font or HUD layout edit by this worker. Shared U3 edits by other owners are
pinned as observed in reports, not attributed here.

Executed with Godot4.6.3 headless on CPUs0,1:

```sh
taskset -c 0,1 timeout 90s godot --headless --path games/yuga-native \
  --script res://tests/ui_pause_navigation_cases.gd -- --report=/tmp/ui-pause-navigation.json
taskset -c 0,1 timeout 100s godot --headless --path games/yuga-native \
  --script res://tests/ui_end_to_end_cases.gd -- --report=/tmp/ui-end-to-end.json
```

Final tests load approved R2 canonical imports after root's explicit cache-sync
receipt. The first baseline predates that sync; it establishes UI behavior only.
Keyboard dispatch is real engine input, not OS/XTest. No import or render ran
in this worker. Source commit0437ea91… with authorized shared edits. Next owner:
independent UI06 acceptance and root/capture. U2 frozen evidence is untouched.
