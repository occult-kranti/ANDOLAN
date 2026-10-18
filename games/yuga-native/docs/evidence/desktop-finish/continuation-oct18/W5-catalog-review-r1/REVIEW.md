# Bounded catalog source review

Accept the three current registrations: `ui-modal-resize-focus`, `desktop-world-render-resources` and `desktop-army-render-resources`. Both external text-script oracles are explicit dependencies and match the fixtures’ fixed hashes. Their shader and infantry/vehicle-art references, the map, modal input bindings, and runtime assets are included by the existing recursive inventory. None of these three fixtures inherits an unlisted test.

The existing final before/after dictionary equality remains mandatory for a passing catalog. Nine private copied-file mutations (three invoked fixtures, two oracles and four transitive runtime inputs) were detected individually by the actual inventory function; canonical files were never changed. Existing selftest source retains CLI routing, closure expectations and its synthetic invoked-fixture mutation rejection. No engine, native test suite or broad selftest was run by this reviewer.

This accepts the reviewed source closure, not rendered behavior or cache identity. Persistent drift is checked; transient mutation followed by byte-exact restoration is not monitored. Imported cache payload qualification is separate. The fourth, idle-HUD fixture/registration remains pending and needs a short separate closure review.
