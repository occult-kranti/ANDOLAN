# Classic Rust sparring · all 14 heroes

The classic Rust sparring roster has one primary and Q/E/R for each of 14 heroes. This is a separate product from Rust Confluence, whose Hanuman and Rama have five-action kits. The rows below state the current classic mechanics and propose animation or effect layers for production review. They do not grant new effects. [Classic launch and verification](../../rust-rebuild/deep-search/CLASSIC-DISTRIBUTION.md) · [Confluence design](HANUMAN_RAMA.md)

Every classic primary uses an authority projectile, including staff, mace and spear heroes. Speed, damage and authored repeat interval below come from the hero profile. Melee-looking weapon animation must still reveal a traveling shot. A projectile stops at its first enemy or solid contact. The simulation advances at 20 Hz. [Primary fire](../../../../yuga-rust/src/bin/roster/lab.rs) · [Roster profile](../../../../yuga-rust/assets/classic-roster.json)

Immediate front fans, circle damage and support checks require line of sight. A slow field follows an accepted ground point and refreshes a 0.5 s slow status while an enemy remains inside. Its listed per-second rate is the authored power divided by its lifetime and must be validated at tick boundaries. Dashes and ordinary leaps move against world collision and do not use the profile’s generic power as contact damage. Summons can produce fewer than two units when placement or actor limits prevent a spawn. [Classic cast dispatcher](../../../../yuga-rust/src/bin/roster/abilities.rs) · [Zone ticks](../../../../yuga-rust/src/bin/roster/lab.rs)

Color never carries team or danger information alone. Every directional fan, circle, accepted impact and ally receipt also needs a shape, icon or label that works with reduced motion and muted audio. The listed counterplay is a review intent to test, not a claim from a human study. [Accessibility guidance](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-fixed-colour-alone/)

The source snapshot SHA-256 values are roster `77dd71bd7d4657305dfac3b13ff7f394cdd1c2f8c836e974ccd69d490cc42d60`, cast dispatcher `32982e8b6a9348a4760147eecc031e5ed4ddfc9631b4252713c4350a42cba247`, and match simulation `0d9d8109f2188b62308d057e5ce0d91e18047f8cc2d2830c813399ecbdf4d580`. Regenerate this file after any source change using `python3 games/yuga-native/docs/design/combat-panel-2026/classic_roster.py`, then run the same command with `--check`.

## Rama · Striker

The current silhouette is tall curved bow, swept sash, narrow crest.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Bow | 27 damage; 46 m/s; authored 0.48 s repeat | Draw the compact bow silhouette and keep the string hand visible. | Move during repeat fire and verify a wall ends the projectile. |
| Q · Steady Arrow | 54 damage; 26 m range; 38 m/s projectile; 9 s cooldown | Lengthen the bow arm and draw a narrow, steady sightline. | Sidestep or hide behind cover and verify one bolt contact. |
| E · Measured Step | up to 10 m movement, blocked by solids; 12 s cooldown | Shift the feet under the bow without turning the held aim into a hitbox. | Step into a wall and verify the shortened endpoint. |
| R · Dawn Volley | 1 s windup; three simultaneous 32-damage arrows; 28 m range; 44 s cooldown | Show three separate sightlines during the draw and release together. | Block one path and check three simultaneous, independently colliding arrows. |

## Ravana · Vanguard

The current silhouette is ten-faceted crown, broad mantle, ring blade.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Chakram | 26 damage; 34 m/s; authored 0.52 s repeat | Keep the ring blade outside the crown silhouette before the ranged release. | Verify the visible disc is a projectile and stops at cover. |
| Q · Tenfold Guard | 48 shield; 4 m ally radius; 4 s ward; 11 s cooldown | Close the broad mantle into a protective silhouette and place brackets on eligible allies. | Place an ally outside the radius and another behind cover. |
| E · Commanding Circle | 35 damage in a 5 m aimed circle; up to 6 m pull; 20 m placement range; 16 s cooldown | Turn an open right palm toward a marked center, then draw a segmented inward pull. | Check the pull moves at most six metres and a wall limits it. |
| R · Crownfire | 90 damage; 7 m caster-centered radius; 48 s cooldown | Raise the crown and open a broken full-circle boundary around the caster. | Leave the radius or hide behind solid cover before resolution. |

