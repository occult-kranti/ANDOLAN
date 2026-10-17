# Final action capture — independent art review

**The inspected samples support readable action direction, receiver feedback and
effect cleanup in this controlled offline setting. Overall production art and
continuous animation quality remain LIMITED.** This is an AI review of original
game pixels, not a human play study or a Deadlock/Overwatch/Dota 2 parity claim.

## Exact evidence inspected

All 25 original stills in `../capture-action-r1/` were individually opened:
windup/release/contact for five abilities, six separate low-angle replay stills,
the reduced-Guardian still, and hero hit/defeated/respawned stills. These are
actual engine captures, not generated concept images.

Thirty-one original sequence frames were also individually opened. Their
unaltered PNGs are retained in `film-samples/`, with exact hashes and ticks in
`FILM_REVIEW_inputs.json`:

`4, 5, 6, 7, 8, 9, 44, 63, 64, 65, 98, 100, 101, 102, 119, 135, 136, 137,
269, 270, 271, 279, 280, 281, 286, 287, 315, 316, 317, 361, 362`.

The adjacent release groups cover all five actions. Frames 7–9 cover Kodanda's
actual unit contact; 269–271 cover Guardian's tactical expiry; 279–281 cover its
later lifecycle end. The final frame of each take was inspected. The event map
is the completed capture's `contact-review-index.json`, not a guess from still
filenames.

I independently verified all 388 original PNG hashes against the completed
report: 363 sequence frames and 25 stills. Hash verification does not mean all
388 images were visually reviewed. Each take advances two actual 60-Hz physics
ticks per captured frame. Report source hashes are unchanged. The film is a
silent 12.1-second, 30-Hz concatenation of five separate takes with reset cuts;
staged live receivers receive real runtime casts. It is not one uninterrupted
fight, human OS-input testing, an audio audition or a physical-GPU benchmark.

- Capture report: `cbb4c0cb262cd8078d93c1387ff64daef5ec99deb3fba6e72dd2713557bb98d6`.
- Film: `888fbf15453c1a18ba12f93134183404bb362e9c8d733bcb70f915bcba849b5c`.

## Visible action and UI findings

| Action/state | Visible observation | Bounded result |
| --- | --- | --- |
| Kodanda | Small gold projectile shape appears across release frames 4–6. A target-centered gold contact ring appears in 7–9 while the receiver health bar changes. The final frame is clear of the ornament. | Readable basic-shot direction and one real hit in this quiet arrangement. The report confirms one damage receipt, 150 to 122 health. |
| Piercing Dawn | Long gold directional strokes and crescents distinguish windup; release frames 63–65 remove the long guide and send the projectile forward. Contact stills show target-centered feedback, with the HUD readable. | Direction and phase distinction are clear in the sampled views. The report records three unit receipts of 70 damage each; the still samples do not independently resolve every contact in time. |
| Measured Step | Blue trails and a visible camera/world shift show advance. Frames 100–102 change from a staggered-leg pose to a near-level stance as movement begins; later contact/end samples show the new position and cleared effect. | Movement and cleanup are visible. That rapid pose change still needs a dedicated stride/acceleration-blend review; these few frames do not establish natural motion or contact throughout the dash. The event is `movement_accepted`, not a damaged-receiver hit. |
| Guardian Circle | The dark-backed gold rim remains locatable on pale ground. Cyan decoration leaves units and HUD visible. The reduced-effects still preserves the tactical rim. Release frames 135–137 add the visible +55 shield state. | Area readability is improved in this setting. Frames 269/270 retain the rim and active/shield HUD while decoration has almost faded; frame 271 clears the rim, shield and active notice together. Health ends at 285/300 after starting at 240/300. |
| Dawn Volley | The wider fan of gold guides and looping gold/violet strokes distinguishes the action from the linear shot. Release frames 315–317 show the projectile transition, and the contact still shows target feedback. Final frames 361/362 are clear of the ornament. | Readable fan direction and cleanup in the sampled scene. The report records three unit receipts; the selected contact still is not a frame-by-frame review of all three hits. |
| Hero lifecycle | The hit still shows 150/300 health; defeated shows 0/300 and a return countdown; respawn shows the arrival court and 300/300. | The displayed states are coherent. Three stills cannot accept the entire hit, fall and recovery animation. |

Guardian's 182 reported receipts include its repeated real guardian ticks; they
are not 182 distinct characters or 182 damage hits. The source records one
normal release and normal expiry for each take. These facts support the visible
samples without converting event counts into artistic quality claims.

## Remaining visible limits

The live soldiers have simple block/cylinder forms, repeated neutral silhouettes
and sparse surface detail. They remain a conspicuous quality gap next to the
more developed Rama costume. The large paving fields, repeated building facades
and sparse distant blocks also remain evident in the actual play camera.

Rama retains useful indigo/gold/ivory identity and distinct bow/crown shapes,
but face, groom, fabric finish and secondary motion are unfinished. The samples
do not establish smooth rapid reversals, sustained locomotion, animation under
interruptions, slope/step contact, moving shadow-cascade behavior or crowded
combat. The three-frame dash release deserves further motion review as noted
above. No full temporal playback or human feel acceptance is claimed here.

## Ordinary final-source anchors

All three originals in `../capture-final-anchors-r4/` were separately opened:
title day, near-hero day and near-hero night. `FINAL_ANCHORS_inputs.json` verifies
their hashes and independently checks equality of all 266 source pins shared
with the film. They use the same frozen runtime without diagnostic overrides;
the capture harnesses, clocks, scenes and framing differ.

The ordinary title remains legible, terrace supports remain visually grounded,
and costume/material identity survives the promoted shadow settings. No new
gross foot-shadow detachment or broad facial-patch regression is apparent in
these three views. Fine scalp/chest stippling and the previously documented
face/groom/world-art gaps remain open. This preserves the bounded lighting
acceptance; it does not promote the character or district as finished art.

Anchor report:
`66d47708f7bdde947f4339c981c3b9615193dea7090b41bb912bf0ea1d530f18`.

No runtime, asset, camera or roadmap changes were made by this reviewer.
