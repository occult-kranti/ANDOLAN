---
name: yuga-anatomy-review
description: Sculpt and review a YUGA hero by body region in Blender, from reference landmarks and mass studies to skinned details, close-ups and contact checks.
---

Use the [hero art skill](../yuga-hero-art/SKILL.md) for the shared rig, build, and export workflow. Start with the existing editable model and exact target illustration. Pin the source file, camera, intended action and quality budget. Separate material, outline, and deformation issues during review so the next edit has a specific cause to address.

## Plan the part studies

Spend the first pass on mass and negative space. Rotate forms on Practice Drawing This, sketch cranium, jaw, rib cage, pelvis and hand volumes from two angles, and read the weight line through the feet. Gesture studies guide the cape, tail or fabric arc before adding surface detail. Use the source in the browser for observation. A short practice pass can cover three minutes of rotated primitives, four minutes of skull and rib cage, four minutes of opposed thumb and folded fingers, and four minutes of load and gesture. Record the one observation that changes your sculpt. [Model index](https://practicedrawingthis.com/3d/) · [Source audit and exercises](../../../games/yuga-native/docs/research/hanuman-match-sources.md)

Sketch the shoulder block and gada cylinder from the matched camera and an oblique angle. Check where the main axes converge, where a circular cross-section projects to an ellipse, and which openings show the elbow, grip and tail. Reduce a full render to thumbnail size to check which masses still read before adding trim or court decoration. [Verified form and composition exercises](../../../games/yuga-native/docs/research/hanuman-match-sources.md#form-symmetry-and-composition-follow-up)

| Region | Inspect before adding detail | Evidence after the edit |
| --- | --- | --- |
| Eyes and brow | Orbit depth, brow ridge, upper and lower lid arcs, visible iris, eye line | Full shot and close eye crop with coherent iris direction, catchlight and continuous lid contact. Look from the other side to check recession. |
| Nose, mouth and jaw | Cheek mass, nostril placement, muzzle, closed lip corners, jaw hinge and bite line | Face crop under grazing and soft light. Check that the lips close with a tapered seam, nostrils read from three-quarter view, and the beard emerges from skin. |
| Scalp, ears and neck | Forehead angle, swept hair masses, ear position, sternocleidomastoid and clavicle | Compare silhouette, strand roots at hairline and sideburns, and ear attachment. Check head turn under the portrait and neutral lights. |
| Chest, back and pelvis | Rib cage, clavicle bridge, scapula, breathing room under costume, pelvis tilt | You should be able to trace shoulder to breastplate, upper back to waist, and waist through the garment in two views. Audit shoulder and hip crossing in motion before export. |
| Arms, hands and fingers | Separate upper-arm and forearm peaks, elbow plane, wrist angle, knuckle cascade, thumb opposition | Close view of dorsal and palm side. Compare the hand with the prop contact marker, then inspect normal grip, anticipation, release and recovery. |
| Legs, ankles and feet | Thigh to patella, shin to calf, Achilles transition, heel, toe box and weight-bearing edge | Both feet visible in the keyframe with measured paving clearance. Inspect cloth over knee bend and toes during stride and landing. |
| Tail and attachments | Swept curve, taper, root and tuft direction. Check the mass flow before adding hairs. | Continuous arc from behind the hip to the tuft. Inspect silhouette and clearance while standing, turning, striking and landing. |

## Check symmetry on the rest mesh

1. Establish the armature-local midline. Compare neutral front and back views of the skull, torso, palms and lower legs. Mark the structural pairs and any intended left and right differences in the visual brief.
2. For a bilateral correction, compare paired samples across local X before and after the edit. Use Sculpt Mirror for paired strokes or a Mirror modifier for a newly built paired piece. If using directional Mesh Symmetrize, test the operation on a duplicate because it copies the source side’s geometry and data. Review centerline continuity, normals, UVs and left and right skin assignments before adopting it. [Blender operator notes](../../../games/yuga-native/docs/research/hanuman-match-sources.md#form-symmetry-and-composition-follow-up)
3. Review gaze, hands, weapon contact, cloth, hair and tail in the actual pose once the symmetric masses hold. Use an alternate or profile camera to reveal side-specific tension and gaps. Keep exact rest bones, animation signatures and visible fitting as separate evidence.

## Run the reviews

1. Give each region one author and a peer. Record an exact view and the largest visible gap. Work in isolated modules with shared skin and bone names.
2. Apply one bounded sculpt, fitting or material correction. Reopen the file and inspect the actual result at the full-figure camera, a cropped close-up and an alternate angle. Sweep camera and lighting briefly to distinguish a shadow from a geometry defect.
3. Revise the failure that the view exposed. Save the chosen comparison and open issues. When a geometry change affects weight-bearing or an attachment, run the relevant contact test even when the intended change is cosmetic.
4. Before runtime promotion, review UV packing, tangent normals, shoulder/neck/hip deformation, foot and grip drift, cloth clearance, LOD continuity and the actual imported performance. Keep rig and action file contracts pinned and report any changed runtime assets. Texture and clip acceptance happens in the importer under test. [Engine handoff checks](../../../games/yuga-native/docs/research/hanuman-match-sources.md#engine-handoff-checks)

Use the smallest representative feedback artifact. A good still is evidence for likeness in its camera. Action playback, runtime budgets and the hidden side each need their own evidence. [Hanuman design and action timeline](../../../games/yuga-native/docs/HANUMAN_GAME_DESIGN.md) · [Blender armature manual](https://docs.blender.org/manual/en/4.3/animation/armatures/index.html)
