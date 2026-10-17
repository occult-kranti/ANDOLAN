# Rama skin shading diagnosis

The large triangular cheek, temple and neck patches are visible in the actual
R2 front and three-quarter baseline closeups. Both originals were individually
viewed, their hashes match the capture receipt, and both use near LOD 0 with
the optional wisps absent. [The source-pinned report](report.json) records the
images, GLB, texture measurements, reading scope and numerical method.

**The source does not support a simple flat-normal explanation.** Neither skin
primitive has any triangle with three identical corner normals at tolerance
`1e-6`. The body skin contains 85,152 triangles; the separate eyelid/eye-opening
face partition contains 10,756. Counts alone do not establish good sculpting.

| Coordinate proxy on body skin | Triangles | Median edge length | Stored normal versus area-weighted reference, median / p95 |
| --- | ---: | ---: | ---: |
| Cheek | 2,780 | 3.98 mm | 0.178° / 1.141° |
| Temple | 1,332 | 5.81 mm | 0.108° / 1.527° |
| Neck | 4,002 | 6.58 mm | 0.176° / 2.173° |

These are coordinate selections, not semantic segmentation or a mapping from
each bad pixel to a mesh triangle. The reference is an independent numerical
comparison, not a replacement-normal recommendation. Among 222 exact-position
duplicate groups on the body's head/neck, the largest normal difference is
0.0286°. Normal lengths remain within approximately `1 ± 1.2e-7`; the maximum
absolute normal/tangent dot product is `0.000144`. No large split-normal seam
or gross tangent nonorthogonality was found in those inputs.

Skin vertex RGB is constant white. The face's alpha 0 and body's alpha 1 are
semantic masks, not triangular RGB variation. The 512 × 512 skin normal map
has R123–132, G122–133 and B255. At its retained strength 0.24, reconstructed
normal deviation is median 0.275°, p95 0.381° and maximum 0.652°. The inspected
albedo and normal maps contain fine procedural variation rather than painted
large triangles. This weakens, but does not eliminate, a direct texture cause.

The anatomy generator enables smooth polygons and one Catmull–Clark refinement.
The later facial partition preserves original corner normals. The current
surface finish does not alter geometry, normal maps, normals or UVs. Import,
skinning, shadowing and screen-space effects can still change the final result.

**Next correction packet:** the renderer should freeze this same three-quarter
pose/camera/exposure/LOD and capture a one-variable comparison with only the
sun's shadows disabled, then restore it. The portrait fill is already
unshadowed; the sun uses bias 0.025, normal bias 0.35 and four cascades over
70 m. Directional self-shadow/normal-bias interaction is a plausible first
suspect. If the patches disappear, tune a bounded shadow correction and retain
contact/jewelry shadows. If they remain, test SSAO, skin normal mapping and SSS
independently before increasing mesh count or rewriting normals.

No ablation was rendered in this assignment, so the cause remains **unproven**.
No runtime, asset, texture, rig or animation was edited. No Blender, Godot or
heavy rendering process was started. Raw source inspection does not establish
the GPU's imported or posed vertex values, final sculpt quality or AAA parity.
