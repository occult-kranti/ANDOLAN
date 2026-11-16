# Open resources for YUGA: Blender, maps, artifacts and engine research

Task **YUGA-RESOURCE-AUDIT-2026-11-15**. Product: **YUGA native · Sanctum**, Godot/Blender, local 5v5 Casual, first to 13; sides switch after round 12. Research session dated **15 November 2026, America/New_York**; machine-readable retrieval receipts use UTC. Starting source: `e59a07a4786e9ad491cfef7a4e706dbd06063adc`, on the existing `work/yuga-studio` checkout. The supplied *Open-Source Hero Shooter Resource Catalog* is a set of leads to verify, not an engine-migration instruction or proof of reuse rights.

**Recommendation: keep Godot, Blender and the existing Rama/Sangam assets.** Spend the next production pass on one finished Sangam encounter and Rama's two-hand contact, face and hair. Reuse CC0 materials, selectively licensed props, small compatible authoring tools and narrowly scoped permissive code. Study other engines where they answer a specific question. Replacing the engine or importing an entire shooter would add migration and asset-clearing work before improving the current game.

## Reading map

| Document | What it establishes |
| --- | --- |
| [Blender and art matrix](BLENDER_ART.md) | Authoring tools, geometry/vegetation, materials, hero bases, temple/heritage artifacts, formats, licenses and practical selection |
| [Engines, games and inspection tools](ENGINES_TOOLS.md) | Released source versus reimplementation versus extraction, code/content split, map tools, networking and build candidates |
| [Catalog corrections](CATALOG_AUDIT.md) | Unsupported claims and Unreal-specific assumptions in the pasted source; primary-source corrections |
| [Next implementation packets](ADOPTION_PLAN.md) | A finite, ordered pilot, named owners, exact deliverables and acceptance gates |
| [Verification and handoff](VERIFICATION.md) | Fresh checks of the inherited studio changes; actual reviewed visuals and remaining limits |
| [Publication receipt](PUBLICATION.md) | Commits, push/deployment results and checks of the delivered dashboard |
| [Blender/art sources](blender-art-sources.json), [engine/tool sources](engine-tool-sources.json), [catalog sources](catalog-sources.json) | Retrieval scope, revisions where resolved, license evidence and inaccessible pages |

The matrices contain recommendations based on source reading. A repository revision or readable license is not a local build result. No newly researched engine, tool, marketplace pack, animation or museum model is claimed installed, imported or production-approved by this task. Previously exercised local reuse has its own [map intake](../map-code-reuse-oct23/README.md) and [production continuation](../reuse-production-continuation/README.md) evidence.

## What we can borrow

| Need | First choice | Concrete use in YUGA | Boundary |
| --- | --- | --- | --- |
| Sangam modular architecture | Existing courtyard/civic GLBs and authored map kit | Reuse piers, lintels, stairs, railings and cover with consistent dimensions and collision | Existing provenance still applies; do not copy a competitor's level layout |
| Stone, plaster, brass and wet surfaces | Existing Poly Haven sandstone first; verified Poly Haven/ambientCG assets when something is missing | One restrained palette with shared materials, normal/roughness maps and a small decal set | CC0 applies to identified assets; website/API terms are separate |
| Original shrine, diya, bell, urn and objective ornaments | Artist-authored Blender meshes informed by cleared historical references | A readable family of small and medium props; reserve the Astra silhouette for gameplay | A museum's age or public access alone does not establish scan/photo rights |
| Hero anatomy and hand repair | Existing Rama rig first; verified CC0 base meshes/MPFB components as anatomy donors | Fix topology/deformation while preserving current skeleton and attachments | Another base model is not a finished hero; community clothing/hair need individual terms |
| Sculpt cleanup, paint and rigging | Blender/Rigify; evaluate RetopoFlow and Ucupaint at compatible versions | Editable sculpt → topology/UV → baked material → deform rig → baked clips → GLB | Add-on source and bundled brushes/examples can have different licenses |
| Brush-based layout experiments | TrenchBroom plus a pinned FuncGodot candidate | Author one original test room with existing cleared materials, then compare with the current pipeline | Importer permission does not license Quake/Source maps, WADs or textures |
| Scene lifecycle and rendering patterns | Godot's official demos, subject to their separate art notices | Compare spawn/cleanup/import practices against current code | Samples can target a different Godot version; port the needed part only |
| Future transport | Existing native authority experiment; study GameNetworkingSockets/yojimbo | Make a measured decision only when the current transport has a named deficiency | Transport alone supplies no matchmaking, rewind, anti-cheat or authoritative game rules |
| Optimization and diagnostics | Existing glTF/meshoptimizer path; RenderDoc and owned-build inspection | Diagnose one observed mesh, material or draw issue, then compare exact before/after behavior | Tool output and software timing do not establish physical-GPU performance |
| Commercial shooter references | Official engineering talks/docs and separately licensed tools | Write original rules from observable requirements; compare clarity, timing and architecture | Viewer/extractor licenses do not grant rights to proprietary game content |

## Reuse decisions must answer three different questions

1. **Can we run the tool?** A GPL Blender add-on can be a useful authoring tool. That does not automatically change the license of independently authored output. Embedded templates, textures, brushes or generated code still need their own review.
2. **Can we ship the result inside a game?** A marketplace or animation license may permit an incorporated game while imposing restrictions on source files or redistribution.
3. **Can we commit the editable inputs to this public repository?** This is the stricter practical filter here. CC0, properly attributed CC BY, and appropriately licensed original/code assets are the simplest starting points. A free price or permission to ship a compiled game is insufficient for raw asset publication.

For example, [Fab's published Standard-license summary](https://www.fab.com/eula) permits compatible tools beyond Unreal and distribution as part of a project, but excludes standalone asset redistribution. Therefore a selected Fab pack requires an acquisition/license record and a distribution decision before public `.blend`, texture or model files are committed. The exact governing agreement and asset acquisition history take precedence over this summary.

Copyleft is not a prohibition on commercial activity. It creates obligations when covered work is distributed; the combined-work boundary matters. Keep GPL/AGPL runtime ports outside the default adoption queue until the project chooses and satisfies the applicable distribution terms. CC BY-SA permits commercial adaptation with attribution, share-alike and no additional restrictions; it is not automatically forbidden in every game store. Our default is a **project simplicity choice**, not a claim that those licenses are noncommercial. [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

## Evidence and scope

The pasted catalog contains contradictory repository activity figures and license generalizations. This study does not use star counts as quality evidence and does not claim exhaustive discovery of every open shooter. Priority upstream repositories are pinned where access allowed. Date-sensitive prices, pack availability, compatibility and license terms must be rechecked at actual acquisition.

The source review does not add assets to runtime or change the commercial-distribution license of YUGA. Existing third-party notices remain applicable. New intake must update the asset manifest and shipped credits together; the [adoption plan](ADOPTION_PLAN.md) specifies the fields.

The inherited studio work has been preserved for publication and checked separately. Its preview animation is presentation, not new full-body tactical locomotion or another finished hero. The older desktop acceptance record stays **17/78 scoped packets, 0/13 complete rounds**; mobile remains **0/108**, deferred. Native online, Ranked, full roster, human feel/listening and physical-GPU qualification remain open. The browser protocol-2 3v3/480-second game is a separate product and has not become native online authority.

Next owner: **world artist + independent reviewer** for packet RC-01, **hero artist + motion reviewer** for RC-02, with the integration lead owning shared manifests, imports and any eventual runtime promotion.
