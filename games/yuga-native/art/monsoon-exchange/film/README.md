# Monsoon Exchange camera tour

[Play or download the silent MP4](district-tour.mp4). The film visits four registered views of the finished district. Each chapter moves the camera through the actual 3D geometry. The H.264 video plays independently of the interactive atlas.

| Time | Camera | What to look for |
| --- | --- | --- |
| 00:00–00:04 | Monsoon Exchange | The high overview turns slowly across the market. Identify the low indigo western district and the raised copper court to the east. |
| 00:04–00:08 | Weavers’ Gate | The camera approaches the central sandstone arch. The woven awning and two different wall profiles frame the crossing. |
| 00:08–00:12 | Sun Court | A lateral move reveals the eastern pavilion behind the ritual disk and its standing cover. |
| 00:12–00:16 | Indigo Cistern | The near parapet moves against the opposite arcade. The five stepped terraces lead down to the architectural pool. |

The recording reads the original GLB and its Blender camera register. It uses the atlas’s metre basis, lens and orbit math. The native renderer retains the mesh instances, original PBR materials and UVs, then lights them with one fixed warm sun, ambient fill and a graded sky. A short arc and dolly around each registered target supply parallax. The captions are composited after each frame. The camera tour documents the map’s appearance. The separate measured floorplan and clearance checks document player movement. [Scene and camera register](../scene/scene-register.json) · [Interactive atlas](../viewer/) · [Floorplan](../plan/floorplans.pdf) · [Recording inputs and SHA-256](recording.json)

## Reproduce the film

Use Python 3.11 or 3.12, a working Linux EGL implementation (Mesa llvmpipe works on CPU), FFmpeg with libx264 and ffprobe, and the DejaVu Serif and Sans fonts. The capture used Python 3.12 and the versions below. NumPy 1.x supplies the constants used by PyRender 0.1.45. Installing PyRender last preserves the PyOpenGL 3.1.10 EGL binding exercised by this film. On Linux the script uses a private temporary frame directory under `/dev/shm`. Specify `--frames-dir` to select another filesystem. Allow about 160 MB of temporary space.

Inside a Python virtual environment, install the capture libraries.

```sh
python3 -m pip install numpy==1.26.4 scipy==1.17.0 trimesh==5.2.2 networkx==3.7 Pillow==12.3.0 imageio==2.38.2 pyglet==2.1.19 six==1.17.0 freetype-py==2.5.1 PyOpenGL==3.1.10 PyOpenGL-accelerate==3.1.10
python3 -m pip install --no-deps pyrender==0.1.45
```

From this directory, run the following command to inspect the first, middle and last actual model views in each planned shot.

```sh
python3 record.py --contact-sheet /tmp/monsoon-camera-review.jpg
```

Run the recording command to export 384 camera frames at 1280 × 720, 24 fps. It verifies the source asset against the scene register before capture, checks its identity again before encoding, and probes the resulting H.264 stream. The four-second takes contain 96 distinct poses apiece. Each frame retains the original triangles, with all fixed instances grouped by material for efficient drawing. The renderer compares the beginning and end of each chapter before encodes are accepted. EGL drivers, library and encoder versions can change pixels and compressed bytes on another machine. [Shot timing and capture code](record.py)

```sh
python3 record.py
```
