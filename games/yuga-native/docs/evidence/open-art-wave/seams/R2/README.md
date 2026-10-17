# Role06 admission correction

Independent QA preserved four R1 admission failures: a candidate path inside
the native project was admitted; a short logical BIN length and an existing
NaN tangent were accepted; and a dangling report symlink was followed after
publishing the candidate. The original source, tests, reports and failing
receipts remain unchanged in `source-before/` and the adversarial evidence.

The splitter now wraps the frozen Mikk tool with its own stronger public guard.
It resolves parent symlinks, rejects a candidate anywhere inside the native
project, refuses existing output directory entries including dangling symlinks,
checks source/library/output/report aliases, and creates reports exclusively.
It reuses the existing bounded `repair_mesh.read_checked` logical-BIN, view,
stride and sparse validation, then checks **every** accessor for finite values,
including protected attributes, morphs, bind matrices and unreferenced data.
The Mikk generator and mesh-repair source files were not modified.

Verification passed 48 author checks, 16 independent adversarial checks and
42 independent actual-candidate checks. The author suite retains its 30 R1
checks and adds 18 regressions, including a valid reflected chart with 40-byte
interleaved POSITION/NORMAL/TANGENT, shared UV storage, normalized uint8 COLOR
and sparse morph data. This fixture still copies every attribute/morph row
without replacing the original tangent values.

The independently executed corrected CLI produced exactly the same candidate:
`5fc60979b7e258144e01a5ffb46752c263635e848c983cbd24aad52c5827c792`.
The previous 38-check deformation/lineage evidence therefore remains relevant
to its unchanged bytes. The guards add no shading, UV or runtime improvement;
52,971 unresolved corners remain recorded, and no playable asset was changed.

`summary.json` pins the corrected source/test hashes, dependency hashes, author
suite, independent adversarial result and actual execution receipt. The existing
test command is unchanged:

```sh
python3 games/yuga-native/tests/hero_seam_cases.py \
  --report=/absolute/fresh/seam-tests.json
```
