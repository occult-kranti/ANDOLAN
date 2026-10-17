# Combat film direction and acceptance review

Status: **revised still-frame composition accepted; revision 4 screenplay, native-viewer and numerical motion checks pass; full video and packaged-window review pending**. This is a native animation/presentation prototype. It does not establish Deadlock-level graphics, a finished Ravana hero, live multiplayer combat or the full game's visual target.

The [screenplay](COMBAT_FILM_SCRIPT.md) describes the intended action. The canonical runtime manifest is [confluence-duel.json](../assets/cinematics/confluence-duel.json), revision 4, SHA-256 `6ec07cb86aa645ba23c4eec51e652bbe89ad42d0558225583f6a8dd54248af6b` at this review. The accepted R2 still-frame composition used revision 3 (`a7f9c8263f0117fa322f5a51ff765710bfe619026c076eda32d207aaf8be5826`). Revision 2 (`5a641d8febad461b633bf5fb5edd80e9a3429ab3754ad21b01e2e90e5aecaea4`) is the captured first preview. Revision 3 changes cameras and the revision number only; cue, action, receipt and audio content is identical. Evidence from another manifest/actor/library revision must be identified separately.

## Current evidence boundary

| Evidence | Observed result | Limit |
| --- | --- | --- |
| `tests/evidence/combat-film-script-final.json` | 20 screenplay/resource checks pass on revision 4, with actual asset resources and 24-second audio duration verified | Scripted receipts and resource validity do not certify gameplay authority or perceptual sound quality |
| `tests/evidence/combat-film-integration-final.json` | 42 imported-animation/native-viewer checks pass; nine clips per actor, finite poses, sole geometry, seek, lifecycle and wired UI behavior evaluated | Headless callback/layout tests are distinct from operating-system input, visible animation quality and package execution |
| `tests/evidence/combat-film-motion-continuity-final.json` | Five continuity checks pass on revision 4; 577 time samples, zero frame-speed alerts and continuous action boundaries | Numerical pose continuity does not establish artistic quality, gameplay movement or cloth physics |
| `tests/evidence/combat-film/duel-effects-cases.json` | 32 bounded VFX configuration, sampling, lifetime, projectile-origin and invalid-input checks pass on revision 3 | Headless component behavior does not establish visible effect quality, actor contact or integrated playback |
| Script/camera preflight | Clear guard → warned wave → evade → counter causal sequence; planned actors fit the main wide camera frusta in a geometric estimate | Estimated framing is not actual occlusion, animation or UI review; the effect can still hide the hands/feet |
| `build/film-poses-r2/combat-film-render.json` | Actual Forward+ studio report contains eight static poses; this reviewer inspected Rama draw/release and Ravana guard | Detached red/gold pieces are visible beside Ravana. Static poses do not establish smooth transitions or staged-film framing |
| `build/film-scene-r1/combat-film-render.json` | Twelve actual integrated frames at 960 × 540 on Godot 4.6.3 Forward+ / llvmpipe, revision 2 | Sampled frames reveal composition defects; they are not a 24 fps continuous recording or a real-time hardware benchmark |
| `build/film-scene-r2/combat-film-render.json` | All 12 revised actual full-scene frames independently inspected; footroom, two-shot profiles and reaction framing corrected | Bounded still-frame acceptance only; continuous motion, sound listening and native controls remain separate gates |
| Continuous render, sound listening and game UI | Pending exact evidence from the revised integrated build | Do not mark these complete from the source manifest or isolated test counts |

This milestone contains two skinned actors, two libraries with nine clips each, a 24-second deterministic director, ten visual cues, three scripted outcome receipts, captions and original synthesized audio. The planned [cinematic preview release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-confluence-duel-2026-10-17) is not recorded as published until its video/package evidence is supplied. Existing map-preview download facts remain unchanged. Audio has numerical duration, level and cue-timing evidence; this review makes no listening-quality claim.

## Direction preflight and retained motion gates

