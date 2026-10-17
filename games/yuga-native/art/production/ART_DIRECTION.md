# Native production art direction

This pass improves one original Rama model and a small Lanka-inspired court. Its
target is the character readability, material discipline and motion quality of a
finished third-person action game. It does **not** establish visual parity with
Deadlock or Overwatch, and it does not complete the roster or city. “4D/5D” is
treated as animated 3D, temporal effects and presentation; no separate graphics
format or capability is implied.

## Evidence inspected

| File | What it establishes |
| --- | --- |
| `games/yuga/art/references/rama-hanuman-sita.png` | Generated concept target: distinct blue/ivory, red/saffron and green/ivory costumes; coherent anatomy, hair/fur, layered cloth, ornate weapons and selective gold. This is not a game render. |
| `games/yuga/art/production-concepts/priority-model-direction.png` | Generated front/rear and material direction for Rama, Hanuman and Sita. Its turnarounds are visual guidance, not verified geometry or deformation. |
| `games/yuga-native/build/visual-initial/frame-3.png` | Actual initial native frame: functional courtyard blockout, small rear-facing hero, muddy costume, repeated thin trim, dominant empty paving, flat atmospheric separation. |
| `games/yuga-native/build/visual-final/packaged-title.png` | Godot startup splash only. It establishes neither the YUGA title nor gameplay presentation. |

The actual initial view cannot establish facial detail, animation continuity,
foot contact, weapon grip or performance. Those require additional native views
and motion evidence. A texture count, bone count or successful export cannot
close a visual gate.

## Five changes for the current pass

### 1. Make Rama's body, hair and bow read before ornament

**Observed gap:** the distant rear view reads as a narrow rigid mantle above two
parallel pale lower legs. The generated target has a clear shoulder-to-waist
taper, layered shoulder shapes, topknot and falling hair, separated arms and a
sweeping bow that remains identifiable outside the body silhouette.

**Implement now:** improve the exposed torso and forearm transitions; use
distinct dark hair masses rather than a helmet-like shell; separate mantle
tails; retain the tall curved bow and quiver above one shoulder. Keep new
geometry attached to the existing rig. Shape eyes, brow, nose and jaw where the
existing mesh allows, without claiming a finished facial likeness.

**Visual gate:** inspect actual front-three-quarter, rear and mid-stride frames
at matched scale, plus a bow pose. Hair and bow must read against the scene;
hands must visibly contact the weapon; there must be no newly detached parts,
cape-through-calf intersections or rigid accessories floating during movement.
An anatomy close-up must accompany any claim about face quality.

### 2. Restore a quiet cobalt, ivory, skin and gold hierarchy

**Observed gap:** the initial rear mantle reads as muddy brown-gray with evenly
busy detail. It loses the large blue/ivory fields and fabric volumes that define
the approved concept. Small ornament alone will not repair this.

**Implement now:** use a cobalt outer mantle and narrow diagonal sash, a folded
ivory lower garment, warm exposed skin and restrained gold borders. Show broad
cloth folds before small embroidery. Separate rough fabric/skin from metallic
trim and gem response; reserve the strongest contrast for silhouette and face.

**Visual gate:** at gameplay distance, cobalt and ivory remain visibly distinct
under both warm key and cool fill. In a close view, cloth folds cast or receive
shading and gold produces a different response from cloth. No clipping white
skin/ivory regions, glittering all-over noise or uniformly plastic surface.

### 3. Give the court a focal mass and quieter foreground

**Observed gap:** broad paving and a very large near-camera lotus dominate the
initial composition. Thin repeated trim flattens the gate and colonnades; the
opening and supporting piers need greater depth and shadow hierarchy.

**Implement now:** narrow and soften paving seams, reduce the foreground lotus,
deepen the main gate recess and pier/lintel/plinth massing, and concentrate
brass around a few focal features. Preserve quiet pale/warm stone areas, dark
indigo inserts and sparse turquoise accents. Existing water, reeds and lamps
should provide human scale at the edges without obstructing practice routes.

**Visual gate:** in an actual spawn view, the main gate and target line are
clearer focal points than paving seams or floor ornament. An oblique view must
show gate depth rather than a flat decorated facade. The original spawn,
target positions, walking corridor and collision contract remain intact.

### 4. Shape depth with light, not exposure or glow

**Observed gap:** the initial view has a pale cyan atmosphere, weak separation
between lit planes and recesses, and limited separation of material responses.

