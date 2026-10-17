# R2-05 facial deformation handoff

Native YUGA baseline: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
This role changed only the new test and role05 evidence. No runtime writer,
default asset, rig, animation library, or shared ledger was changed.

The actual imported baseline passes **73/73 runtime assertions**, with 37
sampled rest, blink, combined effort, aim-extreme, action, recoil and cancel
poses. The real `courtyard.tscn` player, face writer, motion controller and
five gameplay cast entry points execute. Authority emits each release; the
test never calls `release_action` or `_publish`. This is automated execution,
not human input or receiver-damage acceptance.

The existing driver is the only morph writer. Actual paired partial/full
blink samples exercise `max(blink, effort * 0.14)` and the full/half target
weights `max(0, 2*w-1)` / `1-abs(2*w-1)`. Real scene pause preserves all four
target values and head/neck poses; reset restores zero clocks/targets;
teleport clears expression; cancellation fades effort without a release.
The runtime keeps 164 bones and the separate 23-clip library. Role08's
source-equivalence checks retain the nine embedded GLB animations.

## Geometry evidence

The independent analyzer evaluates **55,363 actual imported vertices per
sample**, including face, body skin, lips, sclera, iris and pupils. It applies
the actual imported skin weights, inverse binds, and sampled global bone
poses. There are 37 actual baseline runtime samples plus 13 explicitly
offline individual-left/right and combined partial/full target cases. The
offline combinations never write a runtime mesh.

Final candidate source replay uses the candidate's exact GLB position deltas
with the existing imported skin arrays and runtime poses. It verifies exact
source topology, skin and morph invariance before replay. This proves a
bounded source-deformation result; candidate Godot import and candidate
pixels remain separate checks owned by R2-06.

The baseline has zero measured gaps at all 146 face/body attachment witnesses
and 226 original lip/body witnesses in the sampled poses. The source held
ring is extracted from the actual native quad blend: 146 boundary vertices
plus incident selected quads give 288 held source vertices. This is stronger
than inferring that ring from triangulated export adjacency.

The r5 candidate (`2dbd60ae...`) failed the held-ring requirement: four rest
vertices moved by at most **9.876 micrometres**, while their morph deltas and
all 146 attachment positions stayed zero. The failure is retained in
`candidate-r5-source-deformation.json`. R2-08 corrected the rest-form mask,
producing r6 (`140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a`).
The corrected r6 source replay passes **16/16** checks, including all 288
fixed ring vertices and the 50 sampled combinations. R2-10 independently
reproduces the correction. No new corrective morph or blend adjustment was
justified.

The checks cover finite posed positions, attachment continuity, corresponding
face-triangle orientation, actual eye-surface closure at 63 frontal rays per
eye, and vertex inset into a convex hull of the actual sclera. Full blinks
cover the sampled eye surfaces. The partial baseline samples expose 29, 15,
0 and 0 of the 63 rays at the four sampled closing times; both eyes agree.
These are sampled geometry checks, not exhaustive triangle collision tests.

Existing hidden face vertices lie inside the original sclera hull, with
baseline maximum inset around 4.6–5.1 mm. The candidate does not create new
sampled inset witnesses or worsen existing inset by more than the 0.2 mm
diagnostic tolerance; maximum extra inset is approximately 0.084 mm. This
does **not** establish zero geometric intersections everywhere. Role08's
source validator also reports the same two original open-cornea obstruction
failures on baseline and candidate, 17/19, while its closure/aperture checks
pass. Neither retained limitation is silently converted to a new pass.

The original rest check in `baseline-deformation-r2.json` failed because it
compared quantized imported skinning with an unweighted rest point. Actual
weight sums reach 0.99995418, producing up to 79.65 micrometres of raw rest
deviation. The corrected check keeps those weights and compares against the
point times the actual sum: maximum bind residual is 1.51 micrometres. The
failed diagnostic is preserved; no source asset was altered to satisfy it.

## Visual review and remaining gate

Viewed actual R2-06 baseline `courtyard-front-day.png` and
`courtyard-three-quarter-left-day.png` in
`/workspace/scratch/visual-round2/capture-baseline-court-r1`. The open neutral
lids and head/neck surface are continuous at those views; the baseline has
the already visible simplified orbital forms and skin stippling. These
stills do not establish a moving blink, candidate deformation, or independent
wink quality.

R2-06 owns the remaining exact candidate import, continuous paired blink,
and five-action pixel checks. Independent L/R combinations are CPU-only by
root agreement. Supported aim extremes move the existing upper-body pose;
there are no authored gaze, brow or jaw-expression targets to accept. This
role makes no physical-GPU, continuous full-body motion, production-art or
commercial-quality claim.

## Reproduction and next owner

Run from `games/yuga-native` with the already imported baseline:

```sh
taskset -c 0,1 godot --headless --path . \
  --script res://tests/visual_round_face_cases.gd \
  -- --report=/workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json

taskset -c 0,1 python3 docs/evidence/visual-rounds/round2/role05/analyze_deformation.py \
  --runtime /workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json \
  --baseline-runtime /workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json \
  --candidate-glb /workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb \
  --held-ring /workspace/scratch/visual-round2/role-08/face-form-candidate-r5/reconstruction.held-ring.json \
  --report /workspace/scratch/visual-round2/role-05/candidate-r6-source-deformation.json
```

Use fresh report basenames when repeating commands to preserve prior runs.
The runtime command also writes `-meshes.json` alongside its report. Complete
rig poses and imported arrays remain in role05 scratch; the compact repository
runtime summary preserves checks, source hashes and state samples.

After R2-06 imports the final candidate, run the same test with `--path` set
to that isolated project and the absolute test script path. Then run the
analyzer with `--runtime` pointing to the new candidate runtime report,
`--baseline-runtime` as above, and `--held-ring` as above. **Omit
`--candidate-glb`** for this actual-import comparison. R2-06 has the exact
commands. Test SHA-256:
`8569a901862d28a851c6b757b9a9be3b94b60957b22c7fb937f7e7f43f2119fe`.

R2-10 independently reproduces the source evidence, exercises negative
counterexamples, and records its disposition under `role10/`. Root owns
integration and final status; R2-06 owns imports/renders.
