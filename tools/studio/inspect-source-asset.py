#!/usr/bin/env python3
"""Inspect an embedded GLB without altering it; optionally render three stills.

The transformed-eight-corner bounds and camera-heading approach are adapted
from universal-modder um/blender/render_sprites.py at
3c4ac6c38e411b8c543bce217eae197039516bfc. Unlike that sprite helper, this tool
preserves imported metre scale/transforms and performs no synthetic motion.
See NOTICE/universal-modder-MIT.txt and the complete MIT notice below.

MIT License

Copyright (c) 2026 Rehan and universal-modder contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib

UPSTREAM = {
    "repository": "https://github.com/rehan-remade/universal-modder",
    "commit": "3c4ac6c38e411b8c543bce217eae197039516bfc",
    "files": {
        "um/blender/render_sprites.py": "358dc36a2712f640b02da6d5ce28ef48cc54daebc5a4760c790997fb2e27bd71",
        "um/render3d.py": "7352f7cf80f2d8b8b30e1627ba8b2786bc9c21315b89c2f55258c5b62767dfa9",
        "LICENSE": "db6cfa2ad2c44f73080440c866c4a3a078749d84ba40b4dfa27d50f18a525543",
    },
    "license": "MIT; full notice retained in this tool and adjacent NOTICE file",
    "adapted_scope": "Transformed mesh bound-box corners and camera headings; original validation, raw-scale fit, census and receipts.",
}
VIEWS = (("front-oblique", -55.0, 28.0), ("rear-oblique", 125.0, 28.0), ("top", -90.0, 89.9))
MAX_BYTES = 64 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path: Path, with_bytes=False):
    """Reject malformed containers and external-resource dependencies pre-import."""
    if path.suffix.lower() != ".glb" or not path.is_file():
        raise ValueError("input must be an existing .glb file")
    if not 20 <= path.stat().st_size <= MAX_BYTES:
        raise ValueError("input must be 20 bytes to 64 MiB")
    raw = path.read_bytes()
    if not 20 <= len(raw) <= MAX_BYTES:
        raise ValueError("input byte length changed or exceeds inspection cap")
    magic, version, total = struct.unpack_from("<4sII", raw)
    if magic != b"glTF" or version != 2 or total != len(raw):
        raise ValueError("invalid GLB2 header or declared byte length")
    chunks, offset = [], 12
    while offset < total:
        if offset + 8 > total:
            raise ValueError("truncated GLB chunk header")
        size, kind = struct.unpack_from("<II", raw, offset)
        offset += 8
        if size % 4 or offset + size > total:
            raise ValueError("invalid GLB chunk length/alignment")
        chunks.append((kind, raw[offset:offset + size]))
        offset += size
    if not chunks or chunks[0][0] != 0x4E4F534A or len(chunks) > 2 or (len(chunks) == 2 and chunks[1][0] != 0x004E4942):
        raise ValueError("expected JSON then optional embedded BIN chunk")
    model = json.loads(chunks[0][1].decode("utf-8").rstrip(" \t\r\n"))
    if not isinstance(model, dict) or not isinstance(model.get("asset"), dict) or model["asset"].get("version") != "2.0":
        raise ValueError("expected glTF2 asset")
    if not isinstance(model.get("meshes"), list) or not model["meshes"]:
        raise ValueError("GLB has no meshes")
    if not isinstance(model.get("nodes", []), list) or len(model.get("nodes", [])) > 4096:
        raise ValueError("inspection cap: 4096 source nodes")
    for collection in ("buffers", "images"):
        entries = model.get(collection, [])
        if not isinstance(entries, list):
            raise ValueError("invalid resource collection")
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError("invalid resource descriptor")
            if "uri" in item and (not isinstance(item["uri"], str) or not item["uri"].startswith("data:")):
                raise ValueError("external resource URI rejected; use an embedded owned GLB")
    return (model, raw) if with_bytes else model


def transformed_corners(corners, matrix):
    """Use every bound-box corner, including mirrored/nonuniform transforms."""
    result = []
    for corner in corners:
        values = [sum(float(matrix[row][col]) * float((*corner, 1)[col]) for col in range(4)) for row in range(4)]
        if not all(math.isfinite(value) for value in values) or abs(values[3]) < 1e-12:
            raise ValueError("nonfinite or singular transformed corner")
        result.append(tuple(value / values[3] for value in values[:3]))
    return result


def bounds(points):
    if not points or not all(len(point) == 3 and all(math.isfinite(value) for value in point) for point in points):
        raise ValueError("bounds need finite 3D corners")
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    size = [high[i] - low[i] for i in range(3)]
    if max(size) <= 1e-8:
        raise ValueError("zero-size geometry")
    return {"min": low, "max": high, "size": size, "center": [(low[i] + high[i]) / 2 for i in range(3)]}


def fit_scale(projected, unit_width, unit_height, margin=1.2):
    """Fit Blender's measured unit camera frame; do not assume scale/aspect semantics."""
    if not math.isfinite(unit_width) or not math.isfinite(unit_height) or unit_width <= 0 or unit_height <= 0 or not projected or not math.isfinite(margin) or margin < 1:
        raise ValueError("invalid camera frame")
    width = 2 * max(abs(point[0]) for point in projected)
    height = 2 * max(abs(point[1]) for point in projected)
    result = max(width / unit_width, height / unit_height) * margin
    if not math.isfinite(result) or result <= 1e-8:
        raise ValueError("degenerate camera fit")
    return result