## Arjuna · Striker

The current silhouette is long bow, split shoulder scarf, high quiver.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Bow | 20 damage; 48 m/s; authored 0.35 s repeat | Track the aim line along the long bow while keeping the high quiver visible. | Move across the firing line and verify a single projectile hit. |
| Q · Converging Volley | 38 damage; 18 m front fan; 8 s cooldown | Expand the drawn bow into an open forward fan with a distinct edge. | Test one target just inside and outside the fan angle. |
| E · New Angle | up to 12 m movement, blocked by solids; 11 s cooldown | Let the split scarf lag the footfall as the archer repositions. | Dash against cover and check the actual endpoint. |
| R · One Clear Line | 88 damage; 28 m range; 62 m/s projectile; 42 s cooldown | Narrow the shoulders and use one straight elongated trail. | Step sideways and verify one fast shot stops at cover. |

## Duryodhana · Vanguard

The current silhouette is square shoulder guards, low crown, heavy mace.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Mace | 29 damage; 26 m/s; authored 0.55 s repeat | Show the heavy mace at the side while the ranged primary leaves along aim. | Confirm the apparent mace scale does not suggest a melee-only hit. |
| Q · Mace Shock | 48 damage; 10 m front fan; 10 s cooldown | Sink the shoulders into a short front-facing impact fan. | Test a target beyond the range and one behind the caster. |
| E · Hold the Ground | 55 shield; 4 m ally radius; 4 s ward; 15 s cooldown | Plant the stance and give protected allies a firm square ward edge. | Move an ally beyond the circle or behind cover before the grant. |
| R · Iron Crescent | 92 damage; 12 m front fan; 46 s cooldown | Sweep the heavy mace into a broad wedge with visible side limits. | Check one receiver on either side of the cone threshold. |

## Hanuman · Keeper

The current silhouette is curved tail, flowing scarf, rounded mace.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Mace | 23 damage; 29 m/s; authored 0.46 s repeat | Keep the rounded mace and tail clear as the classic ranged shot leaves. | Confirm this sparring primary uses a projectile. |
| Q · Windward Leap | up to 14 m movement, blocked by solids; 9 s cooldown | Compress the rear leg, then extend the tail to counterbalance travel. | Compare a clear leap and a wall-shortened endpoint. |
| E · Bring Them Home | 48 healing; 5 m ally radius; 14 s cooldown | Offer the open hand and connect an arc only to healed recipients. | Test a damaged ally, a full-health ally and an ally behind cover. |
| R · Mountain Pulse | 0.7 s windup and 0.45 s travel; up to 14 m; 7 m landing radius; 65 enemy damage and 45 allied healing; 45 s cooldown | Lift the mountain through the 0.7 s brace, then travel with a clear landing disk. | Move out of the landing radius or stop travel against cover. |

## Karna · Striker

The current silhouette is radiant shoulder discs, crescent bow, long sash.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Bow | 30 damage; 43 m/s; authored 0.55 s repeat | Angle the crescent bow so the radiant shoulder discs frame the release. | Use cover and verify a single shot terminates at the wall. |
| Q · Sunshaft | 62 damage; 27 m range; 62 m/s projectile; 11 s cooldown | Pin a bright, narrow line between bow and accepted target. | Move across the line before the projectile reaches the target. |
| E · Borrowed Dawn | 42 shield; 4 m ally radius; 3 s ward; 16 s cooldown | Turn the shoulder discs outward and give allies a distinct ward outline. | Compare shielded allies inside and outside the 4 m circle. |
| R · Solar Reprisal | 95 damage; 6 m caster-centered radius; 50 s cooldown | Collect the shoulder light inward before a single circular flash. | Leave the six-metre radius and verify blocking cover. |

