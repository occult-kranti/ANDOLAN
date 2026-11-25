# Independent rounds 4 and 5 review

The [first three rounds](independent-review.md) established the character
and playable practice route. These two revisions check the facial and rear
silhouette, the native response on each tail joint, the original ability
animations and their recorded presentation. Keep the three kinds of evidence
separate. The authored tail remains in the Blender studio reel. Native
movement adds a bounded response after those imported animations evaluate.

## Round 4

I opened the actual source-matched studio face and rear for GLB
`12a98de9dce59462cbd866c4e68b0a889ea01825513898f01432c2b5abe98153` and
Blender file `8de0ce422e29dcdb1de242eaf80ac5de05082e855334963f1b44ddc9e530170f`.
The new cuffs clean up the greave edges. The dorsal patch and cloth now read
as separate parts of the costume. Eye shapes read clearly, but the flat black
mouth line and nostrils still look like an applied graphic. The artist used
that finding to revise the muzzle in round 5. The [R4 tail census](independent-r4-tail-curves.json)
checks the exported links and compares all sampled transform data with R3.

The [R4 lifecycle run](independent-r4-tail-lifecycle.json) used the actual
native trial with the R3 model and the first four-joint modifier. All eleven
checks passed after correcting the fixture to count actual typed child nodes.
The run traveled 2.18 m, with procedural pitch/yaw magnitudes of 2.49°, 3.56°,
4.43° and 5.18°. The engine modifier signal supplied 28 observations showing
all four final rotations changing. A vault climbed to 1.55 m. The four
landing responses reached 2.62°, 4.35°, 6.25° and 8.52°. Pausing held the exact
response state and resetting cleared it. Pose protection worked but set the
overlay to zero immediately as the protected cast began. Round 5 tests the
blended entry and still requires zero by contact.

I opened the seven-shot midpoint overview. It showed actual poses on the
packed Blender set. The upright mace came very close to the upper crop
during the guard. The full sequence has adjusted framing. Midpoints provide
preflight evidence only.

## Round 5

The [final raw GLB](independent-r5-glb.json) is
`9de9e032d55685dffd51734bef98c241024283c5d23767646b5c68ca782dec7e`.
The packed Blender source is
`b27582783f7a68f35225cd0545e7e31e3c09762c736da1e6a689cabaa400e589`.
The actual face render shows less stark lips and nostrils and readable eyes.
This is a clear polish gain within the current character style. Dynamic
facial expression and richer fur remain open.

The [raw tail curve check](independent-r5-tail-curves.json) pins all four
links, their parent-child hierarchy and their terminal attachment. The
export contains 105,848 triangles across 17 skinned surfaces. Four joints
have 607, 532, 427 and 1,063 influenced surface vertices and every adjacent
pair blends across a shared set of vertices. Each of the eleven clips carries
nonconstant rotation keys on every link. The canonical decoded curve hash is
unchanged from the [R3 raw baseline](independent-r3-tail-curves.json) and root
translation remains zero. Geometry changes alter the vertex census. They
preserve the actual transform curves by value.

The [R5 lifecycle check](independent-r5-tail-lifecycle.json) passes 12/12 on
the exact new asset and native source. The native actor issues sampled motion
to the modifier. Entering a protected rear cast from a fully weighted run
produces overlay weights of 1.00, 0.85, 0.70, 0.55, 0.39, 0.24, 0.09 and 0.00,
reaching zero after seven 60 Hz ticks. The four applied angles remain zero
through the rear and mountain release windows. Cancel settles, pause retains
the previous response, and all joints reset without a surviving extra modifier.
The previous independent [effects checks](independent-r5-effects.json) also
pass 13/13 on the revised presentation script. They cover the locked warning
mesh, invalid ordering, duplicate events and cancellation. The synthetic
transcript leaves visible effect quality for the native capture.

The unrendered sole audit still measures authored run sole height at about
−1.74 to +0.82 cm relative to the raw plane. A grounded gameplay capsule and
real movement response cannot fix that inherited source animation detail by
themselves. Treat in-game sole contact, authored LOD, physical GPU pacing,
human response and the commercial art target as separate open checks.

## Studio reel verification

The [movie receipt](independent-r5-studio-movie.json) matches all four source
pins and all 120 PNG bytes, preserves each take’s full sampled interval and
checks the encoded H.264 timestamps. Its seven shots show idle, running,
gada, guard, vault, tail and mountain motion over 7.5 seconds at 16 frames per
second. Every decoded frame is distinct within its shot. No frame’s mean
luminance error exceeds 0.534 on a 0–255 scale when compared with its source
PNG. A separate test sequence passed with eight frames and was rejected when
one encoded frame was dropped.

I opened 21 frames decoded from the delivered MP4 across the seven shots. The
new shot framing retains the lifted weapon through the pose checkpoints. The
three-quarter and rear views expose the cloth and tail motion. The authored
vault is in place above the plinth by design. Grain remains visible in this
low-sample software render. Event-driven effects and physical movement belong
to the separate native reel.

## Native reel verification

The [native movie receipt](independent-r5-native-movie.json) verifies all 112
originals and decoded frames at 960×540 and 16 frames per second. The fixed
simulation timestamps advance throughout and the five actual impact events
occur in order. I opened 18 decoded frames covering anticipation, releases,
impact and recovery. The guard shows a distinct shield attached to Hanuman.
Lanka Dahan projects a low rear fan beneath the tail. Mountain Pulse shows a
locked warning circle, a separate visible payload during travel, and a
landing form. The target selection and effect position remain fixed across
the actual Mountain Pulse release at age 0.70 s and impact at 1.15 s.

| Input | Independently viewed decoded frames | Matching native trace phases |
| --- | --- | --- |
| Q | 29, 33, 36 | Windup at physics 127, shield recovery at 142, ready at 153 |
| C | 61, 65, 71 | Windup at physics 247, rear sweep recovery at 262, ready at 284 |
| X | 85, 89, 95 | Windup at physics 337, travel at 352, impact recovery at 374 |

The visible markers align with the observed phases in those samples. The
encode comparison cannot verify contact or motion quality between frames.
The nearby gold target remains oversized at the right in the
opening view, and effects can still blend into bright paving. The 7-second
movie comes from scripted input on the actual native trial at a fixed rate.
Its output is muted. The separate ordinary input route remains in the earlier
review.

## Generated material in the editable Blender scene

I reviewed the actual Cycles render of the new look. The lighting separates
the gada and shoulder bronze from the skin. The generated madder pattern
reads on the legs, where it repeats coarsely at the current scale. Keep it as
an editable material and lighting experiment.

The [independent Blender reopen](independent-r5-lookdev.json) verifies the
actual packed image bytes and the output render hash. The viewport reference
is hidden from the render. The swatch feeds the new scene’s cloth albedo.
The original scene keeps its color source and the two scenes retain the same
cloth normal image, 246 shared mesh or armature datablocks and eleven
actions. This is an isolated studio scene. The native reel uses the R5 GLB
listed above.

Run these checks after importing the current assets:

```sh
python3 games/yuga-native/tools/hanuman-review/tail_curves.py HANUMAN.glb \
  --compare EARLIER.glb --report /absolute/fresh/tail-curves.json
godot --headless --fixed-fps 60 --path games/yuga-native \
  --script res://tools/hanuman-review/tail_lifecycle.gd
```
