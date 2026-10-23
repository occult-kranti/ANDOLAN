---
name: yuga-ui-flow
description: "Implement and review YUGA native screens, controls, feedback and accessibility. Use for W2 boot-to-match flow, settings, HUD, remapping and lifecycle assignments."
---

# YUGA W2: screens and interaction

Improve one assigned native player flow with actual input evidence.
Keep the native, browser and deferred Android products explicitly separate.
The current assignment, not the entire roadmap, defines the implementation scope.

## Entry points and ownership

Read [AGENTS.md](../../../AGENTS.md), [start here](../../../docs/START_HERE.md),
[native product](../../../games/yuga-native/PRODUCT.md),
[native design](../../../games/yuga-native/DESIGN.md) and the assigned
[screen gate](../../../games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.md).
Root product/design files belong to the separate browser game.

Inspect [runtime composition](../../../games/yuga-native/scripts/rama_hero_runtime.gd),
[player input](../../../games/yuga-native/scripts/player.gd),
[native contracts](../../../games/yuga-native/docs/NATIVE_CONTRACTS.md) and the
[build handbook](../../../games/yuga-native/docs/BUILD_HANDBOOK.md) as relevant.
Find the real screen owner before editing; do not invent a parallel UI framework.
Lead owns shared tokens, contracts, ledgers and integration. Coordinate any
overlap with W3 hero presentation, W5 combat state and W6 loading/package work.

## Phase 1: define the flow and contract

1. Record task ID, baseline commit, exclusive files and the reproduced problem.
2. Specify starting state, input, expected feedback, completion/cancel behavior
   and focus destination. Include one failure or interruption that could regress.
3. Freeze truthful authority-owned values for health, cooldown, ammo, outcome,
   reload and availability. Presentation must not invent usable abilities or
   represent offline practice as an active online service.
4. Reuse established spacing, typography, focus and interaction components.
   Inspect current originals before changing their proportions or information.

## Phase 2: implement and exercise

- Preserve semantic actions and saved remappings. Labels and hints must show
  the current binding, support cancel/back and resolve conflicting inputs.
- Cover keyboard/mouse focus, pointer capture, modal return, pause, loss of
  focus, resize, error/retry and fresh-process settings as applicable.
- Keep the hero and hostile telegraphs readable at supported UI scales.
  Use clear states and concise copy; avoid duplicate controls and fake loading
  progress. Loading feedback must reflect actual mounted or failed resources.
- Run the relevant existing checks from the handbook, then exercise the actual
  native flow. Capture the changed state and its boundary at gameplay scale.
  A layout calculation or static screenshot does not verify input behavior.
- Inspect repeated entry/exit and reset without leaking input, overlays or
  resource owners. Preserve deliberate timing and accessible reduced motion.
- Coordinate UI with actual W5 events. Do not alter damage, cast release or
  cooldown rules to conceal an unclear screen state.
- Serialize heavy renders with other workers. On the confirmed 8 GB laptop,
  shared system memory is not extra VRAM and six agents do not need six models.

## Phase 3: independent acceptance

Ask W1 to review the original native captures and input journey against the
frozen expected behavior. Return source hashes, changed files, exact commands,
pass/fail results, original evidence, remaining defects and next owner.
One correction pass follows a concrete issue; stop the scoped packet once its
result is proven or an indispensable external prerequisite remains blocked.

Android adaptation belongs to its later M2/M3/M9 gates: live camera, touch
ownership, aiming, safe areas, backgrounding and physical-device validation.
Making desktop labels bigger is not a mobile UI implementation.
Generated concepts can guide art direction but are not accepted runtime UI.

Preserve existing work and user saves. Do not automatically create a worktree,
switch branches, force-push or publish through an unassigned task. Continue
authorized work without repeated confirmation; user instructions take priority.