**Readable cause and effect.** The first shot is visibly guarded before its receipt. The wave warning occupies the same locked line the wave will travel; Rama completes the evade before release. The counter lands after the guard is down. Captions appear at current/completed beats instead of announcing an outcome during projectile travel. Keep these relationships when revising animation or camera timing.

**Framing.** The first actual preview confirmed that placing both actors inside the camera frustum was insufficient: the camera mostly saw Rama's cape, the sentinel was small, and captions covered near feet. Revision 3 uses side/three-quarter two-shots with more comparable actor sizes. Fresh R2 frames confirm the intended footroom and actor profiles. Diagnostic close-ups still need to inspect grip and release rather than treating a wide shot as proof.

**Impact camera.** Revision 2 moved the camera approximately 10.8 m over 0.18 s at 15.85 s. Revision 3 replaces that move with a clean cut to a closer reaction view and cuts back to the two-shot at 18 s. The intended result is clear contact/recoil without a fast synthetic dolly. Continuous playback must still confirm the edit; damage and audio were not retimed.

**Movement risk.** Rama travels 5 m during a 0.70 s evade. A posed body translated across that distance would read as skating even if sole-height tests pass. The continuous capture must show a believable step/dash impulse and recovery. Contact tests apply differently to movement, pivots and planted bow shots. Trails must not cover a failed footwork transition.

**Momentum and intent.** The film contains a 3.9 s recovery gap before the counter draw and a 7 s resolution. These are teaching pauses, not proposed live ability cooldowns. They can make the action understandable, but the first continuous pass must check whether the actors have enough purposeful settling, breathing and attention to sustain the hold. If the hold is static, the follow-up production edit should shorten or animate it; adding camera motion alone will not fix inert actors.

**Presentation hierarchy.** Keep warning shapes on the ground, held guard around the defending actor, projectile trails narrow and hit flash localized. The bow hands and planted feet remain visible. Sound reinforces what is seen: charge before release, impact at receipt, no hit cue for the evaded wave. The two gold/violet identities also need distinct shapes, not colour alone.

## Actual-render inspection record

Selected studio poses from `build/film-poses-r2/` have been inspected. Their report pins Rama to `6657f4bf…`, Ravana to `2c3df8bd…`, Rama motion to `79b6992d…` and Ravana motion to `19e43c0c…`. Rama draw and release have distinct arm silhouettes. Ravana guard shows three small red/gold pieces floating to the left of the body; the artist has been asked to inspect leftover bow decoration and armor fit. This is a concrete correction request, not a visual acceptance.

The first staged preview is `build/film-scene-r1/`, with archived evidence under `docs/evidence/combat-scene-r1/`. Its source manifest is revision 2. The report contains **12 sampled frames**, despite a capture-rate field of 24 Hz; it is not a 576-frame recording. It took 53,658 ms on software rendering, which does not establish consumer-GPU frame rate.

| Actual frame | Observation | Disposition |
| --- | --- | --- |
| `frame-00000.png`, 0 s | Rama is seen from behind; the sentinel is much smaller. Empty paving dominates the encounter. | Revision 3 moves the establishing view to the side and equalizes actor depth. |
| `frame-00002.png`, 4.3 s | Arrow and guard are legible, but Rama's back hides much of the hand/weapon relationship. | Side-profile draw composition authored; actual grip review remains required. |
| `frame-00003.png`, 4.85 s | Guard feedback surrounds the sentinel and the HUD reports blocked/no damage. The caption panel covers Rama's lower legs. | Camera footroom correction authored; VFX owner confirmed the explicit impact position stays on the sentinel. |
| `frame-00004.png`, 6.7 s; `frame-00005.png`, 7.65 s | The violet corridor is readable. During the evade, the caption covers Rama's feet, preventing a useful movement-contact review. | Higher side view includes both the fixed corridor and evade destination; motion acceptance remains open. |
| `frame-00007.png`, 13.9 s | The counter is again a cape-dominated rear view with a distant target. | Recentered side two-shot authored for the post-evade positions. |
| `frame-00009.png`, 16.1 s | The HUD correctly shows 55 health and the sentinel stands, but the reaction is small within a large expanse of court. | Closer frontal three-quarter reaction cut authored. |
| `frame-00011.png`, 23.95 s | Both fighters remain standing. A still cannot show whether the long hold contains purposeful motion. | Short-term timing stays fixed for this capture; continuous review must assess settling and pace. |

