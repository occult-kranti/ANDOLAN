# Source-bound open-game reuse study

The [narrative](../../../research/OPEN_GAME_CODE_REUSE.md) and [machine-readable ledger](../../../research/open-game-code-reuse.json) audit five specific public source repositories: official Source SDK2013, ioquake3, OpenMW, OpenRA and the official Godot TPS demo. Classification, code license, game-data terms, integration cost and study/adoption status are separate fields.

`repository-pins.json` records retrieved heads and nontruncated tree hashes. `source-retrievals.json` records 30 successful source/license/config downloads and one retained wrong-path404, with immutable URLs, file hashes, selected line ranges and exact section hashes. Raw source remains in `/workspace/scratch/open-game-code-reuse-r1/`. Fetched-only and symbol-search-only records are explicit; no whole-engine audit is claimed. The copied license texts retain upstream terms.

The [module-check](module-check/NOTICE.md) is a separate GPLv3 research fixture, not native game code. It directly compiles the unchanged OpenMW pool header with C++20, warnings as errors, AddressSanitizer and UndefinedBehaviorSanitizer. The accepted repeat passes **9/9** cases, exits zero and has empty compiler/sanitizer stderr. Quality QA also independently repeated the frozen fixture successfully and owns that separate receipt. No full game/engine, installer, asset converter or commercial client was run.

The module exposes useful limits: objects retain payload, capacity grows with concurrent borrows and the owner must outlive borrowed handles. Reuse is demonstrated for a fixed-concurrency workload, not as a universal performance or memory guarantee. Current YUGA bounded pools should retain their reset/capacity/generation contracts.

`source-validation.json` checks 120 local provenance, section-hash and adoption-scope conditions. This validates the audit's source references, not runtime game behavior, asset rights beyond the inspected terms, finished graphics, human feel or online play. Root/performance owns the separate official MikkTSpace adoption and its acceptance evidence; this audit imports none of the five game codebases or their artwork into the runtime.
