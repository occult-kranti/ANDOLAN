# Rama visual campaign: resume here

Review cut: 17 October 2026. Source base
`38d11148fe69b184e981164c8a71387c91dc64c5`, branch
`game/yuga-native-production`. The repository
[publication receipt](../../../docs/evidence/visual-campaign-publication.json)
records the exact pushed source and CI status when verified. This handoff is
not a new downloadable release receipt.

The user requested **ten rounds of fifteen specialist assignments**. All fifteen
initial roles have returned artifacts, with several corrective follow-ups,
rotating through six worker slots. **135 future assignments remain planned.**
Schema 2 of [VISUAL_CAMPAIGN.json](VISUAL_CAMPAIGN.json) separates ten workstreams
from ten complete fifteen-role cycles. R1, R2 and R3 are capture/correction
iterations inside Round 1, not three completed squad rounds. Round 1 is complete as a bounded implementation/review cycle, with
**LIMITED** art acceptance. Nine rounds remain planned. Deadlock-level art
has not been achieved.

## Changed components and owners

| Area | Files / owner | Current result |
| --- | --- | --- |
| Hero materials | `scripts/rama_surface_finish.gd`, `assets/materials/rama-finish/`; surface artist and material reviewer | Five roughness maps reduce broad glare while retaining indigo/gold identity. Three ownership/lifetime defects fixed. [Independent review](evidence/visual-campaign/material-review/REVIEW.md). |
| District | `scripts/hero_district_detail.gd`; district artist and environment reviewer | Eight batches, 43,008 triangles: arches, cupolas, plants, relief and supporting terrace. Packed roughness GREEN channel and inward faces corrected. Four bounded warm practicals added. [Review](evidence/visual-campaign/environment-review/REVIEW.md). |
| Atmosphere | `scripts/hero_atmosphere.gd`; lighting artist | Reversible day/night settings, corrected sky seam and lifecycle checks. SSAO/glow remain real renderer work with unmeasured GPU cost. |
| Five abilities | `scripts/rama_ability_effects.gd`, `shaders/rama_ability_calligraphy.gdshader`; ability artist and effect reviewer | Solar strokes, arrow vanes, lotus ward, traversed-position echoes and contact accents. Invalid duplicate-release/pre-release-impact events rejected. Guardian now has a contrasting perimeter. [Review](evidence/visual-campaign/effect-review/REVIEW.md). |
| Locomotion | `scripts/rama_motion.gd`; animator and motion reviewer | Threshold hysteresis and braking contact corrected. Retain source `4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1`. All later reversal prototypes were rejected. [Motion evidence](evidence/visual-campaign/motion-review/REVIEW.md), [rejected prototypes](evidence/visual-campaign/motion-reversal-review/REVIEW.md). |
| Optional hair | `scripts/rama_character_accents.gd`; character-detail artist | Four temple wisps, 800 triangles: **REJECTED after matched close-up review**, remain unbound in ordinary play. Preserve the original groom until a better candidate is reviewed. |
| Capture / integration | `tools/visual-campaign/`, `player.gd`, `courtyard.gd`, `tools/run-visual-checks.py`; capture engineer, root, build engineer and independent art reviewer | Frozen source, original framebuffers, exact camera/player comparisons. Native content revision 5 covers fifteen gameplay source pins, **not the entire visual catalog**. |
| Reuse / performance | Reuse researcher and performance engineer | [Source/license findings](research/VISUAL_REUSE_RESOURCES.md), [resource census](evidence/visual-campaign/performance/REVIEW.md). No commercial client or asset recovery. |

The base near-hero GLB remains
`de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`:
geometry, UVs, skin and rig are unchanged. It has one 164-bone skeleton and nine
embedded animations; the 23-state runtime motion library is separate. New
material maps and generated district/effect geometry change the rendered scene.

Both `production_lighting.gd` and `world_lighting.gd` now use shadow depth bias
`0.2` instead of `0.025`, retaining normal bias `0.35`, sun shadows, cascades,
distances and caster policy. This is an actual rendered correction to the
large facial self-shadow patches, not a geometry replacement.

