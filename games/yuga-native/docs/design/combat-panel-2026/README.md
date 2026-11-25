# YUGA combat design · November 2026 panel

The current Confluence build has five actions each for Hanuman and Rama. Shiva and Krishna have animated preview rigs and proposed kits. The separate classic Rust sparring build has 14 heroes with a primary and three named actions each. This design pass adds a shared approach to anticipation, contact, recovery and counterplay while retaining the published timing and balance as the baseline. [Hanuman and Rama action pass](HANUMAN_RAMA.md) · [Shiva and Krishna proposals](SHIVA_KRISHNA.md) · [All 14 classic heroes](CLASSIC_ROSTER.md) · [Team combinations](TEAM_COMBINATIONS.md) · [Peer review and next checks](REVIEW.md)

The descriptions are a production brief. Each row labels implemented behavior and proposed presentation or mechanics. The actual authority, skinned motion and played match determine whether an item has been delivered. Four newly generated action boards are illustrated composition references for the animators. Their frames do not establish gameplay timing or 3D model quality. [Measured kit index](baseline.json) · [Illustrated action boards](../../../art/ability-keyframes-2026/README.md) · [Existing animator scripts](../../../art/four-hero-motion/README.md)

## Shared cast contract

The server accepts one cast and owns its generation, identifier, start tick, eligibility, collision and result receipts. A visual effect may predict a local aim preview, then follows the accepted cast. Deduplicate event-driven sounds and one-shot effects by generation and event sequence. Persistent ground effects track the accepted cast identifier and its authoritative field lifetime, even after the actor can start another action. Reconnect or late snapshot uses current cast age rather than replaying the opening cue. [Hanuman authority](../../../../yuga-rust/src/combat.rs) · [Rama authority](../../../../yuga-rust/src/rama.rs) · [Current renderer](../../../../yuga-rust/web/scene.ts)

Simulation runs at 20 Hz. Present at the display frame rate by interpolating snapshots and seeking the existing animation clip. Hanuman rounds the separate windup, travel and recovery durations to the nearest 20 Hz tick. Rama rounds up combined windup-plus-recovery for unlock. A 60 fps review frame is three times the authoritative tick age, but a rendered frame never creates a second damage event. The layered motion scenes use their own sampling rate and must align to the same server event. [Baseline generator](baseline.py) · [Game Programming Patterns, Game Loop](https://gameprogrammingpatterns.com/game-loop.html) · [Fix Your Timestep](https://gafferongames.com/post/fix_your_timestep/)

Use four layers with distinct jobs.

1. **Body** communicates who is acting and where, through the weapon, hands, gaze, support foot and tail or cloth.
2. **Ground or trajectory** communicates who or what space is eligible. Anchor it to the actor or ground target as the rule specifies.
3. **Result** marks actual recipient hits, heals, wards or blocked contact from authority receipts. Empty swings have no victim flash.
4. **Recovery** returns the body and transient effects to ready. Any longer-lived field stays independently anchored until its field end.

Use different shapes and edge patterns for hostile damage, allied support, valid aim and unavailable aim. Pair hue with geometry, text or iconography and optional audio. The player can turn off shake and reduce particles without losing the perimeter or state. A seven-metre Mountain Pulse radius spans an eight-metre lane, so its line must remain legible at the edges while targets remain visible inside. [Current map](../../../assets/world/confluence-map.json) · [Game Accessibility Guidelines](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-fixed-colour-alone/)

## Five review passes

| Pass | Decision and evidence |
| --- | --- |
| Baseline | Read the two profile JSONs, their Rust cast/impact code and all four prior actor scripts. The generated index records profile and authority hashes, exact 20 Hz release, unlock and field times. |
| Design | Preserve the live rules and specify body, trajectory, result and recovery for all ten live actions. Add clearly marked experiments and response tests for the eight proposed Shiva/Krishna actions. |
| Production | The separate motion artist is authoring a five-action Hanuman layered Blender study. Physics corrects interrupted vault height and adds player elevation to Hanuman's area checks. Their own files and tests carry the implementation evidence. |
| Challenge | Review collision and timing with physics, cue visibility and frame phases with the animator, and the eight-metre lane and team-color constraints with the world designer. Test blocked release, early landing and action interruption independently. |
| Handoff | Rebuild and check the baseline index after any authority edit. Use the action brief's prioritized tests to decide the next candidate before promoting it to the engine. Human balance and a physical-GPU playtest remain open. |

## Source notes

Robert Nystrom's *Game Programming Patterns* chapter on the game loop describes fixed-step update with a separate rendering cadence and interpolation. Its state chapter discusses isolating state transitions. This brief applies those principles to the existing YUGA server, whose exact semantics are defined by its code. [Game Loop](https://gameprogrammingpatterns.com/game-loop.html) · [State](https://gameprogrammingpatterns.com/state.html)

Glenn Fiedler's *Fix Your Timestep!* explains bounded update steps and interpolation between simulation states. The Game Accessibility Guidelines recommend pairing color with text, shape or pattern. Neither source establishes YUGA's network stability or a measured balance target. [Fix Your Timestep](https://gafferongames.com/post/fix_your_timestep/) · [Color guidance](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-fixed-colour-alone/)

Hunicke, LeBlanc and Zubek's MDA paper distinguishes authored mechanics, interactions during play and the experience players report. The counterplay listed here is a test intention. Human observation is needed to establish whether players actually read and use it. [MDA paper](https://users.cs.northwestern.edu/~hunicke/MDA.pdf)

The runtime profiles, scene builders and original animation scripts are the primary inputs for the numbers and markers. Public museum links in the hero scripts identify the specific religious and art-historical references used for Krishna and Shiva. Direct YouTube oEmbed requests were blocked in this session, so this packet does not claim that a video was watched or transcribed. [Hanuman](../../../art/four-hero-motion/scripts/hanuman.md) · [Rama](../../../art/four-hero-motion/scripts/rama.md) · [Shiva](../../../art/four-hero-motion/scripts/shiva.md) · [Krishna](../../../art/four-hero-motion/scripts/krishna.md)

## Maintain the timing index

Run from the repository root after changing either profile or its authority code.

```sh
python3 games/yuga-native/docs/design/combat-panel-2026/baseline.py
python3 games/yuga-native/docs/design/combat-panel-2026/baseline.py --check
python3 games/yuga-native/docs/design/combat-panel-2026/classic_roster.py
python3 games/yuga-native/docs/design/combat-panel-2026/classic_roster.py --check
```

The index verifies the current source formulas and Rama's clip map before writing. The classic generator checks 14 heroes, 14 primaries and 42 named abilities, then binds the output to the roster and simulation hashes. A change to an event definition still needs a code review and direct test.
