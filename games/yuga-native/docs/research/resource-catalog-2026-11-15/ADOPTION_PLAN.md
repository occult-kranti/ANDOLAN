# Turn the research into one finished encounter

Task `YUGA-RESOURCE-AUDIT-2026-11-15`; native Sanctum. These are proposed implementation packets, not new accepted production milestones. Keep existing runtime paths, local Casual authority and the original two-site layout. No bulk downloads or engine migration are required to begin.

## Ordered packets and owners

| ID / owner | Work and exact output | Entry / exit evidence |
| --- | --- | --- |
| **RC-01 · world artist** | Inventory existing Sangam/courtyard pieces and choose one approach to one site. Produce an editable Blender composition and a module manifest using existing sandstone/indigo/brass materials. Add only missing pieces: stair edge, lintel, cover end, drainage/planter edge and one original focal artifact. | Entry: freeze current scene/camera/collision. Exit: matched native day/shadow views, both team approaches, ordinary capsule traversal and clear obstacle silhouettes; manifest agrees with actual geometry. Reviewer records remaining repetition/seams. |
| **RC-02 · hero + motion artists** | Repair Rama's supporting hand and firearm contact, then face/hair. Preserve the 164-bone runtime skeleton, existing attachment and ability contracts unless an explicit measured migration is needed. Use CC0 anatomy donors only where they save cleanup. | Front/back/profile plus advancing idle/aim/Q/E/C/X/reload transitions, interruption and reduced-motion cases. Root/feet/grip remain stable; accepted geometry and material result is reviewed in native lighting. No second hero before this kit is accepted. |
| **RC-03 · tools owner** | One isolated original TrenchBroom/FuncGodot room, only if brush layout solves an observed authoring problem. Pin plugin/engine versions; use existing cleared textures. | Compare authoring/reimport time with current Blender workflow. Test one unit conversion, winding/UVs, convex and concave collision, clip/skip/origin semantics and capsule clearances. Reject migration if it adds more repair than it saves. |
| **RC-04 · world artist + provenance owner** | Select at most three extra resources: one surface, one foliage family, one artifact/reference. Save upstream item ID, license evidence and hashes before alteration. | Review the actual downloaded files, not search thumbnails. License covers public source and packaged use; no hidden textures/meshes with incompatible terms. Original/derived versions and notices are linked. |
| **RC-05 · integration + QA** | Promote only accepted assets to their existing runtime directories; update credits/manifest and the relevant current tests. | Native import/reimport, collision/navigation, original full route, HUD/objective readability and normal input. Review a focused moving scene. Export an exact-source package when this promotion changes delivered game content. Windows execution remains a separate gate. |
| **RC-06 · networking owner, later** | Advance the existing native authority slice using a concrete requirements comparison before adding a transport library. | Two rendered clients and one authority agree on movement, hit/death, objective, economy, reconnect and result under measured delay/loss. Then a real ten-player match. Browser fixtures or local bots do not close this packet. |

RC-01 and RC-02 can proceed in parallel with exclusive files. RC-03 and RC-04 are conditional, not compulsory dependency collection. Serialize imports, shared exports, heavy renders and runtime promotion. RC-05 follows actual accepted content. Online work has its own ownership and does not make art acceptance optional.

## Minimum intake record

Save a machine-readable manifest beside each selected source kit and retain the governing notice. Use the established source-kit layout; do not relocate runtime assets for this study.

```json
{
  "asset_id": "original-sangam-bell-01",
  "title": "Original Sangam bell",
  "creator": "record actual author",
  "source_url": "record exact upstream item URL or original source path",
  "retrieved_at_utc": "record actual acquisition time",
  "source_revision": "record exact commit/release/item version",
  "license_id": "record exact identifier; never infer from price",
  "license_evidence": "path and hash of retained notice",
  "public_source_redistribution": "reviewed yes/no/hold with reason",
  "packaged_game_distribution": "reviewed yes/no/hold with reason",
  "input_sha256": "actual hash",
  "dependencies": [],
  "modifications": [],
  "authoring_tool_version": "actual Blender and add-on versions",
  "export_settings": {},
  "output_sha256": "actual GLB/texture hash",
  "review_status": "candidate",
  "evidence": [],
  "owner": "named next owner"
}
```

This example is a schema guide, not an asset receipt. Also record units/up axis, pivots, dimensions, triangle/material counts, texture sizes/color spaces, UV/tangent/normal conventions, skin influences and clips when applicable. Track third-party inputs separately from the author's changes. Credit includes title, creator, source, license and modification notes when required; retain supplied copyright/disclaimer notices.

## Blender → Godot artifact contract

Use the installed project-qualified tool versions until a candidate proves compatibility. Do not assume the newest add-on works with Blender 4.3.2 or a Godot sample's current main branch works with Godot 4.6.3.

Author at consistent real-world scale with stable module dimensions and pivots. Keep high-resolution sculpt and procedural source separate from the game export. Realize/bake geometry needed at runtime, produce a deliberate low-poly mesh, UV and collision mesh, then bake supported PBR maps. Shader nodes and Geometry Nodes graphs are not portable Godot shader programs. Preserve original node source for edits; verify the actual exported appearance.

For rigs, export the deform skeleton and baked action clips with explicit frame ranges and looping policy. Inspect actual contacts and root transforms after import. glTF is the existing interchange path; an Unreal-oriented FBX recommendation does not justify replacing it. For materials, confirm color versus data textures, roughness/metallic channels, tangent-space normals, transparency and double-sided surfaces. Optimize only after visual comparison; keep a recoverable source and the existing unsupported-extension failures.

Use separate, simple collision geometry where appropriate. Decorative carvings should not become invisible snag surfaces. Test stairs, corners, low cover, sight lines and the full player capsule from both directions. A successful GLB parse is not route or gameplay acceptance.

## Performance and build gate

Measure the current representative encounter before setting new numeric budgets. Record triangles, materials, textures and scene counts as diagnostics; do not convert them into claimed FPS. Use a named physical GPU, driver, resolution, quality settings, warm-up, frame-time distribution and memory observations for a hardware claim. Existing llvmpipe captures are useful visual evidence only.

Build documentation must record the exact source commit, imported asset hashes, engine binary, export options, platform and actual execution. Keep source-only checkpoint, generated package and fresh public download identities separate. New resources are selected for a demonstrated improvement in art, authoring time or measured runtime cost—not for the number of repositories downloaded.
