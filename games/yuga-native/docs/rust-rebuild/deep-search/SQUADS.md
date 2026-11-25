# Confluence private matches for two or six people

The same fixed-step Rust battle now hosts a **1v1 duel** or **3v3 teams**. Hanuman and Rama are available to either side, including duplicate picks. The Sun and Moon armies still fight over three lanes. The full-team format requires six connected players. The separate Sangam City package has all fourteen classic heroes in local graphical sparring. [Download Confluence](../../../../yuga-rust/downloads/yuga-rust-confluence.zip?raw=true) · [Download classic sparring](CLASSIC-DISTRIBUTION.md)

## Host a match

Extract the ZIP on the host. Use Node 22.12+ to run `node serve_rooms.mjs --host 0.0.0.0` from the extracted directory. Everyone opens `http://HOST-LAN-IP:8787` in their own browser. Each player selects a hero. The host opens **Private multiplayer**, chooses **3v3 teams** or **1v1 duel**, selects **Create room**, and shares the code. Others choose **Join**. The waiting lobby displays the team, seat and number still needed. The match starts when the last seat fills. Leaving ends that room. Run `node serve_rooms.mjs` to host only on the local machine. [Host implementation](../../../../yuga-rust/tools/serve_rooms.mjs)

## What changes with six seats

- Sun takes seats 0, 2 and 4 in the protocol. Moon takes 1, 3 and 5. Players spawn at separate clear positions. A receiver ID follows a player independently of their hero choice, camera or animation.
- All six heroes can resolve attacks on the same tick. Shields present at its start absorb damage. New protection and healing apply to survivors, including the caster. A ward cannot bring back a player defeated on that tick. Dead heroes return after 60 ticks.
- Each graphical client interpolates its five peers’ rigs separately. Repeated Rama picks retain independent bows and projectiles. Repeated Hanuman picks retain independent casts, team rings and health bars. The local host can use the native executable or the Rust/Wasm worker bundled in the ZIP. [Authority](../../../../yuga-rust/src/battle.rs) · [Fixture](../../../../yuga-rust/tests/team_battle.rs) · [Renderer](../../../../yuga-rust/web/scene.ts)

## Release verification

| Test | Observed result |
| --- | --- |
| Rust authority | All six players were knocked out on tick 630 and returned at tick 690. Two separate complete 18-minute scripted runs settled consistently. The lethal-ward test covers six attackers releasing on the same tick. [Combat integration](../../../../yuga-rust/tests/team_battle.rs) |
| Native versus Wasm | 201 frames, 1,206 seat views, 6,030 opposing/allied views and 3,222,630 numeric comparisons. The largest difference was approximately 0.00000006 radians in an army unit’s facing direction. Ten malformed transcripts and ten invalid direct calls were checked. [Differential receipt](squad-authority-parity.json) |
| Extracted room server | Six playing clients, a separate playing duel and a ninth attempted join. All six seats moved and cast. The largest observed six-seat client snapshot was 39,872 bytes. Both rooms and workers were released. A separate run filled 16 native duels with 32 clients and tested restart. [Extracted host](squad-host-portable.json) · [Native stress](squad-release-duel-stress.json) |
| Graphical match | Two Chromium clients and four other real WebSocket clients joined a 3v3 room. Both browsers displayed five other players. Moon saw the designated Hanuman’s Mountain Pulse while his independently moved duplicate stayed idle. The browsers and remaining sockets left cleanly. [Seven checks](squad-team-browser.json) · [Gameplay capture](squad-team-browser.png) |

The same final ZIP also passed 29 Hanuman drill checks, 18 solo lane checks and nine original two-browser duel checks. Two earlier duel browser attempts disconnected before movement was acknowledged. The unchanged package passed the complete repeat. The cause of the earlier disconnects remains unconfirmed. [Drill](squad-release-drill.json) · [Solo match](squad-release-solo.json) · [Duel](squad-release-duel-browser.json)

These runs used a loopback host and software-rendered Chromium. Public matchmaking, reconnection into an existing seat, bot substitution and physical GPU or WAN frame-time qualification remain open. The prior two-seat release and its exact tests are archived at an immutable commit. [Earlier package](https://raw.githubusercontent.com/occult-kranti/ANDOLAN/f4ce736955011d5397401548f32c85f49d2c5c41/games/yuga-rust/downloads/yuga-rust-confluence.zip) · [Complete roadmap](FULL-PORT.md)
