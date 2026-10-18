# U5-03 — final loading, recovery and shared native capture

Native YUGA, Godot 4.6.3. The capture identities are the exact source manifests below; the worktree base at handoff is `00a204bfbf5e1de47a0a12a233841d7f3a2475ab`. Later I1 motion work is separate. This role made no commit or shared ledger edit.

The complete run produced **39 manual + 15 automatic originals**, then an explicit correction supplement produced **15 manual + 15 automatic originals**. Both finish through actual native Quit with exit **0**, unchanged source and unchanged source cache seed, and no engine warnings/errors. Separate final-loader boot recovery completes **five manual + three automatic originals**, Retry/Back and actual Quit **0**. Its only warning is Compatibility llvmpipe's unsupported V-Sync setting.

The originals and state/phase receipts are centralized in [integrated-r1/index.html](integrated-r1/index.html), [integrated-r2/index.html](integrated-r2/index.html) and [boot-recovery-r1/index.html](boot-recovery-r1/index.html). `archive-run.py` copies and verifies original bytes; galleries use CSS sizing only. Integrated PNGs are **960×540 content framebuffers from 960×600 native windows**. The separate 2D recovery PNGs are 960×600. Input coordinates include the letterbox transform.

## Exact source and execution

- First snapshot: `/tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native`, **748 source / 350 existing import files**, manifest SHA-256 `720d124a51d3c31b95424889a1047360720c078cda1480405f4e705442cd5ecb`. Receipt: `source-freeze-r1.json`. It combines the accepted R7 hero/cache promotion and sealed U4 UI.
- Final derivative: `/tmp/yuga-u5-source-r2/ANDOLAN/games/yuga-native`, **750 source files**, manifest `0f4871dd0b09cca7f240454f33016bbe154567f0840fc15d6e7f164c3871666f`. `repair-overlay.json` records twelve changed/added files, including **three runtime scripts**, capture fixture/observation/input support, and focused tests/catalog. No asset or imported resource changed. Earlier screenshots remain labeled r1.
- Final courtyard: `197a2349cebdf26d195bcec64c9380f74c76537970def2ea9bea3193086b5a30`; guide: `ff710c7aad3a4214ccd0398bc1d8cac9064ca8ec9f864a1faf94744346f256c5`; world: `1a11e57c1ae5a6e663b993a12d565228f30dec618a4336856c19d471ddf71c6b`.
- Loader is unchanged from the U4 cancellation fix: `8ecaa8ae6359b2a5a89f1acbdd1d544058570a3effe656698b97a9adab7ec5e0`. Boot, theme/fonts and loader closure are unchanged by the final overlay.

Both integrated takes use CPU 0,1, Forward+ llvmpipe with two workers, OpenMP/BLAS one, isolated XDG directories, and a 600-second per-condition watchdog. The first independently copies 105 seed files from the prior U2 Mesa cache; the supplement copies the completed r1 private cache. Source seed hashes and thread/affinity settings are in `run.json`. This is warm-cache software rendering, with no cold-start or hardware-FPS claim. Elapsed harness durations were 496.9 and 191.8 seconds, including startup, input, captures and cleanup; they are not performance benchmarks.

Reproduction command for the final supplement:

```sh
taskset -c 0,1 python3 /tmp/yuga-u5-source-r2/ANDOLAN/games/yuga-native/tools/ui-campaign/run.py \
  --mode integrated --project /tmp/yuga-u5-source-r2/ANDOLAN/games/yuga-native \
  --allow-authority-staging \
  --plan /tmp/yuga-u5-source-r2/ANDOLAN/games/yuga-native/tools/ui-campaign/u5-repair-plan.json \
  --renderer forward_plus --width 960 --height 600 --display 188 --timeout 600 \
  --render-threads 2 --shader-cache-seed /tmp/yuga-u5-integrated-window-r1/user/cache/mesa \
  --output /tmp/yuga-u5-integrated-window-r2
```

