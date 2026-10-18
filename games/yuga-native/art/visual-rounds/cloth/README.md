# R3-01 smooth woven roughness candidate

One 1024×1024 8-bit grayscale PNG replaces the broad diamond roughness pattern
with restrained, continuous warp/weft variation. Mean roughness is 0.789982
(previous finish: 0.726729), range 0.772549–0.811765. Existing folds and silhouette
supply the macro shape; this candidate adds no fold geometry or thickness.

Run from repository root:

```sh
python3 games/yuga-native/art/visual-rounds/cloth/build_candidate.py
python3 games/yuga-native/art/visual-rounds/cloth/build_candidate.py --check
python3 games/yuga-native/art/visual-rounds/cloth/test_candidate.py
```

The output is `textures/woven-roughness-r3.png`. Python requires the already
available NumPy and Pillow. The builder writes only this directory's texture and
profile. It reads no source images and uses no random state or external service.

Root owns the runtime binding. In a frozen candidate project, supply this
texture to the existing finish owner's `woven` map slot, or overlay the existing
`assets/materials/rama-finish/woven-roughness.png` with these bytes. Preserve
RED channel selection, scalar multiplier 1, specular 0.38, identity UV transform,
and existing `rama_secondary_cloth.gdshader` owner. Only `Cobalt handwoven silk`
and `Cobalt lotus brocade` should receive the map. Near, mid and far LODs must
share that imported resource. Preserve all other material bytes and bindings.

Explicitly enable `mipmaps/generate=true` for the candidate texture and the
staged woven texture if overlaid. The current woven import has it false. Its
roughness sampler already declares `filter_linear_mipmap` without `source_color`.
Do not gamma-convert roughness or set it as a normal map. The PNG's logical
storage is R8; Godot's actual imported format and VRAM use require its receipt.
One 1024 R8 texture with a complete mip chain has 1,398,101 scalar texels; engine
format/compression may use more memory. It replaces an existing map slot.

After the capture owner has imported this directory in the isolated project:

```sh
godot --headless --path <frozen-project> --script res://art/visual-rounds/cloth/import_probe.gd -- --report=<fresh-report.json>
```

That probe checks actual mip payload, channels and a real ShaderMaterial input.
It has not been executed by role01 because role06 owns the serialized import
queue. Integrated material ownership and LOD sharing still need role09/14 review.

The seven executed CPU tests cover repeatability, actual PNG encoding, bad
flat/gamma/packed-map counterexamples, periodic value/gradient seams, a floating
point mip reference, source hashes across all three LODs, and channel selection.
The initial 8-bit Pillow mip-reference failure is retained: Pillow's sequential
integer averaging shifted the mean by up to 1.554688 code values. The corrected
reference uses float averages to avoid adding intermediate quantization bias;
it does not predict exact engine mip bytes or replace the import gate.

The generated texture was opened with `view_image`; it is only an authoring
artifact. Actual matched day/night front, rear, profile, gameplay and continuous
action images decide whether the change improves cloth. Reject if folds flatten,
blue fabric turns chalky, embroidery disappears, or motion shimmers. A roughness
map cannot correct baseline secondary-motion normal-frame mismatch, skin/cloth
intersection, or missing physical thickness. No GLB or runtime source was edited.