## Actual-image decisions

| Capture | Completed evidence / decision |
| --- | --- |
| Baseline R1 | Eight raw 1280 × 960 views, 254 source pins, exit 0 and no producer warnings. [Receipt](evidence/visual-campaign/capture-baseline-r1/run.json). |
| Candidate R1 | Eight raw views, 266 source pins. Composition/material improvements retained, but floating bases and sky seam rejected. [Original rejection](evidence/visual-campaign/art-review/R1_REVIEW.md). |
| Candidate R2 | **All 33 originals individually reviewed**: nine standard views, twenty ability milestones and four hair-comparison frames. Grounding and horizon corrections succeed; hair accent rejected. Overall hero/world art remains LIMITED. [Completed review](evidence/visual-campaign/art-review/R2_REVIEW.md), [producer receipt](evidence/visual-campaign/capture-candidate-r2/run.json). |
| Candidate R3 | **All 17 originals complete and reviewed**: nine standard views plus Guardian day/night phases, 268 source pins, exit 0 and no warnings. Warm practical pools and contrasting Guardian perimeter accepted **only for these inspected views**. [Review](evidence/visual-campaign/art-review/R3_REVIEW.md), [receipt](evidence/visual-campaign/capture-candidate-r3/run.json). Capture-report SHA `eb1ac396bc4f1bf1efe5a5a60d1399a5c4c2cb76f6d1c435676f813741cdba7b`. |

The R2 `impact` filename does not always mean target damage: Kodanda and Piercing
Dawn contact a wall with no receiver receipts in those takes. Dawn Volley shows
one confirmed 82-damage hit. Continuous films require their own receiver and
adjacent-frame evidence; still phases do not establish smoothness or game feel.

Closeups revealed large triangular skin shading patches. The
[source-only diagnosis](evidence/visual-campaign/character-surface-diagnosis/REPORT.md)
finds smooth stored normals, small normal-map perturbation and no large observed
source-normal seam. Four subsequent controlled ablations identify directional
self-shadowing as the major contributor. Two bounded bias sweeps and twelve
eligible courtyard/Confluence day/night confirmation originals support the
[accepted correction](evidence/visual-campaign/art-review/SHADOW_BIAS_REVIEW.md).
Fine scalp/ear/chest stippling and moving-camera/cascade contact remain open.
Two incorrectly framed world portrait runs are preserved as failed harness
evidence; they do not support acceptance. The [final-source action film](evidence/visual-campaign/capture-action-r1/rama-five-abilities.mp4)
contains 363 sequential frames from five separate real ability takes; encoding
and decoding succeeded. The [independent final review](evidence/visual-campaign/art-review/FILM_REVIEW.md)
inspected all 25 original stills, 31 selected sequence frames and three ordinary
final-source title/day/night anchors. These support bounded action direction,
receiver feedback, Guardian expiry and displayed hit/defeat/respawn state.
Live soldiers remain visibly blocklike; face, groom, cloth, rapid direction
changes and world repetition still need substantial art work.

The film is silent and 12.1 seconds at a fixed 30 Hz capture clock with actual
60 Hz physics. It has deliberate cuts between the five takes and uses staged
live receivers through the real cast API. Full temporal playback, human input,
listening and performance are not accepted. All 363 raw sequence PNGs remain
local-only; 31 inspected samples are also archived with the review. The compact
MP4 and 25 original stills are committed evidence. The film source manifest
compares 506 files; 505 are shared with final numerical verification, which
also pins export configuration while the film also pins the authoring map.
Three invoked film helpers are verified separately.

All current captures use Forward+ on CPU llvmpipe. A fixed recording clock is
not achieved hardware FPS. R3 stills do not close moving-camera light leaks,
crowded-fight readability, final face/groom/fabric, uniform paving or repeated
skyline defects. These are source-bound AI reviews, not human art/feel approval
or a direct commercial-game comparison.

## Final known verification

