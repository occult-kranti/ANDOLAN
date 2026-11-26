"""Film the editable Mandala district with Blender Workbench and Cycles. Run with python3."""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from functools import cache
from itertools import pairwise
from pathlib import Path

try:
    import bpy
except ImportError:
    bpy = None

STUDIO = Path(__file__).resolve().parents[1]
MAP = STUDIO.parents[1] / "docs/design/ember-rite-5v5/atlas/maps/mandala.json"
TILE = (736, 416)
CLIP = (640, 360)
HD = (1280, 720)
FPS = 16
PAPER = (232, 222, 196)
INK = (18, 31, 33)
GOLD = (218, 170, 98)
MINT = (167, 203, 187)
TYPE_NAMES = {
    "room": "Room",
    "route": "Passage",
    "cover": "Cover",
    "architecture": "Architecture",
    "artifact": "Artifact",
    "rite": "Rite object",
}


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scene", type=Path, default=STUDIO / "mandala-rift.blend")
    p.add_argument("--catalog", type=Path, default=STUDIO / "catalog.json")
    p.add_argument("--output", type=Path, default=STUDIO)
    p.add_argument("--stage", choices=("all", "plates", "clips", "district", "tour"), default="all")
    p.add_argument("--only", nargs="+", default=[], help="Film selected inventory IDs.")
    p.add_argument("--threads", type=int, default=3)
    p.add_argument("--force", action="store_true", help="Replace already completed assets.")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None)


@cache
def font(size, role="label"):
    from PIL import ImageFont

    names = {
        "title": ("NotoSerif-Regular.ttf", "DejaVuSerif.ttf"),
        "label": ("NotoSans-Regular.ttf", "DejaVuSans.ttf"),
        "mark": ("DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"),
    }
    for name in names[role]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def v3(x, y, z):
    from mathutils import Vector

    return Vector((x, y, z))


def direction(azimuth, altitude):
    az, alt = map(math.radians, (azimuth, altitude))
    return v3(math.cos(az) * math.cos(alt), math.sin(az) * math.cos(alt), math.sin(alt))


def extent(points):
    lo = v3(*(min(v[i] for v in points) for i in range(3)))
    hi = v3(*(max(v[i] for v in points) for i in range(3)))
    return lo, hi


def rectangle(x, y, z, w, d, h=0):
    return [
        v3(x + a * w / 2, y + b * d / 2, z + c * h) for a in (-1, 1) for b in (-1, 1) for c in (0, 1)
    ]


class Passage:
    def __init__(self, edge, nodes):
        self.edge = edge
        self.a, self.b = nodes[edge["from"]], nodes[edge["to"]]
        coords = [self.a["xz"], *edge.get("via", []), self.b["xz"]]
        self.distances = [0.0]
        for a, b in pairwise(coords):
            self.distances.append(self.distances[-1] + math.dist(a, b))
        self.length = self.distances[-1]
        self.points = [
            v3(x, z, self.a["y"] + (self.b["y"] - self.a["y"]) * d / self.length)
            for (x, z), d in zip(coords, self.distances)
        ]
        self.is_fold = edge["kind"] == "fold"
        self.width = edge["width"]

    def position(self, distance):
        d = min(self.length, max(0.0, distance))
        for i, stop in enumerate(self.distances[1:]):
            if d <= stop:
                prev = self.distances[i]
                return self.points[i].lerp(self.points[i + 1], (d - prev) / max(1e-6, stop - prev))
        return self.points[-1].copy()

    def heading(self, d):
        along = self.position(d + 4.0) - self.position(d - 4.0)
        along.z = 0
        along.normalize()
        return along

    def framing(self):
        return [
            p + v3(dx * self.width / 2, dy * self.width / 2, h)
            for p in self.points
            for dx in (-1, 1)
            for dy in (-1, 1)
            for h in (0, 4.0)
        ]


