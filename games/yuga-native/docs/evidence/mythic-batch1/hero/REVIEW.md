# Rama material correction: actual five-view review

Accepted for the bounded FG02-T01 material correction, 17 October 2026. All five retained PNGs were independently viewed after the actual Godot 4.6.3 Forward+ capture. The current runtime GLB is `3424d72e74bb425c7e6bb2ff2fddc05c792657c437a888c56671fbd7d3ec3bcc`; all five recorded PNG hashes, dimensions, CRCs and compressed image payloads verify. The imported resource matched this source before capture, and the asset hash was unchanged afterward.

## Visible findings

- **01 front:** medium warm-brown skin, deep indigo, warm ivory and brass separate clearly. The former pale/pastel palette error is corrected. The bow silhouette and garment values remain legible.
- **02 rear:** indigo fold bands, brass hems and the contrasting ivory legs remain distinct. The stiff rectangular upper cape and repeated fold geometry remain obvious; the material work does not turn them into simulated cloth.
- **03 face:** skin, lips, iris, hair and brass now have clearer colour separation. Protruding eyes, simplified eyelids/anatomy, cord-like hair and the drawn hand obscuring the mouth remain production-art limitations. This unchanged native idle pose is not a new posture correction.
- **04 garment:** ivory fold relief and indigo sash contrast survive the new palette. Angular fold transitions, hard geometry and broad smooth garment regions remain visible. No claim of realistic fabric or corrected deformation is made.
- **05 distance:** the indigo mantle, ivory legs and brass bow read at a greater studio distance. This is a staged rear three-quarter studio view, not an actual gameplay camera or combat readability test.

No new detached component or obvious material-caused clipping was identified in these five static poses. They cannot establish continuous-motion intersection safety, foot contact, complete face quality, playable hero behavior or commercial-game visual parity. Actual integrated world and earlier motion evidence are separate packets; the earlier motion proof retains its earlier surface hash.

## Structural and editable-source evidence

`reconstruction.validation.json` records six passing preservation, reproducibility, corruption and palette gates. The original 6,500,208-byte binary prefix, rig, skin, geometry and animation data remain identical. The original 59,759 vertices, 100,938 triangles, 164 bones and nine clips remain. The original-source GLB and deterministic generator remain in `art/production`; this archive pins them rather than duplicating the large binaries.

The new editable reconstruction is `art/production/reconstruction-rama.blend`, SHA256 `4a9a4af12a737fdb01ff5f4b3ad94a0657bfda9b2bf4086dfbd48e054fa9973b`. It was actually reopened with fifteen packed images, 164 bones and nine actions; its build evaluated 81 finite bounded poses. This reconstructs an editable scene from the licensed committed GLB. It does not recover the missing original author's modeling history. The linked production provenance and NOTICE copy agree.

## Rejected attempt and capture bookkeeping

`rejected-surface-r1/` retains the pale first-pass diagnosis, exact generator/manifest/structural evidence and three actual older motion-render images used for its material rejection. That older motion run also had an independent action-timing rejection; these images only document the rejected surface. The extra linear-to-sRGB conversion was an authoring palette-space error, not evidence of a Godot double-gamma defect. The current palette negative fixture rejects that old candidate.

The actual five-view Godot capture completed and its log has no errors or warnings. Import also completed without errors or warnings. Xvfb emitted a `/tmp/.X11-unix` ownership note; the display and all images completed. The scratch runner subsequently called a traversal-only image checker that expects draw counters absent from this static hero report, so it stopped before producing its wrapper receipt. `post-capture-verification.json` independently checks the correct hero report contract, current source/import hashes, all five PNGs and advancing rendered-frame counters. The exact as-executed helper and wrapper are preserved; no draw counters or performance results are invented, and no repeat capture was substituted.

This is a static material correction acceptance. There was no full-video playback, audio audition, realtime performance test, Windows package test, fourteen-hero model completion or AAA-quality acceptance in this packet.
