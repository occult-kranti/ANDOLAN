"""Build editable upright wayfinding marks from the bundled DejaVu outlines."""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
DEPTH_M = 0.045


def _bronze():
    name = "YUGA Wayfinding Bronze"
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        material.diffuse_color = (0.64, 0.39, 0.13, 1.0)
        shader.inputs["Base Color"].default_value = material.diffuse_color
        shader.inputs["Metallic"].default_value = 0.68
        shader.inputs["Roughness"].default_value = 0.36
    return material


def _outline(font, item):
    # Blender's native text tessellator preserves counters in the rings and digits.
    # Temporarily link the curve so its evaluated geometry belongs to a depsgraph.
    curve = bpy.data.curves.new(item["key"], "FONT")
    source = bpy.data.objects.new(item["key"], curve)
    try:
        curve.font = font
        curve.body = chr(int(item["unicode"][2:], 16))
        curve.extrude = 0.016
        curve.bevel_depth = 0.002
        curve.bevel_resolution = 0
        curve.resolution_u = 4
        bpy.context.scene.collection.objects.link(source)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph), depsgraph=depsgraph)
    finally:
        bpy.data.objects.remove(source, do_unlink=True)
        bpy.data.curves.remove(curve)
    if not mesh.vertices or not mesh.polygons:
        bpy.data.meshes.remove(mesh)
        raise ValueError(f"Empty outline for {item['unicode']}")

    points = [v.co for v in mesh.vertices]
    left, right = min(v.x for v in points), max(v.x for v in points)
    bottom, top = min(v.y for v in points), max(v.y for v in points)
    back, front = min(v.z for v in points), max(v.z for v in points)
    face_scale = 1.0 / max(right - left, top - bottom)
    depth_scale = DEPTH_M / (front - back)
    # Local text XY becomes vertical XZ; the Blender front normal is -Y.
    mesh.transform(Matrix((
        (face_scale, 0, 0, -0.5 * (left + right) * face_scale),
        (0, 0, -depth_scale, 0.5 * (back + front) * depth_scale),
        (0, face_scale, 0, -bottom * face_scale),
        (0, 0, 0, 1),
    )))
    mesh.update()
    return mesh


def build_symbols():
    """Return 24 fresh, unlinked asset collections keyed by manifest glyph name."""
    manifest = json.loads((HERE / "manifest.json").read_text())
    font_spec = manifest["source_font"]
    font_path = HERE / font_spec["file"]
    if hashlib.sha256(font_path.read_bytes()).hexdigest() != font_spec["sha256"]:
        raise ValueError("The symbol font differs from the pinned FireRed repository subset")
    font = bpy.data.fonts.load(str(font_path), check_existing=False)
    material = _bronze()
    collections = {}
    try:
        for item in manifest["glyphs"]:
            key = item["key"]
            label = "YUGA Symbol " + key
            mesh = _outline(font, item)
            mesh.name = label
            mesh.materials.append(material)
            obj = bpy.data.objects.new(label, mesh)
            collection = bpy.data.collections.new(label)
            collection.objects.link(obj)
            collection["glyph_key"] = key
            collection["source_codepoint"] = item["unicode"]
            collection["source_font_sha256"] = font_spec["sha256"]
            collections[key] = collection
    finally:
        bpy.data.fonts.remove(font)
    return collections
