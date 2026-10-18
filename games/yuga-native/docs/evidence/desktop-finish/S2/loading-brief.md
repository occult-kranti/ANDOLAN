# S2-W2 — loading presentation brief

Audit source: S1 candidate `98e10cc5184ba1b51b42113496a529d8cc8f62b0`, loader `81e2ef601dbc6888ac79ee3f866d8c8f436a3126464915cddd4aeebb6b68de07`, boot `c14fa334fd9555973cc3b3603df3cb606cf130adf4d8905f463e135df06e655b`. S2 logic remains W6-owned. This brief does not claim new rendered acceptance.

Directly inspected untouched originals: G1 [queued](../../graphics-six/G1/native/auto-queued-1.png), [resource loading](../../graphics-six/G1/native/auto-loading-1.png) and [construction](../../graphics-six/G1/native/auto-constructing-1.png), plus U5 [real missing-scene recovery](../../ui-campaign/U5/role03/boot-recovery-r1/01-initial-missing-scene.png). G1 JSON records actual queued/loading/constructing phases; filenames alone were not used as phase evidence. The [U5 loading review](../../ui-campaign/U5/role03/REVIEW.md) distinguishes resource loading, synchronous construction and native recovery. No new engine or image capture was needed for this audit.

The actual G1 loader is a narrow centered panel, with a large gold wordmark and comparatively small destination/status. Its height and center change when the resource bar appears. The error original retains working Retry/Back but reads as a generic dialog. Current boot also labels itself “Confluence” although its first destination is the courtyard practice menu, before choosing Confluence or training.

Only two improvements are proposed:

1. **A stable loading/recovery plate with a clearer information hierarchy.** Use the existing indigo/gold/ivory grammar, a smaller serif YUGA signature and fine gold rule, then the destination heading and actual status. Reserve a fixed progress region so queued/loading/construction/error do not move the outer panel or action row. Use a bounded reading width and a scrollable body with actions outside the scroll for shorter/scaled viewports. Retry remains the error primary; Cancel/Back remains a native secondary control. No fake gameplay image, new 3D dependency or ornamental progress animation is introduced.
2. **Destination and progress scope made explicit.** A concise context tag distinguishes Practice menu, Offline lanes and Scripted duel. Resource percentage is labeled as scene-resource progress only; queued/unknown/construction/error show a real named phase without a fabricated percentage. “Cancel loading” describes the busy-state action; error retains Retry/Back. Boot’s static subtitle should say “Offline practice”, not imply direct Confluence entry. Map/actor preparation remains explicitly pending until the real controller completes; the view cannot invent separate map/hero-ready checkmarks from ResourceLoader percentage.

## Exclusive implementation contract

W2 owns new `scripts/loading_presentation.gd`, a lightweight Control using bundled fonts and private native StyleBoxes. It exposes the same `card`, `heading`, `detail`, `progress_bar`, `retry_button` and `back_button` references to W6’s controller. It may consume `phase_changed`, destination and resource progress to format a stage/context label; it does not start/retry/cancel work, change timing/tickets, own focus, toggle enabled/disabled state or claim readiness. No new await/deferred lifecycle is required for the view.

After W6’s logic freeze, serialize a small `_build()` delegation in `scene_transition.gd`; W6 keeps button signal binding and focus-cycle wiring unchanged. W6 also owns the one-line boot subtitle correction. Existing scene allowlist, snapshot fields, exact progress value, visible-bar rules, error messages, atomic commit, disposal, caller restoration and duplicate suppression remain controller-owned. There is no second navigation owner.

## Acceptance

One focused 2D presentation test should verify stable panel/action geometry across phases, scoped percentage visibility, long error wrapping, footer reachability at compact/scaled sizes, destination tags and independent view resources. W6 runs its focused lifecycle fixture against the delegated view; do not repeat the whole game suite for typography. Final native originals must include actual queued/loading/construction, real missing-resource Retry/Back, boot cancellation/reopen, and title↔world/film destinations. Compare the new source to untouched prior originals; retain source hashes and state receipts. Actual rendered/type/native-input review remains the render owner’s gate.

S1’s intermittent ObjectDB exit warning is tracked separately in [the bounded witness](../S1/W2/final-host-leak/witness.json): two exact-root verbose repeats were clean, so no cause or teardown fix was inferred. S2 presentation must not hide or relabel that residual.
