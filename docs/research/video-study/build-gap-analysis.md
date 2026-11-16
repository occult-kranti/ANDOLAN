# YUGA native gameplay continuation

16 November 2026. Build owner `/root/reuse_build_panel`; source baseline
`work/yuga-studio@7162b5d0b666e4422b0bc73100e1fba947d3323f` plus preserved studio
changes. This is a source/runtime gap analysis. This owner did not view the
uploaded videos or game captures; the [gameplay study](gameplay-study.md) and
[ultimate study](ult-study.md) own those observations.

## Current gameplay and the implemented gap

Native Confluence already has a controlled Rama, real damage/health/respawn,
three original local lane armies, player last-hit gold, capture/supply relays,
siege units and core-health outcomes. Its `lane_army.gd` owns the 20 Hz clock,
rewards, bounded units and winner. It is an offline practice game. Fourteen
invocation experiments through Rama are not fourteen finished native heroes.

The concrete economy gap was a gold counter without a native spending decision.
The new original field shop connects existing owned receivers to return-to-base
services. It adds a finite 120-gold starting allowance separately from earned
gold. It never changes `army.gold`. Battle continues while the host stops only
player input for the shop.

| ID | Cost | Actual receiver/effect |
| --- | ---: | --- |
| `heal` | 35 | Restore up to 90 missing health through `rama_vitals.receive_heal` |
| `arrows` | 15 | Add up to 6 arrows, capped at 12, then emit the existing player change signal |
| `ward` | 40 | 55 shield for 8 army-clock seconds through `rama_vitals.apply_shield`; stronger existing shield retained |
| `escort` | 90 | Two existing temporary Sun spearmen: 105 health, 18 damage, 9-second lifetime; current army placement/cap checks apply |

Prices and names are original tuning hypotheses. A player must be alive, within
14 m horizontally and 2.5 m vertically of configured base spawn, in a live
unpaused round, with unchanged and unsuspended receivers. Full/no-benefit,
insufficient-funds and blocked-placement purchases consume no gold. Input
activity is deliberately not an eligibility condition: opening the live UI
stops player input.

Files owned by this task are
`scripts/native_field_shop.gd`, `assets/design/native-field-shop.json` and
`tests/native_field_shop_cases.gd` under `games/yuga-native`. Root owns the shop
panel, battle HUD, world glue, key mapping and outcome metrics integration.

## Frozen interface

```gdscript
signal changed
signal purchased(receipt: Dictionary)
configure(army, runtime, player, spawn, catalog_path = CATALOG_PATH) -> bool
purchase(item_id, expected_epoch, nonce) -> Dictionary
report() -> Dictionary
```

`configure` is single-use for the lifetime of the owner. The army's reset signal
starts a new shop epoch, clears spends and receipts, and waits for the army's
zero-gold signal before admitting commands. It does not sample stale rewards
from the reset callback. `purchase` requires the current integer epoch and a
positive increasing integer nonce. It returns immutable copies of prior
receipts for duplicates and rejects reused/evicted old nonces. The receipt
cache is bounded to 64. Reservation/publication guards reject recursive
purchases. A receiver-triggered round or hero-generation reset cannot charge
its successor.

`report` provides `configured`, `epoch`, `wallet`, `starting_allowance`, `earned`,
`spent`, `near_shop`, `eligible`, `reason`, `pending`, `last_reason` and a fresh
catalog copy. Every row includes `id`, `title`, `description`, `cost`, `icon`,
`effect`, `available`, `disabled_reason` and current numerical `benefit`.
Receipts include `accepted`, `duplicate`, `item_id`, `epoch`, `nonce`, `charged`,
`wallet_before`, `wallet_after`, `reason` and receiver-backed `effect` details.
These are match-local offline commands, not network authentication or a payment
protocol.

## Actual validation

The [retained receipt](field-shop/receipt.json) and [50-case report](field-shop/cases.json)
bind the tested source hashes. The executed command was:

```sh
godot --headless --path games/yuga-native --script tests/native_field_shop_cases.gd -- \
  --report=/workspaces/scratch/native-field-shop-r1/cases.json
```

All 50 checks passed. The fixture uses the actual lane army, minion reward,
hero vitals, shield and temporary-unit receivers; only player ammo/runtime
references use a minimal adapter. It buys an escort at Sun spawn `(0,0,-112)`,
verifies its two real units/stats and expiry, then checks blocked placements,
last-hit reward, zero/double charge, capped benefits, reset generations,
recursive callbacks, invalid tickets/catalog, bounded cache and teardown.
Selected source bytes were unchanged during execution.

This is focused gameplay verification. Root must still review the actual shop
window/input, dense HUD readability, full-round sequence and original balance.
The source remains uncommitted in the shared studio checkout; the two authority
files were frozen and sent to the separate content9 migration owner. Existing
export archives and historical evidence were not changed.

## Next complete-game work

| Gap | Coherent next implementation and acceptance |
| --- | --- |
| Complete offline round journey | Exercise lane pressure → confirmed last hit → base purchase → renewed lane action → core outcome → restart. The existing army remains the only outcome/reward owner; HUD/shop/metrics consume receipts. Root is implementing that flow now. Accept with actual input/captures and source-bound reports, including reset and focus/pause. |
| Persistent build choices | The current shop sells services, not equipment/stat upgrades. Before adding permanent items, define typed ownership and caps for Rama damage/cooldown/movement and serialize that content migration. Do not silently change fixed kit constants or label a shield purchase a full item build. |
| Hero opponents and team tactics | Armies have bounded lane behavior and Rama has practice hazards; this does not establish intelligent enemy heroes, a complete teammate roster or squad matchmaking. A next offline bot slice should own one explicit attack/retreat/target-selection state machine against the current hero receivers and prove path/LOS, death/respawn and lifecycle. |
| Structures and objective depth | Current terminal pressure comes from lane arrivals damaging cores, with separate supply relays. A staged defender/tower objective would need its own finite health/target/blocking state and rendering feedback, then a two-lane race test. New geometry cannot alone establish a complex tactical map. |
| Readable hero combat and production art | Keep the actual five-action Rama receiver/motion pipeline and evaluate contact, anticipation, recovery and support-surface transitions. Concept pictures, still renders and invocation variants cannot accept finished rigs, complete animation or combat readability. |
| Native source-authority adapter | `native_contracts.gd` validates a versioned envelope; `entity_bridge.gd` is a diagnostic presentation bridge. The real `arena_client.gd` still speaks separate browser protocol2. Transport authentication, cold bootstrap/reconnect, typed health/equipment/cast payloads and vertical collision ownership remain separate implementations. Never connect this local wallet to client-selected network rewards. |

The next owner should finish one verifiable offline match journey before
expanding into incompatible engines or a roster whose art and gameplay are
still absent. Public code study remains useful for bounded asset/cache/tooling
gaps; this shop is original code reusing existing YUGA receivers. No foreign
game models, maps, engine binaries or commercial data were imported.
