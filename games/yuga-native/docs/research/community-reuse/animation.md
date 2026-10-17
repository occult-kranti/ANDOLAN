# Animation and character reuse: bounded decisions

Review date: 17 October 2026. YUGA native source
`7c86cd430e2c878b4f5e6ba1b21f562b73fdc32f`, branch
`game/yuga-native-production`. Scope: character authoring, retarget boundaries,
rapid reversal/support release, and the next fifteen-role production packet.
[Source ledger](animation-sources.json) records four repositories, 31 exact files,
licenses, retrieval evidence, executed checks and scratch artifact hashes.

**Keep the accepted Rama rig and motion controller. Prioritize the next authored
face/skin pass; run a separate support-release experiment before introducing any
animation dependency.** Rigify is useful authoring tooling, Godot already provides
relevant comparison APIs, and ozz provides inspectable IK semantics. Availability
of these repositories does not establish better Rama motion or completed art.
No runtime, asset or gameplay file changed in this research packet.

These are primary-source findings. The community worker's new Reddit request
returned HTTP 403 with zero posts/comments; there is no fresh Reddit recommendation
or consensus behind this shortlist. All downloads used the inherited HTTPS proxy
and verified TLS. The startup policy is restricted; environment-status enforcement
was reported as `unknown`, so no claim of verified policy enforcement is made.

## What the actual project permits

The read-only scratch audit parsed the actual `rama-hero.glb`, its separate
`rama_hero_motion.tres`, and the pinned Godot humanoid profile source. Ten checks
passed: one skin with 164 unique bone names, exact name order and parent hierarchy
agreement with the runtime library metadata, nine embedded clips, 23 unique runtime
clips, two intact split-leg chains, the `bowstring` extension, and four full/half
blink targets. The 56-name Godot humanoid profile has **zero exact string-name
matches** with Rama. That establishes an explicit mapping requirement, not that
retargeting is impossible. No bones named hair, cloth or sash were found; naming
alone is not a skin-weight or chain-suitability audit.

The stronger runtime rest-transform checks remain in
[`rama_motion.gd`](../../../scripts/rama_motion.gd), whose `configure()` compares
names, parents and rest matrices before allowing playback. The scratch audit did
not independently establish matrix equivalence, evaluated skin deformation or
successful retargeting. The accepted hashes are:

| Input | SHA-256 |
| --- | --- |
| `assets/heroes/rama-hero.glb` | `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5` |
| `assets/animations/rama_hero_motion.tres` | `1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8` |
| `scripts/rama_motion.gd` | `4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1` |

`RamaMotion` is the single full-body `SkeletonModifier3D`; it pauses the old
AnimationPlayer and samples the original 23-state library itself. Generic
AnimationTree/root-motion examples cannot be inserted without an explicit ownership
change. Gameplay controls release, damage, cooldown and movement. Its upper/lower
leg pairs are actively rotated together, followed by support IK and string contact.
Changing the sampled library or adding another skeleton writer affects this order.

The existing face is a small native orbital partition with four blink morphs and
one exclusive runtime writer. Preserve its shared UV/normal/tangent boundary, skin,
morph ordering, full/half corrective arc, pause/reset/teleport/death behavior and
single-owner guard. The body already contains many anatomical face bones; that is
not evidence that a production brow/jaw/lip performance has been authored.

The secondary system already provides bounded, authored-mask shader motion with
analytic springs: cloth limit 75 mm and hair limit 18 mm. It has no cloth collision
or strand solver. The rejected 800-triangle wisps remain unbound. Better authored
hair masses, garment form and weighting should precede extra secondary motion.

## Exact source decisions

