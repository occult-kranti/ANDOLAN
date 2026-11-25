"""Render exact event stills from the editable Hanuman ability sequence."""
import argparse
import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--output", type=Path, default=HERE / "stills")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str((HERE / "hanuman-layered-abilities.blend").resolve()), load_ui=False)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 1
    scene.render.resolution_x = args.width
    scene.render.resolution_y = round(args.width * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    timeline = json.loads((HERE / "timeline.json").read_text())
    for shot in timeline["shots"]:
        scene.frame_set(min(shot["frames"]["impact"] + 2, shot["frames"]["end"]))
        scene.render.filepath = str((args.output / (shot["id"] + ".png")).resolve())
        bpy.ops.render.render(write_still=True)
        print("Rendered", shot["id"], "frame", scene.frame_current, flush=True)


if __name__ == "__main__":
    main()
