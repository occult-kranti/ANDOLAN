# Rebuilding a complete editable Dust II fan map

Hanzo's December 2013 RocketMinsta release contains the editable geometry of an entire Dust II remake. We compiled that geometry into a fresh Nexuiz map, generated its visibility and lighting, and made a second playable package with jade ground. This gives an editor-to-engine build alongside the separate Counter-Strike BSP workflow. The two levels have different geometry, entities and rules. [Release catalog](https://xonotic.fps.gratis/ui/maps-index.json) · [Author package with source, description and settings](https://dl.xonotic.fps.gratis/q3dust2-jb-beta6.pk3) · [Rebuild script](../../../tools/source-map-lab/radiant/build.py)

## Which level was recovered

The package contains `maps/q3dust2-jb-beta6.map`, an editable 1,880,759-byte Radiant map. Its 298 source entities span 58 classes. The file has 2,864 editor brush entries, including 507 Bézier patches. It contains 20 free-for-all spawn points, four team spawn groups, 12 doors, two flags and five domination control points. The 25 barrel placements reference the stock Nexuiz model library. The geometry covers both sides of the level, connecting passages and areas above and below the main grade. The readme also documents Hanzo's jail rooms, additional cover, sky, ceilings, lamps and hints for visibility. The mapper specified a uniform scale of 1.16 for this release. RocketMinsta uses its own match modes. [Source package and readme](https://dl.xonotic.fps.gratis/q3dust2-jb-beta6.pk3)

Dave Johnston's account of designing Dust II is the primary source for the earlier Counter-Strike level. A separate GoldSrc research repository preserves a genuine `de_dust2.bsp` of 2,057,288 bytes, SHA-256 `15945389528d113562ede0a2c80647ebfa799079ed1c05a25379bcf84e4e9286`. Its maintainer documents identical bytes in multiple Counter-Strike releases, so the checksum alone cannot distinguish one specific early release. The file can serve as a GoldSrc reader fixture. [Designer’s account](https://www.johnsto.co.uk/design/making-dust2/) · [GoldSrc provenance and comparison](https://github.com/gokayfem/dust2-shader/blob/44ac89aea2009e4e37838df65649643fb2417b77/SOURCES.md) · [Pinned BSP](https://github.com/gokayfem/dust2-shader/blob/44ac89aea2009e4e37838df65649643fb2417b77/assets/de_dust2.bsp)

## Compile from the editable file

Use Python 3.11 or newer and Pillow. The Linux run used NetRadiant-custom release 20260114, Q3Map2 `2.5.17n-git-68ecbed`, on two CPU threads. Its public compiler archive has SHA-256 `f48f6f1d0db2b910ef9cb5dc5d8a722852510f3c5c278dc17615c0466b8a7a3d`. Extract the release's 7z archive, run the AppImage with `--appimage-extract`, and use `squashfs-root/usr/bin/q3map2.x86_64`. The Debian Nexuiz packages furnish the original external models, shaders and textures. Extract `usr/share/games/nexuiz/data/data.pk3` and `textures.pk3` with `dpkg-deb -x`. Keep inputs and products in a working directory outside the source tree. [Compiler release](https://github.com/Garux/netradiant-custom/releases/tag/20260114) · [Compiler source](https://github.com/Garux/netradiant-custom/tree/68ecbed64b7be78741878c730279b5471d978c7c) · [Nexuiz data](https://deb.debian.org/debian/pool/main/n/nexuiz-data/nexuiz-data_2.5.2-14_all.deb) · [Nexuiz textures](https://deb.debian.org/debian/pool/main/n/nexuiz-data/nexuiz-textures_2.5.2-14_all.deb)

| Input verified before compiling | SHA-256 |
| --- | --- |
| Hanzo's 19,840,851-byte PK3 | `92d52f60a0c33b0bddc9fb0b534f0dd43d346f0691ef1d947b3034149245ca03` |
| Editable `.map` | `a9fc31088a22ecd44bf6e40ceaef98143e30016fdbe90c735b5b9a06248f9787` |
| Nexuiz `data.pk3` | `8b9b0bd7c6cedd0334ecb8a267d870e74de76949468594c5394821983358b6cc` |
| Nexuiz `textures.pk3` | `38ad44a78a9072e575c44174ac82906621631a7531988a0274dc2329505641a5` |
| Author's shipped BSP, used only for comparison | `f872a2fbb8847cd4075adfde2df5116683175d2e0ebec46ba2c362d5c8460545` |

