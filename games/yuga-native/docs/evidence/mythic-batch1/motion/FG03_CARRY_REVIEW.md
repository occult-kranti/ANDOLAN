# FG03-T01: native Rama carry and grip

Reviewed 2026-10-17 against working-tree changes over `8991a22a9d0fe17e9989eb8ae1edb8fadcf0b019`.
Product: native YUGA. Scope: a bounded upper-body carry correction for native idle/run,
closed bow grip, action ownership, and reproducible evidence. The experimental TPS
full-body run is still unpromoted.

Durable selected evidence: `docs/evidence/mythic-batch1/motion/`. It retains the r3
MP4 and three capture JSON files, eight selected unchanged PNGs, final corrected-
material test reports/logs, both rejected-run notes, and a copy of this review.
The complete 169-frame scratch sequence remains available separately.

## Result and runtime contract

`scripts/hero_pose.gd` is an optional `SkeletonModifier3D`. It resolves 29 upper-body
rotations once, lowers the carry with modest shoulder/elbow adjustments, and closes
the right fingers using calibrated rotations from this project's own authored fire
clip. The carried bowstring returns to its neutral rest position. Other translations,
all scales, spine, root and legs remain owned by the selected animation.

`configure(visual, animator)` returns false atomically for incomplete rigs or duplicate
configuration. `set_state(clip, delta, traversal_mode, action_active)` approaches the
carry pose over 0.22 seconds in idle/run. Fire/cast or an active action sets the carry
contribution to zero immediately: a projectile can be emitted on the first action
tick. Jump, defeat, flight and grapple suppress the carry. `cancel()` is idempotent;
invalid or oversized delta cancels safely. Scene pause stops modifier callbacks.

The root-owned player integration configures after the traversal modifier, supplies
the selected clip and action/traversal guards, cancels alongside traversal/reset/focus
loss, and exposes diagnostics at `traversal_report().carry_pose`. This hook was read
independently and its exact source hash is pinned by the tests and capture.

## Three rounds and retained findings

1. **Inspect and calibrate.** Read the project's original bow construction and finger
   authoring, inspect the actual 164-joint imported skeleton and prior carry images.
   The native clips already contain a closed grip; the experimental rest carry does
   not. Copying the full authored grip without calibration produced 10.287 mm maximum
   distal penetration into the handle proxy. Per-finger closure was calibrated to
   `[0.25, 0.90, 1.0, 0.80, 1.0]`; thumb opposition needed less closure.
2. **Integrate and challenge.** Preserve original native locomotion and add meaningful
   CPU-skinned hand/sole tests. The first capture lacked the player's idle/run loop
   flags; the next capture exposed delayed first-shot ownership and did not reproduce
   the live action timing. An independent read-only agent found the latter mismatch.
   These captures remain rejected; passing frame generation did not accept their flow.
3. **Correct and verify.** Immediate action suppression, exact native loop flags and
   live `.055 s` fire blend / `.32 s` action window / `.24 s` cooldown are represented
   in the final staged capture. At 24 Hz, the three firing triggers occur at 0, .25
   and .50 seconds. Both-clock tests and the fresh 169-frame r3 capture pass their
   stated numerical and provenance checks. Remaining art limits are listed below.

## Sources actually inspected

- `art/production/build_rama.py`: wrist-relative bow handle, centre `(0,.105,.025)` m,
  radius `.022` m, length `.092` m, and string attachment.
- Repository file `games/yuga/art/pipeline/animations.py`: this project's authored grip construction,
  including thumb treatment. These are existing project sources, not extracted
  commercial-game models or animations.
- `scripts/player.gd`: native loop setup, action selection, immediate projectile
  emission, fire cooldown, blend timing, and integrated modifier call order.
- `art/motion/motion-retarget-manifest.json`, `support-contact-samples.json` and
  existing motion QA: retained Godot TPS-demo provenance and unresolved run contact.
- `art/production/reconstruction.validation.json`: explicit material-only derivative
  proof. The original bake target remains recorded; target changes require an exact
  hash-linked structural proof in `compatible-targets.json`.

No new commercial client extraction, native binary analysis, book reading or external
motion download was performed in this correction.

## Tests actually run

Godot 4.6.3; isolated user-data directories; no new import during these test runs.
`tests/hero_pose_cases.gd` passes **24/24** with the ordinary clock and `--fixed-fps 60`.
`tests/motion_retarget_cases.gd` passes **37/37** against the explicitly registered
material-only derivative. The latter is structural QA, not promotion of TPS animation.

