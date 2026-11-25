"""Reopen a relocated Blender asset library, compare its donors and try artist reuse."""
import argparse
from collections import Counter
from hashlib import file_digest, sha256
import json
from math import isfinite
from pathlib import Path
import shutil
import struct
import sys
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector


NATIVE = Path(__file__).resolve().parents[2]
EXPECTED = {"Architecture": 8, "Nature": 7, "Symbols": 24, "Foundations": 4}
FOUNDATIONS = {"foundation-block", "foundation-quad", "foundation-plinth", "foundation-roof-band"}


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def file_hash(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def image_hash(image):
    require(len(image.packed_files) == 1, f"Image requires an external file: {image.name}")
    data = image.packed_files[0].packed_file.data
    require(data, f"Empty packed image: {image.name}")
    return sha256(data).hexdigest()


def socket_value(socket):
    value = getattr(socket, "default_value", None)
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if hasattr(value, "to_tuple"):
        return list(value.to_tuple())
    if hasattr(value, "__iter__"):
        return list(value)
    return getattr(value, "name", None)


def material_hash(material):
    """Record the donor node topology, shader inputs and actual packed image bytes."""
    if not material.use_nodes:
        return list(material.diffuse_color)
    tree = material.node_tree
    nodes = {}
    for node in tree.nodes:
        data = {"type": node.bl_idname, "inputs": [
            [socket.identifier, socket_value(socket)] for socket in node.inputs if not socket.is_linked
        ]}
        if node.type == "TEX_IMAGE" and node.image:
            data["texture"] = [image_hash(node.image), node.image.colorspace_settings.name]
        nodes[node.name] = data
    links = sorted((link.from_node.name, link.from_socket.identifier,
                    link.to_node.name, link.to_socket.identifier) for link in tree.links)
    return sha256(json.dumps([nodes, links], sort_keys=True).encode()).hexdigest()


def geometry(mesh):
    """Fingerprint each wound triangle by its corner positions, material and active UV."""
    mesh.calc_loop_triangles()
    positions = []
    for vertex in mesh.vertices:
        require(all(isfinite(v) for v in vertex.co), f"Nonfinite vertex: {mesh.name}")
        positions.append(struct.pack("<3f", *vertex.co))
    uvs = []
    if mesh.uv_layers.active:
        for corner in mesh.uv_layers.active.data:
            require(all(isfinite(v) for v in corner.uv), f"Nonfinite UV: {mesh.name}")
            uvs.append(struct.pack("<2f", *corner.uv))
    materials = [m.name if m else "" for m in mesh.materials]
    triangles = []
    for tri in mesh.loop_triangles:
        corners = [positions[index] + (uvs[loop] if uvs else b"")
                   for index, loop in zip(tri.vertices, tri.loops)]
        # Rotating the first corner preserves winding and ignores loop-index renumbering.
        face = min(b"".join(corners[i:] + corners[:i]) for i in range(3))
        name = materials[tri.material_index] if materials else ""
        triangles.append(name.encode() + b"\0" + face)
    require(triangles, f"Empty mesh: {mesh.name}")
    return {"triangles": len(triangles), "corners_sha256": sha256(b"".join(sorted(triangles))).hexdigest(),
            "materials": {m.name: material_hash(m) for m in mesh.materials if m}}


def donor_geometry():
    out = {}
    files = {}
    for category in ("Architecture", "Nature"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        source = NATIVE / "assets/world" / (category.lower() + ".glb")
        require(bpy.ops.import_scene.gltf(filepath=str(source)) == {"FINISHED"}, str(source))
        named = {o.name: geometry(o.data) for o in bpy.data.objects if o.type == "MESH"}
        require(len(named) == EXPECTED[category], f"Unexpected donor mesh set in {source.name}")
        out[category] = named
        files[category] = file_hash(source)
    return out, files


def inspect_collection(collection, ancestors=()):
    require(collection not in ancestors, "Collection instance or parenting cycle at " + collection.name)
    path = ancestors + (collection,)
    for child in collection.children:
        inspect_collection(child, path)
    for obj in collection.objects:
        if obj.instance_collection:
            inspect_collection(obj.instance_collection, path)


def detached_append(library, names, link):
    """Construct actual instances in an empty consumer scene and evaluate the depsgraph."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(library), link=link) as (source, dest):
        require(set(names) <= set(source.collections), "Missing append/link target")
        dest.collections = list(names)
    roots = {}
    for index, collection in enumerate(dest.collections):
        require(collection and bool(collection.library) == link, "Wrong link/append mode")
        root = bpy.data.objects.new("use_" + collection["yuga_id"], None)
        root.instance_type = "COLLECTION"
        root.instance_collection = collection
        root.location.x = index * 5.0
        bpy.context.scene.collection.objects.link(root)
        roots[root.name] = sum(obj.type == "MESH" for obj in collection.all_objects)
    bpy.context.view_layer.update()
    seen = Counter()
    for instance in bpy.context.evaluated_depsgraph_get().object_instances:
        if instance.is_instance and instance.object.type == "MESH":
            seen[instance.parent.original.name] += 1
    require(dict(seen) == roots, f"Consumer scene did not evaluate all placed meshes: {seen}")
    return {"placed_collections": len(roots), "evaluated_mesh_instances": sum(seen.values())}


def verify(args):
    blend, catalog = args.library.resolve(), args.catalog.resolve()
    manifest = json.loads(catalog.read_text())
    blend_hash = file_hash(blend)
    require(manifest["library_sha256"] == blend_hash, "Catalog points to a different Blender library")
    data = manifest["assets"]
    catalog_file = catalog.with_name("blender_assets.cats.txt")
    catalog_ids = {line.split(":")[0]: line.split(":")[1] for line in catalog_file.read_text().splitlines()
                   if ":" in line and not line.startswith("#")}
    symbols = json.loads((NATIVE / "art/reuse-library/symbols/manifest.json").read_text())
    glyphs = {item["key"]: item for item in symbols["glyphs"]}
    glyph_hash = file_hash(NATIVE / "art/reuse-library/symbols" / symbols["source_font"]["file"])
    require(glyph_hash == symbols["source_font"]["sha256"], "Changed source font")
    counts = Counter(item["category"] for item in data)
    require(counts == EXPECTED, f"Unexpected catalog categories: {counts}")
    ids = {row["id"] for row in data}
    require(len(ids) == len(data), "Duplicate asset IDs in catalog")
    donors, donor_files = donor_geometry()
    checks = []
    with TemporaryDirectory(prefix="yuga-blender-library-check-") as tmp:
        copy = Path(tmp) / "relocated.blend"
        shutil.copyfile(blend, copy)
        bpy.ops.wm.open_mainfile(filepath=str(copy), load_ui=False)
        require(not bpy.data.libraries, "The relocated library depends on external Blender libraries")
        textures = {image.name: image_hash(image) for image in bpy.data.images
                    if image.source in {"FILE", "TILED", "SEQUENCE", "MOVIE"}}
        for font in bpy.data.fonts:
            require(font.name == "Bfont" or font.packed_file, "Unpacked font: " + font.name)
        marked = [c for c in bpy.data.collections if c.asset_data]
        collections = {c.get("yuga_id"): c for c in marked}
        require(len(marked) == len(collections) and set(collections) == ids, "Asset Browser collection mismatch")
        require({row["id"] for row in data if row["category"] == "Foundations"} == FOUNDATIONS,
                "Unexpected foundation assets")
        donor_seen = {key: set() for key in donors}
        distinct_glyphs = set()
        for row in data:
            key, category = row["id"], row["category"]
            coll = collections[key]
            require(coll.get("yuga_category") == category, f"Category mismatch on {key}")
            require(catalog_ids.get(coll.asset_data.catalog_id) == category,
                    f"Asset Browser catalog UUID mismatch on {key}")
            require(coll.preview and all(size > 0 for size in coll.preview.image_size),
                    f"Missing embedded Asset Browser preview: {key}")
            inspect_collection(coll)
            objects = [o for o in coll.all_objects if o.type == "MESH"]
            require(objects and all(not m.hide_select for m in objects), f"Missing editable meshes for {key}")
            signatures = [geometry(obj.data) for obj in objects]
            result = {"id": key, "category": category, "meshes": len(objects),
                      "triangles": sum(sig["triangles"] for sig in signatures)}
            if category in donors:
                node = row["source_node"]
                require(row["source_sha256"] == donor_files[category], f"Donor SHA mismatch on {key}")
                require(node not in donor_seen[category], f"Repeated donor {node}")
                require(len(signatures) == 1 and signatures[0] == donors[category].get(node),
                        f"Donor geometry, UVs or materials differ for {key} / {node}")
                donor_seen[category].add(node)
                result["source_node"] = node
                result["corners_sha256"] = signatures[0]["corners_sha256"]
            elif category == "Symbols":
                glyph = glyphs[key]
                require(row["source_sha256"] == glyph_hash and len(signatures) == 1,
                        f"Symbol font or mesh count differs for {key}")
                require(row["codepoint"] == glyph["unicode"] == coll.get("source_codepoint")
                        and glyph["triangles"] == result["triangles"], f"Symbol signature differs for {key}")
                signature = signatures[0]["corners_sha256"]
                require(signature not in distinct_glyphs, f"Duplicate glyph shape for {key}")
                distinct_glyphs.add(signature)
                result["codepoint"] = glyph["unicode"]
            elif category == "Foundations":
                points = [obj.matrix_world @ Vector(corner) - coll.instance_offset
                          for obj in objects for corner in obj.bound_box]
                lo = [min(p[i] for p in points) for i in range(3)]
                hi = [max(p[i] for p in points) for i in range(3)]
                require(all(isfinite(v) for v in lo + hi), f"Bad foundation bound for {key}")
                require(abs(lo[2]) < 1e-4 and all(abs(hi[i] + lo[i]) < 1e-4 for i in (0, 1)),
                        f"Foundation origin for {key}: {lo}..{hi}")
            checks.append(result)
        require(all(donor_seen[k] == set(donors[k]) for k in donors), "Unrepresented source nodes")
        names = [c.name for c in marked]
        append = detached_append(copy, names, False)
        linked = detached_append(copy, names, True)
        bpy.ops.wm.read_factory_settings(use_empty=True)
    report = {"blender": bpy.app.version_string, "library_file": blend.name,
              "library_sha256": blend_hash, "catalog_sha256": file_hash(catalog),
              "donor_glb_sha256": donor_files, "categories": dict(counts), "assets": checks,
              "packed_textures": textures, "append_into_empty_scene": append, "link_into_empty_scene": linked}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("library", "catalog", "report"):
        parser.add_argument("--" + arg, required=True, type=Path)
    verify(parser.parse_args(sys.argv[sys.argv.index("--") + 1:]))