## Bhima · Vanguard

The current silhouette is broad torso, crossed straps, long-headed mace.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Mace | 28 damage; 27 m/s; authored 0.55 s repeat | Keep the long mace readable while a separate ranged primary travels forward. | Verify a distant opponent can be hit only by the projectile. |
| Q · Heavy Sweep | 52 damage; 10 m front fan; 10 s cooldown | Rotate the broad torso into a single close fan. | Check front, side and behind positions against the cone. |
| E · Closing Stride | up to 12 m movement, blocked by solids; 15 s cooldown | Bend into the leap and hold the mace near the torso during travel. | Clip travel against a wall and locate the actual endpoint. |
| R · Thunder at Your Feet | 92 damage; 8 m caster-centered radius; 48 s cooldown | Plant both feet and send one low ring outward. | Move past the eight-metre radius and confirm one damage event. |

## Meghnad · Striker

The current silhouette is forked crest, compact bow, layered cloud scarf.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Bow | 22 damage; 42 m/s; authored 0.4 s repeat | Keep the forked crest and compact bow clear of the cloud scarf. | Verify moving fire and the projectile boundary at cover. |
| Q · Cloud Snare | 22 m placement range; 4 m radius for 3 s; nominal 9.33333 damage/s while inside; 12 s cooldown | Mark a fixed cloud field with a broken outer edge and a fading center. | Enter, exit and re-enter; check ticking damage and the remaining slow. |
| E · Storm Step | up to 13 m movement, blocked by solids; 12 s cooldown | Tilt the scarf opposite the step while the movement path remains clear. | Stop at a wall and keep aim readable. |
| R · Gathered Squall | 78 damage; 22 m front fan; 43 s cooldown | Unfold the compact bow into a long fan with spaced edge marks. | Test a target across the fan edge and behind cover. |

## Sita · Keeper

The current silhouette is leaf-tipped staff, long mantle, seed-shaped crest.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Staff | 19 damage; 32 m/s; authored 0.45 s repeat | Lead with the leaf-tipped staff and keep its shot distinct from healing. | Confirm the ranged shot terminates on cover. |
| Q · Grove Renewal | 50 healing; 5 m ally radius; 10 s cooldown | Open the staff hand and use brief leaf-shaped marks on healed allies. | Test full-health allies, range boundaries and blocked sight. |
| E · Rooted Path | 18 m placement range; 5 m radius for 4 s; nominal 6.25 damage/s while inside; 15 s cooldown | Trace a fixed rooted perimeter with gaps that keep moving enemies visible. | Leave the zone and check its slow expiry separately from the animation. |
| R · Shelter of Mithila | 0.8 s windup; 8 m radius; 70 initial ward and 9 healing/s in the field for 6 s; 46 s cooldown | Gather the mantle during the brace, then raise a stable sanctuary perimeter. | Interrupt before release and test the one-time ward plus ongoing field heal. |

## Draupadi · Keeper

The current silhouette is five-point mantle clasp, flame staff, upright crown.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Staff | 20 damage; 33 m/s; authored 0.48 s repeat | Keep the flame staff separate from the five-point mantle clasp. | Confirm the basic projectile has one contact at a wall or enemy. |
| Q · Circle of Resolve | 46 shield; 5 m ally radius; 4 s ward; 10 s cooldown | Gather the mantle at the chest before opening ally ward brackets. | Check allied recipients within radius and behind solid cover. |
| E · Stand Accountable | 30 damage in a 5 m aimed circle; up to 6 m pull; 19 m placement range; 17 s cooldown | Point the staff at a marked center and show a measured inward pull. | Use a wall to limit displacement and check pull distance. |
| R · Unbroken Assembly | 95 healing; 8 m ally radius; 48 s cooldown | Lift both forearms and show one broad, open healing ring. | Leave the radius or block sight and verify no heal receipt. |

