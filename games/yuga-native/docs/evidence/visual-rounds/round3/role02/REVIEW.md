# R3-02 groom and cloth camera handoff

Source commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. This role owns only
this evidence directory and `/workspace/scratch/visual-round3/role-02`.
No default runtime, shared ledger, imported asset, renderer or commit was changed.

The bounded contract is eight matched originals per source plus one five-second
continuous runtime take. `capture-contract.json` supplies exact camera/player
coordinates, yaw, lights, state invariants and controls. The existing visual-rounds
CLI does not yet consume it: sole heavy owner 06 must stage an isolated capture
adapter and run its actual imported-vertex projection gates before rendering.

## Actual originals inspected

Four original R2 PNGs were opened with `view_image`; exact hashes and observations
are in `reviewed-originals.json`. The old foliage station is sky/sea/architecture
around the head. The frontal and profile face crops exclude most garment and the
profile also truncates the nape. The rear gameplay reference shows both long
cobalt panels, whose broad shiny fold streaks are visible. The profile original
also visibly establishes that the existing gallery indigo panels are dark.

## Replacement dark context and bounds

Use existing courtyard east wall, hero `(19,.05,-1)`. Dark close cameras are
`(17.4,1.11,-1)`, aimed at `(19,1.61,-1)`, vertical FOV 38 degrees. Front/rear/profile
visual yaws are -90/90/0 degrees. This slightly low view puts the complete projected
head against the existing elevated indigo inset rather than its sandstone plinth.
No world decoration is added. This is **dark indigo stone**, not a claim to have
closed the separate dark-foliage requirement.

All 36 perimeter ray samples, 12 px outside the union baseline/candidate head
rectangle, first hit `Indigo_glazed_stone` for all five dark shots; no sample hits
foreground geometry. Both light shots first hit `Warm_carved_sandstone` at all
36 samples. Earlier eye-level and panel-edge attempts were rejected and retained
in role-02 scratch because only 11–23 of 36 rays reached indigo. Moving along the
existing panel to z=-1 resolved its edge coverage; a center ray alone was not used.

The verifier skins actual source vertices with the previously captured runtime
`rest` pose and original inverse bind matrices, then applies each player transform.
It projects all principal hair (including topknot), face, central head/neck,
both cobalt cloth surfaces and ivory. Fullbody includes every hero/weapon vertex.
The candidate has 54,285 head-group vertices and 46,077 cloth-group vertices.
Recorded-pose candidate bounds are head y=1.330784–1.793604 m, cloth
x=-.435391–.438919, y=.036940–1.713876, z=-.332929–.462843 m.
These are posed source coordinates, not new imported runtime measurements.

Candidate head rectangles at 1280×960 are front `(473.40,288.27)` to
`(806.68,674.96)`, rear `(462.85,297.63)` to `(827.51,664.31)`, and profile
`(477.59,294.80)` to `(829.63,672.77)`. Light fullbody is `(491.80,239.55)`
to `(788.28,806.13)`; dark fullbody is `(487.95,240.35)` to `(788.75,797.42)`.
All 14 baseline/candidate required projections pass the 24 px border. These
are numerical prechecks; the eighth ordinary-gameplay view retains its exact
R2 recorded camera and must receive a new actual imported fullbody check.

## Reproduce and execute next

Executed successfully:

```sh
python3 games/yuga-native/docs/evidence/visual-rounds/round3/role02/build_fixtures.py
```

This uses NumPy, the committed GLB reader, local scene-ray utility and pinned R2
runtime matrices/R3 groom-r5 scratch inputs. `geometry-verification.json` pins
all source inputs and contains every ray hit and baseline/candidate projection.
The builder is retained here; scratch contains contract construction and rejected
station evidence. No Godot or Blender job was run by this role.

Next owner: 06, then R3 groom/material reviewers. Inspect original new pixels,
verify runtime placement/collision, repeat projection on actual imported current
pose plus shader offsets, and run the continuous input/cast/reset sequence.
Do not accept a face-only projection gate for hair or cloth. The existing harness
must save consecutive raw frames, source hashes, input/events, actual transforms,
LOD, pose and secondary state. Reject missing action events, reset failures,
framing loss, occlusion or a wrong visible backdrop. Camera geometry does not
prove shaded contrast, artistic quality, weapon clearance or hardware FPS.
