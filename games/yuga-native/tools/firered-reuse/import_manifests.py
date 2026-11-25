"""Build a Blender asset library from locally populated FireRed Rust-style manifests.

blender -b --factory-startup --python-exit-code 1 -P import_manifests.py -- \
  --assets /path/to/assets --output /path/to/new-library

The output directory contains intake.json and, when usable assets exist,
elements.blend. The input files themselves stay untouched.
"""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import struct
import sys
from tempfile import mkdtemp
from urllib.parse import quote, unquote, urlsplit

import bpy


MANIFESTS = {
    "kit": "letsgo/kit/kit.json",
    "scenery": "letsgo/scenery.json",
    "model": "models/slice-models.json",
    "battle": "letsgo/battle/battle.json",
}
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".tga"}


def digest(path):
    with path.open("rb") as stream:
        h = sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
        return h.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def local_path(root, base, name, allow_parent=False):
    if not isinstance(name, str) or not name or "\\" in name or "\0" in name:
        raise ValueError("expected a relative asset path")
    parts = PurePosixPath(name)
    if (parts.is_absolute() or PureWindowsPath(name).drive or urlsplit(name).scheme
            or (not allow_parent and ".." in parts.parts)):
        raise ValueError("path is outside the asset namespace")
    path = (base / parts).resolve()
    if not path.is_relative_to(root):
        raise ValueError("resolved path is outside the assets root")
    return path


def entries(category, manifest):
    if category == "model":
        if not isinstance(manifest, list):
            raise ValueError("expected an array of model entries")
        for row in manifest:
            yield row["key"], row["file"], row, "model"
        return
    for key, row in manifest.items():
        if category == "scenery":
            for index, scene in enumerate(row["scenes"]):
                yield f"{quote(key, safe='')}/scene/{index}", scene["path"], {
                    **scene, "map": key, "overlay": row.get("overlay", False)
                }, "scenery"
            if row.get("heights"):
                yield f"{quote(key, safe='')}/heights", row["heights"], {"map": key}, "height"
        else:
            yield key, row["path"], row, category


def discover(root):
    rows, manifests, ids = [], {}, set()
    for category, filename in MANIFESTS.items():
        path = local_path(root, root, filename)
        if not path.is_file():
            manifests[filename] = {"status": "absent"}
            continue
        manifests[filename] = {"status": "found", "sha256": digest(path)}
        data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
        for key, asset, fields, role in entries(category, data):
            if not isinstance(key, str) or not key:
                raise ValueError(f"empty or invalid key in {filename}")
            ident = category + "/" + (key if category == "scenery" else quote(key, safe=""))
            if ident in ids:
                raise ValueError(f"duplicate entry {ident} in {filename}")
            ids.add(ident)
            rows.append({"id": ident, "manifest": filename, "path": asset, "role": role,
                         "metadata": {k: v for k, v in fields.items() if k not in {"file", "path"}}})
    return sorted(rows, key=lambda row: row["id"]), manifests


def glb_resources(root, path):
    """Resolve every external buffer/image before giving Blender a GLB."""
    with path.open("rb") as stream:
        header = stream.read(20)
        if len(header) != 20:
            raise ValueError("short GLB header")
        magic, version, length, chunk_size, kind = struct.unpack("<4sIII4s", header)
        if (magic != b"glTF" or version != 2 or kind != b"JSON"
                or length != path.stat().st_size or chunk_size > length - 20):
            raise ValueError("invalid GLB 2 container")
        doc = json.loads(stream.read(chunk_size), object_pairs_hook=unique_object)
    dependencies = {}
    for obj in doc.get("buffers", []) + doc.get("images", []):
        uri = obj.get("uri")
        if uri is None or uri.startswith("data:"):
            continue
        parts = urlsplit(uri)
        if parts.scheme or parts.netloc or parts.query or parts.fragment:
            raise ValueError("expected an embedded or local GLB dependency")
        dep = local_path(root, path.parent, unquote(parts.path), allow_parent=True)
        if not dep.is_file():
            raise FileNotFoundError(f"missing GLB dependency {uri}")
        dependencies[uri] = digest(dep)
    return dependencies