## Subhadra · Keeper

The current silhouette is spear pennant, rounded shoulder guards, side braid.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Spear | 22 damage; 38 m/s; authored 0.45 s repeat | Keep the spear pennant trailing behind the forward ranged projectile. | Verify the basic shot stops at the first contact. |
| Q · Signal Lance | 44 damage; 24 m range; 38 m/s projectile; 9 s cooldown | Extend the spear and release one narrow lance along the aim. | Hide behind cover and verify a single bolt impact. |
| E · Rally Close | 42 healing; 4 m ally radius; 13 s cooldown | Lower the spear and show short arcs only on healed allies. | Test the four-metre boundary, including a full-health ally. |
| R · Twin Standards | up to two allied sentinels with 105 HP and 28 attack; 9 s lifetime; 48 s cooldown | Plant two standards, then resolve each sentinel at its actual spawn point. | Block one spawn and test actor limits, expiry and ownership. |

## Hidimbi · Vanguard

The current silhouette is broad leaf mantle, braided crest, forked spear.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Spear | 24 damage; 31 m/s; authored 0.5 s repeat | Hold the forked spear outside the broad leaf mantle while firing. | Verify the primary projectile is distinct from a melee sweep. |
| Q · Forest Boundary | 16 m placement range; 5 m radius for 4 s; nominal 6.75 damage/s while inside; 12 s cooldown | Use leaf-shaped notches along a fixed field boundary. | Cross the five-metre edge and check slow persistence. |
| E · Canopy Guard | 50 shield; 5 m ally radius; 4 s ward; 16 s cooldown | Close the mantle into a protective arc and bracket real shield recipients. | Place one ally behind cover and one beyond the radius. |
| R · Grove Watch | up to two allied sentinels with 105 HP and 32 attack; 9 s lifetime; 52 s cooldown | Open two clear spaces under the canopy for the actual sentinel spawns. | Check blocked spawns, ally ownership and nine-second expiry. |

## Chitrangada · Vanguard

The current silhouette is short segmented mantle, braided knot, crescent spear.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Spear | 24 damage; 37 m/s; authored 0.46 s repeat | Frame the crescent spear outside the short mantle during a ranged shot. | Confirm the visible projectile and first hit match authority. |
| Q · Crossing Step | up to 12 m movement, blocked by solids; 9 s cooldown | Lead with the stepping foot and keep the spear free of the moving leg. | Dash into a wall and check movement ends at the collision. |
| E · Spear Arc | 44 damage; 11 m front fan; 12 s cooldown | Turn the crescent tip into a distinct forward wedge. | Test edge angles, range and a target behind cover. |
| R · Defender’s Vow | 80 shield; 6 m ally radius; 4 s ward; 44 s cooldown | Square the segmented mantle and place thin ward brackets on allies. | Check the six-metre boundary and stronger pre-existing shield. |

## Ulupi · Keeper

The current silhouette is wave crest, scale-edged collar, water-ring staff.

| Input and actual action | Current classic rule | Proposed body and visual layer | Counterplay and QA |
| --- | --- | --- | --- |
| Primary · Staff | 20 damage; 35 m/s; authored 0.46 s repeat | Keep the water-ring staff visible as the ranged primary travels. | Use cover and verify a single projectile hit. |
| Q · River Draw | 28 damage in a 4 m aimed circle; up to 6 m pull; 19 m placement range; 12 s cooldown | Draw a marked water center with an inward-moving broken ring. | Confirm the six-metre pull limit and wall-limited movement. |
| E · Cooling Current | 44 healing; 5 m ally radius; 14 s cooldown | Turn the staff across the torso and display restrained ripples at healed allies. | Compare injured, full-health and occluded allies. |
| R · Naga Basin | 23 m placement range; 7 m radius for 6 s; nominal 12 damage/s while inside; 46 s cooldown | Keep a broad basin perimeter visible through muted water particles. | Cross the radius and check damage ticks, slow and six-second expiry. |
