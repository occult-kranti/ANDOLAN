# Confluence: a duel of timing

This is a **24-second original combat film rendered inside the native game**. Rama meets an original Ravana sentinel in the authored Lanka courtyard. The story demonstrates a guard, a readable attack warning, an evade and a countershot. It is a focused animation/VFX/audio integration milestone. Its scripted visual receipts do not run the multiplayer authority, and its teaching holds do not define live hero cooldowns or balance numbers.

The canonical timeline is [confluence-duel.json](../assets/cinematics/confluence-duel.json). It is stored under runtime assets so the same script can drive interactive playback, arbitrary seeking, capture and the packaged game. The accepted full game design and production roadmap remain unchanged.

## Narrative and choreography

| Act and time | Visible action | Meaning and outcome |
| --- | --- | --- |
| Anticipation, 0–6 s | Two readable silhouettes settle. Rama draws; Ravana visibly raises a guard. The first arrow releases at 4.15 s and meets that guard at 4.75 s. | Defense is visible before the shot arrives. A blocked receipt records 0 damage; no false health loss accompanies the flash. |
| Counterplay, 6–17 s | A violet corridor marks Ravana's fixed wave path from 6.0 to 8.1 s. Rama steps sideways from 7.25 to 7.95 s, leaving the marked line before release. The wave reaches the old position at 8.9 s. Rama later draws and releases a countershot at 15.2 s; it lands at 15.85 s while the guard is down. | A warning gives time to react. The wave misses; the subsequent hit records 45 visual damage, leaving the sentinel at 55/100. The sentinel recoils rather than dying. |
| Resolution, 17–24 s | Both fighters return to a readable ready state. The camera holds enough space to see their separation and the outcome caption. | The lesson is warning → evade → counter. There is no additional unexplained attack, victory explosion or unsupported defeat. |

The duel uses two actors deliberately. Adding Sita would require a third production model, support animation, aim/counter timing, sound and camera responsibility before improving the current scene. Her film follows after the two-fighter pipeline passes; a placeholder third actor would weaken the immediate motion review.

## Scene and actor contract

- **Stage:** instantiate `res://assets/environment/lanka_courtyard.glb` directly. Exclude courtyard training and Confluence explorer controllers/UI. The film director owns camera, playback, actors and timeline effects.
- **Coordinates:** metres, +Y up, +Z forward. Positive yaw turns +Z toward +X. Actor root positions lie on y=0; visual model facing correction belongs to the actor adapter, not hidden per-cue coordinate changes.
- **Rama:** existing `rama-production.glb` is preserved. New film animation is in `duel-motion-rama.tres` under the runtime namespace `film`.
- **Ravana sentinel:** new original armour/crown/mantle on the established CC0 anatomy/rig, delivered as `ravana-sentinel.glb`. It is a study actor, not approval of the entire playable Ravana hero. Its motion library is `duel-motion-ravana.tres`, also under `film`.
- **Source ownership:** artist source, export provenance and rig/clip reports remain separate from the runtime JSON. No commercial character or animation is copied into the film.

Rama begins at [-3,0,-6]; Ravana at [3,0,6]. Rama's only root translation is a five-metre diagonal evade over 0.70 s to [-7,0,-3]. Its movement animation must visibly support that travel. If the first reel exposes skating, shorten the displacement or author the required step rather than hiding it with trails. Ravana rotates to track Rama between 9.2 and 10.2 s; this interval is a pivot, not a planted-foot claim.

## Animation beats and contact

| Actor | Clip windows | Required review |
| --- | --- | --- |
| Rama | Ready 0–1.8; draw 1.8–4.15; release 4.15–4.75; ready 4.75–7.25; evade 7.25–7.95; ready 7.95–12.8; draw 12.8–15.2; release 15.2–15.85; resolve-ready 15.85–24 | Feet remain grounded during draws/releases, the bow grip holds, the drawing hand/string relationship is visible, and the release/recoil differs from the held pose. Evade supports actual root travel. |
| Ravana | Ready 0–3; guard 3–5.5; ready 5.5–6; windup 6–8.1; release 8.1–8.9; recovery 8.9–15.85; recoil 15.85–17; ready 17–24 | Guard anticipation precedes impact; wave windup and release are distinct; recoil begins at the accepted visual hit; the tracking pivot does not masquerade as stationary contact. |

Animation libraries contain normalized one-second clips; the director maps each action's 0–1 phase to its imported clip length. Clip/window timing is explicit and deterministic. Blending is bounded by the declared in/out windows and must be inspected at every boundary. External actor motion owns root travel; animation does not independently add a second translation.

Contact windows explicitly distinguish Rama's moving evade and Ravana's pivot from stationary beats. QA should evaluate actual skinned sole height throughout, then tangential slip during intervals where both root position and yaw are stationary. A static pose with finite transforms does not establish believable footwork or bow articulation.

