# Isolated native 3D authority pilot

This prototype sends two actual unchanged native arena clients through the existing
Node WebSocket server to a private Godot `CharacterBody3D` authority. The new
explicit factory path passes 13 physics/transport checks, 21 native intake
controls, 23 TypeScript backend-state controls, 23 factory tests, 17 client
checks and two connected native-factory guards. The public server now accepts
a typed, server-selected authority factory; its default remains the existing
planar simulation. Public clients cannot choose an authority or module.

Run from the repository root after the existing locked `npm ci`, with Python 3
and Godot **4.6.3** installed:

```sh
OMP_NUM_THREADS=1 python3 games/yuga-native/tools/arena-bridge-pilot/run.py \
  --output "$RUNNER_TEMP/arena-bridge" --godot godot
```

`--output` must be fresh and outside the checkout. The exact final report is
`$RUNNER_TEMP/arena-bridge/integration-report.json`; failure returns nonzero.
Use a two-minute CI step timeout. The runner has bounded compile, readiness,
contract and client waits and stops its own child process groups in `finally`.
It links existing `node_modules` and creates a small scratch project; it installs
nothing, imports no canonical art and performs no rendering.

The [factory continuation](../../docs/research/reuse-production-continuation/W6/README.md)
owns the direct-import execution and browser regression evidence. The
[earlier execution packet](../../docs/research/reuse-next-ten/W6/README.md)
retains the earlier scratch import-rebinding reports, meaningful flattened-Y
negative control and failed development attempts; those reports are historical.

## Reused implementation

- `games/yuga/server/server.ts` is imported directly. `authority-factory.ts`
  defines the typed synchronous authority boundary, defaults to the unchanged
  planar simulation, and checks the adapter before publishing a room. The pilot
  explicitly passes `createNativePilotAuthority`; no source copying or import
  rewriting remains. `adaptation.json` records the contract/source hashes and an
  empty replacement list. Parser, identity, room lifecycle, rate/size limits,
  clock scheduling and broadcasts are shared with the browser server.
- `games/yuga/shared/simulation.ts` supplies actor creation, the existing input
  sequence/normalization logic and snapshot schema. The thin subclass disables
  its planar `step`, combat, structures, waves, economy and outcome. The pilot is
  a movement/aim fixture, not a second complete match engine.
- `scripts/arena_client.gd` and `arena_interpolator.gd` are copied unchanged into
  the scratch project. Two real Godot processes create/join a room, send inputs,
  receive each other and disconnect through actual loopback WebSockets.
- `assets/contracts/physics-fixture-v1.json` is copied byte for byte. Static-body
  construction adapts `tests/physics_authority_cases.gd`. Locomotion extracts the
  bounded movement core from `scripts/player.gd`, with an explicit shared-input
  adapter instead of the local `Input` singleton.

The exact reused versions and rights are recorded in [NOTICE.md](NOTICE.md).
No new repository download or commercial game client extraction occurs.

## Contract

`bridge-contract.json` pins metres, +Y up, +Z forward, feet-origin positions,
world-XZ movement and positive-up pitch. The capsule has radius **0.65 m** and
height **1.8 m**. This matches Confluence's manifest override; the base player
constructor uses radius 0.29 m for other contexts. The extracted core still does
not establish full player/traversal parity. Native physics runs at 60 Hz, private TCP updates at 20 Hz and
existing server snapshots at 10 Hz. The server alone resets staged positions.

Six shared stages cover stacked decks, a ramp and 0.5 m stair, ledge gravity and
a low ceiling, distinct high/low aim targets, a bridge underpass and stale-input
expiry. The actual stair stops this capsule; the test does not invent automatic
stepping. Actor-to-actor collision is excluded deliberately so two slots can
occupy the same XZ on separate decks and the two aim-control starts can coincide.

The public input schema accepts intent only; injected position, elevation and
teleport fields are rejected by the existing parser. Private IPC pins fixture
and contract hashes and rejects malformed batches before mutation. It caps the
cumulative registry at two identities with immutable unique slots. Backend state
validation binds identity, slot, epoch, native tick, global/stage time, grounded,
velocity, pitch and acknowledgement; incoherent data leaves the last valid state
unchanged. This private loopback channel is not an authenticated remote service.

Protocol-2 `lastInputSeq` still means Node accepted an input. Experimental
`bridgeAckSeq` means native physics processed it. Experimental `bridge` metadata
and actor `pitch`, `velocity`, `grounded`, support and native epoch/tick are
namespaced extensions, not a production protocol migration. New-epoch inputs can
briefly include an older in-flight intent because public protocol 2 has no input
epoch; this remains an integration gate.

## Boundaries and next integration

No native rendered match, prediction/reconciliation, public map negotiation,
complete online combat, dynamic collision, actor collision, reconnect into this
backend, WAN testing, capacity benchmark or physical GPU measurement is accepted
here. Existing baseline reconnect tests remain a separate planar-server result.
The engine reports the physics backend setting as `DEFAULT`; no specific backend
is inferred from that string.

The factory is trusted server integration code, not a sandbox for arbitrary
plugins. It must return synchronously; thrown, asynchronous, malformed or
wrong-room output returns a safe join error without publishing an empty room.
Factory options are a frozen copy with transport-generated room and seed. A
failed first-player creation also leaves no published room. The native pilot
requires its private connection first and refuses nonzero bots or a second
room; it is not a restartable multi-room service.

Next negotiate the native map hash and authority version, commit one native
match clock and input reset epochs, and mount one accepted lane in a rendered
two-client scene. Keep the unchanged planar rules and their browser regression
suite while qualifying that explicit path. Adapter reconnect, service restart,
room disposal, and full online gameplay remain open.
