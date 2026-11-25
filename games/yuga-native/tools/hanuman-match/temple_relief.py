"""Original Lanka study relief for the editable Hanuman court.

The ornament is authored here as height fields. It borrows the motif families
of South Indian temple stonework without tracing an individual building.
Materials sample architectural loop UVs. The hero camera never drives them.
"""
from math import tau

import bpy
from mathutils import Vector
import numpy as np

ATLAS_NAME = "Lanka temple · original carved relief atlas"
RELIEF_UV = "Architectural relief coordinates"
TILE_SIZE = 256
GUARD = 8
ATLAS_SIZE = 2 * TILE_SIZE
NICHE, JALI, LOTUS, COURSES = range(4)


def _tile_levels(tile):
    coords = np.linspace(-GUARD, TILE_SIZE - GUARD, TILE_SIZE) / (TILE_SIZE - 2 * GUARD)
    x, y = np.meshgrid(coords, coords)

    def strip(distance, width):
        return np.clip(1. - abs(distance) / width, 0., 1.)

    def rounded_box(cx, cy, w, h, corner=.02):
        dx = abs(x - cx) - w * .5 + corner
        dy = abs(y - cy) - h * .5 + corner
        distance = np.hypot(np.maximum(dx, 0.), np.maximum(dy, 0.))
        distance += np.minimum(np.maximum(dx, dy), 0.) - corner
        return np.clip(.5 - distance / .011, 0., 1.)

    grain = .020 * np.sin(tau * (2.9*x + 1.6*y)) * np.cos(tau * (2.8*y - x))
    grain += .012 * np.cos(tau * (10.9*x + 4.2*y)) * np.sin(tau * (6.9*y + 4.8*x))
    levels = .40 + grain
    frame = rounded_box(.50, .50, .94, .91) - rounded_box(.50, .50, .88, .82)
    levels += frame * .13

    if tile == NICHE:
        # The projecting keel follows a shallow capped niche and turned piers.
        for center in (.26, .74):
            vertical = np.clip((y - .57) / .29, 0., 1.)
            span = .152 * (1. - vertical ** 1.38)
            rel_x = abs(x - center)
            inside = np.clip((span - rel_x) * 62., 0., 1.)
            inside *= np.clip((y - .19) * 58., 0., 1.) * np.clip((.863 - y) * 80., 0., 1.)
            levels -= inside * .22
            rim = strip(rel_x - span, .031) * np.clip((y - .16) * 21., 0., 1.)
            rim *= np.clip((.893 - y) * 42., 0., 1.)
            levels += rim * .34
            for shift in (-.176, .176):
                pier = rounded_box(center + shift, .40, .036, .48)
                capital = rounded_box(center + shift, .643, .064, .072)
                levels += pier * .10 + capital * .16
            levels += rounded_box(center, .176, .37, .062) * .22
            levels += .18 * strip(np.hypot((x - center) * 1.4, y - .54), .082)
    elif tile == JALI:
        inside = rounded_box(.50, .50, .82, .70)
        levels -= inside * .06
        for row in range(4):
            for column in range(7):
                dx = (x - .16 - column * .113 - .023 * (row % 2)) / .052
                dy = (y - .24 - row * .172) / .063
                radial = np.hypot(dx, dy)
                angle = np.arctan2(dy, dx)
                cut = radial - (.65 + .17 * np.cos(4 * angle))
                hole = np.clip(-cut * 13., 0., 1.)
                levels -= .29 * hole * inside
                levels += .17 * strip(cut, .22) * inside
        levels += .12 * (rounded_box(.50, .50, .86, .76) - inside)
    elif tile == LOTUS:
        for center in (.264, .736):
            dx = x - center
            dy = (y - .50) * .62
            radius = np.hypot(dx, dy)
            angle = np.arctan2(dy, dx)
            flower_edge = .112 + .025 * np.cos(angle * 8)
            levels += .23 * strip(radius - flower_edge, .020)
            levels += .10 * strip(radius - .36 * flower_edge, .021)
            levels += .13 * strip(radius - .192, .020)
            levels -= .07 * np.clip((.18 - radius) / .055, 0., 1.)
        levels += .12 * (strip(y - .137, .030) + strip(y - .863, .030))
    else:
        for row in range(4):
            center = (row + .5) / 4
            levels -= strip(y - row / 4, .016) * .14
            for col in range(6):
                joint = col / 5 - .069 * (row % 2)
                levels -= strip(x - joint, .013) * np.clip((.125 - abs(y - center)) * 90., 0., 1.) * .13
        levels += .16 * (strip(y - .166, .036) + strip(y - .834, .036))
        motif = .039 * np.sin(tau * (5.5*x + .07))
        levels += .21 * strip(y - .50 - motif, .029)

    edge = np.clip(np.minimum.reduce((x, 1.-x, y, 1.-y)) / .018, 0., 1.)
    return np.clip(.40 + edge * (levels - .40), .06, .91)