## Counter, VFX and sound contract

Every action, effect, receipt, camera segment, caption and sound has a stable ID. References use `actor_id` and `target_id`; projectile endpoints use `from_position` and `to_position`. The threat, warning, counter window and outcome are linked directly rather than inferred from prose.

| Outcome receipt | Warning/defense | Attack travel | Effect and audio timing |
| --- | --- | --- | --- |
| `receipt-opening-block`, 4.75 s | Visible Rama draw symbol before release; Ravana guard active 3–5.5 s | First arrow 4.15–4.75 s | Guard flash and block sound start at 4.75; Ravana health stays 100 |
| `receipt-wave-evaded`, 8.9 s | Locked corridor 6–8.1 s; Rama move 7.25–7.95 s, complete before wave release | Spectral wave 8.1–8.9 s ends at Rama's old position | Charge precedes release; movement trail follows actual path; no hit flash or damage on the evading actor |
| `receipt-counter-hit`, 15.85 s | Counter draw symbol 13.7–15.2 s; Ravana guard inactive | Counter arrow 15.2–15.85 s | Impact/recoil/sound and health 100→55 agree at 15.85 s |

VFX use distinct silhouette and motion as well as colour: a shield volume, a ground corridor, an arrow, a travelling spectral fan, a short movement trail and a localized impact. The corridor is a preview of the actual locked path; it must not move to chase the evading character. Flash intensity is restrained. Ground effects cannot conceal the feet being reviewed.

The audio owner builds original synthesized cue files and a 24-second, 48 kHz stereo mix at `assets/cinematics/audio/confluence-duel-mix.wav`. Cue kinds are bow draw/release, guard block, wave charge/release, evade, counter hit and resolution. Charge must be audible before release; impact cues agree with receipt times. A seek changes the mix position rather than layering another set of cue players. No audio or soundtrack is extracted from a reference game.

## Camera script

| Segment | Time | Camera position / look-at | Purpose |
| --- | --- | --- | --- |
| Establish | 0–3 | [12,4.7,-6] → [0,1.1,0], 48° | Side view with comparable actor sizes and clear separation |
| First draw | 3–5.5 | [10,3.2,-5] → [0,1.1,0], 50° | Show bow profile, guard and contact without covering the feet |
| Wave tell | 5.5–9.5 | [11,4.8,-5.5] → [-1.3,.9,-.3], 50° | Show the complete corridor, evade destination and missed endpoint |
| Counter | 9.5–15.85 | [6,3.2,-7.3] → [-2,1.1,1.5], 50° | Recenter on the new actor positions and preserve the action axis |
| Impact | 15.85–18 | [-.8,2.65,-.2] → [3,1.1,6], 43° | Cut to a closer frontal three-quarter reaction without implying death |
| Resolve | 18–24 | [8,4.5,-9.5] → [-2,1.1,1.5], 47° | Cut back to both actors for the final teaching beat |

Revision 3 replaces the rear-facing compositions after the actual first preview hid Rama's feet behind captions. Establish, draw, warning and counter remain on the same side of the action axis. Their declared blends are 0, 0.45, 0.50 and 0.70 seconds respectively; the impact and resolution use clean cuts. This removes the previous 10.8 m camera move over 0.18 seconds at the hit. Each segment then holds its absolute target, without accumulated orbit or frame-dependent drift. Geometric framing estimates leave footroom, but fresh actual renders must verify courtyard occlusion, weapons and warning visibility. Cue, action, receipt and audio timing is unchanged.

## Captions and accessible transcript

Captions are short and describe current or completed events. Block text appears at the block receipt, miss text at the miss receipt and hit text at the hit receipt. The outcome is not announced while the projectile is still travelling. Captions are on by default, with shape-based warnings and optional audio.

> CONFLUENCE. Rama draws. Ravana guards. Blocked — no damage. Violet marks the wave's path. Evaded. The wave misses. Guard down. Rama counters. Countershot lands. Ravana stands. Read the warning. Evade the line. Counter.

The full transcript is also in the runtime JSON. Film controls must support pause, restart, seeking, captions and return to the game. On loss of focus or exit, stop/park the mix and clear transient effects. Playback must not continue into an unrelated menu or training scene.

## Deterministic sampling and verification

The director samples one absolute time clamped to [0, 24]. Actor root interpolation, animation phase, camera, cue visibility, captions and displayed health are pure functions of that time. Seeking directly to 15.9 s must produce the same state as playing through 15.9 s. Restart, backward seek and repeated same-time calls must not duplicate effects or sounds. At 24 s the final pose/camera/health holds; nothing fires again.

Required evidence:

