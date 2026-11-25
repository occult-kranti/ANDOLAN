"""Photograph the two native Hanuman models in a reproducible Blender Cycles studio.

blender -b -t 2 --python-exit-code 1 -P studio.py -- --take all
The matched studies use identical world coordinates, absolute lens, pose and sampling seed.
"""

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
FOUR = PACK.parent / "four-hero-motion"
sys.path.insert(0, str(FOUR / "tools"))
from blender_stills import load_model, select_pose, aim, coordinate_cloud

sys.path.insert(0, str(FOUR.parents[1] / "tools/hanuman-art"))
from denoise import read_pfm, write_pfm

MODELS = {"baseline": FOUR / "models/hanuman.glb", "enhanced": PACK / "models/hanuman-enhanced.glb"}
# Azimuth is measured from the front. Centers and widths are world-space metres.
STUDIES = [
    ("face", "Face and temple", "idle", 0.18, -26, 3.5, (0, -0.084, 1.81), 0.62),
    ("front", "Full silhouette", "idle", 0.18, 0, 2, (0.09, 0, 1.075), 1.83),
    ("rear", "Crown and nape", "idle", 0.18, 180, 3.5, (0, -0.04, 1.78), 0.76),
    ("tail", "Recovery at 87.5%", "mountain_pulse", 0.875, -142, 8, (0.52, 0.39, 1.38), 1.26),
]
# Lens widths in film frames are horizontal. Identical full-rig cycles drive photos and motion.
TAKES = [
    ("idle", 0.08, 0.45, -29, -17, 4, (-0.075, -0.09, 1.68), 1.46, 27),
    ("mountain_pulse", 0.03, 0.999, -25, -20, 4.8, (0, 0, 1.35), 5.45, 42),
    ("mountain_pulse", 0.72, 0.999, -136, -145, 6, (0.01, 0.15, 1.15), 3.55, 28),
]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cyclorama(tree, camera_shader):
    nodes, links = tree.nodes, tree.links
    coords = nodes.new("ShaderNodeTexCoord")
    plane = nodes.new("ShaderNodeVectorMath")
    plane.operation = "MULTIPLY"
    plane.inputs[1].default_value = (1, 1, 0)
    links.new(coords.outputs["Window"], plane.inputs[0])
    distance = nodes.new("ShaderNodeVectorMath")
    distance.operation = "DISTANCE"
    distance.inputs[1].default_value = (0.70, 0.60, 0)
    links.new(plane.outputs[0], distance.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.061, 0.123, 0.137, 1)
    ramp.color_ramp.elements[1].color = (0.004, 0.009, 0.014, 1)
    ramp.color_ramp.interpolation = "EASE"
    links.new(distance.outputs["Value"], ramp.inputs[0])
    shader = nodes.new(camera_shader)
    links.new(ramp.outputs[0], shader.inputs["Color"])
    return shader


