---
name: yuga-motion-combat
description: "Implement and review YUGA motion, combat presentation and authority integration. Use for W5 ability timing, animation transitions, traversal, counters and networking assignments."
---

# YUGA W5: motion, combat and authority

Deliver one source-bound improvement without concealing gameplay defects in art.
Desktop remains first; native offline, browser and future online/mobile profiles
retain distinct authority, wire and acceptance contracts.

## Entry points and ownership

Read [AGENTS.md](../../../AGENTS.md), [start here](../../../docs/START_HERE.md),
[active handoff](../../../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md),
[native contracts](../../../games/yuga-native/docs/NATIVE_CONTRACTS.md) and
[the backlog](../../../games/yuga-native/docs/ROADMAP_BACKLOG.json).

| Concern | Actual entry point |
| --- | --- |
| Skeleton presentation | [rama_motion.gd](../../../games/yuga-native/scripts/rama_motion.gd) |
| Offline action timing/releases | [rama_ability_kit.gd](../../../games/yuga-native/scripts/rama_ability_kit.gd) |
| Runtime composition | [rama_hero_runtime.gd](../../../games/yuga-native/scripts/rama_hero_runtime.gd) |
| Buffered input | [rama_action_buffer.gd](../../../games/yuga-native/scripts/rama_action_buffer.gd) |
| Effects/audio consumers | [rama_ability_effects.gd](../../../games/yuga-native/scripts/rama_ability_effects.gd), [rama_action_audio.gd](../../../games/yuga-native/scripts/rama_action_audio.gd) |
| Secondary/face motion | [rama_secondary_motion.gd](../../../games/yuga-native/scripts/rama_secondary_motion.gd), [rama_facial_performance.gd](../../../games/yuga-native/scripts/rama_facial_performance.gd) |
| Actual gameplay capture | [run-rama-gameplay.py](../../../games/yuga-native/tools/run-rama-gameplay.py) |

Lead assigns exclusive files and owns shared manifests/ledger. Coordinate W2
state display, W3 imported rig, W4 collision and W6 package/source freezes.

## Phase 1: freeze simulation and motion contracts

1. Record task ID, product/profile, exact baseline, exclusive files, reproduced
   defect, expected outcome and one adverse case that would reveal a regression.
2. Freeze action IDs, simulation clock, cast generation, release sequence,
   damage/cost/cooldown semantics, collision and pause/reset behavior unless the
   task explicitly changes them. Version and coordinate a changed contract.
3. Pin imported skeleton/rest transforms, root ownership, clip hashes, camera,
   locomotion inputs and sampling times. Never move collision to hide bad poses.

## Phase 2: implement and exercise boundaries

- `rama_motion.gd` is presentation. The offline army clock in the ability kit
  releases attacks; effects/audio consume events. Do not award damage, spend
  ammunition or finish cooldowns from animation callbacks or generated frames.
- Preserve commitment, cancel and visual release alignment. Cover interrupted
  windup, consecutive casts, hit/death/respawn, pause, focus loss, reset and
  locomotion/flight/grapple transitions relevant to the assignment.
- Test imported poses and advancing footage, not only authored curves. Inspect
  feet/support, knee/elbow continuity, bow/string/hand contact, cloth, face,
  rapid reversals, blend entry/exit and grounded/airborne boundary frames.
- Generated motion and foreign rigs remain candidates until terms, retargeting,
  scale/rest axes, skin, contact and actual-engine transition checks pass.
- Use the [handbook](../../../games/yuga-native/docs/BUILD_HANDBOOK.md) for
  relevant existing checks. Keep historical oracles and thresholds meaningful;
  investigate unexpected failures rather than rewriting them to force a pass.
- For assigned online work, freeze input/snapshot/elevation versions. Test
  original command replay, stale/duplicate inputs, reconciliation, teleport,
  delay/loss and reconnect against actual authority. A local replica fixture
  does not establish two rendered clients or a competitive team match.
- Queue heavy captures. Six agent roles share the confirmed 8 GB dedicated
  VRAM laptop; 16 GB shared system RAM is not extra equivalent GPU memory.
  A MoE model's active parameters do not represent all resident weights/cache.

## Phase 3: independent acceptance

W1 reviews source-matched originals, continuous motion and relevant actual
inputs. For networking require two rendered clients, then the larger-match
gate. Human game feel/listening and physical-hardware performance remain
separate from deterministic assertions and software-rendered capture timing.

Return source hashes, changed files, commands/results, event chronology,
originals, rejected experiments, remaining defects and next owner. One concrete
correction pass follows review; the lead owns ledger status and integration.
Preserve other owners' work and user state. Continue authorized independent
work without repeated confirmation. Do not introduce purchases, credential
disclosure, force-pushes or publication through this skill. User scope controls.
