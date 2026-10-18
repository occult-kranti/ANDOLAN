# R3-09 independent material and source review

**Bounded source/import checks pass; no promotion approval.** The groom-r6
near/mid/far sources preserve material, sampler, image, rig and clip identity.
The actual imported candidate uses the new scalar cloth texture through the
existing owner and RED channel. No optional frame shader was adopted.

Executed independently on source commit `0437ea91…` and the source hashes in the
reports: 24 source/channel checks, 21 actual imported lifecycle/resource checks,
and 8 additional package/path checks. The imported project is
`/workspace/scratch/visual-round3/capture-candidate-project-r1`, released for
read-only loading by role06. Commands used Godot 4.6.3 headless on CPUs 0,1;
this role performed no editor import or render.

The six cloth surfaces across three LODs share one imported 1024×1024 L8 texture
with 10 mip levels and a 1,398,101-byte CPU image payload. All three groom LODs
bind the existing opaque secondary shader and one 164-bone skeleton. RED channel,
roughness multiplier, finite normalized semantic alpha and new authored tangent
frames pass. Original embedded image bytes are exact. The wrong-channel
counterexample differs by more than 0.6 roughness, so channel validation is
meaningful. Actual GPU allocation and appearance remain separate measurements.

A competing uniform edit makes finish reconfiguration refuse without overwriting
that edit. Repeated configure preserves material identity. A foreign replacement
surface survives finish release; its old binding is reported as invalidated.
The first probe incorrectly required a nonempty conflict list as well, despite
successful preservation. That failed probe/report/log is retained in the packet;
the corrected check accepts the documented invalidated report and still requires
exact foreign material identity.

One **inherited lifecycle defect** is confirmed separately: after another owner
enlarges `extra_cull_margin` to 0.5, `RamaSecondaryMotion.restore_materials()`
resets it to the original 0.0 while restoring its still-owned material. This is
not a groom-r6 regression, but the component does not preserve that later margin
edit. The initial review preserved this failed result; the authorized correction below now addresses it. The baseline shader also still displaces vertices
without transporting TBN; new authored frames do not solve that known dynamic
limitation. The optional transport experiment remains outside this proposal.

The independent R3-14 review validates 65 fixed source records and 24 promotion
files. It also executes matching-byte ancestor-symlink, parent traversal and
absolute-path escape counterexamples, with an accepted direct internal control.
The proposal explicitly remains unpromoted, retains fixed ancestry, and excludes
the unchanged shader/finish/LOD reader from promotion. No concrete identity/path
hole was observed in this bounded review. The exact package/helper/proposal pins
are in `package-review.json`. Geometry clearance and actual art acceptance are
separate gates; R3-10's collar witnesses remain unresolved.

Reproduce from repository root:

```sh
taskset -c 0,1 python3 games/yuga-native/docs/evidence/visual-rounds/round3/role09/audit_source.py
taskset -c 0,1 python3 games/yuga-native/docs/evidence/visual-rounds/round3/role09/review_package.py
taskset -c 0,1 timeout 60s godot --headless \
  --path /workspace/scratch/visual-round3/capture-candidate-project-r1 \
  --script /workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round3/role09/imported_lifecycle.gd -- \
  --report=/tmp/r3-independent-material-fresh.json
```

Reports contain exact source hashes and measured values. Next owners: root and
R3-14 for disposition, role06 for actual pixels, and the focused lifecycle correction below. No asset, ledger, configuration or commit changed in this assignment.

## Focused lifecycle correction

The parent authorized a narrow correction after the inherited counterexample.
`rama_secondary_motion.gd` now records one margin per mesh, restores it only while
its value still exactly equals the stored applied value and the corresponding
mesh/material slots remain owned, and clears ownership on teardown. Readback of
the applied property avoids float-storage precision mistakes. Replaced mesh
resources and foreign materials survive. No response, mask, shader, clock or
skeleton logic changed.

Executed `tests/rama_secondary_lifecycle_cases.gd`: 12/12 checks, including original
margin restoration, external 0.5 and 0.04 values, repeated restore, preexisting
large margin, foreign material, fewer-surface replacement mesh, owner disposal
and already-destroyed mesh. The existing secondary response suite also passes.
`imported_lifecycle_corrected.gd` loads the corrected source by absolute path
against the untouched frozen candidate imports: 22/22 checks pass, including
the formerly failing external 0.5 margin. The original failed adversary remains
in `imported-lifecycle.json`. These are headless tests, not pixel or GPU evidence.

Exact correction source and test pins are in `correction-receipt.json`. Role06
retains the original baseline source; a new candidate freeze must declare this
extra script delta. Root owns final integration disposition.
