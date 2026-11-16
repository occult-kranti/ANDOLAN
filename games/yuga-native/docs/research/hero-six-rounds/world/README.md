# Sangam civic quarter · integrated Confluence art rebuild

Task `YUGA-HERO-6R-WORLD`, native offline YUGA. This follows the user's correction that the previous game/map looked too light and requested a substantial playable-map rebuild alongside the hero. The new district is authored geometry for the actual Confluence world, not the separate Relay Foundry study.

## Built source and purpose

Eight legacy box shells become a coherent original South Asian civic quarter in four mirrored families: warm carved ghat halls, indigo civic archives, observatory chhatri courts and brass-eave galleries. Relief shutters have depth, arched/cusped frames, timber/brass lattice, pilasters, rosettes, layered plinths, bracket-supported chajja, tiled eave rhythm and differentiated roofs. Ground windows remain visibly closed; this does not pretend the inherited solid buildings contain enterable rooms.

Four perimeter galleries replace the disconnected distant skyline outside actor bounds. Two real galleries span the central avenue at z±28, with underside8m and top8.56m. They provide shaded ground underpasses and truthful upper collision for existing flight/grapple traversal. Rama's existing ground-only ability restriction remains explicit: return to a legal ground surface to cast.

Four solid civic cover monuments at x±8,z±60 use the same3×6m footprints in mesh/native physics/offline army. An independent reviewer found that the initially proposed1.4m planter would misrepresent the planar arrow blocker; lead amended the contract to visible2.7m solid carved monuments. The central13m gap and both lateral escape routes remain open. Foliage is not used to disguise invisible cover.

## Source and integration contract

- Authoring: `tools/studio/build_sangam_district.py`; editable `art/sangam-district/sangam-district.blend`.
- Runtime: `assets/world/sangam-district.glb` and companion JSON; `scripts/sangam_district.gd` installs it.
- Root owns `confluence_world.gd` integration and preserves the separately authorized field-shop/battle-HUD stream.
- Call `build(world)` after existing frontage/gate/garden construction. Successful result supplies `root` and `report`.
- Chain `prepare_army_manifest(original, district)` after gate and garden derivation. It adds exactly four ground boxes and no overhead boxes. The army ignores Y; overhead in its manifest would block the ground route incorrectly.
- Original eight planar footprints, lanes, relays, spawn, gate and garden are retained. Active native ground shapes match the declared solids; previous Block2 detailed shape, roof collision and old art visibility are retained/restored by removal.
- The adapter requires identity world/district transforms and exact finite cover IDs/positions/dimensions; moved/scaled/mutated/duplicate state is rejected.

## Measured authoring budget and reuse

Final source: **308,422 triangles,26 visible mesh objects,8 material definitions** (unused definitions may be omitted during export), no new lights. These are measured asset counts, not hardware performance claims. Runtime reports actual surfaces/material resources. Near architecture retains its detail. Distant pavilions and arches use lower tessellation; unseen internal arch faces were removed.

R1 exceeded the320,000 authored gate at475,942 triangles; R2 at369,094. Both scripts/logs remain under `art/sangam-district/rejected-r1/` and `rejected-r2/`. R3 passed308,422 without raising the gate. No failed run is relabeled as a successful export.

Twelve albedo/normal/roughness inputs reuse the existing original YUGA CC0 courtyard sandstone, limestone, glazed indigo and aged brass maps. Their exact hashes are in the asset manifest. Existing `NOTICE/ASSET-NOTICE.md` and `art/README.md` own that dedication. The new geometry/code is original project work. No commercial game files or external photographs were imported. Blender application GPL terms are separate from exported original project assets.

Primary historical references, supplied by the research specialist, guide massing and shade: [ASI Fatehpur Sikri](https://asi.nic.in/pages/WorldHeritageFatehpurSikri), [UNESCO Fatehpur Sikri](https://whc.unesco.org/en/list/255/), [Ministry of Culture](https://culture.gov.in/fatehpur-sikri), [government monument site](https://tajmahal.gov.in/fatehpur-sikri.aspx). This is an invented mythology-inspired city, not an ancient-period or archaeological reconstruction. References do not license their photographs/textures for reuse.

## Executed checks and limits

[Source freeze](source-freeze.json) pins actual files and exact commands. Blender4.3.2 exported the GLB and editable blend on8 threads. No Blender image render was performed by this worker. The root's source/capture lane owns engine import and final runtime images; import artifacts appeared during shared work and are not claimed as this worker's command.

The initial [native suite](checks-r1/result.json) passed **31/31**. The final R6d [successor suite](checks-r6d/result.json) passes **33/33**, exit0 with zero warnings/errors, including shared stone-finish source bindings and isolated brass overrides. It loads actual imported meshes into a matching eight-block host, checks cover top/shot occlusion and planar agreement, all four side escapes, central lane, connector deck/ceiling/ground route, eave headroom, actual ground/elevated kit eligibility, corrupt/moved/duplicate metadata and exact restoration. It does not prove ordinary input, integrated HUD/shop operation, human visual quality or GPU frame time.

Actual visuals reviewed: prior studio gameplay/map overview, the aspirational `art/sangam-direction/art-direction.png`, and ten original integrated native R1 captures. The concept is not gameplay. [R5 review](round5-actual-review.json) pins the images and defects: coplanar cover/shutter surfaces, buried perimeter facade detail, excessive diagonal stone grain and near-black indigo. R6 fixes the geometry offsets and applies the original `shaders/sangam_masonry.gdshader` only to the three stone families. It compresses source-map luminance around warm sandstone, limestone and muted indigo, preserves original normal/roughness texture bindings at reduced normal strength, and makes brass less glossy with a private material override. No raster images were edited. The original R3 model/source and R1 images are retained. Blender previews retain the original albedo; the native shader determines the final finish. R2 actual images verified those fixes but showed an overly flat finish and a reversed perimeter panel side. [Final repair audit](round6-repair-review.json) records the R6d correction, subtle metre-scale ashlar/bevel/grain, and the complete coplanar-source audit: zero exposed different-material rectangular conflicts, with 28 individually documented hidden ground/roof contacts. R2 failed whole-capture source consistency after a separate HUD edit, so it is preserved as a consistency failure. All twelve [final frozen R3 originals](round6-final-visual-review.json) were then personally reviewed: the capture is complete with no reported failure, corrected surfaces and both perimeter sides read clearly, and no new scoped repair blocker was found. These actual Forward+ llvmpipe images establish appearance at1280×720, not hardware performance or commercial-game quality. Wide exposures, long plain north/south walls, the older gate material and heavy HUD cards remain documented quality limits. Complete interiors, dense vegetation, dynamic destruction, online spatial authority and elevated ranged combat remain outside this version.
