"""Render the actual before/after tail at peak recoil with one locked Blender camera.

blender -b -t 1 -P compare_tail.py -- before.glb after.glb output.webp
"""

import argparse
import math
import sys
import tempfile
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

ART = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ART / "four-hero-motion/tools"))
from blender_stills import load_model, select_pose, shadow_lights, studio

W, H = 600, 480
PHASE = 0.83125


def render(source, target):
    rig, _ = load_model(source)
    scene = bpy.context.scene
    scene.render.fps = 30
    select_pose(rig, "mountain_pulse", PHASE)
    cam, lights = studio(0.0)
    scene.render.threads = 1
    scene.cycles.samples = 24
    scene.render.resolution_x, scene.render.resolution_y = W, H
    azimuth = math.radians(161)
    back = Vector((math.sin(azimuth), -math.cos(azimuth), 0.06)).normalized()
    center = Vector((0.21, 0.45, 1.16))
    cam.rotation_euler = (-back).to_track_quat("-Z", "Y").to_euler()
    cam.location = center + back * 6
    cam.data.ortho_scale = 1.15
    right = cam.rotation_euler.to_quaternion() @ Vector((1, 0, 0))
    shadow_lights(lights, back, right)
    scene.render.filepath = str(target)
    bpy.ops.render.render(write_still=True)
    graph = bpy.context.evaluated_depsgraph_get()
    tip = scene.objects["tail_tip"].evaluated_get(graph).matrix_world.translation
    projected = world_to_camera_view(scene, cam, tip)
    return (round(projected.x * W), round((1 - projected.y) * H))


def font(size, bold=False):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    ink = (239, 234, 219)
    old, new = (127, 216, 223), (249, 192, 98)
    canvas = Image.new("RGB", (W * 2 + 3, H + 118), (22, 26, 28))
    with tempfile.TemporaryDirectory() as tmp:
        points = []
        for i, path in enumerate((args.before, args.after)):
            png = Path(tmp) / f"{i}.png"
            points.append(render(path, png))
            with Image.open(png) as image:
                canvas.paste(image, (i * (W + 3), 64))
    draw = ImageDraw.Draw(canvas)
    draw.text((21, 12), "MOUNTAIN PULSE", fill=ink, font=font(31, True))
    draw.text(
        (W * 2 - 19, 25),
        "Rear three-quarter  /  83.1% of motion",
        fill=ink,
        font=font(19),
        anchor="rm",
    )
    for i, (x, y) in enumerate(points):
        x += i * (W + 3)
        y += 64
        color = (old, new)[i]
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), outline=color, width=2)
        draw.text(
            (i * (W + 3) + 21, H + 78),
            ("Native recovery", "Finished recoil")[i],
            fill=color,
            font=font(22, True),
        )
    # Register the other socket on the same final camera. The coloured ring
    # indicates its true position; the pale ticks show the old registration.
    x0, y0 = points[0]
    x1, y1 = points[1]
    x0 += W + 3
    x1 += W + 3
    y0 += 64
    y1 += 64
    draw.line((x0 - 5, y0, x0 + 5, y0), fill=old, width=2)
    draw.line((x0, y0 - 5, x0, y0 + 5), fill=old, width=2)
    draw.line((x0, y0, x1, y1), fill=ink, width=1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, "WEBP", quality=93, method=6)
    print("Projected tail marker before and after", points, flush=True)


if __name__ == "__main__":
    main()
