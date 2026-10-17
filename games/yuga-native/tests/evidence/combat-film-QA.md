# Independent combat-film QA

The final authored 24-second film passes **20 screenplay/resource checks** and **42 native animation/viewer checks**. The result validates a deterministic scripted film. It does not certify authoritative combat, a complete hero kit, animation art quality or a playable multiplayer match.

## Four review rounds

1. **Contract challenge.** Added explicit threat/telegraph/impact links, counter windows and contact modes. The stationary-foot contract excludes Rama's evasion translation and Ravana's 9.2–10.2 s pivot. Runtime review requested unique actor resources, strictly increasing motion keys, nonempty actor actions, unambiguous intervals, and rejection of degenerate camera directions.
2. **Independent screenplay checks.** The Python test verifies full actor/camera/contact chronology, exact receipt times, health arithmetic, visible warnings before release, guard coverage, and geometric escape from the locked wave corridor. It rejects missing actors, invalid/nonfinite times or coordinates, duplicate events/resources/JSON keys, missing links, overlapping or misplaced data, and impossible health results. The final stereo PCM16 mix has exactly 1,152,000 frames at 48 kHz: 24 seconds. Resource hashes are recorded.
3. **Actual imported animation and director integration.** Each actor's nine imported clips is sampled at 41 phases. All **121,032** isolated bone transforms are finite and resolve to the loaded 164-bone rigs. The real director is then sampled at **380** times, including receipt/cue boundaries and 8.55 s; all **124,640** additional bone transforms are finite and actor roots remain within the world. Actual CPU-skinned sole geometry is measured in world coordinates.
4. **Edge-case and lifecycle closure.** Twelve malformed native-script fixtures are rejected, including zero-length actions and camera position equal to its target. Fifty backward seeks reproduce actual bone transforms, camera, effect state and health exactly. The scene retains the same **132 nodes**, **176 unique mesh/material resources** and **one audio player**. The real title button opens the film; wired pause, scrub, replay and return controls work. A missing-model viewer displays a fatal error and still returns to the title. Both logical viewport layouts, 1280×720 and 960×600, fit without control overlap. Capture sampling remains silent.

## Contact and rig interpretation

At 8.55 s, measured world-space soles are:

| Actor | Left sole | Right sole | Actor origin |
| --- | ---: | ---: | ---: |
| Rama | 8.4937 mm | 8.4932 mm | 0 m |
| Ravana | 8.4870 mm | 8.4872 mm | 0 m |

Across all declared planted intervals in revision 4, the minimum sampled sole height is **6.7588 mm** and the greatest horizontal sole-centroid drift is **0.5637 mm**. These remain within the original gates; revision 3 measured 7.2811 mm / 0.3983 mm before the guard-reset interpolation change. These geometry measurements do not determine whether a rendered contact shadow looks convincing.

The initial animation test incorrectly treated every local bone translation as a physical segment length. The actual rig has an unweighted `root` and three body-bearing child branches, `pelvis.L`, `pelvis.R` and `spine05`, that translate together for crouch. Their translation vectors agree within **0.53 micrometres**. The bowstring is a separate intentional deformation control. The corrected gate retains the original **5 mm anatomical-segment threshold**; maximum measured anatomical variation is **0.91 micrometres**.

The control motion is disclosed rather than hidden: the body branches begin 35 mm from their rest translations; guard adds about 43 mm, evasion 160 mm, and casting 59 mm. The unused defeat clip adds about 429 mm, reaching a 464 mm rest offset. An early speculative 450 mm control-travel limit was removed because it was not an authored acceptance requirement; root topology, zero skin weighting, coordinated branch motion, finite poses, actual anatomical lengths and sole behavior are checked separately. These numerical checks do not approve the visual crouch or defeat animation.

## Evidence and reproduction

`combat-film-qa-final-manifest.json` pins the final reports, logs and test helpers. Final source pins include script revision 4 `6ec07cb8…`, director `3fdfbe25…`, actor adapter `f050e4d5…`, Ravana model `f00bed98…`, and the revised Rama/Ravana motion libraries `3ab73222…` / `d0d0f3b2…`.

An additional read-only continuity probe samples all actors at 24 Hz and on both sides of all 17 internal action boundaries. Revision 3 exposed one fast, continuous guard-reset transition. The planner increased only `ravana-ready-wave.blend_in_seconds` from 0.12 to 0.32. All three suites were rerun with unchanged tests and thresholds: **20 script + 42 native + 5 continuity checks pass**. The reset's maximum frame travel fell from 0.2663 to 0.1065 m and its maximum angular delta from 50.20 to 19.41 degrees. No speed alerts remain; the worst boundary displacement remains 12.594 micrometres. `combat-film-motion-continuity.md` records the numerical scope and limitations. Revision 3 evidence is preserved under explicit historical filenames.

```sh
python3 games/yuga-native/tests/combat_script_cases.py --report /tmp/combat-script.json
godot --headless --path games/yuga-native --script res://tests/combat_film_cases.gd -- --report=/tmp/combat-film.json
godot --headless --path games/yuga-native --script res://tests/combat_motion_continuity.gd -- --report=/tmp/combat-motion.json
```

All three final commands exit zero. The native integration log contains one intentional `YUGA_COMBAT_FILM: rama: missing model_path` diagnostic from the fatal-resource fixture and no unexpected errors or warnings. The continuity log contains no errors or warnings.

Earlier reports remain historical evidence. The first schema draft used an incorrect test namespace assumption; later actor reports used the overbroad rig-distance gate described above. The first integrated report also compared JSON float-valued health dictionaries against integer-valued dictionaries too strictly; the final test compares numerical health values and separately records playback state. These were test corrections, not gameplay repairs. Button callbacks and engine state are exercised headlessly; operating-system clicks and actual frames are reviewed separately by root.
