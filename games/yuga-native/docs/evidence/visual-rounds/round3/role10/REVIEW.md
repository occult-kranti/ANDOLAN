# R3-10 independent groom geometry and posed clearance

**R6 clearance is rejected. R7 corrects sampled rest clearance; action and
secondary-stress clearance remain blocked.** This review uses exact triangles
and actual captured rig matrices. No renderer/import ran in this role and
intersection counts alone do not establish visible severity.

The independent source reader and full-triangle narrow phase compare new lower
hair against rest-selected collar/chest/neck regions: 4,882 new hair triangles,
30,165 gold, 2,759 silk, 488 brocade and 17,454 neck/chest. Broadphase radius
buckets preserve nearby pair coverage; exact point/edge/triangle distances and
edge/face crossings handle intersections that vertex-only tests miss. Analytic
5 mm separation and edge-through-face controls pass. An additional independent
linear-system solve confirms the published r6 witnesses to floating-point
residuals below 1e-15 m.

R6 and exact R2 baseline replay the same 37 captured poses (21 unique geometry),
plus 24 opposing secondary-limit fixtures. At rest, baseline→r6 crossing-pair
counts are gold128→24, silk239→14, brocade179→14, neck/chest670→187. The baseline
already has this defect class. Different topology prevents interpreting these
counts as a visual improvement or regression.

The r6 collar witness is an **outer nape-7 clump**, not an attached scalp root:
vertices15824–15839 lie at offsets369–384 of444, alpha0.646–0.696, source
y1.509–1.523 m. A silk witness crosses near(-0.1036,1.3856,-0.0407) m in the
posed hero frame. The neck witness uses outer nape-0 vertices12672/12685/12673,
offsets325–338 of444. `witness-source-groups.json` supplies exact source and
posed coordinates; `intersection-witnesses.json` supplies independent contact
points/barycentrics. These are actionable exposed-clump witnesses, not summed
scalp-shell attachments. Role08 received them before the r7 correction.

A new read-only actual imported r6 run captures 39 sequential walk/run/backpedal/
strafe/stop/aim/draw/release/cancel/jump/fall/land/reset states at30/60/120 Hz,
with all164 bone matrices. Its 15 unique geometries retain crossings. Separately,
the actual imported motion/contact suite passes39/39 hand/string/sole/authority
checks. Nonhair source attributes and indices are byte/numerically exact. Those
passes do not clear the new hair or the previously rejected R4 foot candidates.

R7 is a separate, pinned follow-up. It changes only bounded lower nape positions
and related frames while retaining topology. Independent replay corroborates
zero rest crossings; the minimum full-triangle gap is3.472346 mm at silk and
5.455931 mm at neck/chest; gold/brocade exceed the12 mm search band. Among21
unique ordinary action geometries, `measured_step_recoil` still has536 crossing
pairs (gold52/silk106/brocade106/neck272). The exact action is recovery at elapsed
0.15 s, dash phase0.18. Silk/brocade use nape-0 vertices12739/12752/12740 near
(+0.111,1.384,+0.072) m; `r7-action-witness.json` gives camera/action helpers.
Opposing bounded secondary stress still crosses in19 of24 fixtures. These
independent worst-direction offsets are envelope probes, not claims of an
executed ordinary gameplay trajectory. R7 rest acceptance is limited to sampled
geometry; action/secondary and actual art gates remain open.

The first unbounded broadphase attempt was terminated for excessive memory
before a complete result; it and logs are retained. A baseline helper import
path failure and the first r7 relative-source-path failure are also retained.
Corrected probes completed. All current result files pin source/probe hashes.

Reproduce source replay from repository root with `taskset -c 0,1 python3` and
`geometry_probe.py`, `baseline_geometry_probe.py`, `r7_geometry_probe.py` or
`actual_pose_geometry.py` in this directory. `capture_pose_tape.gd` uses role06's
frozen candidate imports, as does `tests/rama_motion_cases.gd`; no cache mutation.

Source commit0437ea91…; canonical motion remains unchanged. No asset/controller
edit in this role. Next owners: role08 for bounded geometry disposition, role06
for exact original views and root/role15 for actual visible acceptance.
