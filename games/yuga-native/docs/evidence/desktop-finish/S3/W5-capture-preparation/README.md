# Matched motion capture preparation — no rendered acceptance yet

The verified pair is ready; **no W5 render has started**. Root owns the heavy lane and must grant it after the current UI/art captures. The motion source remains frozen at `8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8`; the strict25/27 comparison and its120Hz landing/60Hz swing tradeoffs remain open. This preparation does not turn those failures into passes.

## Stages and ancestry

[Pair receipt](pair-r2.json) pins `/tmp/yuga-s3-motion-pair-r1/{baseline,candidate}/project` and the private import store. The baseline is exact119db2e6; the candidate exact8c3771a3. **Only `scripts/rama_motion.gd` differs between the1010-file staged source/cache inventories.** Both contain the same corrected canonical capture_focus307edf74 and the same new capture_transition helper. Each stage has a private copied103-file Godot warm seed (11,938,824bytes); each launch copies that seed again into its own isolated user directory. No Mesa seed survived the reset: every launch starts a private empty Mesa cache. This is not a cold-start or shader-startup performance pass.

W1's verified current presentation is the parent, marker6349218e…13a19, recovered from full-S2 plus19 declared current changes. These include current UI/world/loader/environment-finish and the inactive optional fletching source; all are identical across this pair. The receipt lists every difference from the historical S2 marker. Root approved current presentation for both variants; the pair is not mislabeled as historical-S2 art. All176 import source/MD5/output mappings were revalidated without importing. Imported bytes share a pair-private content-addressed readonly store; source files and warm shader caches are copied, not linked to mutable canonical files.

The first preparation inherited the parent's source-byte summary despite adding the harness. Only those summary totals were recomputed before the final preflight seals; runtime/helper/import bytes did not change. The original pair/seals and the first valid landing probe remain under [preparation-history](preparation-history). Final stages use the [r2 receipt](pair-r2.json).

## Executed headless proof

Four sequential coordinatedCPU3 runs completed cleanly, using affinity plus LP/OMP/BLAS1, **without unsupported `--max-threads`**. Godot's engine worker pool was not capped. The runner applies a180s overall and120s no-progress deadline for these preflights. Raw reports are retained as deterministic gzip, together with exact command/run/log and raw/compressed SHA receipts under [preflight](preflight).

| Case | Baseline | Candidate | Observations / cadence |
| --- | ---: | ---: | --- |
|landing120|7.576s|7.160s|40 observations; actual120Hz physics, one physics tick per sample|
|full|49.873s|49.677s|120 observations;60Hz physics, two ticks per30Hz sample|

Landing has five applicable observation gates; full has seven. The additional render-adjacency entry is explicitly **not applicable in headless mode**, so it is not presented as a tested rendering condition. In both pairs actual camera, root/velocity, grounded state, kit/army clocks, fixed plant targets, transition clocks, all nonleg globals and physics counters match exactly. The [two paired identity comparisons](preflight-comparison.json) pass; they are identity checks, not motion-quality approval.

The short case begins with40 title ticks, records the first observation at physics41 and retains the known49→50 landing transition. It reproduces the peak ankle displacement4.889→7.324mm and grounded skin minimum−11.350→+0.016mm. The declared close camera frames actual foot/toe skin with a24px margin while intentionally cropping the upper body. A2.435mm reference vertical displacement projects to about2.3–2.5px at the soles; the right ankle's baseline/candidate position difference at sample9 is10.646px. These are numerical projections only. Lighting, shading, filtering, occlusion and human inspection still determine whether the difference is visibly distinguishable.

## Exact actual-capture queue

[Ready commands](ready-render-commands.txt) are self-contained and bounded. Execute **one at a time only after root's lane grant**. They start a private Xvfb display187, preserve full original1280×960 PNGs and callback records, copy private warm caches, capture the exact engine/runner/seal identity, check source stability, and terminate only their own children on deadline/failure. The40-frame landing supplement runs physics and capture at120Hz. Its actual draw counter must increment exactly one per image, as must the physics counter. The full take runs capture30Hz/physics60Hz and requires two physics ticks per image. No skipped/repeated frame is silently accepted.

The full120-frame sequence remains required: public start_training, analog walk, full run, public reset while moving, stop, Input jump/land. The separate40-frame close view supplements it; it cannot substitute for full-body continuity. Both cameras follow the same authoritative actor anchor with fixed offsets/lenses for each case. Controls are declared scene API/Input calls, not XTest or human play. No runtime root, pose, action clock, plant anchor, damage or collision assignment occurs in the harness.120Hz is an explicit fixture setting, not a shipping gameplay-rate change.

No source or renderer setting may differ between the paired actual runs except the declared motion source. Keep matched engine/adapter, image size, scene, camera, input timings, shader/light controls, morphs, secondary behavior and observed LOD receipts. Review first grounded lift, walk→run swing, moving reset and final settling from the original images and complete event data. Preserve the native25/27 numeric evidence regardless of visual disposition. A30Hz full take does not independently resolve a one-physics-tick120Hz peak.

## Resource estimate and recovery

The staged pair currently uses443,035,648allocated bytes across unique inodes (571,188,495logical bytes, including shared imports counted repeatedly). Expected320 original PNGs are roughly0.25–0.50GB from prior1280×960 originals, plus four private per-run Godot caches (~48MB total), new Mesa caches and JSON/logs. A **2GB working budget** is realistic, not a guaranteed maximum: pathological incompressible PNGs could raise the total above2GB. The runner retains a hard3GiB free-space floor and requires an additional512MiB before each run; no automatic deletion or import is performed. Root may schedule the80 close-view PNGs first, then the full240 PNGs without shortening either required take.

The previous/tmp stages were lost during restart. Repository receipts, source helper/runner, recovered-cache provenance and lossless preflight archives now survive independently of/tmp. Reconstruct via `prepare_pair.py` from a freshly verified W1 current base and exact recovered Godot seed; never infer that old/tmp paths still exist. Both prepared projects must pass the snapshot verifier before use. Actual originals must be archived before cleanup or a checkpoint/restart. No new release, GPU-performance, human-feel or overall motion-quality claim is made.