1. **Schema/chronology:** reject duplicate IDs/JSON keys, missing references/resources, nonfinite coordinates, descending or duplicate track times, overlapping actor actions and outcome claims ahead of their receipts. Warning windows precede their releases; counter windows contain the relevant event/receipt.
2. **Actual actor geometry:** imported resource names, rig/rest contract, finite deformed vertices, floor contact, foot slip during stationary intervals, hand/weapon relationships and continuous transition review. Retain intentional bad fixtures so detectors demonstrate rejection.
3. **Runtime seek and lifetime:** sample start, every action/camera boundary, each impact, the pivot, the evade midpoint and the endpoint; compare forward-play and arbitrary-seek state. Verify restart/audio cleanup and bounded effect counts.
4. **Rendered motion:** record the actual 24-second in-engine film and diagnostic views. Inspect anticipation, release, counter and recovery in motion, not just stills. Store source/content hashes, frame count, capture rate and encoder metadata. A fixed-time offline capture does not establish real-time GPU frame rate.
5. **Game integration:** launch film from native UI, pause/seek/restart/exit and return to play. Package includes the exact JSON, actor assets, libraries, effects and mix. Existing game movement/authority behavior remains separately tested.

## Four-round record

**Round 1 — contract.** Saved the canonical runtime JSON early: 24 seconds, 2 actors, 17 action windows, 10 VFX cues, 3 visual receipts, 6 camera segments and 10 audio cues. Shared names and positions with animation, engine, VFX, audio and QA owners so implementation could proceed in parallel.

**Round 2 — script and feasibility corrections.** Switched the stage from the full explorer scene to the authored courtyard GLB so unrelated controllers/UI are excluded. Standardized the animation namespace as `film`. Added explicit contact/counter windows and projectile/telegraph links. Corrected captions that originally described release/block too early. Kept the existing production Rama model unchanged and selected a separately authored sentinel actor.

**Round 3 — cross-discipline challenge.** Independent QA validates the canonical chronology and actual deformations. Artists check grip, feet and the distinction between ready/draw/release; VFX checks the locked corridor and fixed projectile endpoints; audio checks synchronized cues and safe seek. Any failure returns to its owner with the exact event/time/asset hash. Source motion or footage from commercial games is not a dependency.

**Round 4 — runtime and film review.** The first integrated preview contains 12 sampled full-scene frames. It exposed captions covering the evade footwork, distant sentinel framing and an unnecessarily fast impact-camera transition. Revision 3 changes only camera composition and blends; artists separately correct detached costume pieces and stage lighting. The 12 revised full-scene frames confirm visible feet, side profiles, a complete warning corridor and a closer reaction shot; these bounded composition corrections are accepted in the direction review. The continuous film, sound and native playback gate remains open until their own evidence is reviewed. A complete script, generated audio or a successfully exported model is not an accepted animated film.

## Full roster animation and film collection

The larger roadmap still governs the complete game. This film supplies a reusable director/cue/receipt contract, not a replacement for gameplay animation or network authority.

| Collection milestone | Deliverable | Acceptance gate |
| --- | --- | --- |
| One approved duel | This Rama/sentinel film, editable sources, exact 24-second video, timeline and packaged playback | Continuous contact/grip/event review plus seek/lifetime/audio tests |
| Gameplay event bridge | The same presentation cues consume accepted live shot/cast/hit receipts, with prediction confirmation/rejection and deduplication | Two native clients agree on timing/outcomes through reconnect; film-only visual damage cannot enter authority state |
| Three-hero studies | Rama, Hanuman and Sita each receive primary, three ability, counter and recovery studies | Each clip shows its complete anticipation/active/recovery and a visible counter; no placeholder model is silently called production |
| Six-hero interaction library | Add Ravana, Arjuna and Duryodhana; author paired shield/projectile, movement/control and support/damage interactions | Counter matrix, target attribution, contact and effect readability hold during movement and combined casts |
| Fourteen-hero collection | Add Karna, Bhima, Meghnad, Draupadi, Subhadra, Hidimbi, Chitrangada and Ulupi with the same five study categories | Every hero has source/provenance, actual animation/effects/audio, rig-specific tests and independent rendered acceptance |
| Armies and jungle films | Soldier, city watch, minister, king, Naga, Yaksha and Cloudwing windup/attack/support/leash/defeat studies | Visible animation agrees with actual server timing and rewards; crowd LOD/effect budgets remain bounded |
| Full match cinematic capture | Use actual native match/replay events for multi-hero shots and promotional capture | Source-labelled gameplay footage, complete match outcome, all platform/performance gates and no manufactured gameplay claim |

For each subsequent clip, reuse the timeline schema and test harness but author the appropriate rig, silhouette, contact and ability timing. Do not copy one draw/release pose across unrelated weapons or treat a camera cut as evidence that the hidden animation works.
