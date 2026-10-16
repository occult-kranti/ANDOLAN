# Online flow: research panel rounds 4–6

Reviewed on 15 October 2026, America/New_York (16 October UTC). This is a source review and bounded automated validation of the browser preview. It does not establish a public deployment, WAN performance or human playtest results.

## Round 4 — two concrete recommendations

The audit read `apps/client/src/connection.ts`, the client command/status/input paths, `apps/client/src/world/index.ts`, the room service, protocol, existing network/browser tests and deployment instructions. The moderator accepted both changes below and implemented them in the existing PlayCanvas/Node application.

| Observed contradiction before the revision | Accepted change | Acceptance gate |
| --- | --- | --- |
| The server deliberately closed a displaced identity with code 4001, but the client retried every close. A successful welcome reset the retry counter. Two tabs holding the same token could repeatedly take the identity back from each other. Permanent join errors also retained the same failed automatic retry path. | Treat identity supersession and permanent join errors as terminal for automatic retries; offer deliberate reconnect. Ignore callbacks from obsolete socket attempts. | Superseded tab remains paused with no new socket after 30 seconds; explicit recovery uses the accepted room/token. Delayed close/message events from the old socket do not affect the replacement. Permanent join errors stop retries. |
| The connected indicator and input eligibility depended on socket closure. A silent connection could remain apparently connected while no city state arrived; server heartbeat cleanup is periodic and is not immediate player feedback. | Pause actions and report stale city state after more than two seconds without a snapshot; recover on fresh authoritative state. | With the transport open but snapshots absent, both movement input and commands stop. A fresh snapshot restores action eligibility for the same player without replaying attempted stale commands. |

The takeover finding was independently confirmed by the systems reviewer. The manual-reconnect revision initially needed a callback-generation guard: closing an old socket is asynchronous, so its eventual close must not schedule a second replacement. This correction belongs to the first recommendation, rather than expanding the scope.

These changes preserve the server as the authority for positions, seats, mission progression and ballots. The client may explain waiting, but it does not advance the story in order to hide transport loss.

## Primary source inspection

All repositories were retrieved through the configured HTTPS Git path. These are inspected implementation references, not packages adopted into ANDOLAN. No upstream test suite or game was executed in this pass. No source or assets were copied into the product.

