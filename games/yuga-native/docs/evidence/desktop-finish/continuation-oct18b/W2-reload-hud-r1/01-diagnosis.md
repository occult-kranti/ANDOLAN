# Reload readiness mismatch

Actual mounted runtime rejects every kit input during player.reload_remaining>0. The old HUD68e3 only marks Kodanda RELOADING; zero-cooldown abilities still say READY and use ready glyph/surface states. The focused real-world reproduction releases Piercing Dawn, fires one actual bow arrow, calls the real start_reload and submits Dawn Volley through its actual Q/X input path. The unchanged HUD fails the three100/200/100 readiness observations, while real input rejection, cooldown preservation, layout and actual completion all pass14/17. This is a semantic availability defect, not a measured long-label clipping failure.

The first fixture incorrectly used Guardian Circle through the Q/X buffer; its two harness failures and missing native-exit capture remain explicit in baseline-r1. The valid successor uses Dawn Volley and captures the native exit. No fabricated ammo, reload clock, cooldown, UI text, or action percentage establishes the counterexample.
