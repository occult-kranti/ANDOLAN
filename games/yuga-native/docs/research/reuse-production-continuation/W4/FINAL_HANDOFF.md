# W4 handoff: four existing-source bank features

**Delivered:** two carved columns and two diya assemblies are enabled by default
in native Confluence. These reuse 29 complete source components from the existing
CC0 courtyard, with the current water, ground, reeds and lotus unchanged.

- Scene: `assets/world/lanka-water-garden-candidate.scn`, 3,474,458 B,
  SHA `69cebe64d18b6acadc16c5b43c2d4fd4ae069793590a909f2b636ba81cc64dd0`.
- Canonical helper: `scripts/lanka_water_garden.gd`, SHA
  `84f306a9caf021c1bbf602d0059abbd42129d20e49cc62df775aa04ba023dfde`.
  Its stable UID is `uid://dht5wp6kprvg7`; the tool mount is a wrapper.
- Four source-derived bodies, 2,688 visual / 760 collision triangles,
  14 mesh instances / 7 meshes, 5 materials / 2 immutable collision shapes.
- Original 8 authority solids, 8 decks, 10 anchors and source map manifest remain
  unchanged. The production army privately composes 39 boxes: original 16,
  gate 10, garden 4, relay 9. Army code is unchanged.

The root and W1 independently viewed all six original matched day/night/detail
images and accepted these four bank features. This acceptance is narrower than
a complete wet district, animation/roster/online milestone or commercial quality.

## Executed checks

| Actual check | Result | Receipt |
| --- | --- | --- |
| Source/cache/transform and copy controls | 17/17 | `evidence/mount-probe.json` |
| Initial corrected full-world candidate physics | 34/34 | `evidence/preflight-r2.json` |
| Six original matched renders and real physics/state controls | 46/46; exit 0, 52.667 s | `evidence/capture-r1*.json` |
| Default production garden + gate + army composition | 31/31 | `evidence/integrated-r1.json` |
| Existing gate integration with new default garden | 23/23 | `evidence/gate-combined-r1.json` |
| Unchanged strict resource suite | 40/40 | `evidence/resources-r1.json` |
| Legacy floor oracle with explicit gate/garden opt-out | 29/29 | `evidence/legacy-physics-r1.json` |
| Current integrated-view headless UI preparation | 18/18 | `evidence/integrated-views-preflight-r1.json` |
| Three current integrated originals | 24/24 image/state/UI checks; **wrapper timeout** | `evidence/integrated-capture-r1*.json` |

W1 additionally ran 15 independent native mount controls, nine source-selection
rows including a removed-face negative, and reviewed all six original images.
Its separate packet owns those results. Do not sum overlapping checks as unique
whole-game coverage.

## Current capture limitation

R1's six matched originals are preserved, including their explicitly staged,
stale spawn HUD. The later three integrated images refresh the real UI owner
and correctly show West reed court, the player marker and day/night status. Those
images belong to composed world `178e73e34ec538180709e358824c45b71edd56a4484f86d118e828b7763d0f60`,
with W6 camera helper `4bf8e41a03b115d3bf5f9f79c238bc15d592975c500a29817db3481083aca787`.

The latter renderer printed completion but then missed the 240 s process-exit
bound. The wrapper failed and stopped only its owned engine/Xvfb. All three
actual images, checks, source hashes and the failed wrapper are retained. Static
review found the same teardown sequence as the successful six-view run; cause
is unproven. No runtime edit was made in response. W2's real-input Quit gate has
priority and must retain its own outcome. Do not relabel the failed wrapper.

## Next owner and commands

Root owns source publication, current CI, packaging and W2's ordinary input.
The exact CI integration command from repository root is:

```sh
godot --headless --path games/yuga-native \
  --script tools/lanka-water-garden/test_integrated.gd -- \
  --output=/absolute/fresh/water-garden-integrated.json
```

The current public-image candidates are the three originals under
`views/integrated-r1/`; publish them as staged visual evidence with the exit
limitation. No further heavy render is authorized until root grants a new lane.
No worker should mutate runtime files during W2's source freeze.

Next design/optimization work: ordinary input and live combat around the wet
court; temporal/distance readability and source-derived LOD; package execution;
then shared texture/palette resources. Exact decoded image comparison found
12 source images duplicated between the two self-contained gate/garden caches,
9,437,184 decoded bytes. This is a concrete reuse opportunity, not a measured
VRAM saving. Preserve exact pixels/materials/physics and verify resource identity.
