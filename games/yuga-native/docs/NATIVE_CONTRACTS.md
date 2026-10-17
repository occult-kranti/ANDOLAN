# Native rules, identity and replay contracts

FG00-T04, contract revision 1. This implements a pure Godot admission/stream validator and machine-readable specification. It does not change the browser server, connect a native match, simulate a replay or select production collision authority. The existing native `arena_client.gd` continues to speak browser protocol 2.

## Distinct profiles

| Profile ID | Evidence/state | Rules | Map/authority |
| --- | --- | --- | --- |
| `browser-p2-3v3` | Observed current default | Protocol 2; 3 per team; 480 seconds | 140 × 170 m; Node/TypeScript, 20 Hz simulation and 10 Hz snapshots |
| `native-offline-triad` | Current offline implementation | One controlled hero; no competitive team-slot or match-duration contract (`team_size=0`, `duration_seconds=0` means not applicable) | 140 × 260 m; Godot physics 60 Hz, army 20 Hz, relays 10 Hz |
| `production-6v6` | Proposed, unimplemented | 6 per team; 1,080 seconds | Geometry and authority selection pending FG05-T02; no assigned network protocol or simulation frequency |

Protocol `0` in this catalogue means **no network wire protocol assigned**. It must never be sent to the current browser join endpoint. Browser simulation test overrides permit other durations/bot counts; they do not change the named default profile.

The native profile permits flight, grappling and relay supply. The browser and production profiles do not inherit those training mechanics. The current native hero has no health receiver. Production hero-health capability is a proposal, not an implemented native system.

Runtime definitions:

- [native-contracts-v1.json](../assets/contracts/native-contracts-v1.json): profile versions, finite bounds, coordinate conventions and source digests.
- [native-envelope-v1.schema.json](../assets/contracts/native-envelope-v1.schema.json): original closed JSON structural schema, draft 2020-12. Cross-record semantics and finite-number checks belong to the Godot validator.
- [native_contracts.gd](../scripts/native_contracts.gd): engine-consumable `RefCounted`; no nodes, sockets, rendering, rewards or automatic processing.

## Compatibility and deployment

Descriptors contain `contract_id`, `profile_id`, `protocol`, `versions`, `rules_sha256`, `map_id`, `map_sha256` and `content_sha256`. `versions` has independent positive integer `contract`, `rules`, `map`, `content`, `replay`, `input`, `event` and `entity` fields. Version 1 requires an exact match for each field. There is no permissive protocol range, silent downgrade or fallback-to-offline admission. Mismatch returns a reason such as `MISMATCH_MAP_SHA256` before any world is admitted.

`rules_sha256` hashes compact, sorted-key JSON for `{profile, coordinates, limits}` using Godot `JSON.stringify(..., "", true)` and UTF-8 SHA-256. Version 1 profile numbers have finite fixed values. Changing masks, authority, dimensions, timing, coordinate conventions or caps therefore cannot retain an identical descriptor merely by leaving version numbers unchanged. The loader also rejects changes to the three known profiles' essential semantics. An intentional migration updates the catalogue, relevant version, fixtures and source pins together.

The map digests have explicit scope:

- Browser: exact bytes of `games/yuga/shared/map.ts`, not an independently exported collision mesh.
- Native: exact staged `assets/world/confluence-map.json`. Relay centres remain defined in the separately pinned `relay_control.gd`; they are not invented fields in this map.
- Production: exact design-document bytes, labelled `design_document_not_collision_geometry`. No collision map exists for this proposal.

`content_sha256` hashes compact, sorted-key JSON of the catalogue's `path → SHA-256` source ledger. This is the explicitly enumerated rules-content set, not a claim to inventory every render asset or complete production hero. The source-pin checker verifies those bytes against the checkout. A rules or map edit must refresh the affected pins deliberately; a mismatch fails the check. Packaged catalogue reads do not require development source files.

Admission API:

```gdscript
const Contracts = preload("res://scripts/native_contracts.gd")
var contract = Contracts.new()
assert(contract.load_catalog().ok)
var expected = contract.descriptor("native-offline-triad")
var result = contract.open_session("native-offline-triad", expected,
    {"room":"PRACTICE", "epoch":1, "identity":"hero"})
```

This opens only a **validator session**, never a network connection. The bridge owner supplies authenticated, authority-issued scope. Schema validity is not authentication. Do not accept a client-selected epoch or local catalogue as authority to change rules.

