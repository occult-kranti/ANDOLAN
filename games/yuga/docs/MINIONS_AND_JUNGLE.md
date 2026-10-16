# YUGA — lane courts, jungle camps and contested gold

Design contract dated 16 October 2026. This expansion adds four original lane-unit identities, three neutral creature types in four camps, temporary camp buffs and contestable gold. The fourteen heroes and their forty-two ability slots remain unchanged.

**Status:** systems, rendering, animation and UI implementation is in progress. The [fourteen-hero baseline QA](QA.md) predates this expansion. Its real-model checks, bounded simulation/socket runs and AI comparison are useful regression evidence, not proof that the new economy, creatures or interfaces pass. New acceptance results belong in that QA ledger when actually executed.

The numerical source of truth is [shared/map.ts](../shared/map.ts) (`JUNGLE_CAMPS`, `JUNGLE_RULES`, `NEUTRAL_STATS`, `GOLD_RULES`); [shared/types.ts](../shared/types.ts) defines protocol 2. [shared/simulation.ts](../shared/simulation.ts) owns movement, damage, claims, buffs and clocks. No browser or art asset supplies a reward amount.

## Intended play loop

1. Follow an allied wave and identify its soldier, watch and minister. Protect the minister or pressure the opponent's exposed support unit.
2. Decide whether to hold the lane or leave briefly for a nearby camp. Its health, attack and buff are visible before committing.
3. Defeat the creature, receive the credited camp buff and watch for the separate gold shard. An opponent can contest that shard even after losing the creature.
4. Rejoin the wave or rotate while the temporary buff lasts. Towers and the core remain the match objective; camps are optional resources.

This is an original arena loop. No current Deadlock gold formula, deny rule or jungle economy was recovered. “Steal” means claiming newly dropped contested gold; it never removes gold already in another player's wallet.

## Lane units

Sun and Moon use the same roles and rules. These court figures are invented inhabitants of Sangam City, without real politicians, political parties or allegations. Their allegiance is a match-team property. `Actor.unitArchetype` supplies identity while existing `escort`, `siege` and `summon` roles retain their mechanical purpose.

| Asset ID / role | Authored body, weapon and motion | Authoritative combat contract | Intended counterplay to verify |
| --- | --- | --- | --- |
| `soldier` / Spear Soldier | Narrow helmet, clear polearm silhouette, brisk march and forward thrust. The thrust launches the game's visible projectile. | Escort; 130 health, 14 damage, 11 m acquisition, 7 m stopping distance. | Keep spacing or cover; its shorter reach encourages it to advance into a defended lane. |
| `city-watch` / City Watch | Compact shield and baton, squared stance, measured patrol stride and a distinct ranged shot. | Escort; 90 health, 10 damage, 17 m acquisition, 13 m stopping distance. The carried shield is visual equipment, not an extra immunity. | Use cover and another angle against the longer reach; its lower health is an intended vulnerability. |
| `minister` / Court Minister | Upright posture, tall collar, scroll/seal implement; a compact seal shot and visible support pulse. | Escort; 100 health, 7 damage, 13 m acquisition, 9 m stopping distance. Every 5 s, grants 12 shield lasting 3 s to up to three **other allied minions** within 6 m. No self-shield or hero protection from this pulse. | Pressure the support unit, separate the group, or wait out the short shield. Confirm pulse recipients visually. |
| `king` / King siege unit | Broad regal humanoid, crown and layered court armor; deliberate advance and heavy firing recoil. Ground locomotion uses the unit rig. | Existing siege role: 240 health, 3.4 m/s, 22 m acquisition and 14 m standoff; visible-structure priority; projectile damage 12 to actors and 32 to structures. | Intercept its projectile and clear the escort before the next siege arrival. A crown does not imply a hero-sized power budget. |

Waves begin at 1 s and recur every 18 s. Each lane and team receives one soldier, one watch and one minister. Every third wave also receives a king, first at 37 s. The king's authoritative siege behavior is retained. Hero-created summons remain temporary allied minions and grant neither gold nor team score when defeated; they do not become a fourth permanent escort. Ordinary lane defeats still grant one team point, hero defeats five and towers thirty. Camps and gold claims do not add tiebreak score.

The 96-actor cap can limit a scheduled wave. Allocation now reserves whole Sun/Moon pairs for each lane/archetype; fewer than two free slots skips that pair rather than filling the final slot for one team. Soldier/watch/minister use matching lane-parallel offsets of −1.2/0/+1.2 m for both teams, subject to the authoritative collision rules. The exact population and formation checks remain separate from visual review.

The model brief uses grounded, rigged figures. A wheeled throne, vehicle physics, riding animation or additional collision shape is not part of this contract. Art may suggest rank through costume without inventing those mechanics.

## Four camp locations

