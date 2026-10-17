# Triad corrected Linux package: bounded actual-input review

Reviewed 17 October 2026. **The inspected local Linux package passes the bounded input flow below**, including forward entry after Visit Lotus, capture and capped arrow resupply, pause, overview, ordinary reset, siege entry and title return. This accepts those observed flows in this package; it does not accept production art, all gameplay or Windows execution.

## Package identity and checks

The extracted local package was built from clean native source commit `f87de49531b3b456198bf3cd4ebf0b088bfa9094` on `game/yuga-native-production`. `input-review.json` records actual XTest keyboard/mouse events and screenshot/engine/PCK hashes. The native manifests retain package/export identity; `export-capture-verification.json` retains the earlier capture comparisons. The packager's `not_executed_by_packager` field describes the packaging stage; the subsequent actual Linux execution is evidenced by this input record and screenshots.

At archival, all sixteen PNG hashes were independently verified. The extracted Linux executable/PCK and Linux ZIP were hashed against input and package records; the export manifest bytes/hash and the three manifest commit associations matched. The existing traversal, siege and Triad capture validators were independently rerun with `decode=True` against this exported manifest: all three passed, including full MP4 decode, retained-media hashes and current/captured/exported source associations. No new rendering was performed for this archive.

- Linux ZIP SHA256: `dffcf53fa4c47402ea1b36f736f386446afd4c07fb23b5ce1c6872e1ba216209`.
- Extracted engine SHA256: `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`.
- Extracted PCK SHA256: `c10a1ad2625c83564bf905603e01eb26ea4ef86702645afad6de0efbe9bb43c6`.

Raw inputs remain at `/workspace/scratch/yuga-relays/window-r2`; package files remain at `/workspace/scratch/yuga-relays/packages-r2`. Binaries/ZIPs are identified here rather than duplicated. `game-output.txt` and `xvfb-output.txt` are unchanged copies of the raw logs. Godot reports 4.6.3 and Forward+/llvmpipe. No Godot ERROR/WARNING/SCRIPT ERROR entries were found; Xvfb records its separate socket-directory ownership warning. Exit `-15` is recorded after runner cleanup, not as a gameplay crash.

## Screenshots actually inspected

All sixteen PNGs were opened independently. The input sequence and visible results are:

| Images | Observation and bounded conclusion |
| --- | --- |
| `01-title.png`, `02-world.png` | The title opens and Explore Confluence is clicked. **Image02 is an early transitional first world render:** initial HUD layout, 0% energy and close geometry are visible. It is retained as transition evidence and excluded from steady-world acceptance. Subsequent images show the settled HUD/camera and 100% energy. |
| `03-pause.png`, `04-lotus-focused.png` | Escape opens the practice menu. Three Tabs place a visible focus outline on Visit Lotus relay; Return activates it. |
| `05-lotus-approach.png`, `06-forward-entry.png` | The pad/station is now ahead with the 7m-to-centre prompt. W moves into the marked zone, showing 65% Sun capture. This actual input sequence addresses the reversed approach found in the [rejected prior package](../triad-window-r1-rejected/REVIEW.md); it does not rely on the staged-camera render alone. |
| `07-after-fire.png`, `08-captured.png` | The mouse-button hold reduces arrows 12→10 while Lotus reaches 92%. Later Lotus shows Sun ownership and the raised Sun symbol; arrows reach 12/12 without intervening reload input. This supports actual capped resupply in the held zone. The screenshots do not count exact supply ticks or demonstrate troop healing. |
| `09-paused.png`, `10-paused-later.png` | Both show the same visible Sun ownership, 12/12 arrows, hero/nearby scene and pause menu, separated by 23.979 wall seconds in the input log. They support stable visible paused state; they are not byte-identical and are not a complete internal simulation trace. |
| `11-help.png` | F2 opens Keyboard controls, with the corrected “F5 restart round” footer. Remapping/persistence was not changed or tested in this sequence. |
| `12-overview.png` | After leaving Help/pause, F1 presents the overhead map. The HUD now says Lotus Contested after enemy arrival. This verifies the visible overview and contest state, not close readability of station contested flags. |
| `13-reset.png` | F1 returns and F5 restores Surya arrival court, Wave 1, zero gold, 12/12 arrows, open relays and 100/100 cores. |
| `14-siege-drill.png`, `15-siege-paused.png` | Keyboard menu navigation enters the drill. Cannons/chariots are visible, the HUD identifies siege counts, and the relay strip explicitly says relays are inactive during the drill. Escape opens the drill pause menu. This still review does not establish continuous warning/impact readability. |
| `16-title-return.png` | Clicking Return to courtyard reaches the title menu again. |

The source-pinned [Triad render archive](../triad-relay-render-r2/TRIAD-RENDER-REVIEW.md) remains separate simulation/art evidence. The rejected previous package archive is preserved rather than overwritten.

## Limits and remaining work

This is a local extracted Linux package test; it does not prove a later public download is the same artifact. No Windows execution, human study, audio audition, full video playback, physical-GPU performance or online match is claimed. Input wall-clock durations are not simulation-time or performance measurements. Hero health/death remains unimplemented.

The early scene transition is visibly unfinished and should not be presented as a polished loading flow. Neutral pad contrast, weak site-specific silhouettes, primitive surfaces and repeating architecture remain art limits. Pause/help overlays cover parts of the scene/HUD as shown; small-window overlap and broader accessibility need dedicated review. Overlapping combat warnings, continuous character/vehicle contact and Moon/contested station art are not accepted by these screenshots. There is no AAA/commercial-game visual-parity claim.
