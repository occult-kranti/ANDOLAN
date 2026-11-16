# STUDIO3 · Rama tactical preview poses

Task `YUGA-HERO-STUDIO3`, native offline Casual's isolated hero viewer.
Source checkpoint: `e59a07a4786e9ad491cfef7a4e706dbd06063adc` on
`work/yuga-studio`. The earlier finish2 package remains unchanged.

The new controller animates the accepted full-body Rama skin holding SURYA:
subtle idle breathing, a raised Aim hold, Q throw follow-through, C open palm,
E braced upper body and X charged gesture. It is a presentation preview, not
new full-body tactical gameplay or a new hero asset. Root owns the viewer
adapter and capture; the UI owner supplies explicit preview controls.

## Ownership and API

This owner changed only `scripts/tactical_hero_pose.gd`,
`tests/tactical/hero_pose_cases.gd` and this directory. The motion/combat and
hero-art skills were applied. Canonical GLBs, motion library, materials,
quiver removal, gameplay, UI, physics and world scripts remain with their
existing owners. No import, render or git operation ran in this lane.

The module is a `RefCounted` object with no process callback or input handler:

```gdscript
var poses = preload("res://scripts/tactical_hero_pose.gd").new()
var base_firearm = rig.get_bone_global_pose(rig.find_bone("wrist.R")) * weapon.transform
poses.configure(rig, motion, socket, weapon, base_firearm)
poses.set_stance("idle") # or "aim"
poses.play_ability("q") # q / c / e / x
poses.set_reduced_motion(false)
poses.step(delta)       # caller owns visibility/pause; at most .25 s per call
poses.reset()
var state = poses.report()
```

Configure after the accepted static firearm hold and attachment exist. It
requires the validated 164-bone adapter, an inactive motion modifier, a
`wrist.R` attachment and a matching firearm transform in skeleton space.
Duplicate or inconsistent configuration fails without changing the pose.
Root/legs/feet retain their captured local and global transforms. The caller
keeps the existing instance-only quiver removal and hidden bow/nocked arrow.

The controller captures both accepted wrist transforms relative to SURYA.
Idle/Aim retain that relationship, including actual fingertip skin placement.
The right-hand attachment remains fixed in all poses; the rifle is never
repositioned to hide an unreachable arm target. Q/C/X release the left hand
and blend it back to its captured foregrip. E retains both hands on the gun.
The existing four-segment arm solver handles reach without changing rest
lengths. Every sample starts from the accepted local pose, preventing drift.

| Preview | Duration | Motion |
| --- | --- | --- |
| Idle | Until selected otherwise | Bounded breathing, two-hand hold |
| Aim | Until selected otherwise | Raised/reoriented firearm, two-hand hold |
| Q | 1.35 s | Open-hand throw follow-through and continuous regrip |
| C | 1.50 s | Open palm and continuous regrip |
| E | .90 s | In-place upper-body brace; no root translation |
| X | 1.95 s | Charged palm, small three-pulse emphasis, continuous regrip |

These are preview durations, not ability costs, windups, releases, movement or
cooldowns. A gesture returns to the selected stance. A new request blends
from the outgoing pose. `reset()` restores every captured local bone exactly;
omitting `step()` freezes the pose. Reduced motion removes idle breathing and
reduces torso offsets while retaining the recognizable hand gesture.

`report()` includes `selected_stance`, `active_slot`, `age_s`, `duration_s`,
`phase`, `clock_s`, finite state, wrist target errors and support weight.
Its phase follows the authored entry/hold/return times. It emits no authority
events, shots or audio.

## Actual checks and preserved correction

The actual imported skeleton, SURYA and sampled fingertip skin passed
**37/37 focused checks**, exit 0, with no engine warning/error lines. The
fixture constructs the accepted finish2 hold independently of the evolving
viewer UI. It samples 476 left and 478 right distal skin vertices. This tests
preservation of the accepted skin relationship; it does not newly establish
absolute finger-to-mesh collision or perfect anatomical grip.

```sh
godot --headless --path games/yuga-native --check-only \
  --script res://scripts/tactical_hero_pose.gd
godot --headless --path games/yuga-native --check-only \
  --script res://tests/tactical/hero_pose_cases.gd
godot --headless --audio-driver Dummy --disable-render-loop \
  --path games/yuga-native --script res://tests/tactical/hero_pose_cases.gd -- \
  --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/studio3/hero/checks-r3.json
```

[Current report](checks-r3.json) and [log](checks-r3.log) cover 30/60-Hz
consecutive bone poses, reachable wrist targets, hand skin retention, exact
fixed lower body, Q→X interruption, request without a time step, pause,
invalid input, gesture from Aim returning to Aim, reduced motion and exact
reset. Canonical sources did not change during the check.

The [first report](checks-r1.json) preserved four failures: Aim exceeded left
arm reach by 27.3 mm, and Q/X entered too quickly at 30 Hz. The rejected
[pose source](pose-rejected-r1.gd.txt) and
[test source](checks-rejected-r1.gd.txt) remain. Moving Aim's firearm target
into reachable shoulder space fixed the contact loss; lengthening Q/X reach
ramps from .30 to .42 s fixed the entry. No threshold was relaxed.

The corrected maximum 30-Hz bone displacement is .087014 m, below the original
.09 m bound; maximum angular change is .536139 radians, below .65. Wrist
target error stays below .0000013 m. Idle/Aim sampled fingertip retention
stays within .0000037 m, and lower-body local/global transform changes are
exactly zero. The [second report](checks-r2.json) passed 36/36; the final pass
also measures global lower-body preservation and adds the Aim→Q→Aim case.

## Source freeze and next owner

| File | SHA-256 |
| --- | --- |
| `scripts/tactical_hero_pose.gd` | `43dee1cd2c890e38b09377bba3158405331b1599e10c325555ee0f383a77c61e` |
| `tests/tactical/hero_pose_cases.gd` | `3e7a4c5a73aa8645a72d5380afc4b582e22ce4d3d9a08a1b37205e3421343179` |
| Current report | `7710ccbd641d3ad3b15cb24ac5530ca7e08970be16c2e2b57ab44a4293620a4e` |

Root's [actual native capture review](visual-review-r1/README.md) now accepts
the bounded preview after all 135 advancing originals and 13 stills were
checked. Q/C/X return the left hand continuously; feet remain planted and no
new gross cloth separation is apparent at the captured scale. The film
preserves four initial loading frames, followed by 131 visible-hero frames.

Aim remains a restrained chest-level pose: finished stock/cheek and eye-line
alignment is still open. The gestures do not qualify full-body tactical
gameplay; detailed unseen-side contact, stronger silhouette differentiation,
ordinary input, human game feel, audio and hardware performance remain
separate. Next owner: root for final integration and delivery.
