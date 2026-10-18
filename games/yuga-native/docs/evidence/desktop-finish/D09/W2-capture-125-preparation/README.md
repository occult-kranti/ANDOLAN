# D09 W2 — ten-shot final UI capture preparation

This prepares source-bound actual screen review; it does not complete a screen round or establish new pixels. The prior eight-shot helper (`5df5914d8cb52db79ae60ac5566fdf2314e6e1d84032832166f9fc800c2242cc`) is preserved byte-for-byte in `capture_compact_screens-v1.gd`, checkpoint `c96255ac575916cb8c3a300589051b5e2a94d4d4`, and W1's immutable `a02bc44b…` engine fixture. Its earlier native no-progress attempt remains historical evidence, not a successful screen review.

Canonical `tools/graphics-six/capture_compact_screens.gd` v2 is `9a0fb75c6fab298f0babb19c1c7d6aa7e5234b94b9472971086e34a54391c51e`. The added125% title/world observations target W4's actual periodic lane-visibility defect/fix; [W4's source-bound receipt](../../world-compact-title/W4/receipt.json) owns that16-check failure/correction and39-check composite qualification. Final caller is `b03c682669af55ca26b1dc44676850c40106ce794f2f20eb407c6e64e841f0f1`; HUD remains `68e3cc06…`, loader `a5d236a4…` and guide `a76b3d23…`.

W1 owns a new declared child and the external `compact-screens-125` runner case expecting10 shots. The original `compact-screens` engine fixture is not rewritten. V2 captures:

- `00-title-100`, `01-title-125`, `02-title-150`, `03-title-200` after actual boot/loader arrival.
- `04-world-100`, `05-world-125`, `06-world-150`, `07-world-200` after real primary-button Enter activation.
- `08-overview-200` through real F1; `09-guide-200` through real pause/F3, followed by exact-opener return verification.

The same physical960×540 /1280×720 base and12 ordinary frames per factor remain. World processing, camera, clocks, health, light, pose and UI styles remain product-owned. No manual layout helper is invoked. Source hashes before/after, actual camera, clocks, panel geometry, focus, lane visibility and framebuffer identity accompany each observation. All four world clocks must progress; suspended overview clocks must hold. Preflight writes only JSON.

The v2 parser check passed exit0 in0.14s; it instantiated no scene, imported nothing and rendered nothing. It was run before the queued CPU4 release; the full native preflight subsequently ran after W3's import completed and W3 explicitly released CPU4, following W6/W4 coordination. W1's declared child is now `04c1b7dcdc7d0177548d76d9767a1a75f07582363c1775169d68e05e9bca768a`: exactly callerb03 +helper9a over the preserved base. [Native preflight14/14](preflight-r1/preflight.json) passes exit0 without warning/error, with10 JSON observations, no source drift and zero images. World clocks advance0.8→1.2→1.6→2.0; lane visibility is false at125/150/200%. Guide/overview input and exact pause-opener return pass. Actual rendering remains pending. No runtime source changed in this W2 packet.

The supplied command initially refused the occupied default display192 before engine launch; [that attempt](attempt0-display-refusal.json) is retained. The bounded rerun used explicit unused display194. CPU4 was released directly to W3 afterward. Exact invocation/engine output, child-source receipt and source/artifact hashes are retained beside the [sealed receipt](receipt.json).