```sh
godot --headless --path games/yuga-native --script res://tests/hero_pose_cases.gd -- --report=/ABS/NEW/hero-pose.json
godot --headless --fixed-fps 60 --path games/yuga-native --script res://tests/hero_pose_cases.gd -- --report=/ABS/NEW/hero-pose.json
godot --headless --path games/yuga-native --script res://tests/motion_retarget_cases.gd -- --report=/ABS/NEW/motion-retarget.json
```

The pose suite uses **644 actual weighted distal finger vertices** and **3,798 sole
vertices**. Against the cylindrical handle proxy:

| Measurement | Before experimental rest carry | Corrected carry |
|---|---:|---:|
| Mean nearest distal surface gap | 34.609 mm | 0.143 mm |
| Maximum nearest distal surface gap | 55.077 mm | 0.253 mm |
| Maximum sampled distal penetration | 0 mm, open hand | 0.873 mm |
| Sole displacement caused by modifier | — | 0 m |

Each finger's nearest distal distance and maximum distal penetration must remain
within 2 mm. This is a geometric proxy, not tactile grip or proof that every hand
surface avoids penetration. Tests also cover finite dense samples, exact action
ownership on the first tick, ten rapid retriggers, preserved lower-body poses,
endpoint continuity, missing rig, duplicate configure, malformed delta, pause,
idempotent cancel, and engine restoration between modifier frames.

Pre-material-correction reports remain at:

- `/workspace/scratch/yuga-motion-next/check-action-fixed/hero-pose.json`
- `/workspace/scratch/yuga-motion-next/check-action-normal/hero-pose.json`
- `/workspace/scratch/yuga-motion-next/retarget-final-r2/motion-retarget.json`

Both 24-case reports have SHA256
`2c0d4275761541b8d4835575cb2a9d0355a4a6e8ceda958359045f3aa8d6db52`.
The 37-case report has SHA256
`490876a46655ad5fecb656fa30aa91753ea41664574adab69f449b579654f229`.

After the corrected surface was frozen and imported, the same suites were rerun
without runtime/test changes: **24/24 ordinary, 24/24 fixed60, 37/37 retarget**, all
exit 0 with no logged errors or warnings. Final reports are under
`/workspace/scratch/yuga-motion-next/check-material-final/{pose-normal,pose-fixed,retarget}/report.json`.
Both pose reports have SHA256
`336c4caa6740176cc379cc8f991907a9c58d0637dc35cf5b7205c5c567bce616`;
the final retarget report has SHA256
`2d9431dcc3ae61b186e786af8b3a1fb51789f9b4e9c84645541cf0489856abb7`.

## Actual r3 render and visual observations

```sh
python3 games/yuga-native/art/motion/run_carry_capture.py \
  --output /workspace/scratch/yuga-motion-next/render-r3 \
  --display 119 \
  --shader-cache-seed /workspace/scratch/yuga-motion-next/render-r2-user/cache/mesa
```

The command exited 0. It produced **169 actual 640×640 frames**, 24 Hz staged native
idle → run → three fires → idle → grip close-up, and a **7.041667 s silent H.264 MP4**.
Rendering used X11, Forward+, llvmpipe LLVM 19.1.7 and Godot 4.6.3. The runner checks
the imported scene source, image dimensions/hashes, source hashes, renderer counters,
actual run wrapping, trigger count, zero carry on every action frame, and ffprobe
frame count/duration. It cleans up its own display process.

Actual images opened for visual review: frames **30, 60, 76, 77, 78, 83, 89, 94,
97, 98, 99, 100, 101, 102, 120 and 150**. The root independently opened 96, 108 and 150.

- Frames 30/60 show a lowered bow and bent elbows during native idle/run.
- Frames 76→77 show immediate return to the native firing pose. The first-shot arm
  raise is abrupt; this remains an action-anticipation limitation.
- Frames 77/83/89 show the three action triggers with carry contribution zero. The
  modifier no longer holds the string/arms down after a shot has already been emitted.
- Frames 97–102 show the bow lowering progressively as carry contribution rises
  from .19 to 1. Frame 120 retains the lowered carry. The draw hand opens during the
  transition; credible finger/string contact throughout the action remains unfinished.
- Frame 150 shows fingers wrapped around the handle and visible thumb opposition.
  No obvious open-hand gap is visible in that selected close-up.

This is frame/sequence sampling plus a complete machine-validated rendered file,
not a claim that a human watched the whole MP4 or approved production-quality motion.
There is no audio listening, hardware FPS, multiplayer, moving-ground foot-lock or
gameplay-distance readability result here.

