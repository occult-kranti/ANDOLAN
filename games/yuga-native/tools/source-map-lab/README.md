# Build and inspect the Dust II ground study

`rebuild.py` creates two CS:GO Source 1 map mounts and two complete, textured GLBs using Valve’s registered BSP/NAV pair. The `radiant` tool compiles a separately authored Nexuiz Dust II from editable geometry. They target different engine formats. [Edition selection and source research](../../docs/research/dust2-map-lab/README.md) · [Local results and independent verification](qa/verification.json)

## Rebuild the native BSP and full GLBs

These commands assume Linux, Python 3.12, Go 1.20 or newer, Rust 1.88 or newer, `curl`, `unzip` and SteamRE DepotDownloader 3.4.0. The `go` on `PATH` must be the Go compiler. `--go /path/to/go` selects it explicitly. Keep the working directory outside this repository. SourceIO is pinned to the release archive and its SHA-256. The upstream source guide lists the archive checksum for DepotDownloader and the Steam depot manifest. [Exact Valve inputs and acquisition instructions](../../docs/research/dust2-map-lab/sources-dust.md) · [DepotDownloader release](https://github.com/SteamRE/DepotDownloader/releases/tag/DepotDownloader_3.4.0) · [Pinned SourceIO release](https://github.com/REDxEYE/SourceIO/releases/tag/5.4.8)

```sh
# Start at the ANDOLAN repository root. Set the two paths for this machine.
work="$HOME/yuga-map-build"
downloader="/path/to/DepotDownloader"
tools="$PWD/games/yuga-native/tools/source-map-lab"
research="$PWD/games/yuga-native/docs/research/dust2-map-lab"
release="$work/dust2-map-lab"
mkdir -p "$work/tools"
python3.12 -m venv "$work/venv"
py="$work/venv/bin/python"
"$py" -m pip install -r "$tools/importer/requirements.txt"
curl -fL https://github.com/REDxEYE/SourceIO/releases/download/5.4.8/SourceIO.zip -o "$work/tools/SourceIO.zip"
(cd "$work/tools" && echo '52cb92856771fc2785b7c4746e15968135973d11fe80bb78dac8001166bcdfac  SourceIO.zip' | sha256sum -c - && unzip -q -o SourceIO.zip)
"$py" "$research/acquire_valve.py" "$work" --downloader "$downloader"
maps="$work/valve-depot/csgo/maps"
"$py" "$tools/rebuild.py" --bsp "$maps/de_dust2.bsp" --nav "$maps/de_dust2.nav" \
  --assets "$work/assets" --sourceio-parent "$work/tools" --work "$work/build" \
  --output "$release" --verify
```

The checked driver first verifies the full SHA-256 of both source files. It calls the pinned NAV exporter, reconstructs brush and model geometry, bakes the private albedos, then invokes the locked Rust editor three times for the native map, NAV size field and GLB. It saves a copy of the untouched native pair alongside the edit. `--verify` additionally checks individual source faces, studio placements, shader bindings, mip texels, navigation, and original collision support for invisible surfaces. A second run into a fresh directory reproduced both GLBs, the native BSP and NAV, and the complete face selection byte for byte. [Importer](importer/README.md) · [Rust finisher](rust/src/main.rs) · [NAV exporter](nav/README.md) · [Independent implementation of the checks](qa/README.md)

The native edited BSP is 444,484,740 bytes. The original is 325,735,952 bytes. The finished offline data include around 314 MB of separately mounted shared materials/models for research. Steam’s numbered archives can require substantially more temporary transfer/storage than the extracted resources. `--assets` accepts the extracted content root whose children are `materials` and `models`. It can also point at this completed workspace’s `content/csgo/` on a subsequent local build. [Dependency resolution and checksums](../../docs/research/dust2-map-lab/sources-dust.md)

## Make the editable Blender scene and viewer

The following reads the outputs above and the registered radar file. Blender 4.3.2 on CPU made the release views. This step generates the comparison, labeled mattes and camera transforms. Place the project under a local HTTP server to use the browser’s module loader and fetch the GLB.

```sh
render="$release/renders"
mkdir -p "$render" "$release/blender"
blender -b --factory-startup -t 2 --python-exit-code 1 --python "$tools/blender/scene.py" -- \
  --baseline "$release/models/dust2-baseline.glb" --variant "$release/models/dust2-jade.glb" \
  --nav "$release/evidence/official-nav.csv" --objectives "$release/evidence/objectives.json" \
  --entities "$release/evidence/source-entities.json" \
  --overview "$work/valve-depot/csgo/resource/overviews/de_dust2.txt" \
  --output "$render" --resolution 1024 --samples 32
mv "$render/dust2-ground-study.blend" "$release/blender/"
blender -b "$release/blender/dust2-ground-study.blend" --python-exit-code 1 \
  --python "$tools/blender/check_scene.py" -- --output "$release/evidence/reopened.json"
"$py" "$tools/blender/compare.py" "$render"
"$py" "$tools/qa/images.py" "$render" --output "$release/evidence/render-diff.json"
"$py" "$tools/viewer/install.py" "$release" "$render"
python3 -m http.server 8874 --bind 127.0.0.1 --directory "$release"
```

Open `http://127.0.0.1:8874/`. The installer vendors the needed files from checksum-pinned Three.js 0.180.0 plus its MIT license. `--three-tgz` accepts a cached npm release file. Orbit, pan, zoom and finish switching operate entirely on the local mesh. The overview uses the registered north-up orthographic projection, and the two site cameras use the matched 24 mm Blender lens. A separate renderer can interpret shadows and shading differently. [Blender scene controls](blender/README.md) · [Three.js release](https://github.com/mrdoob/three.js/releases/tag/r180)

The offline viewer offers a native BSP, two GLBs and the Blender scene. For its optional Hammer source link, use the BSPSource release to generate the VMF. Run these commands with the unpacked release directory set in `bspsrc_dir`. The ZIP release supplies the launcher and Java runtime on the tested platform. [BSPSource 1.4.8](https://github.com/ata4/bspsrc/releases/tag/v1.4.8)

```sh
mkdir -p "$release/source"
"$bspsrc_dir/bspsrc.sh" -o "$release/source/de_dust2_reconstructed.vmf" "$maps/de_dust2.bsp"
```

## Load or play locally

**Valve edition.** Use **one** matching mount under `native/original/csgo/maps/` or `native/jade/csgo/maps/` in a separate local legacy CS:GO installation. The level relies on the stock game’s shared files. Preserve the internal basename `de_dust2` when replacing the files in a test copy or staging a search path. Run `+sv_lan 1 +map de_dust2` on the local dedicated server. The source guide documents the separate native verification, alternate server-smoke basename, runtime and warnings. [Source and smoke evidence](../../docs/research/dust2-map-lab/sources-dust.md)

**Nexuiz edition.** In the completed local package run `./radiant/play.sh jade` or `./radiant/play.sh original` on a Linux desktop. To rebuild from the original 2013 editable `.map`, use `radiant/build.py` with the mapper package, Nexuiz base data and textures and NetRadiant-Custom’s `q3map2`. The checked recipe lists the exact versions, asset hashes, five compilation passes, playable packages, engine commands and observed movement. [Detailed Nexuiz rebuild](../../docs/research/dust2-map-lab/remakes-and-alternatives.md) · [Radiant scripts](radiant/)

## Inspect individual checks

```sh
cargo test --locked --manifest-path "$tools/rust/Cargo.toml"
"$py" -m unittest discover -s "$tools/importer" -v
"$py" -m unittest discover -s "$tools/qa" -v
```

To exercise the full WebGL pathway in headless Chromium, install `playwright` and Pillow in a test environment and run `python "$tools/viewer/check_browser.py" http://127.0.0.1:8874/ --chromium /path/to/chromium`. It checks all six stills, the actual ground material count from the GLB, live finish switching, an orthographic camera reset and a narrow viewport. For the independently compiled CoD collision fixture and GPL map exports, follow the source-pinned research chapter. [Rust map and CoD experiments](../../docs/research/dust2-map-lab/rust-and-cod.md)