| Camp ID / display name | Species / creature display name | Centre `(x, z)` | Nearest lane centre |
| --- | --- | --- | --- |
| `west-reeds` / West Reed Court | `naga` / Reed Naga | `(-54, 0)` | Ghat promenade, 14 m |
| `stone-grove` / Stone Grove | `yaksha` / Grove Yaksha | `(-20, 0)` | Ghat promenade or Temple avenue, 20 m |
| `sky-garden` / Sky Garden | `sky-sentinel` / Cloudwing | `(20, 0)` | Temple avenue or Metro gardens, 20 m |
| `east-reeds` / East Reed Court | `naga` / Reed Naga | `(54, 0)` | Metro gardens, 14 m |

The four centres fall inside existing gaps between shared solids. A read-only map check found each centre unblocked at body radius 1.2 m, all 32 samples on each 5 m court circumference unblocked at hero radius 0.65 m, and a clear horizontal approach from the adjacent outer lane at `z = 0`. Straight-line spawn distances are equal for Sun and Moon: about 87.62 m to either outer court and 71.84 m to either inner court. This establishes sampled static clearance and geometric symmetry, not navigation quality or equal farming value.

World art uses flat inlaid courts within those gaps. Raised buildings stay inside existing `SOLIDS`; decorative reeds, stones and banners must not imply cover that the shared collision map lacks. Camps are places in the city rather than a new forest map. Different inner buffs on the west/east sides remain a design choice to evaluate across both teams and all lanes.

## Neutral creatures and temporary buffs

Every camp holds one grounded neutral. Initial slots are dead/inactive until 30 s; a defeated creature respawns 40 s after death. Aggro radius is 8 m and leash radius 12 m. Neutral attacks use projectiles with clear-line checks. Losing its target, exceeding the leash or losing sight for more than 1.5 s sends it home; the returning creature recovers health and resets without a reward. Idle regeneration and return behavior are distinct from a completed kill/respawn. None flies through geometry, changes a hero kit, unlocks a fourth ability or creates permanent account progression.

Returning creatures reject incoming damage until reset; the return indicator and target-lock eligibility must communicate that state. Current bot targeting deliberately excludes neutral camps, although incidental attacks can still affect them. Bot match comparisons therefore do not establish deliberate farming or camp-rotation balance.

| Species | Original silhouette and attack | Health / damage / interval / attack range / speed | Buff for the credited living hero |
| --- | --- | --- | --- |
| `naga` / Reed Naga | Biped river warden with serpent hood and tail, reeds and blue-green accents; a readable water-spit release. Grounded humanoid locomotion, not a low coiling snake rig. | 360 / 14 / 1.5 s / 7 m / 3.2 m/s | **Ward:** raise the shared shield pool to at least 60 and its remaining ward duration to at least 12 s. |
| `yaksha` / Grove Yaksha | Broad woodland guardian with stone/wood surfaces, heavy feet and a club/stone projectile. Weight is shown by posture and recovery rather than hidden knockback. | 460 / 20 / 1.7 s / 4 m / 2.9 m/s | **Vigor:** restore 5 health per second for 12 s while alive, capped by maximum health; at most 60 recovery over a fresh complete duration. |
| `sky-sentinel` / Cloudwing | Original avian humanoid with a beak, folded wings and lilac accents; grounded quick steps and a wing-flick wind projectile. | 320 / 12 / 1.2 s / 7 m / 3.8 m/s | **Haste:** the existing 1.25× movement multiplier for 12 s. No extra flight, jump or fire-rate bonus. |

Buff attribution belongs to the living hero credited with the last hit, including the living owner of a credited summon. A lane minion does not receive a hero buff. The buff and shard are separate: a rival can steal the shard without receiving the creature's buff.

Same-kind duration refresh uses `max(existingRemaining, 12)`, never additive time. Ward shares the existing shield pool and uses `max(existingShield, 60)`: it does not add a new 60-point layer or shorten an existing stronger/longer ward. For example, 100 shield with 20 s remaining stays 100/20 at application; 20 shield with 2 s remaining becomes 60/12. Normal damage and elapsed time then apply to that common pool. Vigor/haste similarly retain any longer existing duration. Death clears these buffs. Tests must cover mixed-source ward expiry; the visual shield must not promise independently timed layers.

The intended choices are protection before an engagement, recovery after damage, or faster rotation. These are hypotheses. Camp clear time, damage taken, delayed lane gold and opportunity to contest remain measurement tasks; the numbers are not a claim of human competitive balance.

## Gold: shared credit and one contested claim

| Defeated unit | Guaranteed component | Dropped component | Other reward |
| --- | --- | --- | --- |
| Lane minion, including king | 10 gold to each eligible nearby allied hero under the authoritative sharing rule | One 8-gold shard | Existing score handling |
| Camp creature | 30 gold to each eligible nearby allied hero under the authoritative sharing rule | One 30-gold shard | Credited living hero's temporary buff |
| Hero | Existing 100-gold rule retained | No new lane/camp shard from this expansion | Existing kill/assist handling |
| Hero summon | None | None | No gold or team score |

