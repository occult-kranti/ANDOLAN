# Rama in the Sangam civic quarter

Original native offline YUGA design and current implementation, task YUGA-HERO-6R.
Rama is the held horizon: an archer who chooses a firing lane, commits visibly,
uses a short step to change angles, and holds ground with a fixed protective circle.
The existing authored rig, skin, facial morphs and cloth/hair response are retained;
this continuation improves power entry, warnings, feedback and the surrounding world.

## Play the implemented build

From the repository root, `bash tools/studio/launch-native.sh --district` enters
the actual redesigned Confluence map. `--compatibility` selects the existing
OpenGL fallback. Omit `--district` for the title and bow-training journey.
Godot 4.6.3 is required for source execution. Final packaged builds and exact
execution receipts are listed in the handoff, not inferred from this command.

Move with WASD; aim with mouse movement; fire with LMB; reload with R. Q/E/C/X use the kit.
F3 opens the ability guide, F4 the Confluence field shop, F2 controls, F5 resets,
Escape pauses/returns. Controls remain remappable. Flight/tether use the existing
traversal bindings shown in Help. Rama must land on legal ground before casting.

| Action | Implemented purpose | Commitment and counterplay |
|---|---|---|
| LMB · Kodanda |28 damage,40 m arrow, one target;0.18 s draw |Move while drawing; cover stops the arrow;12-arrow supply/reload |
| Q · Piercing Dawn |70 damage,38 m, up to 6 enemies;6 s cooldown |0.65 s committed draw; sidestep or break line with solid cover |
| E · Measured Step |Up to 4.5 m displacement;5 s cooldown |Collision limits destination; no invulnerability |
| C · Guardian Circle |Fixed 5 m radius for 4.5 s;55 shield and 10 healing/s;11 s cooldown |Leave circle to stop healing; granted shield persists until expiry |
| X · Dawn Volley |Three 82-damage arrows in locked lanes;18 s cooldown |0.95 s commitment; releases 0.1 s apart; each arrow stops at first target or cover |

These are existing original tuning hypotheses, not borrowed commercial-game
balance or a claim of competitive acceptance. The 20 Hz kit owns outcomes.
The new two-tone warning retires each lane only when that arrow launches.
The HUD shows actual readiness, draw/recovery, cooldown, empty ammo and three
volley launches. The five-step training journey awards progress only from real
hit, accepted movement and hero-protection receipts; misses earn no progress.
The action guide explains use, counter and combinations without inventing rules.

## Connected playable city

The original three-lane 140×260 m Confluence envelope now contains eight authored
South Asian civic buildings in four families: ghat colonnades, indigo archives,
observatory chhatri courts and brass-eave galleries. Deep shutters, brackets,
plinths, eaves, roof rhythm and distant perimeter galleries replace the repeated
box presentation. Quiet sandstone paving keeps targets and ability strokes legible.

Four 3×2.7×6 m carved cover monuments at x±8,z±60 create approach/escape choices.
Two overhead avenue galleries at z±28 and eight shaded eaves provide actual
native collision above clear ground routes. Existing landing decks, flight/tether,
three capture/supply relays, local armies, camps, siege practice and core outcomes
remain available. Buildings retain solid footprints; shutters do not imply doors.
Elevated combat remains unsupported even though traversal can reach galleries.

The separately authored field shop and battle HUD are integrated by the user's
explicit instruction. Match-local starting allowance is 120 gold. Base services
within 14 m offer 90 health for 35 gold,6 arrows for 15,55 shield/8 s for 40, or two temporary
spearmen/9 s for 90. Actual health/ammo/shield/capacity and spatial eligibility govern
purchases. Opening the shop does not freeze the battle. These are local services,
not account inventory, payments or an online economy.

## Sound and production limits

Existing event-driven Rama audio provides 15 streams with a bounded 4 voice pool;
movement, armies and invocations have their separate existing pools. The reference
study decoded both complete audio tracks and ran local small.en speech recognition.
That supplies timestamped design evidence; it does not establish personal listening
or final mix quality. No commercial-game audio was imported.

Native 3 D collision and the planar army are deliberately separate: overhead
triangles never enter the army's ground-box list. Only the four new solid covers
are appended. The district source manifest pins meshes, textures and the original
map; content revision 10 records the new native authority inputs. Browser protocol 2
and proposed production 6 v 6 remain distinct. No online integration is implied.

The generated art-direction PNG is a concept only. Actual runtime images, source
hashes, executed tests and known defects belong to the final evidence receipts.
Human audio/feel review, strong defeat performance, hair/drape polish, enterable
interiors, elevated ranged combat, operated online play and physicalGPU profiling
remain production work rather than claims of this local implementation.
