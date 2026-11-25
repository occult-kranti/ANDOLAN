# Assets and provenance

The study vendors the 1K Poly Haven files downloaded on 25 November 2026. It reads existing YUGA sources from the same repository and packs their textures into the Blender scene. These references preserve the original source formats and names.

## Poly Haven rock

**Rock Face 01** by Dario Barresi is made available by Poly Haven under CC0. The scene shares one mesh across 16 placements and makes no edits to its topology or texture files. The glTF has 11,106 vertices and 20,174 triangles. [Asset page](https://polyhaven.com/a/rock_face_01) · [License](https://polyhaven.com/license) · [File metadata](https://api.polyhaven.com/files/rock_face_01) · [Direct glTF](https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/rock_face_01/rock_face_01_1k.gltf)

| Vendored source | SHA-256 |
| --- | --- |
| [rock_face_01_1k.gltf](sources/rock_face_01/rock_face_01_1k.gltf) | `96c332c01d173a2431115f3bac29be101fba341e5500e2a08e384f4edd17299e` |
| [rock_face_01.bin](sources/rock_face_01/rock_face_01.bin) | `873eac0319333e92bc96ddeedf8ebf69dc3c68ff1dfe32d8c14ddc165cdb20ac` |
| [rock_face_01_arm_1k.jpg](sources/rock_face_01/textures/rock_face_01_arm_1k.jpg) | `59128c79d207a50a69a38002986135ade3b19642d26158cec141eca41578c9ca` |
| [rock_face_01_diff_1k.jpg](sources/rock_face_01/textures/rock_face_01_diff_1k.jpg) | `41bd26ed2db1332b1ebb4b1326fd8af4d21f0f0eb57b8ea385033115c722cfdb` |
| [rock_face_01_nor_gl_1k.jpg](sources/rock_face_01/textures/rock_face_01_nor_gl_1k.jpg) | `9a9d85b9a01f4e24fc9ceec8baf96c019f552bca69591ff544c7a725e28b1d97` |

## Poly Haven lighting

**The Lost City**, an HDRI by Greg Zaal, is made available by Poly Haven under CC0. The 1K panorama supplies environment illumination. The visible camera sky uses Blender's procedural sky texture. The vendored [the_lost_city_1k.hdr](sources/the_lost_city_1k.hdr) is SHA-256 `53380c24561f972f2a2066f18ecf1d70a474eb715399d18d184c974629c0ca69`. [Asset page](https://polyhaven.com/a/the_lost_city) · [License](https://polyhaven.com/license) · [Direct file](https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/the_lost_city_1k.hdr)

## Existing YUGA assets

| Source | SHA-256 | Use |
| --- | --- | --- |
| [World-element Blender library](../reuse-library/yuga-world-elements.blend) | `10ee96ea906ca095dbfbc12b15a137a3dc263a77440f332d845a11dbec8616a7` | Temple, mangrove, reeds, lotus and diya objects. Their mesh data is shared by the placed copies. |
| [Lanka courtyard GLB](../../assets/environment/lanka_courtyard.glb) | `1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33` | Detailed foreground threshold, selected by its project-authored COL and DECOR object names. |
| [Hanuman enhanced GLB](../hanuman-hero-finish/models/hanuman-enhanced.glb) | `6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a` | Scale and composition reference, posed using the existing idle action. |

The repository records provenance for the [architecture and nature kits](../../NOTICE/CONFLUENCE-WORLD-PROVENANCE.json), the [courtyard](../README.md), and the [Hanuman character](../hanuman/NOTICE.md). These inputs are authored or licensed project assets.

The art team used the public description of Hampi's natural setting, water structures and temple precincts as a broad spatial reference for the scene. [UNESCO · Hampi](https://whc.unesco.org/en/list/241/)
