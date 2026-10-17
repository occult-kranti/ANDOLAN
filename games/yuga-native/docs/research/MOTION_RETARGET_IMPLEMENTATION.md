# Licensed motion reuse: Rama carry adaptation

This milestone produces an experimental Godot `AnimationLibrary`. Idle and run
adapt source hip, spine and leg motion to Rama's rig while keeping his upper
body in its own lowered bind/rest pose. The nine embedded Rama animations remain
intact. The candidate is **not promoted to gameplay**: actual rendered review
shows open fingers and a rigid carry pose, and run flight, grip, foot locking and
gameplay speed still need artistic and movement review. The firearm-derived aim
sample remains an unpromoted study.

The current library SHA-256 is
`95ffda72b8fc5d4d41e9702ce30918cffb22e75d907545dc5ff28fb01411554f`,
baked and tested against production Rama
`6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`.

The source is the official Godot TPS Demo at commit
`a82f15448e9b015440d3bbdf5e10801b260c4e9f`, asset
`player/model/player.glb`, SHA-256
`16b783ec2e19245d034326d401796b9bd2635de75f4e38917854316abeee4f9c`.
Its asset license is Creative Commons Attribution 3.0, credited to Juan
Linietsky and Fernando Miguel Calabró. The original model, textures, music and
gameplay scripts are not incorporated in this animation library. The adapted
motion is distributed under CC-BY 3.0 with its source and changes credited in
[`TPS-MOTION-NOTICE.txt`](../../assets/animations/TPS-MOTION-NOTICE.txt).

## Four bounded implementation rounds

1. **Source and basis audit.** The imported source has 145 bones; Rama has 164.
   The source's saved/default pose differs from its actual inverse-skin bind
   pose by as much as 1.46 radians among mapped joints. It uses a T-pose, while
   Rama uses a lowered A/ready pose. Simply copying local rotations or applying
   source bind deltas to target bind axes folds the arms incorrectly. The audit
   also found that the inherited 15 Hz source importer discarded part of the
   GLB's authored 24 Hz motion lattice. The isolated importer now uses 24 Hz and
   retains animation suffixes to avoid a source name collision.
2. **Actual retarget and bake.** A matched reference establishes each mapped
   global orientation. The baker reconstructs local rotations in topological
   order against the immediate animated parent, including unmapped twist and
   intermediary bones. It samples at 60 Hz and saves native animation tracks.
   Source root and hip trajectories are exported separately and never drive the
   `CharacterBody3D` or network authority.
3. **Failures and corrections.** Before the workspace replacement, numerical checks found
   run feet hovering 88/142 mm above the floor. A support fit using all 3,798
   actual foot/toe-dominant skinned vertices corrected vertical placement.
   A later 1 ms endpoint probe exposed a real velocity corner despite matching
   endpoint poses. Shared quaternion-log and height tangents fixed that seam;
   the old candidate failed the new gates. Actual rendered review then rejected
   the borrowed upper-body arm swing, despite its numerical passes. The current
   adaptation therefore transfers only ten hip/spine/leg mappings for idle and
   run, with Rama's bind/rest shoulder, arm, hand, head and weapon local poses.
4. **Recovery, handoff and review.** A cloud workspace replacement lost the
   unpublished full-body libraries, the later hero mesh and their old numerical
   reports. The restored production hero, pinned source intake, baker and QA
   were used to generate the current carry candidate and fresh evidence. The
   same implementation agent reconstructed the baker and numerical QA; this is
   **not independent-author QA**. The parent agent supplies the separate actual
   rendered review. Its 236-frame capture keeps the motion/art gate open.

## Artifact and binding contract

| Library animation | Duration | Loop | Intended role |
| --- | ---: | --- | --- |
| `tps_idle` | 15 s | Linear loop | Experimental lowered rest arms, source body rhythm |
| `tps_run` | 0.833333313 s | Linear loop | Source leg/spine rhythm with rest arms |
| `tps_aim_up` | 0.5 s | Held, nonloop | Unpromoted firearm-aim reference experiment |

Load `res://assets/animations/tps_rama_motion_library.tres` into the imported
model's `AnimationPlayer` under a separate namespace such as `tps`. Its
`root_node` remains `..`; tracks address `YugaHeroRig/Skeleton3D:<bone>`. The
library contains 164 rotation tracks plus one visual root-Y position track per
clip. No original animation is renamed or replaced.

```gdscript
animator.add_animation_library("tps", load("res://assets/animations/tps_rama_motion_library.tres"))
# Only after the current artifact passes geometry and rendered carry review:
animator.play("tps/tps_idle", 0.18)
```

For idle/run, the active source mappings are hips→root; spine1/spine2/chest→
spine05/spine03/spine01; and thigh/shin/foot→upperleg01/lowerleg01/foot on each
side. Every other local rotation retains Rama's bind/rest carry pose and
inherits its animated parent. This preserves the weapon's bind relationship;
it does **not** establish a closed finger grip or a finished carry animation.
The actual idle frame shows open, rigid fingers. The aim experiment uses the previous
21-bone mapping against original `fire` at its 25% rotation sample; it does not
solve bow-hand/string contact and must not become the default aim.

