# Rama gameplay capture — accepted R3

[Watch the five ability takes](rama-five-abilities.mp4). This recording uses source commit `9eb6323ef20d8f10436a893ffcd434096686247a`, the final R7 hero and the actual Confluence runtime. It contains 363 consecutive rendered samples across five deliberate fixture takes, lasting 12.1 simulated seconds at 30 FPS. The normal 60 Hz physics and 20 Hz army clocks remain authoritative.

| Take | Frames | Authoritative releases | Observed result |
| --- | --- | ---: | --- |
| Kodanda | 0–44 | 1 | First enemy loses 28 HP; one damage receipt. |
| Piercing Dawn | 45–98 | 1 | Three enemies each lose 70 HP; three receipts. |
| Measured Step | 99–119 | 1 | Actual player movement through the swept CharacterBody receiver; no damage. |
| Guardian Circle | 120–287 | 1 | Ally heals 70→115 HP; Rama heals 240→285 HP; both receive 55 shield, then lose the owned shield at expiry. 182 shield/heal receipts. |
| Dawn Volley | 288–362 | 1 | Three paced arrows each deal 82 HP to their staged receiver; three damage receipts. |

All five casts reach normal gameplay and presentation expiry. The video preserves preparation, release/contact, recovery and cleanup. There are 25 separate stills: fifteen game-camera ability states, six low-angle replay states, one reduced-effects/reduced-motion state, and actual hit/defeat/respawn states.

The final Guardian sequence resolves both rejected recordings. Decoration fades before expiry. Frame 270 retains the exact gold boundary, field-active notice and +55 shield while authority remains at 5.00 seconds. Frame 271 reaches authority 5.05 seconds: boundary and recipient geometry disappear, shield becomes zero, and the same rendered frame shows “Rama is ready.” Frame 287 has no retained effect. [Critical expiry images](guardian-expiry/) and the per-frame `truth` records preserve this comparison.

The runner passed source and PNG hash checks, one release per take, natural expiry, exactly two physics ticks per frame, every-frame notice/shield/boundary agreement, 363 encoded video frames and a full video decode. All 355 source hashes match before and after capture and matched the checkout during archival. The Godot log has no script or engine error; Godot and Xvfb exited cleanly. [Run receipt](capture-run.json), [complete event/source/frame report](rama-gameplay-review.json), [video metadata](rama-video.json), [owner review](owner-review.json) and [archive manifest](manifest.json) are retained.

Owner review covers every frame of Kodanda, Piercing Dawn, Measured Step and Dawn Volley, plus full-size critical Guardian, release/contact, low-angle, reduced-effects and lifecycle images. [Independent QA](../qa/final-review/gameplay-r3-review.json) accepted all243 Guardian/Volley frames and all25stills, including full270/271/287, with no new concrete defect. QA independently matched all355 capture source hashes and351 shared package source hashes. Sequential contact sheets preserve all 363 samples in [sequences](sequences/); the full-size raw frame set remains in `/tmp/rama-gameplay-owner-full-r3` and every frame is encoded in the video.

Earlier failures remain available: [initial decorative cutoff and clock correction](../combat-expiry/review.json), [R2 boundary/HUD rejection and repair](../combat-expiry/r2-boundary/review.json), and [accepted focused expiry probe](../combat-expiry/guardian-probe/review.json). The current combat component suite passes 85 checks; the strengthened actual-world integration suite passes 138; the focused HUD regression passes 9.

This is scripted offline gameplay with deliberate scene resets. It is silent, uses a software Forward+ renderer and simulated FPS, and does not establish audio quality, physical-GPU performance, online play or human-input usability. The separate low-angle and lifecycle stills are outside the video. Continuous reaction and rapid-primary motion have separate [motion evidence](../motion/REVIEW.md); actual packaged controls have separate [window evidence](../window/REVIEW.md). The retained stylized cloth/body-motion limits remain described in those reviews.

Video SHA-256: `77cb1dea4b12a928157d8c1645332409f0a890d9b69ae28bf87370494ede6230`. Independent review SHA-256: `957383bf8f70fa23d518bdac8110a6adc4574f3359feba0580ed586f430991b3`.
