# YUGA mechanics and AI balance check

Protocol 2 adds three regular lane archetypes, a king siege unit, four neutral camps and contested gold to the fourteen-hero, forty-two-ability arena. The new 168-case scripted matrix completed with stable authoritative source hashes: 166 matches ended at the score-based time limit and two by core destruction. Sun won 86 and Moon 82. Peak population was 62 actors against the cap of 96, with four living neutrals and 19 gold shards against the separate shard cap of 48.

These are implementation and bot-policy observations, not proof of human competitive balance. Focused Chromium acceptance ran concurrently for part of the deterministic matrix. Its per-match wall times are retained in JSON for audit only and must not be used as isolated performance measurements.

## Mechanics with counterplay

| Mechanic | Authoritative behavior | Counterplay checked |
|---|---|---|
| Rama · Dawn Volley | One-second stationary, locked-aim preparation; three arrows at 32 power each before upgrades | Leave the warned lane, use building cover, or defeat the caster before release. Arrows do not pierce cover. |
| Hanuman · Mountain Pulse | 0.7-second preparation and 0.45-second collision-limited travel; landing applies 65 damage and 45 allied healing within seven metres | Move from the marked destination, use solid cover, or defeat Hanuman before landing. |
| Sita · Shelter of Mithila | 0.8-second preparation; a fixed eight-metre sanctuary grants 70 allied shield and heals allies inside for nine health per second over six seconds | Defeat the caster before release or move the fight outside the ring. A completed sanctuary persists after its owner dies. |
| Soldier / City Watch / Minister | Each lane receives all three every eighteen seconds, in separated formations. Watch has a longer firing range; Minister grants up to three nearby other minions twelve shield for three seconds, at most once every five seconds | Attack the support unit, intercept projectiles or fight outside the support radius. Spawn allocation reserves complete Sun/Moon pairs near the actor cap. |
| King | Every third wave adds a king per lane, retaining 240 health and structure priority | Its non-piercing round deals twelve damage to an actor and thirty-two to a structure; a hero can intercept the lower actor amount. |
| Summoned sentinels | Two units retain their owner identity and nine-second expiry; no gold or team score on defeat | Ordinary damage and cover apply. Bounded placement avoids buildings and arena edges. |
| Neutral camps | Four camps appear at thirty seconds, aggro nearby heroes, return invulnerably when leashed, and respawn forty seconds after defeat | Leave the leash area to reset; avoid their non-homing projectiles. Resetting grants no reward. Buffs last at most their remaining duration and end on death. |
| Gold shards | Lane kills grant nearby allies ten guaranteed credits and drop eight contested credits. Camps grant thirty guaranteed and drop thirty contested. Either team can secure the shard with a primary hero projectile, or by approaching after one second | Cover blocks the shot. A shard pays one hero once, expires after twelve seconds and never removes banked credits. Abilities and summoned shots cannot claim it. |

Damage alone does not interrupt a hero's preparation. While preparing, a hero cannot move, fire, jump or start another ability; death cancels the pending payload without refund. Disconnecting preserves the cast and identity. Replaying an accepted command returns its receipt without releasing the ability twice.

The authority freeze passed 175 unit/integration tests across nine files, plus client/server type checks and targeted lint. New coverage includes real primary-shot gold races, cover and expiry, capped receipt amounts, shared-recipient eligibility, token reconnect, all three camp buffs, leash/reset/respawn, mixed ward sources, score-free summons, neutral targeting, paired near-cap wave allocation, and ten seconds of actual mirrored formation movement clear of live plinths and shared buildings. Positioned unit fixtures are distinct from native browser traversal and isolated stress.

## Comparison method

Run `YUGA_EVIDENCE_PREFIX=jungle- npx tsx games/yuga/tools/balance.ts`. The tool compares source hashes before and after the run and rejects changed sources. Current evidence: [jungle-balance-matrix.json](evidence/jungle-balance-matrix.json), completed 2026-10-16.

Each hero replaces one member of a fixed Rama/Bhima/Sita benchmark team. Every focal hero is tested in all three lanes, with two deterministic seeds and both sides: twelve matches each, 168 total. Actual bot decisions and fixed fifty-millisecond steps drive every match; there are no injected wins or adjusted damage values. Bots do not purchase upgrades or deliberately route into neutral camps, so this matrix does not evaluate skilled jungle rotations or gold-denial strategy.

