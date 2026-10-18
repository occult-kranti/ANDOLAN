# R3-07: bounded reuse and motion-frame contracts

17 October 2026. Product: YUGA native. Source baseline
`0437ea91edf6989ff78c1eeadb3661f4825b60f2` on `game/yuga-native-production`.
This is a research/offline-tool handoff. No runtime, shared ledger, asset,
Blender export, Godot import, render, gameplay input or commit was changed here.

## Implemented and measured

One small permissive diagnostic was justified by the actual shader:
`rama_secondary_cloth.gdshader` changes `VERTEX` using squared authored alpha,
but leaves `NORMAL`/`TANGENT`/`BINORMAL` unchanged. The offline
`tools/visual-rounds/reuse/secondary_frame_probe.py` adapts the MIT Godot
Plane/SurfaceTool triangle-normal construction to measure the resulting geometry
normal change. It never repairs or promotes an asset. Six test methods passed:
uniform translation, exact tilted-plane counterexample, mirrored-UV frame,
degenerate/nonfinite refusal, displacement/anchor bound and strided normalized
accessors. The known tilted plane turns by atan(.075), about 4.289°, despite two
vertices remaining exactly anchored.

The actual unchanged hero (`de61dc4c…`) was measured at six ±axis limit offsets
in mesh-local rest space. The reproducible report is `baseline-frame-probe.json`.

| Material | Varying-mask triangles | p95 face-normal turn | Max turn | Samples >90° |
| --- | ---: | ---: | ---: | ---: |
| Hair | 53,856 | 10.778° | 178.838° | 300 |
| Body gold/hem | 808 | 83.478° | 122.742° | 207 |
| Silk | 4,291 | 81.203° | 114.021° | 571 |
| Brocade | 1,151 | 81.638° | 177.930° | 162 |

The separate bow gold primitive has no varying masks. Hair has 1,496 baseline
nearly degenerate triangles and body gold 2,000 at the stated 1e-12 cross-length
threshold; these are reported separately, not silently accepted. Angles are
unweighted triangle/sample counts, not pixel visibility or area-weighted harm.
Large changes on tiny triangles need actual rendered diagnosis. A >90° turn
relative to rest alone does not establish topology inversion.

These are deliberately extreme **rest-space stress samples**, not measured
runtime spring paths, skinned normals, collision errors or observed frames.
Actual mesh/visual basis conversion may change the local offsets. No visible
quality or performance improvement has been accepted from these numbers.

## Actual selected reading and decisions

The machine-readable `reading-ledger.json` pins bytes and exact reading scopes.
Cached bodies were independently rehashed. The two newly needed Godot source
files were fetched from permitted `raw.githubusercontent.com` at the pinned
4.6.3 commit using inherited proxy/TLS trust. Runtime network observations were
current but enforcement state `unknown`; no enforced-policy claim is made.
No Reddit retry, other engine survey, source recovery or commercial asset fetch
was performed.

* Robert Nystrom, *Game Programming Patterns*: **selected sections of three
  chapters**, not the full book: Game Loop 373–493, Update Method 200–265,
  Component 184–246 and 469–535. Full bodies remain in scratch; no prose is
  copied into this packet. His mixed license keeps prose under CC BY-NC-ND 4.0
  and qualifying code under MIT. This packet uses original implementation
  reasoning from the reading, not book code.
* Godot 4.6.3: Plane constructor and SurfaceTool normal generation were read and
  minimally adapted with MIT notice. SpringBone description and TwoBoneIK
  description were read as **comparison**, not adopted. SpringBone requires
  nonbranching chains and warns against scaled skeletons/bones; the current
  accepted rig has no newly justified groom chain. TwoBoneIK's virtual skipped
  segments ignore intermediate rotations, so Rama's split legs need an explicit
  compatibility experiment.
* Material Maker 1.6 `weave.mmg` and its MIT license were read in full. The old
  weave combines alternate sine lobes with hard step ribbons; tile repetition
  needs even row/column counts. Hard edges require filtering/mip scrutiny.
  Its cached Godot template still declares Godot 3 SpatialMaterial format 2.
  **No bake or formula was adopted here.** R3-01 owns one original low-amplitude
  smooth warp/weft roughness candidate; there is no duplicate map/tool adoption.

## Cloth/groom implementation contracts

1. Keep zero alpha on scalp, brows, garment attachments and any fixed boundary;
   preserve mask continuity across hem/body duplicates. A zero vertex remains
   fixed, but its incident triangle can still rotate. Do not use alpha as opacity.
2. Derive the shading frame from the actual final displaced/skinned surface.
   For an ideal smooth field x'=x+d f(x), J=I+d⊗grad(f), normals transform by
   J^-T and tangents by J; reorthogonalize while retaining handedness. An alpha
   scalar alone does not provide grad(f). The actual GPU mesh interpolates
   displaced vertices, so blindly applying continuous alpha² derivatives can
   also disagree with its triangles. This diagnostic measures that discrete
   geometry. A screen-derivative flat normal alone would lose authored smooth
   normals; any proposed fix must explicitly preserve the authored frame.
3. Retain one secondary update owner (`player._update_rama_motion`), one
   full-body skeleton writer (`RamaMotion`) and the current analytic springs.
   The spring solution is exact for a constant target during an update; changing
   sampled targets, clamps and reset rules mean it is not automatically identical
   under every frame schedule. Compare shared input tapes at 30/60/120 Hz.
4. Pause holds history; teleport/reset/death clear it. No shader TIME drift,
   duplicated render/physics integration, new bone modifier, or gameplay writes
   are needed for a roughness/groom candidate. Existing cap bounds do not replace
   actual head/cloth collision or moving-light checks.

## R4 support-release and update ownership contract

The Nystrom reading supports an explicit update sequence, not a new component
framework. Player movement supplies the same sampled velocity/basis to body and
secondary presentation. Source shows motion update before secondary and face,
while `SkeletonModifier3D` applies the body pose later. Record the sampling and
pose application clocks rather than assuming function call order equals rendered
pose completion. Keep the 20 Hz ability clock and payload timing independent.

Current `_transition()` clears foot locks; `_apply_contact()` excludes blends
and can relocate a target after 0.36 m error. R4 must log immutable plant IDs and
their original world anchors, contact entry/exit timestamps, gait/state, target
position, correction weight, final foot/joint transforms and authority events.
Measure error against the **original** plant anchor; a moved anchor cannot erase
slip. Separate support, release and swing states. During support retain the
existing <2 mm contact gate; release is explicitly allowed to depart the anchor.
At the release boundary test C0 position and C1 velocity continuity against the
outgoing corrected pose; carry a bounded residual/authored release arc as an
experiment rather than abruptly dropping IK. A partial solver weight is release,
not successful planted contact.

Compare ordinary acceleration, start/stop, reversal, aimed strafe, landing,
draw/release/cancel/death and teleport at 30/60/120 Hz plus bounded hitches.
Record distance/time, speed and acceleration as well as per-frame steps so rate
changes cannot hide discontinuity. Preserve baseline failures. Numerical checks
must precede normal-speed skin/contact footage and independent art review.

## Handoff

R3-01 received weave/normal guidance; R3-08 received anchor and diagnostic
contracts and owns running it on the groom candidate. Root owns runtime
integration, R4 scheduling, source-bound captures and final art decisions.
The tool code, notice, reading ledger, baseline and exact test receipt are this
role's deliverables. The existing stack is sufficient for this isolated workflow;
no environment install/start draft changes were needed.
