# R2-02: source-pinned face contexts

Executed on native source `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. The reusable [fixture data](context-fixtures.json) fixes three existing scene contexts, two camera scales and day/night endpoints. [Geometry verification](verification.json) records the actual imported mesh intersection and collision clearance checks. This artifact selects and verifies coordinates; new rendered acceptance belongs to R2-06.

| Context | Hero feet request, metres | Visual yaw, degrees | Existing background |
| --- | --- | --- | --- |
| Light stone | `(-20, .05, 14)` | `180` | Confluence `block-1`, temple sandstone; wall begins at z19 |
| Dark foliage | `(-54, .05, 0)` | `18.627274488929288` | Confluence west mangrove `coast-nature--1-0` at(-75,0,-10) |
| Indigo/gold | `(12, .05, 10)` | `187.56176418381568` | Courtyard's existing indigo and aged-brass lamp/gallery at(14.7,0,12) |

The JSON contains literal world-space close and gameplay-scale camera positions and targets. Close FOV is32 degrees; the wider frontal review is65 degrees, four times farther along the same ray. The wider view is a review camera that exposes the face at gameplay scale. The ordinary player camera points at the hero's back and does not validate frontal face separation.

Coordinates are Godot metres: +Y up, hero forward+Z at visual yaw0; positive visual yaw rotates+Z toward+X. `player.visual.global_rotation.y` is distinct from the controller's `player.yaw`. Confluence's `teleport_to(position, visual_yaw_degrees)` sets the former and derives the latter. The original close camera offset `(-.64,.04,-.62)` is authored relative to visual yawPI; rotate it by `visual_yaw-PI`. The foliage fixture deliberately uses vertical offset`-.08` to reach canopy behind the face. The earlier camera-bearing value64.53665 degrees is **not** the visual yaw and must not be used.

The fixed target height1.7522m is near the historical head+.075 target. If R2-06 retains its head-bone-derived target, it must record the resolved camera and pose, then reuse those exact values across matched sources and phases. Do not present the literal-target and bone-derived variants as a matched pair without checking their matrices.

I inspected the original full-size final courtyard day/night anchor frames and the accepted-bias Confluence day/night closeups using `view_image`; all four source image hashes and observations are in the JSON. Courtyard anchors leave the face largely against sky, so they do not by themselves establish light-stone or foliage separation. Confluence's historical closeups show architecture and visible residual ear/neck stippling. They are historical references, not new Round2 frames.

The offline verifier reads the current indexed GLB triangles and checks camera-to-face segments plus the background center ray. The stone ray first reaches `Confluence_honey_sandstone`; the foliage ray reaches `leaf_copper_green`; the courtyard ray reaches `Aged_brass`. All16 Confluence solid/deck boxes clear the0.65m hero radius at the selected points. Both close and wider camera-to-face segments are clear in the imported meshes. Center rays do not prove that the whole face silhouette sits against the intended background; R2-06 must inspect the raw frames for canopy coverage, foreground overlap and clipping. The courtyard context is mixed indigo/brass/stone, not a uniformly blue backdrop.

Keep the source scene, architecture, collision, world materials, practical lights, shadow settings, exposure and phase endpoints unchanged. Hide the existing title portrait fill for training views. Both lighting systems retain shadow depth bias.2 and normal bias.35. Their sky reflection remains active, while SSR, SSIL and SDFGI are disabled; these frames do not prove physical colored bounce from a nearby wall. Preserve the original indigo/gold costume and jewelry as local color boundaries in every view.

R2-06's bounded initial capture is14 frames per source:10 courtyard baseline views plus the two Confluence closeups in day/night. The additional courtyard indigo/gold station and wider frontal context views are specified but outside that initial subset. Their capture/acceptance remains pending. All static fixtures are paused, HUD-hidden review views; they make no claim about live HUD values, input, continuous animation, performance or completion of Round2.

Verification executed: `python3 /workspace/scratch/visual-round2/role-02/build_fixtures.py` after reading current GLBs with the accompanying `verify_context.py`. Three source geometry checks passed. No Godot import, render, runtime-source edit or asset modification was performed. The scratch directory retains the exact verifier and builder; source pins cover16 scene/script/asset inputs. Next owner: R2-06 for actual framebuffer coverage and rejection of unsuitable crops, then independent art reviewers.
