# Art tool and source checks — 16 October 2026

The implemented route is an original Blender asset builder around pinned, separately licensed **CC0 MakeHuman anatomical data**. It produces skinned GLB files with modeled clothing, ornaments, hair, weapons and original motion. Generated concept sheets guide composition; they are not represented as recovered meshes or finished runtime geometry.

## Observed here

- Blender 4.3.2 is installed at `/usr/bin/blender`. Headless mesh creation, native skeleton reconstruction, skinning, GLB export, GLB JSON inspection and CPU Cycles renders were executed successfully.
- Five CPU cores and approximately 33 GiB memory are available; no NVIDIA device, `nvidia-smi`, or `/dev/dri` was observed. Disk space was recovered by the parent from disposable build cache before production assets were authored.
- Draco's optional native library is absent. Ordinary uncompressed GLB works. Cycles CPU rendering works; OpenImageDenoise is unavailable, so preview denoising is disabled. There is no installed image-to-3D connector in the available tool list.
- The initial independent deformation proof exported 13,380 anatomical vertices / 26,756 triangles, 163 joints, normalized maximum-four skin influences and preserved UVs. The original joint probe moved 7,969 male-body vertices by more than 1 mm, maximum 0.4635 m. These are technical export checks, not a claim of polished animation.
- Production artifacts and their current counts/hashes are recorded in [hero-assets.json](hero-assets.json). Preview PNGs are actual Blender renders of the authored geometry. The artifact manifest is regenerated during builds and is the authoritative inventory; visual and runtime acceptance remain separate gates.

## Source actually used

[MakeHuman Community](https://github.com/makehumancommunity/makehuman/tree/a8bc2d54ff0ac92e78ff71431b1023eda42bf482), commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`:

| Data inspected and imported | Scope |
| --- | --- |
| `makehuman/data/3dobjs/base.obj` | Only the continuous `body` surface, UVs and original source indices; helper vertices locate the skeleton but are not exported as visible anatomy. |
| `makehuman/data/rigs/default.mhskel` | Native joint positions, hierarchy and orientation planes; 163 bones retained. Bow assets add one original string helper. |
| `makehuman/data/rigs/default_weights.mhw` | Native anatomical skin weights; four largest positive influences normalized per vertex. |
| `makehuman/data/targets/macrodetails/asian-male-young.target` and `asian-female-young.target` | Adult base morph data. These are source filenames, not a claim of Indian ethnic or cultural authenticity. Original stature/width/face proportions and costumes are applied separately. |
| `LICENSE.md`, section C; `LICENSE.ASSETS.md`; file headers | Bundled mesh, morph and graphical asset data are CC0-1.0. Rig/weight metadata independently declare CC0. The MakeHuman application code has a separate AGPL license and is not copied or imported. |

Exact HTTPS URLs, retrieval results, byte counts and SHA-256 hashes are bundled in [sources/makehuman/manifest.json](sources/makehuman/manifest.json). Original license texts accompany the data. Source acknowledgments preserve the creators' provenance even where CC0 does not require attribution. Blender is a build tool; its executable is not redistributed with the game.

## Alternatives read, not executed

| Repository and pinned revision | Actual reading | Decision and limits |
| --- | --- | --- |
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR/tree/107cefdc244c39106fa830359024f6a2f1c78871), `107cefdc244c39106fa830359024f6a2f1c78871` | Official README and MIT LICENSE. README describes MIT coverage for code/pretrained models/demo and a default 6 GB VRAM requirement. | No weights downloaded or inference executed. Upstream A100 performance is not a local measurement. CPU inference time and useful riggable output are unverified here; generated topology would still require human cleanup and rigging. |
| [Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/tree/f8db63096c8282cb27354314d896feba5ba6ff8a), `f8db63096c8282cb27354314d896feba5ba6ff8a` | Official README and custom LICENSE. README lists 6 GB VRAM for shape and 16 GB for shape+texture. | No weights or inference. The custom license excludes EU/UK/South Korea from its territory and has a large-service commercial threshold; it is not a general MIT asset route for this worldwide browser build. |

No proprietary game models, commercial animation rips, paid service credentials, or unverified downloaded executables are used. No claim is made that these two reconstruction projects or the MakeHuman repository were read wholesale.

## Rebuild and review

From repository root, with Blender 4.3+:

```sh
blender -b --factory-startup -t 2 --python games/yuga/art/pipeline/build_heroes.py -- rama hanuman sita --preview
blender -b --factory-startup -t 2 --python games/yuga/art/pipeline/build_heroes.py
```

Source PNGs remain in `art/textures`; export embeds downscaled JPEG base color. Mesh skinning, continuous anatomy, cloth folds, broad pose changes and distinct silhouette need inspection in the exported asset, not just key art. Current limitations include no LODs, cloth simulation, facial blendshape expressions or film-quality sculpting. The initial goal is a credible original browser hero roster; illustration parity is not claimed.
