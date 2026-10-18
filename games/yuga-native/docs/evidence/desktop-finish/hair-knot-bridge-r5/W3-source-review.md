# W3 source-only review of the compact knot bridge

Reviewed the authored proposal and generator, without running the generator,
an engine, an import, a geometry/contact probe or a renderer. The R4 visual
rejection is the parent/W2 decision motivating this change; this review does not
independently repeat that pixel disposition. The sealed shoulder packet is untouched.

Exact reviewed inputs:

- `art/hero-finish/hair-knot-bridge-r5/SHAPE_BRIEF.md` —
  `a63b9869e62b8aab4827fba05100d74e77f32fd9085629ae69ef0b02f2cd3780`
- `art/hero-finish/hair-knot-bridge-r5/build_candidate.py` —
  `ce35bbd0439d1571aba59b5c9bf3eb1e572b8db908a1819dfe04fbba7c9fbb5a`
- The generator pins the retained R4 builder to
  `dccbbd8c25e5d093d16940a5aa53153a220408b9fcae56fa3f57d45c258c7f39`;
  that builder pins the original groom helper to
  `4bcdb1121a52c68f2cb3f35850ace8956fb0554d120a85ce292c4f4afa8f6044`.
  Their `OuterHead`, `Mesh.arrays` and `append_candidate` implementations were read.

The nominal 48–50 mm bridge width is restrained relative to the reported
70.6 mm lower-knot width. Its nominal top at y1.861 m sits 4 mm below the reported
tie minimum at y1.865 m. The proposal adds one short gathered connection with
zero secondary alpha and the existing opaque hair material/head binding. It
does not move the knot, tie, crown or nape, introduce a second runtime writer,
or add unrelated adornments. These are source design limits, not measured final
mesh clearance or proof of a visible improvement.

The assembly concatenates the existing R4 active attribute arrays and indices
before the new bridge, then changes only the hair primitive references through
the existing append-only helper. This is appropriately narrow. The final validator
must still compare exact stored bytes: complete original BIN prefix, every
nonhair JSON/resource field, original active hair array/index prefixes, fixed
source identities, and new head-joint/weight/mask records. A source comment or
an unchanged knot bounding box is insufficient preservation evidence.

Two concrete qualification risks remain:

1. The radial smooth-maximum seating step can move each top-ring vertex beyond
   its declared nominal top coordinates. Therefore nominal width, y1.861 and the
   ring's aperture do not establish tie clearance. Check the final stored envelope
   and complete new triangles against actual head and gold/tie triangles at all
   three LODs. Do not describe the fitted result as bounded below the tie merely
   from the control point.
2. The closing fans join fitted ring vertices to separately specified center
   points. Even when every sampled ring vertex has positive head relief, a fan
   triangle can cut the underlying surface. Include both fans in the full-triangle
   clearance test; sampled-vertex relief alone cannot qualify them.

Also verify intentional hair-to-hair attachment at both ends. A small endpoint
distance can still leave a visible gap; actual intersection or a sound solid-
containment test is required. New-triangle posed/stress clearance must be separate
from inherited unchanged-R4 checks. The same full source identity must justify
any inherited result. Exact imports and new matched rear/profile/live-cast
originals remain necessary for the eventual art decision.

W2 acknowledged both risks and committed to checking final stored triangles,
fans, actual envelopes, positive attachment at each end, and exact preservation.
Those checks were not executed or independently verified by W3 in this review.
No reason was found to broaden the bridge or revise the lower nape at this stage.
Disposition: reasonable bounded source proposal; generated geometry, import,
contact and pixel acceptance remain open.
