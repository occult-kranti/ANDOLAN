# Native tactical motion rehearsal

Task **YUGA-TACTICAL-CASUAL-13**, native offline Casual. Base commit
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`.
Combat owns `tools/capture-tactical-motion.gd`; root owns the film render,
wrapper and encoding. This tool adds no runtime rule or presentation changes.

The tool records 180 original 1280×720 frames at 15 simulation frames per second,
one real physics callback per sample, with the actual tactical world, player,
weapon, receivers, utilities and HUD. Every frame has a PNG hash, clock,
authority state, weapon pose, camera, receiver state and effect list in
`motion.json`. Runtime source files, reused map assets and corresponding import
files are hashed before and after the run. Audio cues execute, but this tool
does not capture or assert synchronized audio.

This is a **scripted rehearsal**, not ordinary OS input or a natural match.
Declared setup: give the local actor 9000 credits, purchase SURYA/armor/Q/C via
the actual own-spawn purchase API, advance the real preparation clock, stage
the player at `(-29,0,-18)` and two real enemy bodies at `(-29,0,-3)` and
`(-35,0,-2)`, and disable bot decisions. Normal actor animation, damage,
one-life deaths, weapon authority, effects and collision remain active. Eight
settling ticks precede the film. No in-film actor teleport occurs. The camera
stays first person and smoothly aims toward the second receiver after the dash.

| Frames | Actual action |
| --- | --- |
| 0–17 | Three normal SURYA shots at 8, 11, 14; real primary receiver death |
| 18–50 | Actual 2.1-second reload and return to weapon origin |
| 51–65 | ADS press and release through the real input action state |
| 66–85 | Q cast; airborne seed and cloud bloom |
| 86–103 | C placement; physical ward and animated pattern |
| 104–123 | E sidestep, 5 m of collision-aware lateral travel past ward edge |
| 124–145 | Explicit six-point ultimate fixture, actual X cast and three paced rays |
| 146–179 | Receiver death/weapon recovery and continuing utility effects |

The ultimate points are **staged**, not naturally earned during these twelve
seconds. The three real schedule thresholds `.55/.79/1.03` seconds are crossed
at `.60/.80/1.0667` seconds on this 15-Hz capture clock, frames 132/135/139.
These samples do not claim finer temporal precision or hardware frame rate.

The non-rendering rehearsal passed **17/17 checks**, all 180 samples had actual
physics delta `1/15`, and the world advanced exactly twelve film seconds. It
confirmed primary receiver death, reload return with 24/69 ammo/reserve,
accepted Q/C/E/X, seed-to-cloud lifecycle, actual ward, a 5 m dash, three solar
releases, second receiver death, continuing live authority and unchanged source.
The final run exited 0 with no warnings or errors:

```sh
godot --headless --audio-driver Dummy --disable-render-loop --fixed-fps 15 \
  --path games/yuga-native --script res://tools/capture-tactical-motion.gd -- \
  --probe-only \
  --output=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/combat/motion-probe-r3
```

Receipts: [final report](motion-probe-r3/motion.json), [final log](motion-probe-r3.log).
Tool SHA-256 at this checkpoint:
`fdd638dd35a49955fd30512c43cee1f7aa2a018c8e1b616b5299350b1adfb5c6`.
Final report SHA-256:
`3516dd8dde874c35cc9bb67c4d60426eb1d2c1deafb3be92a94953dd724ee3c4`.

Earlier probes remain. Probe r1 caught the startup accumulator's initial
60-Hz tick before the new 15-Hz setting took effect. This tick is now confined
to the explicitly excluded eight-tick warmup; film samples retain the strict
15-Hz check. Probe r2 passed behavior but retained audio resources at shutdown.
The harness now stops voices, frees the world, awaits two cleanup frames and
allows 100 ms of wall time for the audio mix worker. A simulation timer alone
does not guarantee that wall interval in accelerated headless tests.

Next owner: root, after the new SURYA asset is imported and its runtime path is
pinned. Run the tool on the serialized Forward+ display with `--fixed-fps 15`,
omit `--probe-only`, and use a fresh absolute output directory. Review actual
originals before claiming visual acceptance. No rendered film or actual audio
review is claimed by this non-rendering checkpoint.
