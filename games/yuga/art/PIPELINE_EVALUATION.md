# YUGA runtime character pipeline evaluation

Evaluated 2026-10-16. This is an independent capability and acceptance review; it does not certify the appearance of a finished character. The character builder, renderer and browser evidence are separate deliverables.

## Decision

Use Blender with MakeHuman's bundled CC0 humanoid geometry as a starting point, then author the hero's proportions, clothing, hair, face treatment, weapon, materials and animation. Export a skinned GLB and load it in the actual PlayCanvas arena. This is the fastest practical route available in this workspace to replacing the current sphere/capsule bodies with continuous, articulated characters.

No callable image-to-3D service was found in the tool metadata available during this check. Local automatic image-to-3D inference is also not ready: no GPU device or inference stack was detected. The initial filesystem check found approximately 0.52 GiB free; after the parent removed rebuildable Docker cache, a later check found 12.8 GiB free. This removed the immediate storage constraint without supplying a GPU or an inference stack. A generated illustration can guide the mesh and materials; it does not supply a playable, rigged character by itself. This evaluation makes no claim that a quick scripted model will match a polished illustration or a commercial game's character art.

## Observed environment

| Check | Observed result | Consequence |
| --- | --- | --- |
| `blender --version` | Blender 4.3.2 at `/usr/bin/blender` | Local mesh authoring and export can use Blender. Headless asset generation is being exercised by the research agent. |
| Exposed tool metadata | 19 entries at the time of inspection; no advertised image-to-3D, mesh-generation, Blender, Tripo, TRELLIS, Hunyuan or Rodin tool; no deferred tool-search entry | There is no currently demonstrated remote 3D generator to call. This is a statement about the active tool surface, not every service on the internet. |
| Image generation | `image_gen__imagegen` generates and edits images | Useful for concept sheets and texture references. No mesh, UV, skeleton or animation output is advertised. |
| GPU visibility | `nvidia-smi` absent; `/dev/nvidia0`, `/dev/nvidiactl`, and `/dev/dri` absent | No detected accessible NVIDIA or DRM GPU. This does not prove the physical host has no GPU. |
| Python package discovery | NumPy and Pillow present; Torch, Transformers, Diffusers, Accelerate, trimesh, Open3D, OpenCV, ONNX Runtime, safetensors, huggingface_hub and rembg absent | No installed image-to-3D inference pipeline was demonstrated. `bpy` is absent from the ordinary Python interpreter; Blender supplies its own Python API. |
| Capacity | 5 reported CPUs; approximately 33.3 GiB reported memory; free storage increased from approximately 0.52 GiB to 12.8 GiB after cache cleanup | Modest Blender scripts and assets are feasible. These are host-visible observations, not performance guarantees. No large inference model installation or CPU inference benchmark was attempted. |
| Existing engine | PlayCanvas 2.23.3 includes GLB container loading, render-entity instantiation, materials and animation resources | Runtime asset import requires integration, rather than replacing the engine. The current `makeRig` implementation constructs primitive geometry. |

Managed environment status reported a running, connected instance with current observations and no configured secret bindings or outbound identities. Its network-policy state was `unknown`; this is not a blanket connectivity claim. This evaluation installed no packages, requested no paid service and used no new API key.

## Alternatives checked

| Route | Source evidence | Evaluation for this environment |
| --- | --- | --- |
| MakeHuman bundled assets + Blender | Pinned MakeHuman `LICENSE.md`, section C, explicitly includes the base mesh, proxies, targets, textures, clothes, poses and expressions under CC0 1.0. Section D distinguishes output from the separately AGPL program code. The downloaded base OBJ is 1,749,303 bytes; native skeleton and weights are about 1 MiB combined. | Chosen. Provides actual humanoid topology and a small local foundation. It still needs original hero design, fitted clothing, materials, animation and deformation review. Third-party community assets require their own license checks. |
| TripoSR | Pinned README states MIT coverage for code and pretrained models and approximately 6 GB VRAM with default single-image settings. It advertises reconstructed geometry and an optional baked texture. | Credible future experiment on a suitable machine; not run here. No claim that its output has clean humanoid topology, joint weights or a usable animation rig. |
| Hunyuan3D-2 | Pinned README states 6 GB VRAM for shape and 16 GB for shape plus texture. Its pinned custom license contains territory restrictions, including restrictions concerning output, and additional commercial terms. | Not selected. It is not a drop-in permissively licensed replacement, and the required local inference environment is absent. No model weights or generated output were downloaded. |
| More primitives plus a concept-art backdrop | Existing arena code can do this immediately. | Does not address the requested continuous, detailed runtime character geometry. A new illustration or menu background is not evidence of a character upgrade. |

Source snapshots and their SHA-256 manifest are held in `/workspace/tooling/yuga-art/sources` for the current build. This evaluator independently recomputed and matched the manifest hashes for the MakeHuman base, skeleton, weights and licenses, and the TripoSR/Hunyuan READMEs and licenses. These checks establish the local files match the recorded download manifest; they are not a signature verification or an assessment of model quality.

## Build path and integration contract

