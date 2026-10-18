# Traversal availability during return

The combat HUD correctly reports RETURNING and zero health, but normal and constrained traversal guidance still advertises flight/tether inputs while the actor is inactive. Current source logic reads traversal mode/energy without checking the real hero receiver’s life state. This is misleading state/copy, not a missing traversal mechanic.

A current engine baseline creates the real Confluence world, delivers lethal damage through RamaVitals, observes actor deactivation and tests native 100→200→100 canvas layout. The same receiver’s army-clock respawn restores the ready actor. Twelve of 14 checks pass; only unavailable traversal prompts during RETURNING fail at both scales. Presentation leaves vitals exact; pause preserves the delay, terminal precedence and the existing 88px ready card pass. Raw results, exit 1 and 4.03seconds are retained. This staged-damage fixture is not a played enemy defeat or actual screenshot.

Historical actual defeat image inspected: `docs/evidence/ui-campaign/U5/role03/integrated-r1/19-STAGED-defeat-hud.png`. Existing current-package controls capture also exposes paused traversal action copy behind its modal, but is not a current defeat capture. W1’s current-source 100/200 defeat originals remain pending at this checkpoint; no shipping UI source is edited until that witness is reviewed.

Repair intent: use a small shared normal/constrained availability formatter based on real receiver/actor state, keeping energy and contextual recovery guidance while suppressing unavailable bound-action instructions. Preserve terminal precedence, active flight/tether/cooldown guidance, saved keys, idle 88px layout, the existing focus helper and all gameplay timers/receipts. No new theme or general UI manager.