| Focal hero | AI wins / 12 | Mean health damage | Mean deaths | Support cast starts | Mean enemy core damage |
|---|---:|---:|---:|---:|---:|
| Rama | 9 | 9,887 | 11.42 | 0.00 | 143.08 |
| Ravana | 8 | 10,103 | 8.67 | 17.58 | 332.67 |
| Arjuna | 7 | 9,956 | 12.08 | 0.00 | 120.42 |
| Duryodhana | 9 | 10,056 | 7.75 | 13.92 | 276.67 |
| Hanuman | 5 | 8,235 | 11.92 | 20.83 | 126.67 |
| Karna | 10 | 10,368 | 9.25 | 12.83 | 208.33 |
| Bhima | 4 | 9,488 | 10.17 | 0.00 | 236.92 |
| Meghnad | 1 | 9,531 | 12.25 | 0.00 | 79.42 |
| Sita | 5 | 8,640 | 8.83 | 25.42 | 157.33 |
| Draupadi | 7 | 9,031 | 8.58 | 24.67 | 175.92 |
| Subhadra | 10 | 9,223 | 9.50 | 15.08 | 306.58 |
| Hidimbi | 6 | 9,182 | 8.92 | 13.67 | 113.00 |
| Chitrangada | 4 | 9,102 | 11.17 | 7.75 | 173.00 |
| Ulupi | 3 | 8,978 | 10.42 | 13.75 | 82.08 |

Damage counts health removed from actors and structures, excluding shield absorption. Support starts count accepted healing/shielding cooldown starts, including interrupted preparation; they are not effective-healing totals. Core damage and towers destroyed are team outcomes. The JSON also records positive net team healing and shield additions outside bases, excluding respawn. These observations can undercount concurrent damage and are not attributable to the focal hero.

## Interpretation and remaining playtests

The one-to-ten win spread is a lead for further testing, especially Meghnad/Ulupi versus Karna/Subhadra. No hero's damage or health was tuned solely to improve this small AI table. Bots favor some durability and targeting patterns, do not deliberately evade warnings, do not buy upgrades, and place aimed ground abilities at their authored maximum range. Humans can aim down to place zones nearby, which particularly affects placement-dependent kits. The 86/82 side split is a sample result, not proof that the map is unbiased.

Human sessions should rotate lanes and mirror sides with comparable players, recording objective pressure, effective support, avoided damage, upgrade choices, gold contests, jungle travel costs and readability alongside wins. Most scripted games still end on the timer; objective finishing and actual human match length need explicit playtesting.

Historical roster-only evidence remains in [final-roster-balance-matrix.json](evidence/final-roster-balance-matrix.json) and [final-roster-stress-all.json](evidence/final-roster-stress-all.json). Those measurements predate protocol 2 and must not be presented as its capacity or balance result. The even earlier [balance-before-summon-placement.json](evidence/balance-before-summon-placement.json) predates the placement fix.

## Isolated stress

Run `YUGA_EVIDENCE_PREFIX=jungle- YUGA_STRESS_SECONDS=40 npx tsx games/yuga/tools/stress.ts`. The protocol-2 run completed on 2026-10-16 with unchanged authoritative source hashes: [jungle-stress-all.json](evidence/jungle-stress-all.json). Browsers, Docker builds and heavy art work were held; the evidence records one incidental 0.03-second helper syntax check. Server and synthetic loopback clients shared one Node process on a four-core CPU quota, so CPU and memory include both sides.

All six complete-match scenarios passed finite-state and entity-bound checks. Three bot matches reached the 480-second score limit; three fixed-intent synthetic-player matches destroyed the opposing core at 458.7 seconds. Their identical outcomes across seeds reflect that repeated input policy, not independent human trials. Peak population was 63 actors, four living neutrals and 21 shards; the caps remain 96 actors and 48 shards. Simulation-step p95 ranged from 0.48 to 0.98 milliseconds in these scenarios.

| Real loopback clients | Rooms | Duration | Snapshot interval p50 / p95 | Combined CPU, one-core equivalent | Peak RSS |
|---|---:|---:|---:|---:|---:|
| 6 | 1 | 40 seconds | 100.2 / 101.5 ms | 6.2% | 242 MiB |
| 12 | 2 | 40 seconds | 100.1 / 101.6 ms | 9.6% | 241 MiB |
| 24 | 4 | 40 seconds | 100.2 / 102.3 ms | 16.8% | 236 MiB |

All 42 joined connections remained open through their scenario, with no server errors and approximately 19.95 input messages per client per second. Every client observed all four living camps after their thirty-second spawn. These runs cover camp creation and replicated shard/wave populations; native camp combat, rewards and respawn are separately exercised by QA. They do not measure WAN latency, public WSS deployment, adversarial traffic, multi-host capacity or human balance. The deterministic matrix's concurrently recorded wall times remain outside this performance evidence.
