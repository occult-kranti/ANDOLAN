# D09-W2 implementation and focused tests

Controls and the guide now request a shared scroll reveal only when their viewport geometry changes. `ui_scroll_focus.gd` snapshots the existing focus, waits two native container frames and then scrolls it into view **only if clipped**. It never grabs focus. It resolves weak references before each typed check and rechecks owner/scroll/focus lifetime, visibility, the caller's existing `_accepts_input` policy, ancestry, tree identity and unchanged global focus. Unrelated focus, hidden/disabled/retiring owners and freed controls cancel the work. Manual scrolling after the resize is left alone.

The guide calls the same helper for its ability list and details pane; only the pane containing current focus qualifies. Existing initial Bow reveal, effect-feedback reveal, capture/persistence, close/opener semantics, fonts and layout remain in their original owners. The helper is 34 lines rather than a new generalized focus manager. Pinned craft-floor was read before UI edits; the native indigo/ivory/gold identity is unchanged.

## Same final regression, original versus current

`tests/ui_modal_resize_focus_cases.gd` uses engine-dispatched press/release input to select Guardian Circle capture and Dawn Volley, starts from a fully visible focus at100%, and changes the actual canvas factor to200%. It includes preserved state/bindings, native Escape/cancel/close/opener behavior, manual scroll, focus moved elsewhere and hidden/disabled/freed peer/freed modal races.

- Exact originals: **21/23**, native exit1, clean log. Only the controls and guide 200% reveal assertions fail.
- Current source: **23/23**, native exit0, clean log. Target focus and all lifetime/ownership counterexamples pass.

`baseline-r3/` and `candidate-r3/` contain the same final fixture's complete native reports, source pins and command logs. The source-before checkpoint is `a7c9f46bbbfeef59a042919231978436892be934`; full final hashes and `.gd.uid` identities are in `source-freeze.json`. Shared helper UID is `uid://b8uc3y583d6ti`; regression UID is `uid://bktm5cprp3hxr`.

The first candidate run caught a real lifetime error: a freed Node was rejected at a typed function boundary before its validity guard executed. Weak-reference resolution closes that boundary. The next attempt exposed inferred-Variant warnings for `weakref()` results, corrected with explicit `WeakRef` types. The initial fixture also took three reverse tabs to the final **Dawn Volley** mapping while asserting **Guardian Circle**; the final route uses four. All those failed reports/logs remain. The earliest helper bytes were not separately pinned before replacement; its failure log remains, while final executions pin every helper/caller/test byte. No failure is relabeled as a passing implementation.

All runs use tiny copied scripts/data with immutable font hardlinks, CPU4 and bounded native headless execution. No editor import, world/hero scene, heavyweight renderer or giant dump was run by W2. Source whitespace checks are separate from behavior. Root owns the shared catalog registration; W6 independently reviews the final source and evidence.

## Actual handoff

The parsed tiny `board.gd` and `native-plan.json` use production controls and guide, with native keyboard capture/selection. A late input gate handles F8 before binding capture; F8 changes only the fixture's real scale, not shipping shortcuts or layout code. The observer/project owns the 1280×720 canvas and960×540 window. Metadata records target/ScrollContainer rectangles, selected ability, capture action/status and actual scale.

W1 owns one combined native before/current batch, limited to six meaningful originals: original100/200 controls and guide, then current200 controls and guide. The full return/cancel route still executes on both branches without redundant return screenshots. Headless23/23 is not pixel or OS-window acceptance. See `03-acceptance.md` when that separate gate closes.