Use a fresh output and an explicitly reserved render lane. The original 39-view take uses the r1 snapshot, `u5-integrated-plan.json`, and the U2 seed. Exact executed commands are retained in each `run.json`.

## Actual coverage and corrections

The first run contains 82 native event records: configured boot/title, Bow and ultimate guide, actual saved effects toggles and their bound receiver, fixed-Done Settings, key capture/cancel, nested Back/focus, Help, world HUD/map/overview, pause, training/reset, scripted duel and returns. The supplement contains 43 native event records, including native wheel scrolling and a full night transition before any simulation hold. `07-night-world-pause` records `night=true`, `phase=1.0` and focused Continue; darkness is not inferred from pixels.

Original review found and preserved these r1 issues:

1. Help default focus scrolled its heading out of view. The final source shows the heading on fresh entry and reopening; a native wheel scroll moves the content between those entries.
2. Saving guide preferences on long Dawn Volley details could leave the saved-status line below the viewport. The final screenshot shows the full status and preserves focus on the motion toggle.
3. The explicit capture fixture held the world's presentation callback while respawn/army reset moved the player, leaving the old location/map marker in four staged r1 views. This was a **fixture defect**. The corrected helper runs the normal presentation callback, verifies that army/relay authority is unchanged, and verifies both map position and district label against the actual player. Corrected respawn and all three outcome originals are in r2.
4. Siege copy combined an enemy total with all-team type subtotals. Final native siege shows the actual enemy-only total (`Siege 2 enemies · Gold 0`).
5. A film round trip reset the title's training selection. The final actual round trip retains Bow training and focuses `Begin bow training →`.

The observer remains read-only. The opt-in `integrated_capture.gd` driver executes clearly recorded `authority_stage.gd` steps for arranged lane/relay actors, damage/respawn and terminal core inputs. It never assigns a winner or UI label. Each outcome comes from the actual army step and emitted outcome signal. The fixture records its explicit process holds, before/after rules, presentation refresh and release. These are **staged authority views**, not native combat wins. All navigation and preference changes use XTest.

## Loading and verification

Both integrated runs retain exactly one loader and one persistent layer across five real replacements: boot→title, title→world, world→title, title→duel, duel→title. Each completion emits once; the observed phase stream has no exact adjacent duplicates. Construction has no aggregate percentage. In r1, the fifteen automatic originals contain **five queued, two loading and eight constructing states**; some `auto-loading-*` filenames completed after construction began, and their JSON correctly records that later phase. Filenames are never used as phase proof.

`verification.json` passes **18/18** lifecycle/correction receipt assertions. The final frozen real-world authority helper passes **9/9**, clean, in `yuga-u5-frozen-authority-r2.json`; earlier preparatory receipts, including the initial teardown warning and subsequent clean drain, are retained. U4's separately captured queued/threaded cancellation, detached caller and reentry evidence remains tied to the same final loader hash, rather than being relabeled as new U5 input.

Independent role06 validates **101/101** receipt/hash/frame assertions for r1 and **53/53** for r2, including every raw PNG, captured-frame expectations, exact source identity and Quit. Roles02/06 directly inspected all 84 integrated originals; roles01/04/05 reviewed their screen domains. Their reports and validator commands are under the sibling role directories. This author also inspected loading/construction, initial and returned title, Help failure/repair, guide saved feedback, live/contested world HUD, terminal summary, corrected respawn and siege originals. The five final recovery originals exactly match the previously inspected final U4 recovery pixel hashes and were generated by a fresh successful U5 native run.

This establishes the scoped native UI/input/loading behavior above. It does not establish finished hero/world art, continuous action motion, a physical GPU, Windows behavior, full-game asynchronous construction or untested 2× scaling. Synchronous construction and first rendering can still block behind the visible preparation screen. Later I1 overview-motion synchronization has its own source and gate.

All owned engines/Xvfb stopped. The heavy lane was explicitly handed to `r2_06_capture` for R4. Next owner: root and independent reviewers for campaign acceptance; role03 proceeds to the separately assigned I2 seeded transition stress on CPU 2.
