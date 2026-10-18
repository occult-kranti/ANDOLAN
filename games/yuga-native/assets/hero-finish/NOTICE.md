# Original Rama finish fields

The G1 hair-bundle and forged-gold roughness maps are original analytic scalar
fields authored for YUGA in [the editable generator](../../art/hero-finish/build_g1_maps.py). They contain no photographic,
commercial-game or third-party texture data. The source formula is the editable
asset; `g1-manifest.json` pins the generator and lossless PNG outputs.

Both 512×512 grayscale maps use the linear red channel, repeat with matching
opposite edge pixels, and request a full mip chain. Hair U follows the existing
R7 clump circumference and V its length. Hair combines irregular bundle widths
and finer directional variation; gold combines restrained forging and crossing
tool-mark variation. These maps affect roughness only, with no displacement,
normal replacement, geometry, opacity, rig or motion change.

Rebuild with `python3 art/hero-finish/build_g1_maps.py` from the native project
directory. Pillow is required only for offline generation and verification.

## Optional G2 upper-hair tier

`upper-hair-layers.json` contains seven original broad layer guides authored by
[`art/hero-finish/build_g2_hair_layers.py`](../../art/hero-finish/build_g2_hair_layers.py),
fitted by rays against the exact original YUGA R7 hair source identified in that
file. The generator, source GLB and guide bytes are pinned. No third-party hair
or commercial model is used. The source guides are editable; the separate
`scripts/rama_upper_hair_layers.gd` helper builds a closed 1,904-triangle mesh and
uses the existing head bone and shared hair material. It is an optional review
candidate, not the rejected temple-wisp prototype or a default player feature.

Rebuild the guide file with `python3 art/hero-finish/build_g2_hair_layers.py` from
the native project directory. This offline source-fitting step requires NumPy
and the repository's existing `glb_lod.py` reader; it does not import or re-export
a model. Actual model/art acceptance requires the matched off/on captures.
