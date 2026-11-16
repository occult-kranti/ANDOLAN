# Round 4 · cross-owner review and corrections

UI owner reviewed root's `rama_training_journey.gd` and `courtyard.gd` integration plus combat's `rama_ability_effects.gd` and `rama_projectile_warning.gdshader` changes. Root reviewed the new UI.

## Findings addressed

Root correctly identified that an empty real bow magazine still received a ready meter/card. The HUD now shows an empty primary meter, cooling bow glyph/card, retains `0 / 12`, and supplies the current reload binding in the notice. Other four abilities keep their independent ready/cooldown states. A new fixture spends all twelve arrows through the actual mounted cast/release path and confirms this behavior. The implementation does not rewrite ammo or award hits.

An R3 log had a Godot warning because filled `draw_rect` ignored a width argument. The call now branches between filled and outlined marks. The exact successor reran new feedback and combined action suites: 53/53, zero warnings/errors. Initial logs remain in `r3-evidence`; successor logs are `r3b-evidence`. One initial parse-check Variant inference error was corrected before any runtime test.

## Independent root training review

The root observer grants progress from ordered actual receipts, refuses old generations/duplicates, ignores misses/cover/cancel, and reads current bindings each time it reports. It cannot award damage or change cooldowns. Ground movement credit requires a meaningful accepted displacement; Guardian requires an actual hero shield/healing receipt.

The independent `r4_journey_layout.gd` mounts the actual courtyard and stages all six progress states to check the visible card at 960×600 and logical 100/150/200% scales with long Space/Shift/Ctrl bindings. All **18/18** geometry checks pass: card, labels and text fit; pause does not overlap; bottom hero HUD remains separate. This staging establishes containment, not natural completion or rendered appearance. Root's separate actual-kit 25-case suite owns natural receipt logic.

## Independent combat warning review

Code-level acceptance: the full firing lane is present throughout preparation; each pending lane retires only when `_projectile_eligible` says its authority delay elapsed. The stroke lies inside the exact projectile sweep. The two-tone shader has no TIME-driven launch claims and remains in the essential warning layer under reduced-effects/motion options. Primary shots retain no unnecessary ground-lane warning. Actual distant/bright-floor readability remains a rendered review: do not widen the warning beyond true collision to compensate.

The HUD and world warnings use the same actual `release_age_s` plus projectile delay, preventing contradictory pending/launched states. Marks indicate launch, never hit confirmation or charges.

R4a feedback passed 25/25 and root card layout passed 18/18 without engine warnings. A final availability guard was added after that feedback process (empty reload advice only while actively playable); the final R4b successor explicitly reruns feedback, context, reload and compact remap suites and owns final UI hashes. Previous reports retain their actual source hashes.

Next owner: lead for serialized imports/native captures, then this owner for R5 image/input review. Hardware performance, human feel and commercial art quality remain open.