def atlas_image():
    pixels = np.ones((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    for tile in (NICHE, JALI, LOTUS, COURSES):
        x = TILE_SIZE * (tile % 2)
        y = TILE_SIZE * (tile // 2)
        pixels[y:y + TILE_SIZE, x:x + TILE_SIZE, :3] = _tile_levels(tile)[..., None]
    image = bpy.data.images.new(ATLAS_NAME, width=ATLAS_SIZE, height=ATLAS_SIZE, alpha=True)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.pack()
    return image


def apply_relief(material, image):
    """Layer the authored chisel height over the retained CC0 stone normal."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    stone = nodes["Principled BSDF"]
    project = nodes.new("ShaderNodeUVMap")
    project.label = "Face-local projection with guarded atlas tiles"
    project.uv_map = RELIEF_UV
    relief = nodes.new("ShaderNodeTexImage")
    relief.label = "Original modeled stone motifs · linear height"
    relief.image = image
    relief.extension = "EXTEND"
    links.new(project.outputs["UV"], relief.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .38
    bump.inputs["Distance"].default_value = .031
    links.new(stone.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    links.new(relief.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], stone.inputs["Normal"])
    tone = nodes.new("ShaderNodeMapRange")
    tone.label = "Restrained patina in carved recesses"
    tone.inputs["From Min"].default_value = .12
    tone.inputs["From Max"].default_value = .73
    tone.inputs["To Min"].default_value = .35
    tone.inputs["To Max"].default_value = 1.27
    links.new(relief.outputs["Color"], tone.inputs["Value"])
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1
    links.new(stone.inputs["Base Color"].links[0].from_socket, mix.inputs[1])
    links.new(tone.outputs["Result"], mix.inputs[2])
    links.new(mix.outputs[0], stone.inputs["Base Color"])


class ReliefPanels:
    """Batch painted stone faces with independent stone and ornament UVs."""

    def __init__(self):
        self.vertices = []
        self.corners = []
        self.stone_uvs = []
        self.relief_uvs = []

    def panel(self, center, along, width, height, tile):
        center = Vector(center)
        along = Vector(along)
        up = Vector((0., 0., height))
        start = center - along * (width * .5)
        end = center + along * (width * .5)
        first = len(self.vertices)
        self.vertices.extend((start, end, end + up, start + up))
        self.corners.append(tuple(range(first, first + 4)))
        self.stone_uvs.extend((u + along.dot(center) * .83, v + center.z * .83)
                              for u, v in ((0., 0.), (width * .83, 0.),
                                           (width * .83, height * .83), (0., height * .83)))
        left = (tile % 2 * TILE_SIZE + GUARD + .5) / ATLAS_SIZE
        bottom = (tile // 2 * TILE_SIZE + GUARD + .5) / ATLAS_SIZE
        extent = (TILE_SIZE - 2 * GUARD - 1) / ATLAS_SIZE
        self.relief_uvs.extend(((left, bottom), (left + extent, bottom),
                                (left + extent, bottom + extent), (left, bottom + extent)))

    def band(self, x, y, z, width, depth, height, front_count, side_count, front_tile, side_tile):
        """Apply matching panel widths around all four vertical faces."""
        edges = (
            ((x, y - depth * .5 - .006, z), (1, 0, 0), width, front_count, front_tile),
            ((x + width * .5 + .006, y, z), (0, 1, 0), depth, side_count, side_tile),
            ((x, y + depth * .5 + .006, z), (-1, 0, 0), width, front_count, front_tile),
            ((x - width * .5 - .006, y, z), (0, -1, 0), depth, side_count, side_tile),
        )
        for start, along, span, count, tile in edges:
            pitch = span / count
            for index in range(count):
                center = Vector(start) + Vector(along) * (pitch * (index + .5) - span * .5)
                self.panel(center, along, pitch - .046, height, tile)

    def build(self, stage, material):
        name = "Lanka temple · wrapped carved stone faces"
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices, [], self.corners)
        mesh.update()
        for name_uv, values in (("Surface coordinates", self.stone_uvs), (RELIEF_UV, self.relief_uvs)):
            uv = mesh.uv_layers.new(name=name_uv, do_init=False)
            uv.data.foreach_set("uv", [value for pair in values for value in pair])
        mesh.uv_layers.active_index = 0
        mesh.uv_layers[0].active_render = True
        mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        stage.collection.objects.link(obj)
        obj.matrix_world = stage.matrix
        return len(mesh.polygons)
