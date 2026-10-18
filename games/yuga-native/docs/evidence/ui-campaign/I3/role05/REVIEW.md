# I3-05 · Packaged preference persistence

Accepted for the stated Linux scope: native input saved aim, sound, courtyard shadow, keyboard and ability-effect preferences; the actual packaged game retained them across training, Confluence, return to title and a fresh process using the same isolated user directory. The independent receipt validator passes **31/31**. Eleven original images were opened directly and verified byte-for-byte against the central archive. This role changed evidence and its read-only validator only; no runtime repair was needed.

The first process completed with **two explicitly recorded native fixture recoveries**. It is not an uninterrupted planned-navigation pass. The fresh-process relaunch completed without recovery. Both used native Quit and exited 0, with no engine errors or leak messages.

## Exact build and execution

- Product: YUGA native; source commit `9e81a7c849837dea477ddb5a8c93f43665774573`.
- Export source manifest: `61700ca7e3a77e20ae81175ad5babd337d7094ab82907801ac2b20ee85bce5e4`.
- Linux ZIP: `56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5`.
- Executed ELF: `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`.
- Executed PCK: `d387d34ad37fc959f974b9ced0107d5ad2a0e2505e55a090dd20fc583d62aa27`.

UI03 executed the extracted ELF with explicit `--main-pack`, an external read-only observer and native XTest input. Both runs used X11, software Vulkan Forward+ / llvmpipe and Dummy audio. Native window size was 960 × 600; the unmodified viewport PNGs are 960 × 540 from the logical 1280 × 720 interface. Neither preference run enabled authority staging. Exact commands, input journals, observer and original driver bytes remain in the [first-run archive](../role03/native-r1/run.json) and [relaunch archive](../role03/relaunch-r1/run.json). [Identity and recovery review](identity-recovery-review-r1.json) verifies the actual payload bytes, source pins and preserved instrumentation.

## Observed behavior

| Preference | Native edit and cross-scene observation | Fresh-process observation |
| --- | --- | --- |
| Aim | End on Sensitivity set 2.50×; invert enabled. Confluence's actual player receiver loaded sensitivity 0.006 and inverted aim. | Settings remained 2.50× with inversion checked. |
| Sound | Home on Volume set 0%. Training retained it; Confluence displayed “Sound · muted” and all four actual audio receivers reported volume 0. | Settings and the actual action-audio receiver remained at 0. |
| Courtyard lighting | Dynamic sun shadows unchecked; the value remained false after returning from Confluence. | The checkbox remained unchecked. |
| Keyboard | Native key capture remapped Piercing Dawn to physical J / 74. World HUD and guide both used J. | The focused Piercing Dawn binding and guide still showed J; key capture was inactive. |
| Ability effects | Both ability-only reductions enabled through native input. Saved confirmation and focused toggle were simultaneously visible. Confluence's live receiver loaded both values. | Both checked controls and the actual receiver retained the saved values. |

The first run began with an empty isolated user directory. Its final saved config, relaunch's initial config and relaunch's final config are byte-identical: SHA-256 `d09a812fbee26e7fa682e459511504e35d64cf02d20b629ad4905c3967cffdb5`. This establishes a real process restart, not only in-memory scene return.

Direct original review covers [P01 settings](../role03/native-r1/P01-native-settings-edited.png), [P02 remap](../role03/native-r1/P02-native-piercing-dawn-remap.png), [P03 saved feedback](../role03/native-r1/P03-native-guide-preferences-saved.png), [training Settings](../role03/native-r1/05-package-training-settings.png), [world HUD](../role03/native-r1/08-package-world-live.png), [P04 world guide](../role03/native-r1/P04-world-guide-loaded-preferences.png), [P05 world sound/return](../role03/native-r1/P05-world-muted-sound-and-return.png), [P06 returned Settings](../role03/native-r1/P06-returned-title-settings.png), and relaunch [R01 Settings](../role03/relaunch-r1/R01-relaunched-settings.png), [R02 remap](../role03/relaunch-r1/R02-relaunched-remapped-control.png), [R03 guide](../role03/relaunch-r1/R03-relaunched-guide-preferences.png). Selected controls, focus outlines and fixed Done/Back actions are contained. Partially clipped earlier rows are ordinary scroll boundaries. Per-image findings, frames and original hashes are in [the final image review](original-review-final-r1.json); the earlier partial review remains unchanged.

## Native fixture recoveries

The first immediate pause-guide click used a rectangle observed before layout settled. Rama's guide button subsequently moved down 33 pixels; the injected point `(474, 192)` hit **Restart lane practice**, as established by [exact settled hit analysis](../role03/native-r1/coordinate-recovery-analysis.json). Kit generation changed from 1 before that click to 4 before recovery. The separate [native recovery journal](../role03/native-r1/native-recovery.json) records Escape, settling and F3 in the same process/window. Its earlier “resumed practice” wording is superseded by the exact Restart hit analysis. P04 and P05 therefore demonstrate retained preferences after this restart/recovery, not an uninterrupted world session.

The immediate Settings click after title return also missed. A [second native journal](../role03/native-r1/native-recovery-title.json) records clicking the current settled Settings rectangle in the same process. No product callbacks or runtime values were assigned by these recoveries. The original first-run driver is preserved at its recorded hash. The relaunch driver adds a three-frame stable-geometry check before pointer clicks; its different hash is recorded independently, and the relaunch needed no recovery. Main input journals contain 78 and 29 events respectively; the three recovery events are preserved separately.

## Verification and limits

Executed from the repository root:

```sh
python3 games/yuga-native/docs/evidence/ui-campaign/I3/role05/validate_preferences.py \
  --first /tmp/yuga-i3-native-r1 \
  --relaunch /tmp/yuga-i3-relaunch-r1 \
  --report games/yuga-native/docs/evidence/ui-campaign/I3/role05/receipt-validation-r1.json
```

[Result: 31/31, exit 0](receipt-validation-r1.json). The validator checks package/observer identity, completed process ordering, same-XDG config bytes, original image hashes, actual settings and receiver values, and native remap input. Direct pixel review and the separately disclosed recovery journals supply the visual and navigation qualification.

“Dynamic sun shadows” is scoped to courtyard lighting by the controls screen's `PreferencesLocation` text. Confluence retains its independent lighting and visible shadows; this review does not claim that the saved flag disables world shadows. The Master bus mute flag remains false while local receiver volume is zero. Dummy audio establishes neither listening quality nor loudness perception. Fullscreen stayed false and was not toggled. Package save failures, malformed saved data, alternate resolutions, Windows execution and hardware performance are not established here; earlier source-bound I2 tests retain their own scope. General hero art and compact auxiliary text limits remain separate from preference persistence.

Next owner: root / I3 integration acceptance. UI03 owns the central immutable originals, package execution journals and separate staged-outcome supplement.
