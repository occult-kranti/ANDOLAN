# Shiva and Krishna · proposed layered kits

Shiva and Krishna have preview GLBs and motion references. Their proposed abilities are not registered in the current Confluence authority. The values and interactions below are first-playtest targets drawn from the existing YUGA character scripts. They require explicit server rules, hit tests and two-client review before they can be called playable. [Shiva source script](../../../art/four-hero-motion/scripts/shiva.md) · [Krishna source script](../../../art/four-hero-motion/scripts/krishna.md)

The base scripts use 30 fps. Their F0 marks accepted input. At 20 Hz, a 0.8 s windup equals 16 ticks and a 1 s windup equals 20 ticks. Unlike the live Confluence table, the following examples are proposals rather than measured runtime events.

## Shiva

Shiva is an area-control fighter with a stable trident line. An asymmetric lifted knee and planted supporting foot offer clear anticipation and a predictable impact direction. The Chola Nataraja visual reference informs silhouette and gesture. The bronze does not establish a game animation's timing or a unique historical interpretation. The generated action board is a visual concept for anticipation and impact. [Metropolitan Museum of Art, Shiva as Lord of Dance, late 12th–early 13th century](https://www.metmuseum.org/art/collection/search/39329) · [Cleveland Museum of Art, Nataraja](https://www.clevelandart.org/art/1930.331) · [Generated action board](../../../art/ability-keyframes-2026/shiva.png)

### Crescent Spark · primary

- **Proposed rule**. Launch one 24-damage projectile at 40 m/s, with a 0.60 s repeat interval. Solid cover stops the shot.
- **Layered design**. Keep the trident center tine aimed ahead in the ready pose. A narrow white-blue line follows the actual projectile. A short directional contact mark belongs at the authority's collision point. The tied drum moves slightly after the weapon decelerates.
- **Further experiment**. Compare a tapered line with a small arrowhead for readability at long range. A visible charge should never imply a damage increase unless an explicit charge rule is adopted.
- **Counter and test**. Move behind a wall and run across the projectile's path. Check that the target or wall receives one contact and that auto-fire repeats without a discontinuous shoulder flip.

### Threefold Sweep · Q

- **Proposed rule**. Apply one frontal cone check for 50 damage within 8 m. Use the existing classic cone's cosine threshold of 0.55 as an initial reference. Proposed cooldown is 10 s.
- **Layered design**. The right shoulder rotates, then three fine tine trails cross the same fan. Use one unbroken fan boundary and one hit receipt per receiver. Stop the trails together as the shaft returns.
- **Further experiment**. Trial a small delay before the swing in human playtests if immediate area damage proves unreadable. Adding such a delay requires an explicit simulation timing change and updated defense windows.
- **Counter and test**. Flank the caster or use cover. Check the cone edge, all three visible prongs against the single damage receipt, and a second accepted cast after cooldown.

### Stillwater Coil · E

- **Proposed rule**. Place a 4 m radius slow field on visible ground within 18 m. Lifetime is 3 s, proposed total power is 27 and cooldown is 14 s.
- **Layered design**. The left hand opens toward the accepted target. A cool broken ring with a fixed notch at the original facing marks the full field. Repeated small inward strokes show active duration while enemies remain visible through its interior.
- **Further experiment**. Evaluate an edge-entry pulse that highlights crossing without changing slow magnitude. Instrument how often opponents identify the exit before changing the power or radius.
- **Counter and test**. Walk out of the field, enter after it starts, place it near cover and verify field expiry independently of the actor's recovery. Lost snapshots must not duplicate the field.

### Tandava Downbeat · R

- **Proposed rule**. A stationary 0.80 s windup ends in one 90-damage radial release within 6 m and line of sight. Proposed cooldown is 50 s.
- **Layered design**. Mark the full circle on accepted input. At frame 24 of the 30 fps action, the raised left sole plants and one server release resolves. A brief outward ripple follows the foot contact, then the damaru and cloth settle separately.
- **Further experiment**. Try a fractured outer ring with a quieter inner band so the limit remains visible on pale stone and water. Do not present separate bands as separate damage zones.
- **Counter and test**. Leave the radius or take cover before release. Interrupt at tick 15 and compare release at tick 16. A second receipt, a reconnected client or the return footstep must never cause a second blast.