Stage material chatter and detached sentinel ornament were referred to their owners. Those are separate asset changes and need fresh source hashes. The camera revision alone cannot resolve them.

### Revised full-scene review

`build/film-scene-r2/combat-film-render.json` records 12 actual 960 × 540 Forward+ frames, using llvmpipe and manifest revision 3. The complete set was independently inspected at 0, 2.75, 4.3, 4.85, 6.7, 7.65, 8.55, 13.9, 15.45, 16.1, 18.5 and 23.95 seconds. The report pins these revised components:

- Rama remains `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`.
- Sentinel is `f00bed98cc11847da41d2f9f13ef9119e3ed983d41ca6dd7a14862a1c80672ca`.
- Rama film motion is `3ab73222e16d6925eb972f900e385fd18d1b3df2c47a6b744663be7007f0df94`.
- Sentinel film motion is `d0d0f3b23dff6c12bc0174f3e1cedb66475ba85c0c8e61c533800f0d0a8ea3be`.

**Accepted bounded corrections:** the two-shot now shows both actors in profile with comparable screen size. First-block and evade frames leave the complete feet above the caption panel. The full warning corridor, old target location and moved Rama are visible together. The 8.55 s wave frame shows travel along the original line while Rama is clear of it. The 15.45 s arrow is legible, and the 16.1 s sentinel reaction is closer with intact standing silhouette and 55 health. No additional camera edit is required for this prototype pass. The previously floating red/gold pieces are not visible in the revised reaction view; this observation is not a replacement for the artist's geometry checks.

**Remaining quality limits:** broad paving and repeated architecture still dominate the set; character proportions, material finish and deformation remain prototype work. Early draw anticipation is subtle in the selected stills. A 5 m evade, the pivot, clip boundaries, cuts and long ready holds must be evaluated in motion. None of these frames proves cloth physics, smooth foot contact, production bow-string behavior, final roster quality or real-time performance.

### Revision 4: guard-reset correction

The preserved [revision 3 continuity report](../tests/evidence/combat-film-motion-continuity-revision3.md) passed its finite-pose and micro-boundary gates, but flagged a fast sentinel guard reset around 5.54–5.58 s: the reported 24 Hz sample step changed forearm orientation by 50.20° and fingertip position by 0.2663 m. Finite transforms and continuous interpolation therefore did not establish acceptable motion. The preceding 12 stills did not sample this transition.

Revision 4 changes only `ravana-ready-wave.blend_in_seconds` from 0.12 to 0.32 seconds, inside its existing 5.5–6.0 s action window. The action start/end, every effect/receipt/audio time and all cameras remain unchanged. A deep equality assertion checked that the revision number and this single blend field were the only manifest changes. The revision 3 evidence is preserved. Independent QA reran unchanged tests and thresholds on revision 4: 20 screenplay, 42 native integration and 5 continuity checks pass. The guard-reset maximum 24 Hz travel falls from 0.266273 to 0.106485 m, accumulated rotation from 50.2016° to 19.4095°, and local rotation from 49.6560° to 19.1736°. No frame-speed alerts remain; action boundaries and planted-contact gates still pass. The final continuity report SHA-256 is `4e54fddd377249740cc032f235126753a7ee9d5456c08359d221678805fa8dec`. This accepts the bounded numerical correction; the continuous render still needs visual review.

With revision 4 passing the independent transition checks, the next gate is a continuous 24-second recording of the frozen revision. Review the whole bow release, transition into and out of the evade, sentinel pivot, both camera cuts, effect/audio contact and final settling. During native-window testing, exercise pause, seek, restart, captions and return; verify that exit stops audio and clears temporary effects. A contact sheet supports pose review but cannot establish smoothness or sound synchronization.

## Release evidence checkpoint

The planned tag is [`yuga-confluence-duel-2026-10-17`](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-confluence-duel-2026-10-17). The following outcomes remain open until root supplies the matching evidence:

