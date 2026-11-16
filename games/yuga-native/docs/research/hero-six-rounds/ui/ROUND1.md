# Round 1 · native hero interaction audit

Task YUGA-HERO-6R, YUGA native. Source commit `7162b5d0b666e4422b0bc73100e1fba947d3323f`; pre-existing uncommitted studio work is preserved. [Source receipt](round1-source.json) pins the actual inspected files.

Applied skill: `.agents/skills/yuga-ui-flow/SKILL.md`. Read START_HERE, native PRODUCT/DESIGN and relevant build-handbook paths.

## Reviewed evidence

Personally inspected studio `final-native/10-final-world.png` and `04-final-guide.png` using the image tool. These are previous-build originals, not images of this proposed change. Read the HUD, guide, glyph, theme and ability-kit runtime sources and existing layout/action/reload tests.

The current five-slot bar already shows truthful ability names, current keys, health/ammunition, cooldown decimals, drawing/recovery, queued input and pause/defeat status. The read-only guide preserves keyboard focus, real JSON values, effects preferences and saved remaps. Existing information must stay; a replacement fake battle UI would regress the actual player journey.

## Finding and proposed upgrade

Five equal dark rectangles leave the ultimate indistinguishable from a normal action. Readiness is communicated almost entirely with small text. The guide explains individual rules but has little instruction about choosing an action, counterplay or combining it with another action.

Add narrow authority-driven cooldown/active progress strips inside existing slots and a distinguished ultimate presentation with three arrow lanes. An active meter reads the existing cast snapshot; it cannot advance combat, invent damage, imply charge stacks or persist after reset/cancellation. Keep current labels and exact layout footprint; unavailable states remain visibly unavailable. The original worked-brass/indigo palette is sufficient; avoid claiming this ornament is an archaeological reconstruction.

Add concise Use / Counter / Follow-up advice to the guide, grounded in the current kit: piercing groups stops on cover, Measured Step preserves aim but has no invulnerability, Guardian Circle is fixed and cannot cross cover, Dawn Volley locks three lanes and is countered by cover/lateral movement during preparation. Suggested combos are tactical hypotheses, not measured balance conclusions.

## Proposed ownership and validation

Request exclusive `scripts/rama_hero_hud.gd`, `scripts/rama_hero_panel.gd`, new `scripts/rama_ability_meter.gd`, new `tests/rama_hero_feedback_cases.gd`, plus this report directory. Shared theme, simulation, world and input files remain with their current owners.

Run existing HUD layout, availability/reload/action/glyph/guide scaling regressions plus a small real-kit meter lifecycle case. Preserve 100/150/200% scales, long remaps, no node growth, pause/defeat/reset and read-only guide semantics. Lead coordinates actual native images and ordinary input after implementation. This audit alone accepts no new rendering or gameplay.

No runtime files changed in R1; no tests executed yet. Next owner: lead for R2 contract, then UI specialist implementation.
