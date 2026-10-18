# R4-02 existing-surface ground and camera fixtures

Source commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Three bounded source
fixtures are specified and checked in `ground-fixtures.json`: central-courtyard
start/stop/turn, an actual raised-gallery jump, and landing on Confluence's
existing 8 m sun-lift-west deck. No scenery, collision, motion or camera runtime
was edited. Actual capsule/input/landing execution remains for the capture owner.

The central floor collision is the existing box top y=0. The gallery support is
source triangle y=.4399999976, confirmed by a downward ray; player start is
support+.0001. Confluence declares a base-centered8×8×8m box at(-20,0,-88),
whose top is y8. Its staged start(-20,9.5001,-88) is explicitly an initial1.5m
fall, not a claim that an input moved there. All expected upper-face normals are
(0,1,0); these do not test sloped ground. Actual runtime collider identity and
normal must be recorded rather than inferred from visuals.

The central route is sampled every.25m through(0,12)→(0,6)→(3,6)→(3,9).
The actual take uses input and threshold observations, not root-position writes.
Source collision broadphases find no above-floor COL triangle overlap. Minimum
remaining edge clearances after the actual .29m capsule radius are12.71m central,
1.705m gallery and3.71m deck. Neither a sampled route nor these distances are
native collision sweeps. Other live agents, warnings and dynamic blockers remain
runtime observations.

The common review camera tracks actual horizontal root position only, at
relative(0,2.4,7), looking at relative(0,1.7,0), FOV52 at1280×960. Camera Y stays
relative to the fixed support surface so floor and jump remain in view. A
conservative±1m horizontal,0–3.6m vertical hero/weapon/jump envelope projects to
(471.79,178.73)–(808.21,763.89), passing the24px border. The earlier shorter camera
cropped the airborne envelope and is preserved in `rejected-camera-envelope.json`.
Twelve source scene rays per sampled courtyard position, at foot/head/airborne
heights and left/right edges, find no foreground visual geometry. Confluence's
new camera still needs actual world-geometry/viewport occlusion review; its
native deck/landing square contract alone does not prove pixels.

Source jump speed7.2m/s and gravity18m/s² give an ideal continuous apex1.44m and
return time.8s. These are analytic references, not fixed-step physics results.
The receiver must log actual capsule trajectory, first contact collider/normal,
final SkeletonModifier3D pose, all selected sole distances, immutable planted
anchors and drift/release state, fullbody projection and spring-arm shortening.
A true `foot_locks` boolean does not prove visible sole contact.

Executed successfully:

```sh
OPENBLAS_NUM_THREADS=1 python3 games/yuga-native/docs/evidence/visual-rounds/round4/role02/check_ground_fixtures.py
```

All three source fixtures pass the stated route/envelope checks. No Godot,
Blender, import, render or actual input run occurred in this role. The accepted
controller remains the original; role05's rejected continuity candidates are
not mixed into these fixtures. Next owner: root/06 for the integrated R3 asset
and actual uninterrupted R4 runtime captures.
