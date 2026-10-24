# W6 — explicit native authority factory

The existing WebSocket server now accepts a typed, server-selected authority
factory. The native physics pilot imports that server directly and passes its
existing Godot bridge adapter. The previous scratch server copy and string-based
import replacement are removed. The browser default remains the original
`ArenaSimulation`, with unchanged protocol 2, planar match rules and 20 Hz clock.

This is a working integration boundary for the existing movement/aim pilot. It
does not establish a rendered online match or a production native authority.

## Implementation and reuse

`games/yuga/server/authority-factory.ts` defines only the state and methods used
by the transport: room, phase, actors, player lifecycle, intent/commands, step
and snapshot. Factories are synchronous trusted server code; clients cannot
provide a module, URL or factory selector. The default factory constructs the
unchanged shared simulation.

The factory receives a frozen copy of options with server-generated room/seed.
Its result is validated before room insertion. Thrown, asynchronous, malformed
or wrong-room results produce a safe join error without exposing backend error
text. A returned rejecting Promise is consumed before refusing the unsupported
async contract. A failed first-player creation also leaves no published room.
This validation is an integration check, not a sandbox for untrusted plugins.

The existing pilot owns its private TCP/native state guards, two fixed slots,
fixture/map hashes and native clock. Its explicit factory requires a connected
backend and refuses nonzero bots or a second room. The actual client, physics,
stage and protocol behavior remains the prior isolated fixture. No commercial
game code, game assets, model downloads or new network service is used here.

## Executed verification

| Check | Actual result | Original evidence |
| --- | --- | --- |
| Browser regression | 225/225 tests, 14 files; browser TypeScript check passes | [Baseline R2](evidence/baseline-r2/receipt.json), [test log](evidence/baseline-r2/command-2.log) |
| Factory boundary | 23/23 tests, including real failed joins, same-connection parser survival, no leaked rooms, default identity, two peers/reconnect/dispatch, invalid config and native disconnection | [Final TS log](evidence/native-r2/typescript-contract.log) |
| Direct-import native pilot | 13/13 physics/transport checks, 21/21 native IPC guards, 23/23 previous backend-state checks, 17/17 actual native client checks, two connected factory guards | [Final report](evidence/native-r2/integration-report.json), [direct import receipt](evidence/native-r2/adaptation.json) |
| Default server with actual native clients | Transport/reconnect, interpolation/replay and all six meaningful negative mutations pass; source bytes unchanged | [Planar native baseline](evidence/planar-native-r1/integration-report.json) |
| Contract/source separation | 58/58 checks, unchanged revisions and browser/native content pins | [Contract report](evidence/native-contract-pins.json) |
| Type/build/lint | Pilot/test TypeScript check, selected authored TypeScript lint and actual NodeNext server emission pass; emitted server starts and serves protocol-2 health | [Final validation](evidence/final-validation-r1/receipt.json), [compiled server smoke](evidence/final-validation-r1/compiled-smoke.json) |

The native pilot uses Godot `4.6.3.stable.official.7d41c59c4` and Node `v24.19.0`
locally. All native processes are headless and use one worker-pool thread. No
rendering, physical GPU, WAN, production-capacity or human game-feel claim is made.
Node 22 CI remains a separate root qualification.

The first browser typecheck failed because an existing network fixture accessed
planar-only `goldShards`/`time` through the new narrower transport interface.
[That failed log](evidence/baseline-r1/command-0.log) is preserved. Its correction
adds an explicit `instanceof ArenaSimulation` guard at that fixture, strengthening
the default-authority requirement; existing economy assertions are unchanged.

The first direct-import native run passed. The final run repeats it after the
test-only type cleanup and tool documentation freeze; it is not a second
production milestone. The earlier flattened-Y negative remains in the previous
W6 packet and was not rerun or recounted here. W1 owns a separate independent
boundary/WebSocket review.

## Reproduce

From the repository root, with the existing locked dependencies:

```sh
npm run yuga:typecheck
npm run yuga:test -- --maxWorkers=1
OMP_NUM_THREADS=1 python3 games/yuga-native/tools/arena-bridge-pilot/run.py \
  --output /absolute/fresh/scratch/native-pilot --godot /usr/local/bin/godot
OMP_NUM_THREADS=1 python3 games/yuga-native/tools/check-native-arena.py \
  --output /absolute/fresh/scratch/planar-baseline --engine /usr/local/bin/godot
```

Both output directories must be fresh. Existing native foundation CI already
runs the pilot runner, so it now includes the new factory tests without a second
parallel server pipeline. The default native-client tool now pins the new
factory dependency and uses one worker-pool thread; its test assertions and
negative-control mutations are unchanged.

## Next owner

The next packet must negotiate native map/authority identity and explicit input
reset epochs, then mount the accepted lane for two rendered clients against the
real authority. The pilot still has one process-global native connection and a
single staged room. Native backend reconnect/restart/disposal, prediction,
reconciliation, actor collision, full abilities, minions, economy and outcomes
remain open. Do not promote this fixture to the public match server by changing
its default factory.

See [execution.json](execution.json) for exact code hashes, commands, retained
attempts and scope. Historic W6 scratch-import reports keep their original pins.
