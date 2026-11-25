# Finding reusable game projects

The directory carries **3,870 distinct project locations** from **4,492 source observations**. A developer can search for an original game, engine, language, platform or genre, open the corresponding source row, and then inspect the project’s own code and terms. A repository containing eight games has one location and eight traceable records. The separate component and model inventories describe individual reusable files. [Machine-readable counts](data/discovery-counts.json) · [3D model inventory](MODELS.md)

| Source at its recorded revision | Observations | Distinct locations within source | What the entry establishes |
| --- | ---: | ---: | --- |
| Open Source Game Clones | 3,304 | 3,296 | The catalog’s project type, platforms, languages, playability, development, listed licenses and content class when supplied. Original-game references identify the corresponding genre records. |
| Engine Reimplementations section | 845 | 844 | Project name, URL and language as listed. |
| Awesome REA Games | 140 | 138 | Projects listed under 103 original titles, with the original category and accompanying links. |
| GitHub repository searches | 126 | 114 | Membership in a saved search result. All repeated appearances and exact query strings remain inspectable. |
| Primary repository inspections | 56 | 56 | Pinned README and recorded licensing-file observations. |
| Module inspections | 21 | 21 | Identified implementation files, SHA-256 digests and media-dependency notes for a specific revision. |

**578 locations occur in multiple source families.** The counts file includes exact intersections. The project count excludes REA fork census rows, original-title metadata and individual assets. A catalog’s `playable` tag records the catalog author’s assessment at that revision. Opening an official port, running a test or inspecting a rendered asset yields separate evidence. [Saved inputs and upstream file digests](sources/discovery-inputs.json)

## Identity and evidence

- Repository roots on GitHub, Codeberg and Blender’s forge use normalized host/owner/repository identities. Other project links retain path case, fragments and query values. HTTP and HTTPS variants can represent different historical material.
- The importer joins a website to a repository when a source explicitly pairs the two and the website identifies one location. Four sites appeared alongside competing projects and were excluded from this shortcut. Showcase posts, videos and associated repositories remain source links. A future row supplied solely as a social post or with a missing URL has its own stable source-and-row ID.
- Each source entry retains its original title, index locator, pinned evidence URL and the fields it actually supplied. Merged language, status, content and license lists are useful for discovery. Look at the individual record or module before reusing commercial game data or combining code. A `Rust` language filter in a saved GitHub query is labeled by that exact query.
- A game clone’s `originals` value is an explicit upstream reference. All of them resolved against the **2,005** original-game records. `genres` includes the original’s genre when supplied and the curated list’s category when applicable. Each clone links the original YAML rows. This join never equates two projects by their title.
- **Example.** OpenRA occurs in three source families. The `github:sigmafier/ellaz-games` repository has eight separate clone observations and seven searchable title aliases. Each observation still has its own original-game and content record. [OpenRA project](https://github.com/OpenRA/OpenRA) · [Ellaz games repository](https://github.com/Sigmafier/ellaz-games)

## Reproduce the directory

From the repository root, use Python 3.10 or newer and PyYAML. The checked upstream ZIP contains all 27 game shards, 27 original-title shards and the unchanged attribution file. Five additional input files are local to this repository. Each input is verified against the manifest before indexing. The normal rebuild has no network dependency.

```sh
python -m pip install PyYAML==6.0.3
python research/game-resource-library/tools/discover.py --verify
python research/game-resource-library/tools/discover.py
```

To re-fetch the exact upstream files and compare the resulting catalog, run `python research/game-resource-library/tools/discover.py --refresh-inputs --verify`. The checked discovery archive has SHA-256 `f7afb6b3f357f685eb8008d666f9b29a36639b3ffb7a9d66f400b482ab41d0e0`. The deterministic gzip archive contains a JSON list with UTF-8 names. [Importer](tools/discover.py) · [Normalized projects](data/discovery.json.gz) · [Pinned catalog snapshot](sources/osgameclones.zip)

These queries recover the discovery counts and the individual Ellaz records from the built SQLite library.

```sql
SELECT json_extract(observation, '$.family') AS family, count(*) AS observations,
       count(DISTINCT project_id) AS locations
FROM project_sources
WHERE json_extract(observation, '$.family') IS NOT NULL
GROUP BY family
ORDER BY family;

SELECT json_extract(observation, '$.title') AS catalog_title,
       json_extract(observation, '$.originals') AS originals, url AS source
FROM project_sources
WHERE project_id = 'github:sigmafier/ellaz-games'
ORDER BY seq;
```

**Attribution.** Open Source Game Clones catalog content is © 2011–2016 Vsevolod Solovyov, Alexander Solovyov and other contributors, available under Creative Commons Attribution 4.0. This directory normalizes and joins selected metadata. The upstream license and original files are included in the snapshot. Each listed project and its media have their own terms. [Original catalog at the recorded revision](https://github.com/opengaming/osgameclones/tree/3a6994d85c9e007325a1040f439d778a7ca49a26) · [Catalog terms](https://github.com/opengaming/osgameclones/blob/3a6994d85c9e007325a1040f439d778a7ca49a26/LICENSE)
