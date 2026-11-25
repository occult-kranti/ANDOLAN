# Hanuman and Rama · layered action pass

Times below use the current Rust Confluence authority at 20 Hz. Tick zero is the accepted cast. The 60 fps equivalents help animators place keys. The layer and experiment sections are design work, so actual engine support must be checked in a release capture. Values come from the checked-in profiles and code. [Timing index](baseline.json) · [Hanuman kit](../../../assets/design/hanuman-ability-kit.json) · [Rama kit](../../../assets/design/rama-ability-kit.json)

## Hanuman

For the Mountain Pulse silhouette, a Rajasthan miniature shows Hanuman carrying a mountain in one hand with a large curling tail. It is a reference for the carried mass and profile. The game’s timing and shield effects are YUGA designs. The new illustrated Hanuman board explores the launch, impact and recovery as a visual concept. [Metropolitan Museum of Art, Hanuman bearing a medicinal mountain, c. 1800](https://www.metmuseum.org/art/collection/search/37960) · [Generated action board](../../../art/ability-keyframes-2026/hanuman.png)

### Vajra Gada · primary

- **Live rule**. Release and sector damage occur at tick 5, corresponding to frame 15 in a 60 fps review. Unlock is tick 11. A target in the 3.5 m frontal sector receives 34 damage if visible. Cooldown is 12 ticks.
- **Body and anticipation**. Turn the planted shoulder before the right hand accelerates. Hold the left palm low and preserve the gada grip. A short open fan follows the attack direction and terminates at the true boundary.
- **Result and recovery**. Use one concise metallic contact on each actual enemy receipt. The mace slows after the contact before returning to guard. It does not spawn a second strike on the return path.
- **Optional testable depth**. Trial a narrow tip accent whose damage stays identical to the inner sector. If players interpret the tip as bonus damage, remove the accent or formally define the rule and its tradeoff.
- **Counters and checks**. Compare an enemy ahead, one behind, one just outside the range and one behind cover. Every cast can damage each qualifying receiver once.

### Vajra Kavacha · Q

- **Live rule**. At tick 7, grant up to 48 shield for three seconds to the caster and eligible visible allies in the 5.5 m forward fan. Unlock at tick 12 and cooldown at 180 ticks.
- **Body and anticipation**. Left forearm opens toward the fan and the body settles behind the palm. A segmented half-ring makes the forward direction distinct from a full-circle ultimate.
- **Result and recovery**. On receipt, place a thin, stable bracket around each protected ally. Shield absorption and expiry each have a compact secondary cue. Finish the hand gesture after the grant without ending the real shield.
- **Optional testable depth**. Test an ally-protection assist that records shield absorption without increasing damage. Display it only when damage was actually absorbed, and evaluate team value before adding a reward.
- **Counters and checks**. An ally behind cover or outside the fan receives no shield. A stronger pre-existing shield must retain the authority's maximum rule. Test expiry, repeat casts and a shielded ally leaving the area.

### Maruti Udayana · E

- **Live rule**. Release is tick 4, nominal end of travel is tick 13 and nominal unlock is tick 17. Travel is up to 8.5 m, clipped by solids, and deals no damage. Cooldown is 140 ticks.
- **Body and anticipation**. Compress at the rear leg, pull the gada beside the flank, then raise the leading knee. A short, open wind lane ends at the accepted endpoint. The tail follows the pelvis and never moves the capsule.
- **Result and recovery**. The current `impact` event is emitted at takeoff for this movement ability. Use the authoritative `landed_age` or grounded state for one landing dust cue, including a shortened vault. On interrupt, clear the visual arc and return the character to ground.
- **Height and collision**. Hanuman's area checks now use inclusive vertical overlap between the authored height band and each receiver's body, with actor feet elevation and position sampled from the same pre-tick state. Grounded soldiers and older receiver callers default to zero elevation. A vault whose feet rise above a ground attack's band can clear that Hanuman attack. Rama's projectile and ward checks still use their previous ground-plane target policy. [Hanuman payload](../../../../yuga-rust/src/combat.rs) · [Battle height snapshot](../../../../yuga-rust/src/battle.rs) · [Native/Wasm six-seat check](../../research/physics-panel-2026/airborne-parity.json)
- **Arc tradeoff**. The authority derives peak height from travel distance and caps it at 1.55 m. A clear 8.5 m vault can rise above the gada's 1.4 m band near its apex. A shorter vault may stay within that band. The landing position and live pre-tick height decide the result, so this is not a general invulnerability window.
- **Optional testable depth**. Add an optional direction indicator while preparing the action, using the same endpoint validation. Keep it private until the action is accepted so it cannot reveal a target the server rejects.
- **Counters and checks**. Test open travel, wall-shortened travel, blocked takeoff and interruption at the airborne apex. Knockout and 60-tick respawn must clear the old vault height, and the first subsequent cast must be accepted when otherwise eligible.

### Lanka Dahan · C

- **Live rule**. At tick 9, a 5 m rear sector applies 28 burst damage. It continues applying 8 damage per second through tick 49. The body unlocks at tick 17, and cooldown is 220 ticks.
- **Body and anticipation**. The hips turn against planted feet as the four tail links coil. A broken rear fan makes the danger direction visible even without the ember particles.
- **Result and recovery**. At tick 9 send one tail arc across the marked rear sector. The ember boundary remains at the cast's original origin through tick 49 while the body can face, move or begin a different action. Tick receipts drive damage reaction.
- **Optional testable depth**. Trial a subtle ground notch at the original facing axis, helping both sides understand that turning after impact does not rotate the field.
- **Counters and checks**. Cross the sector edge after impact, exit and re-enter, stand ahead, and block line of sight. Ensure a second cast's body pose cannot reanchor the earlier field.

### Mountain Pulse · X

- **Live rule**. Accepted ground targets must be within 14 m and visible. Release at tick 14 and impact at tick 23. The 7 m radius impact deals 65 damage to enemies or heals qualifying allies by up to 45. Unlock is tick 33 and cooldown is 600 ticks.
- **Body and anticipation**. Both heels plant, then the gada rises as a fixed target perimeter begins its countdown. The preview indicates a clear center or an unavailable crossed center using both shape and label.
- **Result and recovery**. The launch streak moves from the caster to the fixed target. On tick 23 a low ring expands through the disk while individual hit and heal receipts mark actual targets. The actor remains at the caster location and the tail follows through after impact.
- **Optional testable depth**. A clearly marked final-quarter countdown can give opponents a consistent visual exit cue. It conveys existing time and adds no extra damage or target-lock rule.
- **Counters and checks**. Reject blocked, airborne and out-of-range placement without spending the cast. Compare an ally and enemy on opposite sides of the boundary, a recipient behind cover, movement out of the mark before impact and interruption just before release.

## Rama

A Jammu painting shows Rama and Lakshmana seated on a hill with their bows at rest. Use it for quiet readiness and the relationship between figure, weapon and terrain. The work does not document a firing action. The new illustrated action board explores the bow silhouette, while the authority table below controls each arrow's release timing. [Metropolitan Museum of Art, Rama and Lakshmana on Mount Pavarasana, c. 1690–1710](https://www.metmuseum.org/art/collection/search/53684) · [Generated action board](../../../art/ability-keyframes-2026/rama.png)

### Kodanda · primary

- **Live rule**. Release at tick 4, unlock at tick 8 and cooldown at tick 8. An arrow travels at 60 m/s, up to 40 m, dealing 28 damage to the first eligible target. A 12-arrow magazine uses a 32-tick reload.
- **Body and anticipation**. The drawing hand reaches the string while the bow remains in the right hand. Lower-body movement can continue during this primary draw.
- **Result and recovery**. Release one shaft from the sampled muzzle and give one victim or wall contact from the authoritative impact. Restore the ready hand without snapping the string through the forearm.
- **Optional testable depth**. Add a distinct empty-magazine cue and a visible reload progress segment. Neither cue changes ammo availability.
- **Counters and checks**. Move during draw, release near cover, hit two aligned receivers and verify only the first is damaged. Test reload after exhausting the magazine and interrupted primary draw.

### Piercing Dawn · Q

- **Live rule**. Release tick 13, unlock tick 19, cooldown 120 ticks. The arrow travels at 52 m/s for up to 38 m and can apply 70 damage to as many as six distinct eligible enemies. Solid cover stops it.
- **Body and anticipation**. Open the drawing elbow beyond the primary silhouette with a thinner, longer horizontal sightline. Keep the defender's body visible through the line.
- **Result and recovery**. One advancing shaft drives a contact accent for each distinct actual receipt. Dim the trail at the first wall. Recovery lowers the bow without reversing the projectile.
- **Optional testable depth**. Trial spacing a single segmented line by projected depth to help opposing players judge the path. Avoid fake marks on actors the authority has not hit.
- **Counters and checks**. Place six enemies in line, a seventh beyond them and a wall between two targets. Reverse target input ordering and ensure deterministic nearest-first contact.

### Measured Step · E

- **Live rule**. Release tick 2, nominal movement end and body unlock tick 7. The ground step reaches up to 4.5 m over 0.22 s, shortened by cover, with no invulnerability. Cooldown is 100 ticks.
- **Body and anticipation**. Keep the bow in the aim plane while the lead foot takes the movement direction. Use a short open footprint at the selected endpoint.
- **Result and recovery**. The first planted foot, not an arrival guess from a client timer, closes the wind trace. No dodge immunity or contact damage is implied by the visual.
- **Optional testable depth**. Test a small duration-independent status cue that says the step is positional only. Keep the cue accessible with sound muted.
- **Counters and checks**. Step forward, backward and sideways near a wall. Confirm traveled distance and facing, then issue a shot at the first legal unlock tick.

### Guardian Circle · C

- **Live rule**. Release at tick 11 and unlock at tick 17. A fixed 5 m radius circle lasts through tick 101. Within it, eligible allies can receive up to 55 temporary shield and 10 healing per second. The target must be visible and within 16 m. Cooldown is 220 ticks.
- **Body and anticipation**. The off hand draws the circle while the bow remains vertical. A broken ring stays centered on the accepted ground target.
- **Result and recovery**. Use receipt-driven shield brackets and small intermittent recovery pulses. The persistent ring outlives the caster's gesture. Visually communicate its exact ending without consuming pre-existing stronger shields.
- **Optional testable depth**. Add a threshold marker that changes texture as expiry approaches. Investigate ally confusion before considering any additional resource effect.
- **Counters and checks**. Move an ally into and out of the field, put cover between recipient and center, compare stronger and weaker prior shields and verify expiration and restoration.

### Dawn Volley · X

- **Live rule**. Release begins at tick 19. Three individual arrows are emitted at ticks 19, 21 and 23 along offsets of −0.105, 0 and +0.105 radians. Each deals 82 damage to its first eligible enemy, up to 30 m at 34 m/s. Unlock is tick 30 and cooldown is 360 ticks.
- **Body and anticipation**. Lock the three narrow firing lines during the long draw. Preserve enough empty space between them for an opponent to identify a safe gap.
- **Result and recovery**. Each real arrow has a distinct nock/release beat and its own authoritative target or wall impact. A missed arrow does not create a target flash. Return to the normal handhold after the last shot.
- **Optional testable depth**. Test a patterned line treatment that indicates left-to-right stagger while remaining understandable without color and in reduced motion.
- **Counters and checks**. Walk between lines during windup, block one lane, place different targets along the three rays, and interrupt before tick 19. Replay delayed and duplicate receipts and ensure each arrow produces at most one terminal impact.

## Acceptance

At minimum, capture a normal and blocked case per ability from the actual match camera with the active HUD. Compare body markers to the authoritative tick and sample the frames around release, collision and first recovery. Repeat Mountain Pulse and Guardian Circle with opposing team views. Record player-facing readability with particles and sound reduced. [Automated Confluence release checks](../../../../yuga-rust/tools/test_hanuman_release.mjs) · [Actual input captures](../../../art/hanuman-hero-finish/media/playable-casts/)