def init(model, thread_count, samples, beauty):
    source_sha = sha(model)
    rig, _ = load_model(model)
    if source_sha != sha(model):
        raise RuntimeError(f"Model changed during import: {model}")
    rig["motion_studio_source_sha256"] = source_sha
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = bool(getattr(bpy.app.build_options, "openimagedenoise", False))
    scene.cycles.seed = 271
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.threads_mode = "FIXED"
    scene.render.threads = thread_count
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.use_sequencer = False
    scene.world = bpy.data.worlds.new("Blue-black studio surround")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.12, 0.17, 0.22, 1)
    bg.inputs[1].default_value = 0.29 if beauty else 0.55
    if beauty:
        # Camera-window lighting gives the photographic sweep a soft, asymmetric teal falloff.
        # Non-camera rays retain the studio fill that lights the actual hero materials.
        nodes = scene.world.node_tree.nodes
        links = scene.world.node_tree.links
        background = cyclorama(scene.world.node_tree, "ShaderNodeBackground")
        view = nodes.new("ShaderNodeLightPath")
        mix = nodes.new("ShaderNodeMixShader")
        links.new(view.outputs["Is Camera Ray"], mix.inputs[0])
        links.new(bg.outputs[0], mix.inputs[1])
        links.new(background.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], nodes.get("World Output").inputs["Surface"])

    bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 0, 0.002))
    floor = bpy.context.object
    floor.name = "Matte basalt sweep"
    mat = bpy.data.materials.new(floor.name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.042, 0.055, 0.06, 1) if beauty else (0.095, 0.111, 0.12, 1)
    bsdf.inputs["Roughness"].default_value = 0.81
    if beauty:
        # A shallow orthographic view sees the distant floor. Blend its far surface
        # into the same painted studio sweep while retaining real contact shadows nearby.
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        position = nodes.new("ShaderNodeNewGeometry")
        distance = nodes.new("ShaderNodeVectorMath")
        distance.operation = "LENGTH"
        links.new(position.outputs["Position"], distance.inputs[0])
        fade = nodes.new("ShaderNodeMapRange")
        fade.inputs["From Min"].default_value = 3
        fade.inputs["From Max"].default_value = 6
        links.new(distance.outputs["Value"], fade.inputs["Value"])
        emission = cyclorama(mat.node_tree, "ShaderNodeEmission")
        mix = nodes.new("ShaderNodeMixShader")
        links.new(fade.outputs["Result"], mix.inputs[0])
        links.new(bsdf.outputs[0], mix.inputs[1])
        links.new(emission.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], nodes.get("Material Output").inputs["Surface"])
    floor.data.materials.append(mat)

    camera = bpy.data.objects.new("Hanuman studio camera", bpy.data.cameras.new("Studio portrait lens"))
    scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.clip_end = 500
    scene.camera = camera
    specs = [
        ("Window key", (-2.6, -3.1, 3.8), 595, 2.2, (1.0, 0.72, 0.52)),
        ("Face fill", (2.1, -2.9, 2.1), 155, 2.2, (0.63, 0.81, 1.0)),
        ("Cold shoulder edge", (1.8, 1.35, 2.9), 515, 1.4, (0.54, 0.83, 1.0)),
        ("Mane edge", (-1.1, 1.82, 3.0), 525, 1.2, (1.0, 0.48, 0.22)),
        ("Eye catch", (-0.28, -2.25, 2.33), 28, 0.40, (1.0, 0.93, 0.84)),
    ]
    if beauty:
        specs.append(("Eye bounce", (-0.12, -1.75, 1.44), 45, 0.45, (1.0, 0.92, 0.84)))
    lights = []
    for name, local, power, size, rgb in specs:
        lamp = bpy.data.lights.new(name, "AREA")
        lamp.shape, lamp.size = "DISK", size
        lamp.energy = power if beauty else power * (0.80 if name == "Mane edge" else 1.0)
        lamp.color = rgb if beauty else tuple(0.40 + 0.60 * x for x in rgb)
        obj = bpy.data.objects.new(name, lamp)
        scene.collection.objects.link(obj)
        lights.append((obj, local))
    return scene, rig, camera, lights


def camera_at(camera, lights, azimuth, elevation, center, width, light_angle=None):
    az, el = math.radians(azimuth), math.radians(elevation)
    back = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    camera.location = Vector(center) + 7 * back
    aim(camera, center)
    camera.data.ortho_scale = width
    # Lights follow each studio view as a unit. Both versions receive identical world-space light transforms.
    light_az = math.radians(azimuth if light_angle is None else light_angle)
    for source, (x, y, z) in lights:
        source.location = (
            x * math.cos(light_az) - y * math.sin(light_az),
            x * math.sin(light_az) + y * math.cos(light_az),
            z,
        )
        aim(source, (0, -0.07, 1.55 if "Eye" in source.name else 1.28))
    bpy.context.view_layer.update()


def snap(scene, path, size):
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def describe(scene, rig, camera, action, phase):
    bpy.context.view_layer.update()
    names = ["head", "wrist.R", "wrist.L", "foot.R", "foot.L", "tail_01", "tail_02", "tail_03", "tail_04"]
    return {
        "action": action,
        "phase": round(phase, 6),
        "frame_in_source": round(scene.frame_current_final, 5),
        "width_m": round(camera.data.ortho_scale, 5),
        "camera_to_world": [[round(v, 6) for v in row] for row in camera.matrix_world],
        "joint_centers_m": {
            n: [round(v, 6) for v in rig.matrix_world @ rig.pose.bones[n].head]
            for n in names
            if n in rig.pose.bones
        },
    }


