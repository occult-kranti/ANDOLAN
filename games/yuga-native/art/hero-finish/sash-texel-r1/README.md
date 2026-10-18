# Cross-body sash textile scale — inactive original candidate

The lead directly reviewed the eight smooth-crown originals. The cross-body sash turns the original small gold flowers into long diagonal streaks. Source measurement of its complete welded volume confirms directional UV stretch: near/mid/far median metres-per-V divided by metres-per-U is 4.890/5.064/5.129. This is a texture-coordinate issue in addition to the separate unresolved cloth shape, collision and material quality.

The candidate uses one positive UV scale, U×0.20 and V×0.95, on the complete cross-body sash only. This both restores more even motif proportions and gives the cloth a quieter pattern with approximately one flower across its width. Corresponding median metric ratios become1.029/1.066/1.080. This is a source-rest directional metric, not a complete conformal-distortion or pixel-quality proof. Small extrusion-side UV triangles are excluded by the declared numeric threshold; the per-LOD manifest records counts before and after.

The input is the reviewed smooth-crown R2 trio. Only selected TEXCOORD_0 float bytes change. The GLB JSON, global UV accessor bounds, all positions, normals, tangents, indices, weights, joint binds, morphs, images, materials, crown and other cloth components remain byte-identical. Positive constant independent UV-axis scaling preserves normalized tangent direction and handedness; actual importer behavior still needs verification. No new texture, draw, geometry or runtime shader is introduced.

Run from repository root using the prepared NumPy/SciPy Python:

```sh
/workspace/tooling/yuga-native-python/bin/python games/yuga-native/art/hero-finish/sash-texel-r1/build_candidate.py --output /absolute/fresh/directory
```

The first attempt stopped before writing a GLB because it incorrectly assumed absent UV min/max metadata. It is preserved in candidate-r1. Revised candidate-r2 verifies that all actual accessor extrema stay exact; it never ignores or rewrites them.

## Actual-review handoff

Private-import candidate-r2 using original descriptors. Compare loaded UV arrays and ensure every non-UV array/skin/texture/material remains exact against the smooth-crown imported baseline. The existing smooth-crown rest-front and cast-three-quarter originals may serve as baseline only if the capture helper's sole change is the declared raw-admission pin and all recorded camera, lighting, pose, clocks, sources, imported cache and quality settings match. Otherwise take a fresh matched pair. Do not mix this with new hair/shoulder/lighting or motion.

Accept only if flowers read as deliberately woven ornament rather than scratch-like streaks, the cobalt field has clearer large shapes, and no seam, moiré or new normal-map anomaly appears. Front/cast pixels are required. Preserve baseline skin, gold and lighting. Reject if larger ornament becomes distracting or stretched side walls become exposed. This is not part of the current schema6 crown integration or qualified package until explicitly accepted.
