# Independent shadow-on correction review

AI reviewer `/root/visual_art_review` individually opened all eight originals
in `../capture-shadow-bias-r1/`: four bias configurations, each in the same
three-quarter face view and normal gameplay view. The capture preserves the
same rig pose and each camera, with shadows enabled throughout. File hashes,
control values and source identity are in `SHADOW_BIAS_R1_inputs.json`.

## First bounded sweep

| Depth / normal bias | Face observation | Contact/environment observation | Disposition |
| --- | --- | --- | --- |
| 0.025 / 0.35, baseline | Broad cheek/neck triangles and stippled scalp remain. | Hero and building shadows are present. | Known defect remains. |
| 0.1 / 0.35 | Cheek/neck patches reduce visibly, but residual angular shading and scalp stipple remain. | Hero shadow still joins the ground near the feet in this view; building shadows remain. | Partial improvement; does not close the face finding. |
| 0.025 / 1.0 | Larger angular temple/forehead changes remain noticeable; the skin is not clean. | Ground and structural shadows remain visible. | Reject as a completed correction. |
| 0.1 / 1.0 | A conspicuous diagonal forehead patch and residual side-face/scalp artifacts remain. | Ground and structural shadows remain visible. | Reject as a completed correction. |

None of these pairs provides the clean skin result seen in the diagnostic
shadow-off frame while maintaining shadows. No whole-scene shadow disabling is
approved. The fixed gameplay views show no wholesale loss of contact shadows,
but cannot exclude small gaps or moving-camera detachment at all positions.

The moderator requested one final bounded comparison: 0.1/2.0, 0.2/0.35 and
0.4/0.35. Its result will be recorded separately below; the failed or incomplete
first-sweep findings above remain preserved. If the follow-up does not provide
a defensible correction, retain the existing R3 source and the open defect.

Report: `222067b7ce74d6a745bef1b168dc326105ff1b4025cbf5952d8c3dfaee0abc5b`.
No runtime or asset edits were made by this reviewer. Final hero art, human
review, continuous contact and physical-GPU performance remain separate gates.

## Final bounded sweep

All six originals in `../capture-shadow-bias-r2/` were independently opened,
then hash-verified against the report/archive. `SHADOW_BIAS_R2_inputs.json`
records the exact controls and same-camera/pose checks.

| Depth / normal bias | Observation | Disposition |
| --- | --- | --- |
| 0.1 / 2.0 | Prominent diagonal forehead and cheek patches remain. | Reject as the correction. |
| 0.2 / 0.35 | Broad cheek, forehead and neck patches are clearly reduced. Stipple behind the ear/scalp remains. Hero, target and structural shadows still connect visually with their supporting surfaces in the inspected gameplay view. | Smallest tested setting with a credible large-patch improvement; conditionally support pending night/Confluence confirmation. |
| 0.4 / 0.35 | Skin is cleaner again, but its benefit over 0.2 is less decisive than the larger shadow shift it requires. | Do not select over the smaller 0.2 candidate on this evidence. |

No obvious gross foot-shadow detachment is visible in the selected 0.2 gameplay
frame. This is deliberately a limited finding; a fixed camera cannot rule out
detachment during movement, at other geometry or across shadow cascades.
The moderator is capturing courtyard night and Confluence day/night comparisons
before any promotion. Scalp/ear stippling and final facial artistry remain open.

## Final fixed-view confirmation

All 12 eligible originals were independently opened and verified against their
capture reports and archives. `SHADOW_CONFIRM_inputs.json` pins each file and
the equal-camera/equal-pose controls. Eligible series are courtyard night r1,
Confluence day r3 and Confluence night r3. Earlier Confluence day r1/r2 portrait
framing was incorrect and is excluded from this acceptance.

**Accept depth bias 0.2 with normal bias 0.35 as a bounded correction of the
major facial shadow patches. Sun shadows remain enabled.** The day world
portrait shows the clearest reduction across forehead, nose and cheek. Night
comparisons retain the improvement without a new broad angular face defect.
In each fixed gameplay view the hero and building shadows remain visibly
connected to the ground; no gross new foot-shadow detachment is apparent.

This does not close all shadow or skin work. Scalp/behind-ear stippling persists,
and the brighter Confluence portrait also exposes stippling around the ear and
chest. The simple facial forms and rope-like groom remain as previously noted.
Fixed views do not establish behavior while moving through shadow cascades or
near every wall. A final film of the accepted frozen runtime remains a separate
continuous-action review input. Overall production art remains LIMITED.

Capture reports:

- Courtyard night: `1eca1f930e99c88b13ab98fc93ac94cb61337b57b61502444c13ae55859e76c6`.
- Confluence day: `23125d9c4da45c9f8315f10dd73eb960d0ce84915f811fb113e418cffa6ede25`.
- Confluence night: `87bd32605c87c30a90dade80d1be1e071cdf6abfc6f9c18ed317d75c36de724c`.
