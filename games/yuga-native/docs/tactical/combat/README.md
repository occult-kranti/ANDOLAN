# Tactical Casual combat handoff

Task **YUGA-TACTICAL-CASUAL-13**, native offline 5v5, first to 13.
Base commit `7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch
`work/yuga-studio`; concurrent work was preserved. This implements the new
user-selected tactical mode. Historical Rama bow/MOBA rules were not rewritten.

The combat owner applied the YUGA motion/combat skill and implemented
`scripts/tactical_round_rules.gd`, `scripts/tactical_bots.gd`,
`assets/tactical/rules.json`, three focused test scripts and this packet.
Root owns world physics, firearms, player, visuals and input; the map and UI
specialists own their respective host interfaces.

## Passes 1–3: contract, implementation and counterexamples

The rules own buy/live/armed/result/match phases, single life per round,
plant/defuse holds, attacker/defender elimination, deadlines, first-to-13 score,
the round-13 side swap, credits, survivor inventory, utility charges and earned
ultimate points. Purchases use the shared ARKA/SURYA/Kavacha catalog. The
objective is the **Astra**: attackers attune it; defenders sever it. API event
kinds retain `plant` and `defuse` so presentation can use the agreed names.

Root ticks rules once **before** human and bot interaction. A hold can accrue
at most the current authority delta, once per tick. Missing an interaction tick,
death, changed site, release or phase change cancels its progress. Phase expiry
processed by that tick cannot be retroactively undone by a later hold call.
The host owns grounded position/range checks, own-spawn purchase checks and
physical shot/effect validation. Armor absorbs damage before health; friendly
fire is rejected. Time alone never earns ultimate charge.

`generation` changes on a new match or new buy round. Root uses it to reset
actor bodies and firearm magazines. Every event has `seq`, `generation`,
`round_number`, `phase` and `time_s`; `drain_events()` returns independent copies
once. Event kinds are `match_start`, `round_start`, `buy_end`, `purchase`,
`ability`, `damage`, `elimination`, `plant`, `defuse`, `side_swap`, `round_end`
and `match_end`. `snapshot()` deeply copies actors/catalog/score and exposes
normalized interaction progress. Roles swap after round 12; credits and
surviving equipment persist through that swap.

Nine local bots buy affordable equipment in their own spawn, follow supplied
map routes, react to visible enemies, request host-authorized fire and actually
attune/sever through the same timed rules. They stop shooting on lost line of
sight and remain dead until the next generation. Opposite-site retakes retrace
known route segments before taking the alternate route, avoiding unsafe
straight-line shortcuts through cover. This is intentionally a longer route;
a real connectivity-based `route_from` can improve later retakes. Bots do not
spend utility without a matching host effect implementation.

Final focused checks: **53/53 authority** and **21/21 bots**, no warnings or
errors. Counterexamples include duplicate same-tick holds, missed input,
interactor competition, site changes, death during hold, unfinished objective
at deadline, attacker elimination after plant, duplicate purchases/kills,
invalid clock values, snapshot mutation, one-life rules, economy/ult caps,
side-swap timing, closed sight lines and out-of-spawn bot purchases. The bot
fixture is transparent about its synthetic movement/LOS host; its completion
claim is separate from the actual scene run below.

```sh
godot --headless --path games/yuga-native --script res://tests/tactical/round_rules_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/combat/rules-final.json
godot --headless --path games/yuga-native --script res://tests/tactical/bot_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/combat/bots-final.json
```

Reports: [authority](rules-final.json), [bots](bots-final.json). Earlier failure
logs remain: two initially inferred local types required explicit `bool`, and
JSON catalog values needed numeric comparison because JSON numbers load as
floats. The catalog now validates exact semantic values instead of comparing
int/float Variant identities. Expectations were not relaxed.

## One actual-world natural match

The user asked to prioritize look and finished artifacts over expanding stress
testing. Accordingly, one natural actual-scene match was run with the human
idle and nine bots. No actor positions, damage, deaths, scores or winners were
injected. Actual map collisions, movement, firearm raycasts, ammunition,
effects and round rules ran together.

Result: **Sun 13–0 Moon in 666.667 simulation seconds**, with 415 damage events,
89 eliminations, four plants, 123 purchases, 13 buy/live rounds and exactly one
side swap. Six observational checks passed, no warnings or errors. The 13–0
result is a conspicuous balance limitation in one fixed-seed run; this does
not establish fair opponents, human game feel or repeatable match balance.

```sh
timeout 180 godot --headless --audio-driver Dummy --disable-render-loop --fixed-fps 60 --path games/yuga-native --script res://tests/tactical/full_match_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/combat/full-match-r1.json
```

The test used engine time scale 10 and a maximum actual step of 1/6 second,
within the authority's 0.25-second bound. This speeds simulation; it is not
measured FPS or physical-GPU evidence. [Full receipt](full-match-r1.json)
includes every round result, exact world/source pins and final actor state.
Sources were unchanged throughout that run.

## Frozen owned sources

| File | SHA-256 |
| --- | --- |
| `scripts/tactical_round_rules.gd` | `d41cfc4156e5973c7cdf80c435c0fd9d17e483bece496f5b658447696e92871f` |
| `scripts/tactical_bots.gd` | `deb952fc068524f91fd75a04fde149bd2282c39d45119da7a02120b176ef0ca3` |
| `assets/tactical/rules.json` | `cad9040663dcab8adc720cb051c34046b214dd923828d2b5b53af52207a9f017` |
| `tests/tactical/round_rules_cases.gd` | `bfe98a35cc3855efe06585897ab89b6ef9f46e1d6abbddc62f6caaa2d951c7bb` |
| `tests/tactical/bot_cases.gd` | `3795441680be93192aac159a8cabcbe43f59d6d876789acdd115900f747429da` |
| `tests/tactical/full_match_cases.gd` | `6c27cd5e83d74c4814bf53232578c2d4d847fd48cdcee86a2900ef482b649d28` |

Authority receipt SHA-256
`8b557475bfcdd942c5b67422d1598e452d426d604b74cb4060355fb2f62651fd`;
bot receipt `7c0159891e176dc4214629e5c4620951491cd7e59396fb0984a4229935d21ec3`;
actual-match receipt
`34f433e7d23b4c71fb17f2ddf41064eb1874fa5fbf282a8fb75c99172a3c9ee1`.

## Independent corrections and next owner

Source review identified stale held input after pause/focus, incomplete camera
rotation reset after spectating, one-frame phase-boundary movement, vertical
objective eligibility, objective commitment during fire/reload/movement and
ward placement through cover. Root accepted those findings and owns their
implementation/tests. The actual-match receipt pins the root source used then;
later weapon/effects art changes require their own source-bound visual review.

The next weapon/effects source review found two concrete presentation defects.
Reload subtracted from the model's Y position every frame without restoring
the origin, causing cumulative downward drift. Stationary bots retained their
previous movement velocity and could animate marching while firing or holding
the objective. Root corrected reload to reset the model position before each
frame's pose, added a focused reload-origin check, and made actor animation
derive speed from actual position change. These are root-owned corrections;
their actual appearance still needs the R2 original-image review. Another
natural-match run was not needed for those presentation-only changes.

Root owns imports, composed visuals/ordinary input, final package and delivery.
Combat now reviews actual weapon/motion/effects pixels. Remaining independent
gates include art quality, readable useful abilities, human balance/playtesting,
audio listening and hardware performance. Online matchmaking, Ranked/rating
and anti-cheat remain unimplemented roadmap work, never inferred from bots.