| Source and pin | Specific inspected boundary | Decision and cost |
| --- | --- | --- |
| **ANIM-01: Blender 4.3.2 Rigify**, [`32f5fdce`](https://github.com/blender/blender/tree/32f5fdce0a0a571a39198edf8d7b5d719bf59f2c/scripts/addons_core/rigify). GPL-2.0-or-later. | `utils/animation.py` implements FK/IK snap/bake operators; `rigs/limbs/limb_rigs.py` generates control, mechanism and deform chains; face/eye and tail rig modules were inspected. This is the release-matched bundled source, not the stale `blender-addons` mirror. | **Tool-only.** An optional copied-scene control rig can help author original reversal/settle poses and bake them onto the exact original deform skeleton. Mapping, pole axes, segmented legs, bow sockets and constraints all need validation. Do not replace Rama's 164-bone rig with generated Rigify bones. No Blender rig generation was executed here. |
| **ANIM-02: Godot 4.6.3**, [`35e80b3a`](https://github.com/godotengine/godot/tree/35e80b3a8822a9df9be390814b62f44c0a9c69e8). MIT. | [`TwoBoneIK3D`](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/doc/classes/TwoBoneIK3D.xml) treats skipped segments as straight virtual bones and ignores their rotations. [`RetargetModifier3D`](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/doc/classes/RetargetModifier3D.xml) overwrites mapped target poses; global mode needs matching lengths. [`SpringBoneSimulator3D`](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/doc/classes/SpringBoneSimulator3D.xml) requires nonbranching chains and warns about scaled skeletons. | **Native comparator first; retarget authoring only; spring-chain adoption deferred.** Compare the existing solver with a native isolated baseline before an external port. No need for a per-frame retargeter when the shipped clips already match the rig. SpringBone is conditional on accepted geometry and a separately justified chain/skin contract; do not add bones merely to unlock it or block the face pass on it. |
| **ANIM-03: Godot IK demo**, [`b761b4cd`](https://github.com/godotengine/godot-demo-projects/tree/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/3d/ik). Repository MIT. | `project.godot` declares **4.7**, and repository master targets the development engine. The runner uses `SkeletonIK3D`, deprecated in our 4.6.3 source. SADE FABRIK sets a 10 mm tolerance and ten-iteration cap. | **Inspire debug visualization; defer direct import.** Target/pole/chain displays are useful. Ten-millimetre solver tolerance does not satisfy Rama's retained two-millimetre contact check. No demo model, textures, scripts or motions were imported. Model README gives scale context but no distinct license clarification; a future asset transfer needs its own notice review. |
| **ANIM-04: ozz-animation 0.17.0**, [`744eb9d9`](https://github.com/guillaumeblanc/ozz-animation/tree/744eb9d99f606eda849acb0b1204f7a3dc20bca1). MIT. | [`IKTwoBoneJob`](https://github.com/guillaumeblanc/ozz-animation/blob/744eb9d99f606eda849acb0b1204f7a3dc20bca1/include/ozz/animation/runtime/ik_two_bone_job.h) returns local correction quaternions, softens reach and exposes correction weight/reachability. Intermediate joints stay fixed. The foot-IK sample orders target, pelvis and IK corrections; it is not a planted-foot ownership or inertial-transition system. | **Actual scratch-only source use; defer runtime port.** A small C++ fixture adapted upstream test/FK reconstruction and directly compiled the selected upstream solver. Its useful lesson is explicit release/reach semantics. A new C++ extension, importer, serialized animation format and platform packaging have no established benefit for the current one-hero defect. |

License boundaries are separate from technical compatibility. Preserve MIT notices
for any copied ozz/demo/engine code; the scratch probe retains ozz's notice. Copied
Rigify code and generated rig UI scripts require their GPL treatment. Merely using
an authoring tool does not supply rights to an external model or motion pack.
Existing MakeHuman anatomy/pose data has its own retained CC0 ledger; the historical
TPS motion study has separate attribution and is not the current original motion
library. No animation dataset, commercial character, trained model or model weights
were acquired in this work.

## The next motion experiment is support release

The existing [reversal rejection](../../evidence/visual-campaign/motion-reversal-review/REVIEW.md)
is still authoritative. Its archive and current-source hashes were independently
verified here: 22 members, zero accepted reversal prototypes. The stored 120 Hz
measurements are **161.919 mm** maximum joint-origin step for the ordinary
38 m/s² accelerated fixture and **912.671 mm** for instantaneous adversarial
heading changes. These are retained measurements, not rerun gameplay results.
The projection candidate worsened ordinary motion to **265.532 mm** and moved the
support anchor as much as **46.299 mm in one stress frame** despite tiny numerical
contact error.

The code exposes a concrete discontinuity boundary: `_transition()` clears both
foot locks; `_apply_contact()` disables locking during transitions and may relocate
a target beyond 0.36 m; same-gait directional changes can rotate the stride without
a gait transition. Smoothing heading or softening IK reach alone does not provide
a continuous transition from a planted foot to an authored swing pose.

The Round 4 animation owner should first instrument the unchanged controller and a **separate native
TwoBoneIK3D baseline** on copied inputs. Add a proposed `planted → releasing → swing`
presentation state to only one scratch candidate, preserving the original world
anchor while classified as planted. Once releasing, measure target error and foot
velocity honestly as release behavior. A bounded pose/velocity residual or authored
release arc is a candidate, not an accepted solution. Do not conceal slip by moving
the lock target and then measuring error to that moved target.

The comparison must retain ordinary player acceleration and the existing stress
fixture at 30/60/120 Hz, fixed aimed facing, start/stop, both strafes, draw/release,
hit/cancel/death, teleport and landing. Record full-body joint speed/acceleration,
release-boundary steps, plant duration, world-anchor drift and correction magnitude,
with exact event clocks and source hashes. Keep per-rate baseline values; an
absolute per-frame step alone changes with sampling rate. Require no ordinary-case
regression, no new mid-stance replant/anchor drift, retained sub-2 mm planted contact
and unchanged authority events before scheduling the normal-speed skin/contact
reel. A better headless number cannot close that render gate.

The scratch ozz probe demonstrates why labels matter:

| IK correction weight | Reported reached | Measured target error | Meaning |
| --- | --- | --- | --- |
| 1.0 | true | 0 m at printed precision | Synthetic two-bone full correction reaches its target. |
| 0.5 | false | 0.221597940 m | Partial correction is a release/blend; it is not planted contact. |
| 0.0 | false | 0.447213620 m | No correction; endpoint remains at its original pose within 0.000000060 m. |

Four cases passed, including rejection of an unconfigured job. The fixture uses
unit-scale synthetic joints, no Rama skin, no animation stream and no authority.
This verifies actual upstream API behavior, not a measured improvement to YUGA.
There is no claim that ozz supplies inertialization or solves release scheduling.

## Next-goal changes for the canonical fifteen assignments

These recommendations map to the exact IDs and titles in
[VISUAL_ROUND2_TASKS.json](../../VISUAL_ROUND2_TASKS.json). They refine its planned
face/skin round, not a new set of role numbers or executed assignments. The body
support-release investigation remains the separate Round 4 motion workstream;
secondary hair/cloth remains conditional Round 3 work. Neither blocks this face pass.

Use the existing four phases: A freezes baseline/context/source evidence; B makes
isolated material/light/form/deformation candidates; C captures and independently
reviews them; D corrects demonstrated defects and makes source-bound decisions.
Rotate fifteen assignments through six workers plus the lead. R2-06 alone owns
heavy Blender exports/imports/renders, coordinated with each asset owner; do not
activate concurrent writers on the shared hero.

| Canonical assignment | Concrete next output from these findings | Dependency / acceptance |
| --- | --- | --- |
| R2-01 Skin material artist | One-variable skin candidate retaining original maps, UVs and authored palette. | R2-06 baseline and R2-07 provenance; material appearance cannot conceal eyelid deformation. |
| R2-02 Face-context artist | Freeze close and ordinary-camera backgrounds against light stone, foliage and indigo/gold in both worlds. | R2-06 camera contract; use existing architecture. |
| R2-03 Lighting diagnostician | Compare face/ear/scalp/chest shading with accepted shadow bias retained as control. | R2-02 context and R2-06 capture; keep detached contact and eye-socket failures explicit. |
| R2-04 Facial action-context designer | Exact blink/aim/draw/release/cancel shot list using existing five action timelines. | Current authoritative action events; separate diagnostic effects-off and normal effects-on takes. |
| R2-05 Facial deformation animator | Test full/half eyelid morph arcs and head/neck poses on the R2-08 candidate; correct only demonstrated failures. | R2-08 form freeze and R2-04 fixtures; retain unique writer, pause/reset/cancel and unchanged body locomotion. |
| R2-06 Capture engineer | Source-pinned baseline/candidate views plus continuous imported face/action footage. | Baseline can precede candidates; candidate capture waits for frozen manifests. Sole heavy slot. |
| R2-07 Skin-source researcher | Pin existing reconstruction, CC0 pose data, rig/rest/morph contracts and exact optional Rigify source before proposing authoring use. | R2-01/R2-08 input questions; no external rig or animation pack is required for this pass. |
| R2-08 Principal facial-form artist | One copied editable face candidate with a bounded edit mask, stronger principal planes and exact body/face boundary. | R2-07 source audit, R2-06 closeups and R2-01 controls. Rigify controls optional; no skeleton replacement or hair-wisp detour. |
| R2-09 Independent material reviewer | Inspect actual decoded channels, binding/restore lifecycle and paired skin pixels. | R2-01/R2-07 manifests and R2-06 raw frames; reject improved beauty-lighting alone. |
| R2-10 Independent face-motion reviewer | Counterexamples for lid penetration, boundary cracks, intermediate-frame popping, duplicate writer and reset/cancel drift. | R2-08/R2-05 candidate plus R2-06 continuous evidence; do not close body reversal from face tests. |
| R2-11 Independent face/action-context reviewer | Verify eyes/lips remain coherent during all five actions and reduced-effects/motion settings. | R2-04 exact-event fixtures and R2-06 normal captures; no new VFX or release timing. |
| R2-12 Independent lighting/context reviewer | Same-camera and moving-camera review in courtyard/Confluence day/night with contact shadows visible. | R2-02/03/06 artifacts; no courtyard-only transfer of acceptance. |
| R2-13 Face resource/performance engineer | Account for morph buffers, materials, LODs and exactly one face/skeleton writer; exercise load/reset/unload. | R2-14 integrated candidate; physical-GPU performance remains a separate gate. |
| R2-14 Integration/build engineer | Freeze reviewed inputs, validate 164 names/parents/rests, nine embedded clips, separate 23-state library, skin/morph boundary and writer ownership. | R2-01/05/08 manifests and lead-owned integration contract; structural audit is supporting evidence, not full deformation acceptance. |
| R2-15 Independent face art director | Inspect every required raw frame and continuous take; accept or reject precise forms, skin, motion and limits. | Completed independent reviews and current-source capture identity; no commercial-quality claim from task counts or passing scripts. |

For the separate VRF key-reduction experiment, original-key agreement is
insufficient: densely sample between retained keys and across the looping seam,
check quaternion angular error and chained endpoint amplification, and preserve
bows/soles at action/contact milestones. A smaller candidate file is not evidence
of better animation. Do not replace the existing constant-track pruning or runtime
library solely because an offline reducer passes its own numeric tolerance.

## Executed evidence and remaining gates

- `python3 .../motion-reversal-review/verify.py --native games/yuga-native`:
  passed immutable archive and current-source verification; motion issue remains open.
- Scratch `audit_rama_contract.py`: ten structural checks passed on actual inputs.
- GCC 14.2, `-std=c++17 -O2`, compiled actual pinned ozz `ik_two_bone_job.cc`
  and `simd_math.cc` with the adapted scratch fixture; its four cases passed.
- Four primary repositories and 31 selected files were read and hashed. This is
  not a full security audit, dependency acceptance or compatibility certification.

The exact compiler command, reports and scratch hashes are in
[animation-sources.json](animation-sources.json). Scratch evidence lives under
`/workspace/scratch/community-reuse/animation/`; it is not a shipped dependency.
The first scratch compile lacked `<initializer_list>` and the first `.tres` reader
expected the wrong array wrapper; both were corrected before the reported passing
runs. `cmake` is absent; the full ozz CMake build and upstream test suite were not run.
The initial Blender license URL `COPYING.txt` returned 404; `COPYING` and the linked
GPL text were retrieved successfully.

No Blender/Godot engine, import, retargeted pose or renderer was run for this packet.
No actual visuals or input were newly reviewed. Next owners are R2-01/R2-08 for the
face/skin goal, R2-05/R2-10 for deformation/review and R2-14/R2-15 for the frozen
integration/art decision. The separate Round 4 animation owner owns future release
evidence. Hair/cloth chains, more expressive face performance, normal-speed
continuous contact, human feel, online authority and physical-GPU cost remain
separate unclosed gates.
