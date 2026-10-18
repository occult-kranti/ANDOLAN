# G1-06 — independent graphics baseline and capture admission

**Baseline reviewed; capture tooling ready. Current G1 art is not yet visually accepted.**
This worker directly opened eight unmodified published-package originals, read
their full state receipts, inspected the current capture/source paths, and made
verification-only additions. No Godot process, import or new render was started.
Root owns the next source freeze and sole heavy lane; G2 remains a separate
assignment. [Baseline pins](baseline.json) identify each original and JSON hash.

The published baseline is source `9e81a7c849837dea477ddb5a8c93f43665774573`,
Linux ZIP `56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5`.
The review checkout began at `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c` with
other workers' G1 changes in progress. Old pixels are not images of those changes.

## Actual baseline observations

| Original opened | Visible finding and acceptance question |
| --- | --- |
| [Published title](../../ui-campaign/I3/role03/native-r1/01-package-title-idle-a.png) | Indigo cloth, warm metal and cream garment identify the hero; focused primary and selected mode remain distinct. Face/torso read as broad planes, and the feet visibly separate from floor/shadow. Does a candidate improve surface/light breakup while preserving the silhouette and exposing, rather than concealing, the support gap? |
| [Bow training](../../ui-campaign/I3/role03/native-r1/04-package-training.png) | Rear hair reads as a solid cap, cloak as large patterned sheets. Arches/domes give the courtyard identity, but the pale floor and repeated wall bays dominate. Test rear/profile under light and dark backdrops, not only a flattering front portrait. |
| [Live ordinary world](../../ui-campaign/I3/role03/native-r1/08-package-world-live.png) | Nearby troops are simple straight segmented figures with broad torso/shield blocks. Team identity is clearer than role identity. Streets are large pale slabs, buildings repeat window modules, and peripheral cards contain tiny text. Can melee/archer/standard silhouettes be distinguished at ordinary distance without health bars carrying the entire distinction? |
| [Staged street](../../ui-campaign/I3/role03/staged-r1/S01-STAGED-lane.png), [staged contested relay](../../ui-campaign/I3/role03/staged-r1/S03-STAGED-contested-relay.png) | Route space is unobstructed but visually sparse; warm/cool facade variation is overwhelmed by similar module size and pale ground. These arranged authority states do not establish a populated fight. Test route/landmark readability alongside actual marching units and distant threats. |
| [Scripted film](../../ui-campaign/I3/role03/native-r1/06-package-film.png) | Wide camera leaves both actors small with a large unoccupied court. This is the separate authored duel film, not proof that playable hero animation is smooth. No temporal judgment is made from this still. |
| [Guide](../../ui-campaign/I3/role03/native-r1/P04-world-guide-loaded-preferences.png) | Selected ability, enabled toggles, focus ring and Back action remain clear. The backdrop is strongly dimmed. Preserve those distinctions when changing theme/material intensity. |
| [Native night pause](../../ui-campaign/I3/role03/native-r1/P05-world-muted-sound-and-return.png) | Actual `night=true, phase=1` is recorded. Visible world areas cool to blue; the central pause panel hides the hero and main street. This cannot approve unobstructed night hero/background separation. The fresh native plan explicitly closes that missing view. |

The originals use a 960×600 native window and a 960×540 framebuffer. Auxiliary
HUD/map/ability captions are roughly 8–9 physical pixels (11–12 logical): containment
passed earlier, but comfortable readability remains open. The title original has
initial shadows enabled; the later training/world views follow native preference
edits including saved `shadows=false`. The world has its own lighting owner. Fresh
default-settings captures must disclose that difference, not claim identical
lighting simply because image sizes match. A still can show separation, but it
cannot measure skating, contact duration, perceived smoothness or frame rate.

## Questions carried across G1–G6

| Owner | Required visual/behavior check | Counterexample that prevents acceptance |
| --- | --- | --- |
| Hero | Same front/rear/profile/full-body camera; dark and light backdrops; existing gold relief and cloth identity; moving highlight stability in a later continuous take. | Plastic hair lobes merely darkened, gold detail lost, high-frequency shimmer, changed crop or lighting used to hide defects. Roughness-map arithmetic is not a pixel result. |
| World | Actual ordinary camera day/night, route edges and district landmarks, near/mid/distant threat retention, ground joints while moving. | Haze obscures distant enemies, darker paving loses the hero, added detail blocks sightlines or produces crawling edge noise. Empty staged street is insufficient for combat clarity. |
| Motion | Same-clock start/stop/turn/cast entry, early cancellation, warm retrigger, repeated cancellation, exact release and pause/overview hold/resume. Observe final rig in `modification_processed`. | Smooth-looking stills hide an entry snap, second cancellation rescales an already-fading layer, pose drifts while authority is frozen, or feet/body contact is measured in different update phases. Existing support/garment gaps remain open. |
| Screens | Critical objective, stock/cooldown and pause cue at native 960×540; keyboard focus/selected/disabled states against actual hero/day/night backgrounds. | More ornamental copy competes with objective, focus disappears, smaller text is accepted because no bounding box clips, or changed Back/scroll behavior breaks the actual input plan. |
| Units | Both teams and all three infantry roles at ~5 m and ~15–25 m, actual march→attack→death/pause, then detail transition across 38–46 m in both directions. | Role identity exists only at close zoom; shared rigid poses or bow/string separation; a visible projectile appears during nocking before the authority impact. The units owner reports the latter as a known G2 issue, not independently reproduced here. |
| Independent acceptance | Match source, cache, camera, stage/native classification and raw original bytes before comparing. Keep rejected runs. | Old published images stand in for new source; staged cameras become a native-play claim; numerical checks substitute for opened pixels; compressed video replaces primary PNG/JSON. |

