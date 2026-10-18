# S4-W5 — independent diadem rail source review

The exact review-only candidate has a bounded source pass. Its byte-preservation,
normal/tangent construction and retained sample census pass the independent
checks below. A separate retained-resource check closes the actual imported
numeric bone-order mapping. Candidate import,
matched images and activation remain separate gates. No motion source or motion
capture stage changed in this review.

This review binds W3 receipt `e1199cf16f4e7da2e1eb060356658a3f558348c1df95140e8e9d161ca8e08cf4`
at source HEAD `c96255ac575916cb8c3a300589051b5e2a94d4d4`. The three exact candidates
are near `bda22a046d44079769ac60ca15db2b82be1a34eea72efc962547cfc7bd4b40f0`,
mid `ab2e0bacd9804c4af05f0ecfcbdfedfdeec6b3c40d8a7d86f2271613a94ddc82`,
and far `33019438b13e895181ef0d010e3abfef116f4048ebc0b3b19ad5d0201839d9d7`.

[Independent results](rail-source-review-r3.json) record 22/22 checks in 5.99 s
on CPU4, OMP/BLAS/LP/MKL1. No Godot, importer, renderer or Blender ran. The
[verifier](rail_source_review.py) independently reads the GLB chunks/accessors,
including sparse morph accessors. It validates every author receipt pin, exact
JSON bytes, all binary bytes outside the selected P/N/T rows and all 4,612 other
accessors at each LOD. It finds 729/491/249 rail vertices and 1,130/764/380 rail
triangles. Rig, weights, UVs, indices, colors, morphs, animation and separate
crest/leafwork remain exact.

The original front-sector wording was too broad. Fixed centerline samples do
not preserve all neighboring tube frames. The author's retained correction
records 16/11/4 changed front position rows, at most 0.146 micrometres, and all
front rail normals/tangents recomputed. A claim of unchanged front appearance
would therefore still be unsupported. The separate crest/leaf components are
byte-exact. No shape change was requested merely to preserve the old wording.

The frame check solves each stored triangle's UV Jacobian independently, sums
U/V derivatives at vertices, orthogonalizes U against the stored normal, and
compares the handedness of `cross(N,T)` with the accumulated V direction.
All LODs agree: minimum tangent dot 0.9999999609; no handedness mismatch; maximum
normal/tangent orthogonality error 6.04e-8. Stored normals agree with the area
orientation of stored triangles, minimum dot 0.9999999568. Flipping one tangent
sign is rejected for every LOD. The inherited UVs contain 10/11/9 degenerate
triangles; all rail vertices nevertheless receive defined derivatives from
adjacent nondegenerate triangles, with no fallback vertex. This establishes
source-frame consistency, not MikkTSpace equivalence or rendered normal-map
appearance. The front metallic highlight and LOD transitions need actual views.

The reported rest minima of 2.123794/2.023039/2.290806 mm belong to W3's stored
float32 full-triangle run. I reviewed its complete-pair radius/AABB broad phase
and point/edge/triangle narrow phase, plus its exact-byte input checks; I did
not rerun that full distance sweep here. The source head/hair triangles omitted
below 1.70 m cannot produce those minima: the full rail is above 1.784 m. These
are source-rest distances, not posed/secondary/whole-body clearance. Khronos
zero errors/three warnings per GLB is the author's pinned structural result,
not a new independent importer run.

The retained native archive decompresses to exactly 31,908,960 bytes, SHA
`ed5aa15f6eb065b02992ce8ea695f4d15520a57c0d842b7e236571599b486b01`.
Its producer is the exact archived fixture `cd2ca73c…1485e6`; all before/after
source/import pins agree, including the accepted R7 near raw GLB and motion
`8c3771a3…`. There are **348 recorded samples, not 347**: each of three pitches
has 13 Kodanda, 42 Piercing Dawn and 61 Dawn Volley evaluations. Their IDs,
declared elapsed values and maximum 1/60-s advancement match the fixture;
every row contains 164 finite affine bone matrices. These are genuine retained
Godot imported-player **direct API pose evaluations**, with the actor and
modifier clock deliberately disabled. They are not 348 rendered frames or a
native modifier continuity tape. The existing engine log records 18/18 checks;
that historical count is not included in this review's 22 checks.

The imported hand influence points recover source rest positions without
assuming importer vertex-index order: maximum nearest-source error 0.163 µm
and inter-influence spread 0.254 µm in this independent calculation. Raw
quantized weights are preserved. A different, conservative clearance method
compares the entire posed rail AABB with each of the 24,644 actual selected
hand-triangle AABBs. The minimum lower bound is **61.958 mm over all 348 rows**.
It supports the author's weaker ≥40-mm near-hand bound without relying on its
triangle narrow phase. It is limited to this selected hand subset; the numeric
index mapping is closed as described next.

The tape stores numbered bone matrices but no names. Resolving glTF
`skin.joints[104]` to `head` alone did not prove imported `bone_globals[104]`
was the head. This evidence gap is now closed by
[the separate mapping check](rail-mapping-review.json), **6/6**: the actual R4
role06 original capture records all164 imported names in index order, and its
near raw GLB, descriptor and imported SCN bytes exactly equal both before/after
pins in the 348-sample tape and the retained baseline resource. Every recorded
name agrees with glTF skin order, including104=head. Its original observer
`af519bfc…c0e7` matches its captured before/after source pins and explicitly reads
`rig.get_bone_name(index)`. Only immutable resource indexing is reused; old R4
motion behavior is not transferred. No new engine or baseline import was needed.
The original 22-check receipt retains its then-conditional wording; this later
separate receipt resolves that dependency without overwriting the first result.

Two verifier failures are retained as fixture failures: r1 could not decode an
inherited sparse accessor, and r2 incorrectly required every inherited UV
triangle to be nondegenerate. Their exact scripts and tracebacks are retained.
The final reader handles sparse arrays; the final frame calculation records
and excludes undefined face derivatives while requiring a defined accumulated
derivative for every rail vertex. No candidate byte or geometry threshold
changed to obtain the source result.

Next owner: W3 supplies the new candidate imported equivalence receipt; W1/root
owns matched front/profile/rear plus cast originals, with identical light,
pose, camera and inactive optional hair/fletching helpers. Reject new kinks,
pinching, crest discontinuity, material-frame artifacts, clipping or no useful
visual improvement. Mid/far posed clearance, full body contact, continuous
motion and physical-GPU quality remain open. The separate motion pair remains
frozen and unrendered, with its 25/27 comparative result unchanged.
