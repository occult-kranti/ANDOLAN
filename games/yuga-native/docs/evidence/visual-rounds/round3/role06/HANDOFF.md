# R3-06 — actual groom and cloth comparison

The full comparison is complete: **334 original framebuffers and 167 matched
pairs** across eight capture groups. `archive-audit-final.json` verifies every
original, producer log, archived harness and 1,330 unique frozen source paths.
All captures have unchanged source pins, successful native exits and warning-free
render logs. This role does not promote runtime assets.

## Original evidence

Each branch (`baseline` and `candidate-r7`) contains these raw 1280×960 Forward+
framebuffers, complete reports, producer logs and exact producing harness:

| Directory | Originals per branch | Purpose |
| --- | ---: | --- |
| `stills` | 8 | Light/dark stone, front/profile/rear, close/fullbody, night and ordinary gameplay |
| `diagnostic` | 3 | Rear/profile rest and source-bound Measured Step recoil shoulder witness |
| `continuity` | 150 | Adjacent normal-runtime movement, two public ability releases and reset |
| `actions` | 6 | Five public ability phases and a matched reduced-effects Volley |

The `*-comparison.json` files compare exact camera, lighting, final pose, facial
state, LOD, ground, velocity, render settings and secondary dynamics. Authored
anchored/masked groom vertex counts are intentionally different; they are
explicitly excluded from the dynamics comparison. The continuity control
receipt lists the four changed count fields rather than declaring entire reset
reports identical. Ability events and all other sequence controls match.

The two MP4s are review conveniences derived from the 150 original PNGs. Each
contains five seconds at 30 Hz; capture rate is not measured hardware FPS.
No ordinary-speed human playback review is claimed by this role. The inherited
generic capture scope still mentions the old R2 1.2-second take; mode, counts,
clocks and MP4 metadata establish the actual R3 duration without rewriting old
producer receipts.

## Source identity and imported resources

The runtime baseline is promoted R2 commit
`6046171a5ae53e1b1a9777c0ee0011e2ebf1dc95`.
`baseline-source-check.json` verifies all 505 tracked runtime files against it;
two generated UID files are separately pinned. Ongoing UI work, historical
evidence, `.git` and editable duplicates were excluded from the lean snapshots.
Baseline stills/continuity use `capture-baseline-project-r1`; diagnostics/actions
use `capture-baseline-project-r2`, whose only changes are capture tooling.

The final rendered candidate is
`/workspace/scratch/visual-round3/capture-candidate-project-r2`. Its exact six
runtime deltas are in `imports/r7/candidate-overlay.json`:

| Runtime file | SHA-256 |
| --- | --- |
| Near GLB | `8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c` |
| Mid GLB | `d95a061e2243477afc0227bf52564252fbcb20cb039d303ad10292ea5d85beed` |
| Far GLB | `ee2e35278ce49efdda6751850fddbb8f1b4de99ad019e6992c10e7702dc6317c` |
| Woven roughness PNG | `eec110e598ac1a2fa95fb5899fac5fc314a191bff8e670547d79dfaf1468e500` |
| Woven import descriptor | `646c1b220662472d42a56884d8a1b51bddb625724b6de53d9f61cbf621109c24` |
| Secondary ownership script | `2b8e467df254dcda175694ab988071f24b41ddaa93275f5cbb9768abcb143f34` |

The script is root-approved teardown ownership correction only; active response
is unchanged. All lighting retains accepted R2 zero-angular shadows and .2/.35
bias. The optional normal-transport shader is deferred. The comparison combines
groom and cloth changes and does not attribute every changed pixel to one.

The actual serialized import receipt binds all three PackedScenes and woven
texture resources to their source hashes/MD5s. The loaded cloth probe passes
**11/11** checks: actual 1024² texture, ten mip levels, preserved linear scalar
samples and RED-channel binding. Cloth specular stays .38. One import-time
capture-probe UID was regenerated with a warning; render logs are clean.
The earlier R6 stage/import/editable remain historical and are not relabeled R7.

