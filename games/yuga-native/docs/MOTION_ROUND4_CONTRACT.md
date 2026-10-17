# Round 4 continuous movement contract

The movement round follows the accepted face/groom/cloth source. Independent source study can run earlier, but final regression and rendered acceptance must use the integrated asset. The current controller and rejected prototypes are preserved in `evidence/visual-campaign/motion-reversal-review/`.

## Observable target

Reduce visible start/stop/reversal and support-release discontinuities without changing character movement, action timing, damage or input. Compare the same actual rig at 30/60/120Hz with stationary aim, gradual steering, ordinary 38m/s² acceleration, abrupt adversarial reversal, strafe/backpedal, jump/land, action cancel, reset, pause and a bounded hitch. Source numerical joint steps support analysis; skinned contact and continuous native images are required.

The current adversarial 120Hz repeated-direction maximum joint-origin step is 912.671mm; the ordinary acceleration-law fixture is 161.919mm. These are fixture-specific defect measurements, not pass thresholds. Previous nearest-reachable projection worsened the ordinary case to 265.532mm and moved a stress contact anchor 46.299mm in one frame. Keep that candidate rejected.

## Implementation decision to investigate

Current `_apply_contact` switches stance correction off instantly, and it relocates a plant target after a .36m discrepancy. Current directional leg placement also uses immediate `atan2` heading. Investigate continuity at these exact boundaries: preserve fixed world anchors while planted, explicitly release an unreachable plant, and blend the released leg toward the moving swing trajectory with bounded position/velocity continuity. A limited heading response alone already failed; combine only if the new measured comparison justifies it.

A released foot is not planted. Report its contact state honestly. Do not move a target every frame and call the resulting tiny solver error no-slip contact. Do not hide a bad result by slowing the authoritative character, deleting a stress fixture, changing its expected values or increasing permitted thresholds. Any native IK comparator must honor the four existing leg segments and single skeleton writer.

## Required evidence

1. Exact controller, rig, clip-library and fixture hashes for baseline and candidate.
2. Actual executed numerical results, all failed candidates retained, ordinary and adversarial comparisons separate.
3. Joint-origin and actual skinned-vertex continuity, planted anchor drift, release state, floor penetration, finger/string contact and event timing.
4. An uninterrupted source-bound original movement sequence including the problematic transition; include clocks, camera and input tape. Fixed recording rate is not achieved hardware FPS.
5. Independent motion and art dispositions before default promotion, with unresolved defects explicitly retained.
