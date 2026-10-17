# Integrated player/runtime hooks

The module is a deliberately small adapter around the unchanged immediate combat API. Root authorized this role to implement the buffer-only hooks in `player.gd` and `rama_hero_runtime.gd`. Their accepted buffer source snapshot and real-world polling tests are in [integration/](integration/). Root owns subsequent quality-component changes to those shared files; revalidate against the resulting source.

## Runtime

1. Add `const ActionBuffer = preload("res://scripts/rama_action_buffer.gd")` and an `action_buffer: Node` property. Create/add it after the kit is configured. Connect the runtime's existing `_event` before configuring the buffer so the runtime unlocks player movement before a legitimate recovery dispatch.
2. Configure it with `action_buffer.configure(kit, cast_ability, _input_eligibility)`. Keep `cast_ability(id)` and `kit.request_ability(...)` immediate. Existing tests and other callers must still receive an ordinary busy rejection from those APIs.
3. Expose a separate `request_input_ability(id, edge_token, echoed=false)` that calls `action_buffer.push_input(...)`. A queued response is `{accepted:false, queued:true, reason:...}`. A queue is feedback, never a begin, ammunition reservation or cooldown. The real request runs only through `cast_ability` after actual recovery.
4. `_input_eligibility()` returns `{eligible:bool, reason:String}` using current values: configured, not suspended, gameplay active, Rama alive, tree unpaused, no reload, no legacy invocation, traversal ground, actual floor contact, finite player position, finite camera/pivot and finite nonzero horizontal aim. Recheck at dispatch. Q/X do not consume or require primary ammunition in the present rules; do not invent an ammo requirement here.
5. `cast_ability` samples the camera, current position, direction and target when it is actually invoked. Do not capture those in the pending intent. If real geometry fails, that single real attempt rejects and is consumed; it must not retry.
6. Clear pending input explicitly at suspension/pause, gameplay modal open, window focus loss, hit reaction, defeat, player reset, teleport, scene change, round outcome and any new actor generation. Tree pause also clears automatically through a node notification, while real kit reset/cancel events clear through the subscription. The explicit root hooks remain required for modal/focus lifetimes where the clock may stop without an event.
7. Integrate truthful status with the shared HUD: pending status can say `… queued after recovery`; a genuine begin/release uses the existing status. Do not play a windup sound, animation, reticle burst or decrement any resource from `queued:true`. Runtime's normal `changed`/`combat_event` paths own those effects.

## Player

The separate callback for discrete buffered input and monotonically increasing edge counter persist across the existing player's resets. Only fresh `is_action_just_pressed` Q/X edges enter it; never held `is_action_pressed`, keyboard echo or held primary fire. A down-state and engine-physics-tick guard prevent repeated manual polls or a released just-pressed phase from creating another edge. If native input events rather than polling are used later, pass their echo state and reject it. Increment the token once per deliberate edge, not once per retry or frame.

The current `not invocation_locked` guard drops Q/X before the runtime sees them. When the new callback is present, allow Q/X to reach it during the committed action so it can distinguish the final recovery window from windup/early recovery. The eligibility callback still rejects reload/legacy invocation/airborne/modal/dead inputs. Do not enable jumping, movement, flight, grapple, LMB, E or C during commitment as a side effect.

E and C remain on the immediate path until a shared nonmutating geometry preflight exists. Their wall/cover checks currently occur after the kit's busy check. Held LMB keeps its existing rate, ammunition and reload path. The legacy path remains available when no Rama-specific callback is configured.

## Executed acceptance and remaining review

The isolated fixture tests genuine 20 Hz army/kit events and all narrow buffer counterexamples: 57/57 passed. The new actual-world fixture passes 31/31 checks using real CharacterBody grounding, `Input.action_press/release`, actual engine physics boundaries and existing player polling. Unchanged combat 85/85, hero integration 138/138 and binding 44/44 suites also passed, with clean Godot exits. Source/content-manifest review remains root-owned.

The actual-world fixture covers windup/early/final recovery, no fake animation/cue/begin, changed current camera aim, ordinary commit locks and pause/controls/guide/overview/focus/teleport/hit/defeat/actor-generation/army-reset/outcome cancellation. Focus is an explicitly emitted window signal. It does not replace OS input or a source-matched continuous rendered transition. The cue count currently reads the existing legacy voice index; when root integrates the separate action-audio owner, update that specific observation to the adopted owner's public event/voice report while preserving the no-queue-cue assertion. Unit checks cannot certify smooth human feel or finished animation quality.
