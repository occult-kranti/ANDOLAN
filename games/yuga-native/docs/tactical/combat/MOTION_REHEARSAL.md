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

## Subsequent actual native film review

Root rendered [180 originals and their report](../evidence/motion-r1/motion.json)
after importing the dedicated SURYA gun. All 180 PNG hashes and 1280×720
dimensions independently match the report; the capture passed the same 17
checks with unchanged sources. The combat reviewer inspected every advancing
original through twelve labeled analysis contact sheets, plus sixteen full
resolution originals. See the [independent visual receipt](motion-r1-review/review.json).
Its findings apply to these exact pixels and source pins, rather than to the
earlier procedural gun. Film report SHA-256:
`7668c72f5893ca4630d00823352ca98dffc5bef174285990d89d5cace3e2bf83`.

The sequence visibly demonstrates recoil/return, completed reload, centered
ADS, seed flight followed by the occluding veil, a clearly patterned ward,
continuous movement around its flank and the ultimate's second receiver
collapse. No delivery blocker was found for this bounded demonstration.
Dedicated Q/C hand casting, a softer veil entrance, a less harsh/faceted dash
ring and stronger visible ultimate windup remain art work. The first two
solar traces appear nearly continuous at 15 fps despite distinct authority
releases; this film does not establish three visually isolated flashes.
Reload contact is still a coarse stylized hand gesture near the bottom crop,
not anatomical finger/contact qualification. Audio was not reviewed.

The analysis sheets were generated with existing FFmpeg; original PNGs were
not modified. The last sheet has four originals and twelve empty black cells.
Source files and imports are pinned in the capture report, including SURYA
GLB `f2ab39c6f559c47461d340a29ae51d040be9565cddd1602cd41cbe118f9cc810`
and weapon script
`7dca037cc8af82b0c0cb9313fa835551231eedfc598726555853c1d005ccfbe1`.

Next owner: root for encoding and delivery. The staged resource/actor setup
and limits above remain mandatory descriptions of the finished film.
