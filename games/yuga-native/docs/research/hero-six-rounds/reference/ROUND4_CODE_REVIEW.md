# Round 4 · independent source review

Task YUGA-HERO-6R; native offline Rama; reviewer `reference_panel`. Source base
`7162b5d0b666e4422b0bc73100e1fba947d3323f` plus the current owned working changes.
Review is read-only outside this reference evidence folder. No new engine import,
render or test run was performed by this reviewer in this round.

## Required correction

**Guardian Circle guide wording was misleading.** `rama_hero_panel.gd` originally
said moving out means protection no longer follows. In `rama_ability_kit.gd`,
`_hero_ward_payload` checks radius/line of sight for new healing/shield grants,
but a granted shield remains until its stored expiry or damage consumes it.
`_attachments` explicitly follows shielded recipient positions, including outside
the fixed circle. The guide must distinguish the stationary healing area from
retained shield. Root and UI owner were notified. Suitable correction: “Healing
requires staying inside the fixed circle; solid cover blocks placement.” No
simulation change is requested. Final corrected wording/source hash belongs to
the UI owner's successor receipt.

## Reviewed source contracts

| Component | Code finding | Decision and limits |
|---|---|---|
| `rama_training_journey.gd` | Requires Rama ID, integer generation/sequence; rejects old epochs/duplicate sequence. Progress observes impact/tick receipts, accepted meaningful movement and actual hero shield/healing. It neither casts nor edits kit state. | Accepted at source level. Completing a hint reflects a successful event, not human mastery. Out-of-order ability success is intentionally permitted. |
| `courtyard.gd` integration | Initializes journey to mounted kit generation; connects runtime events; refreshes hint/card on progress/reset; report reads live bindings. | Source connection is correct. Ordinary all-five completion and real layout remain capture/input gates. |
| `rama_training_journey_cases.gd` | Drives actual kit/receivers through miss, hit, remap, stale receipt, step, ward, volley, pause, reset, cover and cancel. Movement receiver remains a fixture. | Scope is truthfully declared; a source read is not a rerun, and this test alone cannot accept real collision/traversal. |
| `rama_hero_hud.gd` | Replaces/disconnects combat event receiver on configure; bounded cast cache cleared on reset/cancel/end. Meter reads actual kit age/cooldown, current magazine and authoritative release receipt. | Source-level agreement with simulation; meter derives elapsed values and cannot advance combat. UI's current-guide copy correction required above. |
| `rama_ability_meter.gd` | Draw-only child, ignores mouse, no focus. Outline/solid marks distinguish pending/launched lanes; no mark claims a hit or stock of charges. | Sound semantics; 3 px strokes need native image/readability review at supported scales. |
| `rama_ability_effects.gd` | Rebuilds pending warning lanes only when authoritative eligibility count changes. First projectile leaves two lanes; second leaves one; third clears them. Existing generation/geometry guards remain. | Accept the lifetime fix at source level. Event/input tests and actual bright/dark-ground viewing are separate gates. |
| `rama_projectile_warning.gdshader` | Uses actual readiness uniform, no TIME driver; dark edge and warm core remain within owned mesh; no collision/damage output. | Appropriate essential warning design. The shader comment's readability intention is not a measured visual result. |
| `rama_volley_warning_cases.gd` | Tests authority-only transitions, stalled interpolation, pause, reduced options, stale event, cancellation, reset, sweep extent and primary no-clutter behavior. | Meaningful adverse coverage on actual events. No claim of ordinary input or finished VFX. |
| `rama_hero_feedback_cases.gd` | Mounted kit exercises three delay marks, presentation-only time, pause/resume, cancellation, reset, empty magazine, defeat, guide read-only behavior and containment. | Good separation of state/geometry evidence from actual visuals. Current source should remain frozen during final capture. |

The reviewer also inspected the existing kit's ward payload/cleanup and projectile
release code, plus runtime binding/eligibility. Existing ground-only casting,
offline authority, fixed values and remappable actions remain explicit. No new
online, economy, damage or physical-GPU capability is inferred.

## Round 5 capture requirements

1. Normal gameplay camera with hero, target, ground lanes and bottom HUD in one
   view. Include windup, first/second/third Volley releases and return to cooldown.
2. Actual input for primary/Pierce/Step/Guardian/Volley and training progress; one
   miss or cover stop must not grant learning completion.
3. Guardian placed on legal ground: stay inside, then leave. Guide wording must
   match observed healing versus remaining shield.
4. Open/read/close tactical guide, keyboard focus return, pause/resume and reset;
   enlarged UI and current remapping must remain usable.
5. Front/rear/gameplay hero views and continuous action footage: reject visible
   contact/cloth/hair problems independently of passing event tests. New VFX does
   not finish the underlying model.

Next owners: UI corrects copy; root supplies exact-source original captures and
ordinary input receipts; reference reviewer records independent visual decisions.
