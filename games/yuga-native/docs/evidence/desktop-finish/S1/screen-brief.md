# S1 / W2 — desktop launch-screen brief

Status: **audit and implementation brief only**. No runtime files changed in this checkpoint. Mobile work is deferred. This is a new desktop finish campaign, not a reopening or relabelling of the published UI campaign.

Inspection source: `game/yuga-native-production`, HEAD `0fb96d108b1d886a4ebf84d3b5140abca3905465`, with existing uncommitted launch/theme work preserved. Read `AGENTS.md`, `docs/START_HERE.md`, the existing `.design/brief.md`, current launch/theme code, relevant launch/theme tests and the published I3 native-input review. Design Partner guidance is applied in report-only mode.

## Evidence actually inspected

The following untouched originals were opened directly, rather than inferred from thumbnails or capture receipts:

- [G1 title / day](../../graphics-six/G1/native/01-title-day.png), SHA-256 `2be1303891e9feb231d7903bd3f86c6811a425d7e6c1c281b026046c63ba73a4`.
- [G1 title / night](../../graphics-six/G1/native/02-title-night.png), SHA-256 `f3e33d674f5e3c3b64d15f6dcabc5eeba0547978c6ebf9dfc026896868ff88c1`.
- [Published-package title](../../ui-campaign/I3/role03/native-r1/01-package-title-idle-a.png), SHA-256 `f31235c8b954cfcd5976d70c9cfbaa249b3a61697475d917f7b7ece652ea2542`.
- [Published-package Help](../../ui-campaign/I3/role03/native-r1/03-package-help.png), SHA-256 `035a2c4ddacb1a9beca56a1ba288dc56aebb72a405551db09acffdf6ac0ddd55`.
- [Published-package Settings](../../ui-campaign/I3/role03/native-r1/P01-native-settings-edited.png), SHA-256 `180930e6fc75b87556b78d9fa7e4d1d12939e5944aaab5aa69decc1aae16efc0`.

The [I3 native-input review](../../ui-campaign/I3/role03/REVIEW.md) establishes its own content-6 package navigation, remap/persistence and return-flow scope, including two recorded first-process capture-tool recoveries. It does not accept a new S1 source. G1 originals show a 960×540 framebuffer from the recorded 960×600 native-window run. No new render, live input session, listening test or hardware performance check was performed here.

Current inspected source hashes:

| File, relative to `games/yuga-native/` | SHA-256 |
| --- | --- |
| `scripts/launch_shell.gd` | `3a393f9c18d24dbe96f73fdcb5548fc5c15533c97f1de2c21b2a1e35da621c56` |
| `scripts/hero_ui_theme.gd` | `beb4845d10dd40e01b5896c2677264ec4f046c99b2af933e1116d43bb07b45bd` |

## Visual judgment and invariants

The current title communicates the two available modes honestly, has a clear gold launch action and leaves Rama visible. Noto Serif / Noto Sans, indigo, ivory and beaten gold already provide a useful original identity. Preserve them, native Button semantics, selected mode persistence, explicit loading/error behavior, focus restoration and the single real hero.

The strongest remaining opportunity is composition. At compact size the wordmark, eyebrow, separator, small choice instruction, two selector boxes, repeated selected-mode heading, description, primary button, two feature tiles, separator, three utility tiles and status form one dense stack. The mode choice and utilities all borrow the same box language. The live actor reads as a small full-body exhibit beside that form: approximately 290 pixels tall in the 540-pixel G1 framebuffer. These are hierarchy/framing observations, not evidence of broken navigation or a claim of commercial parity.

No online queue, playable roster catalogue, currency/store, account status, fake achievement count or mobile control belongs in this desktop title. Confluence remains offline lane practice; bow training remains courtyard targets; the duel is a film. Preserve those distinctions in copy.

## The three highest-impact changes

### 1. Compose an identity, a practice decision and a quiet footer

