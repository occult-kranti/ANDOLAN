# Invocation practice selector

The native Confluence practice world offers fourteen named invocations through the current Rama avatar. Selecting an invocation changes its troop effect, not the player model. The panel says **“Channel a legend through Rama · offline troop practice”**. It does not advertise fourteen playable production characters or an online match.

## Design decisions

The first density review separated three decisions: which legend to channel, what the actual troop payload does, and how to avoid its footprint. A two-column roster exposes all fourteen names without a hidden paging step. The selected legend has an equipped marker; browsing shows a preview and does not alter the session. A large, static geometric sigil uses each codex accent without requiring fourteen missing portraits or animated background work.

The right column puts identity, invocation name, range and preparation above a scrollable reading area. **Troop effect** is generated from `native-ultimate-rules.json`; **Play around it** explains line of sight, boundaries, caps or expiry. **Art direction** is the codex's ornament brief, not additional damage or a claim that every storyboard detail has been rendered. Hanuman explicitly projects a landing effect without moving Rama. Healing and shielding refer to allied troops; there is no implied player-health system.

At a **logical viewport** of 960×600 the card is 928×568 with 16-pixel outer margins. At a logical 1280×720 it is 1040×620. Long detail scrolls while the roster, Back action, visual preferences, confirmation and status remain available. The nineteen focusable controls have at least a 36×36 **logical-pixel** hit area. Text and focus use cream/gold against a dark teal surface. The panel has no continuous ornamental animation.

The packaged project uses `canvas_items` stretching from its 1280×720 viewport. In the reviewed 960×600 operating-system window it letterboxes and scales the panel to about 780 physical pixels wide; logical hit-area sizes therefore do not establish the same physical-pixel size. Actual Rama and Ulupi preview screenshots retain all fourteen names, scope, payload, counterplay, options and actions without clipping. Text is compact at that scale; a user-adjustable text/UI scale remains future accessibility work. The logical layout suite and physical window review are distinct evidence.

## Integration contract

`scripts/invocation_panel.gd` extends `Control` and uses `PROCESS_MODE_ALWAYS`. Add it to the existing UI canvas before calling `configure()`.

| API | Responsibility |
| --- | --- |
| `configure(catalogue={}, rules={}, selection="rama") -> bool` | Empty dictionaries load the frozen codex and native rules. Validates the fields the UI uses and requires fourteen matching entries. Invalid input preserves a previously valid catalogue. |
| `update_session(report) -> bool` | Accepts authoritative `selected_hero`, finite `cooldown_remaining` in 0–12 seconds, recognized `active_phase`, and boolean `suspended`. Does not tick or reset cooldown. Preserves the current reading scroll. |
| `open(return_focus: Control = null)` | Neutralizes held gameplay inputs, reloads preferences, previews accepted selection and focuses that roster button. |
| `close()` | Neutralizes held gameplay inputs, hides once, returns focus to a still-live visible owner and emits `closed`. |
| `set_available(enabled, reason)` | Disables selection and shows why; Back and preferences remain accessible. |
| `set_notice(text, is_error=false)` | Shows a bounded rejection or save message. |
| `options() -> Dictionary` | Returns copied boolean effect preferences for the real effect owner. |
| `report() -> Dictionary` | Exposes preview/accepted selection, cooldown/phase, options, geometry/payload/counterplay text, card/control bounds, scope and status for verification. |

Signals are `invocation_selected(hero_id)`, `closed` and `effects_options_changed(options)`. Selection is a **request**: the world calls `UltimateSession.select_invocation()`, updates the panel with the accepted report, then closes it. Previewing or clicking Use never optimistically changes the accepted selection or cooldown. Selecting the already-equipped entry returns to practice. Shared recovery remains twelve seconds across hero switches.

The world owns modal/pause/overview/focus-loss behavior and must freeze the actual army/session while the selector is open. It also owns casting, cast rejection messages and the compact practice HUD. The panel never applies damage, spawns units, owns the simulation clock or pauses the tree itself.

## Input and visual preferences

Arrows browse the two-column roster; Enter requests the focused invocation. Tab/Shift+Tab cycle through the fourteen heroes, reading area, two preferences, confirmation and Back. Up/Down and Page Up/Page Down scroll when the reading area has focus. Escape and the shared `open_invocations` action close the modal and consume the event. The world opens only when hidden, avoiding a same-event close/reopen. Both selector and ultimate hints read `Bindings.label(...)`, so the cast hint follows remapping rather than hardcoding X.

Preferences use `Bindings.merge_settings()` in the **`invocations`** section:

```ini
[invocations]
reduced_effects=false
reduced_motion=false
```

Other sections are preserved. The world initially calls `ultimate_fx.set_options(panel.options())` after configuration and forwards `effects_options_changed`. A settings reload that changes the visible values also emits this signal, preventing the displayed toggles and live FX from diverging. Invalid configuration bytes are preserved; a failed save shows a reason and emits no successful-save event. Safe defaults loaded from an invalid file are also synchronized to the effect owner.

Reduced effects removes secondary ornament, and reduced motion freezes ornamental orbit/flutters. Exact threat boundaries, preparation, impact and actionable timing stay visible in both modes. These guarantees belong to `ultimate_effects.gd` and are verified separately from the panel.

## Verification

Run the actual Godot control suite from the repository root:

```sh
godot --headless --path games/yuga-native \
  --script res://tests/invocation_ui_cases.gd \
  -- --report=/absolute/output/invocation-ui.json
```

The suite checks all fourteen source-derived payload summaries, control rectangles at both viewport sizes, accepted versus preview selection, shared-cooldown preservation, keyboard focus cycling, real overflowing detail scrolling, remapped hints, neutralized held gameplay, weak return-focus disposal, invalid-state rejection, preference merge/reload synchronization and original invalid-file preservation. Reports include `passed`, individual `checks`, engine version, layouts, scope and hashes of the panel, bindings, catalogue, rules and suite.

The initial keyboard check caught a mismatch between preview and actual focus after programmatic previews. Navigation and Enter now use the actual focused roster button. The final scroll regression requires a positive scroll offset; equality at zero cannot pass as evidence of retaining a scrolled page.

Headless control geometry and method-injected input do not establish visual acceptance, operating-system input behavior, moving-effect readability or online readiness. Actual window screenshots/input and the world integration suite are separate release gates. Evidence paths and final runtime hashes belong in the batch archive after those gates complete.
