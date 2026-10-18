# U3-06 independent UI review

Outcome: 36/36 independent headless checks pass on unchanged source, with zero engine errors. Eighteen isolated 2D guide originals were captured through 30 actual XTest events and all eighteen were inspected. This accepts the tested native modal behavior and the bounded guide views. Current U3 world/outcome/paused-menu pixels remain with the serialized integrated capture work.

Source commit: `bc1a3dceaddc11f5c0745e73ad1f25f2ca77a0fb` on `game/yuga-native-production`, with the explicitly pinned working changes below. Review date: 18 October 2026.

## Counterexamples and corrections

- Retained first run: 13/21 checks passed, eight failed, source unchanged. Four non-Kodanda pages overflowed at 960×540 with no keyboard route to their final lines. Hidden and disabled guide owners still consumed Escape. Closing courtyard guide/help after `Window.focus_exited` resumed training. That run also exposed detached-HUD `get_tree().paused` script errors.
- The guide owner added PageUp/PageDown/Home/End, effective visibility/disabled-owner guards, and a detached-HUD guard. The pause owner changed training-origin guide/help return ownership to pause after focus loss. Independent rerun verifies these behaviors; application fixes belong to their owners.
- Independent inspection of U2 `03-world-pause.png` confirmed the first-open scroll clipped the heading and mode eyebrow. The U3 pause owner corrected initial reveal. The final independent native test verifies the complete heading and terminal summary/focused action rectangles at 960×540. Later U3 integrated pixels must still verify that correction visually.
- The final suite expands the retained baseline with 1280×720 guide checks, End/Home reachability, one deliberately long explanation, and ordinary/terminal pause header containment. The count increase does not erase the rejected run.

## Executed checks

```sh
env XDG_DATA_HOME=/tmp/yuga-u3-independent-modal-r2/user OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 0,1 timeout 120s godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/ui_independent_modal_cases.gd -- --report=/tmp/yuga-u3-independent-modal-r2/report.json

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LP_NUM_THREADS=1 taskset -c 0 python3 games/yuga-native/tests/ui_independent_guide_capture.py --output /tmp/yuga-u3-independent-guide-960-r1 --display 184 --width 960 --height 540

env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LP_NUM_THREADS=1 taskset -c 0 python3 games/yuga-native/tests/ui_independent_guide_capture.py --output /tmp/yuga-u3-independent-guide-1280-r1 --display 185 --width 1280 --height 720
```

All commands ran from `/workspace/ANDOLAN` and exited zero. The headless process used an isolated settings directory and existing imported resources after the source-matched cache synchronization receipt at `docs/evidence/visual-rounds/round2/canonical-import-sync.json`. No import was run here. The two Compatibility/Xvfb captures used isolated settings and only copied production guide/theme/bindings/fonts/rules, with zero GLBs. The existing observer's `integrated` option starts the tiny 2D fixture; it does not mean integrated gameplay acceptance.

The headless run exercises real viewport key dispatch and an emitted window focus-loss signal, actual courtyard/world modal ownership, overview suspension, terminal outcomes through an army tick, logical bounds, and read-only authority snapshots. It does not establish OS focus-loss behavior. `accepted-r2/receipt.json` records the exact command, counts, source identity and report/log hashes.

## Original pixels reviewed

| Evidence | Results and limits |
| --- | --- |
| `guide-960/` | Nine originals, fifteen XTest events, all inspected. Mouse selection, Down/Return traversal and PageDown/Home expose every detail page without footer or focus-border clipping. Initial focus scrolls the left list enough to hide its small Bow group label; the overall Bow + four abilities heading remains visible. Carry this minor issue into U4. |
| `guide-1280/` | Nine originals, fifteen XTest events, all inspected. Full Bow/Four abilities grouping and every detail page fit; PageDown reveals the context and disabled effects rows. |
| `u2-originals-review.json` | Five existing source-pinned U2 originals inspected: construction, title, world HUD, first pause, return focus. First pause clipping is retained as an observed defect. Other controls fit; auxiliary world text is small at the actual 960×540 framebuffer. These images do not accept later U3 sources. |

