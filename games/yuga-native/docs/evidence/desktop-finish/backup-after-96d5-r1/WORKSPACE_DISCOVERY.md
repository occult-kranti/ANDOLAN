The full `/workspace` metadata walk completed at 2026-10-18T11:29:21.492678+00:00 UTC. It visited 37,864 directories and 132,000 regular files, recorded 396 symlinks without following them, and pruned only the five `.git` internal directories. There were no traversal errors. `workspace-discovery.json` retains every repository, manifest-root and symlink record. This is a dated discovery census; later experiment outputs are tracked separately by their owner receipts.

The primary product repository is `/workspace/ANDOLAN` at `96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12`, origin `https://github.com/occult-kranti/ANDOLAN.git`. It contains the root TypeScript/Vite client/server (`apps`, root npm scripts), the browser Yuga project (`games/yuga`, root `yuga:*` scripts), and the native Godot project (`games/yuga-native/project.godot`). These are components of one monorepo, not separate Git repositories. No builds or environment readiness checks were run for this inventory.

Four other Git repositories are reference checkouts in scratch:

| Reference | Path under `/workspace/scratch/community-reuse/` | Exact HEAD |
|---|---|---|
| Blender add-ons | `animation/sources/blender-addons` | `b42d68627734cb18af0e6f41537063984313a284` |
| ozz-animation | `animation/sources/ozz-animation` | `744eb9d99f606eda849acb0b1204f7a3dc20bca1` |
| Godot demos | `animation/sources/godot-demo-projects` | `b761b4cd5718a7118f2c95eb55f181d0a5f004f1` |
| Material Maker | `art/upstream/material-maker` | `b4fcad06f0b13785de423c42b36406df605c8321` |

These remain third-party references. Their presence does not establish asset/code reuse permission or inclusion in the game. Installed Godot, Ghidra/JDK, REA and Python tooling under `/workspace/tooling` are development dependencies, not additional owned game repositories.

The 1,043 manifest roots do not represent 1,043 products: 887 are dependency/reference subtrees, 110 scratch snapshots/evidence roots, 12 tooling/reference roots, one primary root, and 33 paths inside the monorepo requiring finer classification. Of the latter, the native Godot project is active product source; `tools/reuse-art` and `tools/native-analysis/rea-runtime` are tool wrappers with separate dependency attribution; `.npm-cache/_npx/...` is cache; the remaining 29 are archived evidence, source snapshots or third-party REA/engine reference material. Archived `project.godot` or `package.json` files must not be treated as additional active checkouts.

For a future cloud draft, use the existing `/workspace/ANDOLAN` checkout, preserve local work, and select the required root npm or native Godot workflow deliberately. This census does not request installs, create a worktree, download references or alter setup configuration. Refer to project `AGENTS.md`, existing setup scripts and the exact engine/exporter provenance before any later execution.

`workspace-discovery-initial.json` preserves the first walk; the final full walk confirms the same five repository identities after later generated outputs. `workspace-discovery-delta.json` records the metadata count delta.