class CameraStudio:
    def __init__(self, plan, elements, scratch):
        from mathutils import Vector

        self.scene = bpy.context.scene
        self.plan = plan
        self.nodes = plan["nodes"]
        self.items = {i["id"]: i for i in elements}
        self.groups = {i: bpy.data.collections.get(i) for i in self.items}
        missing = [i for i, c in self.groups.items() if not c]
        if missing:
            raise ValueError("Missing item collections: " + ", ".join(missing))
        self.floor = bpy.data.collections.get("base-floor")
        self.backdrop = bpy.data.collections.get("district-backdrop")
        if not self.floor:
            raise ValueError("Missing base-floor collection")
        self.edges = {
            f"route-{l['from']}-{l['to']}-{l['kind']}": Passage(l, self.nodes) for l in plan["links"]
        }
        self.tmp = scratch
        self.scene.render.engine = "BLENDER_WORKBENCH"
        self.scene.render.resolution_percentage = 100
        self.scene.render.film_transparent = False
        self.scene.render.image_settings.file_format = "PNG"
        self.scene.render.image_settings.color_mode = "RGB"
        self.scene.render.image_settings.compression = 2
        self.scene.render.use_file_extension = True
        self.scene.view_settings.view_transform = "Standard"
        self.scene.view_settings.exposure = 0.52
        shade = self.scene.display.shading
        shade.light = "STUDIO"
        shade.studio_light = "outdoor.sl"
        shade.color_type = "MATERIAL"
        shade.show_shadows = True
        shade.shadow_intensity = 0.43
        shade.show_cavity = True
        shade.cavity_type = "BOTH"
        shade.curvature_ridge_factor = 0.66
        shade.curvature_valley_factor = 0.97
        shade.cavity_ridge_factor = 0.73
        shade.cavity_valley_factor = 0.97
        shade.show_specular_highlight = True
        shade.background_type = "WORLD"
        self.scene.display.light_direction = (0.48, -0.57, 0.67)
        self.scene.display.render_aa = "FXAA"
        for material in bpy.data.materials:
            if material.use_nodes:
                shader = material.node_tree.nodes.get("Principled BSDF")
                if shader:
                    material.metallic = shader.inputs["Metallic"].default_value
                    material.roughness = shader.inputs["Roughness"].default_value
        self.sunlight_world = self.scene.world
        world = bpy.data.worlds.new("District camera backdrop")
        world.color = (0.040, 0.063, 0.072)
        self.scene.world = world
        self.camera = bpy.data.objects.new(
            "Mandala production camera", bpy.data.cameras.new("District lens")
        )
        self.scene.collection.objects.link(self.camera)
        self.scene.camera = self.camera
        self.camera.data.clip_start = 0.05
        self.camera.data.clip_end = 1400
        self.camera.data.sensor_width = 36.0
        self.stage = bpy.data.objects.new(
            "Render-only contact ground", bpy.data.meshes.new("Studio sweep")
        )
        self.stage.data.from_pydata(
            [(-420, -420, 0), (420, -420, 0), (420, 420, 0), (-420, 420, 0)], [], [(0, 1, 2, 3)]
        )
        base = bpy.data.materials.new("Camera ground • matte deep jade")
        base.diffuse_color = (0.062, 0.096, 0.102, 1.0)
        self.stage.data.materials.append(base)
        self.scene.collection.objects.link(self.stage)
        self.all_bounds = {}
        self.parts = {}
        self.clearances = {}
        bpy.context.view_layer.update()
        for ident, group in self.groups.items():
            self.parts[ident] = [
                (o.get("socket_index", 0), [o.matrix_world @ Vector(c) for c in o.bound_box])
                for o in group.all_objects
                if o.type in {"MESH", "CURVE", "SURFACE", "FONT"}
            ]
            points = [p for _, corners in self.parts[ident] for p in corners]
            if not points:
                raise ValueError(f"Empty renderable item: {ident}")
            self.all_bounds[ident] = points
        self.draw_size = TILE

    def population(self, ident=None):
        item = self.items.get(ident)
        kind = item.get("kind") if item else "district"
        allowed = set()
        in_world = kind in {"district", "route", "room"}
        if kind == "room":
            node = self.nodes[ident.removeprefix("room-")]
            x, y = node["xz"]
            w, d = node["size"]
            for name, points in self.all_bounds.items():
                lo, hi = extent(points)
                if (
                    lo.x <= x + w / 2 + 3
                    and hi.x >= x - w / 2 - 3
                    and lo.y <= y + d / 2 + 3
                    and hi.y >= y - d / 2 - 3
                ):
                    allowed.add(name)
        elif in_world:
            allowed = self.groups.keys()
        else:
            allowed = {ident}
        for name, group in self.groups.items():
            group.hide_render = name not in allowed
        self.floor.hide_render = not in_world
        if self.backdrop:
            self.backdrop.hide_render = not in_world
        self.stage.hide_render = bool(in_world and self.backdrop)
        self.stage.location.z = -1.58 if in_world else extent(self.all_bounds[ident])[0].z - 0.035

    def subject(self, ident, socket=None):
        if socket is not None:
            return [p for index, corners in self.parts[ident] if index == socket for p in corners]
        p = list(self.all_bounds[ident])
        if self.items[ident]["kind"] == "room":
            n = self.nodes[ident.removeprefix("room-")]
            p.extend(rectangle(*n["xz"], n["y"], *n["size"]))
            x, y = n["xz"]
            for other, parts in self.parts.items():
                if self.items[other]["kind"] in {"architecture", "cover", "artifact", "rite"}:
                    for _, corners in parts:
                        lo, hi = extent(corners)
                        center = (lo + hi) * 0.5
                        if (
                            abs(center.x - x) <= n["size"][0] / 2
                            and abs(center.y - y) <= n["size"][1] / 2
                        ):
                            p.extend(corners)
        return p

    def set_size(self, size):
        self.draw_size = size
        self.scene.render.resolution_x, self.scene.render.resolution_y = size

    def ortho(self, points, az, alt, margin=1.19, scale=None):
        eye = direction(az, alt)
        rotation = (-eye).to_track_quat("-Z", "Y")
        inv = rotation.inverted()
        low, high = extent(points)
        origin = (low + high) * 0.5
        xl, xh = extent([inv @ (p - origin) for p in points])
        center = origin + rotation @ v3((xl.x + xh.x) * 0.5, (xl.y + xh.y) * 0.5, 0)
        aspect = self.draw_size[0] / self.draw_size[1]
        fit = max(0.6, xh.x - xl.x, (xh.y - xl.y) * aspect) * margin
        self.camera.data.type = "ORTHO"
        self.camera.data.ortho_scale = scale or fit
        self.camera.location = center + eye * max(12.0, (high - low).length * 2.5)
        self.camera.rotation_euler = rotation.to_euler()
        return fit

    def lens(self, eye, look, mm):
        self.camera.data.type = "PERSP"
        self.camera.data.lens = mm
        self.camera.location = eye
        self.camera.rotation_euler = (look - eye).to_track_quat("-Z", "Y").to_euler()

    def chase(self, passage, d, reverse=False):
        foot = passage.position(d)
        heading = passage.heading(d) * (-1 if reverse else 1)
        side = v3(heading.y, -heading.x, 0)
        return (
            foot - heading * 8.3 + side * 1.65 + v3(0, 0, 8.1),
            passage.position(d + (-4 if reverse else 4)) + v3(0, 0, 0.9),
        )

    def camera_obstacles(self, passage, reverse):
        """Find an unblocked camera path around the roof at each end of a passage."""
        key = (passage, reverse)
        if key in self.clearances:
            return self.clearances[key]
        deps = bpy.context.evaluated_depsgraph_get()
        blocked = []
        steps = max(20, math.ceil(passage.length))
        for i in range(steps + 1):
            d = passage.length * i / steps
            eye, look = self.chase(passage, d, reverse)
            for rise in (0.0, 3.0, 6.0, 9.0, 12.0):
                candidate = eye + v3(0, 0, rise)
                hit = self.scene.ray_cast(deps, candidate, (look - candidate).normalized(), distance=7.0)
                if not hit[0]:
                    break
            if rise:
                blocked.append((d, rise))
        self.clearances[key] = blocked
        return blocked

    def track(self, passage, t, reverse=False):
        if passage.is_fold:
            turns = passage.edge["quarter_turns"]
            arrival = t >= 0.5
            local = (t - 0.5) * 2 if arrival else t * 2
            approach = 1 if passage.a["xz"][1] < 0 else -1
            anchor = passage.points[-1 if arrival else 0]
            if arrival:
                angle = turns * math.pi / 2
                heading = v3(approach * math.sin(angle), approach * math.cos(angle), 0)
                # Track the turned bearing from beside the pavilion. An eye inside
                # its roof would show stone in place of the destination facade.
                at = anchor + heading * (local * 1.8)
                eye = at + v3(-13.0 + local * 3.0, -(13.0 - local * 1.5) * approach, 8.4 - local * 1.4)
                self.lens(eye, at + v3(0, -2.0 * approach, 1.7), 32)
                return "Arrival  /  exit faces " + ("east" if heading.x > 0 else "west")
            eye = anchor + v3(4.8 - local * 1.45, -(12.0 - 3.1 * local) * approach, 4.8 - 0.9 * local)
            self.lens(eye, anchor + v3(0, -2.0 * approach, 1.6), 31)
            return "Threshold  /  face " + ("north" if approach > 0 else "south")
        d = passage.length * t
        eye, look = self.chase(passage, d, reverse)
        rise = max(
            (
                h * smooth(1 - abs(d - point) / 13.0)
                for point, h in self.camera_obstacles(passage, reverse)
            ),
            default=0.0,
        )
        eye.z += rise
        self.lens(eye, look, 31)
        return "Arrival" if t > 0.82 else "Approach" if t < 0.24 else "Crossing"

    def picture(self):
        """Read Blender’s saved render, whose pixel buffer stays private in background mode."""
        from PIL import Image

        path = self.tmp / "view.png"
        self.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        with Image.open(path) as image:
            return image.convert("RGB")

    def sunlit_picture(self):
        """Use the authored sun, bounce light and shader materials for the district cover."""
        scene = self.scene
        stage_world = scene.world
        engine = scene.render.engine
        view = scene.view_settings
        previous = view.view_transform, view.look, view.exposure
        denoiser = os.getenv("OIDN_DENOISE") or shutil.which("oidnDenoise")
        try:
            scene.render.engine = "CYCLES"
            scene.cycles.samples = 24 if denoiser else 64
            scene.cycles.use_denoising = False
            world = self.sunlight_world.copy()
            tree = world.node_tree
            path = tree.nodes.new("ShaderNodeLightPath")
            mix = tree.nodes.new("ShaderNodeMixShader")
            backdrop = tree.nodes.new("ShaderNodeBackground")
            backdrop.inputs["Color"].default_value = (0.040, 0.073, 0.082, 1)
            backdrop.inputs["Strength"].default_value = 0.8
            output = next(n for n in tree.nodes if n.type == "OUTPUT_WORLD")
            ambient = output.inputs["Surface"].links[0].from_socket
            tree.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
            tree.links.new(ambient, mix.inputs[1])
            tree.links.new(backdrop.outputs[0], mix.inputs[2])
            tree.links.new(mix.outputs[0], output.inputs["Surface"])
            scene.world = world
            view.view_transform = "AgX"
            view.look = "AgX - Medium High Contrast"
            view.exposure = 0.22
            image = self.picture()
            if not denoiser:
                return image
            return denoise_srgb(image, denoiser, self.tmp)
        finally:
            scene.world = stage_world
            scene.render.engine = engine
            view.view_transform, view.look, view.exposure = previous

    def screen(self, point):
        from bpy_extras.object_utils import world_to_camera_view

        projected = world_to_camera_view(self.scene, self.camera, point)
        return projected.x * self.draw_size[0], (1 - projected.y) * self.draw_size[1]


