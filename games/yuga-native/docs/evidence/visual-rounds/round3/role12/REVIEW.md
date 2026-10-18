# R3-12 independent fixture and revision audit

Source commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
Use **`capture-contract-r6.json`**, which supersedes role02 for both current groom
pins and gallery ground height. Historical role02 files remain unchanged.

The independent audit caught a real placement error: both east-gallery stations
stand on the existing `COL_BEVEL_Indigo_glazed_stone` deck at y=.4399999976 m,
not the central courtyard floor. The original player y=.05 intersects that deck.
The rejected pre-correction report is retained as `rejected-embedded-station.json`.
Two downward source-triangle rays establish the deck height at both x19,z=-1
and x19,z=-15. Correct player origin is y=.4400999976 m; translate every station
camera and look-at target upward by .3900999976 m. Close dark camera becomes
`(17.4,1.5000999976,-1)` and target `(19,2.0000999976,-1)`; relative framing,
yaws, FOV and background geometry remain identical. The ordinary gameplay shot
and central-courtyard continuous take are not on this gallery and are unaltered.

A conservative 1.3 m wide, 2 m high box above the corrected deck has zero source
`COL_` triangle AABB overlaps at both stations. The actual source capsule radius
is .29 m and height1.8 m; the larger box checks additional visual room. This is
not a new native capsule sweep or gameplay-grounding result.

Every source accessor array and every BIN byte in groom r5/r6 is exact at all
three LODs. The near GLB is entirely byte-identical:
`bdd917daa88254bdf203fd0bb92c7fb1167fda05a3c223dea4c9f3a3bc0453d1`.
Mid/far JSON differs only in optional accessor min/max values (11 scalar leaves
per file); their geometry, index, UV, skin, animation, materials and images remain
exact. Thus the near source projection values legitimately transfer to r6.
This does not transfer an imported runtime or pixel verdict that never existed.

The backdrop calculation uses ray-plane intersection followed by Gram-matrix
barycentrics, separate from role02's Moller-Trumbore implementation. It samples
a 9×9 grid across the complete union head rectangle plus12px border, including
interior positions. After the ground correction, **81/81** samples in each of
five dark views first hit existing indigo stone and **81/81** in each of two light
views first hit warm sandstone. There are zero foreground hits. Raw shaded
pixels and actual imported pose/secondary displacement still decide acceptance.
The dark-foliage requirement remains unclosed; this is explicitly dark stone.

The audit records current `courtyard.gd` and capture-runner source drift relative
to role02, alongside the unchanged environment geometry identity. The capture
owner must pin the frozen project it actually executes; this packet does not
assert that evolving UI/capture code is byte-identical to role02.

Executed successfully:

```sh
OPENBLAS_NUM_THREADS=1 python3 games/yuga-native/docs/evidence/visual-rounds/round3/role12/audit_context_r6.py
```

`context-r6-audit.json` contains all seven dense ray grids, ground hits,
conservative obstacle checks, revision comparisons and exact source hashes.
No original image is recolored/cropped or used to claim new station pixels.
The prior actual R2 profile original establishes the physical panel's visibly
dark appearance; R3-02's original-image ledger retains that observation.

Next owner: 06 uses the corrected contract, final modifier-processed rig poses,
actual imported vertices and current shader offsets before capturing. The new
source hashes and rejected older station must remain in the capture receipt.
No canonical runtime, ledger, imports, renders or commits changed in this role.