The existing sharing rule awards the credited source hero and other living same-team heroes within 26 m of the defeat. The credited source can retain this award even if its projectile arrives after it moves away or dies; receiving a camp buff still requires a living credited hero. Credits are capped at 99,999. Tests should cover these distinctions rather than infer identical eligibility for gold and buffs.

Camp and defeat events expose `sharedAwards: { actorId, amount }[]` with each actual capped wallet delta; the event's nominal `amount` alone is not an individual receipt. A gold-claim event's `amount` is likewise the actual delta after the cap. Presentation should aggregate receipts for the local hero rather than guess eligibility from proximity or a wallet animation.

“30 shared + 30 contested” is not a 60-gold team pot. If two nearby allies each qualify for the guaranteed camp award, they each receive 30; one eligible hero of either team can receive the separate 30 shard. If an opponent claims it, the two allies keep their awarded 30 each and the opponent gains 30. The camp buff remains with its credited recipient.

Each `GoldShard` exposes ID, source, origin team, position, value, creation time and expiry. Rules:

- Its centre is at 1.2 m height, with 0.75 m hit radius. A hero's primary shot can contest it immediately; clients do not send a trusted payout or hit result.
- After 1 s, a living eligible hero within 1.7 m can claim it by proximity, with clear-line and vertical-distance checks. Candidates resolve by distance, then actor ID for a tie. Both teams can contest; `secure` identifies the origin team's claim and `steal` the rival's claim.
- The authoritative first valid claim removes the shard and pays exactly one hero. Simultaneous hits/proximity must resolve deterministically without duplicate awards. An ability, neutral, lane minion or summon must not silently become an extra claim route.
- Lifetime is 12 s and the pool is capped at 48. Expiry and cap eviction remove the shard without payout. Stale snapshots and reconnects cannot reclaim a removed ID.
- No one loses already-earned wallet gold. The UI must distinguish the guaranteed award, a spawned unclaimed shard, and the final confirmed claim.

The extra escort changes the economy even though the per-unit potential remains 18. Excluding kings, one three-unit wave now offers 30 guaranteed gold per nearby qualifying hero plus 24 single-claim gold across its shards. The earlier two-escort wave offered 36 guaranteed per eligible hero. For `n` nearby eligible allies, old guaranteed creation was `36n`; new creation is `30n` plus at most 24 claimed shard gold, possibly awarded to opponents. Neutral camps add another resource stream. Record these effects before changing upgrade prices or claiming the expansion reduces snowballing.

## Presentation and animation contract

Use real, independently animated instances for all seven asset IDs. The existing anatomical/rig pipeline may be reused with original costume and creature shapes; its licenses and generated files remain in the asset provenance ledger. Minimum clips are idle, run, fire and defeat. A minister support gesture or wing motion may be additional art, but cannot add gameplay authority. Root motion remains disabled; server position, facing, attack events and alive state drive presentation.

Team identity, role and neutral hostility must survive low graphics settings and reduced motion. Give the soldier a narrow polearm outline, watch a compact shield outline, minister a vertical collar/scroll outline and king a broad crown outline. Preserve hood, heavy woodland body and folded wings for the three creatures. Avoid relying solely on gold color to identify a claimable shard or on green to identify a buff.

The UI should show a camp's name, health and reward while relevant; a short first-encounter instruction can explain primary fire and delayed proximity pickup. A buff indicator names Ward/Vigor/Haste, its actual effect and remaining authoritative time. Claim feedback names the actual recipient and amount. Gold effects must not obscure an incoming projectile or the core objective, and sound must reinforce rather than replace text/shape feedback.

## Literary sources and adaptation boundaries

Read on 16 October 2026 using the pinned older English editions in [MYTHOLOGY_AND_ROSTER.md](MYTHOLOGY_AND_ROSTER.md). The scope is selected passages, not whole epics, all regional traditions, current religious practice or settled historical reconstruction. No source prose or scanned art is bundled into these units.

