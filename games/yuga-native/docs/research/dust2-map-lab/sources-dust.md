# Finding the full CS:GO Dust II and rebuilding its dependency set

The local input is Valve's **Dust II for Counter-Strike: Global Offensive, Source 1 BSP v21, Hammer map revision 10535**. Steam's dedicated-server depot still serves this particular build anonymously. We retrieved the BSP, the navigation mesh, two original radar images, their registration and the mounted game assets that the BSP references. An independent public copy of the BSP had the same size, Steam SHA-1 and separately computed SHA-256. The public Steam Workshop item saying “Official map by Valve” proved to contain a small empty-room BSP. Opening both files and counting their faces changed which build we selected. [Valve's Dust II release study](https://www.counter-strike.net/dust2) · [Steam Workshop record](https://steamcommunity.com/sharedfiles/filedetails/?id=125438255) · [Measured source fingerprints](source-evidence.json)

## Where the complete map actually comes from

| Identifier | Value and use |
|---|---|
| Client and branch | Steam app 730, branch `csgo_legacy`. The shared game content belongs to depot 731. |
| Downloaded server source | Steam app 740, public branch, depot 731, manifest **1224088799001669801**. Steam reported the manifest date as 12 October 2023. The server build record is 12426148. No personal account was used. |
| Primary BSP | `csgo/maps/de_dust2.bsp`, **325,735,952 bytes**. The Steam manifest SHA-1 is `d905c6f7dd694a0dace9380a8558ca8a177cbd91`. The independently computed SHA-256 is `b91be410539fbbfc16300423f1e19c024f12addf1429c8cb2f72b53fe0fd6bcc`. |
| Navigation | `csgo/maps/de_dust2.nav`, **579,121 bytes**, Steam SHA-1 `4f53ff186ee3532b681943724d81a6e27f835cc3`. This is a separate file. The BSP alone cannot prove walkable route coverage. |
| Radar | `csgo/resource/overviews/de_dust2.txt` and the corresponding `de_dust2_radar.dds` and `de_dust2_higher_radar.dds`. The mapping text records the 1024-view origin at X −2476, Y 3239 and scale 4.4. The placements and upper radar have separate provenance. |
| Shared content index | `csgo/pak01_dir.vpk`, 15,920,251 bytes, Steam SHA-1 `fe38c13f82ae49ec1a7a613465271b13a9a1636c`. Its 133,676 entries map material and model paths to a numbered archive, offset, preload length, body length and CRC. |
| Retrieval code | SteamRE DepotDownloader release **3.4.0** fetched the registered content through Steam. The Linux x64 release ZIP we used hashes to `a999dec66b4850fc961bd50366696d23c2d0fad7b18790e6a5647b2f19097a53` (SHA-256). The Python helper performs the subsequent map-specific work. |

The public Steam app-information mirror independently reports the same depot and manifest for the dedicated server and legacy client. The binary comparison above uses Valve's actual content manifest and downloadable files. The full depot is 32,722,411,363 bytes uncompressed. Reading its index first avoids installing an entire game to identify a door or resolve a material. [Dedicated-server app info](https://api.steamcmd.net/v1/info/740) · [Client app info](https://api.steamcmd.net/v1/info/730) · [Pinned transfer tool and usage](https://github.com/SteamRE/DepotDownloader/releases/tag/DepotDownloader_3.4.0) · [Verification record](source-evidence.json)

## Which alternative sources survived inspection?

| Source examined | What is actually there | Decision for this build |
|---|---|---|
| Valve's old Workshop item 125438255 | Steam's published-file API returned a 1,444,042-byte ZIP. Its embedded `de_dust2.bsp` is 3,104,932 bytes, revision 1, with **44 faces, two brush models, six entities and zero site triggers**. Its packed resources explicitly refer to `workshop_empty_room`. | Useful as a negative control. A matching level name, preview image and publisher are insufficient to identify the playable geometry. [Workshop entry](https://steamcommunity.com/sharedfiles/filedetails/?id=125438255) · [Steam's downloadable package](https://cdn.steamusercontent.com/ugc/884099481704512720/AAC9108709EDFB9244B1476609425DCE05B00989/) |
| ReagentX's 2018 decompiled CS:GO map archive | The pinned tree contains `de_mirage_d.vmf`, `de_nuke_d.vmf`, `de_inferno_d.vmf`, `de_overpass_d.vmf` and other useful format references. Its Dust entries include `am_dust2_d.vmf` and `de_shortdust_d.vmf`. A full `de_dust2_d.vmf` was absent from this revision. | A useful Hammer document comparison for other levels. Full-build attribution requires checking individual files. [Pinned tree](https://github.com/ReagentX/decompiled-csgo-maps/tree/6083016d512291a45cf4080db839d56f6e1bfc2d) |
| Rolivencia's `de_dust2_largo` | A mapper-published, intentionally restricted side-passage spin-off. We retrieved the CS:GO editable VMF (829,085 bytes) and packaged BSP (3,180,440 bytes). The repository also contains GoldSrc RMF/WAD sources and a changelog describing the port. | An inspectable **source-to-distribution** example. Its route, scale of data and content are a different level. The repository page did not expose a general asset-reuse license. [Source and design description](https://github.com/rolivencia/de_dust2_largo/tree/c4fa3b17693f1e4974b1397aa67ad4a8a5f6b9ec) · [Editable CS:GO map](https://github.com/rolivencia/de_dust2_largo/blob/c4fa3b17693f1e4974b1397aa67ad4a8a5f6b9ec/csgo/src/de_dust2_largo.vmf) |
| `Ktulue/cs-flythrough` | MIT Rust/wgpu viewer with camera routes and instructions for supplying Counter-Strike **GoldSrc** BSPs. The tree contains a Dust II camera-route example. | A practical reference for camera travel and clean viewer separation. The format and rendering code target an earlier game generation. [Pinned source and license](https://github.com/Ktulue/cs-flythrough/tree/9a2e01ce259cb7b74db04f94fac3263c870046c9) |
| `sy-1225/dust2-3d-atlas` | A community **CS2** web atlas with streamed binary scene chunks, lightmap, HDR and browser/mesh-decoder notices. | A useful comparison for progressive loading. The assets and engine generation differ from this Source 1 lab. Repository inspection found component licenses for bundled tools and no blanket license for Valve's map art. [Pinned tree](https://github.com/sy-1225/dust2-3d-atlas/tree/7b327f83f0db824deb098db888caa943f4e390c9) |
| Lasa's Plumber and `plumber_core` | A Blender add-on and modular Rust crates for VMF, VPK, MDL, VMT, asset loading, and filesystem mounts. The Rust core carries Apache-2.0 with an MIT alternative in its Cargo manifests. The Blender add-on has its own GPL terms. | A genuine Rust/Blender map pipeline worth comparing to YUGA's loader, especially its division between a material description, a mounted asset and an exported object. Inspect the input path when using a compiled BSP. [Blender add-on](https://github.com/lasa01/Plumber/tree/f978c700880f84a48d98a59693c5adca00e28dfb) · [Rust workspace](https://github.com/lasa01/plumber_core/tree/e7ad8d05d3c197ec402debb951461a9fc422f280) |

BSPSource reconstructs editable VMF documents from supported compiled BSPs. The compiler has already clipped and split faces, assigned visibility partitions and baked lighting. A decompile can recover useful editing geometry, but cannot establish the original brush grouping, project history or exact precompile source. Keeping the source BSP fingerprint and its native gameplay lumps allows stronger regression checks for this one-color study. Valve's public SDK headers also document format families used when inspecting lumps, meshes and studio models. The 2013 SDK has its own game scope and license. [BSPSource](https://github.com/ata4/bspsrc/tree/85943055376b9e330263a5e4e88f574d98a7f01c) · [Valve BSP layout](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/bspfile.h) · [Valve studio-model header](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/studio.h)

## What we found inside the selected revision

| Measured layer | Result | Why it matters to reconstruction |
|---|---:|---|
| SDR face records / HDR face records | 9,852 / 9,852 | These are parallel render representations. Count the world faces once when reporting the map. Detail displacement geometry needs independent triangulation. |
| Brush models / map entities | 43 / 375 | Some solids and triggers are entities with `*n` brush references. An image exporter that only reads the first brush submodel loses map structure. |
| Team start entities | 15 per team | The count is measured from entity text. It does not imply that a match must have 30 players. |
| Objective volumes | 2 | Model 26 spans (976, 2336, 96)–(1248, 2624, 192). Model 27 spans (−1728, 2496, 0)–(−1344, 2864, 96). Their east/west positions agree with the overview's A/B markers. Coordinates are unscaled Source XYZ. |
| Static prop placements | 3,158 | The `sprp` game lump uses version 11 and 80-byte placement records. The corresponding 3,158 embedded VHV files carry baked vertex-lighting data. Repeating a model requires per-instance transforms. |
| Unique static model names | 1,257 | The 1,258 dictionary entries contain one duplicate shutter stem. A separate `prop_physics_multiplayer` references the soccer ball, making 1,258 unique render-model stems overall. |
| Packed files | 5,579 | These include 679 each of MDL/VVD/VTX, 302 PHY, 48 VMT, 34 VTF, and the VHV data. A compiled map can be hundreds of megabytes and still depend on mounted VPK content. |
| Resolved render dependencies | 364 VMTs, 535 VTFs, 4,566 model components | Starting from 120 world material names and the model and skybox tables, we followed 1,608 model material slots. The final count includes both soccer-ball skins. |
| Additional verified loose files | 3,114 files, 321,541,499 bytes | 579 each of MDL/VVD/VTX, 490 PHY, 352 VMT and 535 VTF. Native VPK CRCs were checked against the bytes extracted for each external file. |

A small data detail fixed a visible class of failures. Two door models use a material name ending in a **literal space**. The mounted VPK contains `dust_door_46x106_03 .vmt` with that same space. Trimming the model string lost the texture lookup for both models. The resolver now normalizes separators and case while retaining that authored character. It checks each model's directory table as well as qualified material names. [Source acquisition and resolver](acquire_valve.py) · [Machine-readable evidence](source-evidence.json)

## Reproduce the official-only acquisition

Run these commands from the repository root. Use a new local project directory with room for the original map, several numbered VPKs and the expanded resources. The active downloader uses public game content from the fixed server depot. The workload stays small compared with installing the 32.7 GB depot. The script retains the geometry-stage VPKs for repeated material reads and processes additional VPKs in batches of three. It normally needs about 3 GB of free space for this source stage. Blender exports and rendered outputs have separate storage requirements. [Downloader CLI](https://github.com/SteamRE/DepotDownloader/tree/DepotDownloader_3.4.0) · [Acquisition script](acquire_valve.py)

```bash
work="$PWD/../yuga-dust-local"
mkdir -p "$work/tools"
gh release download DepotDownloader_3.4.0 --repo SteamRE/DepotDownloader \
  --pattern DepotDownloader-linux-x64.zip --dir "$work/tools"
python3 -m zipfile -e "$work/tools/DepotDownloader-linux-x64.zip" "$work/tools"
chmod u+x "$work/tools/DepotDownloader"
python3 games/yuga-native/docs/research/dust2-map-lab/acquire_valve.py "$work" \
  --downloader "$work/tools/DepotDownloader"
```

The output has three consumers.

- `$work/valve-depot/csgo/maps/de_dust2.bsp` is the canonical input to the native BSP recolor, mesh importer and map-instance audit. Use its internal packed resources as the highest-priority map mount.
- `$work/assets` is the fallback mount containing the verified external MDL, VVD, VTX, PHY, VMT and VTF resources. A model file alone does not contain the complete vertex and index streams. The directory VPK uses archive index 32767 for embedded data and supports preloaded bytes preceding the archive body.
- `$work/valve-closure.json` lists the exact resource names and versioned inputs. Preserve it with local derived files. After a successful acquisition the same command without `--downloader` checks the mounted inputs and closure offline using only Python's standard library. The separate original NAV and radar files remain in their standard `csgo/maps` and `csgo/resource/overviews` directories.

The closure deliberately describes **render assets referenced by this district**. Audio playback, NPC logic, shader permutation parity, Source's full clustered visibility pipeline and a running game server are separate systems. A complete scene reconstruction and an accurate gameplay simulation each need their own acceptance evidence. [Official file checks](source-evidence.json)

## The native server opens both maps

Valve's **Counter-Strike: Global Offensive Dedicated Server 1.38.8.1** started the original and jade BSPs in separate processes. Each reached `Host_NewGame`, initialized the LAN server and accepted `status` at `127.0.0.1:28719`. A read-only Squirrel query counted **two bomb-zone triggers and 15 spawn entities per team on each live map**. Both servers reported zero humans and zero bots, then exited with code 0 on `quit`. We used `de_dust2_jade` as the second map's basename so the engine identifies the edited file explicitly in its console. The durable native game mount keeps the retail basename `de_dust2` to preserve the stock radar and map-specific configuration when swapping variants. [Machine-readable console receipt](server-smoke.json)

The executable was Valve's unmodified 32-bit Linux `srcds_linux` from app 740, binary depot 740, manifest `6998097922547485721`. The server and both maps used the same 12 October 2023 retail content depot. This cloud kernel returned `ENOEXEC` on native i386 executables. Debian's QEMU user-mode i386 interpreter and a private i386 glibc sysroot ran the retail program. The lab mounted the original map assets, 26 Linux runtime files, stock configuration, bot and navigation databases, and a reduced VPK index pointing to genuine archive data available locally. The server was started with `-ip 127.0.0.1 -port 28719 -insecure -nomaster +sv_lan 1 +tv_enable 0 +bot_quota 0`. [Valve developer documentation for the Source Dedicated Server](https://developer.valvesoftware.com/wiki/Source_Dedicated_Server) · [Dedicated-server binary manifest](https://steamdb.info/depot/740/manifests/) · [Debian QEMU user-mode package](https://packages.debian.org/trixie/qemu-user)

The selective mount omitted 27 generic particle libraries from the stock server's global precache. Both runs logged these missing libraries, including particle sets for other maps. The offline Steam client API reported no running Steam session and the console reported an unregistered server ID. The first exploratory original run also warned about an undefined callout dictionary. Adding the retail `navplace.db`, `botprofile.db` and `botchatter.db` resolved the callout warnings. An interactive GPU client, joined players, packet delivery and a played round remain separate measurements. [Machine-readable console receipt](server-smoke.json)

### Reproduce in a standard installation

1. Install the Source 1 **CS:GO Dedicated Server** into a separate directory with `steamcmd +force_install_dir /absolute/path/to/csgo-server +login anonymous +app_update 740 validate +quit`. For historical comparison, confirm the map and patch hashes above, the executable's depot manifest and the product version in `csgo/steam.inf`. That full server installation supplies shared models, VPKs, scripts, particle libraries and bot databases. [SteamCMD installation and login](https://developer.valvesoftware.com/wiki/SteamCMD) · [App 740 depot list](https://steamdb.info/app/740/depots/)
2. Keep the stock `csgo/maps/de_dust2.bsp` and `.nav` files. Copy the two newly built files into that directory under the alternate names `de_dust2_jade.bsp` and `de_dust2_jade.nav`. The first stays byte-identical to the generated jade BSP. The NAV's stored BSP-size field must match the jade file. The normal-name `native/jade/csgo` overlay is also available for a second, isolated copy of a standard installation.
3. From the server directory run the command below. After startup, enter `status`, then `quit`. Repeat with `+map de_dust2_jade`. The server binds to loopback and requires no game account for this private test. To repeat the live entity count, copy `yuga_map_audit.nut` to `csgo/scripts/vscripts`. At the private server console, enter `sv_cheats 1` and then `script_execute yuga_map_audit` before `quit`. [Entity census script](yuga_map_audit.nut)

```sh
./srcds_run -game csgo -console -norestart -insecure -nomaster \
  -ip 127.0.0.1 -port 28719 +sv_lan 1 +tv_enable 0 +bot_quota 0 \
  +map de_dust2
```

For first-person visual or joined-player verification, install Steam app 730's **`csgo_legacy` branch**, mount the matching local BSP and NAV, and connect that client to `127.0.0.1:28719`. On separate machines a loopback-bound process is reachable only from its own host. Source 2 clients use a different map format. A standard full game installation also supplies first-person and global effects outside this map's static presentation. [Counter-Strike on Steam](https://store.steampowered.com/app/730/) · [CS:GO legacy branch and depots](https://steamdb.info/app/730/depots/?branch=csgo_legacy)

## Other source maps with verified depot entries

These are examples from the **same Valve manifest**. The SHA-1 values below identify the original BSPs independently of similarly named community exports. This run acquired and rebuilt Dust II. The remaining file entries establish availability. Porting the importer to a second map should begin by checking its BSP version, static prop stride, visibility and lighting lumps, mounted dependencies and objective entities.

| Path in depot 731 | File size (bytes) | SHA-1 in Valve's content manifest |
|---|---:|---|
| `csgo/maps/de_mirage.bsp` | 62,825,348 | `5af2e6cc82145e12954397e8cdb00800512eaf4b` |
| `csgo/maps/de_inferno.bsp` | 102,233,048 | `d37f61f64d34fab673be9d3a0b3f9cc24e3aaa2b` |
| `csgo/maps/de_nuke.bsp` | 281,356,840 | `0bd46e12c74b2ec22d6733e3e79725b1d5656861` |
| `csgo/maps/de_overpass.bsp` | 60,880,332 | `3b30f709445dfd5c67759e966977113959fab48c` |
| `csgo/maps/de_train.bsp` | 97,225,268 | `619dcecf4333a1e797296ece1fb0882e75d79fff` |
| `csgo/maps/de_cache.bsp` | 486,323,964 | `c4a370702c00945756be9a29876e79b996447555` |
| `csgo/maps/de_vertigo.bsp` | 66,531,872 | `06345338ab0a110b2e46a80eb7f6b56cc2618ad8` |
| `csgo/maps/de_ancient.bsp` | 406,270,188 | `0a4dac9871e552f0f1daadf660f826e5b784a3a3` |

The public VMF archive has editable examples for several of these maps. Reconcile a VMF's revision and compiler context with the chosen BSP before comparing their geometry. [CS:GO decompiled map archive](https://github.com/ReagentX/decompiled-csgo-maps/tree/6083016d512291a45cf4080db839d56f6e1bfc2d) · [Legacy depot identity](https://api.steamcmd.net/v1/info/740)

## What transfers to YUGA

**Test the geometry behind a level's name.** A production intake should verify the source's content hash, face and entity counts, objective volumes and placement inventory. That simple check caught the official six-entity placeholder. YUGA can apply the same pattern to its eight active courts when a generated model or fixture claims to be a whole district. [Mandala fieldbook](../../design/ember-rite-5v5/atlas/vertical-play/README.md)

**Keep map-specific art, reusable definitions and individual placements distinct.** Dust II uses 1,257 static model names for 3,158 placements. Separate the reusable geometry key from each instance's transform, skin and color. Mandala's lanterns, screens, court steps and stone courses then need one authored asset per variant, with the collision policy and source dimensions carried alongside each placement. [Original asset registration](../../../art/mandala-map-studio/README.md) · [Source model structures](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/gamebspfile.h)

**Test player readability with a controlled change.** Valve's Dust II release comparison describes removing dark doorway distractions behind Site A, improving light in the lower tunnels and changing site props so movement and outlines read more clearly. Original mapper Dave Johnston's account documents the early blockout, iteration and problems of making a sequel. For YUGA's court review, freeze camera, geometry, placements and light, then recolor the same ground mask before evaluating the hero silhouette. Define precisely whether steps, fixed floor panels and cart tops belong to that mask, and audit any exception. [Valve comparison and interactive views](https://www.counter-strike.net/dust2) · [Dave Johnston, *The Making Of: Dust 2*](https://www.johnsto.co.uk/design/making-dust2/)

**Carry source terms with each layer.** Rendering a documented local map study and reusing open tooling involve different material. The Git repository can carry the authored selectors, conversion code, checks, source IDs and research. Valve's SDK license and Steam terms govern the shipped game content and developer tools. For a distributable YUGA city, author new modular geometry and art from its signed court plans and reuse the importer architecture, scale tests and measurement methods under their respective terms. [Steam subscriber agreement, developer tools and game content](https://store.steampowered.com/subscriber_agreement/) · [Valve SDK license](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/LICENSE)
