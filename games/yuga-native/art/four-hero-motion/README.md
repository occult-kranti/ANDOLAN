# Four heroes in motion

**For the newest playable Hanuman**, open the separate hero studio. It contains the revised facial sculpt, copper mane, textured costume and Mountain Pulse tail recovery. This four-hero pack keeps the earlier Hanuman as a control for camera-matched comparisons. [Enhanced game, scene and films](../hanuman-hero-finish/README.md)

This production kit contains four animated GLBs, turnaround art, illustrated action beats, four-camera Blender stills, four 3D motion studies and an illustrated film. It is for sculptors, riggers, animators and game designers working on Hanuman, Shiva, Rama and Krishna. [Download the studio kit](https://github.com/occult-kranti/ANDOLAN/releases/download/yuga-four-hero-motion-studio-2026-11-25/YUGA-Four-Hero-Studio.zip) · [Illustrated animator book](animator-book.pdf) · [Watch the signature animatic](media/video/signature-animatic.mp4?raw=true)

Extract the ZIP and open **index.html**. Choose a hero and select **Inspect the animated rig**. When opening directly from disk, pick that hero’s GLB from the **models** folder once. You can orbit, switch actions, slow playback or scrub to a specific pose. The viewer, models and textures work offline. For automatic loading, run the command below in the extracted directory and open **http://127.0.0.1:8000/**. To edit the films, open the corresponding file in **blender/**. Each scene includes packed textures, lights, camera markers, editable NLA actions and effects. For a game engine, import the standalone GLBs in **models/**. [Blender scene inventory](blender/manifest.json)

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

| Hero | Rig | What to study | Production script |
| --- | --- | --- | --- |
| Hanuman | 167 joints · 11 clips | Trace the tail from the back view through its counter-swing. Compare the classic airborne Mountain Descent with the planted caster in the enhanced Mountain Pulse. | [Hanuman](scripts/hanuman.md) |
| Shiva | 163 joints · 9 clips | Follow the trident as a vertical reference while the left knee gathers. The planted foot marks Tandava Downbeat, with the tied damaru providing secondary motion direction. | [Shiva](scripts/shiva.md) |
| Rama | 164 joints · 19 clips | Inspect the bow socket, string and release stages across ordinary fire, Piercing Shot and Dawn Volley. The native rig grips the bow in the right hand and draws with the left. The painted release boards reverse this assignment. | [Rama](scripts/rama.md) |
| Krishna | 165 joints · 9 clips | Compare right-hand disc release, left-hand flute contact and the left index finger rising under Govardhan Canopy. The flute and chakra have dedicated sockets for repositioning and visibility. | [Krishna](scripts/krishna.md) |

**How to use the references.** Start with the concept turnaround for proportions, silhouette and palette. Compare it with the Blender study at the same angle to find differences in the current mesh. The action triptych gives three intended pose shapes. Use the corresponding rig clip to judge arcs and spacing continuously. The illustrated animatic holds each key for reading. Its editorial time differs from the action clock printed on screen. The GLB index retains first and last authored key times in seconds, including export offsets. [All 48 action tracks](motion-index.json) · [Illustrated shot timeline](evidence/animatic.json)

**What ships in the game.** Hanuman and Rama use existing project assets with enhanced controller tracks baked into their rigs. Shiva and Krishna are new animated development models. Their scripts include proposed aim, hit, support, cancel and counterplay rules. They have no playable entry in the current fourteen-hero roster. Some directions for fingers, face, fabric and VFX remain animation targets. The new hero meshes reproduce a simpler fabric, hair and surface treatment than the generated key art. The gallery makes both visible for review.

## Sculpt and rig handoff

- **Hanuman.** Compare the muzzle and copper mane at profile. The mesh has a narrower tail tip and shorter groom than the painting. Preserve the existing tail weights while shaping the brush and cheek fur. Use the rear view for the tail attachment; the reference profile overlaps the torso. [Concept](media/art/hanuman.png) · [Mesh](media/stills/hanuman.webp)
- **Shiva.** The crescent, trident and raised knee already carry the silhouette. The mesh’s nape locks end at the shoulders, while the painted locks fall well down the back. Prototype that extra length against the trident during the recovery before refining individual strands. [Concept](media/art/shiva.webp) · [Mesh](media/stills/shiva.webp)
- **Rama.** The real bow and forearm obscure the face in the front aim view. Inspect the string and thumb in profile and the eyes from the release-side three-quarter camera. Mark the grip side on any repainted release frame before handing it to a retargeting artist. [Concept](media/art/rama.png) · [Mesh](media/stills/rama.webp)
- **Krishna.** The feather and disc read from profile. The painted loose curls and overlapping yellow dhoti folds still need sculpting around the existing cap, braid and simpler garment. Check the flute clearance again after reshaping the shoulder drape. [Concept](media/art/krishna.webp) · [Mesh](media/stills/krishna.webp)

## Sources and rebuild

The project’s YUGA anatomy importer, costume and face tools, IK solver, packaged MakeHuman data and 163-joint foundation supply the two new meshes. The new Blender authoring scripts build Shiva’s jata, crescent, rudraksha, trishula and damaru, and Krishna’s feather barbs, ocellus, bansuri and beveled chakra. The topology is skinned and each GLB embeds its textures. Hanuman uses the native 167-joint asset and enhanced motion library. Rama uses the native near mesh and baked controller poses. Read the project’s asset notices for source-specific terms. [Hero art pipeline](../../../yuga/art/pipeline/) · [MakeHuman data and license](../../../yuga/art/sources/makehuman/) · [Native asset provenance](../../NOTICE/ASSET-NOTICE.md)

The nine concept and storyboard images were generated with ImageGen. These paintings establish the visual target for future character sculpting and surfacing. The Blender stills are rendered from the four GLBs. The four moving 3D studies are rendered in PlayCanvas against the project’s Lanka courtyard with sampled skeletal actions. The signature animatic is edited from the illustrated frames. [Hanuman and Rama art directions](prompts/hanuman-rama.md) · [Shiva and Krishna art directions](prompts/shiva-krishna.md) · [Ensemble concept](prompts/ensemble.md)

From the repository root, regenerate the two new models or bake the two enhanced existing rigs using the same tools as the moving film. A Blender 4.3.2 rebuild of Shiva and Krishna produced byte-identical GLBs.

```sh
kit=games/yuga-native/art/four-hero-motion
blender -b -t 2 --python-exit-code 1 -P "$kit/tools/build_models.py" -- shiva krishna
python3 games/yuga-rust/tools/pack_rama.py --lod near "$kit/models/rama.glb"
cargo build --release --locked --manifest-path games/yuga-rust/Cargo.toml --bin hero_export
games/yuga-rust/target/release/hero_export games/yuga-native/assets/heroes/hanuman/hanuman.glb games/yuga-native/assets/heroes/hanuman/hanuman-ability-motion.tres "$kit/models/hanuman.glb"
python3 "$kit/tools/motion_index.py"
```

Each 3D film has an adjacent JSON record of its camera shots, source clips, timings, sampled bone transforms and file hash. The package includes offline notices and SHA-256 checksums. The repository retains the art-generation prompts, build sources and verification tools. [Video and shot records](media/video/) · [Blender studio renderer](tools/blender_stills.py) · [Motion renderer](tools/render/) · [Validation evidence](evidence/)
