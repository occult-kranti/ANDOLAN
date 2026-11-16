# Rama completion — single-hero production pass

Task `RAMA-COMPLETE-01`, native YUGA. Baseline commit
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`, plus
preserved existing uncommitted work. The user's new scope is **one entire Rama
hero**: coherent art, playable kit, motion, feedback, guide/practice and delivery.
The existing commercial-quality target is the review reference, not a status
inferred from a generated image or number of checks.

Four concurrent roles are used: lead/integrator, character/motion artist,
hero interface expert and combat-presentation/audio expert. They have exclusive
source ownership. Imports, Blender jobs, shared asset exports and heavy native
rendering run through the lead's serialized lane. Later peer review switches
roles after source freezes; a worker does not accept their own art.

| Owner | Exclusive work | Current observable outcome |
| --- | --- | --- |
| Art/motion | `rama_motion.gd`, new motion checks, original gear candidates only after a source contract | Replace the defeated arms-up/carry silhouette with a supported bowed kneel; preserve body authority and three-second return. Additional identity art must demonstrate improvement over existing geometry. |
| Hero UI | `rama_hero_hud.gd`, `rama_hero_panel.gd`, new `rama_combat_feedback.gd` and tests | Confirmed hit/defeat/hurt reticle feedback, actual shield/health segmentation, real hero profile and context-correct practice readout. |
| Combat feel | `rama_ability_effects.gd`, `rama_action_audio.gd`, focused checks | Distinguish health, shield, defeat and wall contact using actual effective receipts; range expiry and empty contacts cannot pretend to be hits. |
| Lead | Read-only `rama_practice_record.gd`, courtyard composition, capture tools, shared contracts/manifests and packages | Real current-attempt accounting, source-matched native five-action/lifecycle footage, ordinary input, integrated review and exact playable source/package. |

## Required verification

1. All five existing actions retain the real kit's admissions, damage, geometry,
   release/cancel/recovery, cooldown, reload, remapping and receiver behavior.
2. New feedback reports confirmed effective receipts only; stale/duplicate,
   interrupted, paused, inactive, defeated and reset states remain truthful.
3. Hero silhouette, hand/bow/foot contact and defeated/returning performance
   receive actual front/rear/profile/gameplay and continuous action review.
4. Hero HUD/guide/practice remain usable at supported logical scales, with
   ordinary native input, modal/focus return and no overlay collisions.
5. The final source/asset notices and package hashes match the executed build;
   Windows, hardware, human listening/feel and online claims keep separate scopes.

The initial panel found concrete existing defects: arms raised above the head
while defeated, absent aim-centered confirmed feedback, and world blooms that
could be created from an empty unit contact. The implementation targets these
observed gaps first. Existing roadmap/historical campaign counts are preserved.

Source/authority changes require deliberate identity migration; presentation
observers cannot award damage, XP, currency, artificial mastery or progression.
New candidate assets remain original/cleared and retain notices/editable files.
The prior [video studies](../video-study/README.md) and
[current hero/map design](../../../games/yuga-native/docs/research/hero-six-rounds/HERO_AND_MAP.md)
provide context; old captures do not qualify this new source.
