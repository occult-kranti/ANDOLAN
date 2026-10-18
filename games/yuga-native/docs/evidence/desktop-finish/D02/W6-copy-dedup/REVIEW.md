# D02 — loading error guidance deduplicated

The actual initial-boot error repeated recovery instructions in both the controller error and the generic progress guidance. Only `scripts/loading_presentation.gd` changed: the error-phase progress guidance is now empty. The specific destination error, `LOADING STOPPED`, Retry/Back actions, focus behavior and reserved layout remain intact. Source `3db9158ff1be3806a406d6b561e9523188428590` plus this one-file overlay; all earlier journey and boot snapshots remain unchanged.

Before: `a37992fd733d96f4ec866aa95e04c60ad835d8a33ba762849c3cf632b2bdb3e0`.
After: `a01b52890a80cd14a0cecb767680e7905c411f926cae7f1ae97ca28c967424ac`.

The existing focused catalog passed **64/64** with stable inputs and clean engine logs: boot recovery 29, loading presentation 12, cancellation/focus 23. No test mirrors the removed sentence. [The retained summary](checks-r1/summary.json) and reports own exact commands and source inventories.

W1 then executed the frozen tiny fixture with native keyboard/pointer input, using the installed official Godot 4.6.3 engine, GL Compatibility, one software-render thread and fresh isolated state. Five manual and three queued originals, five native events, Retry, error dismissal to usable boot, reopen and genuine Quit completed with engine/cleanup exit 0. The existing independent audit passed **9/9**. This fixture does not exercise cancellation of an in-flight heavy resource load.

I directly opened all eight originals and rehashed all **34** central artifacts. The sole fixture source delta is the presentation file. The three error images each change 1,834 pixels; the two recovery images and all three queued images are pixel-identical. Specific error guidance and focused Retry remain legible; Back and boot Quit are contained. No new layout issue was observed. [Independent image/source comparison](native-original-review.json) and [execution audit](native-audit.json) retain the exact pins.

Originals and full logs live once in [W1's central archive](../W1-boot-dedup-native-r1/REVIEW.md), receipt `d514f7b70f0215e3ba91c11af021549b0d94483981bd83a0a677353a32d3d082`. The one driver V-Sync warning is retained; the run has no engine errors or leaks. The read-only pixel comparison emitted a Pillow API-deprecation warning; it did not alter images or the engine result.

This closes the observed duplicate-copy follow-up only. No world-load timing, GPU performance, full quality, art, package or in-flight cancellation acceptance is added. CI observations in the adjacent folder track exact `3db` separately and do not qualify this overlay or the later paving promotion. Newly copied test-user caches are excluded from this report's artifact receipt/checkpoint list.
