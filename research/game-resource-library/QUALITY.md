# Resource library coverage and reuse decisions

This audit uses the shipped database and its pinned source receipts. The rows support different decisions. A project observation helps find a lead, a glTF descriptor answers format questions, and an executed import can demonstrate specific rig or material behavior. The saved notebook runs the SQL behind these figures and includes worked lookups. [Executed audit](analysis.ipynb) · [Database](library.sqlite) · [Integrity receipt](evidence/quality.json)

| Grain | Records | Quality finding | Practical consequence |
| --- | ---: | --- | --- |
| Canonical project locations | 3,922 | 3,922 distinct IDs, 26 more rows than distinct display names | Join on project ID. A name search can find independent repositories. |
| Project observations | 4,544 | 4,492 discovery observations describe 3,870 locations. 578 locations appear in multiple discovery families. | Group by project before counting coverage. Preserve the individual observations for provenance. |
| Curated files or symbols | 191 | 76 projects and 190 distinct file hashes. | Count content hashes when estimating download or source review work. Count element IDs when looking for distinct techniques. |
| Parsed model descriptors | 153 | 152 distinct JSON hashes, one upstream sample collection. | Different sidecar bytes can produce different models from identical JSON descriptors. |
| SVG icon paths | 4,239 | 4,239 distinct SVG hashes, 4,176 distinct display names, one source repository. | Use source path, creator and hash to choose an icon. |
| Direct REA forks | 116,393 | 106,949 have no reported language (91.9%). | Review upstream and fork revisions, changed paths and terms before scheduling a port. |

The two largest overlapping discovery families are Open Source Game Clones and Engine reimplementations, with 506 shared locations. Each source can also make repeated observations about a single location. Among the current pinned duplicates, two OpenRA radar records examine the same C# widget, while the Box Textured and Box Textured Non Power of Two directories have identical JSON descriptor bytes. Keep the project provenance and distinct sidecar paths intact. [Catalog reconciliation](data/discovery-counts.json) · [Model coverage](evidence/model-coverage.json)

## Rights and evidence

- **Icon attribution.** All 4,239 icons have a license link. 61 have CC BY 3.0 terms and no recorded individual creator (1.44% of all icons). Their attribution needs resolution before distributing a copy. The catalog suppresses previews for those entries. [Icon evidence](evidence/icons.json)
- **Code and tool reuse.** Curators assigned 112 elements to adaptation, 62 to study and 17 to terms verification. 5 lack a pinned license link. Every adaptation candidate has one. A pinned software license covers the scoped file and applicable obligations. Media bundled beside a project can carry a different grant. [Audited elements](sources/) · [Schema and verification](tools/library.py)
- **Strength of evidence.** 160 entries record a source read, 18 a format inspection and 13 an executed step. The bulk model importer read descriptors, metadata and model licenses. Its bulk pass downloaded zero external geometry buffers, textures or previews. Separate Blender import records identify actual GLB executions. The SVG pass parsed actual file contents. [Blender records](sources/art.json) · [Model method](MODELS.md)
- **Language and sampling.** Multivalue discovery tags list C++ for 1,072 projects, C for 912 and Rust for 235. A project can appear in several counts. 172 locations have no such language entry. The source catalogs favor clones and engine reimplementations, and the bulk asset corpus concentrates on two collections. These counts describe the collected sample. A single release cannot establish maintenance or popularity trends. [Source scope](DISCOVERY.md)

## Three useful queries

1. **Find a rig to exercise.** Filter model metadata for positive skin and animation counts. 8 descriptors qualify. Fox, Cesium Man and Rigged Figure also have evidence of a Blender import for a binary variant. BrainStem’s custom Poser terms lead to a different reuse decision despite its matching shape. Consult the actual credit breakdown for mixed-license models. [Rig lookup](analysis.ipynb) · [Inspected imports](sources/art.json)
2. **Choose a keyboard UI control.** Search inspected UI for `button AND (focus OR keyboard)`. The Godot capture button offers an MIT implementation for rebinding and restoring focus. The OpenRA command button is classified for study under GPL. Reproduce the keyboard activation and focus-return behavior in the receiving UI before enabling it. [Button lookup](analysis.ipynb) · [UI records](sources/)
3. **Build a Blender material handoff.** Search `(material OR texture) AND (Blender OR glTF)`. The concrete Flight Helmet leather image supplies a CC0 example of packed ambient occlusion, roughness and metallic data. The glTF Blender exporter supplies the Apache-licensed gathering code. These inputs address different parts of the import and rendering task. [Material lookup](analysis.ipynb) · [Art evidence](sources/art.json)

## Reproduce

From the repository root, verify the built database and execute the notebook. Jupyter, nbconvert and a Python kernel are sufficient. The analysis itself uses Python’s standard library and SQLite with JSON and FTS5 support.

```sh
python3 research/game-resource-library/tools/library.py verify
jupyter nbconvert --execute --to notebook --inplace research/game-resource-library/analysis.ipynb
```

The final notebook cell reconciles counts and SHA-256 with the build receipt. The initial cell checks database integrity, foreign keys and the identities in each of its three search indexes. Current SQLite SHA-256 is `ced483ca959419ea94f7f6cabf3ee34b941479dfca013f32795cd370a8e27672`. [Saved SQL and results](analysis.ipynb)