| Deliverable | Current status | Required release record |
| --- | --- | --- |
| Complete film | Rendering in progress | Exact video hash, resolution, frame count, duration, audio stream and source manifest; actual transition review |
| Linux native package | Pending final package/window evidence | ZIP hash, extracted launch and actual film controls/return behavior |
| Windows native package | Pending final package evidence | ZIP hash and archive/resource validation; execution status stated separately |
| Public release | Planned | Published URL and downloadable asset names/hashes |

This release is an original scripted animation prototype. It does not complete the full hero roster, live native multiplayer, match authority, production physics or the commercial visual target. Offline rendering on llvmpipe is not evidence of consumer-GPU frame rate. Audio listening remains unverified unless an explicit listening result is added.

## Collection roadmap tied to existing full-game gates

Films are supporting studies. They do not complete the referenced game tasks by themselves, and this document does not change backlog statuses.

| Hero | Existing production gate | Required study package |
| --- | --- | --- |
| Rama | FG02-T05 model/rig; FG03-T04 motion and complete kit | Primary draw/release, three individual ability studies, counter/recovery study; current film is a prototype input |
| Hanuman | FG06-T01 | Primary, three abilities and counter/recovery with leap contact and landing readability |
| Sita | FG06-T02 | Primary, three abilities and counter/recovery with clear support recipients and expiry |
| Ravana | FG07-T01 | Primary, three abilities and counter/recovery; current sentinel is a study actor, not this hero's completion |
| Arjuna | FG07-T02 | Primary, three abilities and counter/recovery with a distinct archery rhythm |
| Duryodhana | FG07-T03 | Primary, three abilities and counter/recovery with mace weight and contact |
| Karna | FG10-T01 | Primary, three abilities and counter/recovery with authored weapon and projectile timing |
| Bhima | FG10-T02 | Primary, three abilities and counter/recovery with grounded heavy motion |
| Draupadi | FG10-T03 | Primary, three abilities and counter/recovery with readable ally/enemy effects |
| Ulupi | FG10-T04 | Primary, three abilities and counter/recovery with water-themed boundaries and contact |
| Meghnad | FG10-T05 | Primary, three abilities and counter/recovery with visible warning and escape opportunities |
| Subhadra | FG10-T06 | Primary, three abilities and counter/recovery with distinct command/support cues |
| Hidimbi | FG10-T07 | Primary, three abilities and counter/recovery with authored creature/hero silhouette behavior |
| Chitrangada | FG10-T08 | Primary, three abilities and counter/recovery with spear reach and recovery windows |

The initial collection estimate is five studies per hero: one primary, three abilities, and one explicit counter/recovery scenario. That is planned work, not 70 completed clips. Each ability still requires its gameplay counter and interaction checks; a single general counter film does not replace the matrix in FG10-T09.

| Supporting collection | Existing gate | Acceptance required beyond the video |
| --- | --- | --- |
| Soldier, city watch, minister, king | FG08-T01 | Animation events agree with actual attacks/buffs; original weapons, readable anticipation, hit/defeat and army LOD cost |
| Naga, Yaksha, Cloudwing | FG08-T02 | Attack/leash/reset/respawn and temporary-buff outcomes agree with authority; readable counterplay |
| Shared effects and sounds | FG11-T03 | Bounded effect/audio counts, threat priority under combined casts and accessible alternatives |
| Live combat presentation bridge | FG04-T03/T04 and FG06-T05 | Actual native clients consume accepted event IDs once, handle rejection/reconnect and finish a full match |
| Complete roster interactions | FG10-T09 | Pairwise/stacking/interrupt/counter behavior and twelve-hero fight readability on a frozen content revision |
| Final platform presentation | FG11-T05 and FG14 | Actual target-hardware traces, integrated art approval, supported-platform execution and complete player journey |

Repeat the same four rounds for each new study: source/contract, authored motion/effects, independent challenge, actual runtime verification. Keep failed footage and exact revisions so a later attractive frame cannot silently replace an unresolved transition defect.
