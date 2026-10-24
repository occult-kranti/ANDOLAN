# W6 — actual two-client native authority feasibility

The isolated native 3D bridge passes its final local run. Two actual native
clients use the existing Node server transport while Godot owns their capsule
positions, gravity, vertical collision and aim. This closes a bounded feasibility
experiment; the browser authority remains planar and a complete rendered native
match remains open.

[execution.json](execution.json) pins the tested source at base
`f09953428767ddbdd7ede27fe53ca72bb3483d15`, versions, checks and retained attempts.
The [tool README](../../../../tools/arena-bridge-pilot/README.md) explains reuse,
contract and remaining protocol work. Canonical server, client, player, map and
package-lock files were not edited by this worker.

## Evidence

| Execution | Actual result | Retained evidence |
| --- | --- | --- |
| Existing planar/native-client baseline | Pass: interpolation, real two-client transport/reconnect, replay and all six negative controls detected | [baseline-report.json](baseline-report.json) |
| Final native 3D pilot `pilot-r10` | Pass: 13 physics/transport checks, 21 native intake controls, 23 TypeScript guards, 17 native client checks; source bytes unchanged | [positive-report.json](positive-report.json), [host](host-report.json), [guest](guest-report.json), [TS controls](typescript-contract.log) |
| Actual flattened-Y mutant | Expected exit 1: five intended vertical checks fail; other eight checks pass and transport stays live; only scratch wire Y was changed | [negative-flatten-report.json](negative-flatten-report.json) |
| Saved snapshot parity | All 204 received snapshot envelopes have exact fixture/contract identities; 99 nonwaiting samples per client match saved native state within explicitly bounded numeric serialization tolerance | [snapshot-parity.json](snapshot-parity.json), [verifier](verify_saved_snapshots.py) |
| Independent adversarial review | W1 owns actual fake-native TCP controls and additional stage/global-clock counterexamples; concrete gaps were fixed before freeze | [W1 review packet](../W1/README.md) |

Saved native samples end at tick 600; each client's final tick 603 is explicitly
outside that saved-sample comparison. The saved actual client reports retain it.
An initial R9 exact floating-number comparison failed because Godot writes a
received number such as `0.000917968340218067` as `0.00091796834021806` in its
report. [That failed comparison](serialization-exact-comparison.json) is retained.
The read-only corrected comparison uses absolute tolerance `1e-9`, with observed
maximum difference `6.94e-18`; IDs, booleans and other metadata remain exact. It
does not claim raw JSON byte identity. Rerun it without starting a server:

```sh
python3 games/yuga-native/docs/research/reuse-next-ten/W6/verify_saved_snapshots.py
```

## What the experiment exercises

The capsule is 0.65 m in radius and 1.8 m high, matching Confluence's manifest
override in `confluence_world.gd`; the base player constructor uses 0.29 m in other
contexts. This is not full player parity. The pilot uses native `move_and_slide`,
6 m/s target speed, gravity 18 m/s² and jump speed 7.2 m/s. Movement inputs use
world XZ; positions are feet origin with +Y up. The exact existing collider
fixture and shared contract hashes appear in every actual client snapshot.

The two peers stand at the same XZ on different stacked decks, climb a ramp,
stop at the existing 0.5 m stair, fall from a ledge, jump under a low ceiling,
shoot high/low ray targets with distinct pitch, preserve underpass/deck elevation
and stop after stale intent expires. The server owns every stage spawn and pose.
Existing public parsing rejects three actual forged position/elevation/teleport
packets; stale sequences and nonfinite input are exercised as well.

Private native IPC validates complete actor batches before mutation, fixes two
identities to unique slots, pins map/contract hashes and rejects malformed,
nonfinite, impossible clock/epoch, teleport and acknowledgement states. A private
backend is trusted executable code; these checks are not a proof against a
compromised local authority. The experiment keeps private IPC on loopback.

The final local headless fixture recorded native-step p50 **483 µs**, p95 **1,448 µs**,
maximum **24,958 µs**, 206 accepted native packets, zero rejected native packets
and two stale public inputs. These values describe this small CPU fixture, not
WAN capacity, production frame time or GPU performance. The engine was Godot
`4.6.3.stable.official.7d41c59c4`; the reported backend setting is `DEFAULT`,
which is preserved without guessing a named backend.

## Failed attempts remain evidence

`execution.json` lists report paths and hashes for scratch attempts R1–R9. Early
attempts exposed a SceneTree callback error, duplicate ESM module instances,
non-running scheduling and JSON float slot membership. R6 reproduced invalid
underpass support placement and a brittle expiry displacement threshold. These
were corrected before the final pass. The old scratch reports remain; these are
debugging attempts, not completed game-production rounds.

W1 separately found cumulative registry/slot and malformed backend-field gaps,
then global/stage clock coherence and persistent partial-packet slot ownership
gaps. W1's unchanged final probes pass 8 actual fake-TCP cases, 4 clock cases
and 2 native slot cases. The final adapter hash is
`647aa7fc3572bf89cb51f32748951af277cce6f42358597c774675f87c96388c`.
The concrete independent counterexamples and failed earlier verdicts remain in
W1's packet rather than being rewritten as successes.

## CI and next lease

After the repository's existing locked `npm ci` and verified Godot 4.6.3 install:

```sh
OMP_NUM_THREADS=1 python3 games/yuga-native/tools/arena-bridge-pilot/run.py \
  --output "$RUNNER_TEMP/arena-bridge" --godot godot
```

The output must be fresh and outside the checkout. The exact result is
`$RUNNER_TEMP/arena-bridge/integration-report.json`; nonzero means failure. Use a
two-minute CI step timeout and the runner's tested per-stage deadlines, without
an external 40-second SIGTERM wrapper. Its `finally` stops only owned process
groups. Locally Node 24.19.0 ran the test with existing locked `ws` 8.22.0 and
`tsx` 4.23.15; the repository requires Node >=22.12 and root's CI uses Node 22.
Node 22 execution must be confirmed by that CI, not inferred from this local run.

The next integration should lease `games/yuga/server/server.ts` for a small typed
simulation/authority factory, replacing scratch import rebinding. Then commit
one native match clock and processed-input acknowledgement/reset epoch, negotiate
the native map/authority version, and mount W4's accepted lane in a rendered
two-client scene. Actor collision, abilities, minions, towers, economy, outcome,
reconnection into this backend, prediction/reconciliation and WAN tests remain
separate named gates. A complete game or Deadlock visual-quality pass is not
implied by this movement/aim result.
