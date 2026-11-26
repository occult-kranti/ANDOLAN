# Ember Rite balance measurements

Use these figures to decide where to test a split push, late rotation or interrupted quench. All distances and times come from the authored floorplans. The runner walks at 5 m/s. The model counts the bent routes, grades, shallow-water allowance and authored fold time. Opponent decisions, camera peeks and combat delays need human matches. [Travel model and full routes](measurements.md) · [Hero decisions](../HERO_BALANCE.md)

## Time to change sites

At the instant of ignition a defender at the other site centre has 40 s. The dry margin is 40 s less dry travel and a successful 3.5 s quench. The last column also deducts one interrupted quench that lasted 3.45 s, one simulation tick short of completion. Both cases assume immediate movement, a centre placement, and no extra channel delay. A negative value is a missed deadline. The closed-mid column removes the room and both spawns. A dash means that this closure severs the dry connection.

| Map | Dry A–B | All links | Dry, mid closed | Dry margin | After one late interrupt |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mandala Rift | 11.4 s | 11.4 s | 24.3 s | 25.1 s | 21.7 s |
| Lanka | 21.9 s | 21.9 s | 29.6 s | 14.6 s | 11.1 s |
| Ayodhya | 28.0 s | 24.5 s | 34.7 s | 8.5 s | 5.0 s |
| Kurukshetra | 21.9 s | 21.9 s | 27.2 s | 14.6 s | 11.2 s |

## Time to set up and space to enter

Defender lead equals attacker arrival minus defender arrival at the same site. A positive lead gives the defender time to set up. For each side, the door column gives the widest pair of threshold points that two players can reach by dry routes sharing only their spawn and the final objective. The other spawn and site are closed. Each threshold is where its last centreline enters the rectangular site room. The search splits each room into an entry and exit with capacity one and sends one unit of flow to each candidate door.

Hanuman’s single Sena field is 6 m across. A separation greater than that diameter proves a stationary disk cannot cover both threshold centres simultaneously. A smaller separation only means it might fit. Range, solid walls and the caster’s placement still matter. This test says nothing about other abilities, standing inside the site, or whether two players clear the corners at the same time.

| Map / site | Attack | Defend | Defender lead | Attacker doors | Defender doors |
| --- | ---: | ---: | ---: | --- | --- |
| Mandala Rift / Ghat Mandapa | 26.6 s | 24.8 s | +1.8 s | 24.2 m · separate | 24.2 m · separate |
| Mandala Rift / Bazaar Sanctuary | 31.5 s | 29.1 s | +2.4 s | 21.2 m · separate | 20.0 m · separate |
| Lanka / Signal Court | 24.7 s | 19.8 s | +4.9 s | 22.9 m · separate | 20.8 m · separate |
| Lanka / Ashoka Garden | 18.9 s | 21.7 s | -2.8 s | 22.8 m · separate | 20.1 m · separate |
| Ayodhya / Assembly Court | 23.3 s | 24.2 s | -0.9 s | 21.0 m · separate | 21.0 m · separate |
| Ayodhya / Ferry Quay | 17.9 s | 18.3 s | -0.4 s | 23.8 m · separate | 23.8 m · separate |
| Kurukshetra / Palace Terrace | 22.8 s | 19.5 s | +3.3 s | 17.9 m · separate | 16.3 m · separate |
| Kurukshetra / Wind Field | 20.6 s | 14.6 s | +6.0 s | 14.2 m · separate | 11.7 m · separate |

The JSON lists the rooms, exact X/Z thresholds, map content hashes and full comparison precision. Recompute both files with `python3 balance.py` in this directory, or use `--check` to detect stale output. [Machine-readable measurements](balance.json) · [Sena’s runtime radius](../../../../../yuga-rust/assets/vanara-sena.json) · [Round timing and tick order](../../../../../yuga-rust/src/ritual.rs)
