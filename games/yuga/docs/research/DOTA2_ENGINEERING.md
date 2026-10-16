# Dota 2 public engineering sources and YUGA lessons

Research date: 16 October 2026 UTC. This is a bounded source study of three public repositories: an analytics service, a data-maintenance project and a replay parser. **None is the complete Dota 2 game or Source 2 engine source.** No game executable, replay, commercial model, animation, texture or audio was supplied, downloaded or extracted. No Dota 2 match or video was watched in this pass, and no Steam account or API credential was requested.

The selected files were fetched over ordinary managed HTTPS into a temporary research directory and read. Repository HEADs were resolved first, then reads used immutable commits. No reference project was installed, built or run. The [source register](dota2-source-register.json) records URLs, retrieval results, sizes, hashes and reading boundaries. The game remains an original implementation; this pass copies no reference code or constants into YUGA.

## What is actually available

| Source / pinned revision | License inspected | Files read and scope | What it provides; what it does not |
| --- | --- | --- | --- |
| [OpenDota core](https://github.com/odota/core/tree/e30f5ac973dfece86d096ee0a27f08c0248948e3), `e30f5ac973dfece86d096ee0a27f08c0248948e3` | MIT; `LICENSE`, copyright The OpenDota Project | Full README/license; selected `svc/util/compute.ts` sections at 69–178, 251–338 and 412–455; full `svc/util/matchups.ts`, `svc/util/scenariosUtil.ts`, `svc/api/responses/ScenarioLaneRolesResponse.ts` | An API/analytics backend consuming Valve WebAPI and parsed replays. Its computation code defines derived statistics, not the authoritative game simulation, matchmaking or current server rules. |
| [dotaconstants](https://github.com/odota/dotaconstants/tree/5c0242df9057848fa2036ca3fafe9f2bd4508163), `5c0242df9057848fa2036ca3fafe9f2bd4508163` | MIT; `LICENSE`, copyright The OpenDota Project | Full README/license and small `json/permanent_buffs.json`/`json/skillshots.json`; first 110 lines of `build/neutral_abilities.json`; `tasks/updateconstants.ts` source URLs at 123–145 and neutral-ability transform at 707–815 | Maintained/generated data and a transformation pipeline. The selected neutral output is an ability-ID-to-image-path registry, not full creature AI, damage formulas, camp geometry or verified current balance. |
| [Clarity](https://github.com/skadistats/clarity/tree/bd37eab0a572cd963dcfeaeaf9afb195f12c43aa), `bd37eab0a572cd963dcfeaeaf9afb195f12c43aa` | BSD 3-Clause; full `LICENSE`, copyright Martin Schrodt | Full README/license, `model/CombatLogEntry.java`, `processor/gameevents/CombatLog.java`, `engine/s2/DotaS2EngineType.java` under `src/main/java/skadistats/clarity/` | A Java replay parser with Source 1/Source 2 representations, combat events and entity/state access. An engine-type decoder describes how to interpret a recording; it does not reconstruct game source or prove every replay version parses. |

The repository licenses describe these tools and their own code. The data pipeline also refers to game-derived text/image paths and upstream repositories; this is not permission to redistribute commercial art or an assertion that every upstream file shares that license. Those images and upstream game resources were not fetched. The OpenDota README's operational installation/account advice is reference text only; none was executed or adopted as YUGA setup.

The official bot-scripting lead, [Valve Developer Community: Dota Bot Scripting](https://developer.valvesoftware.com/wiki/Dota_Bot_Scripting), returned **CONNECT HTTP 403**, curl exit 56, no page body, at approximately 18:31 UTC. No official bot API or script implementation was therefore read. Earlier official Dota home/heroes/new-frontiers access failures remain in [the existing source-access register](../../tools/research/source-access.json). No alternate proxy or verification bypass was used. We cannot claim this pass reproduced Valve bot behavior, camp-stacking rules, deny percentages or patch-specific counters.

## Concrete observations

### Separate measurement from authoritative rules

[OpenDota `compute.ts`](https://github.com/odota/core/blob/e30f5ac973dfece86d096ee0a27f08c0248948e3/svc/util/compute.ts#L73) derives total gold from gold-per-minute and duration; it also classifies lane, neutral, tower and other kill counts from unit names. Those are analytics transformations over supplied records. Their existence does not establish the underlying reward eligibility, rounding, sharing or last-hit rules.

Its lane-efficiency denominator at lines 159–170 is static and explicitly commented **“6.84 change.”** This is a concrete reason not to copy a familiar metric's denominator and label it current economy truth. A pinned repository revision establishes what code was inspected, not that every statistic is current for today's game patch.

For YUGA, `[credited source + nearby eligible allies]` and a single contested shard are explicit original rules. The new `sharedAwards` receipts and gold-event deltas provide a better measurement foundation than inferring earned gold from the present wallet after purchases. Keep initial funds, shared lane rewards, camp rewards, contested claims, structure awards and purchases separately attributable. Camp clears and gold are deliberately distinct from tiebreak score.

### Support contribution cannot be reduced to low farm or a role label

[OpenDota's position estimator](https://github.com/odota/core/blob/e30f5ac973dfece86d096ee0a27f08c0248948e3/svc/util/compute.ts#L255) ranks early gold/last-hit windows and uses early ward purchases as a tie-breaker, assigning core/support positions only when a complete team has the required parsed data. It is labelled an estimate and contains validation claims in comments; this pass did not inspect the linked validation issue or reproduce its reported accuracy.

That is a useful boundary for YUGA: “Keeper” is an authored kit emphasis, while healing delivered, shield actually absorbed, rescue timing and objective participation are observable actions. A low-damage match does not demonstrate low contribution. Conversely, attempted overhealing and an unused shield should not be counted as delivered benefit. No new support-reward formula is proposed from these source files; first measure actual contributions without creating a farmable healing/score loop.

### Neutral identity should be explicit data, with provenance

[dotaconstants' neutral transform](https://github.com/odota/dotaconstants/blob/5c0242df9057848fa2036ca3fafe9f2bd4508163/tasks/updateconstants.ts#L707) resolves inherited unit properties, excludes placeholder abilities and selected attached/courier/building/siege categories, then emits deduplicated ability identifiers. This shows the care needed when deriving a creature category from heterogeneous source data. It is not evidence that a neutral's name alone determines its behavior.

YUGA already has explicit species, camp ID, state and reward fields. Preserve those authored definitions: Reed Naga, Grove Yaksha and Cloudwing use original grounded designs and fixed buffs. Do not infer attack range from an icon or copy a Dota creature's numerical kit. Keep camp aggro, leash, returning invulnerability, regeneration, death, respawn and buff/shard attribution independently testable. Current YUGA bots do not deliberately farm camps, so an AI-only win matrix cannot validate a human farming strategy.

### A matchup association is not a universal counter

[OpenDota `matchups.ts`](https://github.com/odota/core/blob/e30f5ac973dfece86d096ee0a27f08c0248948e3/svc/util/matchups.ts) builds sorted team combinations and outcome keys, excluding a match with an unknown hero ID. [Scenario processing](https://github.com/odota/core/blob/e30f5ac973dfece86d096ee0a27f08c0248948e3/svc/util/scenariosUtil.ts) attaches outcomes to item-timing, lane-role and other conditions, and validates required match fields. These transformations make comparisons possible; they do not establish that a particular pick or purchase caused victory. Opponent skill, team composition, patch and selection effects remain relevant.

YUGA's useful counter claims are narrower: a projectile is blocked by cover; moving before a locked release can avoid damage; Sita's fixed sanctuary loses healing value when allies leave; a minister's pulse does not protect heroes. Use exact interaction fixtures and native observations for those claims, then stratify broader outcomes by side, lane, seed, controller policy and version. Do not retune fourteen kits from a few aggregate bot wins or call one hero a hard counter based on theme alone.

### Events need presence, timing and attribution

[Clarity's `CombatLogEntry`](https://github.com/skadistats/clarity/blob/bd37eab0a572cd963dcfeaeaf9afb195f12c43aa/src/main/java/skadistats/clarity/model/CombatLogEntry.java) exposes `hasX()` alongside optional values such as gold reason, assist players, target building, neutral camp type/team, stun/slow duration, healing and regeneration. Missing fields are not automatically zero. [Its combat-log processor](https://github.com/skadistats/clarity/blob/bd37eab0a572cd963dcfeaeaf9afb195f12c43aa/src/main/java/skadistats/clarity/processor/gameevents/CombatLog.java) collects entries and emits them at tick end; it explicitly warns that a bulk-data message is not decoded. The selected [Source 2 engine decoder](https://github.com/skadistats/clarity/blob/bd37eab0a572cd963dcfeaeaf9afb195f12c43aa/src/main/java/skadistats/clarity/engine/s2/DotaS2EngineType.java) also has an early-Reborn-version warning.

For YUGA, preserve match/source revision, event ID, authoritative tick/time, source actor and target, actual amount and outcome. A successful cast-start is distinct from release, hit and useful healing. A shard spawn is distinct from a claim; a camp reset is distinct from a defeat. The live event feed is bounded and may omit old events, so it is not a complete historical analytics database. A future dedicated run recorder must capture continuously and report dropped/missing records rather than claiming lifetime totals from the last 64 events.

### Objectives require their own outcomes

OpenDota's selected code separates tower/neutral/hero counts and reads objective events for scenarios. That distinction is useful without copying its objective rules. YUGA's end condition remains its own: destroy two defending towers to expose that team's core, destroy the core or resolve the eight-minute score/core-health tiebreak. Report tower/core damage and objective timing separately from hero KDA and gold. The new minister, king and neutral resources should be evaluated for the pressure they create or divert, rather than adding gold directly to victory score.

## Bounded decisions and acceptance work

These are original recommendations derived from the inspected sources. They introduce no gameplay changes during the frozen build and are not claims that human balance, performance or enjoyment was tested.

| Topic | Existing YUGA foundation | Next measurable check / boundary |
| --- | --- | --- |
| Economy accounting | Authoritative actual-delta `sharedAwards`, one-owner shard claims, capped wallets, separate upgrade purchases | For a fixed run, reconcile initial funds + each earned category − purchases with final wallets; distinguish per-hero shared awards from a team pot. Never use a commercial static denominator. |
| Support | Keeper kits and minister shields have explicit recipient/range/duration rules | Track useful heal and actual absorbed shield independently of attempts; compare with objective participation. No inferred “support quality” score from low farm alone. |
| Jungle | Four explicit camps, 30 s first spawn, 40 s respawn, 12 s buffs, original shared/contested rewards | Measure physical clear time, damage taken, time away from lane and buff use; include real players later. Existing bot policy excludes deliberate camps. |
| Counters | Fourteen authored kits and three telegraphed R mechanics | Verify actual timing/cover interactions first; use matched side/lane/policy cases and report sample/version limits. Aggregate matchup wins do not prove a causal counter. |
| Objectives | Towers/core and bounded match end rules | Retain objective-damage/timing outcomes and the authoritative reason for each finish. Gold gain, kills and winning are related measurements, not interchangeable labels. |
| Telemetry integrity | Protocol 2, stable entity IDs, authoritative events and bounded snapshots | Preserve missingness, deduplicate IDs, and distinguish live history from a complete recorder. A parser's supported schema is not proof a particular recording decoded successfully. |

No parser run, replay-derived statistic, official bot implementation, commercial engine reconstruction or player-review conclusion is reported. The Docker smoke, native browser checks, complete match evidence and public deployment remain separate workstreams with their own results.
