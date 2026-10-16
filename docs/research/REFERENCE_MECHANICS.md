# What real reimplementations teach this prototype

This extends the initial REA/Sketchbook investigation with **actual selected source and oracle-document inspection**. It does not import a legacy engine or copyrighted game assets. “Observed source” means text inspected, not a game played. Hashes and exact URLs are in [the library source manifest](../library/source-manifest.json).

## 1. DX-Ball: a genuine REA-assisted reconstruction with bounded claims

**Pinned project:** [`N0zoM1z0/dx-ball@a55dca27…`](https://github.com/N0zoM1z0/dx-ball/tree/a55dca27ec0a07018c1b2c95ae2be027f7d8c3c4), the revision linked by REA's own showcase. This is a separate reconstruction project using REA, not a fork of REA and not a completed browser game.

**Actually inspected:** README, `docs/PROGRESS.md`, `docs/ORACLES.md`, `docs/GAMEPLAY_OWNER.md`, `config/source-owners.toml`, and the `dxball_screen_pan` function/caller in [`src/gameplay.c:41–56`](https://github.com/N0zoM1z0/dx-ball/blob/a55dca27ec0a07018c1b2c95ae2be027f7d8c3c4/src/gameplay.c#L41).

The C function explicitly converts a screen coordinate using multiply/subtract/scale and integer conversion. The gameplay-owner document explains why the first decompiler view was incomplete: it omitted an argument and the floating-point expression, so instruction/caller evidence was needed. This is a concrete code result, beyond a promotional demo description.

The progress ledger reports 55 source-present functions, 55 with scoped semantic acceptance, 33 byte-exact functions and 473 unclassified candidates. It explicitly says the playable whole-game build is pending. The oracle matrix distinguishes original-code semantic comparisons, compiler-byte replay, decoded pixels and actual display/backend behavior. Those upstream comparisons were **not rerun**: they need an authorized original executable and the specified native toolchain, neither acquired for this task.

**ANDOLAN lesson:** State exactly what a test establishes. Our content tests can establish branch consistency; they cannot establish whether driving feels good. A two-client vote test can establish one accepted outcome; it cannot establish a fair real-world political process. Keep source, state, rendering and experience evidence separate.

**Acceptance proposal:** For each game subsystem, retain one tested contract and explicit excluded cases. For the current choice system, separate “history contains this choice,” “the correct conditional dialogue renders,” and “a novice understands the consequence.” Only the first two can currently be automated.

## 2. OpenRW: seat occupancy is an invariant, animation is a different concern

**Pinned project:** [`rwengine/openrw@5c5f266…`](https://github.com/rwengine/openrw/tree/5c5f266b71aa55aeec8cb4d823f19e7c4348f3bd). GPLv3-or-later GTA III program; legitimate original game data required upstream. No code adopted.

**Actually inspected:** [`rwengine/src/objects/CharacterObject.cpp:482–518`](https://github.com/rwengine/openrw/blob/5c5f266b71aa55aeec8cb4d823f19e7c4348f3bd/rwengine/src/objects/CharacterObject.cpp#L482). `enterVehicle` rejects an occupied seat and updates vehicle/character references. `isEnteringOrExitingVehicle` checks animation identity separately. `isStopped` delegates to vehicle motion when seated.

**ANDOLAN lesson:** Separate logical ownership, physical motion and presentation state. Our original server owns seat transitions; visuals may animate them, but an animation cannot grant a second driver. This source is a useful architecture comparison, not proof of network-safe authority or code licensed for unrestricted copying.

**Acceptance proposal:** Competing seat claims give at most one driver. A rejected claim leaves both reference fields consistent. Exit/disconnect clears control input and ownership independently of animation completion. The existing original simulation is the test subject; OpenRW runtime was not executed.

## 3. OpenLara: explicit modes and a defined fallback

**Pinned project:** [`XProger/OpenLara@3b268ca…`](https://github.com/XProger/OpenLara/tree/3b268ca4bf986c380f44a26ffd9218bf6d376249). BSD-2-Clause engine; original-game assets are separate. No code adopted.

**Actually inspected:** [`src/character.h:13–20`](https://github.com/XProger/OpenLara/blob/3b268ca4bf986c380f44a26ffd9218bf6d376249/src/character.h#L13) defines ground/air/slide/hang/water modes. [`getNextState` and `updateState`, lines 149–181](https://github.com/XProger/OpenLara/blob/3b268ca4bf986c380f44a26ffd9218bf6d376249/src/character.h#L149) select a mode-specific state and fall back if the animation state cannot be set.

**ANDOLAN lesson:** A requested visual transition needs a safe fallback; missing polish must not break gameplay authority. The current original prototype can use atomic logical entry with simple presentation, then add authored animation without changing seat semantics.

**Acceptance proposal:** Missing/disabled presentation animation preserves control and authoritative state. Reduced-motion presentation reaches the same gameplay outcome. More movement modes remain backlog; this source reading is not a reason to add swimming/climbing before the existing loop is reliable.

## 4. Sketchbook: the most immediately useful permissive browser reference

The previous [REA run](REA_RUNBOOK.md) actually parsed seven TypeScript controller files at [`62f4b798…`](https://github.com/swift502/Sketchbook/tree/62f4b7986fd1ce1e4f91daba89ef032c20a6ce55). Its exact statistics and partial semantic trace are saved in `evidence/`. The trace did **not** solve ownership across players; direct reading clarified the local physics/parenting/input boundaries. The source is MIT and archived; its old dependency/animation assumptions were not carried into the game.

**Adoption:** original state and collision code, original procedural geometry, retained provenance. No controller source or asset directory imported. [VEHICLE_TRANSITION_SPEC.md](VEHICLE_TRANSITION_SPEC.md) remains the original contract; current implementation constants may differ from its explicitly labelled initial proposals.

## REA's useful place in the workflow

Use readable source first. Run a bounded REA inventory/trace when it creates useful evidence, repeatable identities or a comparison between versions. Use native providers only for an authorized binary question that source inspection cannot answer. Then implement an original contract or deliberately licensed code adaptation and test its actual behavior.

A fork count, GitHub star count or repository title does not establish that a clone is playable, maintainable or legally reusable. This pass found an inspectable REA-assisted reconstruction and inspected two real reimplementation sources. It does not claim to have audited every fork, ported GTA, obtained proprietary data, or reproduced another project's oracle results.

## Decision for this development round

Do not replace the existing PlayCanvas/browser implementation with OpenRW, OpenLara or a bundle of unrelated engines. Apply the verified boundary lessons to the current simulation and keep source research separate from product runtime dependencies. The three user-facing changes selected by this panel are decision trade-offs, visible persistent consequences and understandable crew voting; see [the design library](../library/README.md).
