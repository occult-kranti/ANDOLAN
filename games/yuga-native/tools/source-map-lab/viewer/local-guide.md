# Open the local Dust II study

Start a local web server in this directory and open `http://127.0.0.1:8874/`.

```sh
python3 -m http.server 8874 --bind 127.0.0.1
```

- Switch **Original** and **Jade ground** to compare the same view. Select **Inspect in 3D** to load the full 205 MB model. Drag to orbit and use the wheel to zoom.
- Open `blender/dust2-ground-study.blend` to edit the shared geometry and compare two finishes. The timeline selects overview (1), Site A (2) and Site B (3). The `.glb` files are in `models/`.
- Load `native/jade/csgo/maps/de_dust2.bsp` with its matching `.nav` in a separate legacy CS:GO installation. `native/original/` holds the original. Both native filesets loaded on Valve’s dedicated server. Shared content under `content/csgo/` in this prepared workspace supports the art pipeline.
- The local Nexuiz edition has its own source, engine and map packages under `radiant/`. On a Linux desktop, run `./radiant/play.sh jade` or `./radiant/play.sh original`. `./radiant/play.sh jade --check` runs the actual game client headlessly. The original and jade packages are separately selectable.
- `source/de_dust2_reconstructed.vmf` is an editable Hammer reconstruction. `radiant/q3dust2-jb-beta6.map` is the independently authored source used for the five-pass Nexuiz build.
- An archive of the native jade BSP and matching NAV is in `downloads/dust2-jade-source1.zip`. `downloads/open-geometry.zip` contains two GPL Xonotic sources and Blender-ready geometry; prepared local `.blend` files sit in `open-geometry/`.
- `renders/dust2-ground-comparison.webp` shows the whole district and both sites. `evidence/` contains the numerical checks. The prepared package also includes `dust2-field-guide.pdf`.

The jade finish covers 7,736.74 m² of structural paving. Separate stair and curb models, props, orange site markings and original collision retain their authored appearance and behavior. The screenshots of the Valve edition are Blender renders. The Nexuiz captures are from the graphical game client. [Research, credits and YUGA integration](https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-hanuman-trial/games/yuga-native/docs/research/dust2-map-lab) · [Rebuild tools](https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-hanuman-trial/games/yuga-native/tools/source-map-lab)
