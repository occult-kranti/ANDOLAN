# YUGA — guidance and city-lighting review cycle

Opened 16 October 2026 after the protocol-2 jungle baseline. This is a **new three-round cycle**, separate from the earlier [QA panel](PANEL.md). Reviewers are collaborating software agents: root moderator/client owner, story/content, systems, world/renderer, research, audio and QA. No human expert workshop, cultural consultation or participant playtest is claimed.

The accepted scope is small: optional first-session guidance, honest hero/upgrade explanations, and readable original day/night civic scenery. Fourteen heroes, forty-two abilities, all unlocks, the match economy and public-server requirements stay explicit. Each round records evidence, impact, decision, owner and acceptance; a pending check is not a passing round.

## Entry evidence and research boundary

The prior build passed eight focused native/presentation cases, a separate [480-second native finish and fresh replay](evidence/jungle-native-soak-check.json), the [168-match AI comparison](BALANCE_CHECK.md), isolated local stress, and the [21-asset production container](evidence/jungle-deployment-container.json) and root/nested browser checks. These are the starting baseline. New UI/scenery changes require their own checks; the earlier Docker image does not contain subsequently edited client code.

[Firsthand feedback F1–F7](research/DEADLOCK_PLAYER_FEEDBACK.md) comes from the bounded official sample of 40 posts/145 unique comments/26 requests. Counts include automated, removed, joke and media-only material. Learning and status-signifier examples coexist with enjoyment and an author's later positive matchmaking update. No prevalence, current competitor-bug diagnosis or watched-media claim follows. [Design research](DESIGN_RESEARCH_NEXT.md) records the publisher/author passages actually read; a bibliography or inaccessible paper is not a completed reading.

The separate [environment/mythology brief](ENVIRONMENT_MYTHOLOGY_RESEARCH.md) records selected lamp, day/night-weaving, courtyard and reservoir passages plus a distinct 19-post/21-comment contemporary sample. It does not convert those opinions into scripture, architectural authenticity or community approval. The civic rings and match-time light cycle remain original designs.

## Round 1 — source and design decisions

**State: design/source review complete for the accepted scope.** Root commissioned the implementation; numerical authority changes were not required. Cultural and player-research limitations remain open rather than being turned into fictional expert approval.

| Finding and evidence | Impact | Decision / owner | Acceptance |
| --- | --- | --- | --- |
| F1/F3 describe missed cues and unclear playstyle/build rationale, despite enjoyment. The roster has 42 skills and three upgrades with different formulas. | More compulsory instructions could make the opening harder; inaccurate upgrade advice could change spending. | Story authors all fourteen guides; root shows one first action, optional longer details and labelled upgrade tradeoffs. Free play stays immediate. | Exact current skill names and mechanics, distinct Power/Vitality/Tempo effects; later novice explanation remains a human gate. |
| An input press is not an accepted action or a skill assessment. Current snapshots include actual hit events, accepted ability events, ranks and capped camp receipts. | A goal could falsely celebrate a rejected cast, old event or another player's reward. | Systems builds five optional, pure observation goals; root integrates selection, dismissal and a fresh session baseline. No goal grants credits, rank or account power. | Old/repeated/foreign receipts do not complete goals; pause preserves state; death relocation does not count as movement; replay starts fresh. |
| The user requests day/night, lamps/diyas and circular civic spaces. Existing map authority has three lanes and eight shared solid-building definitions. | Dark backgrounds or ornamental geometry could hide threats or imply false cover. | World authors visual-only lighting and flat civic inlays, with fixed-day/fixed-night options, ambient/fill floors and reduced-motion handling. | Targeting, collision and combat rules stay unchanged; actual night/day, low/high and touch captures must preserve legibility. |

The design supports a voluntary stopping point: try an action, keep playing, change the next session or leave. It makes no motivation, wellbeing, retention or competitive-balance claim.

## Round 2 — implementation and independent source review

**State: guidance and environmental source review passed, including the narrow UI repairs. Native integration remains pending.**

