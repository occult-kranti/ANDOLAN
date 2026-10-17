# Native arena transport: verified library

`scripts/arena_client.gd` connects Godot 4.6 to the existing YUGA protocol-2 Node authority. Two independent headless Godot processes have joined the same actual server, moved through authoritative inputs, exchanged snapshots, received command results, reconnected and completed short matches. This library has not been connected to the rendered native scene, its camera or its UI. It does not establish a playable native online match or commercial production readiness.

## Contract and integration

The existing authority remains responsible for movement, collision, health, economy, abilities and outcomes. The adapter emits intent; accepted snapshots are the source of gameplay state. Its lifecycle is `disconnected → connecting → joining → playing → finished`, with transport loss returning to `disconnected`.

Add the script as a child `Node` so its `_process` polls `WebSocketPeer`. Connect signals before opening a transport:

| API | Contract |
| --- | --- |
| `connect_arena(endpoint, hero_id, player_name, room_code="")` | Creates a session through `ws://` or `wss://`; returns a Godot `Error`. Use the authority's `/ws` endpoint. An empty room creates a room. |
| `reconnect_arena()` | Reuses the current in-memory, room-scoped session token. Clears snapshot history and pending commands; preserves input ordering. |
| `disconnect_arena()` | Closes transport and clears identity, credentials, snapshots and command state. |
| `can_reconnect()` | Indicates an available session token and room, not a guaranteed successful reconnect. |
| `send_input(move, yaw, pitch, fire, jump)` | `Vector2` maps to world X/Z; returns whether a packet was sent. Call continuously with current intent. |
| `send_ability(slot)` | Accepts slots 0–2; returns a command ID, or an empty string if unsent. |
| `send_upgrade(upgrade)` | Accepts `power`, `vitality`, `tempo`; returns a command ID, or an empty string. |
| `get_snapshot()` / `get_previous_snapshot()` | Deep copies of accepted authority snapshots. |
| `pending_command_count()` | Number of pending command receipts. |

Signals are `state_changed(state)`, `welcomed({id,room,protocol})`, `snapshot_received(snapshot)`, `command_result(result)`, `protocol_fault(fixed_code)`, `disconnected(code)` and `match_finished({winner,reason,scores})`. Reconnect credentials are never included in signals, reports or log messages. They remain in memory only. Raw server error text is replaced with a fixed error code.

Input transmission is limited to 20 Hz. Movement is normalized, yaw wrapped and pitch clamped. A sequence number advances only after a successful send and stays above the latest authoritative acknowledgement across reconnects. Commands are limited to 20 Hz and 32 pending entries; a missing receipt expires after four seconds. Commands are not automatically replayed. The finish signal fires once per connection and stops gameplay intents.

Reconnection is explicit; the library does not run an unbounded retry loop. When pausing, keep submitting neutral intent until accepted by the rate limiter, or disconnect. The existing authority also clears stale intent after 350 ms. Reset the presentation interpolator on every transport start, including reconnect to the same room; see [the interpolation contract](NATIVE_INTERPOLATION.md).

## Defensive bounds

The adapter retains two snapshots. A packet may contain at most 512 KiB; the WebSocket has a 1 MiB inbound buffer, 8 KiB outbound buffer and 32 queued packets. Processing consumes at most 16 packets per poll. Connect/join has an eight-second deadline. Five consecutive invalid messages close the connection; an accepted snapshot resets that invalid-message count.

Snapshot validation covers protocol, room, connected local human identity, required fields, finite numeric values, duplicate IDs and collection bounds: 96 actors, 192 projectiles, 64 events, 48 gold shards, and 32 entries in each other collection. Coordinates are bounded to ±10,000. The recursive JSON check limits depth, collection sizes and string lengths. Older or duplicate ticks are dropped; decreasing server time and a finished-to-playing regression are rejected. JSON-decoded whole-number floats are accepted for protocol integer fields. Victory events may carry the authority's empty actor ID.