Rebuild the left column as three deliberate zones within the existing protected portrait half. The upper identity is YUGA plus the Rama signature. The middle practice region contains the two available mode selectors, one selected-mode explanation and one gold action. The lower footer carries Rama’s abilities / Watch duel as secondary destinations, then Help / Settings / Quit and a concise offline/status line. Give the decision region more breathing room instead of making every element larger.

Keep a single column rather than introducing competing panels. Remove the ornamental separator above the practice choice; use spacing to distinguish identity. Retain one fine rule before the utility footer. Visually subordinate the selectors to the selected practice and launch action: selection uses the existing gold edge plus pressed state, not a second gold-filled button. The selected title and its two-line explanation should read as one unit. Shorten the persistent instruction to “PRACTICE” or “CHOOSE A PRACTICE”; avoid repeating extra instructions around an already clear primary action.

Wide layout: identity above, decision region below a deliberate gap, secondary/utility footer near the lower edge of the same card. Compact layout: reduce flexible gaps first, retain at least 44-unit action targets and readable body type, then use the existing vertical scroll/follow-focus fallback. The footer must remain part of the card and its focus path; do not create a detached dock that falls outside current geometry invariants. Preserve `card`, `scroll`, `content`, all public Button aliases, stable node names and host signals.

**Owned implementation:** `scripts/launch_shell.gd` build/layout/refresh functions. `tests/launch_shell_cases.gd` only when behavior/geometry coverage requires adjustment; do not weaken its existing enclosure, portrait-clearance or action-height assertions.

**Acceptance:** at 960×600, 1280×720, 1366×768 and 1920×1080 the user can identify selected practice, its offline purpose and the launch action from the initial viewport. All eight current controls remain available; the two selectors change mode without launching, and each destination emits its existing host route once. Loading locks navigation, error permits retry, mode selection persists across film/guide/settings return, and short-window scrolling exposes the last utility with its focus visible. The title contains one gold-filled primary action. Capture both selected modes, primary/utility keyboard focus and error/loading state after native layout settles.

### 2. Give the launcher a stronger type and control hierarchy while protecting the hero

Use the existing serif for the YUGA wordmark and selected practice title; keep readable sans-serif controls and body. Proposed starting sizes are wordmark 72 on wide layouts / 52–56 compact, selected title 28–32 wide / 24–28 compact, body 17, and supporting metadata 14. These are source implementation candidates, to be tuned in actual renders; they are not accepted font measurements. Keep line lengths bounded by the existing approximately 364–438-unit column rather than stretching text across the world.

Treat Rama’s abilities / Watch duel and Help / Settings / Quit as quiet navigation rather than equally weighted dark tiles. Trial native flat Buttons for launcher-only utilities, retaining hover/pressed backing, focus ring, disabled state and minimum hit area. Do not make global utility surfaces transparent: the shared theme’s opaque contrast guarantees also protect modal/HUD contexts. The gold launch button stays full width and clearly heavier than mode selection. Keep the title signature concise, and preserve the live status/error line without replacing it with decorative lore.

Shape the left scrim around text rather than darkening the entire actor. Keep UI bounds before 52% of viewport width, and reserve a portrait region from approximately 56% across to the right edge. The actual head, torso, bow and feet remain visible, with no UI over the face or grip. A more prominent full-body hero is desirable: a candidate approximately 60–68% of framebuffer height would improve face/silhouette read while retaining feet/contact. That requires a matched title-camera adjustment, **not a crop masking known foot/contact problems**. The world, lighting and live actor remain the visual proof; no new poster image is proposed.

**Owned implementation:** launcher-specific metrics/type roles and scrim in `scripts/launch_shell.gd`; additive launcher-only semantic tokens/helpers in `scripts/hero_ui_theme.gd` if needed. Do not alter global `TYPE_HUD`, shared combat surface rules, fonts, shader effects or actor materials.