def write_note(output, name, value):
    output.mkdir(parents=True, exist_ok=True)
    at = output / (name + ".json")
    tmp = at.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(at)


def studies(opts, work, label):
    scene, rig, camera, lights = init(MODELS[label], opts.threads, opts.samples, False)
    records = {}
    if opts.study:
        recorded = json.loads((work / (label + ".json")).read_text())
        if recorded["sha256"] != sha(MODELS[label]):
            raise ValueError("Study patch requires the same model source")
        records.update((r["study"], r) for r in recorded["shots"])
    for key, title, action, phase, az, el, center, width in STUDIES:
        if opts.study and key != opts.study:
            continue
        select_pose(rig, action, phase)
        camera_at(camera, lights, az, el, center, width)
        file = work / (label + "-" + key + ".png")
        snap(scene, file, (480, 622))
        records[key] = {
            "study": key,
            "title": title,
            "pixels": sha(file),
            **describe(scene, rig, camera, action, phase),
        }
    record = {
        "source": str(MODELS[label].name),
        "sha256": rig["motion_studio_source_sha256"],
        "shots": [records[key] for key, *_ in STUDIES],
    }
    write_note(work, label, record)


def font(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans" + ("-Bold" if bold else "") + ".ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def presentation_png(path, opts):
    """Reuse YUGA’s PFM display-transform workflow for builds without bundled OIDN."""
    if not opts.oidn:
        return path
    final = path.with_name(path.stem + "-filtered.png")
    with tempfile.TemporaryDirectory(prefix="yuga-studio-oidn-") as cache:
        src, dest = Path(cache) / "source.pfm", Path(cache) / "result.pfm"
        with Image.open(path) as img:
            pixels = np.asarray(img.convert("RGB"), np.float32) / 255
        write_pfm(src, pixels)
        subprocess.run(
            [
                str(opts.oidn.resolve()),
                "--device",
                "cpu",
                "--threads",
                str(opts.threads),
                "--affinity",
                "0",
                "--ldr",
                str(src),
                "--srgb",
                "--output",
                str(dest),
            ],
            stdout=subprocess.DEVNULL,
            check=True,
        )
        filtered = read_pfm(dest)
        if filtered.shape != pixels.shape:
            raise ValueError("Filtered image size differs from render")
        Image.fromarray(np.rint(filtered.clip(0, 1) * 255).astype(np.uint8)).save(final)
    return final


def contact(opts, work, output):
    rows = [json.loads((work / (label + ".json")).read_text()) for label in MODELS]
    if any(
        a["camera_to_world"] != b["camera_to_world"] or a["width_m"] != b["width_m"]
        for a, b in zip(rows[0]["shots"], rows[1]["shots"])
    ):
        raise RuntimeError("The baseline and enhanced camera gates differ")
    w, h = 480, 622
    tail_detail_crop = (26, 130, 392, 604)
    pad, gap, header, gutter = 22, 8, 69, 42
    sheet = Image.new("RGB", (w * 4 + pad * 2 + gap * 3, (h + gutter) * 2 + header + pad), "#131819")
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 4), "Hanuman", font=font(30, True), fill="#f6e8d4")
    draw.text((pad, 43), "BLENDER CYCLES  /  MATCHED RIG, LENS AND LIGHTING", font=font(13), fill="#b5c1c1")
    for row, label in enumerate(MODELS):
        for col, (key, title, *_) in enumerate(STUDIES):
            x, y = pad + col * (w + gap), header + row * (h + gutter)
            with Image.open(presentation_png(work / (label + "-" + key + ".png"), opts)) as im:
                panel = im.convert("RGB")
                if key == "tail":
                    panel = panel.crop(tail_detail_crop).resize((w, h), Image.Resampling.LANCZOS)
                sheet.paste(panel, (x, y))
            draw.text(
                (x + 3, y + h + 8),
                ("Original" if row == 0 else "Enhanced") + "  /  " + title,
                font=font(16, row == 1),
                fill="#e8dfd2",
            )
    output.mkdir(parents=True, exist_ok=True)
    dest = output / "matched-studies.webp"
    sheet.save(dest, quality=94, method=5)
    write_note(
        output,
        "matched-studies",
        {
            "blender": bpy.app.version_string,
            "samples": opts.samples,
            "denoiser": "Open Image Denoise RT" if opts.oidn else "Blender default",
            "media_sha256": sha(dest),
            "size": list(sheet.size),
            "tail_detail_crop_source_pixels": list(tail_detail_crop),
            "models": rows,
        },
    )


