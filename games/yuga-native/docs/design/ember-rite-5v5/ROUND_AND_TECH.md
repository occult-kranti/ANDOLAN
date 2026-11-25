# Ember Rite · round and authority specification

All values below are **initial tuning** for a future human playtest. The [separate Rust experiment](../../../../yuga-rust/src/ritual.rs) implements only the explicitly identified portions; it is not the current online game.

## Round script

1. **Prepare — proposed, not coded.** Five Sun and five Moon players choose heroes, see their side and sites A/B, and get ten seconds to plan. Start with duplicate heroes allowed in private tests because the current Rust roster has two. No purchases or ultimate economy are required in the first rules test.
2. **Approach — coded round clock only.** Attackers begin with a designated carrier; defenders choose where to hold. A 100-second clock applies until ignition. There are no in-round respawns in the proposed mode; the future match adapter must enforce this.
3. **Carry and recover — coded.** The carrier can drop the ember by death or disconnect; it stays at the last server-confirmed grounded position rather than teleporting away after three seconds. Any living attacker may interact within 1.5 m to recover it. If several request recovery on one tick, the lowest stable seat ID wins. Recovery and ignition cannot both complete in the same tick. Defender pickup is rejected. Actual map collision and line-of-sight validation are adapter work.
4. **Kindle — coded.** Hold interact, grounded and inside site A or B, for **4.0 seconds (80 ticks)**. Release, positive health or shield damage, loss of connection, knockout, leaving the site or invalid server-verified reachability cancels progress. Switching sites starts progress again. The holder is vulnerable; no character can remotely complete the ignition in this first version. A legal completion on the final pre-plant tick succeeds.
5. **Contest — coded basic timer and quench.** Ignition locks its site and begins **40 seconds (800 ticks)**. Any living defender carrying a personal water vessel may hold interact within 1.5 m for **3.5 seconds (70 ticks)**. Only one channel counts; extra defenders do not accelerate it. The same interruption rules apply. If the original defender is interrupted, a second eligible defender starts from zero. The ritual deals **no automatic area damage or team speed buff**. Decorative flames communicate state but have no gameplay hitbox.
6. **Resolve — coded.** Before ignition, all attackers eliminated or time expiring awards defenders; all defenders eliminated awards attackers. A simultaneous pre-ignition wipe awards defenders. After ignition, eliminating attackers does **not** end the round: defenders still have to quench. If all defenders are eliminated or both sides are wiped after ignition, attackers win. Otherwise a completed quench wins for defenders and the expired fire wins for attackers. Lethal damage and elimination resolve before interaction completion; a quench completed on the last fire tick succeeds. A resolved round is frozen.
7. **Reset, sides and match — series scoring coded; reset not wired.** Clear fields, actions, projectiles, vessel and round-specific state, restore heroes and present the result. Regulation is first to **13**, with sides swapped after 12 rounds. At **12–12**, play two-round overtime pairs, swapping sides after each round; a team wins after a pair if it leads by two. After three tied pairs, this private-test ruleset is a draw at **15–15**. Overtime uses the same 40-second fire; a 30-second variant requires separate testing. Planning, resets and score screens are not yet implemented.

An attacker protecting a plant and a defender interrupting it both contribute: the carrier channels while teammates hold entrances; a defender who lands damage resets the channel. After ignition, defenders can fake a quench, draw a response and retry. No hidden stun, elemental multiplier, invulnerability or enemy-revealing cosmetic is granted by this objective.

## Tick order and trust boundary

The rules experiment consumes **ten fixed alternating Sun/Moon seats** and one full set of trusted post-movement, post-damage actor observations per 20 Hz step. `Actor.reachable` is a server-verified gate, never a client assertion. The eventual adapter must derive each position, grounded state, alive/connection state, accepted positive damage and interaction input from server authority; it must validate the relevant site or vessel's floor, collision, distance, line of sight and same-level reachability. The present experiment does not run those world queries.

Within a step: validate the entire observation; reject non-finite coordinates without advancing; apply deaths and elimination precedence; update/drop the vessel; select a legal interaction and advance/cancel its channel; resolve successful completion before the clock expiry on that tick; then freeze a resolved round. `Series` tracks sides and results, but does not itself prevent a caller from recording an unverified winner: only the server must call it after a real authoritative outcome.

The present module does **not** create event IDs, deduplicate network input, serialize snapshots for clients, implement reconnect/grace windows, validate movement, run no-respawn battle rules, prevent another hero action while channeling, implement drop ownership visibility, or reset a real match. Those are required before connecting it to `Battle`, the Wasm/native room workers or browser controls. A disconnect is immediately unavailable to this experiment; production reconnect behavior must be specified before release.

## Visibility, UI and sound contract

- Before a drop, only allies know the carrier's identity from the objective UI. Do not expose hidden opponent position on the minimap through a carrier marker, tail movement, lion, objective VFX, sound or ability preview. Visibility of an actually seen carrier uses the normal server vision rules. Public site ignition and fire timer need distinct, authorized events.
- Show objective state, site, remaining time, channel progress and cancellation reason in text/icons and shape as well as color. A stable ring and segmented timer must remain legible at reduced effects; do not block the site with a pillar of fire. Provide captions and independently adjustable sound.
- Lobby, round briefing, plant/quench and result screens must show attacker/defender roles relative to the viewer. Sun/Moon identity persists on side swap. Separate spectators from players, and reconstruct state on reconnect without replaying a stale cue.
- Same-tick ordering, interaction range and end-of-timer rules must be documented in tutorials. Check both teams, color-vision settings, muted audio, latency, late joining, repeated input and simultaneous channels before a competitive release.

## Test in this checkout

```sh
cargo test --locked --manifest-path games/yuga-rust/Cargo.toml --test ritual
```

Tests exercise the pure rules experiment and its fixed tick boundaries; they do not prove an online match, a map, frame rate, sound mix or balance.
