# Round 3 · implementation and behavioral checks

The current hero HUD now has read-only cooldown/ammunition/cast strips, a distinct Dawn Volley surface, and three pending/launched lane marks during the committed ultimate. It consumes the existing runtime combat event and current kit snapshot. It retains current label nodes, remaps, availability and compact geometry. The guide shows JSON-derived damage/protection/movement output and per-ability use/counter/follow-up advice.

The new suite exercises actual volley preparation, each paced release, UI-only time, pause/resume, recovery, interruption, reset, defeat and read-only guide behavior. It confirms meter containment at 100/150/200% logical scale. Initial result: 23/23. Ten existing suites passed 195/195: HUD geometry/context/reload/action/compact/glyph/guide-scale/screens/expiry/detach. Exact commands and per-suite reports are in `r3-evidence/summary.json` and `r3-evidence/`.

These tests prove state and layout only. The initial draw_rect warning and the later empty-magazine finding were corrected in Round 4. R3 reports retain their source hashes; [Round 4](ROUND4.md) and [its receipt](round4-receipt.json) own the final corrected source. No imported assets, rules, damage, cooldowns or common theme files changed.
