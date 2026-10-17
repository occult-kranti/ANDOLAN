# Rama native eyelid performance

The final component uses **actual native eyelid quads**, extracted as a small orbital partition. It retains the original 164-bone skeleton, eye meshes, neutral anatomy, UVs and weights. The face has 5,452 source vertices and 5,564 exported vertices, with four small full/half blink morphs. The remaining 43,332 body polygons and the 5,378 partition polygons cover all 48,710 original anatomical polygons exactly once. There is no overlay skin shell or extra skeleton.

The bounded full-closure and continuous-blink review passed. **Facial art remains LIMITED**: folds are puffy, the closed contour is stylized, and neutral eyes are wider than the earlier tube-rim version. Gaze, brow, jaw, lips and expressive dialogue are not authored. This does not meet the Deadlock character-quality target.

## Source and pose construction

`build_native_face.py` extracts the original orbital topology and preserves its attachment. The 146 shared boundary vertices retain exact exported positions, UVs, normals and tangents; both blink targets hold their boundary positions and normal deltas at zero. Original skin weights differ by at most float normalization error (`5.96e-8`). A held neighboring ring keeps the deforming fold away from the attachment.

The [CC0 source ledger](sources/source-ledger.json) and [notice](NOTICE.md) identify pinned MakeHuman pose-unit data. Native upper/lower eyelid bone poses are evaluated during authoring, then baked into small mesh morphs. The original bones are restored before export. Central pose gains are upper `0.75` and lower `0.15`; medial corners smoothly approach full upper/lower gain across outward eye X from `-9 mm` to `-2 mm`. Authored half poses follow the native rotation arc. Runtime presentation uses these morphs and never writes the skeleton or changes eye scale.

The rejected R3 overlay entry `build_face.py` is retained for shared fingerprint/export helpers and historical inspection. Running that old entry is disabled. Its exact rejected source is preserved under `history/r3-rejected/`.

## Reproduce the final tangent repair

Three inherited zero tangent vectors in Ivory silk blocked strict LOD validation. The final repair derives each frame from its existing UV triangle and normal, including handedness `+1, -1, +1`. It changes 37 actual bytes inside three 16-byte records. Every other byte, including all face data, is identical to the reviewed input.

Run from the repository root with Blender 4.3.2. Use a fresh output directory:

```bash
blender -b -t 1 --python games/yuga-native/art/hero-rama-face/build_native_face.py -- \
  --input games/yuga-native/art/hero-rama-quality/rama-hero-quality.blend \
  --output /tmp/rama-face-repaired \
  --repair-reviewed-input games/yuga-native/art/hero-rama-face/history/r4f-reviewed-before-tangents.glb \
  --reviewed-sha256 1fdb01ccb894004a618a594cb41b2e955810c7bdc76855c42f7ce19b0516d92b \
  --reviewed-metadata games/yuga-native/art/hero-rama-face/history/r4f-reviewed/candidate.json \
  --reviewed-editable games/yuga-native/art/hero-rama-face/rama-hero-face.blend
```

This CLI mode was executed and reproduced final GLB `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`. The editable source remains `c541b2bf233843634db27de1768953756f2821d08b23242dd0ddacc29b66f351`. A complete Blender re-export may produce different bytes; it is not claimed to reproduce the reviewed GLB exactly. The fixed reviewed input makes the final repair reproducible.

To author a new native candidate, omit the four repair arguments. That creates fresh anatomy/pose output and requires new structural, seam, aperture and actual-render review. Renderers and imports must be serialized with the project owner.

## Runtime interface and checks

`rama_facial_performance.gd` exposes `configure(visual)`, `update_facial(delta, state)`, `reset(reason)`, `release()` and `report()`. State accepts `paused`, `alive`, `effort` in `[0,1]`, `reset`, `teleported` and `blink_enabled`. It binds exactly one small authored face, rejects duplicate ownership or incomplete corrective pairs, and leaves an unsupported old hero untouched. Normal blinks use a deterministic varied schedule. Effort uses bounded partial closure; death closes lids over 0.28 seconds; respawn/reset clear old state.

The [evidence archive](../../docs/evidence/rama-quality/face/REVIEW.md) contains 41 component/import checks, 19 geometry checks, four seam checks, eight whole-aperture checks, 39 actual candidate frames, three matched baseline views and independent review. Source hashes distinguish the visually reviewed input from its tangent-only repair. A later bounded runtime correction preserves the current per-eye closure when death begins during a blink; two old-source counterexamples fail and the final 41 checks pass. Physical-GPU performance, world integration and the full expressive face remain separate gates.
