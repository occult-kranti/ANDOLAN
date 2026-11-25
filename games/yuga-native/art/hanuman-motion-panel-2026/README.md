# Hanuman · five ability motion study

This editable Blender scene studies how Hanuman's five existing abilities can carry a clearer anticipation, release, contact and recovery. It reuses the shipped 167-joint Hanuman, his original action clips and the existing Lanka court. The scene is an offline presentation study. The match authority remains responsible for damage, shield, movement and cooldowns. [Editable Blender scene](hanuman-layered-abilities.blend) · [Motion review](hanuman-motion-review.mp4) · [Five contact stills](contact-sheet.webp) · [Timing and geometry](timeline.json) · [Verification](evidence/verification.json)

The timeline runs at 40 fps. Each 20 Hz gameplay tick occupies two Blender frames. Source clips are time-remapped to their authored release and impact phases, then return to the source recovery pose. The scene has five NLA strips, camera shots and named editable effect objects. The study palette is recorded alongside the current runtime colors. The film is a low-resolution silent review rendered from the scene.

| Ability | Shipped authority markers | Presentation study |
| --- | --- | --- |
| Vajra Gada | Impact 5, recovery 11 | A warm frontal boundary narrows to a contact arc and brief raised sparks. The 3.5 m radius and angular extent come from the shipped sector. |
| Vajra Kavacha | Shield release 7, recovery 12 | A mint forward boundary is distinguished by four separated inner arcs and upright protective arches. This scene indicates the area. Actual ally shielding is decided from live recipients and cover. |
| Maruti Udayana | Takeoff 4, nominal landing 13, recovery 17 | Pale wind traces mark a six-metre clear-route example. Its body follows the Rust parabolic height formula. The real game can land early against cover. |
| Lanka Dahan | Rear burst 9, body recovery 17, field end 49 | A red-orange rear-sector outline and sparks establish direction. The field outline remains visible after the body recovers. |
| Mountain Pulse | Release 14, landing 23, recovery 33 | A fixed ground target shows the actual seven-metre impact radius. An outgoing line precedes the landing arc and lifted impact plumes. |

Times in the table are ticks after accepted input. In the current Rust authority the vault's event named `impact` is emitted at takeoff. A production landing cue must instead use `landed_age_ticks` or grounded contact and account for an early blocked landing. A chosen Mountain Pulse target is fixed in world space and can be up to 14 m from the caster. The studio uses a 5.5 m example. [Shipped ability profile](../../assets/design/hanuman-ability-kit.json) · [Rust combat and events](../../../yuga-rust/src/combat.rs) · [Current gameplay guide](../hanuman-hero-finish/GAMEPLAY.md)

## Five panel rounds

1. **Freeze.** Pinned the playable GLB SHA-256 `6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a`, the prior packed scene and the authority profile. The earlier six-shot film uses editorial durations. [Original scene and source proof](../hanuman-hero-finish/evidence/editable-scene.json)
2. **Design.** Combat and physics reviewers established per-ability timing and counterplay requirements. Boundary shape differentiates a friendly shield from attack zones, and the persistent rear field remains separate from body recovery.
3. **Author.** Retimed the original NLA clips without changing their bone animation curves. Added parametric sector and disk meshes, airborne strike and landing accents, shield arches and wind trails. The nominal vault movement follows the existing clear-path parabolic trajectory.
4. **Challenge.** The first source comparison found Blender shortened NLA strips after their action ranges changed. Applying strip durations after the ranges restored the full recoveries. The initial [wide review](evidence/first-gada.png) made the hero too small; the close camera and moving vault camera improve the study. A later [review](evidence/second-gada.png) exposed a black courtyard inlay that looked like a false impact mark. The final scene hides that decorative inlay and its import helper.
5. **Verify.** Reopened the saved scene, sampled head, wrists, feet and two tail joints at release, impact and recovery, and compared them to the source animation at the same authored phases. Checked field expiry, the seven-metre disk, packed textures and nominal vault positions. A copied scene reopened and rendered with the project workspace hidden. The review does not exercise an actual game client, blocked route or target GPU. [Machine-readable checks](evidence/verification.json) · [Offline reopen](evidence/offline.json)

At the planted action checkpoints, the lowest vertices weighted to each foot or toe are approximately 10.8 mm above the studio floor. The vault midpoint rises as intended. This vertex screening is a visible-contact lead for the next animation pass and does not measure game collision or every shoe triangle. [Sole samples](evidence/sole_samples.json) · [Measurement script](verify_soles.py)

The study uses original YUGA character and court assets. Effect curves are authored from the shipped profile and the presentation decisions above. [Character provenance](../hanuman/NOTICE.md) · [Native asset notices](../../NOTICE/ASSET-NOTICE.md) · [Source profile](../../assets/design/hanuman-ability-kit.json)

The new [illustrated Mountain Pulse board](../ability-keyframes-2026/hanuman.png) carries the gada through the windup, impact and recovery. The playable rig attaches the gada to the anatomical right wrist. The illustration places a small vegetated mountain above the weapon and green debris at impact. This Blender study uses an outgoing line, a fixed ring and gold impact accents. The playable game now has a separate textured stone projectile and short impact sparks, timed to its authority events. A vegetated mountain, debris and an independently checked two-hand grip are further work. The still board is an art target, while the timeline uses the shipped tick and pose markers.

## Rebuild and inspect

From a full checkout with Blender 4.3.2, Python, NumPy, Pillow, FFmpeg and the Open Image Denoise command-line tool available, set `OIDN_EXECUTABLE` to the tool's path and run:

```sh
study=games/yuga-native/art/hanuman-motion-panel-2026
review=$(mktemp -d)
blender -b -t 1 --python-exit-code 1 -P "$study/build.py"
blender -b -t 1 --python-exit-code 1 -P "$study/verify.py"
blender -b -t 1 --python-exit-code 1 -P "$study/verify_soles.py"
blender -b -t 1 --python-exit-code 1 -P "$study/render_review.py" -- --samples 4 --width 720 --output "$review"
python3 games/yuga-native/tools/hanuman-art/denoise.py --oidn "$OIDN_EXECUTABLE" "$review"/*.png
python3 "$study/contact_sheet.py" --stills "$review" --output "$review/contact-sheet.webp" --receipt "$review/stills.json"
blender -b -t 1 --python-exit-code 1 -P "$study/render_motion.py" -- --samples 2 --width 480 --oidn "$OIDN_EXECUTABLE"
```

The builder checks the source scene and model hashes before writing the study. `look.json` contains camera choices, staged target distances and presentation colors. The still renderer saves one actual Cycles frame for each ability. Open Image Denoise 2.5.1 creates separate presentation frames. The movie renderer samples every second timeline frame at 20 fps, denoises each frame when the tool path is provided, and validates the H.264 frame count. Intermediate frames are kept in a temporary directory during encoding. Inspect the NLA strip time curves and the **Ability layers · editable** collection in Blender before changing a cue. [Builder](build.py) · [Look parameters](look.json) · [Movie receipt](evidence/film.json) · [Open Image Denoise](https://github.com/RenderKit/oidn)

To promote a visual cue into the match, bind it to accepted authority snapshots. Verify early landing, a blocked target, interrupted windup, skipped snapshots, both teams and a full private match. Benchmark against the target hardware and compare readability in the actual shoulder camera. The present arcs, sparks and low-sample review are an early study of timing and composition.
