# Multiplayer beta: inspected sources and original design

Research performed 16 October 2026 UTC. Scope: the existing browser preview, the accepted shared-room job design, selected pinned permissive source files, one additional REA static analysis and one small interpolation probe. No complete book/repository study, commercial game recovery, reference multiplayer playtest or asset import is claimed.

The systems plan already supplies five repeatable activities, one active room job, explicit Story/Free Roam modes, shared progression, vehicle-bound cargo and recovery after a starter leaves. The recommendations below refine that plan; they do not add another engine, account economy or mission framework.

## Five implementable lessons and acceptance gates

| Lesson from inspected evidence | Original ANDOLAN implementation decision | Falsifiable acceptance |
| --- | --- | --- |
| **Bind actions to explicit states and roles.** Sketchbook's entry instance checks approach/state; seat switching disables conflicting actions until the transition completes. | For cargo jobs, show Load → Drive → Unload. Bind `vehicleId` when loading. Loading requires a stopped driver; the driving leg checks that bound vehicle. A teammate can unload on foot only beside the actual stopped carrier at its destination. A passenger sees the shared state throughout. | Load vehicle A, travel to the endpoint in B: reject delivery. Walking to the endpoint with A elsewhere also fails. Two duplicate unload commands pay once. The HUD explains the failed prerequisite. |
| **Separate shared success from the last actor.** Tank Battle tracks both individual and team scores; Sinander's coordination example distinguishes common benefits from differing preferences. | Credits/project progress belong to the room. Record accepted participants/contributions and show the shared completion receipt. Do not award an exclusive reward to whichever player clicked unload last. Late joiners can perform remaining work without resetting progress. | A loads and B drives/unloads: one shared reward, both accepted contributors visible. A late joiner sees the current stage/cargo car. Replayed completion or reconnect cannot mint another reward. These checks establish rules, not measured human cooperation. |
| **Recovery changes authority, not physical cargo.** Tank Battle removes the departed entity; Godot Bomber ends a running game when a player disconnects. The latter is a useful counterexample for persistent co-op jobs. | Preserve job/cargo position when the starter leaves. Allow the planned participant recovery and later orphan timeout; take-wheel recovers driving separately from cancelling a job. Recovery never teleports a cargo vehicle or completes an objective. | Disconnect the starter after loading; another participant can continue with that car. If nobody eligible remains, a late joiner can recover/cancel after the configured timeout. Repeat the scenario across a room checkpoint/restart. No reward on cancellation; no duplicate payout on completion. |
| **Pacing needs an understandable next action.** Schreiber Level 7 discusses decisions, trade-offs and flow; Tank Battle's completion/three-second winner-state reset shows that an activity needs explicit closure, though its arena reset is unsuitable for a persistent city. | Keep ordinary service/project jobs untimed; reserve a visible deadline for the timed circuit. Show ordered checkpoint progress and a completion receipt before the next offer. Job cards state vehicle requirement, first destination and whether the activity is timed. A provisional two-to-four-minute target is an original playtest hypothesis, not a source fact or measured result. | Reject circuit checkpoints out of order and after the server-owned deadline. A reconnect preserves the accepted checkpoint/deadline. Untimed service work never acquires an invisible failure timer. A player can identify the next verb and place from the normal HUD. |
| **Presentation can interpolate while authority remains current.** Tank Battle separates received targets from entity transforms, but its constant-frame lerp is not timestamp buffering. Geckos supplies timestamp bracketing, identity matching and bounded history; the probe also found edge-case defects. | Use a small original buffer for remote poses only, initially about 100 ms. Keep local player/occupied vehicle and all jobs, seats, payouts and interactions authoritative/current. Snap discontinuities, clear stale history on reconnect and clamp missing samples. Pair this with role-specific action text and a single active-job destination marker. | Midpoint position and shortest-angle wrap are correct; duplicate/out-of-order poses do not rewind; history is bounded; reconnect/time reset, seat change and large displacement snap; missing data never extrapolates indefinitely. The local car receives no added buffer delay. Browser tests separately verify label readability and feel. |