def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def height_grid(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    if not isinstance(data, dict):
        raise ValueError("expected a scenery height-grid object")
    dimensions = [data.get(k) for k in ("width", "height", "res")]
    if any(type(value) is not int or value <= 0 for value in dimensions):
        raise ValueError("expected positive integer width, height and resolution")
    width, height, res = dimensions
    grid = data.get("grid")
    if not isinstance(grid, list) or len(grid) != height * res:
        raise ValueError("height-grid row count differs from height times resolution")
    holes = 0
    for line in grid:
        if not isinstance(line, list) or len(line) != width * res:
            raise ValueError("height-grid column count differs from width times resolution")
        for value in line:
            if value is None:
                holes += 1
            elif not finite_number(value):
                raise ValueError("expected finite height samples or null")
    trees = data.get("trees", [])
    if not isinstance(trees, list) or any(
            not isinstance(point, list) or len(point) != 2 or not all(map(finite_number, point))
            for point in trees):
        raise ValueError("expected tree positions as finite x/z pairs")
    return {"width": width, "height": height, "res": res, "null_samples": holes,
            "sample_count": width * height * res * res, "tree_count": len(trees)}


def asset_name(label):
    # Blender truncates ID names by byte length; retain a deterministic suffix.
    short = label.encode("utf-8")[:46].decode("utf-8", errors="ignore")
    return f"{short} {sha256(label.encode()).hexdigest()[:10]}"


def mark(block, row):
    block.asset_mark()
    block.use_fake_user = True
    block["intake_id"] = row["id"]
    block["source_manifest"] = row["manifest"]
    block["source_path"] = row["path"]
    block["source_sha256"] = row["sha256"]
    block["source_metadata_json"] = json.dumps(row["metadata"], ensure_ascii=False, sort_keys=True)
    block.asset_data.description = f"{row['manifest']} · {row['path']}"
    row["blender_name"] = block.name


def import_geometry(path, fingerprint):
    # Import into an empty scene so imported collections and direct children can
    # be captured without touching earlier sources or flattening the hierarchy.
    scene = bpy.data.scenes.new("Source " + fingerprint[:12])
    bpy.context.window.scene = scene
    before = {key: set(getattr(bpy.data, key)) for key in ("collections", "objects", "actions", "images")}
    result = bpy.ops.import_scene.gltf(filepath=str(path), import_pack_images=True)
    if "FINISHED" not in result:
        raise ValueError(f"Blender did not import {path.name}")
    new = {key: set(getattr(bpy.data, key)) - old for key, old in before.items()}
    if not new["objects"]:
        raise ValueError(f"{path.name} has no scene objects")
    geometry = bpy.data.collections.new("Geometry " + fingerprint[:16])
    children = {child for collection in new["collections"] for child in collection.children}
    for collection in sorted(new["collections"] - children, key=lambda col: col.name):
        geometry.children.link(collection)
    for obj in sorted(new["objects"], key=lambda obj: obj.name):
        if not any(col in new["collections"] for col in obj.users_collection):
            geometry.objects.link(obj)
    for ob in list(scene.collection.objects):
        scene.collection.objects.unlink(ob)
    for child in list(scene.collection.children):
        scene.collection.children.unlink(child)
    scene.collection.children.link(geometry)
    for action in new["actions"]:
        action.use_fake_user = True
    for image in new["images"]:
        if image.source == "FILE" and not image.packed_file:
            image.pack()
    return geometry, {"objects": len(geometry.all_objects),
                      "parented_objects": sum(ob.parent is not None for ob in geometry.all_objects),
                      "armatures": sum(ob.type == "ARMATURE" for ob in geometry.all_objects),
                      "packed_images": sum(bool(i.packed_file) for i in new["images"]),
                      "actions": sorted(action.name for action in new["actions"])}


def build(root, output):
    rows, manifests = discover(root)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    initial = bpy.context.scene
    sources, imported = {}, {}
    for row in rows:
        try:
            path = local_path(root, root, row["path"])
            ext = path.suffix.lower()
            if not path.is_file():
                raise FileNotFoundError("supply the referenced local input")
            is_image = row["role"] == "kit" and ext in IMAGE_TYPES
            is_height = row["role"] == "height" and ext == ".json"
            if not ((ext == ".glb" and row["role"] != "height") or is_image or is_height):
                row.update(status="unsupported", reason=f"unsupported file type {ext}")
                continue
            checksum = digest(path)
            row["sha256"] = checksum
            if "sha256" in row["metadata"] and checksum != row["metadata"]["sha256"]:
                raise ValueError("file differs from manifest SHA-256")
            deps = glb_resources(root, path) if ext == ".glb" else {}
            if is_height:
                row["grid"] = height_grid(path)
        except FileNotFoundError as exc:
            row.update(status="missing", reason=str(exc))
            continue
        except (ValueError, TypeError) as exc:
            row.update(status="invalid", reason=str(exc))
            continue
        # Identical GLBs may refer to different relative textures in two directories.
        fingerprint = sha256(json.dumps([ext, checksum, deps], sort_keys=True).encode()).hexdigest()
        if fingerprint not in sources:
            info = {"sha256": checksum, "dependencies": deps}
            if ext == ".glb":
                ob, detail = import_geometry(path, fingerprint)
                info.update(detail, kind="collection", datablock=ob.name)
            elif is_image:
                ob = bpy.data.images.load(str(path), check_existing=False)
                ob.pack()
                info.update(kind="image", datablock=ob.name)
            else:
                ob = bpy.data.texts.new("Heights " + fingerprint[:12])
                ob.write(path.read_text(encoding="utf-8-sig"))
                ob.use_fake_user = True
                info.update(kind="text", datablock=ob.name)
            sources[fingerprint] = info
            imported[fingerprint] = ob
        shared = imported[fingerprint]
        row.update(status="available", resource=fingerprint)
        if ext == ".glb":
            asset = bpy.data.collections.new(asset_name(row["id"]))
            asset.children.link(shared)
            mark(asset, row)
        elif is_image:
            material = bpy.data.materials.new(asset_name(row["id"]))
            material.use_nodes = True
            tex = material.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = shared
            bsdf = material.node_tree.nodes.get("Principled BSDF")
            material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            mark(material, row)
        else:
            row["blender_name"] = shared.name
    blend = None
    if sources:
        if len(bpy.data.scenes) > 1:
            if bpy.context.window.scene == initial:
                bpy.context.window.scene = next(s for s in bpy.data.scenes if s != initial)
            bpy.data.scenes.remove(initial)
        blend = "elements.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(output / blend), compress=True)
    report = {"schema": 1, "blender": bpy.app.version_string, "library": blend, "assets_directory_present": root.is_dir(),
              "manifests": manifests, "entries": rows, "resources": sources}
    (output / "intake.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--assets", type=Path, help="locally populated assets directory")
    inputs.add_argument("--checkout", type=Path, help="upstream checkout, including its code-only state")
    parser.add_argument("--output", required=True, type=Path, help="fresh destination directory")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.checkout is not None:
        prototype = args.checkout.resolve() / "rust-prototype"
        if not (prototype / "Cargo.toml").is_file():
            parser.error("checkout must contain rust-prototype/Cargo.toml")
        root = (prototype / "assets").resolve()
    else:
        root = args.assets.resolve()
        if not root.is_dir():
            parser.error("assets must be an existing directory")
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(root):
        parser.error("choose a fresh output directory outside the input assets root")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(mkdtemp(prefix=".intake-", dir=output.parent))
    try:
        build(root, tmp)
        tmp.rename(output)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
