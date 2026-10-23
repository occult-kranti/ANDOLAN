# Narrow roadmap evidence-binding repair

Independent addendum after foundation run `40023890588` failed its ledger step. The frozen initial [review](final-review.json) is retained; it did not claim a full foundation-CI run.

The unpatched `069ab775` ledger reports exactly one error: FG00-T02's recorded SHA no longer matches `FULL_GAME_PRODUCTION_ROADMAP.md`. Its earlier tool/process amendments changed the document without refreshing this binding. FG00-T02 is **“Approve full design and validate executable backlog”**, an already-complete documentation/design task. Its scope remains appropriate: the current document still distinguishes planned 6v6/eighteen-minute production rules from current browser 3v3/480-second authority, owns fourteen heroes/lifecycle work, and preserves the complete FG06 native 3v3 gate and remaining art/network/hardware acceptance.

Root's patch changes **one JSON scalar only**: that evidence SHA, from `f886c42e…` to actual document SHA `455edc1115befbb629b8870da139460370ffb89e9c04066c53346e7a44aaab8a`. Restoring the old scalar makes the parsed working ledger exactly equal to committed HEAD. Task status, acceptance, scope, dependencies, owners, queue, milestone/task counts and campaign completion are unchanged. The repair does not edit the document or accept new game work.

Independent local checks passed:

- Ledger: 16 milestones, 70 tasks and 30 evidence files; no errors.
- All 12 graph/evidence counterexamples, including the stale-hash rejection.
- Archived committed evidence: 6,244 files at `069ab775`; no errors.

[The machine-readable addendum](roadmap-binding-fix.json) records the exact semantic comparison and tool results. Root still needs to push the repair and observe the fresh CI result; these local checks are not a claim that remote CI has passed.
