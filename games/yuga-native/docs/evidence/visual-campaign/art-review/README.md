# Independent visual review record

AI reviewer `/root/visual_art_review` inspected the original native-game
framebuffers named in the linked input ledgers. This folder records review
evidence, not a human play study or a commercial-game quality certification.
The moderator owns final acceptance and the production roadmap.

| Evidence | Decision |
| --- | --- |
| [R1 baseline/candidate](R1_REVIEW.md) | Preserve the failed backdrop-grounding and horizon findings. Reduced sash glare and distinct ability shape are limited improvements. |
| [R2 corrected candidate](R2_REVIEW.md) | Accept visible backdrop grounding. Reject the optional eyebrow-to-ear hair strands. Keep hero, environment and motion quality gates open. |
| [R3 light and Guardian boundary](R3_REVIEW.md) | Accept the restrained local diya pools and the more readable outer area-effect boundary in the inspected day/night views. |
| [Face source inspection](face-diagnosis/README.md) | The sampled source normals are smooth. A blanket mesh-smoothing change is unsupported. |
| [Controlled face ablation](FACE_ABLATION_REVIEW.md) | Sun-shadow removal isolates the major patch artifact; removing all scene shadows is not an accepted product fix. |
| [Shadow-on bias trials](SHADOW_BIAS_REVIEW.md) | The smaller effective candidate is depth bias 0.2 with normal bias 0.35. Final night/world confirmation is recorded separately; residual stippling remains open. |
| [Final action samples and ordinary anchors](FILM_REVIEW.md) | All 25 stills, 31 selected original sequence frames and three final anchors were reviewed. Direction, feedback and cleanup are readable in the controlled samples; full motion, soldier art and commercial-quality acceptance remain open. |

Each `*_inputs.json` pins the exact inspected inputs and their scope. Failed
trials remain retained rather than overwritten by later success. Fixed capture
time and a software Vulkan renderer do not establish physical-GPU performance.

## Highest-impact remaining art work

These are visible acceptance gates for subsequent work, not new claims of
completed design or a numerical art score.

| Area | Current visible gap | Evidence required to close it |
| --- | --- | --- |
| Face and skin | Simple eyelid/lip shapes, limited expression and residual scalp/ear stippling. | Matched original front, three-quarter and gameplay captures under day/night light show deliberate facial forms and clean shading; expression transitions retain those forms without eye/lip intersections. |
| Hair | Regular thick rope-like masses; the tested flyaways read as wires across the face. | Rooted, tapered strands integrate with the main groom in front/profile/three-quarter views, and contiguous moving frames show no isolated tips or face/ear crossings. The rejected candidate stays unbound until that evidence exists. |
| Cloth and costume | Strong color identity, but broad cloth surfaces and repeated trim still lack authored material variation. | Near and gameplay views distinguish cloth, metal, skin and hair under both lighting phases without restoring broad white sash glare or turning fine detail into flicker. |
| District | Repeated skyline, large uniform paving fields and repeated structural modules dominate. | Actual traversal views establish readable landmarks, believable joins and differentiated stone/metal/plaster surfaces while retaining clear combat paths and targets. Decorative density alone does not close this gate. |
| Lane soldiers | Simple block/cylinder forms, repeated silhouettes and sparse materials remain conspicuous in the actual action capture. | Authored unit silhouettes and weapon/body detail read at gameplay distance; moving formations show deliberate gait, attack, hit and defeat transitions without merging roles into identical figures. |
| Light and depth | Local title lighting improved; the wider environment still has weak spatial hierarchy. | Day/night traversal shows coherent local sources, readable target silhouettes and grounded characters without broad color wash, through-surface light or detached shadows. |
| Combat presentation | Single-action stills show distinguishable effects; crowded fights and uninterrupted feel are not established. | Source-bound continuous captures retain attack direction, receiver feedback, threat boundaries and HUD legibility through overlapping actions, movement and cleanup. Sampled stills alone cannot certify timing or feel. |
| UI journey | Desktop game captures are readable, with text-heavy ability slots and small world labels. | Actual launch, play, pause, settings, failure and recovery journeys remain legible at supported sizes, with keyboard/controller focus and state synchronization verified separately. |

The target remains an original high-quality game. No proprietary reference
footage was directly inspected by this reviewer, and no Deadlock, Overwatch or
Dota 2 parity claim follows from these captures.