The target's local translations and scales retain their rest values except for
the visual deform-root Y offset. That offset combines scaled source hip bob
with support candidates inferred from source foot/toe heights within 25 mm of
their clip minimum. Contact offsets interpolate through flight intervals;
actual sole geometry can raise a penetrating pose but does not force every
flight frame down. The intended minimum model-space clearance is 5 mm; it is
not a maximum foot height or a guarantee that both feet stay grounded. This preserves
segment lengths and root XZ; it is not horizontal foot locking or authoritative
player displacement.

Three symmetric periodic quaternion filters reduce source key corners. At the
loop seam, first and last neighboring quaternions share a signed logarithmic
tangent; root Y shares a linear tangent. A common neighborhood lift preserves
both the tangent and sole clearance. Interior interpolation remains linear /
SLERP. Godot excludes keys after `animation.length` from interpolation, so a
positive-time ghost-key workaround was rejected after source review.

## Evidence and reproduction

The current output inventory is:

- [`motion-retarget-manifest.json`](../../art/motion/motion-retarget-manifest.json): exact model/library hashes, original nine clip names, mappings, durations, solver checks and limitations.
- [`source-target-rig-audit.json`](../../art/motion/source-target-rig-audit.json): complete local/global rests, hierarchy and source bind/default differences.
- [`source-root-trajectories.json`](../../art/motion/source-root-trajectories.json): extracted source motion, never applied to gameplay authority.
- [`support-contact-samples.json`](../../art/motion/support-contact-samples.json): actual all-sole CPU skinning and vertical correction samples.
- [`sampled-local-poses.json`](../../art/motion/sampled-local-poses.json): representative baked poses, explicitly not rendered-image evidence.
- [`full-body-reference-study`](../../art/motion/full-body-reference-study/README.md): historical rejection notes; the old binary evidence was lost, not retained.
- [`motion-retarget-recovered-support.json`](../../tests/evidence/motion-retarget-recovered-support.json): current 35-check reconstructed numerical report, exact runner hash and all-sole run timeline.
- [`motion-retarget-recovered.json`](../../tests/evidence/motion-retarget-recovered.json): earlier fresh 33-check report, before the all-sole diagnostic was added.
- [`motion-carry-restored`](../evidence/motion-carry-restored/): separate actual rendered sequence, selected frames, source hashes and review scope.

Prepare the verified source using the reference importer, then reproduce the
current motion with the pinned Godot 4.6.3 engine:

```sh
python3 games/yuga-native/art/reference-models/godot-tps-player/reproduce_reference.py \
  --destination /workspace/tooling/reference-character
python3 games/yuga-native/art/motion/reproduce_motion.py \
  --reference-project /workspace/tooling/reference-character/godot \
  --work-dir /workspace/tooling/yuga-motion-retarget
python3 games/yuga-native/art/motion/run_motion_qa.py \
  --work-dir /workspace/tooling/yuga-motion-qa
```

The helper copies only model/material/texture dependencies into its own project,
uses task-local XDG paths and a two-thread worker limit, imports there, and runs
our headless baker. It never executes upstream gameplay scripts. An alternate
target requires `--target` and its expected `--target-sha256`; that does not
recover a lost historical target mesh or reproduce a historical hash by itself.

Reconstructed numerical QA verifies unchanged original assets and rests, valid bindings,
actual rest-geometry reconstruction, dense 60 Hz poses, bounded 15 Hz skinning,
bone lengths, finite transforms, root XZ, loop endpoints and 60/240/1000 Hz seam
velocities. The declared run limits are ≤0.05 m/s root-Y and ≤0.25 m/s worst-joint
velocity mismatch at 1 ms. It also checks original fire/defeat transitions into
retarget clips without manually resetting bones. Those zero-blend checks do
not establish production crossfade quality.

The current candidate passes 12 bake checks and 35 reconstructed numerical
checks. At a 1 ms seam probe its run root-Y velocity mismatch is zero and its
worst-joint mismatch is 0.05085 m/s. The QA also detects injected nonfinite
transforms, altered rest axes, borrowed arm rotations, a closed-pose animation
with a bad velocity seam, and an artificial 10 cm whole-pose lift. These are
numerical detector checks, not finished-animation acceptance.

The added run diagnostic evaluates **all 3,798 foot/toe-dominant skinned
vertices** at 51 samples (60 Hz, including the duplicate endpoint), independently
of the baker's stored height values. All 21 source-inferred support samples have
a lowest sole at no more than **5.0012 mm** above the floor. Per-foot minima are
approximately **5 mm**. However, maximum simultaneous clearance of both feet is
**221.906 mm**, at 0.483333 s, and 24/51 samples have both feet above 15 mm. There
are 11 left-foot and 16 right-foot near-floor samples at that diagnostic
threshold. This confirms support compensation exists and flight is preserved;
it does not establish plausible flight or planted feet. Source support labels
are inferred from bone height, not authored contact events. No horizontal
foot-lock or grip test is claimed.

The separate actual render agrees that the run becomes visibly airborne and
that the lowered carry remains stiff with open fingers. The candidate stays
experimental. Historical 44-check reports from before recovery are not current
deliverable evidence. Rendered review remains necessary for shoulder shape,
bow clearance, cloth intersections and perceived motion. An offline capture's
sample rate is not a hardware performance measurement.

Remaining production work includes gameplay-speed matching, horizontal support
locking, dedicated archery draw/release/recovery, cloth/weapon collision review,
and competitive movement testing. A passing retarget bake does not establish
finished hero animation or commercial-game visual parity.
