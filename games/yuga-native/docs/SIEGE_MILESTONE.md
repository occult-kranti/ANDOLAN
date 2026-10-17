# Siege vehicles and the route to the visual target

17 October 2026. Supporting offline-native packet for FG08/FG13. The current build is Godot 4.6.3, with original assets; the commercial reference games have not been reconstructed. Production authority, the full roster and final graphics gates remain open.

## Five parallel tasks

| Packet | Owner | Deliverable | Acceptance |
| --- | --- | --- | --- |
| SIEGE-01 | Gameplay / native_engine | Cannon carts, royal chariots, wave scheduling, collision, committed blasts and drill | Mirrored reinforcements; bounded actors/attacks; walls, dodge, death, reset and exactly-once rewards tested |
| SIEGE-02 | Vehicle art / world_nature | Original brass, wood and cloth models; wheel, recoil, hit and defeat motion | Two roles/teams readable in actual renders; finite continuous poses; bounded shared geometry |
| SIEGE-03 | Effects / traversal_audio and audio worker | Ground warnings, projectile arcs, impacts, original synthesized cues | Visual warnings work muted; bounded effects/voices; pause/reset/focus safe; cue provenance retained |
| SIEGE-04 | World UX / full_game_roadmap | Immediate Siege practice entry, HUD, minimap and settings integration | Keyboard and mouse entry/exit; compact-screen menu; regular reset restores ordinary lanes |
| SIEGE-05 | Independent QA / world_collision_qa | Adversarial combat, lifecycle and pose checks | Real damage/event assertions, sustained simulation, current-source reports and actual render review |

These are supporting prototype tasks, not substitutes for the dependency-ready production tasks in `ROADMAP_BACKLOG.json`. Round 1 fixes interfaces and failure cases; round 2 implements; round 3 challenges the integrated result. A defect triggers a bounded correction and rerun. The root integrator owns source freeze, roadmap, package and release evidence.

## Gameplay contract

Ordinary practice retains its initial thirty soldiers. A cannon pair can reinforce each lane on every third wave; a royal-chariot pair can reinforce the centre on every fifth. Each pair must fit both teams' spawn clearance and the global capacity. A rejected pair does not produce a one-sided reinforcement. The existing bounds remain 72 live units, 24 corpses, 96 total units and 72 pending attacks.

Cannon shots commit to a ground location before impact. Visible anticipation, a fixed blast location and a slow repeat rate create opportunities to move away or defeat the attacker. Royal chariots are elite lane units, with their own silhouette and shorter-range attack. They are not a completed jungle-boss encounter. Siege practice stages the same units and rules for immediate inspection. Normal reset returns to the ordinary wave schedule.

This offline army simulation handles troop and core damage plus the hero's last-hit gold. The native hero currently has no health/death receiver in this world: siege blasts are not advertised as damaging the hero. Authoritative team economy, contested gold, boss rewards and production player combat remain FG08/FG04 work.

## How long to the concept target?

The comparison is between [`rama-hanuman-sita.png`](../../yuga/art/references/rama-hanuman-sita.png) and actual native captures, including [the previous army encounter](evidence/traversal-armies-render-r2/still-army-engagement.png). The concept has detailed anatomy, faces, hair, layered costume, engraved materials and intentional lighting. Current procedural troops and world dressing remain prototype art. Additional objects alone cannot close that gap.

**Planning estimate, not an established delivery schedule:** with a stable scope, funding, an experienced core team of roughly 8–12 people across character/environment art, animation, technical art, gameplay/network engineering and QA, and dedicated audio/UI support, budget roughly **3–6 months for an accepted visual vertical slice**: one arena, two finished heroes, representative troops, abilities and a complete playable encounter. The roadmap's three-hero networked slice has additional integration gates. A fourteen-hero competitive online game at the requested standard could require **18–36+ months and a larger production/operations team**. There is no measured project velocity or staffed production budget yet, so neither range is a promise. Agent concurrency reduces some implementation and research time; it does not establish art approval, hardware performance or player acceptance.

Replace calendar guesses with these successive gates:

| Gate | Required proof | Current gap |
| --- | --- | --- |
| Visual benchmark | Approved gameplay-distance comparison against the concept, same lighting/camera and explicit style/material targets | Concept exists; final in-engine appearance is unaccepted |
| First hero | Editable source, anatomy/silhouette, face/hair/costume, PBR materials, LODs, clean rig and readable weapons | Rama preview exists; source recovery and production corrections remain |
| Motion and effects | Continuous run/aim/attack/ability/hit/defeat transitions, foot/grip contact, release-to-hit timing, counters visible in crowds | Numerical and bounded motion studies exist; full production motion remains |
| One complete arena | Accepted modular city kit, terrain/swamp/water, collision, lighting, navigation, troop scale and fight readability | Playable extended world exists; final environment art remains |
| Integrated performance | Complete encounter on declared minimum/recommended GPUs; frame-time/memory budgets under actual load | Software rendering is available; physical-GPU qualification remains |
| Competitive slice | Rendered authority, reconnect, player death/result/rematch, bots and measured human playtests | Transport studies and offline armies exist; integrated online acceptance remains |
| Full production | Remaining heroes/maps, balance, accessibility, security, matchmaking, operations and support pass their milestone gates | Keep all corresponding production tasks open until evidence exists |

Review the estimate after the first accepted hero and arena benchmark. Record actual authoring/revision time, hardware traces and player findings. Expand roster production only after those pipelines produce repeatable accepted output.

## Evidence and current status

Implementation and verification are in progress. This section is replaced with the final source, executed checks, render/package evidence and remaining defects before acceptance. The previous public release remains the verified download until a new release is independently checked.
