# Sandstone Blocks 05: original-source material intake

**Author:** Rob Tuytel. **Provider:** [Poly Haven](https://polyhaven.com/a/sandstone_blocks_05). **Asset license:** [CC0 1.0](LICENSES/CC0-1.0.txt). The downloaded PNGs are unmodified. Attribution is optional under CC0; it is retained here for provenance. No affiliation or endorsement is implied.

This is one coherent, small PBR material: 1,024 × 1,024 albedo, OpenGL/+Y normal and roughness maps, **6,220,633 bytes total**. The official asset metadata describes a 3 × 3 metre tile. [manifest.json](manifest.json) binds each map's publisher URL, byte count, publisher MD5 and locally measured SHA-256. MD5 matching is an additional publisher comparison; TLS and the recorded SHA-256 identify the actual intake bytes. The upstream API asset has no immutable Git revision; its `files_hash`, response hashes and downloaded-file hashes are retained instead.

In Blender, use albedo as sRGB and normal/roughness as Non-Color. Feed the normal through a Normal Map node, not directly into the Principled normal socket. This kit deliberately omits displacement, tessellation, height and metallic maps. Set physical UV scale deliberately; importing the images does not impose a 3 m tile on arbitrary geometry.

`sandstone.tres` is a Godot 4.6.3 StandardMaterial3D source fixture. It connects the albedo, normal and red-channel roughness textures with metallic zero. The `project.godot` and `check_godot.gd` templates allow an isolated check. Copy this directory into a **fresh scratch directory outside the canonical game**, then run:

```sh
godot --headless --path /absolute/fresh/sandstone-fixture --editor --import --quit
godot --headless --path /absolute/fresh/sandstone-fixture --script check_godot.gd
```

Both commands were actually executed successfully in the [intake evidence](../../../../docs/research/production-reuse-oct23/evidence/godot-intake.json). This establishes texture decoding and material-resource binding only. It does not establish Godot rendered appearance, native-game integration, geometry/collision quality or hardware performance.

The native-art worker is using the same frozen maps and manifest in a separate retained Blender look-development composition. That experiment must report its own output and image review. **This source kit is not promoted into the runtime.** The existing W4 wind-court gate requires the current material family and no new texture resources; introducing this material into that gate would require an explicit revised acceptance contract. See the [reuse decision and staged plan](../../../../docs/research/production-reuse-oct23/README.md).

The CC0 asset grant is separate from the provider's website content, live API terms and GPL asset-browser add-on. The source ledger retains the official license statement and API terms; no provider logo, example render or paid add-on was imported.
