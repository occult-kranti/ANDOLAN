# Rama motion correction review — 17 October 2026

Goal: one reusable, authority-driven Rama presentation controller for native YUGA.
Source base: `e765a23264cf3c3c38fab1ded677832a24fdd64e` on
`game/yuga-native-production`; the working-tree sources below identify this review.
Gameplay, input, projectiles, health and movement remain integration-owned.

The motion layer has 23 original authored clips, exact rest-rig validation,
full-body traversal/reaction priority, upper-body mobile bow actions, stationary
ability planting, world support contacts, calibrated hand/string sockets and a
visible nocked arrow. Windup holds until the combat-authoritative release event.
Cancellation hides the arrow immediately and fades the interrupted pose. Runtime
presentation does not change velocity, ammo, damage, cooldowns or cast timing.

## Final source pins

| Source | SHA-256 |
| --- | --- |
| R7 `assets/heroes/rama-hero.glb` | `667f3a215a7b868e3bdbcde880a73d42b68b29af1303db4e1d99b93f73cf2b50` |
| `scripts/rama_motion.gd` | `d3a898b640de9c62aa3a919786b5a3b7c56dea823349472e361ba33906010f22` |
| `assets/animations/rama_hero_motion.tres` | `1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8` |
| `capture_motion.gd` | `04342f932cd22f6f95502d9709a0837eca5e3d7f75d3124b30c97bac87774878` |

`provenance.json` also pins the generator and historical rest-rig input. All body
trajectories and IK are original project work. No third-party TPS animation was
imported. The existing MakeHuman/CC0 anatomy and project finger-animation provenance
remain in the asset notice.

## Findings corrected

1. The old production carry/fire interaction lowered or retriggered the bow before
   a readable complete draw. Separate draw, ready-draw, authoritative release and
   recovery states now share a continuous prior-pose blend. Repeated primary fire
   uses ready-draw while retaining the raised bow.
2. The first authored motion take used an incorrect native foot-axis assumption.
   R1 visibly raised the toes. Preserving the actual foot rest orientation and
   validating CPU-skinned sole vertices corrected this; R1 remains rejected.
3. Independent review reproduced a roughly 30 cm wrist jump when a cached aimed
   pose received aim a second time on cancel, a new draw or a locomotion change.
   Transition caches now retain the pre-aim shoulder rotation separately from
   final socket/render transforms. The same nonzero-pitch/yaw cases now match
   zero-angle controls, with submicrometer wrist changes at the transition frame.
4. R2 exposed a broad triangular ivory-cloth fan with striped self-overlap during
   strafing, especially frames 97 and 105. A dedicated low-clearance, noncrossing
   side-step trajectory replaced sideways rotation of the long forward stride.
   The art owner separately repaired the dhoti and both border bindings in R7:
   smooth torso-dominant weights, limited upper-thigh influence, no lower-leg
   ownership. All other geometry/material/rest-rig data remained unchanged by
   that art correction. R2 is preserved as failed evidence for this finding.

## Executed functional checks

Both commands completed with exit 0 on the exact imported R7 asset:

```sh
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/rama_motion_cases.gd -- --report=/tmp/rama-motion-study/motion-new-r7-fixed.json
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/traversal_pose_cases.gd -- --report=/tmp/rama-motion-study/traversal-migrated-new-r7-fixed.json
```

The focused motion suite passes **39/39**. It checks exact 164-bone rest compatibility
and altered-rig rejection; 1,403 finite clip samples and positional loop seams;
release/hold/cancel ownership; actual finger/string/sole skin; locomotion and
traversal states; preserved mobile lower-body pose; rapid cycles; nonzero-aim
transitions; 30/60/120 Hz phase/aim equivalence; invalid inputs and reset.

The migrated traversal suite passes **34/34**. Historical `TraversalPose` behavior
is still exercised on its explicitly historical production hero. Current-player
checks use the new Rama controller, verify that it is the only pose owner, execute
flight/grapple modifier callbacks and verify pause/resume and finite transforms.
No historical component coverage was removed to accommodate the new player.