The r3 images pin the earlier surface asset `81f7f2c5…`; its pale skin/pastel indigo
encoding was subsequently diagnosed by the material owner. Preserve these exact
images as motion evidence. The corrected surface requires its own final images and
an exact rig/animation equivalence proof; do not relabel r3 as a new-material capture.

Both surface targets now have explicit compatibility entries. The corrected current
GLB is `3424d72e74bb425c7e6bb2ff2fddc05c792657c437a888c56671fbd7d3ec3bcc`;
its six-check proof is `art/production/reconstruction.validation.json`, SHA256
`f750863cfa775554f285e02e26db7431d3505928cc41b5da8a8a9bb1d1a7a5b6`.
The earlier five-check proof is retained immutably as
`art/production/reconstruction.surface-r1.validation.json`, SHA256
`81da388632a387f0be3a706cbb8954d9aec93c251a4e0d7416ac185c0341d040`.
Both preserve the original 6,500,208-byte binary prefix, SHA256
`5d887c43f23001e826007a2b4fbb343a2f60569b6aca00e4b5cbcf8983506df2`,
plus the same hierarchy, skins, animations and original accessors/buffer views.

## Source and capture pins

| File | SHA256 |
|---|---|
| `scripts/hero_pose.gd` | `c07def74a71e755cd323c7e730d0884ea737fb8efd1342ed36d87dd8da22fceb` |
| Root-owned `scripts/player.gd` | `6b7206ff94ae5a79733c1e2ea8d4e10a842e65c3e5cf5ce6d28748bef0deea2c` |
| `tests/hero_pose_cases.gd` | `dfa7498c9f4851880ae831171c162d7e1f6c4a209f0ed8702c48f94997fef917` |
| `tests/motion_retarget_cases.gd` | `b20e5063156d8833e89ec11ab3fd20f3602603298eb3e88ccfc5f21c8f9af12e` |
| `tools/capture-motion-next.gd` | `836c08e5acf3dcf653f08be456077d38595ac20d914f065853736a5714b043d4` |
| `art/motion/run_carry_capture.py` | `e0ac4776ea028150d7bc9e97ece9d6c1ea297622b7192eec95e0a39c8f888265` |
| Final `art/motion/compatible-targets.json` | `63493f6d10450661567ce21098797e59c9bace325f7a92b70ce67243797cd431` |
| Unchanged `assets/animations/tps_rama_motion_library.tres` | `95ffda72b8fc5d4d41e9702ce30918cffb22e75d907545dc5ff28fb01411554f` |
| r3 hero GLB | `81f7f2c51b7e5c20207bc449d7c81b7c3fee3cce618c93636cf009e9df9ce7d7` |
| r3 imported scene | `88373b16e224d957e567a9f6120821aea52f9ab0a139d5ec55e128058268886b` |
| r3 `motion-next-render-review.json` | `4fec745372022cbcfbdfaeb1b765a144916e8e4c762a4fe7bf68becf780fcf87` |
| r3 `motion-next-video.json` | `018646e58fae43f33e8206606ba6a13f3b102e7d0b58976751f5c2adef2b5fea` |
| r3 MP4, 746,204 bytes | `846f786f0a0b593534754e152c6d9b698a3e2038c478e6c6b1ce595816a65700` |

## Retained failures and next acceptance gates

- `render-r1/REJECTED.md`: capture-only missing native loop flags stopped the run
  instead of wrapping; renderer counters were missing. Original frames/report retained.
- `render-r2/REJECTED.md`: first-action ownership delay and capture timing mismatch.
  Original frames, report and MP4 retained; they are not the accepted flow evidence.
- `retarget-final/motion-retarget.json`: the first derivative run rejected the old
  direct target-hash equality. Fixed by explicit proof binding, preserving the bake
  source and tolerances rather than overwriting provenance.
- Experimental TPS run still reaches **221.906 mm simultaneous sole clearance**,
  with both feet above 15 mm in **24/51 samples**. No horizontal foot locking or
  gameplay-speed calibration has been accepted; native lower-body clips remain active.
- Next animation owner: author draw/raise/release anticipation compatible with the
  firing gameplay contract, inspect hand/string contact throughout actions, and verify
  translated locomotion against ground distance before promoting a full-body candidate.
- Next material/world owner: publish corrected-surface images and immutable structural
  proof. Root owns evidence archive, integration, roadmap status and release decisions.
