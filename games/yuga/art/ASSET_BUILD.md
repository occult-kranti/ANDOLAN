# Authored hero asset build

Measured from the frozen 16 October 2026 GLBs. These are original stylized browser costumes, faces/hair additions, weapons and animations around licensed CC0 anatomical data. They substantially replace the primitive character placeholders. They do **not** achieve the generated concept sheets’ sculpting, texturing or cinematic quality.

The fourteen external models total **46,520,992 bytes (44.37 MiB)**. A selected match may reuse models; this table is the complete roster download inventory, not a measured initial-page transfer or GPU-memory budget.

| Hero | Triangles | Exported vertices | Materials | Joints | GLB bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| rama | 47,648 | 25,929 | 9 | 164 | 3,537,764 |
| hanuman | 52,472 | 28,537 | 10 | 163 | 3,372,660 |
| sita | 47,938 | 25,956 | 9 | 163 | 3,209,348 |
| ravana | 49,865 | 27,036 | 9 | 163 | 3,285,496 |
| arjuna | 48,035 | 26,114 | 9 | 164 | 3,525,940 |
| duryodhana | 50,481 | 27,480 | 9 | 163 | 3,290,176 |
| karna | 49,916 | 27,233 | 9 | 164 | 3,276,564 |
| bhima | 49,621 | 27,019 | 9 | 163 | 3,269,816 |
| meghnad | 48,034 | 26,113 | 9 | 164 | 3,516,820 |
| draupadi | 47,938 | 25,977 | 9 | 163 | 3,208,820 |
| subhadra | 48,296 | 26,206 | 9 | 163 | 3,222,772 |
| hidimbi | 48,816 | 26,516 | 9 | 163 | 3,241,344 |
| chitrangada | 47,898 | 26,026 | 9 | 163 | 3,205,468 |
| ulupi | 52,548 | 28,352 | 9 | 163 | 3,358,004 |

All fourteen contain `idle`, `run`, `fire`, `cast`, `cast1`, `cast2`, `cast3`, `jump` and `defeat`. Four bow heroes add an original skinned bowstring helper to the native 163-joint skeleton. Anatomy is 1.73–2.08 metres tall; crown/weapon bounds extend beyond the anatomy height. Export is metre scale, +Y up, +Z forward. Character collision and authoritative positions are unchanged by art.

Exact GLB, source-data, source-texture and pipeline SHA-256 values are in [hero-assets.json](hero-assets.json). The licensed data, exact source URLs, terms and hashes are bundled under [sources/makehuman](sources/makehuman/manifest.json). No downloaded MakeHuman application code or commercial game asset is included.

## Actual verification

- [Independent exported-GLB check](../docs/evidence/hero-assets-check.json): all fourteen passed buffer/accessor/index, joint/weight, finite skinned samples and generic transition checks. It sampled17 times per required clip and432 generic TRS crossfades per model; it does not establish every runtime frame or artistic correctness.
- [Independent authored deformation check](../docs/evidence/animation-final-authored-deformation.json):126 clips /5,052 frames on full continuous anatomy, zero root translation and exact loop closure in the authored data, no nonfinite or frozen motion. The most negative anatomical vertex was approximately20.52mm during Bhima’s run, within the chosen35mm check threshold.
- [Rama hand/string measurements](../docs/evidence/animation-rama-grip-validation.json) verify the actual closed grip and moving skinned string. This is a contact/deformation check, not professional animation polish.
- Actual PlayCanvas exploratory priority-trio captures are recorded separately in [exploratory-priority-gallery.json](../docs/evidence/exploratory-priority-gallery.json). Final runtime browser acceptance is owned by QA; do not infer it from Blender or binary checks.

## Deliberate limits

The measured9–10 material sections and3.2–3.5MB typical files exceed the initial four-section/~2MB proposal. No LODs, compressed geometry, cloth simulation, facial blendshape acting or bespoke hand-sculpted head for every hero is present. Face proportions and modeled additions vary around two underlying adult anatomical morphs. Clothes use modeled folds, image-generated source brocade/gold and an original mathematical jacquard; these are base-color textures, not recovered game materials or automatically inferred normal maps.

Generic animation transitions and long garments can intersect or pool against the ground. QA observed approximately12.25cm of full exported Sita geometry below the floor in defeat, while her continuous anatomical surface reached only1.409mm below it; this is a costume/prop presentation limitation, not a simulation penetration or body-rig failure. Further visual review determines whether individual garment poses should be reauthored.

Preview PNGs under `previews/` include iterative Blender renders; their filenames do not alone certify the latest binary hash. Use the frozen manifest and timestamped final QA evidence for release identity. `pipeline/render_saved.py` renders local saved authoring files without rewriting GLBs. Full rebuild commands and tool/source checks are in [tools-research.md](tools-research.md).