**Implement now:** use a warm directional side key, restrained cool fill and
ambient illumination, dark but legible recesses, less intrusive fog, and warm
local lantern pools. Keep the sky sun disc small. Bloom and ambient occlusion
are supporting effects, not substitutes for shape and light placement.

**Visual gate:** native daylight and low-light views retain readable blue cloth,
warm skin and pale stone. Gate recesses are visibly darker than exposed piers;
lanterns read as warm localized lights. Target discs, crosshair and architecture
edges remain visible without bloom halos merging them. Evaluate the actual
renderer used for the package, not an offline beauty render alone.

### 5. Present the hero and validate visible motion

**Observed gap:** the initial rear framing makes costume detail small and gives
most of the image to empty paving. One still cannot verify animation quality.

**Implement now:** tune a near-shoulder camera with a clear forward aim corridor
and a visible bow-side silhouette. Keep aiming obstruction, camera collisions
and player visibility under review. Provide a separate close review camera or
turnaround for model assessment; do not force a portrait view during play.

**Visual gate:** actual gameplay frames at representative supported sizes show
the hero, reticle and objectives without clipping or UI overlap. Inspect idle,
run, jump/landing, fire and cast transitions in motion. Foot sliding, grip loss,
pose snaps and cloth intersections are recorded as defects even when animation
transforms are finite and automated tests pass. The title capture must show
YUGA after loading; a startup splash is not title acceptance.

## Cultural and source boundaries

This is original myth-inspired fantasy. Broad Lanka passages can support pale
building masses and selective gold gates, but do not establish these exact
proportions, costumes, ornaments, period or composite city layout. Reeds and
lotus imagery from Pampa is a separate landscape source; it is not evidence
that Lanka itself was a swamp. The generated Rama costume is a design target,
not a documented historical reconstruction. The [production source library](SOURCE_LIBRARY.md)
records exact reading scope, source hashes and the boundary between cited
motifs and original design. Retain that distinction in asset names.

## Actual production review

The following views were opened and inspected, rather than inferred from an
asset manifest. Both capture sets use Godot 4.6.3 Forward+ on llvmpipe and are
explicitly staged, frozen animation poses. They do not prove continuous motion
or hardware performance.

| Capture set | Inspected views | Observation |
| --- | --- | --- |
| `build/hero-review-production-v1/` | `01-front-idle.png`, `02-rear-idle.png`, `10-pose-fire.png`, `13-pose-run.png` | Cobalt/ivory identity is much clearer than the initial court view. Rear decorative loops read as punctures; the tall bow is cropped in some shots. Surface and deformation gaps remain substantial. |
| `build/hero-review-production-v2/` | Front, rear, three-quarter idle, fire and run (`01`, `02`, `04`, `10`, `13`) | Wider framing includes bow and feet. Puncture-like rear loops are gone; bow decoration is better positioned. The pale inflated grip-hand region remains a substantive defect, confirmed by the artist as a trouser/anatomy vertex-selection error. This asset is not accepted pending that correction and fresh evidence. |
| `build/hero-review-production-v3/` | Rear, three-quarter idle, defeat, fire and run (`02`, `04`, `09`, `10`, `13`) | The pale grip-hand shell is removed and separate warm-toned fingers are visible. Rear loop removal and full-bow framing are retained. Rectangular brown skin exposure/intersection remains visible at the outer lower trouser leg in idle/run and at the bent knee/calf in defeat. The defeated pose reads, but drape and attachment/contact quality remain coarse. |
| `build/hero-review-production-v4/` | Three-quarter idle, defeat and run (`04`, `09`, `13`) | The rectangular lower-leg/knee openings are visibly closed in all three inspected views. Separate warm-toned fingers remain intact, and the full standing bow remains in frame. The bounded introduced-defect correction is accepted; the larger production-art gaps remain. |
| `build/window-production-v3/` | `native-menu.png`, `held-fire.png`, `settings-view.png`, `title-ready.png`, `night-courtyard.png`, `aimed-fire-night.png` | Actual packaged Forward+ court: smaller pale floor ornament and quieter seams, a clearer focal gate, warm side light/long shadows, dark galleries and readable cobalt hero/target discs. At night, the hero, target discs, HUD and localized warm lamps remain readable. Fine repeating floor patterns and very dark gallery interiors remain. Despite their names, `native-menu.png` shows gameplay and `title-ready.png` shows only the Godot startup splash. These package views contain the v3 hero, not the corrected v4 asset. |

