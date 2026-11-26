# Monsoon Exchange atlas viewer

Open the district painting, inspect the survey at either ritual court, and compare the same location in a Blender camera and interactive 3D. **Floorplan** opens first. Its floor patches, walls, water, cover, connections, site discs and room coordinates come from the editable survey and its registered geometry. Select a site on the plan or through **Inspect a location**. **Blender view** shows a rendered camera frame. **Orbit in 3D** fetches the engine and GLB on demand. [Public atlas](https://occult-kranti.github.io/ANDOLAN/production/monsoon-exchange/) · [Survey source](../plan/survey.json) · [Compiled geometry](../plan/geometry.json) · [Scene and cameras](../scene/scene-register.json)

To open the source checkout locally, start the following server at the repository root and visit `http://127.0.0.1:8000/monsoon-exchange/viewer/`. Keeping the server rooted at `art/` also makes the existing font sources available. Once the repository is present, viewing the district requires only a local HTTP connection to that server. External links lead to research and credits on GitHub.

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory games/yuga-native/art
```

## How the views line up

The drawing projects the survey’s east and north coordinates onto SVG. Floor and wall geometry come from the plan build, so an opened threshold remains visible in the diagram. The selection ring follows the exact room rectangle. Sun Court and Indigo Cistern show the room dimensions, floor elevation, ritual radius, registered entrance count and named links. **Routes** and **Cover** control two independent drawing layers. Open the measured SVG or the PDF to see printed dimensions and section profiles. [Floorplan](../plan/floorplan.svg) · [Floorplans and sections](../plan/floorplans.pdf)

The orbit viewer reuses the local Three.js loader and orbit-controller approach from the Dust II rebuild. It imports the original YUGA district GLB. The survey and Blender use east, north and up. Three.js reads glTF coordinates as east, up and negative north. The three landmark camera positions and targets use that transform. The entire-district camera fits the exported bounds. The static overview preserves the Blender camera and lighting. The interactive view uses perspective, a sky gradient, image-based material reflections and a directional shadow map computed once for the static architecture. The complete model and rendering library load on the first 3D request. If WebGL is unavailable, the drawings, rendered views and editable files remain accessible. [Orbit implementation](orbit.js) · [Source-map viewer](../../../tools/source-map-lab/viewer/viewer.js)

Choose **Walk a route** inside **Orbit in 3D** to experience one of four measured approaches from Caravan Yard. The camera follows the checked floor path through Copper Arcade, Ledger Balcony, Dyers’ Passage or Sluice Walk at the survey's standing eye height of 1.6 m. Its distance follows the length of each three-dimensional segment, including ramps. The displayed time uses each measured route's 5 m/s walk. All four dry approaches start paused. Scrub to any point, start and pause playback, or use five-metre steps when reduced motion is enabled. Returning to orbit restores the selected landmark camera. The renderer draws on interaction and during explicit playback. [Distance and time measurements](../plan/metrics.json) · [Walk geometry checks](../qa/walks.py)

Tab to a plan marker and press Enter or Space to inspect it. With the 3D canvas focused, the arrows rotate the camera, + and − zoom and Home restores the selected view. On touch screens, drag to orbit and pinch to zoom. The buttons below the canvas provide the same essential actions, including a full reset. **Landmarks at eye level** opens a selected still in the inspector. The district painting, illustrated plan, north-up Blender roof plan and dimensioned drawing can each be opened at full size. A recorded model tour is available in **Working files** and from the WebGL fallback. [District concept](../concepts/district-keyart.webp) · [Painted plan](../concepts/painted-plan.webp) · [Blender roof plan](../renders/north-up.webp) · [Filmed tour](../film/district-tour.mp4)

## Source and tool credits

The browser bundle contains an offline subset of Three.js **0.180.0**, including `GLTFLoader`, `OrbitControls` and `RoomEnvironment`. The builder uses the package URL and SHA-512 already recorded by the source-map lab, extracts an exact file list, and bundles exports with the repository’s installed esbuild. Rebuilding requires Node, the project’s installed esbuild and Python. For an offline build, supply the npm tarball already collected by the map lab.

```sh
python3 games/yuga-native/art/monsoon-exchange/viewer/rebuild_vendor.py \
  --three-tgz /workspace/ANDOLAN-local/dust2-map-lab/sources-of-tools/three-0.180.0.tgz
```

The browser uses the project’s DM Sans and Barlow Condensed font files. The fonts and their OFL notices are already published with the production site. The local edition reads the same files from the four-hero motion viewer. The WebGL scene uses the generated district art and models credited in the district project. [Three.js MIT notice](THREE-LICENSE.txt) · [Pinned upstream package](https://registry.npmjs.org/three/-/three-0.180.0.tgz) · [DM Sans OFL](../../four-hero-motion/viewer/notices/DM-Sans-OFL.txt) · [Barlow Condensed OFL](../../four-hero-motion/viewer/notices/Barlow-Condensed-OFL.txt) · [District design and asset sources](../README.md)

## Browser verification

The test opens the complete local or published exhibit, checks the actual number of floor patches, wall runs, cover positions and links, then uses visible controls to inspect registered sites. It reads real model pixels after an orbit and reset and at all four walk endpoints. It tests reduced-motion stepping, normal-motion play and pause, 320-pixel touch layout, unavailable-WebGL recovery and downloadable files. It records Content Security Policy violations and compares the bytes received by Chromium with the GLB in the working tree. The test uses Chromium, Playwright and Pillow. The saved run used the production Content Security Policy on a local observatory server, with software rendering and a touch-emulated phone. [Executable test](check_viewer.py) · [Browser verification](verification.json)

```sh
python3 games/yuga-native/art/monsoon-exchange/viewer/check_viewer.py \
  http://127.0.0.1:8000/monsoon-exchange/viewer/ \
  --output /tmp/monsoon-viewer.json --captures /tmp/monsoon-viewer-captures
```
