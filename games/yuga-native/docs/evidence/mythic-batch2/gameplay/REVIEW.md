# MYTH08 gameplay adapter evidence

This archive covers the original native troop-invocation adapter. It separates data/behavior acceptance from the root-owned moving-render, audio, UI, native-contract and release gates. No result here establishes fourteen production hero models, a hero health system, native online play, reference-game visual parity or consumer-GPU performance.

## Review rounds

1. **Source and geometry contract.** Keep the creative codex presentation-only. Define a separate versioned native rules file with exact disk, sector, swept-projectile, zone and atomic-pair geometry. Warnings consume that geometry. The two sectors use cosine thresholds 0.55 and 0.25, not decorative codex widths. One shared 12-second cooldown spans every invocation; selection cannot reset it.
2. **Actual receivers and counterexamples.** Implement real troop healing, shield absorption/expiry, slowed movement, bounded temporary units and existing damage/reward integration. The owner suite exercises all fourteen real payloads, finite/typed inputs, duplicate/deep/oversized JSON, geometry boundaries, the last partial projectile step, expiry, caps, pause/cancel and reset. Independent probes identified and repaired cleanup when replacing the army, an overflowing finite aim vector and reset during a defeat callback. Those initial/fixed logs are retained below.
3. **Regression and integration.** Re-run existing army, siege and relay-control tests on frozen source, including the existing long simulated soaks. Independent actual-world integration is maintained separately by its owner and includes 72 complete combined damage/slow receipts and repeated world disposal/reset. The root-owned relay layout suite needed its expected pause-action count updated from eleven to twelve for the invocation action; this was not an army or supply-rule regression.

## Owner and retained regression reports

| Report | Scope |
| --- | --- |
| [ultimate-cases.json](ultimate-cases.json), [actual log](ultimate-cases.log.txt) | 77 owner checks; fourteen real payloads, parser/geometry/receiver/cooldown/reset cases |
| [lane-army-regression.json](lane-army-regression.json), [actual log](lane-army-regression.log.txt) | 21 existing checks, including 20 simulated minutes |
| [siege-army-regression.json](siege-army-regression.json), [actual log](siege-army-regression.log.txt) | 31 existing checks, including 20 simulated minutes |
| [relay-control-regression.json](relay-control-regression.json), [actual log](relay-control-regression.log.txt) | 42 existing rule checks, including an hour of repeated simulated control steps |

These are fixed-clock, headless tests. Their simulated durations are not wall-clock play sessions or rendering-performance measurements. Source hashes in each report identify the exact tested files. The evidence manifest hashes every archived file and separately pins the final implementation; it excludes itself to avoid a hash cycle.

## Independent defects retained

- [Original reset probe log](reentrant-reset-probe.log.txt) shows a reset attempting to free a signal emitter and an old receipt leaking into a new epoch. [Repeated probe](reentrant-reset-probe-r2.log.txt) shows thirty fresh units and cancellation/reset events without a stale impact. The repair invalidates the cast immediately, defers freeing locked emitters and rechecks epoch/cast identity after applying a receiver. The epoch may increase twice during deferred reset; consumers must accept a greater epoch rather than assume exactly one increment.
- [Original large-direction probe](huge-forward-probe.log.txt) shows that a finite vector could overflow its squared magnitude and normalize to zero. [Repeated probe](huge-forward-probe-r2.log.txt) rejects it before cooldown or cast mutation.
- [Reconfigure probe](reconfigure-probe.log.txt) verifies that a successful move to another live army clears old effects and disconnects old callbacks. Failed reconfiguration remains atomic.

The three original probe scripts are archived as `.gd.txt` files, unchanged. Their absolute scratch/workspace paths are provenance, not portable launcher commands. The initial probe logs preserve observed failures, but this archive does not claim to contain a full snapshot of the failed pre-repair runtime. The final owner suite independently includes the repaired behavior and pins its actual source.

## Remaining gates

The world must suspend the army, session and presentation together during pause/focus/overview and cancel active effects before a teleport. UI must call these **invocations** through the current Rama avatar and read cooldown from the session. Hanuman projects a landing payload; it does not teleport the avatar. Temporary sentinels use current troop models and cannot deal core damage or award expiry gold.

Final effects/audio/UI integration, moving visuals, exact packaged execution, release verification and native-contract revision checks are recorded by their respective owners. Read [ULTIMATE_PRACTICE.md](../../../ULTIMATE_PRACTICE.md) for the complete gameplay/API boundary.
