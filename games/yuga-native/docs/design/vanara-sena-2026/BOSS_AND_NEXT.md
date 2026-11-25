# Future design · coordinated guardians and an original boss

These concepts are **not implemented** in the 5v5 skirmish. There is no current boss mode, New Game Plus, Dharma meter, creature class system, stack/finisher rule or autonomous Vanara squad in the first ability slice. No boss from another game is recreated here.

## Companion research direction

If a later PvE mode needs controllable guardians, prototype one server-owned, short-lived squad as a separate feature rather than silently changing the current disk rule. Give each guardian a stable ID, team, lifetime, position, collision policy, animation state and a deterministic target/command policy. Start with three and prove navigation and camera clarity before evaluating a configurable five-to-seven formation. Their appearance, equipment, behavior and cultural treatment need individual authoring; do not repurpose paused enemy soldiers as an unreviewed shortcut.

Proposed player command: hold a dedicated command input and choose **gather**, **protect** or **flank**. Each command needs a visible endpoint, an audible/visual opponent warning, range and line-of-sight checks, a route failure response and a cancellation condition. A flare or channel should reveal flank intent; pathfinding may not jump walls, cross water or use temple folds unless the world authority explicitly supports those paths. Guardians should not pass information about unseen enemies to a team. Individually targetable units would need per-unit health, clear destruction/dismissal feedback and a gameplay justification for each added entity.

Before online testing, specify spawn obstruction and overlap resolution, owner defeat/disconnect, late join, reconnect, event deduplication, deterministic ordering, packet bounds, authority/state lifecycle, despawn and spectator/visibility behavior. Stress the worst allowed simultaneous casts and evaluate target-frame time, bandwidth, overdraw, readability and accessibility. Do not imply an AI squad is present merely because five spectral visuals are rendered.

## Original PvE boss proposal: The Silt-Crowned Warden

A fictional stone-and-reed guardian watches a flooded causeway near an abandoned stepped sanctuary. This is a new YUGA encounter, not a depiction of a specific religious figure or a reconstruction of another game's boss. Its role is to test a coordinated team against clear terrain changes and telegraphed attacks. It belongs in a future opt-in co-op/PvE mode, not the current competitive map.

### Encounter beats

1. **Read the stance.** The Warden plants a staff and drags a curved trail of silt. A distinct ground pattern and drum accent identify the area before a broad, avoidable sweep. A dry exit and a low-cover route remain visible.
2. **Water warning.** At a health threshold chosen after testing, it summons two shallow pools with clearly timed edges. Pools are environmental hazards, not evidence that all Vanaras can automatically leap, swim or path across them. Players can use the dry banks and normal traversal.
3. **Guard phase.** It kneels behind a shield of loose stone. A segmented meter and changed silhouette explain reduced incoming damage from the front; exposed side markings and an authored recovery window invite positioning. A hit from the current Vanara Sena field deals only its defined normal damage unless a later, explicitly implemented guard rule says otherwise.
4. **Team opening.** When the Warden finishes a heavy attack, teammates can take space, heal or use Hanuman's marked field. The field offers area pressure, not guaranteed pinning, armor shatter, divine stacks or a forced cinematic finisher. The Warden can escape or counter if its rules permit.
5. **Resolution.** End attacks and damaging pools deterministically on defeat or encounter reset. Disperse visual echoes and present the result without classifying an entire community of mythological beings as hostile.

Candidate thresholds, damage, timers and rewards are deliberately **unspecified**. Establish boss health and action timing through a playable graybox and recorded playtests. Add an optional practice mode with one clear attack at a time before layering phases.

## Optional resource and synergy design, later only

An optional future PvE “Dharma” resource could reward observable cooperative actions, but its religious framing, accessibility and anti-farming policy require consultation. Do not label a kill, purity score or forced choice as a canonical moral judgment. Define exact earn/spend events, caps, reset, UI, cooldown and accessibility alternatives before coding. There is no such meter now.

Likewise, a future elemental interaction could add a small, visible, capped and server-owned mark with a counter and expiry. It must be separately balanced in 5v5 and PvE, cannot be inferred from saffron particles, and would need explicit stacking, overlap, ability-to-ability ownership, death/disconnect and anti-exploit tests. No Sacred Flame stacks, 2.5× burst, Brahmastra finisher or enemy-type damage multiplier is present in the current slice.

## Progression gates

| Gate | Evidence required |
| --- | --- |
| Competitive field | Bound the current action's counters and communication in actual human matches; no persistent minion waves. |
| Animation and art | Accepted rigged guardian, material, sound and motion design at game scale, with sources, accessible presentation and budgets. |
| One moving guardian | Server authority, obstacle/collision and target-selection tests, distinct player counter, state lifecycle and gameplay capture. |
| Coordinated squad | Deterministic formation behavior, five-to-seven entity limits, duplicated/delayed command handling, mixed teams and target-hardware stress test. |
| Original co-op boss | Separate authored enemy, water/terrain gameplay, telegraphed phases, playtest outcomes and recovery/reset tests. |
| Optional progression | Tested economy and UX, community/cultural review, published rule descriptions and no claim of historical scriptural authority for invented mechanics. |
