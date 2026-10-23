# Source and asset notices

The local loader and isolated preparation/owned-capture pattern adapt existing
project code in `tools/reuse-vfx-stage/source_loader.gd`, `prepare_preview.py`
and `run_capture.py`. The existing `tools/wind-court-pilot/pbr_material.gd` is
copied byte for byte into the prepared scratch project. No new broad license
for original project code is asserted; source hashes are in the evidence packet.

The measured map geometry is the existing original generated Lanka courtyard,
SHA-256 `1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33`.
Its [metadata](../../assets/environment/lanka_courtyard.metadata.json) dedicates
this generated geometry and textures to CC0-1.0; its generator code is separate.
This prototype reuses one existing named structural group, without remodeling it.

The existing Poly Haven `sandstone_blocks_05` source kit is authored by Rob
Tuytel, CC0-1.0. The [existing manifest and retained license](../../art/source-kits/production-reuse-oct23/sandstone-blocks-05/manifest.json)
remain authoritative. It has three verified unmodified 1K PNG maps. The
existing adapter quantizes roughness to an in-memory R8 upload, creates mipmaps
and uses world triplanar mapping; original file bytes remain unchanged.

Godot is a separately installed MIT-licensed engine. The prototype calls its
glTF and physics APIs; it does not bundle engine source or binaries. Redistributed
Godot executables need their normal engine/third-party notices.

The primary FuncGodot MIT, OpenArena GPL-2.0-or-later and Godot TPS code-MIT/
asset-CC-BY-3.0 evidence is retained under the separate research packet with
upstream notices. None of that newly fetched code is executed, installed or
ported into this adapter. Open engine code, an importer or a file format does
not grant rights to arbitrary game maps/textures. No Deadlock, Overwatch,
Dota 2 or TF2 client content was downloaded or imported here.
