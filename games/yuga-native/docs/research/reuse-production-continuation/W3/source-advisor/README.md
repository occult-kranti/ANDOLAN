# Next N1 donor: directly fit MakeHuman `long01`

**Use the existing CC0 `long01` mesh and its authored texture for the next bounded head-fit trial.** Its coordinated cap/layers/UVs are a more concrete next source than another conversion of the dense guide study into cards over the incompatible R1 masses. This is a source recommendation, **not accepted game art or a new fitted hero**.

The [official pinned catalog](official-system-assets.md) explicitly lists `long01` as CC0. The downloaded OBJ, mhclo and material each also carry a September 2020 CC0 release notice identifying Data Collection AB, Joel Palmius and Jonas Hauquier. [License](CC0-1.0.txt); [catalog revision and exact URL](catalog-source.json). No commercial game data is involved.

Only five members were fetched from the official system archive: **3,088,146 compressed bytes in 2.45 seconds**, HTTP 206, exact range/size and every member's central-directory CRC verified. The 280,737,770-byte archive was **not** downloaded. The slow secondary-mirror attempt was stopped after about 118 seconds without retaining verified member files; its outcome is preserved. The primary mirror succeeded with the same ETag as the cached directory. [Download receipt](download.json).

| Ready source | SHA-256 |
| --- | --- |
| [OBJ, 215,324 B](asset/long01.obj) | `7f1d6dadbdf9e96435251955d6657e77ea5433c9bc7c85a5c5f5e4eae0cb9a8c` |
| [2048 RGBA texture, 2,915,253 B](asset/long01_diffuse.png) | `e8dc25d90f8f62467e8630420e1240a400d070054fb7c3f1d3f7bf3e457d6c2c` |
| [hm08 fitting proxy](asset/long01.mhclo) | `94ecbebfd834da2cbee2ce90b730972590eb22a252ecd9592038ea736e063646` |
| [Original material](asset/long01.mhmat) | `74ec88267e679d316f8037a074511ffc887b27e198ea381d0ae4a3f180f96760` |

Archive URL: `https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip`; members `hair/long01/*`, exact selected range `262788847–265876992`. [Central entries](central-selection.json) and the exact 524,288-byte cached directory are retained for reproducible selective retrieval.

## What the actual source supports

The [upstream 256×256 thumbnail](source-thumbnail.png) was actually opened and viewed. It shows a continuous top cap and coherent long nape mass with strand texture. It is an upstream preview, **not a YUGA render**.

Read-only [inspection](inspection-v2.json) finds 3,239 vertices, 3,314 UV coordinates, 2,054 quads / 4,108 fan-triangulated triangles, and 18 connected components. The dominant connected component has 1,005 vertices and 954 quads; it provides a substantial cap/length substrate while the other components add authored layers. There are no edges incident to more than two faces. The mesh has 2,334 boundary edges and uses alpha, so it is not a closed opaque solid.

In the dominant component's upper third, **380 of 388 face-centroid UV samples** have alpha ≥243/255. This supports trying the donor's already coherent cap, but centroid samples do not prove opacity over every covered texel or native-camera silhouette. The full texture has 56.91% pixels at alpha ≥243 and 75.05% at alpha ≥128; empty atlas space is included. Do not convert those numbers into an in-game coverage score.

The original material requests transparency, alpha-to-coverage and double-sided drawing, and uses a MakeHuman litsphere shader. It is **not** a ready Godot PBR material. The source hair is long and center-parted; shortening and crown/topknot integration are real art work, not an automatic file rename.

## One concrete implementation trial

1. **Fit the intact donor first.** Import the OBJ with its existing UV/texture, establish its source units and Y-up mapping from hm08, and align scalp/temple/ear/nape landmarks to the unchanged Rama head. Preserve the dominant cap and authored layer ordering. Compare the original donor with the fitted source before cutting or shortening it; retain source indices.
2. **Make one hair-region plan.** Protect face, ears, eyebrows, crown hardware, body and canonical rig. Author an explicit hair-only omission mask and a crown/topknot seam plan; do not simply stack this cap over the broad R1 nape panels. Shorten the donor's existing length through an editable source deformation and check silhouette/UV stretch. The earlier nine-nape mask does not authorize removal of upper hair or crown pieces.
3. **Translate its material once.** Reuse the exact color/alpha texture, correct sRGB handling and a measured roughness/specular conversion. Start from its declared double-sided alpha-to-coverage intent, then inspect rear/profile at ordinary and close native distance under matched light. Do not infer Godot appearance from the litsphere thumbnail. Stop if cap transparency, roots or silhouette fail.
4. **Bind through the existing rig adapter.** The mhclo is an hm08 source fitting proxy: 3,239 rows, coefficients from −1.77306 to 4.31528. These are barycentric/extrapolation values, **not skin weights**, and Rama's exported GLB vertex order is not hm08. Use a verified hm08 source correspondence or explicit landmark fit; derive native binds from the canonical rest rig. Check attachment before/after translated and rotated spawns, mirrored/invalid mappings and wrong-head negatives.
5. **Review motion and budget only after the look passes.** Run existing 23-clip skin probes and actual advancing aim/turn/draw/release/run/death/recovery footage. Inspect lower hair against neck, collar, shoulder, quiver and bow. Then produce near/mid/far variants with real silhouette/alpha/LOD comparisons. No independent sway, contact, LOD or hardware budget is supplied by this donor itself.

This trial reuses a complete authored hair source and the existing import/rig/inspection pipeline. No new source geometry or runtime asset was changed in this advisory packet. Full hero art remains open.

For a fresh source read, `inspect_selected.py --input <asset-directory> --output <fresh-report.json>` needs Python, NumPy and Pillow only. `fetch_selected.py --cached-directory systemassets-directory.bin --output <fresh-directory> --primary-mirror` repeats the small range intake; retain its HTTP/CRC failure rather than falling back to the full archive. [Manifest](manifest.json).