[The archived final verification](evidence/visual-campaign/final-verification-r4/REVIEW.md)
records three sequential runs on the same **506 runtime files**, exact before
and after:

| Catalog | Actual outcome |
| --- | --- |
| Visual contracts | **727 assertions**, twelve suites, all exits 0 |
| Existing quality catalog | **777 assertions plus fifteen reproducible PCM files**, sixteen suites, all exits 0 |
| Current resource/effect census | **51 assertions**, five scene lifecycles and five accepted ability fixtures, exit 0 |
| Additional world presentation / lighting | **32 and 30 assertions**, both exits 0 |

The independent verifier checks assertion outcomes, duplicate/nonfinite JSON,
source/report/log hashes, native exits and 48 logs: no engine errors or warnings.
Do not add overlapping catalog totals as independent whole-game coverage.
These runs qualify the pinned source and numerical behavior; they do not
qualify pixels, listening, Windows, native online play or physical-GPU timing.

The actual scene census is 345 nodes, 63 mesh instances, 955,540 resident
triangles, 427,618 triangles visible by scene-tree flags, eleven lights,
nineteen collision objects and one 164-bone skeleton. Relative to baseline,
the district adds eight meshes/materials, 43,008 triangles, four lights and
761,525 texture-file bytes. Scene-tree visibility is not renderer culling;
resource stability is not proof against every leak. Saturated effect fixtures
are bounded tests, not accepted simultaneous gameplay.

The pre-existing rapid-reversal issue remains open. The stress fixture measures
a 0.91267 m joint-origin step at 120 Hz. A separate fixture using the player's
acceleration law also rejects the proposed correction because it worsens the
ordinary case. Numerical contact alone does not justify moving contact anchors
or promoting a visibly discontinuous transition.

From the repository root:

```sh
python3 games/yuga-native/docs/evidence/visual-campaign/final-verification-r4/verify_receipts.py
/workspace/tooling/yuga-native-python/bin/python \
  games/yuga-native/tools/run-visual-checks.py \
  --python /workspace/tooling/yuga-native-python/bin/python \
  --engine godot --output /absolute/fresh/visual-checks
```

Use `--list` to select affected suites after a change. Root owns source freezes
and import/render scheduling; only the capture engineer runs heavy rendering.
Preserve failed candidates and use fresh outputs. A partial report marked
success cannot override a logged engine error.

## Next five visual tasks

The [fifteen Round 2 assignment contracts](VISUAL_ROUND2_TASKS.json) specify
exclusive artifacts, dependencies and rejection gates. They are planned work;
creating that plan does not count as executing another round.

1. **Review the remaining skin and shadow defects in motion.** The large-patch
   correction is accepted in fixed views. Resolve residual stippling and test
   moving-camera/cascade contact without sacrificing silhouettes or costume detail.
2. **Author principal hero forms.** Improve eyelids, lip/chin planes, expression,
   large hair masses and fabric thickness/folds. Test front, three-quarter,
   orbit and deformation; the rejected wisps do not solve the groom.
3. **Finish continuous motion and combat.** Review the completed film and retained contact traces, then fix
   direction changes and support release while preserving contacts and event
   timing. Include start/stop, braking, shooting, cancellation and all five skills.
4. **Develop coherent world and soldier art.** Replace visibly blocklike live
   soldiers with authored, rigged forms. Replace repeated skyline/roof forms,
   calibrate paving/material scale and add authored edge/wear variation while
   preserving clear approach routes and target silhouettes.
5. **Qualify the complete visual slice.** Refine ability glyphs and interaction
   states across supported screens; inspect effect overlap/reduced options;
   profile actual GPU frame time/memory, then qualify the native package.

Source push and exact-commit CI are recorded in the linked publication receipt.
The first cycle's completed review is not acceptance of the complete campaign.
The previous downloadable preview retains its own identity until a new package
is actually qualified and published. Native play remains offline; production
online matches, the full roster, human art/feel/listening, Windows and hardware
qualification remain open. The ten-round campaign continues from these defects.