| Operation | Contract |
| --- | --- |
| `open_session(profile_id, remote_descriptor, scope)` | Only when no session exists; complete descriptor match and valid `{room, epoch, identity}` required. |
| `resume_session(remote_descriptor, scope)` | Exact same room, epoch, identity and descriptor. Preserves input/ack/event/snapshot watermarks, entities and tombstones. JSON numeric round trips are accepted. |
| `migrate_session(profile_id, remote_descriptor, scope)` | Explicit new-match/deployment transition only. Same room and identity, strictly greater epoch, known target profile and matching descriptor; then all old stream/pose state is discarded atomically. |
| `reset()` | Explicit local teardown. Clears the guard; it is not authorization to replay an old room. External session ownership must prevent that. |
| Rollback | Select an available old profile explicitly at a new epoch; reject old-epoch inputs/events/snapshots. Never replay old input or reward receipts into the replacement session. |

Failed validation, resume or migration leaves prior state unchanged. Cold reconnect into a new process needs an authenticated full bootstrap and input/event watermarks; that transport/bootstrap adapter remains FG04-T02 work. The implemented resume path intentionally preserves an existing guard's state. Exhausted safe-integer counters require a new epoch, not integer wrap.

## Inputs, events and entity lifetimes

All wire records are closed objects: unknown fields reject. JSON numbers must be finite; booleans are not integers. Integers lie within JavaScript's safe range `0..9,007,199,254,740,991` unless an explicit sentinel applies. Positions are arrays `[x,y,z]`, bounded to ±10,000 m before float32 vector operations; this is a corruption bound, not traversable map admission.

Every record carries `version`, `room` and `epoch`. The authority owns the monotonically increasing positive epoch; reconnect within the same match does not increment it. Inputs/events cannot cross room/epoch boundaries.

**Input** additionally has `seq`, `actor_id`, `move:[x,z]`, `yaw`, `pitch`, `buttons`. Actor ID must equal the session identity. Start at sequence 0; increasing gaps up to 4,096 allow coalesced transport, while duplicate/stale intent rejects. Movement magnitude is at most one. Yaw is canonical radians in `[-π,π]`, pitch in `[-1.35,1.35]` with positive pitch upward.

Button bits: fire 1, jump 2, pulse 4, dash 8, flight 16, grapple 32, descend 64, reload 128, sprint 256. These are logical contract bits, not physical keys. Only mask 3 is admitted for the browser/default production proposal; native offline admits 511. Existing protocol-2 ability/upgrade commands remain a separate real-server API, not new button bits sent over that wire. This validator does not schedule input; authority/bridge integration must enforce the declared 350 ms stale-intent timeout, clear held actions on pause/focus loss/reconnect, and preserve existing command receipts.

**Event** additionally has `seq`, `tick`, `kind`, `actor_id`, `target_id`, `position`, `amount`. Kinds are spawn, despawn, shot, hit, defeat, objective, reward and match_end. Empty actor ID is allowed only for match_end; target may be empty. Start at event sequence 0; require exactly next sequence. Gaps require ordered event recovery/resync, not skipping rewards. Ticks cannot regress; at most 128 events per tick. Amount is finite in `[0,1,000,000]`. The receipt key is `(room, epoch, seq)`; accepting a receipt never itself grants a reward. Referenced actor/target strings are historical labels in this minimal envelope. Gameplay application must bind the authority's lifetime identity and payload definition, rather than using an old event to mutate a reused actor ID.

**Snapshot** has `tick` and a full `entities` array. Ticks strictly increase; a gap over 200 requires resync. This is a bounded transport guard, not a prediction clock or hardware measurement. Maximum 640 entities, plus per-kind bounds: actors 1/6/12 for offline/browser/proposal respectively; minions 96, neutrals 32, structures 32, projectiles 192, zones 128, pickups 32 and gold shards 96.

Each entity has:

```text
id, generation, kind, team, position, yaw, pitch,
discontinuity, alive, ack_input, owner_id
```

The authority owns entity creation, pose, hit outcomes and removal. `owner_id` records attribution; presentation never becomes authority. A full-snapshot omission despawns presentation. Tombstones retain the last generation; the same `(id,generation)` cannot silently reappear. Reuse requires a greater positive generation. Identity kind/team/owner cannot change within that lifetime. Old generations reject. History is bounded at 4,096 IDs per epoch; an exhausted guard requires a deliberate new epoch/bootstrap, not unbounded growth or eviction that permits old lifetimes to return.

Remote pitch is required in this new envelope; it is **absent from current protocol-2 Actor snapshots**, although protocol-2 input and projectile motion already use pitch. An adapter may not infer verified remote pitch from the local camera. That missing data requires an explicit protocol change or an honest unavailable presentation state in FG04-T02.

