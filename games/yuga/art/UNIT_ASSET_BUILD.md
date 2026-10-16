# Lane and jungle unit assets

This separate pipeline creates four fictional lane roles and three original grounded guardians. It does not rebuild or modify the accepted fourteen hero GLBs. The units are stylized low-detail battlefield models, not hero portraits or commercial key-art reproductions.

| Asset ID | Visible role and equipment | Motion scope |
| --- | --- | --- |
| `soldier` | Spear Soldier; uniform, breastplate, leaf-point spear and round shield | Grounded shield-bearing march and thrust |
| `city-watch` | City Watch; wrapped turban, civic sash and fictional compact carbine | Grounded patrol, supported aim and short recoil |
| `minister` | Court Minister; office mantle, sealed scroll and ceremonial staff | Grounded advance and presenting the scroll |
| `king` | Crown Envoy; seven-point court crown, mace and small back standard | Grounded heavy advance and mace strike |
| `yaksha` | Grove Yaksha; broad green anatomy, bark plates, branch horns and knotted club | Grounded guardian locomotion; no flight or giant transformation |
| `naga` | Reed Naga; bipedal anatomy, flared ornamental hood, tail and staff | Grounded biped locomotion; no slithering or water invulnerability |
| `sky-sentinel` | Sky Sentinel; avian mask, head crest and folded arm feathers | Grounded movement and wing flare; no flight |

The authority owns colliders, attack ranges, hit effects, economy and spawning. A large shield, tail, horn or banner is presentation geometry and does not enlarge an authoritative hitbox.

The seven exported GLBs total **4,477,524 bytes (4.27 MiB)**. These are measured inventory sizes, not an initial-page transfer or GPU-memory measurement. All seven use 80 joints, four material sections and four clips.

| Unit | Triangles | Exported vertices | GLB bytes | Anatomy height (m) | Full rest maximum Y (m) |
| --- | ---: | ---: | ---: | ---: | ---: |
| soldier | 7,599 | 4,699 | 601,612 | 1.45 | 1.469 |
| city-watch | 7,400 | 4,546 | 596,700 | 1.42 | 1.438 |
| minister | 7,499 | 4,614 | 597,528 | 1.40 | 1.441 |
| king | 7,992 | 4,928 | 626,228 | 1.52 | 1.778 |
| yaksha | 10,000 | 6,027 | 693,364 | 2.05 | 2.186 |
| naga | 10,000 | 5,973 | 689,528 | 1.95 | 1.975 |
| sky-sentinel | 9,495 | 5,693 | 672,564 | 1.90 | 2.023 |

The full rest bounds include equipment and head additions, in glTF Y-up coordinates. Four normalized vertex influences remain after topology reduction and joint pruning. [Hero isolation evidence](../docs/evidence/unit-hero-isolation.json) confirms the fourteen hero GLBs, original five pipeline files and original hero manifest retained their pre-expansion SHA-256 values.

## Provenance and build

The unchanged repository `anatomy.py` imports the already bundled CC0 MakeHuman body/UV, adult proportion target, skeleton and skin-weight data. Upstream is pinned to `makehumancommunity/makehuman` commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`; exact URLs, license texts and file SHA-256 values are in [sources/makehuman/manifest.json](sources/makehuman/manifest.json). No MakeHuman application code, commercial game asset, external motion capture or new package dependency was imported.

New [minion_geometry.py](pipeline/minion_geometry.py) authors the clothing, head additions, weapons and guardian silhouettes using the existing unchanged `Sculpt` surface helpers. New [minion_animations.py](pipeline/minion_animations.py) authors four in-place actions using existing native-bone math. New [build_minions.py](pipeline/build_minions.py) prunes unused face/toe helpers, remaps their vertex weights to retained ancestors, normalizes the strongest four influences and reduces mesh topology. Every model retains 80 actual skin joints and four material sections. The single original woven textile per unit is 256×256 pixels, embedded as JPEG; skin, trim and dark surfaces use authored PBR values. No generated hero texture sheet is duplicated into these GLBs.

```sh
blender -b --factory-startup -t 2 --python games/yuga/art/pipeline/build_minions.py --
```

An optional list of IDs builds only those units; `--preview` renders the resulting models in a CPU studio scene. Assets go to `games/yuga/client/assets/units/`, with measured inventory and source hashes in [unit-assets.json](unit-assets.json). Saved authoring `.blend` files go outside the repository to `/workspace/tooling/yuga-art/output/units/`; they include a hidden full continuous `ValidationAnatomy` bound to the final reduced rig. This copy is excluded from selected GLB export and all previews.

```sh
blender -b --factory-startup -t 2 --python games/yuga/art/pipeline/render_units.py -- soldier yaksha
```

This second command renders the saved `.blend` files without rewriting any shipped model. Preview images are actual Blender renders, distinct from generated concept art. A preview filename alone does not establish final asset identity; the manifest records exact GLB and pipeline hashes.

## Verification and limits

All four required clip names are lower-case: `idle`, `run`, `fire`, `defeat`. The builder evaluates every authored frame of full weighted anatomy for finite deformation, meaningful motion, fixed root, exact idle/run/fire endpoint closure and the chosen 35mm anatomical floor tolerance. This does not certify cloth/weapon collision or subjective movement quality. Exported binary skin/transition checks and actual PlayCanvas browser captures are separate QA gates.

[Independent exported-unit checks](../docs/evidence/unit-assets-check.json) passed the seven GLBs: every accessor, bind geometry and vertex weight inspected, 17 skinned-geometry samples per required clip and 72 generic TRS crossfade samples per model, with no warnings. The report records the exact manifest/model hashes; a subsequent re-export requires refreshing that evidence. Actual saved-model renders of all seven are under [previews/units](previews/units/). The rendered review corrected the initial soldier shield direction, torso collar, boot coverage and minister scroll grip. Browser integration and full-population performance remain separate from these asset checks.

[Independent final authored deformation](../docs/evidence/unit-animation-final-authored.json) binds the saved authoring files to final manifest `3adc9c1be2132d5064d5ac8b4122675d88e2079ca68125eac9ed221c12491776`: seven 80-joint rigs, 28 clips and 1,283 evaluated frames. Roots and idle/run/fire-recovery seams were zero; the worst full anatomical floor minimum was approximately −16.15mm in Yaksha's run, within the selected 35mm tolerance. A final City Watch support-hand correction was inspected in its actual model render; the animation owner's measured palm/receiver error stayed below 0.48mm through fire. These contact checks do not imply professional animation polish or collision-free cloth.

There are no mesh LODs, facial acting, cloth simulation, morph-target expressions or airborne creature rigs. Native rig pruning and small meshes reduce asset costs, but do not establish performance with the maximum population of 90 lane units. Runtime population, draw-call, animation-update, network and frame-time tests remain required. Held props and clothing can intersect during generic blends; report observed defects rather than inferring correctness from a successful export.
