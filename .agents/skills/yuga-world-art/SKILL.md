---
name: yuga-world-art
description: "Build and review YUGA original environments, lane units and modular map assets. Use for W4 arena, architecture, water, lighting, collision, minion and world LOD assignments."
---

# YUGA W4: world, lanes and units

Improve one assigned world element while preserving readable gameplay space.
Original mythology-inspired architecture needs source notes and coherent art;
it is not an archaeological reconstruction or permission to reuse game assets.

## Entry points and ownership

Read [AGENTS.md](../../../AGENTS.md), [start here](../../../docs/START_HERE.md),
[active handoff](../../../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md),
[game design](../../../games/yuga-native/docs/GAME_DESIGN_MASTER.md),
[native contracts](../../../games/yuga-native/docs/NATIVE_CONTRACTS.md) and
[research brief](../../../games/yuga-native/docs/research/RESEARCH_BRIEF.md).
Use [the handbook](../../../games/yuga-native/docs/BUILD_HANDBOOK.md) to locate
the actual world/army owner and its current checks before editing.

Lead assigns exclusive geometry, material, scene and source paths. Coordinate
shared navigation/collision with W5, UI overview with W2 and export/resources
with W6. Preserve the existing playable map while a candidate is reviewed.

For a new lane or courtyard, check the [editable world elements](../../../games/yuga-native/art/reuse-library/README.md) first. Link a collection when multiple placements should follow one master. Append it when the map needs a variant. Check its base anchor, footprint and existing material slots from a gameplay camera. The Rust study and the four-manifest importer provide additional building blocks for local authoring. Check the recorded provenance before moving a study into the game.

## Phase 1: freeze the place and gameplay purpose

For an Elden Ring-inspired vista, use the [world research and team brief](../../../games/yuga-native/docs/research/elden-ring-world-study/README.md). Compare the source's framing, silhouette and approach against the current player camera. Use the project's original kits and separately licensed assets with their provenance. Treat the isolated Rust surface-cache probe as an experiment with a ray-query dependency, and reconcile any real route with the chosen runtime's authoritative collision.

1. Record task ID, baseline, exclusive files, intended visible improvement,
   reference images and the route or encounter served by the element.
2. Freeze scale, camera, day/night phase, team visibility, collision and unit
   counts for matched evidence. Declare any intentional contract change first.
3. Define silhouette, material, surface, triangle/LOD and light budgets as
   proposals until measured on target hardware; do not claim simulated FPS.
4. Keep source associations precise. Separate literary Lanka, other water
   settings, historical architecture and original invented map composition.

## Phase 2: build and test in context

- Author a coherent small modular kit before multiplying it across lanes.
  Reuse immutable geometry/materials where safe; keep mutable instance state
  private. Reduced allocation count does not automatically reduce draw calls.
- Make traversable stairs, decks, doors, water edges and grapple anchors match
  navigation/collision. Decorative silhouettes must not imply unusable routes.
- Evaluate lane length by travel, contest, retreat and rotation times; do not
  enlarge geometry without checking pacing, sight lines and encounter purpose.
- Keep gold/objectives, allies, hostile telegraphs and playable surfaces clear
  against ornate architecture. Decorative detail must not imitate combat cues.
- Use bounded lights and deliberate emission for diyas/lanterns. Verify water
  depth/paving readability and identical camera views across day/night phases.
- Give soldiers and siege units readable anticipation, attack, hit and defeat
  poses with coherent weapons. Simulation owns damage, rewards and lifecycle;
  render effects must not create extra gold, targets or authority events.
- Generated props require source/checkpoint provenance, backside/underside
  inspection, topology/UV/material cleanup, collisions and runtime LODs.
  A model preview or scene viewer does not establish a traversable game map.
- Run relevant existing world/army/resource checks and actual native traversal
  with representative unit/effect populations. Capture matched original views
  and advancing footage, retaining failures and occlusion/edge findings.
- Serialize heavy imports/renders. The confirmed 4070 laptop has 8 GB dedicated
  VRAM; 16 GB shared memory is slower system RAM, not equivalent GPU capacity.

## Phase 3: independent integration review

W1 reviews originals and navigation evidence; W5 checks collision/authority
interfaces and W6 checks source/resource/package integrity. Return exact hashes,
commands/results, source references, originals, budgets, unrun hardware gates,
remaining defects and next owner. One correction pass follows concrete findings.

Android is deferred. M10 later requires its own map camera, reduced materials,
collision/LOD/texture variants, occlusion and sustained physical-device budgets.
Do not claim device performance from the desktop or an empty synthetic scene.
Keep source, editable art, meaningful failures and unique evidence. Follow the
[cleanup guide](../../../docs/WORKSPACE_AND_CLEANUP.md) before deleting outputs.
Continue authorized work without repeated confirmation; user scope takes priority.