Actual Blender 4.3.2 import/save/reopen produced the R7 editable with 164 bones,
nine actions, four morphs, 17 packed images and 16 hidden guide curves:
`940c8208d8f5ee8c2e8dd9e4bea2d9893450026189f1a4eb24cd0b1874378f25`.
Inspection SHA is
`9af85ce316cc3a270ef62bef98ad4b203218c6f29a5a27c81dc6d4af8d28e031`.
Both inspection and producer log are under `imports/r7`. This is an editable
import with guide controls, not a recovered original modeling stack or a tested
Blender roundtrip export.

## Actual controls and limits

The corrected role12 gallery contract is pinned as
`f7aa21bc6806dc0d11fc6e9bdea87a0e6c8136dc62649089fcb89bcde99ade41`.
Native rays hit deck y=.4399999976 m with actor clearance .0000999868 m. The old
y=.05 m station was not rendered. Opened dark originals show the head over
indigo stone and feet on the raised deck; this is not a foliage background.

Every frame projects actual visible imported vertices, inverse binds, live
morphs and alpha-squared secondary offsets using final bone globals observed
inside `SkeletonModifier3D.modification_processed`. The gate requires a 24-pixel
border and records the exact rig/world transform. Framing is not occlusion or
collision proof. The initial procedural-mesh preflight failure is retained with
its log and harness; the corrected preflights passed.

The continuous takes have consecutive render frames, exactly two physics ticks
per sample and 48 distinct actor positions. They contain real Kodanda and
Measured Step releases, actual movement and reset; no stored poses or spring
states are injected. Maximum offsets match at 56.65 mm cloth and 16.03 mm hair;
cloth returns to zero after reset. The separate paused recoil witness reproduces
all 164 source pose matrices within 4.9e-15 using the public cast and explicitly
staged army/player updates, not stored matrix assignment.

Action shots retain the real native Target03 aim ray, public cast/generation,
authority phase, actual release count, full hero bounds, receiver bounds and
visible warning bounds. Normal/reduced Volley authority age is .9 s; its actual
presentation age is .933333 s in both cases. Their exact pose/camera/light/aim
match, while separate reset/generation and administrative counters differ.
Reduced effects changes visible effect triangles from 858 to 390.
`action-receipt-check.json` passes all twelve originals and confirms exact
baseline/candidate cast receipts and ability events. All six candidate action
originals were opened; the hero, receiver and relevant visible warnings remain
in frame. Independent reviewers own final occlusion and quality judgments.

Initial capture/import work used CPU2,3 with two llvmpipe threads. Root later
assigned the heavy lane CPU0,1; the in-flight still capture's successful affinity
change is separately recorded, and later continuous/action/Blender jobs use
CPU0,1. No command reports simulated capture rate as real performance.

Independent role15/root approved the full comparison after opening the three
diagnostic pairs. Rest groom mass/flow and cloth response improved in that
bounded review. Recoil hair still tucks into or behind the collar without a clean
gap, and stressed secondary intersections remain open. No collision-clearance,
motion-quality, commercial-parity or default-promotion claim follows from these
capture checks. Independent role11/15 final pixel review and role14 final source
proposal remain separate gates owned by root.

The sealed role14 R7 proposal was then reconciled against this rendered candidate.
`proposal-reconciliation.json` passes all five proposed runtime files, three
preserved runtime dependencies and four actual imported resources/descriptors.
Its promotion-manifest SHA is
`394ffea43f8c7f79ce911e7d0c3c8b9428c4ffa571c0aeca6bdf1e4e32478ff5`.
There is no runtime metadata difference, no new import requirement for this
reconciliation and no relabeling of old capture identities. Root still owns
independent source/art disposition and promotion.

`NEXT_MOTION_TAPE.md` is an unexecuted R4 reuse sketch. UI5's frozen all-screen
capture has the next heavy-lane priority. R4 must use accepted exact source pins;
any metadata-only proposal difference needs explicit payload/import reconciliation
before reuse and must not silently rewrite these capture identities.
