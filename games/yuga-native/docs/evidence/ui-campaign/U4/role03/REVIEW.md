# U4-03 — cancellation, reentry and exact progress notifications

Product: native YUGA, Godot 4.6.3. Base commit: `bc1a3dceaddc11f5c0745e73ad1f25f2ca77a0fb`, with the source hashes in each receipt defining the tested working tree. No commit or shared campaign ledger was changed by this role.

The loader now suppresses a notification only when phase, message and floating resource progress are all exactly unchanged. It preserves even a sub-percent progress change, new-attempt transitions and cancellation inside a phase callback. Resource progress still comes from threaded ResourceLoader; synchronous scene construction remains a distinct phase with unknown percentage. It also rejects detached or foreign-tree callers and cancels pending navigation when a live caller is removed from its tree. The atomic scene-commit interval remains protected.

Final `scripts/scene_transition.gd` SHA-256: `8ecaa8ae6359b2a5a89f1acbdd1d544058570a3effe656698b97a9adab7ec5e0`. `source/` preserves the exact changed loader, verification tools and tests. `archive-manifest.json` maps original scratch runs to copied evidence and hashes. Earlier unsuccessful evidence has not been overwritten.

## Reproduced failures and checks

- `signal-before-r1`: **9/11**, including seven exact duplicate phase notifications among twelve total and a failed exact-duplicate boundary assertion. `signal-after-r1`: **11/11**, zero adjacent exact duplicates and five observed notifications in that fixture. The counts are fixture observations, not a performance benchmark.
- `detach-before-r2`: **11/13**. A detached caller could begin navigation; removing a caller during real threaded loading did not cancel it. `detach-after-r1`: **13/13** after the guard. The preceding parser failure is separately preserved as `detach-parse-before-r1`.
- `ci-transition-r2`: **13/13**, clean exit and diagnostics, exact source unchanged. Reproduce through `python3 tools/ui-campaign/check-transition.py --engine godot --report /tmp/fresh-transition-report.json`. The temporary project contains real small PackedScene fixtures and existing font imports, and refuses execution in the product project. No heavy import or rendering is required.
- `native-transition-final-r3/validation.json`: **21/21** over actual XTest input and read-only signal/state observations. Eleven manual originals, four unique successful completions, one persistent loader instance, four unique cancellation callbacks and two failures (missing scene plus keyboard Retry). A real loading signal precedes threaded cancellation; the cancelled attempts never subsequently complete. Queued duplicate activation produces one attempt. Paused cancellation restores the caller's actual pause/process/focus state, and Back restores its exact opener.
- `boot-recovery-final-r2/validation.json`: **6/6**, five manual originals and actual native Quit exit **0**. Initial failure, keyboard Retry, usable boot Back, reopening the error and return to Quit all retain the final loader hash.

The final native transition command was:

```sh
taskset -c 2 python3 tools/ui-campaign/run.py --mode transition_fixture \
  --plan tools/ui-campaign/transition-plan.json --renderer gl_compatibility \
  --width 960 --height 600 --display 187 \
  --shader-cache-seed /tmp/yuga-ui-u2-integrated-window-r2/user/cache \
  --output /tmp/yuga-u4-native-transition-final-r3
python3 tests/ui_native_transition_cases.py \
  --capture /tmp/yuga-u4-native-transition-final-r3 \
  --report /tmp/yuga-u4-native-transition-final-r3/validation.json
```

Recovery used the same CPU/display/render settings, `--mode boot_recovery --plan tools/ui-campaign/boot-recovery-plan.json`, a fresh `/tmp/yuga-u4-boot-recovery-final-r2` output and no cache seed. All owned processes stopped after each run. The transition process is intentionally terminated after its final usable sample; only the recovery run verifies application Quit.

## Original frames and scope

`native-transition-final-r3/index.html` and `boot-recovery-final-r2/index.html` display untouched originals with state links. All eleven transition manual hashes match the already inspected corresponding seeded-r2 originals, including repeated frames with identical pixels. Final paused-caller and missing-error originals were inspected again, as were final boot error and usable Retry/Quit originals. Text, focus and recovery actions fit the 960×600 2D fixture. The actual phase recorded after framebuffer completion is authoritative; an automatic filename can precede a later phase.

These fixtures do not load a world or hero. Their claims are actual 2D input, loader lifecycle and recovery presentation, not integrated 3D, art acceptance, physical-GPU FPS or full-game asynchronous construction. Compatibility llvmpipe reports its known unsupported V-Sync warning; there are no engine errors. Earlier native runs remain separately labeled as preceding the detached-caller guard.

`run.py` now accepts `--render-threads {1,2}` (default one) and `--shader-cache-seed`. The final tiny run stayed on CPU 2 with one llvmpipe thread and one OpenMP/BLAS thread; it independently copied 105 seed files and verified the source seed unchanged. The two-thread option was dry-run checked without launching a renderer. Future integrated U5 capture may use the separately authorized heavy lane with two workers and a pinned warm cache. This does not make a cold-start performance claim.

Next owner: root for CI/catalog acceptance and final source approval; role03 for the shared U5 integrated capture after the accepted hero/UI freeze. Independent U4 review was informed of the detached-caller counterexample; its own later recheck remains distinct from this author's regression evidence.