| Source actually read | Limited observation | Original game addition |
| --- | --- | --- |
| Griffith, *Ramayana*, Book V, Canto I, “Hanumán's Leap”, especially lines 45405–45437 of the [pinned text](https://github.com/GITenberg/The-R-m-yan-of-V-lm-ki-translated-into-English-verse_24869/blob/b48a7a226e8a20bed61131382aa5b8bf2206e039/24869-0.txt) | The wooded hill passage places Yakshas, Gandharvas and serpent-gods among natural scenery. | Grove Yaksha's stone/wood body, club, hostile camp role and regeneration reward are invented; this passage does not specify that kit or a generic monster taxonomy. |
| Ganguli, *Mahabharata*, Adi Parva, Arjuna-vanavasa Parva CCXVI, lines 19864–19959 of the [pinned text](https://github.com/GITenberg/The-Mahabharata-of-Krishna-Dwaipayana-Vyasa-Translated-into-English-Prose--13-Adi-Parva_7864/blob/f2f859e66ad29dce989b6cd14d15f31a34cfeed4/7864.txt) | Ulupi identifies her naga lineage and has a river/water association. | Reed Naga uses a broad serpent/water motif. It is not Ulupi, a replica of her model, or a claim that nagas are uniformly hostile. Its projectile and ward are invented. |
| Same Ganguli edition, Astika Parva XXIII and opening XXIV, approximately lines 3250–3353 | The passage describes Garuda's birth, radiant bird form, feathers and ascent, followed by reduced size/splendor. | Cloudwing is a new avian arena creature, not the named Garuda as a repeatable enemy. Its grounded locomotion, wind projectile and haste reward are original. |
| Fictional court roles | No particular minister, ruler, caste, ethnic group or modern politician is represented. | Soldier/watch/minister/king identities, costumes, teams and support mechanics are authored game characters. |

The editions and file hashes are retained in the roster source ledger. Regional and contemporary cultural review remains open. Creature hostility is an arena behavior, not a judgment about a community or the source tradition.

## Public game research boundary

[MECHANICS_RESEARCH.md](MECHANICS_RESEARCH.md) and [Deadlock video/tooling notes](../art/DEADLOCK_VIDEO_AND_TOOLING.md) record blocked official/video requests and the sources actually inspected. No Deadlock footage was watched, replay parsed or proprietary asset extracted. Current commercial reward formulas remain unverified.

The useful public-tool lesson is narrower: [Boon's pinned README](https://github.com/pnxenopoulos/boon/blob/0c7663f17aa24a65374925b022fd4d98aaa47477/README.md) describes player, damage, ability, objective and optional lane-unit datasets; [demofile-net's pinned README](https://github.com/saul/demofile-net/blob/fd59701a998cf30a46adc4942e063d90de73c07a/README.md) documents entity/tick inspection. Their public documentation motivates recording YUGA's own kill → guaranteed award → shard spawn → claim/expiry sequence and lane opportunity costs. It supplies no imported combat code, current-patch economy or evidence of player satisfaction.

## New acceptance gates

All gates below are pending expansion-specific evidence at authoring. Passing a source/type check is distinct from a browser encounter or a human playtest.

| ID | Required evidence | Owner / limit |
| --- | --- | --- |
| MJ-1 | Exact three escorts per team/lane per 18 s wave; first king at 37 s; minister selects at most three other allied minions, respects 6 m/5 s/3 s, and grants no hero/self protection. | Systems: deterministic simulation, finite entity bounds and replay. |
| MJ-2 | All four camps inactive before 30 s, then attack valid targets; cover/leash/return/reset behave coherently; death grants once and respawn occurs after 40 s. | Systems plus QA: native approach/attack for one camp; any positional or shortened-clock setup explicitly labelled. |
| MJ-3 | Primary shot and delayed nearby claim each work; both teams can win a contested shard; simultaneous/duplicate/stale claims pay one hero, expiry/eviction pay none, invalid claim routes fail. | Systems/socket tests; QA records one visible secure/steal sequence with the actual wallets and IDs. |
| MJ-4 | Guaranteed reward sharing, last-hit/summon-owner buff attribution and shard ownership are distinct; no summon farming; death, reconnect and finished-match rules cannot repeat a reward. | Systems: eligible/ineligible/rival cases, durable state within the live match. No cross-server persistence claim. |
| MJ-5 | Actual buff numbers, max-health cap, expiry, death cleanup and mixed-source shield/timer behavior match this contract; only authorized speed changes affect movement. | Systems plus native HUD observation; an icon alone is insufficient. |
| MJ-6 | All seven real models load with correct identity, team/neutral status and independent animation; fire/defeat align with authoritative events; no claimed cover lacks collision. | Research/world/QA: export checks and native low/high/mobile frames. Named clips alone do not prove visible motion. |
| MJ-7 | One complete match and revised bounded stress remain finite with the larger wave/camp/shard populations; event and asset lifetime cleanup work. | Systems/QA: actual scenario counts, source hashes and limits. Previous 14-hero runs are historical. |
| MJ-8 | Players can explain shared versus contested gold, recognize the current buff and rejoin the lane; compare lane gold, upgrades, camp time and objective pressure across mirrored seeds. | Root/content: UI acceptance plus future human observation. Automated bot output is not a human balance or comprehension result. |

See [PLAYER_EXPERIENCE_REVIEW.md](PLAYER_EXPERIENCE_REVIEW.md) for the bounded criticism hypotheses and the evidence needed before tuning this contract.
