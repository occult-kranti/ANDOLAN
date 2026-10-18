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
