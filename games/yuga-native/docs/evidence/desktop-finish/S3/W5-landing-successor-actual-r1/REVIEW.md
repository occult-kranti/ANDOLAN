# Actual landing successor — bounded acceptance

The isolated `5023b301` successor materially reduces the visible first-contact upward foot correction in the matched close landing recording. The ordinary full-body recording introduces no new whole-body shift in the inspected poses. Root reviewed the source and eight original images and accepted this bounded correction for canonical promotion **after this receipt is sealed**. This report does not claim general smoothness or full-speed human feel. Canonical motion was still `8c377` at the evidence seal; copying the accepted source is a separate integration action.

The source is [candidate/rama_motion.gd](../W5-landing-successor-r1/candidate/rama_motion.gd), SHA256 `5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5`. Its [source/headless report](../W5-landing-successor-r1/REVIEW.md), failed witnesses and unchanged **26/27** strict result remain immutable. The original [119db→8c377 actual comparison](../W5-actual-motion-r1/REVIEW.md) and its **25/27** result also remain unchanged.

## Actual recordings and control

This packet adds exactly **160 original 1280×960 PNGs**, two complete lossless gzip captures and two derived normal-cadence MP4s. The baseline is the exact archived `8c377` candidate from the original comparison; it was neither rendered again nor relabelled. Both successor processes exited0 with clean engine logs:

| Take | Physics / capture cadence | Originals | Native gates | Actual elapsed |
| --- | --- | --- | --- | --- |
| [Close landing](landing120/archive.json) | 120 /120 Hz | 40 | 6/6 | 107.733 s |
| [Full body](full/archive.json) | 60 /30 Hz | 120 | 8/8 | 217.563 s |

Both use unmodified Godot4.6.3 template-debug SHA `dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f`, Forward+, llvmpipeLLVM19.1.7, the same separately copied Godot/Mesa seeds and CPU0,1 with LP2. The engine worker pool is not capped. Sampling cadence is not measured wall-time frame rate or device performance. Original600/900-second watchdogs were retained.

The exact pair is `25fe7023971e9b07a8a2ac9f8769182cb92dc73469da81cc06d38e2b45bad8aa`; rendering inputs are `85a76c24c00be12e2bdd1b65c2123d2a8dd376566c07c5cd1cb9832a15c3c47f`. The [source preparation](../W5-landing-successor-r1/render-preparation.json) binds every common source/cache file. Only motion and its declared snapshot marker differ. This pair retains its old common FX, art and UI context; it is not evidence for later integrated changes.

[Landing](landing120-archive-comparison.json) and [full](full-archive-comparison.json) pass **42/42 control predicates each**. Actual physics/draw counters advance consecutively at the stated rates. Every camera, light, material, face, secondary state, LOD, root/capsule transform, velocity, authority/event/action clock, fixed world anchor and all126 nonleg global transforms match. The inherited field `foot_targets_rig` names world-space anchors. Repo-only replay repeats those same predicates; it is not another independent test count. [Archive verification](archive-verification.json) also checks all320 paired PNG identities, raw capture hashes, logs and videos without `/tmp` inputs.

## Recorded improvement and remaining residuals

[metric-summary.json](metric-summary.json), derived from the complete captures by [summarize.py](summarize.py), retains the measurements and their definitions.

| Close landing measurement | 8c377 baseline | 5023 successor |
| --- | ---: | ---: |
| Right ankle step007→008, physics46→47 | 7.323952 mm | 0.078929 mm |
| Same step, world Y | +7.323943 mm | +0.078134 mm |
| Same projected ankle movement | 6.484344 px | 0.071963 px |
| Largest adjacent ankle step over all40 frames | 7.323952 mm | 0.922376 mm |
| Lowest sampled sole, including airborne samples | −6.636312 mm | −0.326283 mm |
| Lowest grounded sole | +0.016164 mm | +0.315021 mm |

The successor's maximum occurs earlier at001→002, left foot, physics40→41, with0.908091 projected pixels. The small negative airborne residual remains; this is not perfect nonpenetration. Both takes retain64 grounded side-samples within the defined ±5 mm ray-plane band and30 boolean locked side-samples. These are different observations; neither alone proves planted support or absence of sliding. Both have zero grounded side-samples below−5 mm.

In the full-body take, entry frame000 minimum improves from−4.623290 to+0.571527 mm. Only frames000–003 have any global-pose difference; all164 global transforms are exactly equal from004 through119, including the later jump and landing. Grounded minimum remains+0.490857 mm, with190 grounded side-samples,140 within the ±5 mm band and102 boolean locked side-samples in both branches. The4.534 m peak world step at044→045 is the identical public reset/teleport; it is not a smoothness score.

The unchanged strict source comparison still fails one of27 predicates: the60 Hz unplanted reset-forward step increases by0.228262 mm and reset-left by0.219039 mm against119db. No tolerance was relaxed. The original26/27 report and actual30/60/120 traces remain in the source packet.

## Direct visual review and limits

W5 directly opened **22 original images**: close001/002/007/008 and full000/001/018/047/094/095/119 in both branches. The close first-contact foot edge stays nearly level in the successor where the baseline distinctly lifts. The earlier001→002 correction is small in these adjacent originals, without a comparable visible jump. At ordinary framing, the inspected entry, movement, reset, jump landing and settled poses show no new gross torso/root/framing offset. The decorative rim is not the collision plane, and projected ankle coordinates are not image-edge tracking.

[Independent W1 review](../W1-landing-successor-sampled-review-r1/REVIEW.md) opened20 originals, verified320 image hashes and recorded the same bounded first-contact improvement. Root independently opened close007/008 and full094/095 in both branches. These overlapping review scopes are not summed as unique images. Neither reviewer claims full-speed human playback. Normal-speed videos are viewing aids: [new close](landing120/normal-speed.mp4), [baseline close](../W5-actual-motion-r1/landing120/candidate/normal-speed.mp4), [new full](full/normal-speed.mp4), [baseline full](../W5-actual-motion-r1/full/candidate/normal-speed.mp4). They use recorded cadence without interpolation; lossless originals remain authoritative.

This helper contains only two walk samples, run frames017–044, public reset045 clearing movement and release065 while already idle. It does not establish sustained walking, natural stopping, turns, strafe/backpedal continuity, cast/cancel/pause presentation, earliest drawable title acquisition, arbitrary mutable support geometry, physical-GPU performance or player feel. Those remain separate work. The accepted correction conservatively anticipates only fresh validated box/plane support; unsupported shapes keep the old contact path.

## Integration handoff

Root owns copying the exact accepted source. No player, ability, capsule, socket, hero asset, anchor or motion clock change is included. Existing functional checks need not be broadly repeated merely to copy unchanged bytes.

Two focused catalog additions protect the new behavior: `tests/desktop_landing_support_boundary_cases.gd` (30 checks,4,937,943-byte JSON) and `tests/desktop_landing_pause_cases.gd` (4 checks,92,649-byte JSON). Each accepts only `--report=...` and loads current canonical motion; register after promotion. Both inherit `tests/graphics_g2_support_cases.gd`. The boundary fixture never calls the inherited scratch-baseline path; the pause fixture overrides it with tracked `docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd`. Pin those dependencies and the actual imported resources. Both reports fit the existing8 MiB cap without dropping assertions or poses. Their sealed invocations/results and exact fixture hashes are in the source packet and [receipt.json](receipt.json).
