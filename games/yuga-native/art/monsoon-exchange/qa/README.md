# What the district drawings and meshes agree on

Sun Court has four surveyed entrances. Indigo Cistern has three. From either team’s spawn, a standing YUGA body can reach either ritual floor with any one of that site’s doors left open. Removing all the doors makes the corresponding site unreachable on the sampled floor. Both spawns have completely dry routes to both sites. The seven thresholds, two shelters per threshold and both deployment groups are drawn in the [four-sheet field survey](../plan/floorplans.pdf).

| Question | How to read the evidence |
| --- | --- |
| Is the print registered? | All three plan views independently reproduce 13 room rectangles, 46 passage polygons, 179 exterior runs, 20 cover footprints, seven threshold lines, ten deployment pads and both ritual disks. The two enlargements locate each pictured standing shelter. Two measured terrain sections cross 174 test positions. The PDF stays searchable at A3 and its pages render within the image-comparison tolerance of the corresponding SVG. [Drawing results](drawing-verification.json) |
| Is there actual floor at the surveyed elevation? | Downward rays sample the centre and four corners inset 6% on each of 59 walking patches. Each exterior boundary has a supporting floor sample 12 cm inside, a miss 12 cm outside and a horizontal hit on its own modeled wall 25 cm above floor level. Each corner return must supply its own wall face even where two masonry edges touch. [Mesh results](geometry-verification.json) |
| Can a standing player follow each passage? | Across the 18 connectors, 2,619 foot rays sample the centre and both sides every 40 cm or less. An adaptive 0.65 m radius body-clearance check covers 873 centre positions. A second series of 7,569 rays per file crosses the full visible scene, including art and overhangs, at knee, torso and eye height. [Mesh results](geometry-verification.json) |
| Do the entrances and cover work? | Each entry has 15 standing samples across and through its opening. At every printed pinpoint, rays from an eye 2.5 m outside the threshold must pass through that aperture and hit the named cover before reaching the body. Eight directions at foot, torso and head height give 336 real-mesh hits across the two sites. A second observer 3 m outside each entry tests five additional silhouette points at independently located hiding places. [Cover and position records](geometry-verification.json) |
| Does the objective leave space? | Both sites support 49 positions from the centre out to 2.95 m. Each team has five spatially distinct standing pads. Dry connectivity excludes the wet runnel and cells within one body radius of it. The 0.75 m grid tests whether a route exists. Use the separate 0.5 m route analysis for planned walking times. [Geometry checks](geometry-verification.json) · [Design timings](../plan/metrics.json) |
| What ships in 3D? | The Blender file reopens with its materials packed and twenty editable hidden cover guides. The GLB reader decodes binary indices, vertices and node transforms directly, then converts glTF coordinates to Blender east/north/up as `[x, −z, y]`. Blender also reimports the entire GLB for the full-art line tests. Both files have the same visible district roles. The native lighting studio has a backdrop for render composition. [Scene results](geometry-verification.json) |

The north-up and oblique cameras include all 236 floor-patch corners. The three street-level cameras sit 1.60 m above their local floor. Sun Court’s lotus disk is in the foreground of its photograph. Indigo Cistern’s west-facing photograph shows steps descending into the ornamental basin outside the court. The playable shallow runnel is east of the cistern on Sluice Walk and is marked on the floorplan. [Render register](../renders/render-register.json) · [District plan](../plan/floorplan.svg)

## Reproduce the checks

From the repository root, run these commands with Blender 4.3, Inkscape, Python, NumPy, Pillow and PyMuPDF. The first command measures the saved diagrams and compares separate rasterizations of each SVG and PDF page. The second opens the saved 3D files and exercises both. An exit status of zero means the structural measurements and input hashes match the receipts and the independently rasterized pages pass the image tolerances. Font rasterizers can yield slightly different pixel averages. The receipts include the input hashes. Omit `--check` to record a reviewed change.

```sh
python games/yuga-native/art/monsoon-exchange/qa/check_drawings.py --check
OPENBLAS_NUM_THREADS=1 blender -b -t 1 --factory-startup --python-exit-code 1 \
  -P games/yuga-native/art/monsoon-exchange/qa/check_meshes.py -- --check
```

The clearance rig comes from the shared hero design. At a fixed location the checks ask whether a 1.80 m body with a 0.65 m radius fits and where its 1.60 m eyes can see. Door closures and wet-floor exclusion are temporary changes to the sampled graph. They preserve the artwork on disk. Zero-radius triangle rays check the modeled surface at each surveyed patch. The maximum accepted deviation from survey elevation or disagreement between the two files is 2 mm. [Shared field rig](../../../docs/design/ember-rite-5v5/atlas/vertical-play/heroes.json) · [Sampler](walks.py) · [Mesh and export checks](check_meshes.py)

In the first complete art pass, a rib support crossed the Dyers’ Passage exit at district coordinates (−34, −12). The visible-geometry check caught it. The artist opened the bay. At six site shelters, the initial 2D hiding positions exposed an edge of the standing silhouette around the tapered furniture. Moving each pinpoint 0.5–1 m brought all 24 tested points behind that prop in both formats.

## Runtime verification

A standing route witness establishes a position from which that sample is reachable or hidden. Cover changes with the observer, animation and camera. Competitive side advantage, network-authoritative interaction, wet movement speed, airborne ability clearance, projectile collision, shoulder-camera visibility and frame time on player hardware need in-engine testing and 5v5 sessions. [Map playtest priorities](../design/architecture.md)
