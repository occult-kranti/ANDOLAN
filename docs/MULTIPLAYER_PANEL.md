# City Jobs beta review

This review follows the user's request to shift the published beta toward online city play, add sound and improve the world. It is a new release workstream after the six design rounds in `PANEL_LEDGER.md`. Independent agents supplied systems, job/content, world, audio, reference and QA perspectives. These are source and automated reviews, not human player research.

## Baseline and release goal

Baseline `bb808c1` records the verified public solo preview. Its room server already supported real shared movement, seats, choices and persistence, but the main activity was a fixed story. Pages served the standalone client without a public multiplayer backend. The next beta retains the optional campaign and makes repeatable City Jobs the shared activity.

The accepted release scope is five original jobs, separate Story/City state, shared room rewards and district contributions, a task-focused lobby/job board, original procedural audio, clearer dusk scenery and remote visual interpolation. It does not promise copied GTA assets, a new large district, combat, an account economy or public server capacity.

## Pass 1 — diagnose and implement

| Finding and evidence | Decision and owner | Required proof |
| --- | --- | --- |
| Campaign arrivals are global room narrative state; incidental free-roam movement could advance it. | Systems: independent gameplay mode and checkpoint identity, with explicit legacy Story migration. | Story isolation, room mismatch and old-save tests. |
| Existing seats and collision can support cooperation but no repeatable work loop exists. | Content/systems: five ordered jobs with vehicle-bound cargo, dynamic car recovery, a timed circuit and shared rewards. | Real crew handoff, rejected remote completion, single payout, restart recovery. |
| Static client cannot host live rooms; the old lobby only failed after connecting. | Root: explicit server address, labelled solo practice, secure endpoint validation and token namespaces. Hosting owner: concrete Render/Docker configuration. | Static-site no-server behavior, cross-host identity isolation, actual server tests. |
| Audio is only a quiet engine/rain layer. | Audio/root: layered engines/road/footsteps, job and crew cues, opt-in music, persistent volume and explicit activation. | Native output, attenuation, mute/hidden lifecycle and bounded resources. |
| Low-quality screenshot has flat facades, similar player/car values and washed sky. | World: original facade/workshop detail, dusk palette, legible jackets, sloped vehicle cabin, contribution details. | New low/high screenshots, functional scene and quality settings. |
| Remote rendering chases the latest 10 Hz snapshots. Pinned reference probes expose library edge cases. | Reference/world: a small original remote pose buffer; preserve local response and server authority. | Angle wrap, stale samples, seat/teleport snap, reset and independent integration review. |

## Pass 2 — challenge the changed implementation

| Concrete finding | Correction | Evidence |
| --- | --- | --- |
| Corrupted saves could remove a circuit deadline, regress instance IDs, misclassify gameplay or restore impossible cargo. | Systems now reject inconsistent schema-two state and preserve valid multi-load/legacy saves. | Independent six-probe recheck rejects corrupt saves; valid cargo restores; regression tests in `contracts.test.ts`. |
| Job cancellation stayed disabled while an open panel crossed the orphan recovery deadline. | Root recalculates recovery eligibility on every snapshot. | Independent content reviewer accepted the updated source; browser gate follows. |
| Wrong-vehicle drivers and occupied-seat passengers were offered impossible loading/takeover actions, hiding touch exit. | Root provides exit/required-vehicle guidance and only offers takeover when the driver seat is empty. | Source review and upcoming vehicle interactions. |
| A moving-vehicle error said “before getting out” during loading. | Root uses action-neutral wording and explicit cargo/driver/recovery explanations. | Reviewed against authoritative result codes. |
| Disconnected remote avatars remained visible. | World hides disconnected on-foot models while retaining actual seat state. | Source, typecheck and lint. |
| A persistent read-only analysis of audio state alone cannot prove synthesized output. | Audio adds a post-master analyser exposed only through development diagnostics. | Native browser RMS/volume check; no microphone or recording permission. |

## Pass 3 — integration and release

The frozen City Jobs baseline passed all ten browser checks in 491.765 seconds: the original seven Story cases plus practice/audio/save isolation, mobile jobs and a real two-client job traversal. No fake players, teleports or reconstructed jobs may be represented as physical multiplayer completion. Simulated corruption and completed-state fixtures remain explicitly labelled.

The baseline results are in `evidence/multiplayer-beta-browser-results.json`. The user then requested the additional control and City Reform pass before publication; its review and final results are in `CITY_REFORM_PANEL.md` and `CITY_REFORM_QA.md`. Passing local/CI multiplayer checks does not establish an operated public backend. The GitHub Pages build can offer City practice and the campaign; real internet rooms require the persistent server in `MULTIPLAYER_HOSTING.md`.
