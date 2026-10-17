# Rama surface finish sources

`woven-roughness.png` is an exact copy of the already reviewed
`art/open-art-wave/textures/indigo-woven-roughness.png`. It is a CC0-1.0
derivative of the Microsoft (2020) **SheenCloth** technical-fabric ORM map:

- Repository: https://github.com/KhronosGroup/glTF-Sample-Assets
- Revision: `edc7c9e67c639d230715049ee31f9a96a6babbbe`
- Source path: `Models/SheenCloth/glTF/technicalFabricSmall_orm_256.png`
- Original SHA-256: `41c04abdb9531d00a4ac832d41f02cd549c7be74886c4d492475cfb95d239a20`
- Image license: https://creativecommons.org/publicdomain/zero/1.0/
- Original file-specific license record is retained in
  `art/open-art-wave/source/microsoft-sheen-cloth/LICENSE.md`.
- Upstream license/metadata documents are CC-BY-4.0; this package does not copy
  those metadata documents or imply a license for the entire repository.

The other four maps are deterministic roughness-only derivatives of the
existing original YUGA Rama material maps, named and hashed in `manifest.json`.
No commercial game model or texture is included. `build_maps.py` documents the
exact generation, including low-amplitude variation. The technical weave does
not claim historical textile authenticity. Existing normal maps and all
authored albedo maps remain unchanged at runtime.

The new generator and runtime component are original project code. This notice
does not change the license of existing project code or material assets.
