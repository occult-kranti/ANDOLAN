# S3 W5 actual matched motion comparison

The candidate improves sampled floor clearance, but **smoothness remains limited**: the first grounded close-up contains a visible upward foot correction. This packet preserves all320 lossless originals, complete final-modifier receipts, four native-cadence viewing videos and both matched control comparisons. It does not promote a further runtime change or supersede the strict25/27 native comparison in [S3 W5](../W5.md).

## Exact source and execution

Both branches use the same recovered current presentation, accepted R7 imported hero, fixed camera, lighting, shader/material settings and old common ability-effects source. Only the motion source and its snapshot marker differ: baseline `119db2e65a40c148725813137340bc109f057d98ea82ef777ab7735c999c661c`, candidate `8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8`. These are not exact historical S2 art snapshots, and this is not validation of the newer Volley effect fix.

The engine is the unmodified public Godot4.6.3 source-built template-debug executable, SHA `dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f`, using Vulkan llvmpipe/Forward+,1280×960 and the recorded MSAA setting. Each run receives fresh private copies of the same112 Godot and101 Mesa cache files. CPU0,1 affinity and LP2 bound execution; no unsupported Godot worker-pool flag is used. Fixed sampling rate is not wall-time or physical-GPU FPS.

| Take | Actual physics/render Hz | Originals | Native gates | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
| Landing baseline |120/120|40|6/6|108.537|
| Landing candidate |120/120|40|6/6|110.034|
| Full baseline |60/30|120|8/8|220.547|
| Full candidate |60/30|120|8/8|210.302|

Every run exits0 with clean engine diagnostics. Exact commands, watchdogs, private cache inventories and engine/runtime pins are in [render-inputs.json](render-inputs.json), [runner-derivation.json](runner-derivation.json), [ready-render-commands.txt](ready-render-commands.txt), and each branch's original `run.json`/logs. The former preparation runner's missing PATH Xvfb and120s watchdog were identified before launch; this separately recorded runner supplies the verified runtime Xvfb/lavapipe paths and600/900s bounded watchdogs. No quality, frame count or rate was reduced. The final candidate viewing video was encoded later on CPU4 with one FFmpeg thread after releasing the raster lane; each archive records its actual encoder command.

## Whole-tape controls and contact

[Landing](landing120-comparison.json) and [full](full-comparison.json) each pass41/41 source/control predicates. These compare every frame's camera/light/render settings, source/import pins, nonleg transforms, body/root/capsules, velocity, kit and army clocks, action/event state, traversal, fixed world plant targets and native physics/draw adjacency. They are identity checks, not a motion score. The inherited field named `foot_targets_rig` contains world-space targets; its raw spelling and data are preserved.

| Take | Grounded minimum sole, baseline → candidate | Grounded side samples below−5mm, baseline → candidate | Boolean locked side samples |
| --- | ---: | ---: | ---: |
|120Hz landing|−11.350408→+0.016164mm|12→0|30→30|
|30Hz full-body|−37.247092→+0.490857mm|13→0|102→102|

Measurements use the actual imported active near/mid skin in the final modifier callback and real ray-hit support, not ankle-only estimates or the decorative floor rim. Neither locked counts nor a scalar minimum establishes full sole support or no sliding.

The close pair's first grounded edge is original007→008, physics46→47,8.333ms. The baseline peak ankle step is4.889086mm downward; the candidate peak is7.323952mm upward (+2.434866mm). Candidate right-ankle displacement is(+0.006154,+7.323943,+0.009537)mm, projected6.484344px. The separately projected lowest right-sole point moves upward6.797px. Projection is not tracked image-edge motion. The actual render's callback counters differ from the earlier headless preflight; no absolute preflight index is transferred.

The full-body global maximum includes the public reset's4.534m world relocation in both branches, so it is not a smoothness metric. All rows remain in the comparison rather than hiding that reset. The existing strict25/27 failures—including the60Hz unlocked run/strafe swing-step increase—remain open.

## Direct visual scope and sequence limits

W5 directly opened landing009 in both branches and full001/018/047/094/095/119 in both branches, plus baseline full035:15 originals. At the ordinary wide framing, foot placement differences are small; sampled upper-body composition remains stable. The close landing image shows a more exposed toe/sole, but the adjacent correction needs temporal repair. W5 has not claimed human normal-speed video playback or inspection of all320 images.

The independent [W1 sampled landing review](../W1-landing-sampled-review-r1/REVIEW.md) directly opens007/008/009/039 in each branch and verifies all80 landing PNG identities. It finds improved settled contact with an upward correction visible across adjacent close frames, dispositionLIMITED. Its sealed review SHA is `73ccd5a36a0bf9cb48c834dbefadb1e2d51723532442c8dce9ea75e77a6eb2d8`, receipt `3fa51e7a490c57491a39a5c1505e5ae53bca3dd7db775ffc688d9c8d9ab31914`. W1 separately opened the six full-body001/018/047 originals; that does not constitute a whole-video review.

The full sequence supplies start/training descent, brief walk→run, moving public reset, jump/land and final settle. Actual gait rows show walk only15–16, run17–44; reset45 clears movement, and frame65's scheduled release occurs during idle. **Sustained walking and a natural run→stop are missing.** It contains no turn, cast/cancel, pause/resume or earliest drawable title acquisition. API/Input fixture controls are not native XTest or physical-controller play. The landing close view intentionally crops the upper body; it has useful sole pixels but does not prove ordinary-camera salience.

## Portable artifacts and next action

Each branch directory has byte-exact PNGs and raw logs; `capture.json.gz` preserves the complete raw JSON with deterministic mtime0 and both raw/compressed hashes. `normal-speed.mp4` is a lossy viewing aid at the recorded120/30Hz cadence, without interpolation; originals remain authoritative. [verify_archive.py](verify_archive.py) rechecks every stored byte binding and comparison input without temporary paths or an engine. [archive-verification.json](archive-verification.json) records that replay; the artifact manifest inventories the final packet. Temporary originals remain until the parent verifies the remote checkpoint.

The next bounded experiment should address the visible first-ground correction before broader motion acceptance: investigate nearby measured support during descending presentation, preserving root/capsule/authority, existing locks, elevated floors and interrupted descent/reset/flight behavior. No stale world-y0 plane or altered authoritative clocks are acceptable. The existing source pair and all failed strict checks remain immutable. Any successor needs the same numeric gates and a distinct matched visual review; no further raster is authorized until the shared W1 queue releases it.