def denoise_srgb(image, executable, directory):
    """Open Image Denoise accepts normalized sRGB when the LDR flag is set."""
    import numpy as np
    from PIL import Image

    source, destination = directory / "cover.pfm", directory / "clean.pfm"
    width, height = image.size
    with source.open("wb") as file:
        file.write(f"PF\n{width} {height}\n-1.0\n".encode())
        np.flipud(np.asarray(image, dtype="<f4") / 255.0).tofile(file)
    subprocess.run(
        [
            executable,
            "-d",
            "cpu",
            "--ldr",
            str(source),
            "--srgb",
            "--threads",
            str(max(1, bpy.context.scene.render.threads)),
            "-o",
            str(destination),
        ],
        check=True,
    )
    with destination.open("rb") as file:
        if file.readline().strip() != b"PF" or file.readline().split() != [
            str(width).encode(),
            str(height).encode(),
        ]:
            raise ValueError("Unexpected output dimensions from Open Image Denoise")
        endian = "<" if float(file.readline()) < 0 else ">"
        pixels = np.fromfile(file, dtype=endian + "f4").reshape((height, width, 3))
    return Image.fromarray(np.rint(np.clip(np.flipud(pixels), 0, 1) * 255).astype("uint8"))


def route_ink(studio, image, passage):
    """Overlay only the route being read in the atlas. A fold has two disconnected endpoints."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(image)
    pixels = [studio.screen(p) for p in passage.points]
    if not passage.is_fold:
        draw.line(pixels, fill=(30, 48, 49), width=6, joint="curve")
        draw.line(pixels, fill=(239, 182, 85), width=3, joint="curve")
    for pos, label in ((pixels[0], "IN"), (pixels[-1], "OUT")):
        x, y = pos
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 218, 135), outline=INK, width=2)
        draw.text(
            (x + 8, y - 7), label, font=font(12, "mark"), fill=PAPER, stroke_width=2, stroke_fill=INK
        )


def bearing_ink(image, edge, arrival):
    """A compass gives player bearing while the external camera shows the intact mouth."""
    from PIL import ImageDraw

    pen = ImageDraw.Draw(image, "RGBA")
    side = round(image.width * 0.088)
    x, y = side * 0.82, side * 0.91
    r = side * 0.36
    pen.ellipse(
        (x - r * 1.46, y - r * 1.46, x + r * 1.46, y + r * 1.46),
        fill=(12, 29, 31, 220),
        outline=(160, 170, 147, 190),
        width=max(1, round(side * 0.018)),
    )
    pen.text(
        (x, y - r * 1.44), "N", font=font(max(10, round(side * 0.20)), "mark"), fill=PAPER, anchor="ma"
    )
    sign = 1 if edge.a["xz"][1] < 0 else -1
    angle = edge.edge["quarter_turns"] * math.pi / 2 if arrival else 0.0
    dx, dy = sign * math.sin(angle), -sign * math.cos(angle)
    tip = (x + dx * r * 0.96, y + dy * r * 0.96)
    tail = (x - dx * r * 0.57, y - dy * r * 0.57)
    pen.line([tail, tip], fill=GOLD, width=max(2, round(side * 0.055)))
    pen.polygon(
        [
            tip,
            (x + dx * r * 0.38 - dy * r * 0.24, y + dy * r * 0.38 + dx * r * 0.24),
            (x + dx * r * 0.38 + dy * r * 0.24, y + dy * r * 0.38 - dx * r * 0.24),
        ],
        fill=GOLD,
    )
    return image


def plate(studio, item, filename):
    from PIL import Image, ImageDraw

    ident, kind = item["id"], item["kind"]
    studio.population(ident)
    studio.set_size(TILE)
    art = []
    if kind == "route":
        edge = studio.edges[ident]
        studio.ortho(edge.framing(), -81, 71, 1.19)
        image = studio.picture()
        route_ink(studio, image, edge)
        art.append(("Endpoints" if edge.is_fold else "Route plan", image))
        visits = (
            [(0.09, False), (0.42, False), (0.88, False)]
            if not edge.is_fold
            else [(0.12, False), (0.55, False), (0.91, False)]
        )
        for index, (t, reverse) in enumerate(visits):
            label = studio.track(edge, t, reverse)
            if not edge.is_fold:
                label = (edge.a["label"], "Midway", edge.b["label"])[index]
            elif index == 2:
                sign = 1 if edge.a["xz"][1] < 0 else -1
                root = edge.points[-1]
                studio.lens(root + v3(2.8, -12.5 * sign, 4.2), root + v3(0, -3.8 * sign, 2.9), 36)
                label = edge.b["label"] + "  /  return inscription"
            image = studio.picture()
            if edge.is_fold and index < 2:
                bearing_ink(image, edge, index == 1)
            art.append((label, image))
    else:
        points = studio.subject(ident)
        high_view = (
            "Roof and footprint"
            if kind in {"room", "architecture"}
            else ("Rim and handle" if kind == "rite" else "Upper profile")
        )
        views = [
            ("South-east", -56, 29),
            ("South-west", -136, 24),
            ("North-east", 51, 34),
            (high_view, -79, 73),
        ]
        for k, (label, az, alt) in enumerate(views):
            if len(item.get("placements_xyz", [])) == 4:
                points = studio.subject(ident, k)
                label = (
                    "South Temple · V notch",
                    "South Pyramid · V notch",
                    "North Temple · two bars",
                    "North Pyramid · two bars",
                )[k]
            studio.ortho(points, az, alt)
            art.append((label, studio.picture()))
    w, h = TILE
    pad = 22
    sheet = Image.new("RGB", (w * 2 + pad * 3, 2 * (h + 35) + 116), INK)
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 12), "MANDALA RIFT", font=font(15, "mark"), fill=MINT)
    draw.text((pad, 32), item["title"], font=font(35, "title"), fill=PAPER)
    tag = TYPE_NAMES.get(kind, kind.title())
    draw.text((sheet.width - pad, 50), tag.upper(), font=font(16, "mark"), fill=GOLD, anchor="ra")
    draw.line((pad, 85, sheet.width - pad, 85), fill=(70, 88, 86), width=1)
    for index, (label, image) in enumerate(art):
        x = pad + (index % 2) * (w + pad)
        y = 97 + (index // 2) * (h + 35)
        sheet.paste(image, (x, y))
        draw.text((x, y + h + 4), label, font=font(17), fill=PAPER)
    sheet.save(filename, quality=87, method=4)


def caption(image, title, phase):
    from PIL import ImageDraw

    w, h = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    size = max(14, round(w * 0.022))
    bottom = round(size * 2.35)
    draw.rectangle((0, h - bottom, w, h), fill=(12, 27, 29, 218))
    draw.rectangle((round(w * 0.024), h - bottom + 8, round(w * 0.024) + 2, h - 8), fill=GOLD)
    draw.text(
        (round(w * 0.024) + 11, h - bottom / 2), title, font=font(size, "title"), fill=PAPER, anchor="lm"
    )
    if phase:
        draw.text(
            (w - round(w * 0.024), h - bottom / 2),
            phase,
            font=font(max(11, int(size * 0.74)), "mark"),
            fill=MINT,
            anchor="rm",
        )
    return image


class Movie:
    def __init__(self, target, size, chapters=()):
        self.target = target
        self.temp = target.with_name(target.stem + "-partial.mp4")
        self.metadata = None
        args = [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-y",
            "-f",
            "rawvideo",
            "-pixel_format",
            "rgb24",
            "-video_size",
            f"{size[0]}x{size[1]}",
            "-framerate",
            str(FPS),
            "-i",
            "-",
        ]
        if chapters:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".ffmeta", delete=False) as meta:
                meta.write(";FFMETADATA1\n")
                start = 0
                for title, frames in chapters:
                    meta.write(
                        f"[CHAPTER]\nTIMEBASE=1/{FPS}\nSTART={start}\nEND={start + frames}\ntitle={title}\n"
                    )
                    start += frames
                self.metadata = Path(meta.name)
            args.extend(
                ["-f", "ffmetadata", "-i", str(self.metadata), "-map", "0:v", "-map_chapters", "1"]
            )
        self.encoder = subprocess.Popen(
            args
            + [
                "-an",
                "-c:v",
                "libx264",
                "-threads",
                "2",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(self.temp),
            ],
            stdin=subprocess.PIPE,
        )

    def frame(self, image):
        self.encoder.stdin.write(image.tobytes())

    def __enter__(self):
        return self

    def __exit__(self, kind, value, trace):
        self.encoder.stdin.close()
        code = self.encoder.wait()
        if self.metadata:
            self.metadata.unlink(missing_ok=True)
        if code or kind:
            self.temp.unlink(missing_ok=True)
            if not kind:
                raise RuntimeError(f"FFmpeg failed for {self.target}")
        else:
            self.temp.replace(self.target)


def clip(studio, item, filename):
    ident, kind = item["id"], item["kind"]
    studio.population(ident)
    studio.set_size(CLIP)
    nframe = 48 if kind == "route" else 40
    paired = len(item.get("placements_xyz", [])) == 4
    if kind != "route":
        points = studio.subject(ident, 0 if paired else None)
        scale = max(studio.ortho(points, az, 31) for az in range(-133, 39, 12))
    with Movie(filename, CLIP) as movie:
        for i in range(nframe):
            t = i / (nframe - 1)
            if kind == "route":
                label = studio.track(studio.edges[ident], t)
            elif paired:
                north = t >= 0.5
                points = studio.subject(ident, 2 if north else 0)
                phase = (t - 0.5) * 2 if north else t * 2
                studio.ortho(points, (85 if north else -95) + 54 * smooth(phase), 27, scale=scale)
                label = "North · twin bars" if north else "South · V notch"
            else:
                studio.ortho(
                    points, -132 + 168 * smooth(t), 25 + 11 * math.sin(math.pi * t), scale=scale
                )
                label = TYPE_NAMES.get(kind, kind.title())
            image = studio.picture()
            if kind == "route" and studio.edges[ident].is_fold:
                bearing_ink(image, studio.edges[ident], t >= 0.5)
            movie.frame(caption(image, item["title"], label))


def district(studio, filename):
    from PIL import ImageDraw

    studio.population()
    studio.set_size((1680, 944))
    points = [p for values in studio.all_bounds.values() for p in values]
    studio.ortho(points, -12, 40, 1.10)
    image = studio.sunlit_picture()
    draw = ImageDraw.Draw(image, "RGBA")
    for key, dx, dy in (
        ("atk", -20, 9),
        ("def", 15, -20),
        ("ford", -53, -25),
        ("mid", 24, -65),
        ("a", -97, 3),
        ("b", 69, 18),
    ):
        node = studio.nodes[key]
        x, y = studio.screen(v3(*node["xz"], node["y"] + 0.5))
        tx, ty = x + dx, y + dy
        text = node["label"]
        f = font(17)
        width = draw.textlength(text, font=f)
        if dx < 0:
            tx -= width
        tx = max(15, min(image.width - width - 15, tx))
        ty = max(90, min(image.height - 64, ty))
        end = (tx + width if dx < 0 else tx, ty + 10)
        draw.line([(x, y), end], fill=GOLD, width=2)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=GOLD)
        draw.rounded_rectangle(
            (tx - 5, ty - 2, tx + width + 5, ty + 24), radius=3, fill=(13, 29, 31, 220)
        )
        draw.text((tx, ty), text, font=f, fill=PAPER)
    image = caption(image, "Mandala Rift", "GHAT  /  TEMPLE  /  MARKET")
    image.save(filename, quality=91, method=5)


def tour(studio, filename):
    studio.population()
    studio.set_size(HD)
    district_points = [p for values in studio.all_bounds.values() for p in values]
    shots = [
        ("Mandala Rift", "District overview", "wide", None, 42),
        ("Spice Gate", "The southern arrival", "orbit", "room-atk", 38),
        ("Reed Steps to Reed Ford", "Shallow-water crossing", "track", "route-steps_s-ford-water", 45),
        ("Dry Bank to Ghat Mandapa", "The western approach", "track", "route-bank-a-ramp", 40),
        ("Ghat Mandapa", "The bell screen", "orbit", "room-a", 39),
        (
            "South Temple to South Pyramid",
            "Paired thresholds",
            "track",
            "route-temple_s-pyramid_s-fold",
            54,
        ),
        ("Sluice to Bazaar Sanctuary", "The raised crossing", "track", "route-mid-b-ramp", 41),
        ("Bazaar Sanctuary", "The eastern site", "orbit", "room-b", 40),
        ("Water Gate", "The northern arrival", "orbit", "room-def", 37),
        ("Mandala Rift", "District overview", "wide", None, 35),
    ]
    with Movie(filename, HD, [(name, frames) for name, _, _, _, frames in shots]) as movie:
        for name, section, kind, ident, count in shots:
            for frame in range(count):
                t = frame / (count - 1)
                subtitle = section
                if kind == "wide":
                    studio.ortho(district_points, -23 + 15 * smooth(t), 43 + 6 * t, 1.07)
                elif kind == "orbit":
                    studio.ortho(studio.subject(ident), -70 + 23 * smooth(t), 27 + 4 * t, 1.13)
                else:
                    phase = studio.track(studio.edges[ident], t)
                    if studio.edges[ident].is_fold:
                        subtitle = phase
                image = studio.picture()
                if kind == "track" and studio.edges[ident].is_fold:
                    bearing_ink(image, studio.edges[ident], t >= 0.5)
                movie.frame(caption(image, name, subtitle))


def run(args):
    if not bpy:
        env = dict(os.environ)
        env.setdefault("LP_NUM_THREADS", str(max(1, args.threads)))
        cmd = [
            "blender",
            "-b",
            "-t",
            str(max(1, args.threads)),
            "--python-exit-code",
            "1",
            "-P",
            str(Path(__file__).resolve()),
            "--",
            *sys.argv[1:],
        ]
        subprocess.run(cmd, env=env, check=True)
        return
    bpy.ops.wm.open_mainfile(filepath=str(args.scene.resolve()))
    catalog = json.loads(args.catalog.read_text())
    elements = catalog["elements"]
    out = args.output.resolve()
    for folder in ("renders", "clips"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    selected = [i for i in elements if not args.only or i["id"] in args.only]
    if args.only and len(selected) != len(set(args.only)):
        raise ValueError("Unknown inventory ID in --only")

    def pending(path):
        return args.force or not path.is_file() or path.stat().st_size < 512

    with tempfile.TemporaryDirectory(prefix="mandala-camera-") as work:
        studio = CameraStudio(json.loads(MAP.read_text()), elements, Path(work))
        for item in selected:
            ident = item["id"]
            if args.stage in ("plates", "all") and pending(out / "renders" / (ident + ".webp")):
                plate(studio, item, out / "renders" / (ident + ".webp"))
                print("PLATE", ident, flush=True)
            if args.stage in ("clips", "all") and pending(out / "clips" / (ident + ".mp4")):
                clip(studio, item, out / "clips" / (ident + ".mp4"))
                print("CLIP", ident, flush=True)
        if not args.only and args.stage in ("district", "all") and pending(out / "district.webp"):
            district(studio, out / "district.webp")
            print("DISTRICT", flush=True)
        if not args.only and args.stage in ("tour", "all") and pending(out / "tour.mp4"):
            tour(studio, out / "tour.mp4")
            print("TOUR", flush=True)


if __name__ == "__main__":
    run(arguments())
