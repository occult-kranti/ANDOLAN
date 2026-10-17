# Rejected Triad package window review: Visit Lotus facing

Reviewed 17 October 2026. This archive preserves a real Linux package input test that found a user-flow defect before acceptance. **Rejected for the Visit Lotus approach facing; it is not final package acceptance.** The correction and a fresh package/input repeat belong to the subsequent attempt.

## Package and evidence identity

The tested local package was built from clean native source commit `0e91abd72b102c13db5a041774eaa6d9ddeec9ba` on `game/yuga-native-production`. The window runner recorded XTest keyboard/mouse events against the extracted package, not an editable source launch. `input-review.json` records the event order, screenshot hashes and engine/PCK identities. The native export/package manifests and `export-capture-verification.json` preserve the preceding package and recorded-capture comparisons; those checks do not override this later UX rejection.

At archival, all thirteen screenshot hashes were verified against the input record. The extracted Linux engine and PCK and the Linux ZIP were independently hashed and matched the package/input records. Export-manifest bytes/hash and all three manifest commit associations matched.

- Linux ZIP SHA256: `d2e2ae34246cbcdc249c35c532c082ffb55186c645c775b0f5ae9f15553d1460`.
- Extracted engine SHA256: `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`.
- Extracted PCK SHA256: `58620a59d0755090a01122b2ad11fca2184189f3a30f42f19d16b959d7602362`.

The logs report Godot 4.6.3, Forward+ and llvmpipe software Vulkan. `game-output.txt` is an unchanged copy of raw `game.log`; `xvfb-output.txt` preserves its X11 socket-directory ownership warning. The runner records process termination `-15` after review cleanup; this is not recorded as a gameplay crash. Original files remain in `/workspace/scratch/yuga-relays/window-r1`; package files remain in `/workspace/scratch/yuga-relays/packages-r1`. Package ZIPs and extracted binaries are identified here, not duplicated in this archive.

## Independently inspected screenshots and input

All thirteen PNGs were opened for this review.

| Images | Recorded input and visible result |
| --- | --- |
| `01-title.png` → `02-world.png` | Clicking Explore Confluence reaches the world at Surya arrival court. The HUD shows Wave 1, 12/12 arrows, zero gold, both cores at 100 and open relays. |
| `03-pause.png`, `04-lotus-focused.png` | Escape opens the practice menu; three Tab presses visibly focus Visit Lotus relay, and Return selects it. |
| `05-lotus-approach.png`, `06-after-move.png` | The visit arrives with “Enter the marked zone · 7m to relay centre”. After W, that proximity prompt disappears and the character remains looking away from the intended capture approach. This sequence exposes the wrong-facing visit placement: natural forward movement takes the player away from the objective. |
| `07-after-fire.png` | A recorded mouse-button hold reduces arrows from 12/12 to 10/12. This establishes firing/ammo response, not a hit or kill. |
| `08-relay-entry.png`, `09-capture-progress.png` | A subsequent S hold moves back into the relay area: Lotus displays Sun capture at 11%, then 86%. The character faces the camera in these views. The capture instruction is visible. |
| `10-paused.png` | Escape opens the menu over a visible 87% capture display. This single paused screenshot does not independently prove the whole pause interval or exact capture timing. |
| `11-held-relay.png` | Despite its filename, the image says **Lotus · Contested**, with “Clear enemies to capture and receive supplies”; troops have reached the site and arrows remain 10/12. This is no proof of held ownership or supplied arrows. |
| `12-help.png` | F2 opens Keyboard controls. The footer visibly says “F5 restart round”, matching the revised reset description. No remapping/persistence change was exercised here. |
| `13-reset.png` | Following Escape and F5, the view returns to Surya arrival court with Wave 1, 12/12 arrows, zero gold, open relays and both cores at 100. This supports the ordinary round-reset flow in this package. |

## Rejection and limits

The Visit Lotus helper should present the objective ahead so forward input enters the nearby marked zone. This package instead requires backing toward it. Native integration owns the facing correction; its fresh regression and actual package repeat must be recorded separately. This archive must remain pinned to the pre-fix package.

No held capture, successful supply, combat hit/kill, continuous animation, audio/listening, full video playback, Windows execution, public-download validation or physical-GPU performance is claimed. Wall-clock waits in the input record are not simulation-time measurements. The test is a bounded actual-window input and screenshot review of an offline Linux prototype. Native hero health/death, production art and online matches remain outside this evidence.
