# R3-05 secondary motion and frame-transport experiment

17 October 2026. Product: YUGA native. Source commit
`0437ea91edf6989ff78c1eeadb3661f4825b60f2`.

**Decision: retain current motion and canonical shader.** A single shader-only
experiment is staged for R3-06/15 to compile, capture and independently judge.
The focused test is now in `tests/visual_round_secondary_cases.gd`.
No default visual improvement is accepted here. No gameplay/action clocks,
skeletal writers, alpha weights, materials, mesh data or asset defaults changed.

## Measured motion

The existing component suite passes **42/42** checks. The new suite passes
**24/24**: ten mathematical frame cases and fourteen current-component movement
checks. The canonical test has explicit `--mode=baseline` (14 live-component checks)
and `--mode=candidate-math` (24 including CPU mathematical oracles); both modes
were rerun after promotion. The earlier movement-only receipt also contains 14/14 checks. Receipts and
logs in this directory are from executed commands, not projected outcomes.
One initial GDScript test failed parsing because an integer loop variant needed
an explicitly typed Vector3; its log is retained. The corrected test ran fully.

The six-second shared tape includes starts, stops, continuous reversal, finite
yaw wrap, airborne/grounded transitions, and common 30 Hz observation times.
The actual component states are recorded at every half-second in the JSON.

| Comparison | Maximum cloth difference | Maximum hair difference |
| --- | ---: | ---: |
| 30 / 120 Hz | 0.880 mm | 0.516 mm |
| 60 / 120 Hz | 0.294 mm | 0.177 mm |

Observed largest offsets across this tape are 37.302 mm cloth and 8.327 mm hair,
below their 75/18 mm bounds. A 100 ms constant-target update differs from twelve
120 Hz updates by 8.38e-9 m cloth and 1.60e-9 m hair. Pause preserves the complete
report and resumes identically to an unpaused-call twin. Teleport, explicit
generation reset, death and respawn clear inertia. Oversize delta refuses catch-up.
Zero-alpha anchors remain exactly fixed. No time-step or reset defect was found
in these checks, so no runtime spring change is justified by this packet.

These are **current-component integration examples on synthetic movement input**,
with a small valid semantic-mask material fixture. They are not recordings of
human input, final skinning, collision, moving-light appearance or frame time.

## Actual clock and mask contract

`project.godot` selects 60 physics ticks/s. `player._physics_process()` validates
the step, moves/rotates the visual, then calls `_update_rama_motion()` once.
That method samples the current velocity, position and visual yaw for the body
and secondary presentation. Secondary has no autonomous `_process()` or
`_physics_process()` and owns only its material uniforms. RamaMotion's final
pose is applied later through `SkeletonModifier3D._process_modification()`.
Function call order therefore does not certify rendered pose completion.

The analytic critically damped solution is exact for a target held over one
update. Sampled targets, turn-rate clamp and reset events remain part of the
time-partition behavior. Rendering hitches do not directly change the fixed
physics delta. The body/ability clocks and authority events are untouched.

The shader still displaces by `secondary_offset * alpha²`; white RGB is not
color tint and alpha is not transparency. The R3-08 groom owner confirmed
new scalp/crown/temple vertices stay anchored, only lower nape ramps to .78,
and original topknot retains its earlier masks. R3-01 roughness remains independent.
No gradient or new bone channel is added.

## One staged shader candidate

Overlay source:
`/workspace/scratch/visual-round3/role-05/candidate/rama_secondary_cloth.gdshader`

SHA-256: `701b86520ff2763e0eaf4a4c0762c84f6a1d0cc82240ac6c021321009c0659d0`.

The candidate carries the already-posed pre-displacement vertex in view space.
At each fragment it compares the two triangle differential normals and applies
their shortest-arc proper rotation to **all three authored smooth TBN vectors**.
It retains each vector's length, their mutual angles, smooth-normal deviation
from the geometric plane and mirrored tangent handedness. It does not replace
the authored normal with a flat derivative normal. The neutral uniform bypasses
transport. Collapsed/ill-conditioned differential frames and near-opposite
normals retain the authored frame rather than dividing by a near-zero value.

This is **rotation transport**, not a complete inverse-transpose shear model.
The fallback thresholds can introduce transitions, and tiny near-degenerate
triangles can still have unresolved lighting. It does not repair topology,
collision, skin weights or the unchanged geometry. No universal improvement or
performance claim follows from its mathematical tests.

The independent geometric counterexample fixes two triangle points and moves
the third 75 mm: its plane turns atan(.075) = 4.289153° while the baseline normal
does not. The transport aligns its geometric normal and retains the original
smooth-normal deviation. Identity, uniform translation, both handedness signs,
collapse, near-collinearity, near-opposite fallback and rigid view covariance
pass CPU checks. This proves the proposed operation's invariants in those
examples; it does not execute the staged GLSL on a GPU.

## Godot source-space inspection and unresolved identity

The current upstream `4.6.3-stable` tag resolves with `git ls-remote` to
`35e80b3a8822a9df9be390814b62f44c0a9c69e8`. Source inspected:

- `servers/rendering/renderer_rd/shaders/skeleton.glsl`, lines 248–309:
  skeleton compute transforms vertex, normal and tangent, then writes the
  destination vertex buffer.
- `servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl`,
  lines 349–356, 420–499, 1212 and 1250–1280, 1350–1385:
  user `vertex()` runs on the incoming local vertex; modelview conversion occurs
  after it; the interpolated vertex and authored shading frame arrive in view
  space before user `fragment()`.

The candidate's `MODELVIEW_MATRIX * VERTEX` before displacement therefore shares
the final fragment frame under this inspected Forward+ implementation. It does
not assume unposed rest coordinates or use a geometric rest normal.

**Identity limit:** both installed engine paths report
`4.6.3.stable.official.7d41c59c4`; fetching source at that reported commit returned
404. The upstream release tag resolves to the different commit above. This
packet preserves the mismatch and does not certify that the inspected tag is
the exact binary source. Sources are cached/hashes pinned; no engine was replaced.
An actual rendered skinned fixture remains necessary before promoting the shader.

The source reads informed original experimental code; no engine code was copied.
The existing cloud toolchain was sufficient; no install/start draft was needed.

## Commands and next owner

From `/workspace/ANDOLAN`:

```sh
godot --headless --path games/yuga-native --script res://tests/rama_secondary_motion_cases.gd -- --report=/workspace/scratch/visual-round3/role-05/baseline/component-cases.json
godot --headless --path games/yuga-native --script res://tests/visual_round_secondary_cases.gd -- --mode=baseline --report=/workspace/scratch/visual-round3/role-05/baseline/canonical-motion-tapes.json
godot --headless --path games/yuga-native --script res://tests/visual_round_secondary_cases.gd -- --mode=candidate-math --report=/workspace/scratch/visual-round3/role-05/candidate/canonical-math-and-motion.json
```

R3-06 received exactly one overlay: replace only the shader in an isolated
stage. Keep the paired assets, texture choices, lights, camera, pose times and
actual secondary uniform path identical. First establish shader compilation
and a skinned known-plane control with the running engine; then record matched
normal-speed starts/stops/turns with rear mantle and side hair visible. Include
neutral and normal-mapped material views. Use the recorded runtime component
offsets rather than treating six-axis maximum probes as typical motion.

R3-15/root must decide from the actual images/clip whether this limited transport
improves the rendered defect without destroying authored smoothing or causing
flashing at fallback boundaries. No import, GPU capture, actual image or human
input review was performed by this role. Canonical runtime remains unchanged;
the shader is neither accepted nor rejected on visual grounds yet.