Run from the repository root, replacing the example paths with the actual downloads. Use a fresh output directory.

```sh
python games/yuga-native/tools/source-map-lab/radiant/build.py \
  --author-pack /path/to/q3dust2-jb-beta6.pk3 \
  --q3map2 /path/to/squashfs-root/usr/bin/q3map2.x86_64 \
  --base-data /path/to/data.pk3 \
  --base-textures /path/to/textures.pk3 \
  --output /path/to/dust-rebuild --threads 2
```

The driver stages the source map, original materials and host-game packages. The stage directory starts without a BSP, lightmaps or minimap. It invokes the five operations in the mapper's published order.

| Pass | Mapper settings | What this run produced |
| --- | --- | --- |
| BSP | `-meta -skyfix -samplesize 8 -minsamplesize 4 -mv 1000000 -mi 6000000` | Brush geometry, patches, collision and portal file. The intermediate BSP was 2,545,564 bytes. |
| Visibility | `-vis` | 1,288 clusters and 237,397 visible cluster pairs. The intermediate BSP grew to 2,761,960 bytes. |
| Lighting | `-light -deluxe -patchshadows -samples 3 -lightmapsize 512 -bounce 8 -fastbounce -bouncegrid` | 1,204,144 luxels, eight external light/direction images and a 209-second run. The solver exhausted diffuse light during bounce eight. |
| Minimap | `-minimap` | A fresh 512 × 512 minimap. |
| Scale | `-scale 1.16` | Scaled map, models, entity origins and world bounds. Both playable packages expose it under the authored map name. |

