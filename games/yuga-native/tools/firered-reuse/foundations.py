"""Editable Blender stock forms for the Rust prototype's four geometry roles.

These use Blender mesh construction. Dimensions follow the cited Rust calls.
All collection origins are at the floor center, in Blender Z-up coordinates.
"""

import math

import bmesh
import bpy


SOURCE = (
    "https://github.com/lime41225/FireRed-remake-and-remaster/blob/"
    "6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/src/"
)


def _stock_mesh(name, make, height):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    try:
        bm.loops.layers.uv.new("UVMap")
        make(bm)
        for vertex in bm.verts:
            vertex.co.z += height * 0.5
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    return mesh


def _face_mesh(name, vertices, faces, uvs):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    layer = mesh.uv_layers.new(name="UVMap")
    for polygon, corners in zip(mesh.polygons, uvs, strict=True):
        for loop, uv in zip(polygon.loop_indices, corners, strict=True):
            layer.data[loop].uv = uv
    return mesh


def _roof(width, depth):
    # A six-band gable of arbitrary footprint. A single band's base is the anchor.
    span = width + 0.5
    thickness = (depth + 0.6) / 6
    half = span * 0.5
    profile = [(-half, 0), (half, 0), (0, 1.3)]
    vertices = [(x, y, height) for y in (-thickness / 2, thickness / 2)
                for x, height in profile]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    triangle = [(0, 0), (1, 0), (0.5, 1)]
    rectangle = [(0, 0), (0, 1), (1, 1), (1, 0)]
    return _face_mesh("Gable band", vertices, faces,
                      [triangle, triangle[::-1], rectangle, rectangle, rectangle])


def build_foundations(*, roof_width=3.0, roof_depth=3.0):
    """Return unlinked collections ready for marking, linking or instancing.

    roof_width and roof_depth specify the building footprint in project units.
    The generated roof band includes the overhang of its reference gable.
    """
    if any(not math.isfinite(value) or value <= 0 for value in (roof_width, roof_depth)):
        raise ValueError("Roof footprint dimensions must be positive and finite")

    block = _stock_mesh(
        "Unit block", lambda bm: bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True), 1.0
    )
    quad = _face_mesh(
        "Surface tile",
        [(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0)],
        [(0, 1, 2), (0, 2, 3)],
        [[(0, 0), (1, 0), (1, 1)], [(0, 0), (1, 1), (0, 1)]],
    )
    plinth = _stock_mesh(
        "Preview plinth",
        lambda bm: bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False, segments=32, radius1=0.75,
            radius2=0.75, depth=0.035, calc_uvs=True,
        ),
        0.035,
    )
    for polygon in plinth.polygons:
        polygon.use_smooth = abs(polygon.normal.z) < 0.5
    roof = _roof(roof_width, roof_depth)

    material = bpy.data.materials.new("Foundation · warm stone")
    material.diffuse_color = (0.42, 0.28, 0.16, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = material.diffuse_color
    shader.inputs["Roughness"].default_value = 0.78

    specs = [
        ("foundation-block", block, "presentation.rs#L213"),
        ("foundation-quad", quad, "presentation.rs#L71-L94"),
        ("foundation-plinth", plinth, "models.rs#L210-L212"),
        ("foundation-roof-band", roof, "presentation.rs#L377-L386"),
    ]
    result = {}
    for key, mesh, source in specs:
        mesh.materials.append(material)
        obj = bpy.data.objects.new(mesh.name, mesh)
        collection = bpy.data.collections.new(mesh.name)
        collection.objects.link(obj)
        collection["primitive_reference"] = SOURCE + source
        result[key] = collection
    result["foundation-roof-band"]["reference_building_footprint"] = [roof_width, roof_depth]
    return result
