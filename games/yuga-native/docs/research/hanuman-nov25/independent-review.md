# Hanuman independent review

Baseline `7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch
`game/yuga-native-production`. The attached 42-page *Mythic 3D Hero Design
Pipeline* has SHA-256
`d6970a5e89f9153cfde9ee596c7cfaa3793eec2869db66273be5f64e6827d05a`.
Its Hanuman direction calls for a broad silhouette, an expressive Vanara face,
matte vermilion and warmer metal, legible saffron fabric, a curved tail and a
fluted brass gada. It also proposes a four-slot, non-firearm combat kit.
That portion guides the review. The report describes a separate Satya/UE5
pipeline and speculative tooling. Existing YUGA runs on Godot.

At baseline, the native game provides Hanuman’s Mountain Pulse as an invocation
practice projection from Rama. Its preparation and travel are 0.70 s and 0.45 s.
The projection leaves the avatar in place. Browser Hanuman has an existing dash,
heal and area payload. Neither baseline establishes a native playable Hanuman
mesh with weapon contact and visible motion.

| Gate | Evidence required | Round 1 decision |
| --- | --- | --- |
| Identity and material | Original front, face, rear and actual gameplay views. The face reads as expressive Vanara, the curved tail separates against the body, and the gada has an intelligible grip. Matte fur/skin and fabric retain separation from burnished metal without relying on bloom. | Art candidate pending |
| Export and rig | Exact GLB and Blend pins. Raw GLB verifies bounded indices, weights and embedded resources. Godot import verifies mesh/skin survival and camera transform. Body, gada grip, stance and tail remain coherent across the sampled actions. | Baseline only |
| Ability clarity | Normal inputs reach the actual runtime. Anticipation and aim footprint agree with payload geometry. Cover, range, friendly units and interruption are checked on the receiving system. | Baseline invocation only |
| Motion | Contiguous excerpts cover entry, contact, recovery and cancellation. Visually inspect hand/weapon alignment, sole contact and tail/cloth penetration. Check reset restores neutral pose. | Unrun |
| Production graphics | Same-source actual game frames with combat effects, plus measured physical GPU pacing and human gameplay review. | Open |

The trial sticks to finite, falsifiable acceptance. Raw GLB admission and image
review answer different questions. A beautiful offline render can pass as
portfolio evidence while in-game presentation and animation remain open.

## Round 1 model review

I opened the prior browser hero’s [full model](../../../../yuga/art/previews/hanuman-actual-model.png)
and [face](../../../../yuga/art/previews/hanuman-actual-face.png). The base face
has a small muzzle and large flat cheek pieces. Chest cloth breaks around the
neckline. The gada provides a recognizable weapon, and the tail only surfaces
as a small hook from the front. The prior GLB has 52,472 triangles, ten skinned
surfaces, a 163-joint skin and nine clips. It is a structural starting point.

The independently read new R1 GLB `62f58b7b68dcb99515d8c2bb488b29706772180dc1e94c63b645a83cda31f281`
had 141,764 triangles across 16 skinned surfaces, 167 joints and nine clips.
Its copper body makes real use of exported vertex paint. I opened the beauty,
face and rear Blender renders. The long curved tail and fluted gada were
clear. The separate rounded chest plates and detached shoulder shapes softened
the intended broad silhouette. The face and eyes retained a mainly human read,
and the cloth edges broke against the legs. I rejected this appearance as the
target and proposed a continuous chest piece, seated shoulders, a stronger
muzzle and a cloth pass.

## Round 2 model and gameplay review

GLB `8526f2b784f57ebcd228adeecbedb87828ed848b6d9e0140cdee8c5691af7342`
and Blender file `07eebbfd4b36b8db4dc5970dae9ee66377e753c7418ca86aeb1d6ce16738f493`.
The export now carries 96,988 triangles, down 31.6% from the preceding build.
All 16 surfaces have valid positions, tangent streams, bounded triangle
indices and normalized skin influences. The GLB has 14 embedded images, a
167-joint skin and eleven ordered clips. All eleven have four changing tail
rotation tracks and no root translation delta. Gada-grip and tail-tip nodes
are present. This inventory alone leaves deformation and contact open.

The revised beauty render now reads as a broad warrior with a continuous
bronze chest piece, stronger muzzle and better-seated pauldrons. It retains
broken cloth edges around both hips and the center panel, plus a visible gap
under the feet in the studio pose. I asked for more clearance and shared
weights on the cloth and trim, and an explicit sole-contact check.

Source review showed the original stage had mapped Mountain Pulse to the
existing leap clip and Lanka Dahan to the existing mountain clip. The revised
kit and GLB provide purpose-specific `tail_sweep` and `mountain_pulse` clips.

The [16 authority checks](independent-behavior.json) used production
`RamaPracticeArmy`, `RamaPracticeTarget` and `HanumanCombat` at 20 Hz. They
verify primary team, range and angle; thin-wall occlusion; invalid input;
ultimate timing, cancellation and a capped ally heal; vault-owner veto;
ward expiry; damage only while a rear target stays exposed; reset during
a receiver callback; and isolation of authority from changed event payloads.

The [13 presentation checks](independent-effects.json) used the actual effects
script with a synthetic transcript. The sampled outer warning mesh matches
the locked 5 m radius and 0.15 boundary cosine after rotation. Forty burn ticks
dispatch one release sound total and add no nodes. Invalid timing, premature
end, duplicates and stale receipts fail cleanly. A cancelled cue hides
immediately and frees on the following frame. The test waits for the dummy
audio driver to process stop commands before teardown. It does not measure
sound quality or rendered shader appearance.

Repeat the checks from the repository root after native imports:

```sh
godot --headless --path games/yuga-native --script res://tools/hanuman-review/behavior.gd
godot --headless --path games/yuga-native --script res://tools/hanuman-review/effects.gd
python3 games/yuga-native/tools/hanuman-review/audit_glb.py CANDIDATE.glb \
  --requires-skin --report /absolute/fresh/review.json
