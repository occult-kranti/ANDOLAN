# Visual reuse that improves the current Rama slice

17 October 2026. This review follows the existing Godot 4.6.3 character and
courtyard. It found a real material-channel error, verified the reused texture
bytes and identified specific render checks. The [source ledger](../evidence/visual-campaign/reuse/source-ledger.json)
records fetched URLs, hashes, selected reading ranges, local inputs and unread
sources. No new game repository or commercial asset was imported.

## Findings and implementation decisions

| Finding | Action and evidence |
| --- | --- |
| The new belvedere sampled courtyard roughness from RED, but the actual glTF-exported images store roughness in GREEN. RED is constant 255 in all four images. | Root changed `hero_district_detail.gd` to `TEXTURE_CHANNEL_GREEN` and added an actual-image regression. Root reports 44 district checks passing at `/workspace/scratch/hero-district-channel-r4`. The first frozen render predates this fix; the next capture must include it. This role independently checked all 12 external courtyard PNGs against their GLB-embedded bytes: all exact. |
| The new hero finish uses five separate grayscale roughness maps. | Keep its RED selection. All five output and input hashes match the finish manifest. The woven map is an exact copy of the previously reviewed cloth derivative. Do not apply the courtyard GREEN correction globally. |
| The atmosphere controller's header claimed no added render passes while it writes SSAO/glow settings. | Owner corrected the claim to no added scene nodes/geometry or per-frame callbacks, and explicitly retained the GPU cost caveat. SSAO and glow remain renderer work. Owner reports 47 source-bound checks passing; that is separate from visual/hardware acceptance. |
| Unshaded ability strokes still write `ALPHA`. | They use the transparent pipeline and can overlap or sort incorrectly. Review Guardian/projectile/impact overlap from both sides, camera crossings and night contrast. Existing geometry caps do not measure overdraw cost. |

Observed courtyard roughness ranges are brass 97–145, indigo 184–220,
limestone 184–218 and sandstone 182–223, all in GREEN. RED and BLUE are
255 throughout these images. These measurements explain why a structurally
valid material could previously lose its authored roughness variation.

## Reuse, provenance and boundaries

The belvedere reuses the project's original courtyard maps, not a newly
downloaded environment. The generated courtyard geometry and textures have an
explicit CC0 dedication in [the authoring record](../../art/README.md) and
`assets/environment/lanka_courtyard.metadata.json`. Its 12 extracted image
payloads exactly match the current GLB. The metadata's old phrase “generator
uses repository license” does not establish a repository-wide code license;
there is no root license. The explicit generated-asset dedication is separate.

The surface finish reuses Microsoft (2020) SheenCloth through
`KhronosGroup/glTF-Sample-Assets@edc7c9e67c639d230715049ee31f9a96a6babbbe`.
The original ORM and file-specific license were freshly retrieved and match
the retained bytes. Images are CC0; the upstream license/metadata documents
have a separate CC-BY-4.0 exception. The retained
[notice](../../NOTICE/OPEN-ART-WAVE.md) and
[runtime finish notice](../../assets/materials/rama-finish/NOTICE.md) preserve
that distinction. Technical fabric does not establish historical silk
authenticity. No new normal map, commercial model or game shader was imported.

## Official rendering references translated into concrete checks

Four official Godot documentation files were retrieved at
`godotengine/godot-docs@b10b7ed373c2d15555186914b82e167169b5b87b`; selected
material, spatial-shader and environment sections were read. The lights file
was retrieved for identity continuity but not newly read in this role.
The exact URLs and bytes are in the ledger.

Additional `BaseMaterial3D.xml`, `Environment.xml` and MIT license text were
retrieved at the official `4.6.3-stable` tag. GitHub's tree page resolved that
tag to `35e80b3a8822a9df9be390814b62f44c0a9c69e8`. The installed executable
reports `4.6.3.stable.official.7d41c59c4`; raw URLs for that abbreviated
revision returned 404. These are reference documents with pinned content,
**not proof of source identity for the installed executable**. Actual engine
checks performed by component owners remain the API execution evidence.

| Official contract | Application to this build | Remaining acceptance |
| --- | --- | --- |
| A roughness texture is multiplied by the material roughness scalar; the selected channel matters. | Finish uses scalar 1 and grayscale RED. Courtyard uses packed GREEN. Existing secondary shader's rough sampler has no `source_color`; its albedo sampler does. | Match day/night frames after the channel fix; preserve indigo and gold ornament. |
| World triplanar mapping blends samples from three axes. | Belvedere can reuse stone maps without new UVs, but two maps require multiple samples per fragment. It is not free because the mesh count is bounded. | Actual camera-distance readability and hardware frame timing; avoid relying on triplanar for crisp motifs. |
| Subsurface scattering is a Forward+ effect; skin mode changes its color response and global scale affects depth. | The new skin strength is a presentation adjustment, not new anatomical geometry. | Inspect ears, nose, silhouette and backlit boundaries for halos; confirm selected viewport and renderer support it. |
| Metallic and specular are distinct. Specular changes away from 0.5 are an artistic, non-energy-conserving control. | Current lowered skin/hair/cloth specular values are deliberate stylization. Roughness controls highlight spread. | Compare material hierarchy under identical lights; do not describe the chosen constants as measured physical skin. |
| SSAO is screen-space; high strength can distract. Glow bloom above zero sends broader image content to the glow processor. | Modest AO radius and zero bloom support clear nearby geometry; practical lights can retain local glow. | Check faces, contact shadows, bright cloth and night silhouettes. GPU cost is unmeasured. |
| Writing `ALPHA` invokes transparent sorting; emission alone does not illuminate surrounding geometry without an appropriate lighting system. | The ability shader has no implied physical light source. Owner-driven phase correctly avoids independent shader-time motion during pause. | Overlap and camera-crossing captures; bounded color rather than an obscuring full-frame glow. |

## Where REA helps this art pipeline

REA 6.5.0 is installed. The current compiled MikkTSpace bridge still hashes to
`0f038e6f83f5fce5e10d0b8c14028f96ed7368229c59bded44a2512dda91bb4a`, matching
the [previous actual-component analysis](../evidence/reuse-study/rea/native-component/summary.json).
That earlier Ghidra/REA work checked the selected callback layout and bridge
guards; independent native calls resolved a misleading decompiled NaN
predicate. The present role checked installation/input identity only and did
not rerun unchanged analysis or count it as new graphical progress.

The tangible reused algorithm is the existing permissive MikkTSpace authoring
tool. Its unresolved corner/UV findings still prevent unconditional tangent
replacement. REA is useful when a new compiled authoring component has a
specific numerical or layout question with a separate executable oracle. It
does not generate anatomy, costumes, hair, animation or an accepted render.
The current GREEN-channel defect was resolved by inspecting real image bytes
and documented material semantics; binary analysis would add no evidence.

No new books, Reddit comments or videos were read in this bounded assignment.
Deadlock, Overwatch and Dota 2 client files and rendering implementations were
not available or analyzed. Commercial-game visual parity, final character art,
physical-GPU performance and native multiplayer remain separate open gates.
