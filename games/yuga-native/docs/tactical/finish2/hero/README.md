# HERO-FINISH2 · original first-person casting

Part of `YUGA-TACTICAL-FINISH2`, native offline Casual. The immutable
`sanctum-art-r1` checkpoint remains unchanged. This pass addresses the visible
defect in its 180-frame rehearsal: Q/C and the X windup retained the ordinary
firearm hold pose. Full-body tactical hero work remains separate.

Baseline commit: `143289f410ef17ced20d0546efc7fccafee75ba9`, shared branch
`work/yuga-studio`. See [baseline receipt](baseline.json) and the preserved
[prior weapon source](tactical_weapon-baseline.gd.txt). The SURYA GLB is unchanged:
`f2ab39c6f559c47461d340a29ae51d040be9565cddd1602cd41cbe118f9cc810`.

## Distributed ownership and public API

The hero lead owns `scripts/tactical_weapon.gd`,
`tests/tactical/hero_finish_cases.gd` and this directory. Its nested specialist,
`hero_combat/cast_motion`, authored only `scripts/tactical_cast_motion.gd`.
Both applied the YUGA motion/combat and hero-art skills. Root owns the world
hooks, effects, shared imports, rendering and packaging; the map lead works in
parallel on its exclusive map files. No additional nested processes were used.

Root calls `weapon.present_ability(slot)` **after** successful authority use,
and `weapon.reset_presentation()` at round reset/death. Presentation never
spends a charge, fires a projectile, changes damage, grants movement or delays
an existing ability. `weapon.step(delta)` advances the rig on the same paused
match clock as the firearm. There are no autonomous animation callbacks.

The new module exposes `begin(slot, reduced_motion)`, `step(delta,
reduced_motion)`, `sample()`, `report()`, `cancel()` and `reset()`. Its pose
sample supplies additive weapon position/rotation, cast weight, active slot
and age. The casting arm is a sibling of `weapon.model`, so lowering the rifle
does not hide that arm. The prior support hand hides while casting. Actual
successful fire/reload requests start a `.28s` visual return; rejected requests
leave the current pose alone. Ammunition, recovery and reload rules retain
their original behavior. Equipment rebuilds retain exactly one casting rig.

## Implemented geometry and motion

The hand is original procedural geometry: rounded palm/wrist, five digits
with three hinged segments each, a tapered indigo sleeve and brass bands.
Small hand-local solar rings and a core provide charge accents. These are
cosmetic shapes, separate from real world projectiles and physical cover.
No external mesh, model weight or generated animation was imported.

| Slot | Visible pose | Presentation duration |
| --- | --- | --- |
| Q | Open-hand throw follow-through and rifle lowering | `.90s` |
| C | Spread fingers and open-palm ward emphasis | `1.05s` |
| E | Curled fingers and braced lateral movement pose | `.65s` |
| X | Opening charged palm, hand-local solar accents, restrained rifle lowering | `1.62s` |

Q/C world effects still activate immediately on acceptance: these poses are
follow-through/emphasis, not a new gameplay windup. X accents mirror the
existing `.55/.79/1.03s` release schedule without issuing shots. Interrupted
casts inherit the outgoing hand, fingers and rifle offsets. Reduced motion
retains the readable pose with smaller movement and no ring spin. Hard
lifecycle reset clears the presentation immediately; pause simply stops time.

## Checks and corrections

The actual imported firearm and rig passed **94/94 focused checks** at
30/60/120 steps per second, exit 0 with no warnings or errors. Checks cover
finite consecutive poses, distinct gesture channels, exact return, Q→C
interruption, paused clock, invalid/unknown input, accepted versus rejected
fire/reload, finite ammunition transfer, utility during reload, death/reset,
equipment changes, pistol support, ADS and reduced motion. Twenty additional
checks project actual mesh corners, including every fingertip, at the hand
visibility switch: 15/60 Hz, maximum supported 110° hip FOV and 79.2° ADS,
plus interrupted casts. All outgoing geometry is already below the viewport
before it hides or the normal grip reappears.

```sh
godot --headless --audio-driver Dummy --disable-render-loop \
  --path games/yuga-native \
  --script res://tests/tactical/hero_finish_cases.gd -- \
  --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/finish2/hero/checks-r3.json
```

Evidence: [current report](checks-r3.json), [current log](checks-r3.log).
The nested owner also ran:

```sh
godot --headless --path games/yuga-native --check-only \
  --script res://scripts/tactical_cast_motion.gd
```

The preserved [first report](checks-r1.json) passed 73/74 and exposed a sharp
Q entry: maximum 30-Hz hand step `.236177m`, rifle step `.138657m`.
Lengthening Q's reach ramp from `.08s` to `.13s` reduced those to `.155859m`
and `.091503m`; the existing `.18m/.12m` bounds were retained. No ability
activation, flight or release time changed. A separate geometry correction
extended the sleeve below the lower view edge while preserving wrist/palm
positions, to avoid a visible floating forearm cap during raised poses.

Root then captured an isolated actual native probe using the prior map and
the new hero/effects. Its 18 checks passed, but the [independent visual review](probe-review/review.json)
rejected a real handoff artifact: at frames 75→76, 97→98, 111→112 and 145→146,
the casting hand disappeared while still on screen and the support hand
appeared elsewhere. The original probe, analysis sheets and rejected source
copies remain in this packet. A numeric pose pass did not waive this defect.

The correction retracts the casting hand to local Y `−.72`, restores the
support grip only after the cast becomes inactive, and lengthens presentation
reach/return paths without changing gameplay timing. Maximum sampled hand and
rifle steps are now `.143956m/.042047m`, below the retained `.18m/.12m` limits.
The nearest projected geometry at a visibility switch is Y `737.66` in the
720-pixel viewport, so fingertips and the complete hand have left view first.
The updated durations above describe only presentation. The old
[74-check report](checks-r2.json) remains as evidence of the pre-render stage.

## Frozen sources and next owner

| Source | SHA-256 |
| --- | --- |
| `tactical_weapon.gd` | `246b0038137a15787cef95d32d5e74238807997cfe8481fee774caa5620c2203` |
| `tactical_cast_motion.gd` | `506dae75659f4a9a351866a7ded21cdd7dd202ed4fe3978542ce2610c4cdfe6b` |
| Current check report | `35837b747946e8acb474e2f10f0d5c767a686edb47c2cb66043fe515d1358442` |

Root integrated the authority-success/reset hooks and captured the corrected
combined native film. The [final visual review](final-motion-review-r1/README.md)
accepts the bounded correction after inspecting all 180 advancing originals
in contact sheets and 33 selected full-resolution frames. Every PNG hash and
dimension matches the complete capture report, whose 18 checks pass.

Q/C/E/X casting hands now leave view before the ordinary support grip returns
at frames 79/101/113/148. The support grip still reappears in one frame; this is
an off-screen return followed by a discrete grip reset, not a continuous
anatomical regrip. Stylized procedural anatomy and the simple support cuff
remain limits. Root owns package delivery from the combined frozen runtime
`b682eb7355b4bef4441e943fd007ecd3fc85be371a30dafe59770011f5702055`.
No render/import was run by this owner. The scripted silent film does not
establish ordinary input, finished full-body art, online play, audio listening
or hardware performance.
