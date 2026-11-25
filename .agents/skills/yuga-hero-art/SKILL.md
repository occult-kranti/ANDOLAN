---
name: yuga-hero-art
description: "Author, adapt and review YUGA hero geometry, materials, rigs and animation-ready assets. Use for Hanuman reference matching, Rama quality, character generation, retopology, skinning and hero LOD assignments."
---

# YUGA W3: hero production art

Deliver one accepted character improvement in the actual game pipeline.
Judge silhouette, form, deformation, motion and materials against the reference;
adding polygons or generating an attractive concept does not close that gate.

## Entry points and ownership

Read [AGENTS.md](../../../AGENTS.md), [start here](../../../docs/START_HERE.md),
[active handoff](../../../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md),
[hero milestone](../../../games/yuga-native/docs/RAMA_HERO_MILESTONE.md),
[quality target](../../../games/yuga-native/docs/DEADLOCK_QUALITY_TARGET.md) and
[asset reuse guide](../../../games/yuga-native/docs/REUSE_ADOPTION_GUIDE.md).
The [AI study](../../../games/yuga-native/docs/research/ai-pipeline-oct21/README.md)
owns model/source distinctions; its older laptop proposal is not current VRAM.

For Hanuman, read the [trial handoff](../../../games/yuga-native/docs/HANUMAN_HANDOFF.md),
the [rotating panel roadmap](../../../games/yuga-native/docs/HANUMAN_SWARM_ROADMAP.md),
and the [verified Blender tool intake](../../../games/yuga-native/docs/research/hanuman-match-sources.md).
Compare the actual [generated target](../../../games/yuga-native/art/hanuman/lookdev/hanuman-imagegen-reference.png)
with the existing [editable dusk scene](../../../games/yuga-native/art/hanuman/lookdev/README.md)
before choosing the change.

Inspect the assigned editable source and import contract before editing.
[Hero runtime](../../../games/yuga-native/scripts/rama_hero_runtime.gd) composes
the asset; [motion](../../../games/yuga-native/scripts/rama_motion.gd) owns
presentation. W5 owns motion changes; W6 owns shared export/package inputs.
Lead assigns exclusive asset paths and owns notices/manifests and integration.

## Phase 1: define the artist-controlled change

1. Record baseline asset/source hashes, task ID, exclusive files, reference
   views and one visible defect. Read accepted and rejected art decisions first.
2. Freeze scale, rest axes, skeleton, material slots, camera, light, pose and
   game distance. Agree interface changes with W2/W5/W6 before export.
3. Define front, back and profile checks plus the continuous action sequence.
   For current Rama work prioritize hair flow/silhouette, costume drape, exposed
   body joins, face and material hierarchy over repeated automatic cap tuning.
4. Preserve the original editable source and authoring history when available.
   An imported GLB reconstruction must not be called the original source scene.

## Reference matching in Blender

1. Save a new editable scene from the pinned master. Keep the generated still
   beside the delivered Blender file for comparison. If an artist needs an
   overlay during staging, remove it from the delivered scene. Record camera
   position, focal settings, dimensions, pose, world, view transform and asset
   hashes so the previous image can be rebuilt.
2. Render a matched full-frame baseline. Assign form, costume and prop,
   setting and light, and independent review to separate owners when a panel
   is requested. First match support and silhouette from the ground up:
   both soles, both shoulders, the held gada and the arc of the tail. Check the
   face and fingers in crops once those landmarks read at full-frame size.
3. Work in separate collections or scripts. Use subdivided source topology for
   the sculpt where appropriate, then judge edge flow at eyelids, mouth,
   knuckles and bending joints. Add cloth volume and trim with actual geometry.
   Reserve small shader relief for pores, fabric grain and shallow engraving.
   Test folds and layered metal for intersections from a second camera.
4. Use short Cycles previews before spending time on a higher-sample image.
   Hold camera and AgX settings constant for an art comparison. Keep the raw
   render and any filtered deliverable. Save a cropped face, gripping hand and
   grounded feet, and at least one secondary view of the actual scene. Use
   depth, normal or object masks when a diagnosis requires them.
5. Keep the showcase mesh, materials and court separate from the Godot export
   until motion, appearance and budgets pass review. The anatomic placement
   and surface breaks in the generated view are useful targets. Exact hidden
   geometry and alternate views cannot be recovered from one RGB image.
   Describe what the rebuilt scene actually matches and where it differs.

LoopTools 4.7.7 can optionally relax temporary edge loops before skinning. Its
[isolated install and smoke test](../../../games/yuga-native/docs/research/hanuman-match-sources.md#optional-artist-extension)
keep the normal factory-startup build independent. Check weighted contact and
silhouette again after any smoothing. For Godot, keep the bundled Blender
glTF 2.0 exporter and qualify the actual GLB in the native runtime.

Use the [Practice Drawing This model index](https://practicedrawingthis.com/cgi-bin/3d-models-index.cgi)
for browser-based practice with skull, ribcage and hand construction. Follow the
[per-region anatomy skill](../yuga-anatomy-review/SKILL.md) and its
[Hanuman study exercises](../../../games/yuga-native/docs/research/hanuman-match-sources.md#anatomy-and-gesture-practice)
to produce original YUGA clay views, close-ups and pose strips. Keep study models
in the browser unless their individual redistribution license and provenance are verified.

## Phase 2: author and validate the candidate

- Sculpt or model intentional masses and readable transitions. Inspect hair
  gathers, strand groups, scalp coverage, cloth thickness and garment/body joins
  from unseen angles, not only a chosen hero portrait.
- Use generated meshes as candidates. Pin input rights, code and weight
  revisions, settings and output hashes with W6. Inspect hidden/back geometry,
  topology, UVs, tangent/normal consistency and material seams before adoption.
- Retopologize for deformation, create or preserve a coherent rig/skin and test
  facial/garment behavior. Automatic remeshing alone does not validate skinning.
- Preserve motion/authority separation. Do not move the simulation capsule or
  retime an attack release to hide an art/contact defect.
- Review actual imported continuous movement, cast, recoil, interruption,
  landing, defeat and recovery relevant to the asset. Check bow/string/hand,
  foot support, joints and cloth intersections at transition boundaries.
- Prepare measured LOD, surface/material and texture variants. A reduced mesh
  must preserve threat silhouette and avoid visible popping in its actual camera.
- Run the applicable existing import/rig/source checks from the handbook and
  capture original neutral, day/night and gameplay views for independent review.
- The confirmed laptop has 8 GB dedicated VRAM, not 24 GB. Shared system memory
  is separate. Queue generation/render jobs and unload competing model workloads;
  actual inference and quality must be measured before promising throughput.

## Phase 3: accept or reject with evidence

W1 reviews matched originals and W5 reviews motion/rig interfaces. Return source
and output hashes, editable files, notices, settings, commands/results, originals,
rejected alternatives, unresolved defects and the next owner.
One correction pass addresses specific findings. Keep candidates inactive until
the agreed quality and integration gates pass; a numeric pass cannot waive art.

Desktop remains first. Android variants later require M3 device readability,
material/skin/texture budgets, sustained device footage and their own acceptance.
Do not count an invocation through Rama as another complete hero.
Preserve other owners' work, unique art and user state. Continue authorized work
without repeated confirmation; this skill adds no purchase or publication grant.
