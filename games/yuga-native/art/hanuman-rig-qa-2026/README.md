# Hanuman rig and motion comparison

This independent check compares the shipped Hanuman GLB to a revised candidate. The candidate is still an art study until its visible appearance, face deformation, contact and runtime import are reviewed. It does not modify either input.

From the repository root, with Python 3, NumPy, Blender 4.3.2 and Blender's Pillow dependency available:

```sh
python3 games/yuga-native/art/hanuman-rig-qa-2026/compare.py \
  --candidate games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-candidate.glb \
  --report /tmp/hanuman-rig-qa.json
```

The script checks node hierarchy and transforms, skin joints and inverse bind matrices, animation channel targets, key times and values, mesh index topology, morph data, UVs, colors and joint weights. Positions, normals and tangents may change. It verifies finite positions, unit normals, valid joint indices and normalized skin weights, and reports displacement per material. In a separate Blender background process it imports both assets and samples **idle**, **run**, **Mountain Pulse** and **tail sweep** at five phases each, comparing evaluated meshes plus head, wrist, foot, tail and gada-socket positions. `--skip-blender` runs only the structural portion. `--baseline` selects another explicitly pinned baseline.

## Results for the current candidate

- [Positive control](baseline-report.json): the shipped GLB compared with itself passes both structural and 20 sampled Blender poses.
- [Candidate report](candidate-report.json): candidate SHA-256 `257ff4daf8694d682acc4dbfd171729ed2d5575225cfa9259533c1e9eb113abf` passes the same checks against baseline `6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a`. Eleven animations and 167 skin joints have unchanged encoded motion and bindings. The largest sampled evaluated-vertex difference is approximately 3.47 mm; sampled bones and sockets do not move relative to baseline.
- [Contact-fit v2 report](candidate-v2-report.json): SHA-256 `ce238b5d020ff8e4233cf70eca58502130afef87ebf199c929027f32bfc16b75` also passes those same checks; the largest sampled evaluated-vertex difference is approximately 6.47 mm and sampled bones and sockets do not move relative to baseline.
- [Profile v3 report](candidate-v3-report.json): SHA-256 `ae143cd63e4ac47a4f0f95e4d8f735f9bd7ee5d88ff11d958fa4cb06b27a55a8` passes the same checks, with a maximum sampled evaluated-vertex displacement of 8.04 mm and no displacement of the sampled bones or sockets.
- The [animated face projection report](animated-face-clearance.json) samples all 346 mouth and nostril detail vertices in those same 20 body-action poses, against the front-most nearby skin triangle along the de-rotated head's forward axis. Every sample returned a projected skin hit. V1 has four mouth and 102 nostril vertices behind that projected skin in each sample; v2 has none, and its projected offsets range from about +0.249 to +2.064 mm. This is directional signed depth, not a watertight signed-distance or penetration test. It does not cover speech or facial expressions. Reproduce it with:

  ```sh
  blender -b -t 2 --python-exit-code 1 -P games/yuga-native/art/hanuman-rig-qa-2026/animated_face_clearance.py -- \
    games/yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb \
    games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-candidate.glb \
    games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-contact-candidate.glb \
    /tmp/hanuman-animated-face-clearance.json
  ```

  A [separate profile v3 projection run](animated-face-v3-raw.json) used the same command with the third GLB replaced by `hanuman-face-profile-candidate.glb`. The probe calls its third input `v2` in its output; the SHA in that field identifies the actual v3 model. Each of the 20 poses returned 346 ray hits, with four mouth and 102 nostril vertices behind the projected frontmost skin; the smallest offsets were approximately −0.226 mm and −3.747 mm respectively. The metric has the same directional and expression-coverage limits described above.

- [Negative control](negative-control.json): an intentionally corrupted temporary copy with one valid-range joint index changed was rejected by the structural check. Recreate it without altering either input:

```sh
python3 games/yuga-native/art/hanuman-rig-qa-2026/make_negative_control.py \
  games/yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb /tmp/hanuman-rig-bad.glb
python3 games/yuga-native/art/hanuman-rig-qa-2026/compare.py \
  --candidate /tmp/hanuman-rig-bad.glb --report /tmp/hanuman-rig-bad-report.json --skip-blender
```

The second command should fail with `JOINTS_0 changed`. The bad file belongs in temporary storage and is not a candidate for the game.

The Blender check samples landmark positions and per-vertex differences; it does **not** measure mesh intersections, eyelid contact, grip/foot surface contact, image quality or visual continuity between samples. It does not launch the game or establish a physical-GPU budget. Review those separately before replacing the game asset.
