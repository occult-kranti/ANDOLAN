# Isolated landing successor — eligible for matched rendering, not promoted

The candidate addresses the visible upward correction retained in the actual `8c377` landing take. Canonical `rama_motion.gd` remains `8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8`. The isolated successor is `5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5`. No player, capsule, ability, HUD, hero asset, socket, fixed plant anchor or shared runtime source changed.

The unchanged strict comparator returns **26/27**, retaining the inherited 60 Hz unplanted movement-step failure. This is numerical improvement and permission to examine matched images, not smoothness acceptance. The earlier actual 119db→8c377 packet, its 25/27 result and the visible first-ground correction remain immutable in [W5-actual-motion-r1](../W5-actual-motion-r1/REVIEW.md).

## Mechanism and limits

The candidate measures nearby flat support during the player's existing physics update. After a real grounded support observation, a descending ground-traversal actor may use a fresh ray under its current sampled foot position. The existing four-segment leg solver supplies only vertical clearance before contact. It retains the existing 1 mm correction trigger and 80 mm bound. There is no assumed world-zero plane or new server dependency.

Sampling/blending was mechanically extracted into `_motion_pose()`; its existing statements are byte-identical to the original extraction proof. Physics query and modifier use that same pure sample. Fixed ancestor chains are built once from the actual 164-bone rig. Querying does not advance phase, transition, aim, action or skeleton state. Subsequent correction requires the actual final foot footprint to agree within 10 µm of transform roundoff, unchanged rig and collider transforms, a live support owner, and the same enabled shape on collision layer 1.

Precontact prediction is deliberately limited to one `BoxShape3D` or `WorldBoundaryShape3D` per hit shape owner. Shape identity, index, local transform and exact box dimensions/plane data must remain unchanged. Complex shapes retain the previous contact path without anticipation. No per-frame scene search, arbitrary concave-shape copy, second bone writer or signal connection churn was added. Work remains bounded to the imported rig and two support queries; this is not a device-performance measurement.

Rise, flight, grapple, death, active Measured Step, no-world/off-tree, fresh misses, slopes, out-of-range support and stale ownership cannot apply the new clearance. Flight/grapple invalidate support history; reset/cancel clears all cached hits, and any subsequent use requires a new physics query. Fixed world plant targets are never relocated.

## Final source-bound checks

[final-native-verification.json](final-native-verification.json) binds the executed receipts and clean logs. These are headless tests on actual imported resources, not raster or human-feel evidence. Short processes use CPU4 affinity and LP/OMP/BLAS1; the Godot worker pool is not capped.

| Check | Final result |
| --- | --- |
| Actual-rig component boundary/ownership adversaries | 30/30 |
| Existing unchanged transition guard | 57/57 |
| Existing native scene fixture at 30/60/120 Hz | 11/11 at each rate |
| Original 27-predicate differential comparator against fresh 119db reference traces | 26/27; one retained failure |
| Public pause/resume during actual airborne descent | 4/4 baseline and 4/4 successor |
| Forty consecutive native 120 Hz landing callbacks | 6/6 |
| Fresh 8c377→successor landing control comparison | 35/35 |

The strict comparison keeps roots, velocities, ability/army reports and events, action/transition clocks, locks, plant targets, weapon sockets and all nonleg global poses exact at every rate. Public cancel and protected Measured Step full poses are exact. All targeted grounded soles improve to the unchanged −5 mm gate; no phase has a deeper minimum than the reference. The fresh 119db references each retain their expected four contact failures (7/11).

The remaining strict failure is unchanged: at 60 Hz, reset-forward peak ankle movement is 178.082928→178.311190 mm (+0.228262), and reset-left is 183.105926→183.324965 mm (+0.219039). These are unplanted movement steps. Neither the predicate nor its tolerance was relaxed. See [strict-comparison-r2.json](strict-comparison-r2.json), which retains contact coverage and boolean lock counts separately for every phase/rate.

In the fresh headless 8c377→5023 landing comparison, maximum adjacent ankle movement falls from **7.323952 to 0.922286 mm**. Minimum sampled sole distance improves from **−6.636322 to −0.326224 mm**; grounded minimum improves from +0.016164 to +0.315021 mm. Both tapes have 32 locked side-samples and 62 grounded side-samples within ±5 mm. Small negative residuals remain explicit; this is not proof of perfect nonpenetration. The targeted 120 Hz moving-reset-back trace reaches −0.133658 mm. See [headless-landing-comparison-r2.json](headless-landing-comparison-r2.json).

