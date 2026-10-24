# Prior R3 evidence: capture valid, inspector superseded

The actual runtime trace passed its 92 capture checks. W1 independently found five gaps in the original inspector, so its `accepted: true` reports are not current acceptance. Exact original tool bytes, output bytes and command/source hashes are retained here for review. The archived implementation files are byte witnesses, not relocated runnable tools; their relative paths belonged to the original tool directory.

Use the current [`tools/reuse-event-sync`](../../../../../../tools/reuse-event-sync/README.md) and [accepted R4 run](../accepted-r4/run.json). Its repair rejects shifted or missing frames, invalid source cadence, mismatched capture clocks and malformed presentation state; the original W1 11-control probe passes against the repaired inspector. R4 is a fresh full run with distinct wall timestamps, hashes and 43 checker cases. Nothing here is a rendered or listening review.