```

The [raw auditor control receipt](independent-glb-controls.json) pins the
canonical native Rama input and records six adverse cases rejected. Separate
native captures and sequential visual checks determine the final disposition.

## Round 3 studio review

The [new raw asset receipt](independent-glb.json) accepts the packed
97,818-triangle GLB `76381c5c5e3a1fd6bba7367903452be7d5eb210a35b9195d411c76e651669d9d`.
The editable Blender source is
`d42b116d16568f2a6a8601670a52d5b8448f0fac495a131bc506b05615d0ccb4`.
I opened the unfiltered Blender beauty, face and rear along with the denoised
beauty. The corrected cloth separates from the legs with continuous trim.
The feet appear seated on the raised plinth from both directions. The broad
bronze shell, vermilion accents, mace fluting and curved tail hold a readable
silhouette. Studio asset review accepts this build as a downloadable
character candidate. The closer portrait still shows simplified eye,
eyelid and fur forms. Subtle facial animation, richer materials and
production gameplay fidelity remain open.

The [sole-height receipt](independent-foot-clearance.json) independently
evaluates 2,866 weighted foot vertices at 25 times in each actual GLB clip.
Bind-pose soles are within 0.65 μm of the zero plane. The lowest moving foot
has these sampled height ranges relative to that plane:

| Clip | Range |
| --- | --- |
| Idle | +0.73 to +1.38 cm |
| Main strike and guard | +1.03 to +1.06 cm |
| Tail Sweep and Mountain Pulse | +1.05 to +1.06 cm |
| Run | −1.74 to +0.82 cm |
| Leap and jump | +1.06 to approximately +29 cm |

The earlier Blender plinth was 2 cm below the zero plane, and the neutral
idle sample adds 1.06 cm. That explains the prior visible studio gap. The R3
plinth measures +1.168 cm, seated against the artist’s actual posed sandals.
The inherited running animation still moves through the raw plane by up to
1.74 cm in these samples. The numerical checks do not constrain how studio
camera resolution, actual ground or character interpolation expose it.

To repeat the deformation diagnostic, use the same GLB from the source
receipt and run:

```sh
OPENBLAS_NUM_THREADS=1 python3 games/yuga-native/tools/hanuman-review/foot_clearance.py \
  CANDIDATE.glb --report /absolute/fresh/foot-clearance.json
```

## Native capture R1

The [native receipt review](independent-native-r1.json) matches all 11
request-driven PNGs to the driver’s hashes. The exact R3 GLB was loaded into
the normal Forward+ trial, which was selected from the launcher and exited
through its ordinary title and Quit buttons. Godot exited with status 0.

I opened the title, selected mode, intro, ordinary idle and all five impact
stills. The selected launcher mode changes the description and entry button
while its established stage still names and shows Rama. Hanuman appears in
the trial intro and remains recognizable from behind by the mace, curved
tail and vermilion cloth. The five inputs read clearly on the trial HUD. The
ally target and its large label are too close to the introduction camera and
the left of the normal combat view. The software-rendered courtyard remains
flat and pale compared with the Blender studio lighting.

All five inputs began, released and reached their authority impact event.
The ward visibly applied 48 shield to Hanuman. Vault began an accepted
movement sweep. Mountain Pulse delivered three 65-damage target receipts.
Gada and Lanka Dahan were valid misses, traced to a test driver absolute
pointer move while captured that turned the actor nearly 88° from the
initial direction. Their warning geometry is visible. This fixture leaves
real primary and rear damage to the subsequent route and the independent
receiver tests. These stills establish neither continuous contact nor
physical GPU performance.

## Native capture R2

The [corrected route receipt](independent-native-r2.json) matches all 11
request-driven PNG hashes and all 13 recorded source paths to the current
bytes. Ordinary mouse-button edges replace the captured-pointer warp.
The actor retains facing down the courtyard for the main attack. Native
Quit completes with status 0 and the engine log has no errors.

| Input | Observed result |
| --- | --- |
| LMB | Gada reaches one forward target for 34 damage. |
| Q | The fan and raised palm read, with 48 shield on the HUD and caster receipt. |
| E | The actor rises to 1.07 m in the captured frame and sweeps 4.56 m horizontally before collision. The next grounded sample is within 1 mm of zero. |
| C | Rear sweep hits for 28. The previously hit target then reads 27.6 of 90 in the snapshot, showing one 0.4 damage tick before capture. |
| X | After reset, the locked disk hits three targets for 65 each. |

The corrected lighting gives the reused courtyard better separation from the
hero and restores a blue sky behind the gold arch. I viewed the intro,
ordinary camera and impact image for each input. The warm bronze and red drape
read in the active scene. A large close target and label can still occupy the
right side of frame, especially on the rear sweep. Continuity through the
full action sequence, authored LOD quality, crowded-match readability,
audible listening and physical GPU pacing remain unqualified.
