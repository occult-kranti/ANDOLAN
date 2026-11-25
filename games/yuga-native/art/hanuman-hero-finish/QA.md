# Independent Hanuman finish review

## First review · preserved baseline

The original Confluence model has 64,955 exported vertices, 105,848 triangles, 17 weighted draw surfaces, 167 joints and eleven clips. The editorial camera on the first Mountain Pulse pass cut off the raised gada. The revised shot preserves the full weapon and both feet. The finish brief called for a more compact muzzle, an articulated terminal brush and a layered nape with readable free tips. [Original model review](evidence/review-round1.json) · [Original motion film](../four-hero-motion/media/video/hanuman.mp4) · [Panel decisions](design/PANEL.md)

## Second review · sculpt and motion

The evaluated finish has 23,490 additional vertices and 37,584 additional triangles across 261 modeled hair locks. The existing face surface, eyelid and recessed lines move together inside a facial window. The largest position change is 6.72 cm. The 17 original draw surfaces retain their indices, skin weights and UVs. The four tail rotations in Mountain Pulse add recoil. The other curves, all animation input times, the original skeleton and the five gameplay ability clocks are preserved. [Model and packaged game comparison](evidence/review-release.json)

Blender evaluated five phases of idle and each of the five casts. At all 30 samples the gada grip remained effectively fixed in anatomical right-wrist coordinates. The sampled terminal brush tips cleared the head and torso by at least 15.37 cm. The crown tips cleared them by 2.35 cm. Nape endpoints reached 6.26 mm below the local skin surface and cheek endpoints reached 3.87 mm. A second pass included every anatomical head triangle so fine facial-bone ownership could not create artificial holes in the surface. One terminal-ring point per lock was examined. Close-up hair intersections between sampled phases and individual strand intersections require a separate continuous test. [Blender clearance measurements](evidence/review-clearance.json)

## Shipped controls and presentation

A real Chromium playthrough loaded the release HTML from its ZIP, switched offline, and passed 39 checks. A gada strike took the first guard to 56 HP, the ward supplied 48 shield, Lanka exposed a target after the sweep, Mountain healed the actor and defeated two guards, and Maruti left the ground and landed on the court. The browser recorded a live rig clip and joint pose for each action. It observed counts of 1, 2, 3, 4 and 5 following the distinct accepted results, verified that the victory dialog preserved 5/5 and then restarted to 0/5. It also exercised pause, reset after victory, resizing and the WebGL-disabled message. [Playthrough](evidence/drill-playthrough.json) · [In-game frame](evidence/drill-playthrough.png) · [Victory with all five techniques](evidence/coach-complete.png)

The ground-target check observes 18 rendered weighted surfaces on the 167-joint rig. Selecting Mountain Pulse showed a valid ring over the guard. Clicking beyond the 14 m cast range preserved 0/5 techniques, kept the charge ready and left the ability selected for another attempt. Escape cancelled the indicator and X then activated the ability. [Eight live input checks](evidence/finish-live.json) · [Landing preview](evidence/finish-live.png)

The registered face, front, rear and tail views show the grip and body silhouette in the same pose before and after the sculpt. The final portrait separates the copper hair ridges, eye catch and engraved gold armor against a cool backdrop. The grouped mane locks and smooth facial surface still read differently from the fine hair and skin in the painted target. The portrait crops part of the weapon to emphasize the face. The separate wide performance shot is the framing test for the feet, tail and raised gada. [Matched views](media/images/matched-studies.webp) · [Portrait](media/images/hanuman-beauty.webp) · [Frame-by-frame bounds](media/video/hanuman-framing.json)

The 768 × 432 Cycles film contains 97 distinct decoded frames at 24 fps. In the 42-frame full-body shot the entire deformed model stays inside the viewport, with minimum clearances of 7.89 pixels above and 25.13 pixels below. Relative distances between sampled joints vary by up to 52.68 cm in that shot. The two close-ups deliberately have tighter framing. [Studio film](media/video/hanuman-showcase.mp4) · [Independent presentation check](evidence/review-presentation.json)

## Reproduce

From the repository root, build the downloadable game before running the packaged checks. The Blender probe imports the actual exported file, measures the groom against the deformed donor anatomy and checks the attached gada head and grip in wrist space.

```sh
art=games/yuga-native/art/hanuman-hero-finish
python3 "$art/evidence/verify_finish.py" --output /tmp/hanuman-release.json
OPENBLAS_NUM_THREADS=1 blender -b -t 1 --python-exit-code 1 \
  -P "$art/evidence/verify_clearance.py" -- "$art/models/hanuman-enhanced.glb" /tmp/hanuman-clearance.json
node "$art/evidence/verify_live.mjs" --output /tmp
python3 "$art/evidence/verify_presentation.py" --output /tmp/hanuman-presentation.json
node games/yuga-rust/tools/test_browser.mjs --report /tmp/hanuman-playthrough.json --screenshot /tmp/hanuman-playthrough.png --coach-screenshot /tmp/hanuman-victory.png
```