1. Import the pinned humanoid source while preserving the original vertex-index mapping needed by native weights and morph targets. Remove helper geometry and unused surfaces deliberately. Rebuild or transfer weights if topology changes; do not assume original indices survive arbitrary cleanup or decimation.
2. Establish a convincing body and face before ornament. Check neck-to-shoulder transitions, elbows, wrists, hands, knees and ankle proportions. A recognizable silhouette and continuous facial planes improve the close camera more than additional floating trim pieces.
3. Author clothing and hair as coherent surfaces with thickness or well-controlled backface behavior. Shape a readable mantle, waist, sleeves and boots; fit them in movement poses. Give exposed skin, cloth, hair and metal different roughness and shading. The original team ring and health indicators can remain separate gameplay overlays.
4. Use one coordinated skeleton and stable bone names. Add a right-hand weapon attachment and author idle, run, fire, cast, jump and defeat motions. A source rig can save setup time, but source weights alone do not verify shoulder/elbow deformation or weapon grip. Preview transitions and locomotion in the engine as well as Blender.
5. Export GLB with metres, Y-up runtime orientation, feet at the actor origin and +Z facing forward. Aim for the renderer's roughly 2.2 m character height. Check that Blender-to-glTF axis conversion happens once and that animation bindings survive export. Avoid skeleton renaming after animation paths have been authored.
6. Cache each loaded PlayCanvas container and instantiate an independent skinned hierarchy per hero. Preserve authoritative actor position/yaw, team overlays and hit feedback. Shared mesh/material resources are appropriate; bone state must remain per instance. An import failure must be recorded during QA, even if gameplay uses a fallback to remain available.
7. First validate one representative hero in the arena, including the rear shoulder view that dominates play. Reuse proven rig and material conventions across the roster while varying body shape, clothing profile, hairstyle, weapon and pose. Recoloring the same body twelve times does not establish twelve distinct character designs.

The rendering agent proposes **15–30k triangles per hero, at most six material slots, textures up to 1024 pixels per atlas, and six heroes concurrently**, with inexpensive minion geometry. These are starting budgets, not measured mobile/browser limits. Inspect actual exported primitive counts, skin influences, draw calls, texture memory and match frame times before increasing them. Skinned geometry should not be assumed to batch like the existing static primitive parts.

Generated reference art can help specify front/back silhouette, palette, garment construction and surface detail. A single front illustration leaves unseen geometry ambiguous. Projected image colors also need cleanup for baked lighting, UV seams and distortion. A highly detailed illustration mapped onto an unchanged primitive body does not solve the geometry requirement.

## Acceptance evidence

| Gate | Required evidence |
| --- | --- |
| Real asset | Exported GLB contains mesh primitives, skin/joint bindings and intended animation tracks. Asset URL loads successfully in the deployed build; no missing texture requests. Preserve source URLs, source hashes, license text and a reproducible build command. |
| Appearance | Capture the actual gameplay canvas at the same camera, light and scale as the baseline: front, rear shoulder, side and a moving pose. Inspect face, hair, clothing silhouette, hands and weapon grip. A Blender beauty render or menu portrait cannot stand in for this check. |
| Deformation | Run, fire, cast, jump and defeat without detached clothing, collapsing joints, weapon drift, floor penetration or an exposed bind pose during transitions. Inspect two instances of the same hero in different animation states to detect shared skeleton state. |
| Gameplay readability | Local/enemy/team identity, attack direction, hit feedback and target visibility remain clear in a six-hero fight. Character detail should not hide projectiles or aim cues. |
| Runtime cost | Measure warm and cold load, actual frame times and asset memory in the target browser and viewport. Test low/high quality and repeated match entry/exit. Report software rendering separately from hardware rendering. |
| Failure behavior | Confirm the loaded-asset diagnostic and capture evidence correspond to the new model. Deliberately failing an asset request may exercise a fallback, but fallback screenshots cannot pass the art gate. |

At the time this evaluation was written, the environment inventory, source-license review, local source hash checks and PlayCanvas API inspection had completed. The research agent owns the headless import/rig/export proof; the renderer agent owns game integration; QA owns browser captures and runtime measurements. Those later results must be reported separately. No image-to-3D inference, subjective art approval, finished-roster parity or target-device performance was established by this evaluation.

## Pinned references

- [MakeHuman license and bundled-asset scope](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.md), [CC0 asset license](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/LICENSE.ASSETS.md), [base OBJ](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/3dobjs/base.obj).
- [TripoSR README at inspected revision](https://github.com/VAST-AI-Research/TripoSR/blob/107cefdc244c39106fa830359024f6a2f1c78871/README.md), [license](https://github.com/VAST-AI-Research/TripoSR/blob/107cefdc244c39106fa830359024f6a2f1c78871/LICENSE).
- [Hunyuan3D-2 README at inspected revision](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/f8db63096c8282cb27354314d896feba5ba6ff8a/README.md), [license](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/f8db63096c8282cb27354314d896feba5ba6ff8a/LICENSE).
- Installed PlayCanvas 2.23.3 declaration documentation: `node_modules/playcanvas/build/playcanvas.d.ts`, `ContainerResource.instantiateRenderEntity`, `ContainerHandler`, and `AssetRegistry.loadFromUrl`. This is API availability evidence; successful game import remains a runtime check.