Two independent review findings required extra numerical constraints:

- A finite double is not necessarily safe for angle arithmetic. Literal `+1e308` and `-1e308` yaw values are rejected before subtraction. Accepted incoming yaw must be within ±`TAU`; the interpolator normalizes it before arithmetic.
- A positive double interval can underflow when Godot divides a float32 `Vector3`. Positive server times and positive snapshot intervals below one microsecond are rejected. A tiny terminal remainder is allowed only after a usable absolute timestamp because the final pose is held without division. Equal-time newer ticks remain valid. Match duration is capped at the authority's 4,800-second maximum.

These are defensive input constraints, not a change to the server protocol or simulation. Computed presentation poses receive an additional finite-output check in the interpolator.

## Four review rounds and fresh verification

1. Audited `games/yuga/server/server.ts`, `server/clock.ts` and `shared/types.ts`: protocol version, room identity, reconnect token, sequence acknowledgement, command receipts and final snapshots.
2. Implemented the bounded transport and independent headless client driver. Real-server compatibility covered decoded numeric fields and the empty victory actor ID.
3. Exercised two real native clients, reconnect, stale/malformed traffic, command bursts, finish handling and cleanup. Independent review then exposed the extreme-yaw and subnormal-time defects described above.
4. Reconstructed the owned files after a workspace replacement, implemented the numerical fixes, reran the complete suite and archived fresh evidence. The earlier local source copies, probe and reports were lost; they are not presented as surviving artifacts. A fresh deterministic case reconstructs the unsafe arithmetic expressions and confirms that they produce NaN on the pinned engine before testing the corrected behavior.

Run from the repository root after `npm ci`, with Godot 4.6.3 installed:

```sh
python3 games/yuga-native/tools/check-native-arena.py --output /tmp/yuga-native-network-new-run
```

The output directory must not already exist. Use `--engine /absolute/path/to/godot` if needed; the default is `/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64`. The runner creates a tiny isolated Godot project, imports no production art, binds an ephemeral loopback port, starts the existing Node authority, and cleans up all processes. It checks source hashes before and after execution. No server implementation is replaced by a mock.

The [fresh aggregate report](../tests/evidence/native-network-final/integration-report.json) passed every aggregate check. Its [archive manifest](../tests/evidence/native-network-final/manifest.json) pins exact report and recording bytes, source files and sizes.

| Fresh test scope | Result |
| --- | --- |
| Deterministic interpolation cases | 27 passed |
| Six-second, two-client transport match with host reconnect | 22 host / 20 guest checks passed |
| Separate four-second, two-client interpolation recording | 20 checks per client passed |
| Original and impaired replay of each actual recording | 29 checks per recording passed |
| Six intentionally defective interpolation copies | All six detected by failing assertions |

Each live client rejected four malformed frames and dropped one stale frame. The injected traffic included literal extreme yaw and `1e-50` time, sent over the actual sockets. The reconnecting host retained identity, purchased progress and sequence ordering: sequence 35 before reconnect, authoritative acknowledgement 119 afterward. A 128-call command burst transmitted one command. Each suite ended with zero connected transports; authority shutdown left zero rooms. These short loopback runs are bounded integration evidence, not a long-match soak, WAN benchmark or visual frame-rate measurement.

Final adapter SHA-256: `b0482d783a9e9bf9b64be8f07c8878259cd417f39bb90ae7b4752d1b7e34cbb0`.

Aggregate report SHA-256: `7a06cb1e770919e1323adc5ab4d1e67cb6b06e554cfe2db62510527041abe237`.

## Remaining integration

Rendered actor spawning, local camera/input wiring, remote animation/VFX events, projectile and neutral presentation, native HUD and reconnect UX remain open. Deployment needs a reachable authority; GitHub Pages only serves static content. Full-length matches, sustained room capacity, real network impairment, TLS deployment and rendered multiplayer performance need separate validation. This milestone makes the transport and actor-pose sampling available for that work.