| Implemented finding | Evidence and review | Decision / acceptance status |
| --- | --- | --- |
| Fourteen original guide records and 42 ordered skill notes | [hero-guide.ts](../shared/hero-guide.ts); full YUGA typecheck, targeted lint and exact roster/skill-name/prototype-ID checks passed. Research independently read every entry against current `heroes.ts` and the cast/upgrade branches. | Accepted as accurate source content. Counterplay is a suggested option, not a guaranteed win. Hero-specific exercises are prose, not additional automatic trackers. |
| Five optional Practice goals | [practice-goals.ts](../client/practice-goals.ts) and its fourteen unit cases cover real simulator observations, baseline/stale receipts, shared/capped camp rewards, death relocation and immutability. Story independently reviewed the implementation. | Accepted at helper level. “Hit” explicitly includes structures. Completion now says “Your hit was confirmed” / “Your ability started”, avoiding a false server claim for local Practice. |
| Lobby, guide, forge and HUD integration | Root integrated first action, native details, exact upgrade effects, labelled per-hero tradeoffs, Free play default and Practice-only goal HUD. Source review found the forge wrongly said the match continued during paused Practice, unlabelled tradeoff sentences, and Space competing with focused button activation. | Root repaired all three; story re-read the changed source. Actual keyboard/touch focus, layout and lifecycle must pass the next round. No human comprehension result follows from source approval. |
| World ambience and civic space | [environment-cycle.ts](../client/environment-cycle.ts), `scenery.ts` and `world.ts` implement the 480-second cycle, two directional lights, cached sky/materials, fixed modes, and reduced-motion handling. Source counts are 24 diyas, 26 lanterns, five flat plazas and zero point lights. Story and systems independently read the integration, footprint bounds and resource disposal. Eight pure-cycle tests pass, including 4,801 time samples; typecheck and targeted lint pass. | Accepted at source/numerical level. Palette values interpolate smoothly; sun/moon/star visibility has discrete thresholds. Construction diagnostics and actual day/night legibility remain browser gates. No new collision, target or combat rules are authored. |
| Aim cadence during slow rendering | Root moved keyboard/lock aim advancement to the existing input timer and resets its elapsed baseline for new aim input. The dedicated test uses ordinary keys with a deliberate five-frame-per-second render throttle and read-only observations. | Source reviewed; the native elapsed-turn and between-frame input assertions are authored but not yet run. This is a functional cadence gate, not a hardware frame-rate claim. |

The guide gives Power's 17% primary/12% applicable ability scaling, Vitality's +65 health and Tempo's primary-interval divisor. It does not invent cooldown reduction, stronger slows, longer summons, water immunity, skill unlocks or paid power. Support requires nearby living allies and clear sight; the UI states the clear-sight rule.

## Round 3 — integrated acceptance and release

**State: pending the completed source freeze and targeted QA.** The following are gates, not outcomes. QA owns actual evidence and the moderator closes the round only after examining it.

| Gate | Required observation | Claim limit |
| --- | --- | --- |
| Launch and bypass | Start Free play through ordinary keyboard and touch; select a focus; open/close a hero guide; start any hero without finishing a lesson. | Automation proves functional controls, not intuitive onboarding. |
| Goal lifecycle | Earn a real observed action; verify no reward/power addition; dismiss; pause/resume without reset; replay with a fresh baseline; online rooms show no Practice tracker. Keep fixtures labelled. | An accepted cast is not proven effective support or a successful dodge. |
| Accurate forge and controls | Inspect actual effects, rank/price and labelled hero tradeoffs. Focused button/summary Enter and Space activate UI rather than jumping or casting; out-of-range/paused copy matches mode. | No optimal-build or accessibility-certification claim. |
| Lighting and world | Exercise cycle, Fixed day and Fixed night; verify saved choice, reduced-motion behavior and clear live targets/projectiles/camp/shard states at low/high quality and narrow touch layout. Inspect raised/flat decoration against actual collision. | A still screenshot does not establish every transition, human threat recognition or hardware frame rate. |
| Delivery and regressions | Build the new client with every external GLB, record source/asset identity, run appropriate authority/input/replay checks and verify the actual published revision separately. Preserve ANDOLAN at the root. | The pre-guidance container/soak evidence remains historical for changed client code; static publication is not a hosted public WSS service. |

Unresolved production work includes the 48.64 MiB model payload, no measured consumer-device/WAN performance, no operated public matchmaking/WSS service, no human readability or cultural-consultation result, and remaining face/cloth/grip/material/effect polish. The [production roadmap](PRODUCTION_ROADMAP.md) and [art production plan](ART_PRODUCTION_PLAN.md) keep those obligations visible. Generated art sheets, a model count, numeric skin checks and AI matches do not establish commercial-art parity or human balance.