## Krishna

Krishna is a mobile support proposal. The left-hand flute, right-hand disc and peacock feather provide three different silhouettes for support, attack and recognition. His protection ultimate follows a gesture associated with the Govardhan story. The match-specific shield and numbers are original design proposals. The generated action board explores that gesture as an illustrated concept. [Metropolitan Museum of Art, Krishna Holds up Mount Govardhan, c. 1590–95](https://www.metmuseum.org/art/collection/search/448183) · [Cleveland Museum of Art, Krishna summoning the cows](https://www.clevelandart.org/art/1989.339) · [Generated action board](../../../art/ability-keyframes-2026/krishna.png)

### Chakra Flick · primary

- **Proposed rule**. Fire one 21-damage disc at 42 m/s, with a 0.50 s repeat interval. Cover stops the projectile.
- **Layered design**. The right wrist opens and one gold disc travels on the accepted sightline. After separation the held rim reforms gradually beside the palm, without indicating a returning damaging projectile. The left hand keeps the flute clear.
- **Further experiment**. Compare an interrupted rim with a solid circular disc in team fights. Retain a small open gap between disc and hand at the behind-the-back camera.
- **Counter and test**. Step off the path, put cover in front of the muzzle and fire while moving. Test that the reforming held disc adds no return-path hit.

### Turning Star · Q

- **Proposed rule**. Fire a larger straight projectile for 44 damage at 62 m/s, reaching at most 24 m, with a 9 s cooldown. It ends on the first eligible contact or obstruction.
- **Layered design**. Broaden the right-arm release and give the edge a broken, directional rim. A straight trail indicates the real path, while a single collision accent occurs at the actual endpoint.
- **Further experiment**. Explore a spiral texture moving along the same straight axis. Ask testers whether they mistakenly expect a curved or returning projectile.
- **Counter and test**. Sidestep and block with cover. Give two targets along the line and assert exactly one receives the impact.

### Reed Refrain · E

- **Proposed rule**. Instantly heal living visible allies and self within 5 m for up to 42 health, with a 12 s cooldown. It cannot revive a defeated ally.
- **Layered design**. At accepted input give a restrained breath cue. The left wrist carries the flute toward the mouth and the right fingers alternate after contact. Recipient arcs appear only on actual healing receipts. The existing preview's lower lip measures 1.48 mm from the mouthpiece during 14 sampled contact poses.
- **Further experiment**. Offer a brief optional musical phrase after the immediate grant. Let the pose finish visually without postponing, repeating or extending the server heal.
- **Counter and test**. Place allies at the radius edge and behind a wall, include a full-health and defeated ally, and interrupt the follow-through. Match the receipt to the visible arc and test with sound off. [Flute-contact measurements](../../../art/four-hero-motion/evidence/rig-motion.json)

### Govardhan Canopy · R

- **Proposed rule**. A stationary 1.00 s windup ends in one grant of up to 70 shield for 3 s to each living visible ally within 6 m, including Krishna. The proposed cooldown is 48 s. A recipient carries that shield until depletion or expiry.
- **Layered design**. On accepted input, mark the radius with a broken ground ring. The flute moves into a left-hip socket before the left arm rises. At frame 30, the finger reaches its apex and the server applies the eligible grants. A translucent overhead shelter and recipient brackets explain protection without blocking the camera.
- **Further experiment**. Test a sparse rain-edge effect that stops at the shelter perimeter. It is a visual cue with no projectile collision.
- **Counter and test**. Enter before release, exit at the boundary and stand behind cover. Interrupt one tick before the grant, duplicate a received event and reconnect at mid-windup. Verify a single flute owner and a single grant per ally.

## Registration and review

Add a distinct hero identifier, authored ability data, a specific timed release branch and validation before making either proposal selectable. An unknown hero falling back to Rama is a failed registration. Capture the live authority's accept, cancel, release and result receipts in at least a two-client session. Test exact phase boundaries, target team, line of sight, cooldown, knockout, reconnect and duplicate input. Then review the skinned result from the match camera with the world landmark and lane colors behind it. [Current dispatch](../../../../yuga/shared/simulation.ts) · [Hero loader](../../../../yuga/client/hero-models.ts)
