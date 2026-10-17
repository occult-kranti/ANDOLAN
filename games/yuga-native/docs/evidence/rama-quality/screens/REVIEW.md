# Native screens: Rama quality slice

Role 12, 17 October 2026. Source baseline: `1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`.

## Round 1: inspect the existing native experience

The actual accepted title image at
`../../rama-hero/window/960x600-r3/01-title-loaded.png` shows the real game
actor on the right, a readable gold **Explore Confluence** primary action and
all seven title actions on the left. The 1280 × 720 guide image at
`../../rama-hero/window/1280x720-r1/04-training-ability-guide.png` shows a clear
five-ability list, one detail pane and a visible Back action. These are earlier
build images used to identify the issue, not evidence of the current edits.

The title actor is visually underlit and the screen wash adds darkness across
the portrait. The look-development owner controls scene lighting; this packet
only narrows the title wash so it becomes transparent before the projected
face. It preserves the actual 3D camera, training/world/film entry methods and
all existing modal resource paths. No replacement website, model, scene or
alternate game was created.

The principal control defect is in the current source: Settings and Help return
to **Bow training** even when opened from another title action. Pause modals
similarly default to Resume, discarding the actual opener. The guide already
stores a weak previous control, but its caller also forces its own return
focus. A guide opened during live play can restore a HUD button after the
caller has released interface focus.

## Round 2: implement and check the counterexamples

`courtyard.gd` now stores a separate guarded weak reference for each Settings,
Help and guide opener. After the correct owner is visible again it restores
that exact control, provided it still exists, belongs to that screen, is
visible, supports focus and is enabled. A deleted or disabled title opener
falls back to Explore Confluence; a missing pause opener falls back to Resume.
Courtyard owns guide focus restoration and does not also ask the shared panel
to restore the same control afterward; this prevents a disabled or reparented
opener from overriding the validated fallback. Returning directly to live play
releases interface focus. Controls still
returns to its Settings action, while the outer Settings modal retains its
original title or pause opener.

The title's edge wash reaches zero opacity at 67% of viewport width. Camera,
portrait light, world lighting and character materials are unchanged by this
packet. Existing title actions and pause utilities receive stable node names
without changing their methods or signals. The existing two-frame Settings
entry scroll correction is retained.

All five Godot 4.6.3 headless suites below exited 0 with no engine errors or
warnings. Each used a new isolated `XDG_DATA_HOME`, `--max-threads 2`,
`--fixed-fps 60` and the actual native scene. Exact source hashes and individual
assertions are in the adjacent JSON files; `summary.json` groups their results.

| Suite | Result | Covered behavior |
| --- | --- | --- |
| `rama_screen_quality_cases.gd` | 49 / 49 | Every title action in forward/reverse Tab order; viewport fit and projected face/wash clearance at 960 × 600, 1280 × 720, 1920 × 1080 and 2560 × 1440; exact Settings/Help/shortcut-guide return; deleted/disabled opener fallback; nested controls and preference saves; matching guide/HUD remap labels; pause owner and live-play focus. |
| Existing `rama_screen_cases.gd` | 36 / 36 | Existing title/guide/Settings layout, first-entry/reopen scroll, modal transitions, camera and pause behavior. |
| Existing `input_binding_cases.gd` | 44 / 44 | Existing input capture, conflicts, migrations, safe settings persistence and cancellation. |
| Existing `rama_hud_layout_cases.gd` | 9 / 9 | Existing world HUD separation and gameplay-camera clearance. |
| Existing `rama_hud_expiry_cases.gd` | 9 / 9 | Existing ordinary-update Guardian expiry, shield, damage, defeat and reset display behavior. |

Example invocation from repository root:

```sh
XDG_DATA_HOME=/tmp/rama-screen-quality-r3/rama_screen_quality_cases-user \
  godot --headless --path games/yuga-native --max-threads 2 --fixed-fps 60 \
  --script res://tests/rama_screen_quality_cases.gd -- \
  --report=/tmp/rama-screen-quality-r3/rama_screen_quality_cases.json
```

The first new-fixture run passed 47 assertions but emitted an audio teardown
warning after many synthetic button activations queued menu cues faster than
real interaction. The fixture now clears its scene's menu-sound dictionary;
audio is outside this fixture's stated scope. The clean repeat does not claim
audio teardown or listening acceptance. Runtime audio behavior was not changed.

`before-courtyard.gd` preserves the exact baseline source. Running the same
49-case fixture with `--courtyard-script=res://docs/evidence/rama-quality/screens/before-courtyard.gd`
correctly fails 20 assertions (29 / 49 pass), exits 1 and has no engine
diagnostics. `before.json` identifies the old focus, invalid-opener and portrait
wash failures; the fixed source passes every same assertion. The baseline
snapshot is evidence, excluded from runtime exports.

## Round 3: independent actual-input review

**Pending final integration freeze and packaged build.** Headless focus and
projection checks do not establish the appearance of the final imported hero,
normal OS mouse/keyboard behavior, achieved GPU performance or human feel.

The independent reviewer must inspect the exact packaged source and PCK, then
record actual input and images for the following:

1. At 960 × 600 and 1280 × 720, load the title and verify the final imported
   actor's face is visible, primary action is readable, and all seven actions
   fit without scrolling. Include a 2560 × 1440 layout screenshot if the
   execution environment can render it within the agreed capture budget.
2. Click Settings, use Escape or Back, and verify the Settings utility regains
   focus. Repeat Help and the abilities button. Tab to the primary world
   action, open the guide with F3 and close it; focus must return to that action.
3. Enter Settings, remap one ability through keyboard capture, close Controls,
   change a slider and return to title. Focus must follow Controls → Settings
   opener. Reopen the guide and enter training; both labels must use the saved
   map. Reopening Settings must keep its complete heading visible and initial
   slider focus.
4. In training, pause and open each Settings, Help and guide action. On return,
   the initiating action must regain focus, gameplay must remain paused and
   the gameplay HUD must remain hidden. Opening Help or guide from live play
   must release gameplay input while open and resume without stranded GUI
   focus.
5. Return to title, traverse every action with Tab and Shift+Tab, activate the
   desired entry with Enter, and verify the real world/training entry works.

The release/quality owner attaches the source-bound input receipt and accepts
or rejects this packet. Broader native queue/draft/reconnect/results flows,
controller support, device-specific fonts and human usability remain open
production work; these local corrections do not close that entire gate.
