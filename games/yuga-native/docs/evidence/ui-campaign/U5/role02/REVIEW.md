# U5-02 — consolidated native visual states

Product: YUGA native. Reviewer: `ui_06_acceptance`. This role consolidates actual shared-state pixels and component rules; it makes no runtime changes. Status: bounded U5 visual acceptance complete for r1 plus the exact r2 correction overlay. Compact HUD text remains a readability limit.

The original combined R7/UI4 freeze is `/tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native`, manifest SHA-256 `720d124a51d3c31b95424889a1047360720c078cda1480405f4e705442cd5ecb`. The shared theme is `b1d630e9087f939ba6a68a5bbfac6f126064d417393786380c324317ac5d39a6`. Source review started at checkout HEAD `495fae3aad59bfcce22506cc27f9d042741cd4ab`; per-file frozen hashes establish executed identity because the shared checkout continues to advance.

[Component rules](COMPONENT_RULES.md) record the actual type, surface, spacing, semantic action and focus contracts. [Original review](original-review-r1.json) records direct inspection and hashes for all **39 planned plus 15 automatic original images** from `/tmp/yuga-u5-integrated-window-r1`. UI03 owns the raw originals and native-input trace in [integrated-r1](../role03/integrated-r1/). The actual native window is 960×600, the framebuffer is 960×540, and the logical canvas is 1280×720.

The rendered title, training/world pause, settings footer, keyboard capture, guide selection, live/paused/defeated HUD and three terminal outcomes show contained controls and visible focus rings. The controls screen visibly distinguishes disabled Cancel capture from its enabled capture state. Selected mode/ability marks remain distinct from keyboard focus. World and training return actions restore their actual opener. Native Restart restores the healthy HUD after an explicitly staged outcome. Legacy film controls are reviewed as their separate existing interface.

The earlier U4 theme state board remains [historical component evidence](../../U4/role02/REVIEW.md), including hover, pressed, selected, disabled and focused states on bright/dark backgrounds. It is not counted as newly captured U5 images. The U5 integrated run does not hold every transient hover/pressed combination on every scene.

The original run retains three concrete findings:

- **Help entry, original 09:** Back receives focus and scrolls the fresh heading above the viewport. The rejected PNG/JSON are preserved in [rejected-help-r1](rejected-help-r1/). A paired correction is required.
- **Guide feedback, original 04:** checked preferences and focus are visible, but the save notice is below the viewport. The source owner is preparing a bounded feedback-reveal correction; the original does not prove visible confirmation.
- **Staged respawn, original 20:** the hero and notice return to arrival court while the top location remains Temple avenue. This is a held capture-fixture refresh defect; acceptance of the respawn location waits for a corrected helper capture. It is not attributed to ordinary frame-updated gameplay.

Automatic files `auto-loading-2/3/4.png` contain constructing-phase pixels, confirmed by their JSON. Their trigger names are retained; they are not counted as loading-percentage views. All automatic originals show contained phase text and Back focus. The underlying dimmed title in film-loading frame 4 retains an Opening bow training primary label while the foreground correctly identifies the film destination; no wrong destination or input failure was observed.

Compact world labels remain small: 11–12 logical pixels correspond to roughly 8–9 framebuffer pixels in this presentation. Containment and current information are established, but broad readability at all scales is not. Staged authority is explicit and uses actual rules with held simulation; it does not establish a native combat playthrough. These UI findings do not establish hero-art quality, physical-GPU speed, online play, other-platform execution or package qualification.

## Targeted correction review

All **15 planned plus 15 automatic r2 originals** were directly opened; per-image hashes and findings are in [original-review-r2.json](original-review-r2.json). UI03 owns [integrated-r2](../role03/integrated-r2/). Manifest `0f4871dd0b09cca7f240454f33016bbe154567f0840fc15d6e7f164c3871666f` differs from r1 by the explicit [repair overlay](../role03/repair-overlay.json), including three runtime files: courtyard `197a2349…`, guide `ff710c7a…`, and world `1a11e57c…`. The shared theme is unchanged.

The paired originals close fresh/reopened Help-heading clipping (`03`/`05`, with native reading scroll in `04`) and save-feedback visibility (`02`, both toggles plus focused motion and complete saved notice). Corrected explicitly staged respawn `08` and all three outcomes `09–11` now agree with location and atlas; helper `0ad1f073…` records that its normal presentation refresh does not advance army/relay authority. Native siege `12` now truthfully says **2 enemies**, addressing the separately found all-team count ambiguity. Actual training→film→title originals `14`/`15` retain Bow training and matching primary focus, addressing the separately root-found mode-loss defect.

Native night original `07` confirms phase 1.0 before staging and keeps pause focus/panels contained; the distinct background integration analysis is [I1-02](../../I1/role02/REVIEW.md). This review covers 54 original r1 records and 30 targeted r2 records, not 84 unique visual designs. Original failures remain retained. Later I1 runtime motion changes have their own source/testing scope; these images are not silently assigned to those bytes.
