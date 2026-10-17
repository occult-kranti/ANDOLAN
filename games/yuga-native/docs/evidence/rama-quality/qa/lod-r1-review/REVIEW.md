# Independent native LOD review — LIMITED

Reviewed all **six matched pairs and all thirty camera frames** from the completed
actual Confluence capture. This reviewer did not author the LODs and made no
runtime, tool, asset or acceptance-document changes.

The six frontal pairs cover idle and an actual accepted Piercing Dawn windup at
780 / 350 / 120 hero pixels, selecting levels 0 / 1 / 2. They retain the full
silhouette, attached bow/skin and blue/cream/gold costume without an obvious new
hole, detached limb or large material/clothing shift. The near-to-near images
are identical by construction. Mid/far pixel differences are debug measurements,
not quality scores.

All thirty original camera frames were inspected in order. No obvious geometry
pop was observed at level switches 6, 12, 20 and 26. **Frames 9 and 20 contain a
pale glint around the quiver/left head area**, so the sequence is not uniformly
clean and final LOD acceptance remains open. The decoded `(610,390)–(655,440)`
regions match exactly, contain 505 pixels with every RGB channel above 200, and
peak at `[232,228,225]`. Both use the same 182.3 px camera and level 1. Frame 9
is already within level 1; frame 20 returns from level 2. This does not establish
a switch cause. Full original frames and the measurement script are preserved
here without image edits.

The next material-frame rebake/art packet needs a **forced-near versus selected-mid
pair at that exact 182.3 px camera**, with frozen windup, lighting, material and
controller state. No such reference exists in this capture, so the cause must
remain unassigned.

Independent read-only verification confirms all 42 image hashes, 484 runtime
source pins, nine fresh imported GLBs, one 164-bone rig, a unique source face,
fixed pair states and zero engine warnings/errors. Selected source triangle
totals, including the same retained face, are 408,316 / 216,544 / 140,966. These
are geometry counts; renderer primitive statistics include world/shadow passes
and do not establish consumer-GPU performance.

This is a frozen-pose camera sequence, not continuous gameplay deformation,
secondary-motion evolution, a full match or achieved 15 FPS. Rear/side views,
all clips/elevations, tangent/material-frame correction, physical-GPU profiling
and the final art target remain outside this bounded review.

`review.json` is the final cross-reference. `proof.json` pins every original
image and source check; `measure_review.py` reproduces the read-only identity and
glint measurements against `../../lod/native-capture-r1/`. The root capture/movie
receipt remains the authority for the actual rendering and video decode.
