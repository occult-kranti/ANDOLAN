# Triad relay render: corrected-source repeat

Reviewed 17 October 2026. This is the second accepted technical capture archive, copied from fresh raw run `/workspace/scratch/yuga-relays/triad-render-r3`, following source commit `ce00325612f4ca718e3e5773f7229a9fd94d2172`. Acceptance covers the recorded technical take and seven inspected stills; production art acceptance remains open.

## Source and media verification

World runtime SHA256: `180d7d1671b76c9d0d565b4bac20ed4f4821ab9bf15b9a800281a65f4ddc4c1b`. Relay art remains `32e42d32a4a1e52414c2e274d076c1aac4531fd10084b052082f0cc08cd31cb6`. All 235 captured source hashes matched the current files at archival. The complete captured inventory is preserved in `triad-render-review.json`; later packaging/documentation edits are not represented as captured runtime changes.

The fresh runner reports 180 actual Forward+ frames at 1280 × 720 over 360 physics ticks, time scale 1, on X11/llvmpipe. It stages the hero, ammunition and camera once, prepares for 7.5 unrecorded simulation seconds, records six seconds, then takes four frozen-world station views. All 180 raw PNG hashes, four still hashes and report/video associations were verified. Independent ffprobe confirms 180 video frames, 30/1 fps, exactly 6.000000 seconds and no audio stream. This is structural media validation, not full video playback or physical-GPU performance.

Compared with the [previous accepted round](../triad-relay-render-r1/TRIAD-RENDER-REVIEW.md), the only changed captured source hash is `scripts/confluence_world.gd`. All 180 per-frame image hashes match the earlier recording. The three selected PNGs, four stills and MP4 were also compared directly and are byte-identical to that archive. The fresh report pins the corrected source; unchanged rendered bytes are expected because this take stages its camera directly and does not activate Visit Lotus through the menu.

MP4 SHA256: `0e26eeacdadab766d34bb003f4499cd35dbd99297cd3396414413dad6b4cbe2b`. Fresh render-report SHA256: `59b69226f1d9564d83bef2740f941700cca8eaecf2fc740444225f38cfa5f52e`.

## Actual visual observations

All seven retained images were opened again: frames 15, 90 and 175, Reed/Lotus/Sky day and Lotus night.

- The angular objective corners and segmented progress rows remain visible around the hero. Sun ownership and HUD instructions are readable at 720p. Frames 15/90 show 3/12 arrows; frame 175 shows 6/12, consistent with the separately recorded single +3-arrow supply receipt.
- Stepped plinths appear grounded, with no obvious detached components, gross clipping or new lane overlap in these views. These observations do not replace physical route/collider tests.
- Neutral Reed/Sky floor marks remain low contrast on beige paving, with stippled/dashed dark edges at grazing angles and shadows. The images do not establish the technical cause.
- Reed stems, Lotus petals and Sky sails are present but subtle. The shared large ownership badge dominates their silhouette; site identity remains weaker than owner identity at gameplay distance.
- The paired Lotus night view retains floor, hero, plinth, Sun symbol and progress readability under a cooler palette. Small warm emissive lantern windows remain visible; no area-lighting or transition-smoothness claim follows.

There is no new visible regression in these sampled images. The earlier [rejected gold-inlay capture](../triad-render-r1-rejected/REVIEW.md) remains rejected; the inherited bright mid-lane torus stays hidden in this take. That visual correction is distinct from the subsequent facing correction.

## Facing fix and acceptance limits

The [rejected package input review](../triad-window-r1-rejected/REVIEW.md) found that Visit Lotus faced away from its objective. This runtime includes the facing correction, but the current capture uses a staged camera and therefore **does not prove the menu-facing fix**. A fresh actual extracted-package menu/input repeat must establish that forward input now approaches the relay.

This review did not play the full MP4 or audition audio. Only neutral and Sun states are visible; Moon ownership, teal capture and contested flags still need actual art review. Continuous rotor/contact animation, day/night transitions, human-input usability, human balance, online authority and hardware performance remain outside this evidence. Broad primitive forms, uniform surfaces, repetitive architecture, weak neutral contrast and subtle site motifs remain practical art limits. This archive does not establish Deadlock/Overwatch-level or other AAA visual quality.
