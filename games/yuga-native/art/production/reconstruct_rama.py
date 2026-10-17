"""Reconstruct editable Rama from the licensed committed GLB and author surfaces.

python3 reconstruct_rama.py --output /scratch/rama-production.glb --manifest /scratch/manifest.json
blender -b -t 1 --python reconstruct_rama.py -- --editable-from /scratch/rama-production.glb --blend /scratch/rama-reconstructed.blend

The runtime correction appends images/vertex colours to the original binary. It
never re-exports rig, skin or motion through Blender. The editable file is an
explicit GLB reconstruction, not the unavailable original authoring scene.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math
import struct
import sys
import zlib

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
ROOT = GAME.parents[1]
SOURCE = HERE / "reconstruction-source.glb"
SOURCE_SHA256 = "6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e"
PALETTES = {
    "Warm living skin": {"srgb": (.60, .39, .27), "roughness": .83, "normal": .18, "metallic": 0},
    "Brushed antique gold": {"srgb": (.68, .44, .18), "roughness": .43, "normal": .22, "metallic": .72},
    "Ivory folded silk": {"srgb": (.84, .80, .66), "roughness": .82, "normal": .23, "metallic": 0},
    "Grouped black hair": {"srgb": (.045, .035, .029), "roughness": .58, "normal": .25, "metallic": 0},
    "Cobalt woven silk": {"srgb": (.073, .165, .36), "roughness": .73, "normal": .25, "metallic": 0},
}
SIMPLE = {
    "Deep sapphire": ((.025, .10, .25, 1), .28, .15),
    "Warm eye whites": ((.63, .60, .52, 1), .40, 0),
    "Amber brown iris": ((.055, .028, .015, 1), .33, 0),
    "Natural lip warmth": ((.24, .105, .085, 1), .68, 0),
    "Dark bow grip leather": ((.035, .022, .016, 1), .85, 0),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 28 or struct.unpack_from("<4sII", data) != (b"glTF", 2, len(data)):
        raise ValueError("Invalid GLB header/length")
    length, kind = struct.unpack_from("<II", data, 12)
    if kind != 0x4E4F534A:
        raise ValueError("Missing GLB JSON chunk")
    doc = json.loads(data[20:20 + length])
    offset = 20 + length
    binary_length, kind = struct.unpack_from("<II", data, offset)
    if kind != 0x004E4942 or offset + 8 + binary_length != len(data):
        raise ValueError("Invalid GLB binary chunk")
    return data, doc, data[offset + 8:]


def values(doc, binary, index):
    a = doc["accessors"][index]
    view = doc["bufferViews"][a["bufferView"]]
    code, size = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}[a["componentType"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
    start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = view.get("byteStride", components * size)
    return [struct.unpack_from("<" + code * components, binary, start + i * stride) for i in range(a["count"])]


def png_rgb(width, height, pixels):
    if len(pixels) != width * height * 3:
        raise ValueError("PNG RGB byte count differs")
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def texture(palette, roughness=False, size=256):
    """Original low-amplitude woven colour, not a downloaded photograph/scan."""
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            weave = math.sin(x * math.tau / 8) * math.cos(y * math.tau / 8)
            broad = math.sin((x + y * .37) * math.tau / 83)
            if roughness:
                # glTF's green channel is roughness; blue multiplies metallicFactor.
                rgb = (1, palette["roughness"] + weave * .015, 1)
            else:
                variation = .985 + weave * .009 + broad * .006
                # Palette values are already encoded sRGB, matching the source
                # PNG authoring convention. glTF/Godot decodes them for shading.
                # An extra transfer here made rejected revision1 too pale.
                rgb = tuple(c * variation for c in palette["srgb"])
            pixels.extend(round(max(0, min(1, c)) * 255) for c in rgb)
    return png_rgb(size, size, pixels)


def append_view(doc, binary, payload, target=None):
    while len(binary) % 4:
        binary.append(0)
    view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(payload)}
    if target is not None:
        view["target"] = target
    doc["bufferViews"].append(view)
    binary.extend(payload)
    return len(doc["bufferViews"]) - 1


def vertex_tint(material, position, normal):
    """Restrained artist-authored fold modulation; no geometric displacement."""
    _x, y, z = position
    if material == "Cobalt woven silk":
        broad_fold = .90 + .10 * abs(normal[2])
        hem = .93 + .07 * max(0, min(1, (y - .47) / 1.0))
        return (broad_fold * hem,) * 3
    if material == "Ivory folded silk" and y < 1.15:
        fold = .94 + .06 * abs(normal[2])
        return (fold, fold, fold)
    if material == "Warm living skin" and y > 1.58:
        # Gentle warm cheek/temple separation without changing face anatomy.
        side = max(0, min(1, abs(position[0]) / .10))
        face = max(0, min(1, (z - .06) / .09))
        return (1 - .025 * side, 1 - .045 * side * face, 1 - .05 * side * face)
    return (1.0, 1.0, 1.0)


def build(source=SOURCE):
    raw, original, old_binary = read_glb(source)
    if sha(raw) != SOURCE_SHA256:
        raise ValueError("Reconstruction requires the pinned original licensed GLB; source hash differs")
    doc = copy.deepcopy(original)
    binary = bytearray(old_binary)
    generated_images = []
    for mat in doc["materials"]:
        name = mat["name"]
        pbr = mat["pbrMetallicRoughness"]
        if name in PALETTES:
            palette = PALETTES[name]
            pbr["metallicFactor"] = palette["metallic"]
            mat["normalTexture"]["scale"] = palette["normal"]
            for key, roughness in [("baseColorTexture", False), ("metallicRoughnessTexture", True)]:
                image_id = doc["textures"][pbr[key]["index"]]["source"]
                image = doc["images"][image_id]
                payload = texture(palette, roughness)
                image["bufferView"] = append_view(doc, binary, payload)
                generated_images.append({"name": image["name"], "image_index": image_id, "bytes": len(payload), "sha256": sha(payload), "width": 256, "height": 256})
        elif name in SIMPLE:
            color, roughness, metal = SIMPLE[name]
            pbr.update(baseColorFactor=list(color), roughnessFactor=roughness, metallicFactor=metal)
    added_vertices = 0
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            name = doc["materials"][primitive["material"]]["name"]
            if name not in ("Cobalt woven silk", "Ivory folded silk", "Warm living skin"):
                continue
            attrs = primitive["attributes"]
            colors = [vertex_tint(name, p, n) for p, n in zip(values(original, old_binary, attrs["POSITION"]), values(original, old_binary, attrs["NORMAL"]))]
            payload = b"".join(struct.pack("<fff", *color) for color in colors)
            view = append_view(doc, binary, payload, 34962)
            doc["accessors"].append({"bufferView": view, "componentType": 5126, "count": len(colors), "type": "VEC3"})
            attrs["COLOR_0"] = len(doc["accessors"]) - 1
            added_vertices += len(colors)
    doc["buffers"][0]["byteLength"] = len(binary)
    doc.setdefault("asset", {}).setdefault("extras", {})["yuga_reconstruction"] = {
        "revision": 2, "source_sha256": SOURCE_SHA256,
        "scope": "Original material/fold-tint correction from committed licensed GLB; original editable scene unavailable; rig/skin/motion bytes retained.",
    }
    encoded = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\0" * (-len(binary) % 4)
    output = (struct.pack("<4sII", b"glTF", 2, 28 + len(encoded) + len(binary))
              + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
              + struct.pack("<II", len(binary), 0x004E4942) + binary)
    return output, {"generated_images": generated_images, "vertex_tint_count": added_vertices,
                    "original_binary_bytes": len(old_binary), "original_binary_sha256": sha(old_binary),
                    "preserved_sections": ["nodes", "skins", "animations", "scenes", "scene"],
                    "original_accessors": len(original["accessors"]), "original_buffer_views": len(original["bufferViews"])}


def editable_from(glb, destination):
    import bpy
    import numpy as np
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(Path(glb).resolve()))
    bpy.context.scene["YUGA_SOURCE_STATUS"] = "Reconstructed from committed licensed GLB; unavailable original authoring scene was not recovered."
    bpy.context.scene["YUGA_RUNTIME_GLB_SHA256"] = sha(Path(glb).read_bytes())
    bpy.context.scene["YUGA_RUNTIME_EXPORT_CONTRACT"] = "Use reconstruct_rama.py for byte-preserving material export. A general Blender export needs fresh rig/animation equivalence review."
    bpy.context.scene["YUGA_ORIGINAL_GLB_SHA256"] = SOURCE_SHA256
    for image in bpy.data.images:
        # Embedded GLB images are already packed. Calling pack() again on an
        # image with no external filepath can discard its packed bytes.
        if image.type == "IMAGE" and not image.packed_file:
            image.pack()
        if image.type == "IMAGE" and (not image.packed_file or min(image.size) <= 0):
            raise ValueError("Editable reconstruction lost an embedded image: " + image.name)
    armature = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
    hero = next(obj for obj in bpy.data.objects if obj.type == "MESH" and any(mod.type == "ARMATURE" for mod in obj.modifiers))
    if len(armature.data.bones) != 164 or len(bpy.data.actions) != 9:
        raise ValueError("Editable reconstruction lost bones or actions")
    armature.animation_data.use_nla = False
    poses = []
    for action in sorted(bpy.data.actions, key=lambda item: item.name):
        armature.animation_data.action = action
        start, end = action.frame_range
        for step in range(9):
            frame = start + (end - start) * step / 8
            bpy.context.scene.frame_set(int(frame), subframe=frame % 1)
            for bone in armature.pose.bones:
                if not all(math.isfinite(v) for row in bone.matrix for v in row) or abs(bone.matrix.determinant()) < 1e-8:
                    raise ValueError("Non-finite/singular reconstructed pose: " + action.name)
            evaluated = hero.evaluated_get(bpy.context.evaluated_depsgraph_get())
            points = np.empty(len(evaluated.data.vertices) * 3, dtype=np.float32)
            evaluated.data.vertices.foreach_get("co", points)
            points = points.reshape((-1, 3))
            if not np.isfinite(points).all() or float(np.abs(points).max()) > 5:
                raise ValueError("Unbounded reconstructed skinned mesh: " + action.name)
            poses.append({"action": action.name, "fraction": step / 8,
                          "minimum": points.min(axis=0).tolist(), "maximum": points.max(axis=0).tolist()})
    idle = next(action for action in bpy.data.actions if action.name.startswith("idle_"))
    armature.animation_data.action = idle
    bpy.context.scene.frame_set(int(idle.frame_range[0]), subframe=float(idle.frame_range[0]) % 1)
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    return {"path": str(destination), "bytes": destination.stat().st_size, "sha256": sha(destination.read_bytes()),
            "status": "reconstructed_from_runtime_glb_not_original_source_recovery", "blender": bpy.app.version_string,
            "generator_sha256": sha(Path(__file__).read_bytes()), "runtime_glb_sha256": sha(Path(glb).read_bytes()),
            "meshes": len(bpy.data.meshes), "armatures": len(bpy.data.armatures), "actions": len(bpy.data.actions),
            "images_packed": sum(bool(image.packed_file) for image in bpy.data.images),
            "finite_deformed_pose_samples": len(poses), "pose_samples": poses,
            "pose_scope": "81 actual Blender-evaluated reconstructed mesh/bone poses. Finite bounds only; no contact, cloth collision or motion-quality acceptance."}


def write_production_provenance(report, manifest, blend):
    """Keep the package's existing provenance interface and retain its lineage."""
    baseline_path = HERE / "reconstruction-source-provenance.json"
    meta = json.loads(baseline_path.read_text())
    previous = {key: meta[key] for key in ("sha256", "sourceBlend", "sourceBlendSha256", "generator", "generatorSha256")}
    meta.update(
        asset="Original Rama reconstructed surface revision",
        scope="Material/fold-tint correction of committed licensed GLB. Editable scene reconstructed, not recovered. Geometry/rig/skin/animation retained; visual acceptance separate.",
        bytes=report["output"]["bytes"], sha256=report["output"]["sha256"],
        generator=str(Path(__file__).resolve().relative_to(ROOT)), generatorSha256=sha(Path(__file__).read_bytes()),
        sourceBlend=str(blend.resolve().relative_to(ROOT)), sourceBlendSha256=sha(blend.read_bytes()),
    )
    meta["reconstruction"] = {
        "manifest": str(manifest.resolve().relative_to(ROOT)), "manifestSha256": sha(manifest.read_bytes()),
        "inputGLB": str(SOURCE.relative_to(ROOT)), "inputGLBSha256": SOURCE_SHA256,
        "inputProvenance": str(baseline_path.relative_to(ROOT)), "inputProvenanceSha256": sha(baseline_path.read_bytes()),
        "previous": previous, "originalEditableSourceRecovered": False,
        "editableSourceStatus": "Imported from the licensed committed GLB, packed and pose-sampled with Blender 4.3.2. Original modeling history/modifiers are not recovered.",
        "originalMeshAndAnimationBinaryPreserved": True,
        "historicalFields": "originalAuthoredMeshPieces, sourcePipelineHashes, referenceImageHashes, preservedAnimationCurveHashes and 45 poseSamples describe the retained predecessor. New reconstruction tests separately check 81 Blender-evaluated poses and exact original runtime data preservation.",
        "generatedEmbeddedTextures": report["generated_images"],
    }
    text = json.dumps(meta, indent=2) + "\n"
    (HERE / "rama-production.provenance.json").write_text(text)
    (GAME / "NOTICE/RAMA-PRODUCTION-PROVENANCE.json").write_text(text)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--editable-from", type=Path)
    parser.add_argument("--blend", type=Path)
    parser.add_argument("--production-provenance", action="store_true")
    args = parser.parse_args(argv)
    if args.editable_from:
        if not args.blend:
            parser.error("--editable-from requires --blend")
        result = editable_from(args.editable_from, args.blend)
        if args.manifest:
            args.manifest.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return
    if not args.output or not args.manifest:
        parser.error("--output and --manifest are required for runtime generation")
    if args.output.resolve() == args.source.resolve():
        parser.error("Output must not overwrite the pinned reconstruction input")
    if args.production_provenance and (args.output.resolve() != (GAME / "assets/heroes/rama-production.glb").resolve() or not args.blend or not args.blend.is_file()):
        parser.error("Production provenance requires the canonical runtime output and an existing reconstructed --blend")
    output, details = build(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report = {"schema": 1, "revision": 2, "scope": "Original surface/fold-tint correction; no geometry, rig, rest, socket, skin or animation changes. Visual review still required.",
              "source": {"path": str(args.source), "bytes": args.source.stat().st_size, "sha256": SOURCE_SHA256},
              "generator": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__).read_bytes())},
              "output": {"path": str(args.output), "bytes": len(output), "sha256": sha(output)},
              "palettes": PALETTES, "simple_materials": SIMPLE,
              "palette_encoding": "Albedo PNG palettes are encoded sRGB; no extra transfer. Roughness PNG values are linear data. Simple glTF baseColorFactor values retain glTF linear-factor semantics.",
              "licensing": "CC0 MakeHuman anatomy; original project costume/hair/weapons/animation. New deterministic material fields and tints are original CC0-1.0. No commercial-game models or recordings.",
              "editable_source_status": "Original rama-authored.blend unavailable; explicitly reconstructed editable scene is a separate generated artifact.",
              **details}
    args.manifest.write_text(json.dumps(report, indent=2) + "\n")
    if args.production_provenance:
        write_production_provenance(report, args.manifest, args.blend)
    print(json.dumps({"output": report["output"], "vertex_tint_count": details["vertex_tint_count"], "generated_images": len(details["generated_images"])}))


if __name__ == "__main__":
    main()
