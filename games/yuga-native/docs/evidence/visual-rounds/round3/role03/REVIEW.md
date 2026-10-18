# R3-03 cloth and hair material controls

Source commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Outcome: preserve
current lights and hair material; retain R3-01 as one isolated woven roughness
candidate. Eight executed source checks pass. No runtime or asset was changed.

The original R2 courtyard left-three-quarter day PNG shows repeated narrow
highlights along the many long dark locks and a smooth scalp dome. The ordinary
rear gameplay night PNG shows large coherent fold streaks on both cobalt tails;
cloth folds remain visible while the hair mass is dark. Both originals were
opened with `view_image`. These observations do not isolate roughness from
geometry, normal maps, secondary displacement or lighting.

`material-controls.json` records exact source hashes and measurements. Woven
roughness changes from mean .726729, standard deviation .040927, range
.666667–.796078 to mean .789982, deviation .009566, range .772549–.811765.
Hair remains mean .550994, range .470588–.631373. These are scalar texture
values, not measured specular luminance or a prediction of visual improvement.

The actual owner sets roughness multiplier 1 and RED sampling. The shader's
roughness sampler has linear mip filtering and no source-color conversion.
Candidate cloth targets only the two cobalt materials and retains specular .38;
all groom material JSON remains exact. Original albedo, normals, metallic,
geometry and lighting therefore remain the diagnostic controls. The canonical
vertex shader displaces positions with alpha-squared weights but does not
transport the authored shading frame; R3-05's separate proposed transport cannot
be credited to the cloth roughness change.

Both current hair and woven `.import` files declare `mipmaps/generate=false`.
R3-01 explicitly requires candidate woven mip generation. Capture owner must
record actual imported format/mip count and active shader texture/channel at
all three LODs. Do not silently bundle hair mip changes: they would add a second
material variable without matched evidence. Missing source mip declarations are
not themselves proof of visible shimmer or exact imported runtime payload.

Use the already bounded R3-02 fullbody and rear/profile views with unchanged
source-pinned day/night endpoints, exposure 1, current shadows and no portrait
fill. Reject flattened folds, chalky cobalt, lost embroidery or motion shimmer.
If a defect remains, first compare the same imported source/pose with neutral
secondary offsets as a separately labeled diagnostic; do not change lights or
hair roughness based on an unisolated highlight. No extra capture is required
merely because this diagnostic option exists.

Executed:

```sh
python3 games/yuga-native/docs/evidence/visual-rounds/round3/role03/check_material_controls.py
```

An initial Python syntax failure happened before any check; its cause and
correction are retained in `failed-initial-syntax.json`. The corrected run passes
8/8 source checks. No render, import, GPU shader run or candidate pixel judgment
was performed. Next owner: 06 for matched actual images/import receipts, then
independent material reviewers.
