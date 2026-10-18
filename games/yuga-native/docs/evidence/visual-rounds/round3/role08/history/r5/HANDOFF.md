# R3-08 principal groom candidate

Product: YUGA native. Source commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
Owned source is `art/visual-rounds/groom/`; raw outputs remain under
`/workspace/scratch/visual-round3/role-08/`. No runtime asset/default, shared
ledger or commit was changed.

The real renderable near/mid/far candidate is `groom-r5`. The new scalp is fitted
to the actual anatomical mesh and extends into the bare temple wedge. Five broad
crown, two short temple and nine asymmetric nape clumps replace the former thin
principal locks. Eyebrows and topknot retain exact source records. All nonhair
binary bytes and every material/image/rig/morph payload are preserved. Full
reconstruction commands and binding contracts are in the groom README.

| Level | Output SHA-256 | Hair triangles |
| --- | --- | ---: |
| Near | `bdd917daa88254bdf203fd0bb92c7fb1167fda05a3c223dea4c9f3a3bc0453d1` | 29,448 |
| Mid | `e50b308d75f278bc3b30598776891dce04111e089609a40cc7292be72bb32411` | 13,450 |
| Far | `00e63ad9ff36482f3b8d2157a398a20715d58636aec2b036cf02947d67595ea1` | 6,444 |

Actually executed:

- `build_groom.py` twice: all three outputs byte-identical.
- `validate_groom.py`: 56/56 geometry/source preservation checks pass. Near
  conservative full-triangle clearances: ears 6.095 mm, eyes 46.834 mm, brows
  42.611 mm, diadem 5.554 mm. No new degenerate geometry; all new UV/TBN data
  finite, bounded and normalized. Every new vertex uses original head joint 104.
- `measure_coverage.py`: original 2/208 versus candidate 208/208 predetermined
  temple rays covered within 25 mm of the actual skull.
- `replay_motion.py`: 37 actual previously captured baseline pose matrices
  replayed on source geometry, including aim extremes, partial/full blinks,
  five ability phases and cancellation. New head attachment stays finite;
  maximum relative ear motion is 0.602 mm. This is source replay, not a new
  candidate import or new runtime action execution.
- New-geometry secondary stress: 110,016 triangle/offset samples, 2.536° p95,
  5.161° maximum geometric normal turn, zero samples above 90°. Existing shader
  frame update remains a separate role05 issue.
- Khronos exact-byte validation: near zero errors; mid/far 17 errors each.
  Both inputs reproduce those exact 17 errors. The stale nonhair frame bounds
  and exact declared/actual data are in `inherited-lod-bound-errors.json`.
  Root/role14 owns the input repair and new source pins.

Actually viewed: original R2 courtyard front, profile and left three-quarter day
PNGs, opened individually. Their hashes are in the source manifest. Inspected
the original and quality hair generators, actual source scalp/ear/eye positions,
and the existing native-source Blender inspection receipt. New groom PNGs and a
new Blender import have **not** yet been reviewed or executed by this role.

Preserved failed iterations: r1 inward geometry winding and untested cap UVs;
r2 fixed winding but degenerate tip UVs; r3/r4 numerical clearance failures.
R5 raises and seats the temple root and preserves at least 5.4 mm measured diadem
separation across LODs. Reports retain the original failed outcomes.

Remaining defects and next owners:

1. Role14/root repairs R2 face/body/lip NORMAL/TANGENT accessor bounds 4474,
   4476, 4589, 4598, 4600. Their binary geometry is already correct. After new pins,
   rebuild/revalidate groom; hold mid/far promotion meanwhile.
2. Role06 has the requested serialized front/profile/rear capture and
   `import_editable.py` command. The importer is prepared to inspect source
   groom objects, save/reopen 164 bones, nine clips, four face morphs, 17 packed
   images, and 16 hidden source guide curves. It performs no runtime export.
3. Independent artist reviews actual groom pixels and continuous
   turn/dash/draw/release/reset footage, gameplay scale and LOD transitions.
4. Exact retained topknot still has 220 source degenerate triangles and its
   existing alpha mask can produce 178.838° normal reversal under an 18 mm stress
   offset. Those values are unchanged source defects. Root approved retaining
   them exactly; any topknot repair needs its own declared boundary.

This return completes the bounded source candidate and executed numerical work.
It does not promote the candidate, close final art acceptance, claim collision
free runtime motion, or establish physical-GPU performance.
