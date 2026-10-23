---
name: yuga-hero-art
description: "Author, adapt and review YUGA hero geometry, materials, rigs and animation-ready assets. Use for W3 Rama quality, character generation, retopology, skinning and hero LOD assignments."
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
