# R3-01 cloth candidate handoff

Product: native YUGA. Source commit:
`0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
Status: candidate authored and CPU checks pass; imported and rendered acceptance pending.

Actual original images opened with `view_image`:

- `art/hero-rama-quality/reviews/baseline-front.png`: full hero and drape show
  existing large folds and a narrow, lustrous sash. This is historical studio
  context, not current source acceptance.
- `docs/evidence/visual-rounds/round2/role06/baseline/courtyard/courtyard-front-day.png`:
  current face crop provides shoulder/sash context; it does not cover the full cloth.
- `docs/evidence/visual-rounds/round2/role06/baseline/courtyard/courtyard-gameplay-day.png`:
  rear gameplay mantle shows narrow alternating bright bands and repeated pattern.
- Actual current woven roughness, original floral albedo and generated candidate
  PNG were also opened. Current roughness has large repeated diamond motifs;
  original albedo has different floral embroidery.

Decision: keep original geometry, color and normal-map detail; replace only the
woven roughness response with a smoother continuous original field. This is a
material hypothesis to clarify the existing fold hierarchy. It does not author
new fold geometry or garment thickness. A production art claim awaits pixels.

The 1024×1024 grayscale PNG is
`art/visual-rounds/cloth/textures/woven-roughness-r3.png`, SHA256
`eec110e598ac1a2fa95fb5899fac5fc314a191bff8e670547d79dfaf1468e500`.
Its size is 5,823 bytes; exact mean 0.7899816176470589, range 197–207/255.
`source-manifest.json` pins all three original GLBs, external cloth color/normal
maps, current finish/shader/generators and reviewed image hashes. Source tests
confirm those bytes remain unchanged. No additional LOD geometry work is needed;
all LODs must bind the same candidate resource during integration.

Executed commands from repository root:

```sh
python3 games/yuga-native/art/visual-rounds/cloth/build_candidate.py
python3 games/yuga-native/art/visual-rounds/cloth/build_candidate.py --check
python3 games/yuga-native/art/visual-rounds/cloth/test_candidate.py
```

Seven tests pass. `cpu-tests.json` records the results. An initial 8-bit Pillow
mip reference accumulated rounding bias; its failure is retained in
`cpu-tests-rejected-mip-reference.json`. The corrected float reference preserves
the source mean within 1e-6 and converges to negligible fiber variation at small
sizes. No engine mip test, Godot import, physical-GPU timing or rendered
candidate acceptance has been claimed here.

Research consultation: R3-07 inspected Material Maker's exact weave source and
recommended smooth, even-period crossing instead of its hard gates; this bake
uses original cosine math and no copied formula. R3-07 also found the existing
secondary shader displaces positions without updating normals/tangents. Its
rest/local extreme-offset diagnostic is separate from runtime visual evidence;
roughness does not resolve that baseline limitation.

Next owners: root integrates only the woven roughness slot in a frozen stage;
role06 enables imported mips and runs `import_probe.gd` plus matched images;
roles09/13/14 verify actual channels, LOD texture sharing, resources and lifecycle;
role15 independently accepts or rejects the pixels. Preserve all original
surface names, mask alpha, rigid anchors, gold trim and secondary-motion owner.