Cargo, rewards, timeout values and pacing targets above are ANDOLAN design choices. None was recovered from a proprietary game. An example's license or popularity does not establish its suitability for this game.

## Exact source register

### R1 — Sketchbook: entry, seats and camera

Repository [swift502/Sketchbook](https://github.com/swift502/Sketchbook/tree/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55), commit `62f4b7986fd1ce1e4f91daba89ef032c20a6ce55`; root MIT license, copyright swift502. The existing notice is retained in [Sketchbook-MIT.txt](licenses/Sketchbook-MIT.txt). This pass read these four files in full as source text:

- [VehicleEntryInstance.ts](https://github.com/swift502/Sketchbook/blob/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55/src/ts/characters/VehicleEntryInstance.ts): explicit approach vector, orientation, entry-capability and distance/height gate. Its values are local-animation assumptions, not ANDOLAN network thresholds.
- [SwitchingSeats.ts](https://github.com/swift502/Sketchbook/blob/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55/src/ts/characters/character_states/vehicles/SwitchingSeats.ts): temporarily disables entering/leaving, changes local occupancy and selects Driving or Sitting after animation. This local transition is not a multiplayer seat-lock protocol.
- [CameraOperator.ts](https://github.com/swift502/Sketchbook/blob/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55/src/ts/core/CameraOperator.ts): separates target radius, orbit and follow modes; clamps vertical orbit; changes displayed controls with the input receiver. Its `lerp(...,0.1)` and velocity damping use fixed per-update factors. ANDOLAN should retain time-based damping rather than importing those constants.
- [SpringSimulator.ts](https://github.com/swift502/Sketchbook/blob/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55/src/ts/physics/spring_simulation/SpringSimulator.ts): interpolates position and velocity between two cached fixed-step frames. This is a local spring, not a network jitter buffer.

### R2 — PlayCanvas/Colyseus Tank Battle sample

Repository [endel/tank-battle-multiplayer](https://github.com/endel/tank-battle-multiplayer/tree/6339493130b4b1d4d28f0f52d17b2fba738c7d47), commit `6339493130b4b1d4d28f0f52d17b2fba738c7d47`; [MIT license](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/LICENSE), copyrights Endel Dreyer and Maksims Mihejevs. Source-only fetches; no game assets, dependency install or server execution.

- [BattleRoom.ts, handlers/join/leave/team selection, lines 133–218](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/server/src/rooms/BattleRoom.ts#L133): server-owned state and 20 Hz callback. The move handler checks JavaScript number type but does not itself enforce ANDOLAN's finite bounded-axis contract; do not weaken ours when learning from this sample.
- [BattleRoom.ts, score and end/reset, lines 422–509](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/server/src/rooms/BattleRoom.ts#L422): individual plus team credit, authoritative winner state, reset and brief outcome display. Borrow the separation of team/individual presentation as an idea, not combat scoring or world reset.
- [BattleState.ts](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/server/src/schema/BattleState.ts): inspected the full schema's synchronized and non-synchronized fields.
- [Game.ts, lines 231–307](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/web-playcanvas/src/Game.ts#L231), [score HUD, lines 453–477](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/web-playcanvas/src/Game.ts#L453), and full [Network.ts](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/web-playcanvas/src/Network.ts): received-state callbacks update targets/HUD, entity removal disposes visuals, score values use text rendering. This source inspection does not establish visual readability on a device.
- [Tank.ts, lines 406–435](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/web-playcanvas/src/Tank.ts#L406): target-position lerp `0.2` and short-angle rotation. Fixed per-frame fractions depend on render rate; the source does not implement timestamped interpolation or a tested WAN latency budget.

### R3 — Godot Multiplayer Bomber: lifecycle and lobby feedback

Repository [godotengine/godot-demo-projects](https://github.com/godotengine/godot-demo-projects/tree/b761b4cd5718a7118f2c95eb55f181d0a5f004f1), commit `b761b4cd5718a7118f2c95eb55f181d0a5f004f1`; [MIT license](https://github.com/godotengine/godot-demo-projects/blob/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/LICENSE.md), Godot contributors/Juan Linietsky/Ariel Manzur. Read the selected scripts in full; no Godot application, textures or fonts were downloaded/run.

- [gamestate.gd](https://github.com/godotengine/godot-demo-projects/blob/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/networking/multiplayer_bomber/gamestate.gd): player registration, host/client signals, load/end flow. A mid-session peer departure makes the server end the game. This is explicitly rejected for ANDOLAN's resumable job design.
- [lobby.gd](https://github.com/godotengine/godot-demo-projects/blob/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/networking/multiplayer_bomber/lobby.gd): disable join/host while connecting, restore controls after failure/end, distinguish current player and host start eligibility. Use explicit state feedback; its IP-address entry is not a recommended browser flow.
- [score.gd](https://github.com/godotengine/godot-demo-projects/blob/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/networking/multiplayer_bomber/score.gd): name/score labels, contrasting text outline and completion display. Its exclusive winner calculation is not our shared room payout rule.

### R4 — Geckos snapshot interpolation: useful model, inspected limitations

Repository [geckosio/snapshot-interpolation](https://github.com/geckosio/snapshot-interpolation/tree/a171cefb626085bfff5241cbd60c8099bdd742bf), commit `a171cefb626085bfff5241cbd60c8099bdd742bf`, package 1.1.1; [BSD-3-Clause license](https://github.com/geckosio/snapshot-interpolation/blob/a171cefb626085bfff5241cbd60c8099bdd742bf/LICENSE), Yannick Deubel. It is not an adopted ANDOLAN dependency.

Read [snapshot-interpolation.ts](https://github.com/geckosio/snapshot-interpolation/blob/a171cefb626085bfff5241cbd60c8099bdd742bf/src/snapshot-interpolation.ts), [vault.ts](https://github.com/geckosio/snapshot-interpolation/blob/a171cefb626085bfff5241cbd60c8099bdd742bf/src/vault.ts) and [lerp.ts](https://github.com/geckosio/snapshot-interpolation/blob/a171cefb626085bfff5241cbd60c8099bdd742bf/src/lerp.ts), plus README buffer/API sections and the initialization/missing-data/capacity cases in `test/snapshot.test.js` and `test/vault.test.js`. Full upstream Jest tests were not run.

A deterministic original probe executed the fetched TypeScript with the already-installed `tsx`. It verified six narrow properties: midpoint position, shortest-arc interpolation for a single-letter radian property, a 300 ms constructor buffer at 10 Hz, empty-buffer return, out-of-order timestamp bracketing, and capacity enforcement. The 300 ms value is observed upstream behavior; the proposed 100 ms ANDOLAN delay is our own starting value.

Two additional probe observations reject blind adoption: `heading(rad)` creates a `g` property and leaves `heading` at the newer value, because the method-token parser captures only the last letter; `Vault.get(1090,true)` returns the old sample at 1000 when the other sample at 1100 is closer. These are bounded observations at this commit, not a claim that all upstream behavior is broken. ANDOLAN's proposed helper uses original pose-specific logic and regression cases for its actual contract.

Probe files are outside the product: `/workspace/research/multiplayer-beta/interpolation-probe.ts` and `.json`. It was a local pure-function execution, not a reference game/network/performance test. SHA-256: probe source `cc62d418dab9c8361ac4607d74021df437c3928c43743990b09eda0b81adb9de`; output `5a539627f53439cba227df634c2b104c6f1d51738103c5fe414814ac05af7f13`. The external `manifest.json` records 24 selected fetched text files, immutable raw URLs and hashes.

### R5 — Design/theory reading scope

Previously inspected readings remain indexed in [SOURCE_REGISTER.md](../library/SOURCE_REGISTER.md): Ian Schreiber's Level 7 decisions/flow and Level 17 interface sections via the pinned archival mirror `5c98165cb261143bda0147463acbaee922ca46c9`; Ludvig Sinander's author-hosted `ch_dom.tex` coordination example, lines 438–455, at `eb0eabb9f53588c5651c5d5e17f0e360156c069d`. This pass revisited the coordination example. The analogy motivates visible commitments/shared outcomes; it does not predict real political behavior, prove an equilibrium for the game or establish player enjoyment. Curated books remain bibliography unless explicitly listed as read.

## Actual additional REA execution

Existing verified REA 6.5.0 CLI, no new installation or persistent integration. Executed:

```sh
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  analyze-javascript-application /workspace/research/sketchbook \
  --source-path src/ts/core/CameraOperator.ts \
  --source-path src/ts/physics/spring_simulation/SpringSimulator.ts \
  --source-path src/ts/characters/VehicleEntryInstance.ts \
  --source-path src/ts/characters/character_states/vehicles/SwitchingSeats.ts \
  --max-heap-mb 512 --analysis-timeout-ms 30000 --json \
  > /workspace/research/rea-output/sketchbook-beta-camera.json
```

Exit 0. Four selected files, 11,023 source bytes, 2,000 visited AST nodes, 54 findings, zero parse failures; 187 inventoried files unselected. Semantic graph: 1,130 nodes, 427 relations, 2,613 explicit unknowns, **partial** coverage. No Sketchbook code or bundle bootstrap was executed. The new pass did not run a semantic trace or infer resolved runtime behavior from parse success.

Evidence ID: `ev_73d78b227adbf6a85cc23ebb0886fc528140f47838a6c3dbc85510eaf38bd191`. Full external result: 4,720,041 bytes, SHA-256 `f8c4119df72a10f2893df6e0cf2e1981d5507c66ddd9163107a5a8c25f93c2b8`. Earlier seven-file seat analysis and its ambiguous trace remain separate runs in [REA_RUNBOOK.md](REA_RUNBOOK.md).

REA helped inventory a bounded syntax/relationship slice with explicit unknowns. Direct source reading established the useful transition/camera distinctions. Neither operation measured game feel; original ANDOLAN unit, network and browser tests remain the acceptance mechanism. Research source files, SHA-256 manifest and probe output are retained under `/workspace/research/multiplayer-beta`, outside the product checkout.

## Implementation status

Job recommendations were sent to the moderator/systems/world owners. The original [RemotePoseBuffer](../../apps/client/src/world/remote-poses.ts) now implements a 100 ms presentation delay, at most 12 samples, shortest-arc heading interpolation, current-entity existence, explicit reconnect reset and discontinuity/seat snapping. Local players and their occupied cars bypass it. Invalid/old packets are rejected and missing future data holds the latest pose. Neither authoritative snapshots nor commands are modified; no inspected source implementation was copied and no reference library was adopted.

On 16 October 2026 UTC, `npx vitest run tests/remote-poses.test.ts` passed **14 tests**: timestamp midpoint/angle wrap, render-call independence, duplicate/out-of-order rejection, missing samples/gaps, local driver/passenger exclusion, seat/occupancy change, large displacement, disappearance/return, capacity, identity change, explicit reconnect reset, server/receipt clock regression, snapshot immutability/playhead ordering, and invalid input. Targeted ESLint and whole-project `tsc --noEmit` also passed. These are deterministic presentation tests, not measured WAN performance or a multiplayer browser acceptance claim.

The renderer integration was inspected: only remote position/heading receive the sampled override, without a second smoothing pass; occupancy, wheel speed, objectives and local motion retain current authoritative values. The current welcome callback calls `resetInterpolation()` even for the same room/player identity. A lower tick alone is deliberately rejected as an old packet, since the buffer cannot infer a new session from that packet. The initial received timestamp anchors server-to-presentation time; the 100 ms value is a provisional presentation budget, not a measured network guarantee. Browser feel, reconnect behavior and the separate job acceptance gates still require the moderator's integration tests.

An independent systems review reran the 14 tests and found no blocking helper defect. This small buffer does **not** adapt its initial clock offset to sustained server slowdown: if simulation time falls more than the delay behind wall time, presentation holds the newest pose until server time catches up or the session resets. It never predicts additional movement to hide that gap. Omission of disconnected players from the helper also does not itself hide their renderer entities; visibility remains a separate renderer policy.