| Source and pin | Sections actually read | Applicable lesson and limit |
| --- | --- | --- |
| [Colyseus monorepo `7342663d6af8c41b9d6968f83849102cf5cf83ca`](https://github.com/colyseus/colyseus/tree/7342663d6af8c41b9d6968f83849102cf5cf83ca), MIT; core 0.18.18, SDK 0.18.5 | [SDK Room.ts, lines 153–181](https://github.com/colyseus/colyseus/blob/7342663d6af8c41b9d6968f83849102cf5cf83ca/packages/sdk/src/Room.ts#L153), [reconnection, lines 745–798](https://github.com/colyseus/colyseus/blob/7342663d6af8c41b9d6968f83849102cf5cf83ca/packages/sdk/src/Room.ts#L745) | Distinguishes retryable close causes from leaving, rejects pending requests on closure, and bounds reconnection attempts. ANDOLAN uses its own close code and token protocol; upstream constants are not assumed interchangeable. |
| Same monorepo | [Core Room.ts, lines 887–921](https://github.com/colyseus/colyseus/blob/7342663d6af8c41b9d6968f83849102cf5cf83ca/packages/core/src/Room.ts#L887), [allowReconnection, lines 1942–2020](https://github.com/colyseus/colyseus/blob/7342663d6af8c41b9d6968f83849102cf5cf83ca/packages/core/src/Room.ts#L1942) | Reconnection reserves a specific session using a token; duplicate reservation calls are handled and reservations may expire. ANDOLAN's two-minute disconnected-seat policy and persistent hashed identities are its own design. |
| Same monorepo | [WebSocketTransport.ts, heartbeat options/defaults and lines 259–275](https://github.com/colyseus/colyseus/blob/7342663d6af8c41b9d6968f83849102cf5cf83ca/packages/transport/ws-transport/src/WebSocketTransport.ts#L259), README and package versions | Transport liveness cleanup is explicit and periodic. A two-second player-facing stale-state threshold is an original ANDOLAN proposal, not a number prescribed by Colyseus. README capacity/“cheat-proof” marketing is not treated as a verified property of either application. |
| [Separate Colyseus JS repository `996061d78d7c08fe959836a068dd6dbdb42f435d`](https://github.com/colyseus/colyseus.js/tree/996061d78d7c08fe959836a068dd6dbdb42f435d), MIT, package 0.16.23 | [Room.ts 69–125](https://github.com/colyseus/colyseus.js/blob/996061d78d7c08fe959836a068dd6dbdb42f435d/src/Room.ts#L69), [Client.ts 125–140](https://github.com/colyseus/colyseus.js/blob/996061d78d7c08fe959836a068dd6dbdb42f435d/src/Client.ts#L125), close-code enum and license | Earlier API also exposes explicit leave/reconnect semantics and room-scoped tokens. This is a separately pinned older package, not a compatible current client/server pairing or an installation recommendation. |

The previously inspected [Sketchbook, OpenRW, OpenLara and DX-Ball examples](REFERENCE_MECHANICS.md) remain useful for transitions, explicit modes and bounded reconstruction evidence. None supplies ANDOLAN's multiplayer authority. REA's actual static Sketchbook trace was partial; it does not establish live networking behavior. The small connection source was more directly audited by reading it and constructing controlled failure cases than by claiming binary recovery.

### Inspection hashes

Local reference clones are outside the product checkout under `/workspace/research`.

| Pinned source file | SHA-256 |
| --- | --- |
| Colyseus monorepo `packages/sdk/src/Room.ts` | `eec5f78457999ae38721969d16ed7750a8aef0f2c6754c1a31834bdf1d4be244` |
| Colyseus monorepo `packages/core/src/Room.ts` | `d3dbf5ce2e0ed83761a3c26924cf48dfbe1c972b75b5501829f756c66e873b9b` |
| Colyseus monorepo `packages/transport/ws-transport/src/WebSocketTransport.ts` | `dc43f0823ebc2fd089c379b485e99191cbd46a9341eb92e0a2c5354158b7a072` |
| Separate Colyseus JS `src/Room.ts` | `ae553ad3a3d8ce24f7d00c9077027a09df05ec5bf65cf9b5da62bbfa71dc5e7c` |

## Round 5 — inspect the revised implementation

The revised connection captures the socket for each attempt and ignores obsolete open/message/close callbacks. Code 4001 pauses the superseded identity. `ROOM_REQUIRED`, `ROOM_NOT_FOUND`, `ROOM_FULL`, `SERVER_FULL` and `INVALID_TOKEN` stop automatic retries. Manual reconnect uses the last accepted room and token; unexpected loss retains bounded retry behavior.

A 500 ms watchdog checks the time since welcome/snapshot. A gap **greater than** 2,000 ms marks the connection stale, so detection normally occurs between two and two-and-a-half seconds; browser timer throttling can delay it further. Both input and command sending require joined, fresh, non-stopped state. A subsequent snapshot clears the stale state; attempted stale commands are rejected rather than replayed later. The implementation does not promise reliable delivery of a command already sent immediately before a connection loss.

Source-review verdict: the two accepted corrections are present. No additional production edits were made by this research reviewer. Root owns the connection/UI implementation; this reviewer owns the isolated connection tests.

## Round 6 — executed connection acceptance

`npx vitest run tests/connection.test.ts` passed **1 file / 9 tests**, at 00:42 UTC on 16 October 2026. The tests use fake timers and a controllable WebSocket, allowing failures that are hard to time reliably over a healthy local socket:

- A displaced tab does not reconnect for 30 simulated seconds; an explicit reconnect sends the accepted room/token and resumes the same player.
- An obsolete socket's asynchronous close and late welcome do not create another socket or replace the active identity.
- At 2.5 simulated seconds without a snapshot, input and commands are blocked. Fresh state restores eligibility for the existing identity, without replaying the blocked command.
- Each of the five permanent join errors stops automatic retry.
- An unexpected transport drop retries and preserves the accepted room/token.

`npx eslint tests/connection.test.ts` and the complete `npm run typecheck` also passed. These controlled transport tests exercise the actual `connectOnline` implementation. They are not a rendered two-tab test, a full campaign run, a real internet fault-injection test or evidence of mobile comfort. Integration/browser evidence belongs in the moderator's [QA report](../QA_REPORT.md).

Tested connection SHA-256: `9f5adcae7d1fe9162bcb3ba2b6d97508a58a9b7b8664a08ec9a93cd6b0c10ec4`.

Test file SHA-256: `6e9b5fe918fc37673d7b20193b1e5fd9702f075fab5bc1eeb74a9e4139da9c3d`.

Final integration reread confirmed these two hashes are unchanged. The visible Reconnect button is wired to `connection.reconnect`, and the status callback hides it when connected or in solo mode. The browser test source now includes persistent split-vote status and a mid-story join recap. Merely finding those assertions is not a passing execution; this document does not claim that the final full browser campaign has completed. Dependency review is recorded separately in [DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md): no production audit findings, one unresolved development advisory represented by three dependent-package entries.

## Smoothness: observed implementation and remaining measurement

The existing renderer already uses frame-rate-independent exponential easing for people and vehicles, short-angle rotation, eased camera following and immediate camera obstruction correction. Server simulation runs nominally at 20 Hz and regular full snapshots at 10 Hz. This is real presentation smoothing, but there is no timestamped snapshot interpolation buffer, client prediction or reconciliation in this implementation.

The easing constants are 18/s for people and 16/s for vehicles. With a fixed target between 100 ms updates, their continuous-form approach velocities fall to `exp(-1.8) ≈ 0.165` and `exp(-1.6) ≈ 0.202` of their initial values. This is a formula-derived observation, not a measured visual jitter score. Camera easing can hide or compound perceived lag; actual WAN and device measurements are needed before choosing a different interpolation or prediction design.

The existing [network benchmark](../../tests/network-benchmark.json) measures one local Node process, 16 synthetic sockets and five seconds: median snapshot interval 100.32 ms, p95 103.31 ms, median snapshot 4492 bytes. It measures neither rendering nor internet latency. The panel chose connection correctness and visible waiting as the two immediate changes. A larger networking framework migration was not required to implement either correction.

## External deployment assessment

Read-only checks using existing configuration produced these results:

| Check | Observed result | What it establishes |
| --- | --- | --- |
| `git ls-remote origin HEAD` | Success; remote HEAD `a9a9746f6119beeefa3437b9fa28934046344228` at time of check | HTTPS Git read works. It does not establish push, API or hosting permissions. |
| Credential binding presence, names only | `GH_TOKEN` present; `GITHUB_TOKEN`, `VERCEL_TOKEN`, `NETLIFY_AUTH_TOKEN`, `FLY_API_TOKEN`, `RENDER_API_KEY` absent | No values were read or printed. An absent provider token does not itself prove that every possible hosting route is unavailable. |
| `gh api repos/occult-kranti/ANDOLAN` | `Forbidden` | The repository API read is unavailable through the current path. The response alone does not distinguish network policy from credential scope. |
| HTTPS request to the conventional repository Pages address | Proxy CONNECT failed with 403 | The check cannot establish whether a site exists or is reachable from a user's browser. No deployed URL is claimed. |
| Hosting/tool inventory reported by moderator | No Sites/public tunnel/deployment connector exposed | The local server and screenshots do not create a public service or ChatGPT embed. |

The complete client/server can run on a Node/container host with HTTPS, WebSocket upgrades and a persistent data volume using the existing [deployment instructions](../DEPLOYMENT.md). A static host can serve solo Story; it cannot run the room service. No provider account, charge, Pages setting, workflow, domain or external deployment was created by this reviewer. A public URL remains an external deployment milestone, distinct from the working cloud development environment and downloadable solo artifact.
