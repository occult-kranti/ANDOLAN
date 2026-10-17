# Independent face-shading ablation review

All four original frames in `../capture-face-ablation-r1/` were individually
opened by AI reviewer `/root/visual_art_review`. Their hashes match the
completed capture report and archive; the report records identical camera and
164-bone pose for the four controls, unchanged sources, exit 0 and no warnings.
Exact input identity and control values are in `FACE_ABLATION_inputs.json`.

| Sole changed factor | Visible result |
| --- | --- |
| Baseline | Broad triangular dark patches cross the cheek and neck. Dense stippling appears on the side scalp below the crown. |
| Sun shadows disabled | The broad cheek/neck triangles and scalp stippling largely disappear; the facial surface reads smoothly. Useful architectural and ground shadows also disappear. |
| Skin normal maps disabled | The broad triangles and scalp stippling remain. This does not support a normal-map-only repair of this defect. |
| SSAO disabled | The broad triangles and scalp stippling remain. This does not support an SSAO-only repair of this defect. |

**Diagnosis: the observed defect depends on the sun-shadow rendering path in
this controlled view.** This supports testing a targeted shadow bias correction
with shadows still enabled. It does not establish one universal bias value or
make every skin/material issue a shadow bug. The preceding static normal/map
inspection in `face-diagnosis/` remains valid within its narrower scope.

Do not promote the shadow-off diagnostic. It removes useful building/ground
structure and cannot satisfy contact-shadow quality. The next correction must
improve the side face while retaining believable foot, ornament and building
contact in gameplay views; excessive detached shadows or light leaking are
rejection conditions. The visible simple facial forms, groom, eye/lip detail
and broader material richness remain independent art tasks.

Capture report:
`ebc38d66277b2e20af5a64530c43626cfd1fbb270ff53907bad1d0626b1b2b25`.
No geometry was modified by this review. This is AI pixel inspection, not human
art acceptance, continuous motion review or physical-GPU performance evidence.