def reserve_output(path: Path):
    # mkdir(exist_ok=False) also rejects symlinks and empty existing directories.
    path.mkdir(parents=True, exist_ok=False)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def png_dimensions(path: Path):
    """Validate the tool's noninterlaced RGBA8 PNG and bounded pixel payload."""
    if not 45 <= path.stat().st_size <= 16 * 1024 * 1024: raise ValueError("invalid still byte size")
    data = path.read_bytes()
    if not 45 <= len(data) <= 16 * 1024 * 1024 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("missing/non-PNG still")
    offset, dimensions, compressed, ended = 8, None, bytearray(), False
    while offset + 12 <= len(data):
        size, = struct.unpack_from(">I", data, offset)
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + size]
        if offset + 12 + size > len(data): raise ValueError("truncated PNG chunk")
        checksum, = struct.unpack_from(">I", data, offset + 8 + size)
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != checksum: raise ValueError("PNG checksum mismatch")
        if dimensions is None:
            if kind != b"IHDR" or size != 13: raise ValueError("missing PNG IHDR")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if not 1 <= width <= 1024 or not 1 <= height <= 1024 or (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError("expected bounded noninterlaced RGBA8 PNG")
            dimensions = (width, height)
        elif kind == b"IDAT": compressed.extend(payload)
        elif kind == b"IEND":
            if size or offset + 12 != len(data): raise ValueError("invalid PNG end")
            ended = True
            break
        offset += 12 + size
    if not dimensions or not compressed or not ended: raise ValueError("incomplete PNG")
    width, height = dimensions
    expected = height * (width * 4 + 1)
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(compressed, expected + 1)
    if not decoder.eof or decoder.unused_data or len(pixels) != expected or any(pixels[row * (width * 4 + 1)] > 4 for row in range(height)):
        raise ValueError("invalid PNG pixel payload")
    return dimensions


def finite_sequence(values, length):
    try:
        return isinstance(values, list) and len(values) == length and all(type(value) in (float, int) and math.isfinite(value) for value in values)
    except OverflowError:
        return False


def validate_inspection(output: Path, cfg):
    result = json.loads((output / "inspection.json").read_text())
    if not isinstance(result, dict) or result.get("schema_version") != 1 or result.get("input_sha256_after") != cfg["input_sha256"]:
        raise ValueError("missing/mismatched inspection identity")
    if not isinstance(result.get("blender_version"), str) or not result["blender_version"]:
        raise ValueError("missing Blender version")
    geometry, census, objects, views = (result.get(key) for key in ("geometry", "census", "mesh_objects", "views"))
    if not isinstance(geometry, dict) or not all(finite_sequence(geometry.get(key), 3) for key in ("min", "max", "size", "center")) or max(geometry["size"]) <= 1e-8:
        raise ValueError("invalid geometry bounds")
    if not isinstance(census, dict) or not isinstance(objects, list) or not 1 <= len(objects) <= 4096 or census.get("mesh_objects") != len(objects):
        raise ValueError("invalid geometry census")
    if type(census.get("evaluated_vertices")) is not int or not 1 <= census["evaluated_vertices"] <= 2000000:
        raise ValueError("invalid vertex count")
    if not isinstance(views, list) or len(views) != 3 or {view.get("id") for view in views if isinstance(view, dict)} != {view[0] for view in VIEWS}:
        raise ValueError("missing required three camera views")
    expected_render = {"requested": cfg["render"], "engine": "Cycles", "device": "CPU", "threads": cfg["threads"], "samples": cfg["samples"], "dimensions": [cfg["width"], cfg["height"]]}
    if result.get("render") != expected_render: raise ValueError("render settings mismatch")
    for view in views:
        low, high = view.get("projected_corner_min"), view.get("projected_corner_max")
        if not finite_sequence(low, 3) or not finite_sequence(high, 3) or any(low[i] > high[i] for i in range(3)) or min(low[:2]) < .05 or max(high[:2]) > .95 or view.get("all_corners_inside_5pct_margin") is not True:
            raise ValueError("unverified camera border fit")
        if not finite_sequence([view.get(key) for key in ("near", "far", "ortho_scale")], 3) or not 0 < view["near"] < low[2] <= high[2] < view["far"] or view["ortho_scale"] <= 0:
            raise ValueError("unverified camera clipping fit")
        if not finite_sequence(view.get("location"), 3) or not finite_sequence(view.get("target"), 3) or not isinstance(view.get("matrix_world"), list) or len(view["matrix_world"]) != 4 or not all(finite_sequence(row, 4) for row in view["matrix_world"]):
            raise ValueError("invalid camera transform")
        if cfg["render"]:
            image = view.get("image")
            expected_name = view["id"] + ".png"
            if not isinstance(image, dict) or image.get("path") != expected_name: raise ValueError("missing still record")
            path = output / expected_name
            if not path.is_file() or path.is_symlink() or image.get("bytes") != path.stat().st_size or image.get("sha256") != digest(path): raise ValueError("missing/changed still bytes")
            if png_dimensions(path) != (cfg["width"], cfg["height"]) or (image.get("width"), image.get("height")) != (cfg["width"], cfg["height"]): raise ValueError("still dimensions mismatch")
    return result


def blender_worker(config_path: Path):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    cfg = json.loads(config_path.read_text())
    source, output = Path(cfg["input"]), Path(cfg["output"])
    if digest(source) != cfg["input_sha256"]:
        raise ValueError("input changed before Blender import")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.gltf(filepath=str(source))
    scene.frame_set(1)
    bpy.context.view_layer.update()
    imported = list(scene.objects)
    parts = [obj for obj in imported if obj.type == "MESH"]
    if not parts or len(imported) > 4096:
        raise ValueError("empty geometry or imported object cap exceeded")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    all_corners, objects = [], []
    total_vertices = 0
    for obj in parts:
        evaluated = obj.evaluated_get(depsgraph)
        corners = transformed_corners(evaluated.bound_box, evaluated.matrix_world)
        all_corners.extend(corners)
        mesh = evaluated.to_mesh()
        try:
            total_vertices += len(mesh.vertices)
            if total_vertices > 2000000:
                raise ValueError("inspection cap: two million evaluated vertices")
            mesh.calc_loop_triangles()
            objects.append({"name": obj.name, "vertices": len(mesh.vertices), "triangles": len(mesh.loop_triangles), "materials": [slot.material.name if slot.material else None for slot in obj.material_slots], "matrix_world": [list(row) for row in obj.matrix_world], "world_bounds": bounds(corners)})
        finally:
            evaluated.to_mesh_clear()
    geometry = bounds(all_corners)
    target = Vector(geometry["center"])
    diagonal = Vector(geometry["size"]).length
    scene.render.resolution_x, scene.render.resolution_y = cfg["width"], cfg["height"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = cfg["samples"]
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = cfg["threads"]
    scene.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("Inspection world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (.13, .16, .21, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = .6
    scene.world = world
    for name, azimuth, energy in (("key", -45, 2.5), ("fill", 140, 1.0)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        scene.collection.objects.link(light)
        light.data.energy = energy
        light.rotation_euler = (math.radians(35), 0, math.radians(azimuth))
        light.data.angle = math.radians(12)
    camera = bpy.data.objects.new("Inspection camera", bpy.data.cameras.new("Inspection camera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start = max(.001, diagonal / 100000)
    camera.data.clip_end = diagonal * 10 + 10
    views = []
    for name, azimuth, elevation in VIEWS:
        az, el = math.radians(azimuth), math.radians(elevation)
        camera.location = target + Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) * (diagonal * 2 + 1)
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = 1
        bpy.context.view_layer.update()
        inverse = camera.matrix_world.inverted()
        projected = [inverse @ Vector(corner) for corner in all_corners]
        frame = camera.data.view_frame(scene=scene)
        camera.data.ortho_scale = fit_scale(projected, max(v.x for v in frame) - min(v.x for v in frame), max(v.y for v in frame) - min(v.y for v in frame))
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(scene, camera, Vector(corner)) for corner in all_corners]
        minimum = [min(point[axis] for point in ndc) for axis in range(3)]
        maximum = [max(point[axis] for point in ndc) for axis in range(3)]
        fits = minimum[0] >= .05 and minimum[1] >= .05 and maximum[0] <= .95 and maximum[1] <= .95 and minimum[2] > camera.data.clip_start and maximum[2] < camera.data.clip_end
        if not fits:
            raise ValueError(f"camera fit failed for {name}: {minimum}..{maximum}")
        view = {"id": name, "azimuth_deg": azimuth, "elevation_deg": elevation, "target": list(target), "location": list(camera.location), "matrix_world": [list(row) for row in camera.matrix_world], "ortho_scale": camera.data.ortho_scale, "near": camera.data.clip_start, "far": camera.data.clip_end, "projected_corner_min": minimum, "projected_corner_max": maximum, "all_corners_inside_5pct_margin": fits}
        if cfg["render"]:
            image = output / f"{name}.png"
            scene.render.filepath = str(image)
            bpy.ops.render.render(write_still=True)
            view["image"] = {"path": image.name, "bytes": image.stat().st_size, "sha256": digest(image), "width": cfg["width"], "height": cfg["height"]}
        views.append(view)
    result = {"schema_version": 1, "blender_version": bpy.app.version_string, "coordinate_frame": "Blender import coordinates: metres, +Z up. GLB importer axis conversion retained; no geometry normalization or root motion.", "pose": "Blender import-default pose evaluated at frame1; not a clip/contact review", "render": {"requested": cfg["render"], "engine": "Cycles", "device": "CPU", "threads": cfg["threads"], "samples": cfg["samples"], "dimensions": [cfg["width"], cfg["height"]]}, "geometry": geometry, "census": {"objects": len(imported), "mesh_objects": len(parts), "unique_meshes": len({obj.data.as_pointer() for obj in parts}), "evaluated_vertices": total_vertices, "evaluated_triangles": sum(obj["triangles"] for obj in objects), "materials": len({slot.material.as_pointer() for obj in parts for slot in obj.material_slots if slot.material}), "armatures": [{"name": obj.name, "bones": len(obj.data.bones)} for obj in imported if obj.type == "ARMATURE"], "actions": [{"name": action.name, "frame_range": list(action.frame_range)} for action in bpy.data.actions], "images": [{"name": image.name, "size": list(image.size), "source": image.source} for image in bpy.data.images]}, "mesh_objects": objects, "views": views, "input_sha256_after": digest(source), "scope": "Source-asset geometry and still-view inspection. No collision/traversability, deformed motion, contact, native integration or hardware FPS acceptance."}
    if result["input_sha256_after"] != cfg["input_sha256"]:
        raise ValueError("source changed during Blender inspection")
    write_json(output / "inspection.json", result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="fresh directory; existing paths rejected")
    parser.add_argument("--blender", default="blender4.3")
    parser.add_argument("--render", action="store_true", help="render three stills; otherwise inspect and fit only")
    parser.add_argument("--threads", type=int, choices=range(1, 9), default=8)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--samples", type=int, choices=range(1, 33), default=8)
    parser.add_argument("--timeout", type=int, default=300, help="Blender wall limit, 1..600 seconds; failure log retained")
    args = parser.parse_args(argv)
    if not 128 <= args.width <= 1024 or not 128 <= args.height <= 1024:
        parser.error("dimensions must each be 128..1024")
    if not 1 <= args.timeout <= 600:
        parser.error("timeout must be 1..600 seconds")
    notice = Path(__file__).parent / "NOTICE/universal-modder-MIT.txt"
    if digest(notice) != UPSTREAM["files"]["LICENSE"]:
        raise ValueError("retained MIT notice does not match pinned upstream")
    source = args.input.resolve(strict=True)
    model, validated_bytes = read_glb(source, with_bytes=True)
    executable = shutil.which(args.blender)
    if not executable:
        raise ValueError("Blender executable not found")
    output = args.output.absolute()
    reserve_output(output)
    # Bind the actual bytes validated above, rather than a second mutable read.
    original = hashlib.sha256(validated_bytes).hexdigest()
    cfg = {"input": str(source), "input_sha256": original, "output": str(output), "render": args.render, "threads": args.threads, "width": args.width, "height": args.height, "samples": args.samples}
    config = output / "config.json"
    write_json(config, cfg)
    command = [executable, "--background", "--factory-startup", "--disable-autoexec", "--threads", str(args.threads), "--python-exit-code", "1", "--python", str(Path(__file__).resolve()), "--", "--blender-worker", str(config)]
    failure = None
    with (output / "blender.log").open("w", encoding="utf-8") as log:
        try:
            run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False, timeout=args.timeout)
            returncode = run.returncode
        except subprocess.TimeoutExpired:
            returncode = None
            failure = f"Blender exceeded {args.timeout}-second wall limit; partial output retained"
    unchanged = source.is_file() and digest(source) == original
    inspection_path = output / "inspection.json"
    success = returncode == 0 and unchanged and inspection_path.is_file()
    if success:
        try:
            validate_inspection(output, cfg)
        except (ValueError, OSError, KeyError, TypeError, zlib.error) as error:
            success = False
            failure = "Worker evidence rejected: " + str(error)
    elif failure is None:
        failure = "Blender failed, input changed or inspection evidence is missing"
    shutil.copy2(notice, output / "universal-modder-MIT.txt")
    receipt = {"passed": success, "command": command, "blender_exit_code": returncode, "failure": failure, "timeout_s": args.timeout, "input": {"path": str(source), "bytes": len(validated_bytes), "bytes_after": source.stat().st_size if source.is_file() else None, "sha256_before": original, "sha256_after": digest(source) if source.is_file() else None, "unchanged": unchanged, "glTF_asset": model["asset"]}, "tool": {"path": str(Path(__file__).resolve()), "sha256": digest(Path(__file__))}, "upstream": UPSTREAM, "notice_sha256": digest(notice), "outputs": {path.name: {"bytes": path.stat().st_size, "sha256": digest(path)} for path in sorted(output.iterdir()) if path.is_file()}, "scope": "Original owned GLB inspection; no animation/contact/gameplay acceptance"}
    write_json(output / "receipt.json", receipt)
    print(json.dumps({"passed": success, "receipt": str(output / "receipt.json"), "input_unchanged": unchanged}))
    return 0 if success else 1


if __name__ == "__main__":
    if "--blender-worker" in sys.argv:
        blender_worker(Path(sys.argv[sys.argv.index("--blender-worker") + 1]))
    else:
        try:
            sys.exit(main())
        except (ValueError, OSError, json.JSONDecodeError) as error:
            print(f"asset inspection rejected: {error}", file=sys.stderr)
            sys.exit(2)