**Dependency / handoff:** `courtyard.gd::_create_title_camera()` currently owns FOV 34 and the title look-at. Its owner must receive the safe portrait rectangle and compare any camera change in day/night, compact/wide and idle-motion frames. W2 does not edit `courtyard.gd`, the hero, motion or lighting during this checkpoint. If that camera handoff is deferred, report hero prominence as still open rather than claiming it fixed through the scrim alone.

**Acceptance:** actual new day/night originals show a clearly stronger type hierarchy and calmer utility area; selected mode, primary action and focus remain readable over the brightest courtyard and darkest title. No button label clips or requires hidden horizontal scrolling. Face/bow/feet stay unobscured at tested sizes. Shared Settings/Help/guide and combat HUD retain their existing appearance until their own owner approves a change. Check actual rendered text and keyboard focus separately from contrast/resource tests.

### 3. Apply each style role once and preserve private state ownership

The launch helper currently applies the default button style, then immediately applies primary/utility style to most buttons. `_refresh()` also reapplies selected/secondary styles to both selectors on every refresh, constructing fresh per-state StyleBoxes even when selection has not changed. In the shared theme, `create()` builds role styles and `button_variant()` independently builds the same role values as control overrides. These are confirmed duplication seams; eliminating all overrides indiscriminately would break standalone controls and private-style ownership.

Give the launch `_button` factory a semantic role parameter so each newly built control receives its final initial role once. Update selector role only when selection actually changes; still update pressed state and tooltip correctly. Keep shared button role/state construction in the existing theme helper rather than rebuilding fills/borders/type values inside the title. If adding launcher typography/spacing roles, define them once and reference them from both compact/wide branches.

Retain independent StyleBox instances where callers can mutate them: existing tests explicitly verify that changing one theme/button cannot change another, and that role reassignment clears old text/surface overrides. No global mutable StyleBox cache or broad removal of those tests. Keep `button()`, `button_variant()`, `create()` and `build()` compatibility; avoid a shared-theme redesign while other screen/HUD owners are active.

**Owned implementation:** `scripts/launch_shell.gd` factory and selector role update. `scripts/hero_ui_theme.gd` only for an additive, narrowly scoped launcher role/token or a shared helper preserving the public API. Shared-theme edits are serialized with the root and communicated to the other screen owners.

**Acceptance:** no repeated default-then-final styling in the launcher; refreshing unrelated status does not recreate selector styles or change selection/focus. Existing theme contrast, focus inset, disabled-keyboard and private-resource ownership tests pass unchanged. Existing launch/host integration and resize/focus regressions pass. This cleanup supports consistency and maintenance; it is not presented as measured frame-time improvement.

## Ownership and verification checkpoint

W2 requests implementation ownership of `scripts/launch_shell.gd`, narrow additive changes in `scripts/hero_ui_theme.gd`, and only the affected launch/theme test files if necessary. Other workers retain boot/loading, courtyard/scene host integration, world/atlas, combat HUD, hero/motion and render/capture tooling. Preserve their current dirty changes; recheck baseline hashes immediately before the authorized edit window. No commits or heavy engine runs belong to this checkpoint.

After root authorizes the source checkpoint, run focused headless `launch_shell_cases.gd`, `ui_theme_cases.gd`, `ui_font_cases.gd`, `ui_launch_integration_cases.gd` and `ui_resize_navigation_cases.gd` against isolated user data and fresh reports. Broaden only on an actual cross-owner change/failure. Independent W6/native-window review must exercise actual mode selection, guide/settings return, loading/error recovery, keyboard traversal and compact resize from the accepted source.

The current new-render gate is blocked and being repaired by the render owner. Historical G1/I3 images support this design brief; they cannot approve its future implementation. Save new originals and source hashes once the lane works. Until then, report implementation/resource results and unrun rendered checks separately. No Deadlock-level, Mobile Legends-level or hardware performance acceptance is claimed.
