# I3-01 — independent packaged navigation review

Accept the observed Linux launch, film return, overview hold/resume and relaunch endpoints with the capture-recovery limitation below. This is a bounded packaged navigation result. It does not establish uninterrupted automation, instantaneous layout stability, completed character art, hardware performance or Windows execution. No runtime source was changed by this review.

The reviewed archive is `package-r3/yuga-native-linux-x86_64.zip`, SHA256 `56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5`, from source `9e81a7c849837dea477ddb5a8c93f43665774573`. Its actual launched PCK is `d387d34ad37fc959f974b9ced0107d5ad2a0e2505e55a090dd20fc583d62aa27`. The held content 5 package-r2 remains historical and is not admitted by this review.

The independent read-only audit passes **12/12 grouped checks** in `navigation-check.json`: all 29 ZIP members match the extracted files; all 28 declared payloads match size and SHA256; all 525 runtime-source records match the capture binding; both real native processes use the same package and saved-preference namespace, preserve package/instrumentation bytes and quit with code 0. Both engine logs are free of warnings/errors. Source admission51 checks are the package's separately recorded content 6 proof, not51 additional checks executed by this role. The earlier7-check package-preflight adversary review also remains separate.

I opened **18 original PNGs**: first-run 01–11; initial constructing loader; film-return queued loader; P05 keyboard Return-to-courtyard focus; P06 returned-title Settings; and second-process R00 title, R01 Settings and R03 guide. Their exact names and hashes are in `reviewed-originals.json`; unmodified copies are under `originals/`. All39 PNGs from the two processes additionally pass metadata/hash verification, which is not a claim that all 39 received visual review. Each PNG is 960 × 540 content within a 960 × 600 native window. These are new packaged originals, with no U5 pixels reused.

| Witness | Observed packaged result |
| --- | --- |
| Title01→02 | Primary Enter Confluence focus, practice selection, offline copy and secondary routes are legible and contained. The hero remains clear of the title panel. Inactive player presentation remains unsuspended: idle age 0.133333→0.666667 over32 physics ticks; face and secondary clocks advance while combat elapsed remains 0 and suspended. Two stills plus clock receipts establish this bounded idle behavior, not continuous animation quality. |
| Help03 / training04 / Settings05 | Fresh Help heading and Back are visible. Training entry shows the playable hero, targets and separated HUD. Settings retains its heading and fixed Done footer while paused. |
| Film06→title07 | The original scripted film loads. Native Escape returns to a fresh courtyard retaining session Bow training selection and visible, interactive “Begin bow training →” primary focus. |
| World08 / overview09→10 | World entry is active. F1 overview reports “Practice paused” and disabled ability values. Across64 observed physics ticks (45 requested wait plus capture/settle overhead), motion remains Piercing Dawn windup at 0.133333s, authority cast age 0.1s and elapsed 0.5s; army, face, secondary and HUD reports remain unchanged. The tree itself is not paused. |
| Resume11 | Native F1 restores active player presentation and authority. The same cast/generation releases exactly once in kit and motion, enters recovery, and the HUD reports Piercing Dawn released. This witness precedes the later unintended Restart and recovery. |
| Loader | All28 first-process transition events preserve one owner and disabled outgoing scene during busy phases; all 15 displayed loader receipts show focused, interactive Back with outgoing controls disabled. Two loader originals were opened and show contained copy and focus. No actual cancel/retry activation was added in this package review. |
| Return and second process | P05 shows a completely inset keyboard focus ring on Return to courtyard. P06 shows actual returned-title Settings. After genuine Quit 0, the second process mounts a ready title with primary focus, then shows saved Settings and the remapped guide. Done/Back remain visible. Session mode defaults to Confluence on a new process; saved preferences persist separately. The second process also quits 0. |

The first process required **two explicit native-input recoveries**. The driver selected a pause-guide coordinate from an unsettled layout; pointer [474,192] fell inside the settled Restart control, not Continue, and kit generation changed 1→4. Native Escape, two observed settling frames and F3 opened the guide. Later, an immediate post-world-return Settings pointer missed; a native click at the current settled Settings location opened it. Original pending events, before/after snapshots, timestamps, exact geometry and the original driver are retained under `capture-receipts/first/`. No callback or authority state assignment was used by these recoveries. The final relaunch driver waits for three observed stable target rectangles; its distinct hash is retained under `capture-receipts/second/`. These recoveries support reachable endpoints after correction, not a clean uninterrupted first plan or reliable clicks against transient geometry. Instant-layout click behavior remains unqualified.

The independent checker's initial 8/9 result is also retained: it incorrectly required focus at the synchronous queued signal, which is emitted just before `grab_focus()`. The actual displayed frame already had Back focus. `method-correction.md` explains the corrected event/frame distinction. The completed first process then passed 9/9; the combined 12 includes those repeated checks rather than treating them as new coverage.

Reproduce the read-only audit from the repository root (no Godot, import or rendering):

```sh
env LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 2 python games/yuga-native/docs/evidence/ui-campaign/I3/role01/check_package_navigation.py \
  --first /tmp/yuga-i3-native-r1 --second /tmp/yuga-i3-relaunch-r1 \
  --package /workspace/scratch/ui-campaign/I3/package-r3 \
  --output /tmp/yuga-i3-navigation-independent.json
```

Execution used the bundled Godot 4.6.3, software Vulkan Forward+ llvmpipe and Dummy audio, with native XTest input and an external observer. This review does not establish listening quality, physical-GPU performance, screen-reader behavior, every viewport size or the separate staged outcome scenarios. Existing R4 contact/motion and R3 grooming limitations remain open. Root owns the final package decision; UI03 owns the capture archive and UI02 the detailed preferences review.