def portrait(opts, output):
    scene, rig, camera, lights = init(MODELS["enhanced"], opts.threads, opts.samples, True)
    # Larger lights on a close product portrait can turn the copper locks almost white.
    # Keep the native pigment and scale the studio fixtures to preserve its shadow color.
    ratios = {"Window key": 0.64, "Face fill": 0.73, "Cold shoulder edge": 0.77, "Mane edge": 0.65}
    for light, _ in lights:
        light.data.energy *= ratios.get(light.name, 1.0)
    scene.view_settings.exposure = -0.11
    phase = 0.22
    select_pose(rig, "idle", phase)
    camera_at(camera, lights, -24, 4.1, (0.04, -0.073, 1.67), 1.48)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "native.png"
        snap(scene, png, (1280, 800))
        dest = output / "hanuman-beauty.webp"
        with Image.open(presentation_png(png, opts)) as frame:
            frame.save(dest, "WEBP", quality=96, method=6)
    write_note(
        output,
        "hanuman-beauty",
        {
            "blender": bpy.app.version_string,
            "renderer": "Cycles CPU",
            "samples": opts.samples,
            "denoiser": "Open Image Denoise RT" if opts.oidn else "Blender default",
            "source_sha256": rig["motion_studio_source_sha256"],
            "media_sha256": sha(dest),
            "size": [1280, 800],
            "studio_light_watts": {light.name: round(light.data.energy, 3) for light, _ in lights},
            "exposure_stops": round(scene.view_settings.exposure, 3),
            **describe(scene, rig, camera, "idle", phase),
        },
    )


def perform(take, index, rig, camera, lights):
    action, begin, end, start_angle, end_angle, el, center, width, count = take
    t = index / (count - 1)
    phase = begin + (end - begin) * t
    eased = t * t * (3 - 2 * t)
    select_pose(rig, action, phase)
    camera_at(
        camera,
        lights,
        start_angle + (end_angle - start_angle) * eased,
        el,
        center,
        width,
        light_angle=start_angle,
    )
    return phase


def measure_framing(opts, output):
    scene, rig, camera, lights = init(MODELS["enhanced"], opts.threads, 1, True)
    meshes = [
        obj
        for obj in scene.objects
        if obj.type == "MESH" and obj.find_armature() == rig and not obj.hide_render and obj.visible_get()
    ]
    if not meshes:
        raise ValueError("No drawable hero mesh is bound to the selected armature")
    take = TAKES[1]
    first = TAKES[0][-1]
    samples = []
    minimum = np.ones(2)
    maximum = np.zeros(2)
    for i in range(take[-1]):
        phase = perform(take, i, rig, camera, lights)
        points = coordinate_cloud(meshes)
        axes = np.asarray(camera.matrix_world)[:3, :2]
        camera_xy = (points - np.asarray(camera.location)) @ axes
        width = camera.data.ortho_scale
        uv = camera_xy / [width, width * 432 / 768] + 0.5
        low, high = uv.min(0), uv.max(0)
        minimum, maximum = np.minimum(minimum, low), np.maximum(maximum, high)
        samples.append(
            {
                "movie_frame": first + i,
                "source_phase": round(phase, 8),
                "bounds": [round(float(v), 7) for v in (*low, *high)],
            }
        )
    if (minimum < 0).any() or (maximum > 1).any():
        raise ValueError(f"Wide action crops the actor: {minimum} … {maximum}")
    write_note(
        output,
        "hanuman-framing",
        {
            "source_sha256": rig["motion_studio_source_sha256"],
            "blender": bpy.app.version_string,
            "action": take[0],
            "size": [768, 432],
            "rig_joints": len(rig.pose.bones),
            "skinned_mesh_objects": len(meshes),
            "evaluated_vertices": len(points),
            "coordinate_system": "Normalized viewport [left,bottom,right,top], bottom-left origin",
            "all_frame_bounds": [round(float(v), 7) for v in (*minimum, *maximum)],
            "frames": samples,
        },
    )


