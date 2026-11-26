# Mandala Rift environment art

Start at Spice Gate and follow the baskets of reeds down to the ford. The ghat bells come into view from the water, and the bazaar’s hanging scales come into view from the cloth yards. Between them the Sluice lifts water over the market. These landmarks let a player read the same district from opposite approaches. [Open the gallery](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/) · [Read the 55-page art book](mandala-rift-artbook.pdf) · [Watch the district tour](tour.mp4) · [Download the complete offline ZIP](https://github.com/occult-kranti/ANDOLAN/releases/download/yuga-mandala-rift-art-2026-11-26/mandala-rift-art-studio.zip)

## Find a subject

The 53 studies cover **15 rooms, 26 connections, six cover objects, three landmarks, the Quarter-turn Pavilion and two ritual vessels**. In the gallery, choose an element to see its environment painting, dimensioned drawing, multiple rendered camera angles and short film. Each detail also offers a standalone model. The pavilion has a further construction plate and a film in which its 62 named parts come apart and return to their surveyed positions. [Southern folded passage](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/#element=route-temple_s-pyramid_s-fold) · [Pavilion parts and motion](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/#element=architecture-quarter-turn-pavilion) · [Water ewer](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/#element=rite-water-ewer)

| For this work | Open |
| --- | --- |
| Read mood, material and light | [District key painting](concepts/hero.webp), [14 painted boards and 53 individual crops](concepts/index.json) |
| Check scale, approach and exit | [Searchable inventory](catalog.json), [north-up drawings and sections](plates/), [original district survey](../../docs/design/ember-rite-5v5/atlas/maps/mandala.json) |
| Inspect the actual modeled shapes | [Blender district](mandala-rift.blend), [portable district GLB](mandala-rift.glb), [53 registered model downloads](models/index.json) |
| Direct a camera, assemble a building or light an object | [Rendered views](renders/), [camera studies](clips/), [pavilion construction](assembly/parts.json), [Cycles lighting plate](lighting/study.webp) |
| Check what shipped | [Decoded media and geometry checks](verification.json), [verification source](src/verify_studio.py), [gameplay rehearsal](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/rehearsal.html?map=mandala) |

## Make another image in this district

Each painting begins with a player decision, viewpoint and one foreground landmark. The Spice Gate departure shows sacks and cart timber close to the eye, reeds at the end of the descending street and a clear walking line between them. Its companion passage to South Temple changes the leading edge to a saffron awning. Matching the plaster, stone and indigo between views leaves plenty of room for their silhouettes to differ.

The lead image used the earlier district sketch as its visual input. The full generation prompt, input hash and original output hash accompany it. Fourteen further art boards group adjacent or related subjects. Each crop records its actual rectangle in the generated board, descriptive text and dimensions. The passage ledger also preserves the approach written for each camera. The lossless edition contains the original panorama, fourteen original PNG boards and a ready-to-use PNG of each of the 53 subjects. Painted dimensions and sightlines are interpretive. The survey drawings and registered meshes supply the measurements. [Original sketch](../../docs/design/mandala-rift-5v5/concept-sketch.png) · [Download the lossless paintings](https://github.com/occult-kranti/ANDOLAN/releases/download/yuga-mandala-rift-art-2026-11-26/mandala-rift-painting-masters.zip) · [Lead-image direction](concepts/hero-brief.json) · [Full prompt ledger](concepts/index.json) · [Passage compositions](concepts/route-boards.json)

Hampi’s market streets, waterside pavilions and waterworks informed the relationship between court and river. The receding upper mass of a Chola temple informed the pavilion roof. The game’s signed public passage, rotated exits and civic ritual are invented. The source notes also document the literary reference for the riverbank. [Group of Monuments at Hampi](https://whc.unesco.org/en/list/241/) · [Great Living Chola Temples](https://whc.unesco.org/en/list/250/) · [Historical and literary decisions](../../docs/design/ember-rite-5v5/atlas/RESEARCH_ROUNDS.md)

## Work in three dimensions

In Blender, expand **world_art** in the Outliner. Each element has a collection named with its catalog ID. The continuous floor and district backdrop each have a separate collection. The district GLB contains 797 placed nodes, 533 mesh definitions and 84 materials. Reused meshes account for the difference between 214,330 triangles counted once per mesh and 261,978 across all placements. The temple crown, mangrove roots, reed cluster and lotus cluster reuse the project’s editable world library. The prop sets add the hollow ewer, shuttered dye cabinet, suspended weighing pans, segmented water lift and four readable fold signs. [Scene builder](src/build_scene.py) · [World kit and donor credits](../reuse-library/README.md)

For one piece, import its GLB from **models/** at unit scale. The district uses metres. In Blender X points east, Y north and Z up. In glTF X points east, Y up and negative Z north. Each individual model has its own local origin. Add the entry’s **origin_gltf_m** to its root to restore its full-district placement. Rooms and ordinary paths include a cut of the measured floor. Each fold includes the two threshold patches and the empty span between them. The model index includes local bounds and hashes. [Model index](models/index.json) · [Individual exporter](src/export_elements.py)

The camera follows the bends on physical routes. On the southern fold it cuts at the mouth and turns right. The northern fold turns left. A single V marks the southern pair and twin bars mark the northern pair. The pavilion film separates four wing pieces, 42 pier components, two threshold inlays, twelve roof pieces and two crown pieces. Its final frame restores their installed transforms. To inspect the actual brass, cloth and stone finishes under physical light, use the companion Cycles sheet. [Paired fold drawings](plates/route-temple_s-pyramid_s-fold.svg) · [Assembly film](assembly/pavilion.mp4) · [Lighting study](lighting/study.webp)

## Rebuild and verify

Run these commands from this directory in a checkout of the source branch. The production build used Blender 4.3.2, FFmpeg, Python, Pillow, Inkscape 1.4, ReportLab, PyMuPDF and Noto fonts. The standard library checks for the concept index and standalone models can run without Blender. The offline ZIP includes the two gallery fonts, the map rehearsal and the input world library. In the extracted **games/yuga-native/art/** directory, run **python3 -m http.server 8000** and visit **http://localhost:8000/**. A repository checkout can also serve the gallery through the [local production dashboard](../../docs/PRODUCTION_OBSERVATORY.md#view-the-work).

```sh
python3 src/catalog.py --check
python3 concepts/verify.py
blender -b --factory-startup -t 2 --python-exit-code 1 --python src/build_scene.py
blender -b mandala-rift.blend -t 1 --python-exit-code 1 --python src/export_elements.py
python3 src/export_elements.py --check
blender -b mandala-rift.blend -t 1 --python-exit-code 1 --python src/export_elements.py -- --roundtrip
python3 src/render.py --threads 3 --stage all --force
python3 src/pavilion_assembly.py
blender -b --factory-startup -t 2 --python-exit-code 1 --python src/light_study.py
python3 src/book.py
python3 src/verify_studio.py
```

The cover uses Cycles. To reproduce the denoised pass, put **oidnDenoise** on the path or point **OIDN_DENOISE** at Intel Open Image Denoise. The camera script also supports a 64-sample CPU render without that executable.

For a review of the shipped files, run **python3 src/verify_studio.py --check**. The verifier opens the Blender scene, decodes every film frame, compares the individual pictures with the source boards and checks all 53 element links in the PDF. Khronos glTF Validator 2.0.0-dev.3.10 reported zero errors and zero warnings on the whole district and all 53 standalone models. The portable scene carries tangent frames for the normal-mapped donor surfaces. Re-importing seven specimens into Blender restored 38 floor samples within 1 mm. [Khronos validator setup](../../tools/research/prepare-gltf-validator.py) · [Validation runner](../../tools/research/check-gltf.mjs) · [Noto font notice](../../NOTICE/Noto-fonts/COPYRIGHT.txt)

## Handoff

The map and existing world-library inputs came from revision `9e59880f31452ce0df8d326cd4f1291b700dc228`. The three review rounds covered the existing survey and visual sources, independent construction and painting, then camera clearance and interchange. A test camera clipped the South Pyramid roof. The published shot uses a clear approach and a cut between the registered mouths. For changes, revise the survey first, regenerate its dependents and repeat the source and decoded-media checks. The next game milestone is testing collision, shoulder cameras and both objectives with heroes in the dressed district. The current public rehearsal uses the tactical floor plan. [Integration and playtest roadmap](../../docs/design/ember-rite-5v5/atlas/PANEL_ROADMAP.md)