| Actual R7 measurement | Result |
| --- | --- |
| Right distal-finger mean nearest handle-surface gap | 0.230 mm across 2,382 sampled vertices |
| Maximum distal handle-proxy penetration | 1.429 mm; fixture tolerance 2 mm |
| String to nearest actual left distal-finger surface | 1.055 mm |
| Planted sole maximum clearance, forward 6 m/s | 0.571 mm |
| Planted support-skin maximum step, forward 6 m/s | 0.0514 mm per 60 Hz frame |
| Planted support-skin maximum step, side 4 m/s | 0.0217 mm per 60 Hz frame |
| Side-step midstance replants / crossed body center | 0 / 0 |
| Side-step maximum IK target error | 0.000435 mm |

These are bounded geometry/contact fixtures, not a guarantee of all terrain,
collision pairs, hardware frame rates or aesthetic quality.

## Actual rendered correction evidence

The owned-display runner completed both takes with current import validation,
source hashes, individually hashed PNGs, increasing real rendered-frame counters,
source snapshots and encoded H.264 movies. Rendering used Godot 4.6.3 Forward+,
llvmpipe, X11, Dummy audio, 640 × 640, at a staged 24 Hz sample clock. Each runner
cleaned up its own Godot/Xvfb processes before the next heavy worker started.

```sh
python3 games/yuga-native/art/hero-rama-motion/run_capture.py --output /tmp/rama-motion-side-r3 --display 145 --asset=res://assets/heroes/rama-hero.glb --side --shader-cache=/tmp/rama-motion-render-r2-user/cache
python3 games/yuga-native/art/hero-rama-motion/run_capture.py --output /tmp/rama-motion-render-r4 --display 145 --asset=res://assets/heroes/rama-hero.glb --full --shader-cache=/tmp/rama-motion-side-r3-user/cache
```

- **R3 side correction:** 118 frames / 4.92 seconds. Right frames 12–40, left
  49–77 and walk/stop 78–117 were inspected consecutively in sequence sheets;
  frame 25 was also opened at full size. The ivory fan/striped overlap is gone,
  the feet remain on their respective sides and the cloth remains continuous.
  Independent QA inspected the same sequences and confirmed the targeted repair.
- **R4 expanded full take:** 539 frames / 22.46 seconds. Owner review inspected
  ground frames 17–108 at every fourth frame, air/traversal 109–207 at every fourth,
  bow 208–265 at every second, abilities 266–338 at every third, cancellation
  339–367 consecutively, and grip/draw-detail 368–420 at every second. Full-size
  frames 47, 71 and 97 also checked forward-knee cloth and corrected strafing.
  Bow raising, cheek draw, visible string contact, arrow disappearance at release,
  followthrough and return read coherently. Flight tuck, grapple reach, circle
  palm gesture and landing compression remain distinct.
- The expanded take also contains three aimed primary cycles at 421–453, hit
  454–468, defeat 469–497, respawn 498–526 and settled idle 527–538. Independent QA
  inspected every frame of these reaction/retrigger ranges and full-size frame 488.
  It found no new snapping, disconnection or cloth tear: the rapid cycles retain
  bow-ready posture, defeat lowers and holds, and respawn rises continuously.

The durable archive is `docs/evidence/rama-hero/motion/`, with the complete R4
and R3 movies, capture JSON, real logs, source snapshots, both test reports and
representative PNGs. `selection.json` records the selected-frame mapping and
independently verified video frame counts. The complete raw-frame hashes remain
in each capture JSON; the full raw PNG sequences remain in the local capture paths.

Local source-bound artifacts are `motion-capture.json`, `rama-motion.mp4`,
`frame-*.png` and `sources/` inside each capture directory. Review sheets are in
`/tmp/rama-motion-study/`. R1 and R2, including R2's `REVIEW-LIMIT.md`, are retained;
they must not be relabeled as final correction evidence.

## Limits and next owner

This is real sequential rendered evidence with translated ground marks, reviewed
through consecutive or explicitly sampled frame strips. It is not a claim that a
human watched every frame at playback speed. The staged controller fixture is
separate from Confluence gameplay/input and projectile collision review, owned by
the combat/integration workers. It does not measure physical-GPU performance.

Motion and cloth remain stylized: the carrier torso is restrained, forward running
uses pronounced knee lift, and cloth is skinned rather than physically simulated.
The support solver uses the supplied floor height; independent per-foot terrain
raycasts and uneven-terrain acceptance are outside this change. These limits must
remain separate from the concrete corrected transition/contact/cloth findings.

Root/integration owns the final gameplay capture, evidence archiving, package
validation and milestone acceptance. Motion sources are frozen for that work.
