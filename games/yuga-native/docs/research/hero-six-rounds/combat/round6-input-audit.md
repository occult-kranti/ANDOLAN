# Round 6 ordinary-input correction

Task **YUGA-HERO-6R**, native offline Rama. Source base
`7162b5d0b666e4422b0bc73100e1fba947d3323f` with frozen runtime digest
`b4a253fea063f4fdcb013b56bb83d95fb44fff9d9b8b1080f6084d99d8ada6b9`.
No gameplay, runtime, snapshot or packaged asset was changed by this audit.

**RMB is not an aim feature.** The previous panel suggestion to warm the bow
with RMB was incorrect. `input_bindings.gd::_apply` erases fire's mappings and
adds only `MOUSE_BUTTON_LEFT`. `player.gd::_unhandled_input` handles relative
mouse motion, while `_physics_process` polls the fire action. Motion's aiming
flag comes from held fire while active, or the existing action timer. The
earlier retained [pixel review](round5/hero-pixel-review-r1.json) says ordinary
RMB input was pending; that planned route is superseded here without changing
the original hashed receipt.

Upstream Godot maps X11 raw button 3 to its right-button index 2; action
matching compares the actual button index. This agrees with the executed
probe below. Sources: [Godot X11 input conversion](https://github.com/godotengine/godot/blob/4.6.3-stable/platform/linuxbsd/x11/display_server_x11.cpp#L4838)
and [mouse-button action matching](https://github.com/godotengine/godot/blob/4.6.3-stable/core/input/input_event.cpp#L711).

## Executed evidence

1. Exact packaged Linux engine, SHA-256
   `e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e`,
   ran actual `Bindings.install/release_gameplay` and synthetic Godot input
   events headlessly: **10/10**. RIGHT never activates fire; LEFT does until
   release. Releasing gameplay while left is held does not let a subsequent
   right event revive fire. This is an engine/InputMap check, not OS input.
   [Probe](round6/input_binding_probe.gd),
   [result](round6/input-binding-probe-r2.json); the r1 typed-local parse error
   remains in its original log.
2. The same binary ran a tiny standalone 400×300 compatibility window on
   isolated Xvfb `:138`. Six real XTest transitions were delivered: right
   down/up, left down/up, right down/up. Godot logged right as index 2 with
   `event_fire=false` and `fire=false`; left as index 1 with fire true until
   release. The window was then closed. No gameplay assets, shared imports,
   full render or mutations of root's live package window occurred.
   [Exact command/events](round6/x11-input-probe-r1/result.json),
   [driver](round6/x11-input-probe-r1/run.py),
   [listener](round6/x11-input-probe-r1/probe.gd).
3. Read-only `XGetPointerMapping` on root's `:137` returned identity buttons
   `[1,2,3,4,5,6,7,8,9,10]`. The review tool forwards the requested button
   directly to `XTestFakeButtonEvent`; its button branch has no shadowing
   defect. Its click branch explicitly sends left down and left up.
4. The claimed ammo drain was a **visual reading error**, not a reproduced
   application defect. Original screenshots `04-forward-route`, `05-warm-aim`,
   `06-warm-pierce-result`, `07-warm-volley-result`, `09-reset` and
   `10-right-button-probe` have exactly identical RGB pixels in the entire
   ammo-text rectangle `(235,644)–(385,671)`: **0 of 4,050 pixels differ**.
   All display the same `12 / 12`. The primary meter in 09/10 is also identical
   (0 of 1,050 pixels differ). [Pixel counterexample](round6/ammo-pixel-counterexample.json)
   binds all six original hashes. This is numerical comparison of original
   pixels, not edited evidence or a claim about unsampled internal states.

## Correct ordinary-input route

Use LMB to fire an actual primary shot. Release LMB, then press Q or X near
the end of its recovery while the bow is still raised; repeat separately for
each power. The player polls primary before Q/X. Pressing Q/X during primary
draw is rejected, and holding the key does not continuously retry. A fresh
Q/X edge in the final 0.12 seconds of recovery can queue once. Use the recorded
HUD/cast sequence to identify the phase, since software-rendered wall time
does not equal simulation time. A pause/reset makes a separate cold-start
case; it is not a shortcut to a warm pose.

The initial `package-input-r1` right-button holds do not establish warm casts.
They can support cold Q/X and unmapped-right-button observations after actual
continuous frames are reviewed. Root owns the subsequent explicit LMB take.
This audit does not establish motion quality or physical-GPU performance.

The subsequent successful LMB take is now independently reviewed in
[ordinary-primary-power-review.json](round6/ordinary-primary-power-review.json).
It establishes a raised-arm primary-to-Volley transition and a post-primary
Piercing transition from partly lowered arms, with the stated visual limits.
The tool logs key/click timestamps after release; those values must not be
presented as exact key-down times.
