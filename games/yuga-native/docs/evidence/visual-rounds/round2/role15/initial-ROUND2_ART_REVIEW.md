# R2-15 independent art direction review

**Current verdict: hold runtime promotion; bounded diagnostic findings accepted.** This checkpoint reviews the available original baseline and four single-variable diagnostics. It does not accept an unseen form candidate or a combined lighting/form result. Round 2 is not visually complete at this checkpoint.

Product: YUGA native. Source commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`; branch `game/yuga-native-production`. Reviewer edits are confined to this `role15` directory. No runtime source, asset, import, render, commit or release was changed by this reviewer.

## Actual visual inputs

I individually inspected the 12 available baseline PNG originals at their original 1280 × 960 resolution through `view_image`: all ten courtyard views (front, both three-quarter views, profile and ordinary rear gameplay, each day/night), plus stone three-quarter-left day/night. I then individually inspected the courtyard three-quarter-left daylight originals for roughness mips, SSS off, directional angular distance zero and TAA on. `reviewed-inputs.json` records exact paths, hashes, frame identities, capture hashes and control comparisons. No composite, author report or pixel-difference statistic substitutes for these direct inspections.

The two foliage baselines, final candidate 14-view set, 36 adjacent frames per source, five action poses and ordinary-speed sequence remain outside this checkpoint. The final form must be corrected r6 near GLB `140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a`; the rejected r5 hash `2dbd60…` is not acceptable by inheritance. The role08 candidate manifest and role14 handoff still reference r5 when read for this checkpoint; their old counts and LOD hashes cannot bind r6 without an updated receipt.

## Per-element visual verdict

| Element | Direct observation | Disposition and gate |
| --- | --- | --- |
| Residual stippling | Courtyard front has fine forehead dots. Left three-quarter day/night has a dense dark dotted band behind the ear, beneath the earring and along the hair/neck boundary. Hair crown and floor also show patterned noise. | Baseline defect confirmed. The mechanism is not inferred solely from appearance. A fix must reduce this defect in matched portraits and remain stable in adjacent frames. |
| Roughness mips | The actual single-variable original retains the ear/neck band and forehead dots; palette and gross facial silhouette remain recognizable. | Reject as a demonstrated stippling fix. Preserve as a negative diagnostic. No new final material treatment is accepted. |
| SSS disabled | The same conspicuous ear/neck band remains. No gross bleaching or new edge halo is apparent in this single original. | Reject as a demonstrated stippling fix. This image cannot justify removing SSS from the final skin. |
| TAA enabled | Forehead/crown and distant edges are smoother, while the ear/neck dotted band and broad cheek shadow remain. | Reject as the demonstrated stippling solution. Motion blur/history behavior is unreviewed; no general TAA quality judgment follows from one still. |
| Directional angular distance zero | Most of the conspicuous ear/neck band disappears. The nose projection and lip edge read more clearly. The broad cheek shadow remains, and floor/architectural and neck shadow edges become hard. | Accept the isolated visual benefit as a diagnostic. Hold runtime promotion until the hard-shadow tradeoff passes day/night, both close angles, Confluence contexts, feet/jewelry/architecture contacts and moving camera/caster review. Attribute this benefit to lighting only. |
| Principal face forms | Baseline brows and eye openings are readable, but upper orbital folds look inflated; cheek-to-nose and mouth-to-chin transitions remain shallow. The profile has a simple, rounded transition around the lips/chin. | Form improvement pending actual corrected r6 form-only images. A 1.562 mm maximum edit is a source fact, not visible evidence of stronger anatomy. Require an identifiable improvement in at least the targeted orbital/malar/lip-chin areas without worsening another view. |
| Skin/material response | Warm skin, muted lips, indigo costume and gold/blue ornaments retain their identity. In these close views the skin remains comparatively uniform and the dark cheek patch suppresses shape. Stone views are darker and flatter than the courtyard. | Existing material identity retained in inspected diagnostics, with finish quality still limited. Do not credit unchanged material to a form or light improvement, or brighten the face simply to hide forms. |
| Eyes and expression | Open eyes are visible in baseline stills; no transition was inspected at this checkpoint. Existing numeric evidence retains two open-cornea failures. | Deformation visual acceptance pending. Require full closure/reopening, partial lids and mouth/skin continuity in each adjacent raw frame. Source attachment checks do not close this gate. |
| Neck/jewelry contacts | The inspected baseline necklace/earring silhouettes remain distinct; the zero-angular image makes neck shadow edges sharper. Static portraits cannot establish moving contacts. | Pending candidate contacts and motion. Reject detached shadows, neck seams, lip separation or visibly jumping attachments. |
| Gameplay readability | Day/night rear courtyard views preserve hero costume, limbs, bow, feet, floor separation and turquoise targets. The face is turned away. | Baseline rear silhouette accepted within those two static views. Frontal gameplay face readability and live/crowded action clarity remain unproven. |
| Hair and costume | The close shots retain heavy solid hair strips, crown/groom gaps and a glossy indigo treatment. | Existing limitations, outside this face-form slice. Preserve them as next defects; they prevent a claim of finished character art. |

## Source evidence and its boundaries

The R2-10 report independently accepts corrected r6 for its 17/17 source/CPU checks, including the original fixed 288-vertex ring and sampled face/body/lip attachment witnesses through 37 baseline runtime poses. Four deliberately broken controls were detected. I reviewed that report; I did not rerun its test suite. Its candidate-import and continuous-pixel gates remain separate. The pre-existing source face validator remains 17/19 because one open-cornea point per eye is obstructed. That result is not an overall pass.

R2-09's material source/resource work and R2-12's context checks support source preservation and matched controls. They do not approve unseen r6 pixels. R2-14's r5 integration evidence must be refreshed for r6, including compatible mid/far geometry. R2-13's actual candidate cost/lifecycle report and updated R2-05 candidate-import evidence must be attached before a runtime recommendation.

The independent local audit in `audit_inputs.py` checks each viewed original against its capture SHA-256, native size and source-unchanged receipt. It compares the paired camera, viewport, pose, player transform/yaw, face, motion and LOD controls, plus all common light fields. Baseline courtyard metadata predates an explicit angular-distance field; its pinned lighting source uses 0.7. The zero-angular diagnostic actually records 0.0. The inherited diagnostic overlay text saying “not rendered” is stale; its complete capture and original PNG prove the diagnostic rendered, while acceptance remains this review's separate judgment.

## Promotion gates

1. Bind corrected r6 near/mid/far imports and source receipts. Preserve the rejected r5 fixed-ring failure and the two pre-existing open-cornea failures.
2. Inspect the three matched form-only previews before combining lighting. Record exactly which principal form improves and any visible cost. If the difference is too weak to support the stated benefit, keep it staged rather than calling numerical safety an art gain.
3. Inspect every final 14-view original, all 36 adjacent raw frames per source and the ordinary-speed sequence, plus all five action poses. Confirm actual blink/reopen, Kodanda release and Piercing cancellation from the recorded event evidence; pose-only samples do not close release/impact/expiry review.
4. If zero-angular lighting is included, retain its explicit identity and review the harder shadows in every relevant context and contact. Form-only and lighting-only findings must remain distinguishable from the combined result.
5. Attach updated independent material, motion, action, context and resource/import outcomes for the exact final source. Leave unsupported camera/cascade, frontal gameplay, extreme aim/independent-side blink, physical-GPU and crowded-fight gates open.

Next owner: R2-06 supplies original captures; R2-15 resumes visual review as they arrive; root owns any bounded promotion. A successful bounded source/image improvement would still leave the broader production-art target open. No AAA/commercial parity claim is made.