def write_captions(output):
    descriptions = (
        "Hanuman holds the gada upright as the camera moves toward his front.",
        "Mountain Pulse. He plants both feet, raises the gada and drives it forward.",
        "A rear view repeats the recovery. The copper tail brush follows through and settles.",
    )

    def stamp(frame):
        millis = round(frame * 1000 / 24)
        return f"00:00:{millis // 1000:02}.{millis % 1000:03}"

    lines, start = ["WEBVTT", ""], 0
    for take, description in zip(TAKES, descriptions, strict=True):
        end = start + take[-1]
        lines.extend([f"{stamp(start)} --> {stamp(end)}", description, ""])
        start = end
    output.mkdir(parents=True, exist_ok=True)
    (output / "hanuman-showcase.vtt").write_text("\n".join(lines))


def motion(opts, work, output):
    src = MODELS["enhanced"]
    scene, rig, camera, lights = init(src, opts.threads, opts.movie_samples, True)
    frame_no = 0
    records = []
    combine = work / "frames"
    combine.mkdir(exist_ok=True)
    for take in TAKES:
        action, begin, end = take[:3]
        count = take[-1]
        track = []
        for i in range(count):
            phase = perform(take, i, rig, camera, lights)
            frame_path = combine / f"f{frame_no:04}.png"
            snap(scene, frame_path, (768, 432))
            filtered = presentation_png(frame_path, opts)
            if filtered != frame_path:
                filtered.replace(frame_path)
            if i in {0, count // 3, (2 * count) // 3, count - 1}:
                track.append({"movie_frame": frame_no, **describe(scene, rig, camera, action, phase)})
            frame_no += 1
        records.append({"action": action, "frames": count, "source_phase": [begin, end], "samples": track})
    output.mkdir(parents=True, exist_ok=True)
    final = output / "hanuman-showcase.mp4"
    stage = work / final.name
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-v",
            "error",
            "-threads",
            "1",
            "-framerate",
            "24",
            "-i",
            str(combine / "f%04d.png"),
            "-an",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(stage),
        ],
        check=True,
    )
    with stage.open("rb") as source, final.open("wb") as dest:
        shutil.copyfileobj(source, dest)
    write_note(
        output,
        "hanuman-showcase",
        {
            "blender": bpy.app.version_string,
            "renderer": "Cycles CPU",
            "source_sha256": rig["motion_studio_source_sha256"],
            "media_sha256": sha(final),
            "fps": 24,
            "size": [768, 432],
            "denoiser": "Open Image Denoise RT" if opts.oidn else "Blender default",
            "total_frames": frame_no,
            "cycles_samples": opts.movie_samples,
            "shots": records,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--take",
        choices=("all", "baseline", "enhanced", "contact", "beauty", "movie", "framing"),
        default="all",
    )
    parser.add_argument("--study", choices=[k for k, *_ in STUDIES], help="update one existing matched study")
    parser.add_argument("--work", type=Path, default=Path(tempfile.gettempdir()) / "yuga-hanuman-studio")
    parser.add_argument("--output", type=Path, default=PACK / "media")
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--movie-samples", type=int, default=8)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument(
        "--oidn",
        type=Path,
        default=os.environ.get("OIDN_EXECUTABLE") or shutil.which("oidnDenoise"),
        help="optional Intel Open Image Denoise CPU command line executable",
    )
    opts = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    for label in MODELS:
        if opts.take in (label, "all") or label == "enhanced" and opts.take in ("beauty", "movie", "framing"):
            if not MODELS[label].is_file():
                raise FileNotFoundError(MODELS[label])
    opts.work.mkdir(parents=True, exist_ok=True)
    for label in MODELS:
        if opts.take in (label, "all"):
            studies(opts, opts.work, label)
    if opts.take in ("contact", "all"):
        contact(opts, opts.work, opts.output / "images")
    if opts.take in ("beauty", "all"):
        portrait(opts, opts.output / "images")
    if opts.take in ("framing", "all"):
        measure_framing(opts, opts.output / "video")
    if opts.take in ("movie", "all"):
        motion(opts, opts.work, opts.output / "video")
        write_captions(opts.output / "video")