The pause witness uses the courtyard's public pause API during native descent, holds the complete 164-bone pose/root/anchors/authority over 12 process frames, then resumes by exactly one 1/120 s physics delta. Headless render counters are zero. The headless landing's frame/counter indices are not substituted for the previously rendered first-ground frame007→008 / physics46→47.

## Failed attempts and independent challenge

All meaningful failures and complete compressed traces are retained. [large-json-storage.json](large-json-storage.json) maps large original JSON names to deterministic gzip files, preserving their exact uncompressed hashes and sizes. Scratch originals remain until the remote checkpoint is verified; no pose, assertion or receipt bytes are discarded.

- `d1f54` failed stale teleport and the narrow-pad/final-foot-footprint adversary (16/18). Its cached prior-foot hit could raise a deliberately moved, unsupported final foot. The component injects that pose boundary; it does not claim the recorded authored clip executed it.
- `457d95` fixed those two boundaries (18/18). `57d0098c` added pure current-pose querying and collider ownership, passing21/21 and the first26/27 comparison.
- Independent W1 source review then identified changing support geometry without moving its collider. `57d0098c` failed all four new actual-rig cases: collision-layer exclusion, disabled shape, removed shape and changed dimensions (21/25). Original sources/reports remain pinned.
- `5023b301` invalidates those cases and child-shape movement. The first new plane-positive setup returned a real ray miss (29/30). A diagnostic preserved that missing premise. Waiting for one complete physics registration step after replacing the fixture shape produced actual plane and convex hits; the plane is admitted and the unsupported convex is rejected. No runtime threshold changed.
- The earlier missing guard-witness dependency and genuine guard/reference scheduling overlap remain in [sequencing-correction.json](sequencing-correction.json); those runs are excluded from the final serial gate. The later delayed W4 scheduling message did not establish overlap: retained completion/start bounds are separated by over42 seconds, recorded in [registration-and-scheduling-notes.json](registration-and-scheduling-notes.json).

[independent-source-review.json](independent-source-review.json) records W1's bounded read-only final review: no further blocking source issue found; no independent engine rerun or visual acceptance was claimed.

## Exact next capture

[render-preparation.json](render-preparation.json) verifies the new child contains the same 1,010 source/cache files as the previous actual8c377 branch, with **only `scripts/rama_motion.gd` changed** (and its declared snapshot marker). Every prior capture source pin was checked against that reused baseline. The child is `/tmp/yuga-s3-landing-successor-render-r1/candidate/project`; the immutable pair file is pinned by [render-pair.json](render-pair.json). No imported resources were regenerated. The new render marker recomputes its source byte total before use; the prior metadata is retained in `before-byte-total-correction`. [headless-snapshot-byte-audit.json](headless-snapshot-byte-audit.json) separately records inherited descriptive byte-total mismatches in historical headless markers without rewriting consumed identities; their exact file inventories remain authoritative.

Run only the successor40-frame120physics/120capture landing and120-frame60physics/30capture full-body takes. Reuse the archived8c377 actual candidate as baseline. [ready-render-commands.txt](ready-render-commands.txt) and [render-inputs.json](render-inputs.json) specify the exact unmodified `dce0422d` engine, Forward+,1280×960, old common FX, unchanged camera/input helper, and fresh identical Godot/Mesa cache copies. Prior observed costs were about110 s and210 s; existing600/900 s watchdogs remain. The stage preparation observed about9.1 GB free in `/tmp`; the runner enforces the existing3 GiB floor plus512 MiB start allowance. Estimated additional outputs and private cache copies are under512 MiB for the two runs, excluding this already-created source child.

**No successor raster has run at this source seal.** Root/W1 owns the heavy queue. Normal-cadence lossless originals and derived videos still need independent visual review. The full helper contains only two walk samples and reset-cleared movement; it does not establish sustained walking, a natural run-stop, turns, cast/cancel/pause presentation, earliest drawable title acquisition, physical-GPU performance or player feel. Any later integration of the latest UI/FX/art is a distinct source scope.