Discontinuity is a nondecreasing per-lifetime counter. Death/respawn and displacements over 8 m require it to advance. A generation change or increased counter tells presentation to clear interpolation, trails and temporary attachment state; never blend through teleport or death. The 8 m guard requests resync for a large unmarked gap; it does not prove the authority's collision/movement is valid. Ordinary yaw interpolation should take the shortest circular path; pitch is bounded, not wrapped. This module validates poses but does not interpolate them.

The local actor must appear in a snapshot. Its `ack_input` is `-1` before any input, otherwise monotonic and no greater than the last locally issued sequence. Reconnect retains this watermark. Snapshot/payload dictionaries returned by the module are detached copies.

This minimal envelope deliberately does not claim a finished production actor schema: health/shield, equipment, cast phase/time, support surface, movement mode and rule-specific effect shape/expiry must receive explicit typed bridge payloads/version changes before gameplay application.

## Replay and rollback safety

`validate_replay(header, records)` constructs a private guard. Header fields: `format:1`, exact `descriptor`, `room`, `epoch`, `identity`, uint32 `seed`, exact `record_count`. Maximum 100,000 records. Each record is `{kind:"input"|"event"|"snapshot", value:...}` and passes the same stateful acceptance path.

The format records arrival order with independently monotonic channels. It does not invent a global simulation time for input records. Reordered acknowledgements, duplicate events, missing sequence recovery, foreign epochs, incompatible descriptors, malformed entities and inconsistent counts reject. Validation is transactional relative to the caller's active session. Seeking in this version validates again from the epoch start; there is no unchecked checkpoint restore. Seeds are retained metadata, not proof of deterministic simulation replay.

`parse_packet(bytes, channel)` caps input at 2,048 bytes and event/snapshot data at 524,288 bytes before JSON parsing. No resources or arbitrary object classes are deserialized. Replay container file/stream acquisition and total byte budgets belong to the future replay loader; this bounded in-memory validator is not a large-file parser.

## Handoff to the next batches

FG04-T02 should consume `descriptor`, `compatibility`, `report` and the admission methods rather than mutating protocol 2 in place. Keep the actual protocol-2 adapter as a distinct profile boundary. Define actor/minion/structure/projectile/zone/pickup lifetime adapters and a checked shared-yaw/native-yaw transform: shared yaw 0 faces +Z, native camera yaw 0 faces −Z; `shared_yaw=wrap(native_yaw+π)`. Preserve room identity/acknowledged input, add honest pitch availability and clear interpolation on declared discontinuities. Authenticating a cold reconnect and mapping command receipts remain integration work.

FG05-T02 should create a new versioned collision artifact, not relabel the browser source hash as a solved vertical map. Contract axes are metres, +Y up, +Z forward, feet origin; layer bits world 1/actor 2/target 4 describe current native queries. Support surfaces must allow multiple decks at one x/z. Export identical ramp, stairs, ledge, low ceiling and bridge-over-road fixtures with stable collider/support IDs, transforms and visual-only tags. Compare TypeScript shape queries with headless Godot authority on the same two-client inputs before choosing simulation ownership. This module defines the boundary; it performs no collision experiment or online authority selection.

## Verification and observed corrections

From repository root, without imports or rendering:

```sh
python3 games/yuga-native/tools/check-native-contracts.py --report /tmp/native-contract-source-pins.json
XDG_DATA_HOME=/tmp/yuga-contract-tests godot --headless --path games/yuga-native \
  --script res://tests/native_contract_cases.gd -- --report=/tmp/native-contract-cases.json
```

The final owner suite passes 182 cases, including 2,000 interleaved input/event/snapshot cycles, exact entity-history and population caps, malformed types/finite values, epoch rollback, replay corruption and unchanged source hashes. The source-pin checker passes 26 cases. Independent QA passes 170 additional probes on runtime SHA `321ffb170dc44f3f962bc19e12ac441202f213d35662ab2aaa041d0ca8fd4ec8`.

Preserved failures led to three corrections: numeric JSON arrays now compare dimensions by value; malformed Variant scalar types reject before String comparisons; rules identity now covers semantic profile data and rejects changed masks/frequencies/authority. An early checker incorrectly assumed relay sites were in map JSON; it now checks their actual pinned rules source. Reports retain those failures. Evidence is headless specification/validator evidence only; no live server migration, rendered online match, production collision or deterministic gameplay replay is claimed.

Working evidence: `/workspace/scratch/yuga-contracts/` (owner), `/workspace/scratch/yuga-batch1-independent/` (independent QA). Root owns durable evidence archival, backlog acceptance and the next implementation batch.
