# YUGA rig inspector

Open the studio beside the motion atlas to examine the four skinned models and their embedded animation tracks. The viewer loads the same four GLBs shipped in the package. The clip list comes from each file. Hanuman exposes 11 tracks, Rama 19, Shiva 9 and Krishna 9. Clip times in the inspector come directly from the animation rather than from the storyboard’s planned duration. [Open the viewer](index.html) · [Return to the atlas](../index.html)

## Open the extracted package

Double-click `viewer/index.html`, select a character, and use the file picker to open that character’s file from `models/`. For example, choose `models/krishna.glb` for Krishna. Each new character needs one selection per session. The browser reads the selected file locally, including its embedded textures and animation. Switching back to a previously selected hero reuses the model.

For automatic switching without file selection, run the following command from the extracted motion package directory, then open the local address in a WebGL2-capable browser. The page, game engine, lighting code, typefaces and character files are served by this one local server.

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

```text
http://127.0.0.1:8000/viewer/?hero=rama&clip=volley_release&view=side
```

From the repository root, serve the same directory with `python3 -m http.server 8000 --bind 127.0.0.1 --directory games/yuga-native/art/four-hero-motion`. The `hero` parameter accepts `hanuman`, `rama`, `shiva` and `krishna`. The `clip` parameter takes an embedded track name, such as `tail_sweep`, `circle_draw` or `cast3`. Camera presets are `front`, `side` and `rear`. Pressing the YUGA wordmark returns to the motion atlas.

## Inspect a pose

- Select a character and clip. Drag the timeline to a time in seconds. Scrubbing pauses playback so you can hold an exact pose while orbiting.
- Drag on the character to orbit and use the wheel to zoom. Keyboard users can focus the scene and use the arrow keys, + or −, and Space. The three named views reset the camera distance.
- Choose a speed between quarter speed and double speed. Turn off Loop to hold the final pose after one playthrough. The system’s reduced-motion preference initially pauses the inspector.
- The count beside the hero name comes from the live skin. The viewer shows raw embedded poses. World-space ability effects and match hit detection are separate parts of the game.

## Source and notices

The inspector uses the project’s pinned PlayCanvas 2.23.3, original Sangam environment lighting, Barlow Condensed 5.3.0 and DM Sans 5.3.0 from the repository’s locked dependencies. The two version numbers for fonts identify their Fontsource packages. The classic-script bundle includes the engine and lighting and runs with normal local-file browser permissions. The build refreshes its copy of the shared studio lighting source from the development repository. Copyright and distribution terms for the engine and fonts are included locally. [Viewer source](src/app.js) · [PlayCanvas MIT license](notices/PlayCanvas-MIT.txt) · [Barlow Condensed OFL](notices/Barlow-Condensed-OFL.txt) · [DM Sans OFL](notices/DM-Sans-OFL.txt)

From the development repository, rebuild with the locked dependencies and run the independent browser test. The optional `--root` argument tests an extracted package containing sibling `viewer/` and `models/` directories.

```sh
npm ci
npx playwright install --only-shell chromium
p=games/yuga-native/art/four-hero-motion/viewer
node "$p/build.mjs"
node "$p/tests/browser.mjs" --report /tmp/yuga-rig-check.json
node "$p/tests/local-file.mjs" --report /tmp/yuga-rig-file-check.json
```

The browser test compares selected track names with each actual GLB, exercises the timeline, cameras and playback controls, and samples head, wrist and foot rotations at two instants of each ultimate. A Chromium software-rendering run can establish functional WebGL playback. Hardware-specific framerate and visual quality require a device measurement. [HTTP browser QA](tests/browser.json) · [Local-file browser QA](tests/local-file.json)