The standalone guide intentionally has no connected effects receiver, so its toggles visibly say unavailable. Enabled preferences, integrated U3 map/outcome pixels, arbitrary narrow windows, 2× scale, packaged builds, actual GPU performance and online behavior are outside this result. No commercial visual-parity or complete campaign claim follows from these checks.

## Source identity for the final headless run

| File | SHA-256 |
| --- | --- |
| `assets/design/rama-ability-kit.json` | `4d7a6ddb3873ff1c09470bf24dd6a65b3da3ff853388d29884e575c52ce65eb9` |
| `project.godot` | `976c5fe71bb7a735013b02287701b95fc3c42452e8876675c0250b49c8a96c95` |
| `scripts/confluence_world.gd` | `827b2c34cac135f13e53a0a82190c5a5631f41c5f30a05c5b11bcb69101d7208` |
| `scripts/controls_overlay.gd` | `3ee995c889c6dbd658d4d3dceba649970a61f5cacf848676c7f1b23847a8ceb9` |
| `scripts/courtyard.gd` | `9cd53e74c9978c09a8018da9ee1272940e5fc71f0e5ef8c495c4e872484bf959` |
| `scripts/hero_ui_theme.gd` | `562a6658f7a64acb11ba183904ef8e62814d913825f98f678e4a9c3eef2b883c` |
| `scripts/input_bindings.gd` | `592be5a9950f171005f27740daaeb0a756abfe3fd18368a8a6e80c4af6e3b243` |
| `scripts/rama_hero_hud.gd` | `dbd71a1eaf5b2a2601a936a5f559fe2ddc94c2c9f40c33d1e3fb099f096b6184` |
| `scripts/rama_hero_panel.gd` | `60d1cd7d90a23309839a5a2f87647b1480fdd56b2a7d7049ea756d75c79adf10` |
| `tests/ui_independent_modal_cases.gd` | `f242543ce9aa2f862bf3c6a4d511f783a5b3e6890c0f3722cc6b1e0cdcc491ad` |

Capture receipts pin guide `60d1cd7d90a23309839a5a2f87647b1480fdd56b2a7d7049ea756d75c79adf10` in both runs; `guide-source/` retains the relevant copied source and `visual-review.json` pins every before/after PageDown PNG pair. Original failures and exact source copies remain in `rejected-r1/`.

## Bounded U4 recommendations

| Role | Next independent question |
| --- | --- |
| U4-01 navigation | Resize a first-open pause and a deeply scrolled pause; retain full headings, focused controls and exact opener restoration after guide/help interruption. |
| U4-02 shared visual states | Inspect actual selected/focus/disabled/hover/pressed states over bright/dark surfaces; check contrast and scroll-edge borders, including the compact Bow group label. |
| U4-03 transitions | Cancel/error/retry with a child modal open and focus loss; verify one owner, no hidden Escape consumer and preserved simulation state. |
| U4-04 HUD/map/outcomes | Challenge long relay labels, simultaneous contested states, zero/max cores and held supply clocks during overview; distinguish layout from actual rendered readability. |
| U4-05 guide/controls | Exercise enabled effects preferences, invalid save/reset paths, rebind groups and repeated capture cancellation; verify keyboard scrolling after real resize. |
| U4-06 acceptance | Independently replay other owners' counterexamples on their final hashes, including 2× UI scaling and exact compact-window input; keep rejected receipts. |

Changed owned files: `tests/ui_independent_modal_cases.gd`, `tests/ui_independent_guide_board.gd`, `tests/ui_independent_guide_capture.py`, and this role's evidence directory. No shared campaign ledger, commit or publication was changed. Next owner: root for U3 checkpoint; this reviewer for assigned U4-02 and U4-06.