## Reusable capture workflow actually built

[Runbook](../../../../tools/graphics-six/README.md),
[snapshot tool](../../../../tools/graphics-six/snapshot.py),
[native input plan](../../../../tools/graphics-six/native-plan.json),
[explicit hero camera contract](../../../../tools/graphics-six/hero-camera-contract.json).

One independent source copy (~180 MB) plus an initial compiled-import store
(66,259,142 bytes) is reused. Refresh checks the prior seal, preserves only displaced
source versions, content-addresses immutable compiled imports, verifies raw input
MD5s and rereads source/cache hashes after copying. No mutable canonical cache is
hardlinked. Every round keeps a fresh full receipt; raw screenshots need no copied
project per take. Root alone serializes refresh/import/render and retains the
store until its recovery route is archived. Changing importer settings still
requires root's actual import receipt; MD5 matching raw inputs does not prove that.

Two concrete existing harness limits were found and addressed in this plan:

1. `capture_groom.gd` requires `groom_contract.json`, absent from canonical tools.
   The snapshot admits an explicit JSON-only overlay derived from the archived
   corrected r6 camera contract. It preserves all eight 1280×960 views without
   importing its old runtime acceptance claims or copying large old freezes.
2. Native pointer geometry settlement exists only in package mode. The new
   integrated plan uses real Tab/Return and current observed focus, then native N
   and actual night phase predicates. No product navigation method is invoked.

The first fresh native take requests four originals: title day/night and live
world day/night, then returns and exits through native Quit. Its army clocks
continue, so day/night captures are contextual views rather than equal-population
temporal comparisons. The hero pass retains eight existing staged review-camera
views, including front/rear/profile/full-body. Preserve its 1280×960 framing; a
960×720 substitution would change the historical comparison contract. Exact
copyable commands, fresh paths, display IDs, thread limits and pre/post `verify`
are in the runbook. Root received them before this report was sealed.

## Executed validation and primary references

`taskset -c 3 python3 games/yuga-native/tests/graphics-six/test_snapshot.py`:
**18/18**, exit 0, [full log](snapshot-tests.log). Cases include changed/deleted
source retention, added/tampered snapshot refusal, stale/missing imports, new
unimported images, compressed texture sidecars, canonical/store inode separation,
cache mutation, no-write dry-run, path/receipt protection and JSON-only overlays.
No engine or rendering is involved in these tests.

The actual immutable I1 source was inspected with the final snapshot dry-run:
**910 files, 173 import descriptors, 66,259,142 compiled bytes**, no snapshot/store
created ([receipt](snapshot-dry-run.json)). This exercises the real existing
cache inventory; it is not the new G1 source freeze. The native runner accepted
the new plan with `--dry-run`, two render workers and the requested dimensions
([receipt](native-plan-dry-run.json)); live input remains pending root's take.

Three exact official Godot XML references were freshly downloaded with normal
TLS from immutable commit `35e80b3a8822a9df9be390814b62f44c0a9c69e8`.
[Source hashes and selected excerpts](research/sources.json) retain the bounded
reading scope. Useful implementation guidance was sent to owners:

- `BaseMaterial3D`: roughness texture multiplies the scalar; grazing texture
  stability depends on filtering/mipmaps; normal maps require normals **and**
  tangents. The hero owner confirmed its mapped scalar is 1.0; pixels remain pending.
- `GeometryInstance3D`: range margin is hysteresis when fade mode is disabled,
  not a visual fade. The units owner corrected the new helper's language and
  retained an explicit near-detail cutoff; both directions still need pixels.
- `SkeletonModifier3D`: read final modified poses during `modification_processed`;
  the skeleton applies modifier influence. Existing capture callback timing is
  preserved instead of comparing restored public poses to rendered vertices.

No Blender document, commercial model, texture or animation was downloaded or
newly reviewed. Official API reading guides experiments; it is not art approval.

**Disposition:** G1-06 baseline/research/tooling work complete. No new runtime
quality claim, heavy render, hardware FPS, Windows execution, online gameplay or
commercial-art parity is established. Root captures the frozen G1 candidate;
worker06 will independently review its originals and counterexamples in the next
assigned round. The source/evidence artifact hashes are in [verification.json](verification.json).