The v1 capture records asset SHA-256
`65140691ffed9546ab3ed4919ec7ebe38e118fca1543e1b173273de65d99c312`;
v2 records `86e4acc36c7da2d4abef8823e9bd1b4549ede34091d5518c89f9edbf6a7ea808`.
The corrected v3 records
`459fab62bcf29066490c0156cdf1a3ba7378ff3dba2fa6e4882b9eff96a801a0`.
The final bounded v4 correction records
`6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`.
Each report records the same before/after hash and 13 completed captures; the
visual inspection above covers only the named views. The v1/v2 defects are
retained as revision history rather than silently relabelled as passing.

### Three production gaps that survive these bounded fixes

1. **Anatomy and face need a dedicated sculpt/deformation pass.** The face,
   shoulder, elbow and armpit transitions remain angular or pinched compared
   with the reference. Hair still reads as repeated strips rather than shaped
   volumes. Additional ornament cannot substitute for coherent underlying
   form, retopology and skin weighting.
2. **Cloth and attachments need fitted shapes and deformation.** The mantle
   and dhoti read as rigid pleated panels, the sash has a jagged silhouette,
   and chest jewelry visibly sits away from the torso. The next authored pass
   needs drape, attachment contact and pose-specific deformation; finer
   textures alone cannot repair these volumes.
3. **Archery and locomotion need distinct authored action poses.** Inspected
   idle and run samples retain a held-draw upper-body arrangement; the firing
   pose does not yet demonstrate convincing draw, release and recovery.
   Hand/string contact, projectile release timing, foot contact and continuity
   require motion review, not inference from one sample per clip.

## R3: verification of the current revision

The actual v3 views verify the bounded hand-region correction. The artist's
read-only diagnosis identified the rectangular trouser exposures as ten omitted
lower-leg polygons, five per side, at the selector boundary; that was an actual
garment gap rather than a lighting artifact. The v4 idle, run and defeat views
verify closure of those visible gaps while retaining the restored fingers.
No additional introduced defect was identified in those three inspected v4
views. This is **incremental material/silhouette improvement and correction of
introduced defects**, not acceptance of a finished hero or every animation.

| Gate | Current evidence and decision |
| --- | --- |
| 1. Hero anatomy, silhouette and grip | **Partial; production target not passed.** Bow silhouette, restored fingers and separate mantle tails are visible; introduced hand and lower-leg selection defects are corrected in the inspected v4 views. Face/anatomy, fitted garment deformation and convincing archery contact remain unresolved. |
| 2. Material hierarchy | **Partial.** Cobalt, ivory, warm skin and gold are distinct in staged studio light; blue/ivory remain readable in the dusk court. Rigid cloth forms and coarse shading remain. |
| 3. Courtyard massing | **Partial.** The actual frontal court view confirms a quieter floor motif and clearer focal gate/target line. An oblique view is still needed to judge depth; fine repeating floor patterns remain visible. |
| 4. World lighting | **Partial.** Warm exposed stone, dark galleries and contact shadows are distinct in the actual dusk court; target discs, hero and HUD remain readable in the inspected night view with localized warm lamps. Gallery interiors remain very dark; broader traversal angles and rendering conditions are unreviewed. |
| 5. Presentation and motion | **Partial.** Studio framing includes bow and feet; the defeat sample and frontal gameplay HUD are legible. Continuous animation, foot contact and action differentiation remain unproven. The inspected title capture is a startup splash, not title acceptance. |

## R4: report and next production decision

Accept the bounded v4 correction as a reviewable development artifact and
preserve the earlier failures and remaining production gaps alongside the
images. Do not describe it as final character art, reference likeness, verified
animation continuity or commercial quality. The v4 model still needs inclusion
in, and verification against, the final package; v3 window captures cannot be
relabeled as proof of that package.
The next substantive production milestone is the three-part anatomy,
cloth/deformation and action-animation work above, followed by the same visual
gates. More ornament, texture counts or repeated procedural variations do not
close those gaps. Approval of one view does not approve all animations,
camera angles, renderer settings or hardware performance.

Final integration: [v4 native-window evidence](../../docs/evidence/window-production-v4/input-review.json) records the same final model in the exported PCK. Root viewed the actual title, training and held-fire frames; the PCK hash is `16fc5d53c3bd1706d3b628a115e4f887d559687db31b68fd906fb9fb7cf44592`. This closes the pending package-render check for this incremental pass, with the broader visual gates above unchanged.
