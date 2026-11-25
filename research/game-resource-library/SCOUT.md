# Scout new game resources on GitHub

A designer looking for a rig exporter, an accessible HUD or a WebGPU rendering example can run the scout against public repositories. Each candidate links to a file at the default branch's observed commit and shows the filename, directory or format that earned its rank. The report also links to nearby repository terms found during exploration. A reviewer can then inspect the implementation and any asset-specific notices before adding it to the curated library. [Scout](tools/scout.py) · [Ten search recipes](search/scout-recipes.json)

## Run a search

From the repository root, use Python 3.10 or newer. The scout uses the standard library. These commands list the available domains, open the included sample locally, and search for new rig, interface and audio candidates.

```sh
scout=research/game-resource-library/tools/scout.py
python3 "$scout" recipes
python3 "$scout" replay --project Babylon
python3 "$scout" run --recipe blender-rigs --recipe game-ui --recipe audio \
    --inspect 6 --tree-calls 8 --max-requests 60 --out /tmp/art-and-audio.json
```

Use GitHub repository search qualifiers with `--query`. Use `--match` for file and directory terms and `--ext` for a file format you want to prioritize. Repeat any of these options. A matching filename can appear in any language. For an exact repository search, a path hint is particularly helpful.

```sh
python3 "$scout" run --query 'repo:Arminando/GameRig' --match rig --ext py \
    --inspect 1 --tree-calls 6 --max-requests 8 --out /tmp/rig-files.json
python3 "$scout" replay /tmp/rig-files.json
```

The recipes cover Blender rigs, game UI, shaders and textures, mod interfaces, level editors, accessibility, audio, browser/WebGPU, animation and source ports. Change the recipe JSON to add terms or file types used by your team. Search terms control which repositories are discovered. File and directory terms then rank entries in the selected repositories. [Recipe definitions](search/scout-recipes.json)

## Read a result

GitHub repository results are requested in star order. The scout selects one repository per query in rotation before taking the next rank, deduplicates names and retains each matching query and rank. It resolves the default-branch ref to a commit, then reads individual Git directory trees within the request and entry limits. It prioritizes source containers and relevant domain directories. Hidden metadata and vendored dependency directories are usually skipped. Colors, rendering quality and implementation behavior require direct inspection of the selected files.

A matching filename term earns four points, a directory term two and a recognized extension two. A specialized format adds six. The term counts are capped at three per group. Each saved result exposes its reasons, byte size, Git blob object ID and pinned URL. Candidate file bodies and asset licenses are not analyzed by this scout. A notice path identifies a document for follow-up. A root code license alone does not establish permission to use a texture, sound, brand or model.

Look at `queries[].total_count`, `partial` and `github_incomplete` to see which search results were returned. Each inspected repository lists `directories_attempted`, remaining directories, excluded directory counts, errors, GitHub truncation and the number of candidates before the output limit. Increase `--tree-calls` or `--tree-limit` if the first pass misses an implementation. A partial report is written even after an API error or exhausted request budget, and the command exits with status 2. The default global network budget is 44 requests. Each response has a 5 MiB limit. [GitHub search API](https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories) · [Git trees](https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree) · [Git references](https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#get-a-reference)

## Reproduce the included run

The 25 November 2026 sample used 33 public API requests. Five results per query yielded 15 distinct repositories. Nine directory requests per selected project examined 302 tree entries and produced 59 ranked file candidates, with the top six saved per project. All three searches and repository trees had additional results outside the sample. [Recorded queries, paths, commits and notices](search/scout-sample.json)

| Source project | Example candidate | Matched paths before display limit |
| --- | --- | ---: |
| GameRig | The Blender chain rig and bone utility module. [Pinned chain rig](https://github.com/Arminando/GameRig/blob/f5529583aae75c304f70cc258a341fa1e51cea6b/rigs/chain_rigs.py) | 7 |
| Babylon.js | The core TypeScript WebGPU engine implementation. [Pinned rendering module](https://github.com/BabylonJS/Babylon.js/blob/a39ec0fe92b0cdca30a1cb501581b9d2805b5115/packages/dev/core/src/Engines/webgpuEngine.pure.ts) | 44 |
| Civ V Access | The bridge carrying game events into an accessibility mod. [Pinned event queue](https://github.com/rashadnaqeeb/Civ-V-Access/blob/cf6764a97ee8cfe690c42d5a90698344e87dcd9d/src/engine/CvGameCoreDLL_Expansion2/CivVAccessEventQueue.cpp) | 8 |

```sh
scout=research/game-resource-library/tools/scout.py
cache="$(mktemp -d)"
python3 "$scout" run --recipe blender-rigs --recipe browser-webgpu --recipe accessibility \
    --per-page 5 --inspect 3 --tree-calls 9 --max-requests 36 \
    --cache "$cache" --out /tmp/scout-live.json
python3 "$scout" run --recipe blender-rigs --recipe browser-webgpu --recipe accessibility \
    --per-page 5 --inspect 3 --tree-calls 9 --max-requests 36 \
    --offline --cache "$cache" --out /tmp/scout-offline.json
```

A warm offline run reproduced all selected commits, ranked files, score reasons, notices and tree limits with zero network requests. Search and branch results normally expire after 24 hours. Pinned tree responses are immutable and remain reusable. `--refresh` obtains new responses. `--offline` consults only the supplied cache. `replay` reads a saved report without a cache or a network request. `--use-token` optionally reads an existing environment token for the public GitHub API and never writes it into reports. An empty allocation or missing cache entry is visible in the output.
