# Confluence army mesh library

The browser uses the same team outfits, weapons, banners, wheels and native attack poses as the original Godot lane units. Each team has five roles. Each role has one vertex-coloured mesh for nearby troops and one simplified mesh for distant troops. Both levels use the original geometry. [Infantry source](../../../yuga-native/scripts/lane_infantry_art.gd) · [Siege vehicle source](../../../yuga-native/scripts/lane_vehicle_art.gd)

The exporter joins the original parts in their authored rest pose and samples two strides, windup and release from the native pose functions. It preserves the changed positions and normals as four glTF morph targets. Godot’s LOD generator simplifies the corresponding rest mesh. The browser blends the native poses from Rust positions, headings, attack duration and windup ticks. The closest 16 units within 36 metres use the detailed mesh. Other units use a static pose with their authoritative position and heading. Each body takes one colour-pass draw. Health bars, shadows and effects have additional rendering costs. [Exporter](export_army.gd) · [Runtime](../army-scene.ts)

| Role | Detailed triangles | Distant Sun | Distant Moon |
| --- | ---: | ---: | ---: |
| Spearman | 10,704 | 1,258 | 504 |
| Bow guard | 8,560 | 1,070 | 1,070 |
| Commander | 11,316 | 530 | 530 |
| Cannon cart | 3,768 | 942 | 942 |
| Royal chariot | 5,296 | 662 | 662 |

## Regenerate and verify

Run from the repository root with Godot 4.6.3. The output argument must be absolute.

```sh
godot --headless --path games/yuga-native \
  --script ../yuga-rust/web/art/export_army.gd -- /tmp/yuga-army-vehicles.glb
cmp /tmp/yuga-army-vehicles.glb games/yuga-rust/web/art/army-vehicles.glb
```

Two builds produced the same 6,543,708-byte file with SHA-256 `2ba236492a7c721c343f3e6d65c748700c2e695ac0b17040c59768c9627491ff`. The file has ten detailed meshes, ten distance meshes and one shared vertex-colour material. A Chromium SwiftShader presentation check exercised 96 units, five roles, both hero rigs, a siege telegraph, projectile release, pooling across a wave change and return to solo. It checked rendering and transitions. Hardware frame times remain unmeasured.
