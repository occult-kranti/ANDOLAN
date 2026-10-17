# Rama native art revision

This folder contains an original, skinned Rama model revision for the native
YUGA production track. The supplied Rama/Hanuman/Sita images guide its color
hierarchy and costume silhouette. They are concept references, not renders of
this exported model. The model remains an incremental art pass and does not
establish target likeness or commercial-game visual parity.

The revision uses warm exposed torso anatomy, a quiet cobalt diagonal sash,
long split mantle tails, overlapping ivory dhoti folds, narrow gold borders,
small modeled leaf embroidery, shin plates, grouped falling hair, almond eye
openings, a wrapped bow grip, and a quiver with feathered shafts. Existing
articulated shoulder ornaments, cuffs, sandals and the bow's rest-space frame
are retained. The original web and native `rama.glb` assets are untouched.

`build_rama.py` opens the existing locally authored
`/workspace/tooling/yuga-art/output/rama-authored.blend`, uses its complete
validation anatomy and native rig, rebuilds costume/hair/face detail, and
exports `../../assets/heroes/rama-production.glb`. The source anatomy derives
from the repository's pinned CC0 MakeHuman data. The pre-existing source blend
can be regenerated with `games/yuga/art/pipeline/build_heroes.py rama`; that
older command also rebuilds its original web asset, so use a separate checkout
when reproducing the source without changing an existing build.

Run from the repository root:

```sh
blender -b -t 2 --python games/yuga-native/art/production/build_rama.py
python games/yuga-native/art/production/validate_rama.py
```

The generator preserves all 164 bones and the exact keyframe/handle/interpolation
data of the nine source actions: `idle`, `run`, `fire`, `cast`, `cast1`, `cast2`,
`cast3`, `jump`, and `defeat`. It authors no new animation clips. Every mesh is
bound to the rig with normalized weights and at most four bone influences.
Tail border weights are transferred from their corresponding cloth surfaces.
Cloth thickness is modeled; there is no simulated cloth or hair.

Five original material sets have 512 × 512 albedo, roughness and tangent-space
normal maps: cobalt silk, ivory silk, antique gold, warm skin and grouped black
hair. These mathematical texture fields are generated locally, stored under
`textures/rama`, and embedded in the GLB. Their source images and the newly
authored mesh details are dedicated to CC0-1.0. This dedication does not alter
the licenses of tools, source code or unrelated assets.

`rama-production.provenance.json` records exact source/reference/generator and
texture hashes, GLB hash and size, mesh counts, preserved animation-curve
hashes, and 45 bounded pose samples. The independent binary validator checks
finite accessors, unit normals/tangents, normalized skin weights, joint/triangle
indices, embedded images, animation names and strictly increasing keyframe
times. Its result is `rama-production.validation.json`.

The first export exposed n-gon tube caps that prevented tangent generation.
The accepted export explicitly triangulates before generating tangents. Blender
prints an unavailable Draco library notice; this pipeline does not request or
rely on Draco compression.

The first actual Godot review also found a new grip decoration positioned on
the string plane and small rear medallion outlines that read as punctures.
The next revision centers the wrapped grip on the bow, removes those failed
medallions and increases skin roughness. The initial frames remain useful
failure evidence; they must not be presented as the corrected asset.
Further native pose review exposed inflated ivory hand shells: the trouser
selector used height alone and included lowered rest-pose hands. The third
revision restricts trousers and covered-anatomy deletion to the leg region,
asserts that trousers have no hand/arm bone groups, and asserts preservation of
every original hand vertex. Source hand anatomy and finger animation remain
intact; the initial two capture sets retain their own earlier asset hashes.
The third native review found ten outer-calf faces just outside the 0.24 m
horizontal guard. These made rectangular skin openings, enlarged in defeat.
The fourth revision widens that guard to 0.25 m for this fixed Rama anatomy
and asserts that no face dominated by lower-leg joints is omitted. It keeps
both hand-preservation assertions. Actual fourth-revision native idle/run/defeat
frames were inspected: the rectangular openings are absent and fingers remain
intact. The capture metadata matches the fourth artifact hash; the earlier
capture sets remain failure evidence. See `RAMA_REVIEW_ROUNDS.md` for the exact
subgoals, hashes and scope of acceptance.

These checks prove structure and bounded sampled deformation. They do not
prove absence of intersections, appealing anatomy, production animation
quality, complete concept likeness, hardware performance or multiplayer
readiness. Actual native-engine captures are the visual review source.

Optional Blender studio previews use the saved local production blend and
must be serialized with other CPU-rendering tasks:

```sh
blender -b -t 2 --python games/yuga-native/art/production/build_rama.py -- --preview-only
```

The optional front, rear and stride frames are actual Cycles renders. The
generator's `--preview` flag rebuilds before rendering; `--preview-only` leaves
the validated asset files unchanged.
