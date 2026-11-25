# Game resource library

Find a specific game-development element, see what it does, and follow it to its source file and terms. The collection spans classic game rebuilds, modern open engines, interface design, Blender production, character rigs, animation, graphics, audio, level design and build tooling.

The published database contains 191 reviewed elements from 76 projects, 4,392 indexed media assets and 3,922 distinct project locations. A separate inventory records 116,393 REA fork IDs returned by GitHub. [Coverage and checks](evidence/quality.json)

**Open the library.** Download the standalone HTML and open it in a browser. It includes the search index and credited icon thumbnails. Browsing and filtering work offline. Opening an upstream source or a model preview requires internet access. The ZIP also includes the SQLite database, a SQL/Python notebook and source credits. [Download the library](game-resource-library.zip?raw=true) · [Standalone HTML](library.html?raw=true) · [SQLite database](library.sqlite?raw=true)

| View | What you can find |
| --- | --- |
| **Elements** | An individual control, shader, effect, rig, algorithm or authoring tool. Each entry has a commit, exact path, evidence description, reuse assessment and a concrete adaptation. Search for `button`, `focus`, `palette`, `chase camera`, `Blender` or `ward`. |
| **Asset files** | Actual SVG icons and glTF model descriptors. An icon shows its shape, author and terms. A model shows its scenes, materials, skeletons, named clips, extensions and component credits. Filter to **3D model** and try `Survey` for the Fox rig. |
| **Projects** | Rebuilds, engines, ports and browser projects drawn from six overlapping catalogs. Project aliases retain games grouped in a single repository. Open the individual source observations to see what each catalog reported. |
| **REA fork inventory** | The database also has a `rea_forks` table containing every public ID returned by the completed fork listing. Its metadata can suggest a lead. The fork investigation follows actual ancestry and separate game projects. [Fork census and inspection](../../games/yuga-native/docs/rust-rebuild/deep-search/REA-FORK-CENSUS.md) |

## From search result to design decision

- **Design a controller-friendly menu.** Compare the Bevy directional-navigation example, OpenRA’s stateful command button and libGDX’s modal focus restoration. Inspect focus movement, activation and return after dismissal separately. The Kenney and raygui records include a visual comparison of normal, focused, hovered, pressed and disabled artwork where each pack supplies it. [Button-state sheet](evidence/button-state-contact-sheet.png) · [Measurements and credits](search/button-states.json) · [Interface source records](sources/interfaces.json)
- **Test a character pipeline.** The Khronos Fox has 24 joints and the `Survey`, `Walk` and `Run` clips. It credits its components under multiple licenses. The Blender studies include seven actual headless imports. The GunZRs study exercises a game engine’s quaternion sampler against a different production rig and measures a right-wrist interpolation difference. [Model inventory](MODELS.md) · [Art records](sources/art.json) · [Animation comparison](../../games/yuga-native/docs/rust-rebuild/deep-search/gunz-layers/README.md)
- **Study how an older game presents state.** Follow the REA Dune case to a C++ troop engine and a separate Swift palette controller. Or compare the zoomable Doom automap, OpenLara’s follow camera and OpenXcom interfaces. The entries distinguish what was run, what was read and what belongs to the original game. [Dune evidence](sources/fork-studies.json) · [Rebuild elements](sources/rebuilds.json)
- **Choose a rendering or audio component.** Compare GPU particles, physically based materials, mesh optimization and echo processing. The production studies include executable mesh and audio fixtures with measured results. [Production source records](sources/production.json) · [Fixtures and measurements](search/production.json)

An **adapt** assessment means the record links evidence for reusing the identified component under its terms. **Study** identifies a useful implementation or design reference. **Verify terms** marks an unresolved scope or redistribution question. A repository’s software license can differ from the terms for its art, fonts, recordings or engine subdirectory. Each record identifies its own evidence, and the model credits preserve layers with different terms. [Coverage and data-quality checks](QUALITY.md) · [Source-pin audit](evidence/source-pin-audit.json) · [Model credits](MODELS.md) · [Icon credits](notices/game-icons.txt)

## Query or rebuild

Open `library.sqlite` in DB Browser for SQLite or SQLite with FTS5, or run these from the repository root with Python 3.11 or newer. Building uses the pinned local snapshots. The HTML and database do not require a running service, API credentials or a GPU.

```sh
python3 research/game-resource-library/tools/library.py search 'button' --category ui
python3 research/game-resource-library/tools/library.py search 'walk' --assets --limit 10
python3 research/game-resource-library/tools/library.py search 'quake' --projects
python3 research/game-resource-library/tools/library.py build
python3 research/game-resource-library/tools/library.py verify
python3 research/game-resource-library/tools/package.py
```

The data model separates `elements`, `assets`, `projects`, `project_sources`, `element_facets` and `rea_forks`. Three FTS5 indexes support text search at the element, asset and project levels. `assets.metadata` preserves nested glTF counts and component credits. For example, this SQL finds skinned characters and lists their animation clips.

```sql
SELECT name, json_extract(metadata, '$.counts.joints') AS joints,
       json_extract(metadata, '$.clips') AS clips, license, source_url
FROM assets
WHERE kind = '3D model'
  AND json_extract(metadata, '$.counts.skins') > 0
  AND json_extract(metadata, '$.counts.animations') > 0
ORDER BY joints DESC, name;
```

Use the notebook to reproduce the joins and lookups. The discovery guide explains URL identity, multi-game repositories, missing languages and overlap. The scout accepts a new GitHub topic or a custom query and produces pinned candidates for review. A newly found file enters the curated collection after its content, use, evidence level and terms have been recorded. [Analysis notebook](analysis.ipynb) · [Discovery methodology](DISCOVERY.md) · [Automatic GitHub scout](SCOUT.md) · [Rebuildable source records](sources/) · [Measured quality](evidence/quality.json)

The icon collection credits Game-icons.net and its individual artists. The previews resize the original SVG shapes to 72 pixels. Two contributor folders lack a matching artist in the pinned credit list, so those files carry source links and an attribution note without a reproduced preview. For the models, the database carries descriptor metadata, per-component credits and links to the original media. [Game-icons terms and artists](notices/game-icons.txt) · [Open Source Game Clones notice](notices/osgameclones.txt) · [Model terms and source inventory](MODELS.md)
