# YUGA mechanics and AI balance check

The current build has fourteen playable heroes and forty-two abilities. Three ultimates now have authoritative preparation states and distinct effects. All 168 cases in the final scripted comparison finished within the 480-second match limit; the largest observed population was 43 actors against the cap of 96. Two matches ended by destroying a core; the other 166 used the published timer tiebreak.

This is useful implementation and AI evidence. It does **not** establish human competitive balance.

## Mechanics with counterplay

| Mechanic | Authoritative behavior | Counterplay checked |
|---|---|---|
| Rama · Dawn Volley | One-second stationary, locked-aim preparation; three arrows at 32 power each before upgrades | Leave the warned lane, use building cover, or defeat the caster before release. Arrows do not pierce cover. |
| Hanuman · Mountain Pulse | 0.7-second preparation and 0.45-second collision-limited travel; only the landing applies 65 damage and 45 allied healing within seven metres | Move from the marked destination, use solid cover, or defeat Hanuman before landing. |
| Sita · Shelter of Mithila | 0.8-second preparation; a fixed eight-metre sanctuary grants 70 initial allied shield and heals allies inside for nine health per second over six seconds | Defeat the caster before release or move the fight outside the ring. Leaving stops healing; a completed sanctuary persists after its owner dies. |
| Siege sentinels | Each third wave adds one per lane, alongside the two regular escorts. Siege units prefer visible structures and have 240 health. | Intercept their non-piercing rounds or defeat the unit. A round deals 12 damage to an actor and 32 to a structure. |
| Summoned sentinels | Two temporary units retain their summoner identity and authoritative nine-second expiry | Ordinary damage and cover apply. A bounded placement search prevents spawning inside a building or beyond the arena edge. |

Damage alone does not interrupt preparation. A caster cannot move, fire, jump or begin another ability while preparing; death cancels the pending payload without refunding its cooldown. Disconnecting preserves the authoritative cast and identity. Replaying an accepted command returns its receipt without releasing the ability again.

The focused suite passed 113 tests: roster effects, simulation rules, three fixed-clock cases, real WebSocket authority/reconnect cases, and twenty detailed mechanics regressions. It covers fatal and nonfatal interruption, death during Hanuman's actual travel, sanctuary departure, solid cover, warned-lane evasion, siege targeting/interception, all-lane progression, and summon placement. These are separate from native browser acceptance and performance stress.

## Comparison method

Run `npx tsx games/yuga/tools/balance.ts` from the repository root. The tool checks authoritative source hashes before and after the run and refuses to report if those files changed.

Each of the fourteen heroes replaces one member of a fixed Rama/Bhima/Sita benchmark team. The opposing team keeps that benchmark. Every focal hero is tested in all three lanes, with two deterministic seeds and both mirrored sides: twelve matches each, 168 total. Every match uses actual bot decisions and fixed 50-millisecond simulation steps. There are no injected wins or adjusted damage values. Bots do not purchase upgrades.

Final evidence: [balance-matrix.json](evidence/balance-matrix.json), completed 2026-10-16. The earlier [balance-before-summon-placement.json](evidence/balance-before-summon-placement.json) is retained to identify the run before the wall-placement correction. Its results are not the final build's measurement.

| Focal hero | AI wins / 12 | Mean health damage | Mean deaths | Support cast starts | Mean enemy core damage |
|---|---:|---:|---:|---:|---:|
| Rama | 6 | 9,496 | 12.25 | 0.00 | 279.58 |
| Ravana | 10 | 9,800 | 9.42 | 16.50 | 309.42 |
| Arjuna | 3 | 9,508 | 12.50 | 0.00 | 187.00 |
| Duryodhana | 9 | 10,123 | 9.00 | 14.67 | 308.33 |
| Hanuman | 3 | 8,134 | 11.50 | 20.75 | 318.25 |
| Karna | 7 | 9,958 | 10.67 | 14.17 | 446.08 |
| Bhima | 6 | 9,391 | 10.50 | 0.00 | 190.17 |
| Meghnad | 2 | 9,083 | 13.08 | 0.00 | 171.17 |
| Sita | 7 | 8,790 | 9.33 | 26.67 | 259.00 |
| Draupadi | 9 | 8,994 | 9.25 | 25.33 | 222.33 |
| Subhadra | 6 | 8,583 | 10.75 | 14.17 | 392.92 |
| Hidimbi | 9 | 9,074 | 9.83 | 13.83 | 300.67 |
| Chitrangada | 7 | 9,252 | 11.67 | 7.42 | 222.08 |
| Ulupi | 4 | 8,889 | 10.75 | 14.58 | 155.92 |

Damage counts actual health removed from actors and structures, excluding shield absorption. Support cast starts count accepted healing/shielding cooldown starts, including interrupted preparation; they are not effective-healing totals. Core damage and destroyed towers are team outcomes. The JSON also records conservative positive net team healing and shield additions outside bases, excluding respawn. Those observations can undercount concurrent damage and cannot be attributed to the focal hero.

## Decisions and remaining playtests

The volley was capped at 96 total base power, close to the prior single shot's 92. The implementation corrected three concrete defects found during review: stale actor iteration after an area kill, effect metadata overwritten by actor fields, and summons placed inside cover. Siege rounds now select their damage from the object actually hit, so a hero intercepting an anti-structure shot takes the actor value.

No hero received a damage or health adjustment solely to improve this small AI table. The 2–10 win spread deserves further testing. Simple bots favor some durability and targeting patterns; they do not deliberately evade warnings, purchase upgrades or coordinate team compositions. Their aimed ground abilities use the authored maximum range, whereas a human can aim down to place a zone nearer. This can distort comparisons involving Meghnad, Ulupi and other placement-dependent kits.

The next useful human sessions should mirror sides and rotate lanes with comparable players, especially Ravana versus Meghnad, and compare support-led objective teams with burst-led teams. Record effective support, avoided damage, objective pressure, upgrade choices and perceived ability readability alongside wins. Wider matchup coverage and real player feedback are needed before making a ranked-balance claim.