The BSP pass reported 148 invalid normal-index diagnostics while reading the two historical ASE barrel assets and one duplicate/flipped triangle. The light pass reported six zero-valued projection axes. The staged barrel models encode 14 cap triangles per barrel and 32 or 64 side triangles. The rebuilt level contains all 350 designated cap triangles and all 960 side triangles across the 25 models. The audit captures each diagnostic and the full logs remain in the working directory. The original release and modern compiler batch their geometry differently. [Nexuiz data archive](https://deb.debian.org/debian/pool/main/n/nexuiz-data/) · [Pinned compiler](https://github.com/Garux/netradiant-custom/tree/68ecbed64b7be78741878c730279b5471d978c7c)

## What changed on the ground

The finishing pass selects the mapper's two floor-brick materials, both jail-floor materials, concrete ground, grass ground and the steel floor grate. It requires every vertex on a selected draw surface to have an up-normal of at least 0.65. This keeps the original material on vertical risers sharing a floor texture. Crates, wall caps, masonry trim, water, doors and sky retain their materials. The shader variants remap the original diffuse luminance into jade, preserving the source alpha, UV layout, lightmap and shader stages. The grate retains its cutouts. The base bake also lights the jade version, which makes the comparison repeatable. [Material and BSP implementation](../../../tools/source-map-lab/radiant/finish.py)

| Rebuilt geometry | Result |
| --- | ---: |
| Draw surfaces | 3,929 |
| Draw vertices | 30,907 |
| Explicitly indexed triangles | 4,815 |
| Native curved patch surfaces, tessellated separately by the engine | 507 |
| World plus inline models | 16 |
| Collision brushes | 2,697 |
| Recolored surfaces | 175 |
| Ground selections | 47 brick 1, 37 brick 2, 22 jail, 2 jail 2, 28 concrete, 38 grass, 1 grate |

The local `geometry-audit.json` records every changed surface index, SHA-256 for the 15 unchanged BSP lumps, the eight lightmap hashes and minimap hash. The test verifies that only the shader index field changed within each selected draw-surface record and that all original shader records survive. Entity data, visibility, collision, vertices, indices, UVs and light grids compare byte-for-byte. The two new PK3s include the original editable source and assets plus newly compiled products. The `shaders/` directory holds both material scripts for inspection. [Packaging and checks](../../../tools/source-map-lab/radiant/build.py)

| Local product | SHA-256 in the measured run |
| --- | --- |
| Rebuilt baseline BSP | `a1e0754f51eb5e17e35fa78eb2e94434ec5054204e62b2ff72576e6668545d23` |
| Rebuilt jade BSP | `16598f56f76badc7ac5d13a676d5629f22354f2318fdc8bd593bcffba720cb79` |
| `q3dust2-jb-beta6-original.pk3`, 19,860,152 bytes | `262240f4a998794328168807e67ed06d024844cacfe988c763f8a1c8bdcc5994` |
| `q3dust2-jb-beta6-jade.pk3`, 21,285,310 bytes | `3914fe9e826709e41c5d65cb0ebc79517970b6b768c845fcc0c94c04b70bb12d` |

A second clean build used an isolated compiler profile. Its 30,907 vertex positions, base UV pairs and normals matched as a multiset. The same 175 draw-surface indices were selected and the collision/visibility data matched. Threaded compiler ordering and sampled lighting varied. All eight external lighting image hashes changed between independent builds. The table identifies the first measured build, and the material comparison always uses the same bake for both variants.

Install either rebuilt PK3 in the `data/` directory of a Nexuiz 2.5.2 installation. Keep one version of the map active at a time, since both packages expose `maps/q3dust2-jb-beta6.bsp`. Open the game console and enter `map q3dust2-jb-beta6`. Movement, engine collision and visibility operate on the newly compiled BSP. RocketMinsta-specific modes need their matching game code. Stock sound effects ship as Ogg files in the base Nexuiz data archive. [Nexuiz packages](https://deb.debian.org/debian/pool/main/n/nexuiz-data/) · [Original game mode notes](https://github.com/nexAkari/RocketMinsta/wiki/Making-maps-for-Jailbreak)

## Play the staged local map

The workspace copy at `/workspace/ANDOLAN-local/dust2-map-lab/radiant` contains a working Linux x86-64 client, the compiler, the original editable map, two compiled editions and the source material needed to repeat the build. From that directory, use `./play.sh jade` or `./play.sh original`. The launcher joins a local round automatically. Use WASD to move, the mouse to turn and Space to jump. On a headless machine `./play.sh jade --check` starts a private X display, joins as a player, saves the screenshot to `checks/jade-in-game.jpg` and exits. Both editions use relative links to a single shared stock data directory. [Launcher](../../../tools/source-map-lab/radiant/play.sh)

## Seeing the change in the game client

We loaded both packages in the graphical Nexuiz 2.5.2 client using the Debian DarkPlaces executable and Mesa llvmpipe. A local spectator visited the west courtyard, the high crossing and a player-height view facing the arches. The six 1024 × 576 captures use the same positions and angles in their respective map builds. The paired frames show the original masonry pattern and sun shadows under the jade albedo. Pickups animate independently between the sessions. The virtual display was Xvfb at 1280 × 720 with 24-bit color. [DarkPlaces package](https://deb.debian.org/debian/pool/main/d/darkplaces/) · [Capture script and camera coordinates](../../../tools/source-map-lab/radiant/capture.py)

Use the same completed build directory from the compile instructions. The script accepts a normally installed DarkPlaces client or the extracted executable with its runtime libraries available.

```sh
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" \
  python games/yuga-native/tools/source-map-lab/radiant/capture.py \
  --engine /usr/games/darkplaces --build /path/to/dust-rebuild \
  --output /path/to/dust-engine-captures
```

After the six spectator captures, the jade client joins as a player, walks downhill, jumps and lands. The capture receipt records position, velocity, health and the on-ground flag at each step. In a measured run the player advanced 297.59 Quake units, rose 49.31 units above the pre-jump sample, and landed at health 100.

The output includes six full-size images, `nexuiz-courtyards.jpg`, per-client logs and a SHA-256 receipt. Each profile mounts exactly one variant and the two stock host-game PK3s. The capture runs silently. The headless smoke launcher also tested the sound-enabled engine with a virtual 48 kHz stereo device. The local game opens a normal audio device on the desktop.

## Other map sources examined

| Candidate | What we inspected | Reuse decision |
| --- | --- | --- |
| `dust2_nex_vehicles` | A second full editable map (1,903,781 bytes), plus its 4,740,608-byte compiled BSP. The credits name Hanzo, Mario, Morphed and Jeff. The variant adds vehicles and changes doors. Pack SHA-256 `81ab0900383053cc673fa4b9093f5b71f8dffe74da47b84c08c7f602f31b9720`. | Useful for measuring how widened passages and vehicle placement affect a known base. The catalog also carries BSP-only Quake III and Urban Terror ports. [Vehicle release](https://dl.xonotic.fps.gratis/dust2_nex_vehicles.pk3) · [Map catalog](https://xonotic.fps.gratis/ui/maps-index.json) |
| Dust II Long / browser demo | The Long remake includes a real CS:GO VMF. Its README identifies the tactical fragment it represents. The browser project's toolchain models an A-site scene. | Both illustrate reusable workflows. Neither of these examples establishes complete two-site geometry. [Long source](https://github.com/rolivencia/de_dust2_largo/tree/c4fa3b17693f1e4974b1397aa67ad4a8a5f6b9ec) · [Browser authoring project](https://github.com/StarKnightt/counter-strike-in-browser/tree/190a277555ff6a1b7112090fc0a2db3189006db8) |
| Sunaba `dust2.map` | Editable 114,802-byte TrenchBroom file containing 204 brushes, 1,178 brush planes, 23 player spawn entities and 25 lights. Its entity classes do not establish A/B objectives. Root code and asset license files contain different terms. | Useful for a small brush-parser fixture once material provenance is established. The archive carries insufficient evidence for claiming a full CS:GO reconstruction. [Map](https://github.com/discover3d/SunabaGame__sunaba/blob/9979385d7b177a584412d8e1a3689bce0ceda33c/maps/dust2.map) · [Asset terms](https://github.com/discover3d/SunabaGame__sunaba/blob/9979385d7b177a584412d8e1a3689bce0ceda33c/assets/LICENSE.md) |
| Dust2 Web | A browser renderer/simulation that distinguishes its own code, Awpy-derived map artifacts and Valve content in its notices. | Consult the project for packaging and navigation visualization. Follow its file-specific notices when choosing inputs. [Third-party notices](https://github.com/ETO-ze/dust2-web/blob/f4a2634a339f7cb89a300e59e837d8869572709e/THIRD-PARTY-NOTICES.md) |

## Maps with explicit adaptation terms

**Parpax** is the strongest candidate here for an actual Yuga geometry adaptation. Maximilian “Viech” Stahlberg explicitly lists `maps/*` under CC BY-SA 4.0 or later. Its 10,290,061-byte Radiant source includes 316 entities in 28 classes, 3,366 curved patch definitions, 52 named locations and 11 doors. A Yuga experiment could re-theme a single room, preserve human-scale clearances, then measure travel times across its interlocking entrances. Credit the author, identify changes and retain the applicable share-alike terms for adapted material. The project's file-by-file ledger has separate texture and sound attributions. Source SHA-256 `1d72436a6e3f5c7f2b144b584b2f99a4d8cfaa47f9f6644c488873d1572afa8f`. [Editable source](https://github.com/UnvanquishedAssets/map-parpax_src.dpkdir/blob/bcfecd7aab39abde0a90973785e66b3c2974e6a3/maps/parpax.map) · [Author, tools and material-specific licenses](https://github.com/UnvanquishedAssets/map-parpax_src.dpkdir/blob/bcfecd7aab39abde0a90973785e66b3c2974e6a3/about/map-parpax.txt)

**Atelier** supplies a second full example for conversion and rendering tests. Its 1,941,585-byte Xonotic source contains 874 entities across 35 classes, 1,525 curved patches, 13 deathmatch spawn points and four domination points. The mapper identifies the level as an original design, names NetRadiant and Q3Map2, and lists two textures by Evillair. The map-specific license names Paweł “ShadoW” Chrapka and gives GPL-3.0-or-later terms. Its layered routes and curved silhouettes are useful fixtures for a Radiant-to-engine importer. Source SHA-256 `1e64ca539b1753f06e60eb510287ef9679b8c7bd4ec3d759a3b23efaf4c6d583`. [Editable source](https://github.com/xonotic/xonotic-maps.pk3dir/blob/cc92d86adae0d8a795a3bf5634093593a86bdb53/maps/atelier.map) · [Map license](https://github.com/xonotic/xonotic-maps.pk3dir/blob/cc92d86adae0d8a795a3bf5634093593a86bdb53/maps/atelier.license.txt) · [Author notes and asset credits](https://github.com/xonotic/xonotic-maps.pk3dir/blob/cc92d86adae0d8a795a3bf5634093593a86bdb53/maps/atelier-info.txt)

Hanzo's readme credits edited JSProductions textures and photography from CGTextures. It supplies editable geometry and compile instructions, but does not grant an explicit license for redistributing the entire artwork and map as Yuga content. The reproducible code, measured findings and upstream links can travel with Yuga while the packages remain a local study. For new commercial game geometry, the two original maps above provide named sources and explicit adaptation terms. [Hanzo’s credits](https://dl.xonotic.fps.gratis/q3dust2-jb-beta6.pk3)
