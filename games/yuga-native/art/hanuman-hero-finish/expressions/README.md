# Hanuman facial action study

Three Blender Actions let an animator test a blink, a small shift of attention and a subtle jaw-and-lip recovery on the existing 167-joint Hanuman. This library is for a separate artist scene. The playable GLB keeps its eleven shipped animations. [Action library](hanuman-face-actions.blend) · [Rendered close-ups](face-contact-sheet.webp) · [Donor model](../models/hanuman-enhanced.glb)

| Action | Timing at 30 fps | What to watch |
| --- | --- | --- |
| Studio · Blink | F1 open, F4 closed, F6 closed, F12 open | The upper lid wraps the cornea and meets the lower lid below the eye center. Upper and lower orbital joints move. The eyes, jaw, head and neck hold their pose. |
| Studio · Focus | F1 neutral, F9 focused, F18 held, F28 neutral | Both eyes turn 4.5° toward character left. The medial brow lowers and narrows slightly. A partial lid fold keeps the irises readable. |
| Studio · Relaxed recovery | F1 neutral, F8 relaxed, F13 easing back, F26 neutral | The jaw turns 0.75° and the paired lower-lip controls release tension. At portrait distance the change is a small easing of the mouth crease. The eyes and neck stay still. |

## Open a prepared copy

From the repository root, the following command creates a new scene outside the repository. Use a fresh output directory and a new filename for the scene. The accompanying script imports the existing GLB, installs the three fitted shape keys, connects their drivers and appends the checked-in Actions. Blender 4.3.2 and Pillow were used for the published study.

```sh
blender -b -t 2 --python-exit-code 1 \
  -P games/yuga-native/art/hanuman-hero-finish/expressions/face_actions.py -- \
  --use-library games/yuga-native/art/hanuman-hero-finish/expressions/hanuman-face-actions.blend \
  --out /tmp/hanuman-face-study --scene /tmp/hanuman-face-study/artist.blend --skip-render
```

Open the resulting scene, select the rig, choose an Action in the Action Editor and scrub its frames. The armature has three additional properties for blending the fitted lid, brow and lip correction. To edit from Python, call `install(rig, body, library=path)` on a newly imported copy. It mutes the imported animation tracks and prepares the rest pose for expression work. Omitting `library` regenerates the three actions from the keyed timings in the script. The packed Action file contains the motion data. The installer supplies the corrective shape keys and their drivers on this mesh. [Generator and installer](face_actions.py)

## What the eye test measures

The donor’s anatomical face has weighted orbital and oral controls. The separate visible eyelid and upper-fold surfaces use rigid head weights. At peak blink, moving the orbital joints alone left 273 right-eye and 272 left-eye rays visible. The accepted blink moves the **existing** lid margin around the cornea with a fitted shape key. The iris, pupil and eyeball retain their original positions. Similarly, the focus corrective follows the existing sculpted brow and the recovery corrective keeps the separate lip detail together. [Original lid construction](../../../tools/hanuman-art/build.py)

The test casts a 36 × 22 grid of orthographic rays across each eye on the evaluated Blender mesh. It counts the first visible intersections with actual pupil, iris or sclera geometry. At neutral, 304 right-eye and 303 left-eye rays reached ocular geometry. With the fitted surface at peak blink the count reached zero on both sides. The test also checks protected joint matrices and neutral returns. The four review images use one fixed near-frontal camera and constant lighting. Production combat camera readability, lip sync, speech phonemes and blends against moving body actions remain outside this study. [Verification data](verification.json)
