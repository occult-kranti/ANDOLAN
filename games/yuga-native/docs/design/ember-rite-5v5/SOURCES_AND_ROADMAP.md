# Ember Rite · sources and next work

## What was consulted

Accessed 25 November 2026. The user's long ASTRA/Yagna draft is **creative input from another chat**, not an externally verified source or a record of shipped functionality. The following source reads are bounded; they do not claim the entire books, legends, games, films or communities were reviewed.

| Source | What it informed | Limit |
| --- | --- | --- |
| [Britannica: rasa](https://www.britannica.com/art/rasa) | Aesthetic experience and the listed emotional modes, useful for discussing mood. | It does not validate fixed hex-to-emotion mappings, a universal 60/30/10 rule or quantitative size/visibility claims. |
| [W3C: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) · [Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) · [Text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | Do not use color alone; contrast thresholds guide applicable UI text and meaningful non-text indicators. | A design table or raw swatch calculation is not a full WCAG or game accessibility audit. |
| [Game Accessibility Guidelines: fixed color](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-fixed-colour-alone/) | Offer redundant cues and accommodate different color perception and preferences. | It does not establish actual readability of any YUGA frame. |
| Glenn Fiedler, [“Fix Your Timestep!”](https://gafferongames.com/post/fix_your_timestep/) | Fixed-step simulation helps define interaction and deadline ordering independently of rendered frames. | A fixed 20 Hz timer alone does not establish deterministic networking, fair latency, physics parity or presentation smoothness. |
| [Britannica: Hanuman](https://www.britannica.com/topic/Hanuman) · [Arjuna](https://www.britannica.com/topic/Arjuna) · [Krishna](https://www.britannica.com/topic/Krishna-Hindu-deity) · [Kali](https://www.britannica.com/topic/Kali) · [Durga](https://www.britannica.com/topic/Durga) · [Ravana](https://www.britannica.com/topic/Ravana) | Initial, short secondary-source checks for mythology and varying portrayals. | These do not validate YUGA's weapons, abilities, game skins, chronology, or one definitive religious interpretation. |
| [Wikipedia: Draupadi](https://en.wikipedia.org/wiki/Draupadi) · [Karna](https://en.wikipedia.org/wiki/Karna) · [Shakuni](https://en.wikipedia.org/wiki/Shakuni) · [Ghatotkacha](https://en.wikipedia.org/wiki/Ghatotkacha) | A preliminary lead-paragraph orientation to the characters' Mahabharata connections. | Secondary starting points, not primary-text or community review. Obtain specific translated passages and cultural review before final names, representations or lore. |
| [Project museum-art gallery](../../research/art-history-panel-2026/README.md) · [Previous Vanara source ledger](../vanara-sena-2026/SOURCES.md) | Previously documented Hanuman, Rama and Krishna visual sources and their provenance; distinction between literary inspiration and invented mechanics. | The selected gallery is not a complete source set for all ten heroes. Confirm individual image rights before reuse. |
| [Mandala Rift objective proposal](../mandala-rift-5v5/MATCH_SCRIPT.md) · [current Rust README](../../../../yuga-rust/README.md) | Existing 5v5/no-wave direction, proposed plant/disarm flow and actual current skirmish scope. | The old proposal's numbers and Rift Seal presentation are superseded by the new Ember Rite proposal, not silently implemented. |

An attempted Riot `playvalorant.com/en-us/how-to-play/` page returned HTTP 404 in this session; no gameplay details are attributed to that page. The objective rules here are YUGA design decisions inspired by the user's supplied description, not a claim to have recovered another game's internal implementation.

## Corrections to the supplied draft

1. A 6 m unavoidable damage zone at a 3.5 s quench would make the objective disproportionately costly to defenders. Start with no automatic field damage or team speed bonus, then measure any later change.
2. A 3-second return-to-spawn on dropping the vessel can make recoveries arbitrary and erase counterplay. Keep a server-validated ground drop until recovered or the round resolves.
3. At 12–12, a 13–12 score is not a completed paired overtime. Play both sides, require a two-round lead after the pair and use a declared bounded-draw rule.
4. After ignition, attacker elimination does not automatically defeat the fire; defenders still need to quench. Before ignition, a simultaneous wipe resolves for defenders; after it resolves for attackers. The order is explicit and tested in the isolated experiment.
5. Fixed “good/cool” and “evil/warm” player colors break down when teams switch sides, ignore color-vision differences and conflate appearance with morality. Use viewer-relative, shape-coded cues and separate each hero's art palette from team status.
6. Shakuni and Krishna are already present in the proposed initial cast; later seasons may spotlight them rather than introducing the same character twice. A raw global 51% win count does not yet create a fair world-state service.
7. The “every hero is a mortal carrying a divine soul” premise is a fiction choice, not a summary of the original traditions. YUGA uses fictional echoes and records its creative choices separately from sourced traditions.

## Roadmap

| Order | Next owner / task | Evidence required |
| --- | --- | --- |
| 1 | **Game design:** validate this rule contract, interaction timing, 13-round duration and side-swap language against actual play goals. | Reviewed state diagram, complete tick precedence, tutorial examples, no unresolved contradictory wins. |
| 2 | **Authority:** connect the standalone rules experiment to a server-owned round/movement/damage model, legal sites and no-respawn lifecycle. | Real collision/LOS and same-level checks, held-input sequencing, all wipe/timer edges, channel blocking, legal drop/recovery, authenticated requests and authoritative outcomes. |
| 3 | **Network and UI:** add versioned commands, events and snapshots to both native and Wasm room paths; build briefing, carrier, channel, timer and result interactions. | Native/Wasm deterministic parity; ten seats, duplicate/stale commands, disconnect/reconnect, late join, no hidden-information leakage and two rendered clients. Resolve the existing Sena presentation stall. |
| 4 | **World and art.** Use the [reviewed four-map atlas](atlas/README.md) and first bring Mandala’s dry routes, roofs, collision and site lips into a playable blockout. Reuse reviewed YUGA world modules for the ghat and market, then place approved landmark forms. Use the [five-hero animation intake](../animation-tech-codex-2026/ROADMAP.md) for motion. | Two ordinary routes from each spawn to each site in engine, exact vessel reach, both-shoulder views, matched form and visibility review, then the scripted ten-seat retake. Source drawings and offline massing are ready for this work. |
| 5 | **Hero and game design:** select a minimum playable roster, define and tune each proposed ability, economy and support-credit rule. Keep the existing two-hero skirmish working meanwhile. | Authority receipts, counters, telegraphs, accessibility, reset/death tests and observed player comprehension. More hero concepts do not close a playable roster gate. |
| 6 | **Playtests and operation:** test private rounds, then decide whether a shorter format and a ranked service are justified. | Human 5v5 results and reasons, side/map balance with uncertainty, hardware frame-time and accessibility checks, abuse/reconnect/privacy review and tested deployment. |
| 7 | **Story:** produce the prologue only after voice, cultural-source, accessibility, animation and asset approvals; consider opt-in seasonal voting later. | Actual footage/audio/captions, source and consent records, explicit global-data rules and fallback. No claim that seasons or a global world state exist today. |

The standalone round/series experiment and its tests are an early step under task 2. It does not complete task 2, the old backlog, an online match, first-person play, or the broader commercial visual-quality target.
