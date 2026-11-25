"""Build an editable dusk court around the posed hero and assigned camera.

Ground is at Z=0. Geometry is staged in camera-relative horizontal metres.
The reference contributes object placement, palette and scale; its pixels
are never mapped to or composited into this scene.
"""
from hashlib import sha256
import json
from math import cos, pi, sin, tau
from pathlib import Path
from random import Random
import struct

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from mathutils.geometry import interpolate_bezier

PROJECT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT / "art/hanuman/match-court-assets"
COURT = PROJECT / "assets/environment/lanka_courtyard.glb"
PICKS = PROJECT / "docs/research/reuse-production-continuation/W4/evidence/selection.json"
COURT_SHA = "1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33"
COLLECTION_NAME = "Hanuman · carved dusk court"


class Geometry:
    """Batch repeated stone parts by material while keeping collection roles."""

    def __init__(self):
        self.vertices = []
        self.faces = []
        self.uvs = []
        self.smooth = []

    def add(self, vertices, faces, smooth=False, offset=(0.0, 0.0), density=1.0):
        first = len(self.vertices)
        vertices = [Vector(p) for p in vertices]
        self.vertices.extend(vertices)
        for face in faces:
            self.faces.append([first + i for i in face])
            self.smooth.append(smooth)
            edge_a = vertices[face[1]] - vertices[face[0]]
            edge_b = vertices[face[2]] - vertices[face[0]]
            normal = edge_a.cross(edge_b)
            dominant = max(range(3), key=lambda a: abs(normal[a]))
            axes = ((1, 2), (0, 2), (0, 1))[dominant]
            for index in face:
                p = vertices[index]
                self.uvs.append(tuple(p[a] * density + offset[i] for i, a in enumerate(axes)))

    def stone(self, x, y, base, w, d, h, cut=.018, rng=None, offset=(0, 0), density=1):
        cut = min(cut, w * .17, d * .17, h * .26)
        half_w = w / 2
        half_d = d / 2
        contour = [(-half_w + cut, -half_d), (half_w - cut, -half_d),
                   (half_w, -half_d + cut), (half_w, half_d - cut),
                   (half_w - cut, half_d), (-half_w + cut, half_d),
                   (-half_w, half_d - cut), (-half_w, -half_d + cut)]
        if rng:
            contour = [(xx + rng.uniform(-cut * .5, cut * .5), yy + rng.uniform(-cut * .5, cut * .5))
                       for xx, yy in contour]
        points = [(x + xx * shrink, y + yy * shrink, zz) for zz, shrink in
                  ((base, .96), (base + h - cut, 1), (base + h, .97)) for xx, yy in contour]
        faces = [tuple(reversed(range(8))), tuple(range(16, 24))]
        for level in (0, 8):
            for i in range(8):
                j = (i + 1) % 8
                faces.append((level + i, level + j, level + j + 8, level + i + 8))
        self.add(points, faces, offset=offset, density=density)

    def lathe(self, x, y, base, section, sides=28):
        points = [(x + r * cos(a * tau / sides), y + r * sin(a * tau / sides), base + z)
                  for z, r in section for a in range(sides)]
        faces = [(row * sides + a, row * sides + (a + 1) % sides,
                  (row + 1) * sides + (a + 1) % sides, (row + 1) * sides + a)
                 for row in range(len(section) - 1) for a in range(sides)]
        self.add(points, faces, smooth=True)

    def tube(self, points, radius, sides=6, *, tip_radius=None):
        points = [Vector(point) for point in points]
        vertices = []
        for i, p in enumerate(points):
            direction = (points[min(i + 1, len(points) - 1)] - points[max(0, i - 1)]).normalized()
            basis = direction.cross(Vector((0, 1, 0))).normalized()
            if basis.length < .1:
                basis = direction.cross(Vector((1, 0, 0))).normalized()
            other = direction.cross(basis)
            ring_radius = radius
            if tip_radius is not None:
                ring_radius += (tip_radius - radius) * (i / (len(points) - 1)) ** .82
            vertices.extend(p + ring_radius * (cos(tau * a / sides) * basis + sin(tau * a / sides) * other)
                            for a in range(sides))
        faces = [(i * sides + j, i * sides + (j + 1) % sides,
                  (i + 1) * sides + (j + 1) % sides, (i + 1) * sides + j)
                 for i in range(len(points) - 1) for j in range(sides)]
        if tip_radius is not None:
            faces.append(tuple(range(len(vertices) - sides, len(vertices))))
        self.add(vertices, faces, smooth=True)

    def object(self, name, material, collection, matrix=None):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        mesh.uv_layers.new(name="Surface coordinates").data.foreach_set("uv", [coord for uv in self.uvs for coord in uv])
        for p, smooth in zip(mesh.polygons, self.smooth):
            p.use_smooth = smooth
        if material:
            mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        if matrix is not None:
            obj.matrix_world = matrix
        return obj


def material(name, color, roughness, metal=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metal
    if emission:
        shader.inputs["Emission Color"].default_value = (*color, 1.0)
        shader.inputs["Emission Strength"].default_value = emission
    return mat


def multiply(nodes, links, output, tint):
    node = nodes.new("ShaderNodeMixRGB")
    node.blend_type = "MULTIPLY"
    node.inputs[0].default_value = 1.0
    node.inputs[2].default_value = (*tint, 1.0)
    links.new(output, node.inputs[1])
    return node.outputs[0]


def rock_images():
    manifest = json.loads((ASSETS / "source-manifest.json").read_text())
    images = {}
    for entry in manifest["inputs"]:
        path = ASSETS / entry["name"]
        if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Court texture differs from source manifest: {path.name}")
        img = bpy.data.images.load(str(path), check_existing=True)
        img.colorspace_settings.name = "sRGB" if entry["role"] == "Diffuse" else "Non-Color"
        if not img.packed_file:
            img.pack()
        images[entry["role"]] = img
    return images


def rock_material(name, images, tint, relief, wet=False):
    mat = material(name, tint, .84)
    tree = mat.node_tree
    nodes, links = tree.nodes, tree.links
    shader = nodes.get("Principled BSDF")
    tex = {}
    for role, img in images.items():
        node = nodes.new("ShaderNodeTexImage")
        node.label = role
        node.image = img
        node.extension = "REPEAT"
        tex[role] = node.outputs["Color"]
    diffuse = multiply(nodes, links, tex["Diffuse"], tint)
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = relief
    links.new(tex["nor_gl"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    mix = nodes.new("ShaderNodeMapRange")
    mix.inputs["From Min"].default_value = .18
    mix.inputs["From Max"].default_value = .88
    mix.inputs["To Min"].default_value = .37 if wet else .58
    mix.inputs["To Max"].default_value = .75 if wet else .90
    links.new(tex["Rough"], mix.inputs["Value"])
    links.new(mix.outputs["Result"], shader.inputs["Roughness"])
    if wet:
        position = nodes.new("ShaderNodeTexCoord")
        weather = nodes.new("ShaderNodeTexNoise")
        weather.label = "Ground-scale weathering across sett joints"
        weather.inputs["Scale"].default_value = 1.35
        weather.inputs["Detail"].default_value = 2.5
        links.new(position.outputs["Object"], weather.inputs["Vector"])
        darkening = nodes.new("ShaderNodeMapRange")
        darkening.inputs["From Min"].default_value = .22
        darkening.inputs["From Max"].default_value = .75
        darkening.inputs["To Min"].default_value = .48
        darkening.inputs["To Max"].default_value = 1.0
        links.new(weather.outputs["Fac"], darkening.inputs["Value"])
        weathered_diffuse = nodes.new("ShaderNodeMixRGB")
        weathered_diffuse.blend_type = "MULTIPLY"
        weathered_diffuse.inputs[0].default_value = 1.0
        links.new(diffuse, weathered_diffuse.inputs[1])
        links.new(darkening.outputs["Result"], weathered_diffuse.inputs[2])
        diffuse = weathered_diffuse.outputs[0]
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 4.7
        noise.inputs["Detail"].default_value = 3
        links.new(position.outputs["Object"], noise.inputs["Vector"])
        puddles = nodes.new("ShaderNodeMapRange")
        puddles.inputs["From Min"].default_value = .50
        puddles.inputs["From Max"].default_value = .64
        puddles.inputs["To Max"].default_value = .37
        links.new(noise.outputs["Fac"], puddles.inputs["Value"])
        links.new(puddles.outputs["Result"], shader.inputs["Coat Weight"])
        shader.inputs["Coat Roughness"].default_value = .14
    links.new(diffuse, shader.inputs["Base Color"])
    return mat


def asset_prototypes():
    """Take the exact whole components reviewed by the water garden team."""
    data = COURT.read_bytes()
    if sha256(data).hexdigest() != COURT_SHA:
        raise ValueError("Court donor changed")
    picked = json.loads(PICKS.read_text())
    if picked["source_sha256"] != COURT_SHA:
        raise ValueError("Court selection was not made against this donor")
    size = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + size])
    binary = memoryview(data)[28 + size:]
    node_map = {entry["name"]: entry["mesh"] for entry in doc["nodes"] if "mesh" in entry}

    def reader(accessor_index):
        a = doc["accessors"][accessor_index]
        view = doc["bufferViews"][a["bufferView"]]
        fmt = struct.Struct("<" + {5126: "f", 5125: "I", 5123: "H", 5121: "B"}[a["componentType"]]
                            * {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]])
        step = view.get("byteStride", fmt.size)
        offset = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        return lambda at: fmt.unpack_from(binary, offset + at * step)

    results = {}
    for name, selection in picked["prototypes"].items():
        surfaces = {}
        center = selection["source_center"]
        for row in selection["selected"]:
            p = doc["meshes"][node_map[row["node"]]]["primitives"][row["surface"]]
            read_pos = reader(p["attributes"]["POSITION"])
            read_uv = reader(p["attributes"]["TEXCOORD_0"])
            read_idx = reader(p["indices"])
            material_name = doc["materials"][p["material"]]["name"]
            batch = surfaces.setdefault(material_name, Geometry())
            selected = row["source_triangle_ids"]
            index_map = {}
            for i in selected:
                face = []
                for n in range(3):
                    src_index = read_idx(3 * i + n)[0]
                    if src_index not in index_map:
                        x, y, z = read_pos(src_index)
                        index_map[src_index] = len(batch.vertices)
                        batch.vertices.append((x - center[0], -(z - center[2]), y - center[1]))
                    face.append(index_map[src_index])
                    u, v = read_uv(src_index)
                    batch.uvs.append((u, 1 - v))
                batch.faces.append(face)
                batch.smooth.append(False)
        if sum(len(b.faces) for b in surfaces.values()) != selection["triangles"]:
            raise ValueError(f"Donor triangle census changed: {name}")
        results[name] = surfaces
    return results


def stone_panel(carving, relief, x, y, z, width=.45, height=.62):
    carving.stone(x, y, z, width, .072, height, .011, density=2.8)
    border_y = y - .042
    left, right = x - width * .38, x + width * .38
    bottom, top = z + .07, z + height - .08
    carving.tube([(left, border_y, bottom), (left, border_y, top), (right, border_y, top),
                  (right, border_y, bottom), (left, border_y, bottom)], .014)
    center = Vector((x, border_y - .006, z + .18))
    radius = width * .43
    for i in range(7):
        angle = -.12 + i * (pi + .24) / 6
        length = radius * (.77 + .36 * sin(angle))
        forward = Vector((cos(angle), 0, sin(angle)))
        cross = Vector((-sin(angle), 0, cos(angle)))
        points = [center + forward * (t * length) + cross * offset * .045
                  for t, offset in ((0, 0), (.32, .5), (.62, .53), (1, 0), (.62, -.53), (.32, -.5), (0, 0))]
        for a in points:
            a.y -= .012
        mound = center + forward * (length * .47) + Vector((0, -.035, 0))
        relief.add([*points[:-1], mound], [(i, (i + 1) % 6, 6) for i in range(6)], smooth=True)
        carving.tube(points, .005, 5)
    for step in range(3):
        carving.tube([(x - radius * .65, border_y, bottom + step * .019),
                      (x + radius * .65, border_y, bottom + step * .019)], .0055)


def gopuram(main, dark, fine, x, y, width, depth, height, rows):
    main.stone(x, y, -.020, width * 1.12, depth * 1.11, height * .072, .06)
    main.stone(x, y, height * .06, width, depth, height * .16, .07)
    for row in range(rows):
        t = row / rows
        z = height * (.21 + t * .72)
        dz = height * .72 / rows
        w = width * (1.0 - .62 * t)
        d = depth * (1.0 - .56 * t)
        main.stone(x, y, z, w, d, dz * .72, .052)
        fine.stone(x, y, z + dz * .72, w * 1.085, d * 1.16, dz * .18, .065)
        count = max(3, 8 - row)
        for i in range(count):
            p = x + ((i + .5) / count - .5) * w * .92
            front = y - d * .5
            dark.stone(p, front - .015, z + dz * .16, w * .061, .030, dz * .47, .013)
            for shift in (-1, 1):
                post = p + w * .044 * shift
                fine.stone(post, front - .006, z + dz * .13, w * .026, .13, dz * .37, .017)
                fine.stone(post, front - .016, z + dz * .114, w * .041, .15, dz * .071, .015)
            fine.stone(p, front - .031, z + dz * .49, w * .122, .145, dz * .095, .020)
            fine.stone(p, front + .012, z + dz * .60, w * .086, .127, dz * .102, .024)
        if row in (0, 2):
            for side in (-1, 1):
                fine.stone(x + side * w * .43, y, z + dz * .7, w * .075, d * 1.17, dz * .25)
    for i in range(5):
        at = x + width * .075 * (i - 2)
        fine.lathe(at, y, height * .89, ((0, width * .032), (.12 * height, width * .011),
                                        (.14 * height, width * .004)), sides=8)


def bell(bronze, x, y, base, scale=1.0):
    profile = [(.002, .121), (.018, .122), (.030, .111), (.041, .089),
               (.078, .078), (.113, .067), (.152, .062), (.181, .049),
               (.196, .028), (.209, .010), (.221, .019), (.237, .016)]
    bronze.lathe(x, y, base, [(h * scale, r * scale) for h, r in profile], sides=32)
    bronze.lathe(x, y, base - .073 * scale, [(0,.009 * scale), (.026 * scale,.017 * scale),
                                             (.049 * scale,.009 * scale), (.083 * scale,.004 * scale)], sides=12)
    for j in range(13):
        center = base + (.255 + j * .058) * scale
        axis = Vector((1, 0, 0)) if j % 2 else Vector((0, 1, 0))
        points = [Vector((x, y, center)) + axis * (sin(a * tau / 18) * .014 * scale)
                  + Vector((0, 0, cos(a * tau / 18) * .040 * scale)) for a in range(19)]
        bronze.tube(points, .0044 * scale, 5)


def leaflet(batch, origin, axis, length, width, twist, asymmetry):
    across = Vector((axis.z, 0, -axis.x)).normalized()
    across = across * cos(twist) + axis.cross(across) * sin(twist)
    normal = axis.cross(across)
    profile = ((.14, .40), (.34, .88), (.58, 1.), (.79, .71), (.93, .28))

    def edge(fraction, breadth):
        bent_center = origin + axis * (fraction * length) - normal * (.09 * length * fraction ** 2)
        return bent_center + across * (breadth * width)

    rim = [origin, *(edge(t, w) for t, w in profile), edge(1., 0.),
           *(edge(t, -w * asymmetry) for t, w in reversed(profile))]
    ridge = origin + axis * (.47 * length) + normal * (.11 * width)
    faces = [(0, 1 + i, 1 + (i + 1) % len(rim)) for i in range(len(rim))]
    batch.add([ridge, *rim], faces, smooth=True)


def tamarind_canopy(stage):
    """Screen-staged growth preserves the open crown and the hanging bells."""
    limbs, shaded, tipped = Geometry(), Geometry(), Geometry()
    bark = material("Court · silhouette bark", (.024, .015, .009), .86)
    leaf_shadow = material("Court · tamarind shade leaves", (.018, .027, .009), .81)
    leaf_tip = material("Court · tamarind rim leaves", (.034, .044, .016), .73)
    rng = Random(22413)

    def anchor(u, v, depth):
        z = stage.z_at(u, v, depth)
        return Vector((stage.x_at(u, depth, z), depth, z))

    main = interpolate_bezier(anchor(-.052, .970, -.55), anchor(.027, 1.008, -.52),
                              anchor(.144, 1.046, -.39), anchor(.274, .992, -.26), 16)
    upper = interpolate_bezier(main[8], anchor(.197, 1.039, -.34),
                               anchor(.278, 1.063, -.17), anchor(.364, 1.011, -.10), 16)
    lower = interpolate_bezier(main[2], anchor(.013, .981, -.37),
                               anchor(.057, .950, -.17), anchor(.132, .930, .02), 13)
    far = interpolate_bezier(main[5], anchor(.118, 1.031, -.12),
                             anchor(.166, .995, .05), anchor(.206, .962, .15), 12)

    for path, base, tip, drop in ((main, .033, .0041, .17), (upper, .016, .0018, .13),
                                  (lower, .016, .0017, .16), (far, .010, .0013, .14)):
        limbs.tube(path, base, 8, tip_radius=tip)
        for i in range(2, len(path), 2):
            stem = path[i]
            side = 1 if i % 4 else -1
            reach = rng.uniform(.10, .22) * side
            fall = drop * rng.uniform(.64, 1.29)
            back = rng.uniform(-.096, .098)
            spray = interpolate_bezier(stem, stem + Vector((reach * .38, back * .5, .020)),
                                       stem + Vector((reach * .84, back * .9, -fall * .52)),
                                       stem + Vector((reach, back, -fall)), 7 + rng.randrange(3))
            limbs.tube(spray, .0032, 5, tip_radius=.00055)
            for j in range(1, len(spray) - 1):
                direction = (spray[j + 1] - spray[j - 1]).normalized()
                fan = Vector((-direction.z, back * 2, direction.x)).normalized()
                taper = 1.14 - .54 * (j / (len(spray) - 1)) ** 1.45
                for flank in (-1, 1):
                    step = (spray[j + 1] - spray[j]) * rng.uniform(-.14, .24)
                    blade = (direction * rng.uniform(.33, .70) + fan * flank).normalized()
                    length = rng.uniform(.042, .076) * taper
                    batch = tipped if rng.random() < .25 else shaded
                    leaflet(batch, spray[j] + step, blade, length, length * rng.uniform(.16, .21),
                            rng.uniform(-.68, .68), rng.uniform(.78, 1.10))
    stage.place(limbs, "Left foreground · forked tamarind limbs and rachises", bark)
    stage.place(shaded, "Left foreground · tapered paired tamarind leaflets", leaf_shadow)
    stage.place(tipped, "Left foreground · tamarind rim leaflets", leaf_tip)


class Court:
    def __init__(self, scene):
        self.scene = scene
        self.camera = scene.camera
        if self.camera is None:
            raise ValueError("Assign a camera before staging the court")
        if scene.collection.children.get(COLLECTION_NAME):
            raise ValueError("Stage the court on a fresh working scene")
        bpy.context.view_layer.update()
        rotation = self.camera.matrix_world.to_quaternion()
        forward = rotation @ Vector((0, 0, -1))
        self.away = Vector((forward.x, forward.y, 0)).normalized()
        if self.away.length < .5:
            raise ValueError("Court requires a forward-looking camera")
        self.right = Vector((self.away.y, -self.away.x, 0))
        self.matrix = Matrix((self.right, self.away, Vector((0,0,1)))).transposed().to_4x4()
        self.collection = bpy.data.collections.new(COLLECTION_NAME)
        scene.collection.children.link(self.collection)
        self.random = Random(77351)

    def project(self, x, y, z):
        return world_to_camera_view(self.scene, self.camera, self.matrix @ Vector((x, y, z)))

    def x_at(self, screen, y, z=0):
        left = self.project(0, y, z).x
        right = self.project(1, y, z).x
        return (screen - left) / (right - left)

    def z_at(self, screen_x, screen_y, depth):
        def sample(z):
            return self.project(self.x_at(screen_x, depth, z), depth, z).y
        lo, hi = -1.0, 7.0
        for _ in range(18):
            mid = (lo + hi) / 2
            if sample(mid) < screen_y:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def place(self, batch, name, mat):
        return batch.object(name, mat, self.collection, self.matrix)

    def point(self, name, xyz, watts, color=(1.0, .35, .11), radius=.18):
        light = bpy.data.lights.new(name, type="POINT")
        light.energy = watts
        light.color = color
        light.shadow_soft_size = radius
        obj = bpy.data.objects.new(name, light)
        self.collection.objects.link(obj)
        obj.location = self.matrix @ Vector(xyz)
        return obj

    def area(self, name, position, target, watts, color, width):
        light = bpy.data.lights.new(name, type="AREA")
        light.energy = watts
        light.color = color
        light.shape = "DISK"
        light.size = width
        obj = bpy.data.objects.new(name, light)
        self.collection.objects.link(obj)
        obj.location = self.matrix @ Vector(position)
        obj.rotation_euler = (self.matrix @ Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
        return obj

    def donor(self, prototypes, name, mat_map, placements):
        for material_name, batch in prototypes[name].items():
            proto = self.place(batch, f"CC0 Lanka {name} · {material_name}", mat_map[material_name])
            for ordinal, (x, y, size) in enumerate(placements):
                obj = proto if ordinal == 0 else proto.copy()
                if ordinal:
                    self.collection.objects.link(obj)
                obj.name = f"CC0 Lanka {name} {ordinal + 1} · {material_name}"
                obj.matrix_world = self.matrix @ Matrix.Translation((x, y, 0)) @ Matrix.Scale(size, 4)


def apply(scene, reference_profile):
    """Integrate a bounded original court. Returns geometry and image receipts."""
    profile = reference_profile.get("court", {})
    stage = Court(scene)
    images = rock_images()
    slab = rock_material("Court · damp gray granite", images, (.071, .076, .079), .98, wet=True)
    wall = rock_material("Court · weathered brown stone", images, (.275, .248, .222), .88)
    fine = rock_material("Court · worn relief and ledges", images, (.306, .281, .264), .73)
    distance = rock_material("Court · blue stone in twilight", images, (.125, .169, .205), .51)
    far_trim = rock_material("Court · cloud-worn tower articulation", images, (.168, .231, .274), .69)
    shade = material("Court · deep portal shade", (.032, .042, .049), .86)
    mortar = material("Court · dark recessed wet joints", (.017, .017, .016), .76)
    puddle = material("Court · shallow wet film", (.009, .011, .012), .22)
    water_nodes, water_links = puddle.node_tree.nodes, puddle.node_tree.links
    water = water_nodes.get("Principled BSDF")
    water.inputs["Coat Weight"].default_value = .48
    water.inputs["Coat Roughness"].default_value = .095
    ripple = water_nodes.new("ShaderNodeTexNoise")
    ripple.inputs["Scale"].default_value = 38
    water_coords = water_nodes.new("ShaderNodeTexCoord")
    water_links.new(water_coords.outputs["Object"], ripple.inputs["Vector"])
    ripple_bump = water_nodes.new("ShaderNodeBump")
    ripple_bump.inputs["Strength"].default_value = .18
    ripple_bump.inputs["Distance"].default_value = .003
    water_links.new(ripple.outputs["Fac"], ripple_bump.inputs["Height"])
    water_links.new(ripple_bump.outputs["Normal"], water.inputs["Normal"])
    water_links.new(ripple_bump.outputs["Normal"], water.inputs["Coat Normal"])
    metal = material("Court · patinated hanging bronze", (.21, .109, .045), .35, .81)
    glow = material("Court · oil lamp flame", (1., .245, .04), .35, emission=5.2)
    glow_core = material("Court · white-gold wick", (1., .66, .31), .22, emission=8.7)

    bed, lots, film = Geometry(), Geometry(), Geometry()
    bed.stone(0, 6.7, -.118, 31, 29, .106)
    stage.place(bed, "Court ground · mortar under the setts", mortar)
    dx, dy = .81, .63
    joint_rng = Random(1393)
    course_offsets = [joint_rng.uniform(-.046, .046) for _ in range(43)]
    floor_pavers = 0
    for course, row in enumerate(range(-11, 31)):
        bottom = (row - .5) * dy + course_offsets[course]
        top_edge = (row + .5) * dy + course_offsets[course + 1]
        y = (bottom + top_edge) * .5
        head_joints = [joint_rng.uniform(-.132, .132) for _ in range(36)]
        for column in range(-17, 18):
            nominal_x = dx * (column + .48 * (row % 2))
            if abs(nominal_x) > 7.2 + max(row * dy, 0) * .55:
                continue
            left = nominal_x - dx * .5 + head_joints[column + 17]
            right = nominal_x + dx * .5 + head_joints[column + 18]
            x = (left + right) * .5
            w = right - left - stage.random.uniform(.008, .022)
            d = top_edge - bottom - stage.random.uniform(.008, .020)
            top = stage.random.uniform(-.003, .004)
            if abs(x) < .85 and abs(y) < .65:
                top = 0.0
            lots.stone(x, y, -.058, w, d, .058 + top, joint_rng.uniform(.009, .016), stage.random,
                       offset=(stage.random.random(), stage.random.random()), density=.77)
            floor_pavers += 1
            if abs(row * dy) < 5 and abs(nominal_x) > .85 and stage.random.random() < .082:
                rx = stage.random.uniform(.045, .18)
                ry = stage.random.uniform(.055, .17)
                vertices = [(x + cos(tau * i / 15) * rx * stage.random.uniform(.83, 1.08),
                             y + sin(tau * i / 15) * ry * stage.random.uniform(.83, 1.08), top + .0018)
                            for i in range(15)]
                film.add(vertices, [tuple(range(15))])
    stage.place(lots, "Court ground · bevelled granite setts", slab)
    if film.faces:
        stage.place(film, "Court ground · detached shallow films", puddle)

    shell, bands, carving, petals = Geometry(), Geometry(), Geometry(), Geometry()
    near_y = float(profile.get("near_column_depth_m", .70))
    near_x = stage.x_at(float(profile.get("near_column_screen_x", .996)), near_y - .32, .63)
    for i, (w, d, z, h) in enumerate(((.99,.91,0,.10),(.89,.84,.1,.09),(.79,.75,.19,.07),
                                    (.73,.70,.26,.065),(.67,.61,.325,.65),(.76,.68,.975,.10),
                                    (.81,.72,1.075,.063),(.70,.64,1.138,.127),(.63,.56,1.265,2.20),
                                    (.74,.67,3.465,.11),(.85,.75,3.575,.13))):
        target = bands if i in {2,3,5,6,9,10} else shell
        target.stone(near_x, near_y, z, w, d, h, .033, stage.random, density=1.3)
    stone_panel(carving, petals, near_x - .035, near_y - .32, .34, .59, .57)
    for side in (-1, 1):
        xx = near_x + .245 * side
        shell.stone(xx, near_y - .292, 1.24, .074, .070, 2.23, .018, density=2.1)
    for z in (.99,1.03,1.09,1.14,1.20,1.27):
        carving.stone(near_x, near_y, z, .72, .639, .025, .008)
    stage.place(shell, "Foreground pillar · weathered primary silhouette", wall)
    stage.place(bands, "Foreground pillar · layered dressed courses", fine)
    stage.place(carving, "Foreground pillar · carved lotus panel and bead lines", wall)
    stage.place(petals, "Foreground pillar · lotus relief petals", fine)

    far, small, voids = Geometry(), Geometry(), Geometry()
    y_left, y_right = 14.8, 17.7
    left_tower_x = stage.x_at(.196, y_left, 1.4)
    right_tower_x = stage.x_at(.971, y_right, 1.6)
    gopuram(far, voids, small, left_tower_x, y_left, 4.72, 3.6, 4.03, 7)
    gopuram(far, voids, small, right_tower_x, y_right, 6.3, 4.3, 4.92, 6)
    gopuram(far, voids, small, stage.x_at(.411, 21.1, 2.5), 21.1, 4.2, 4.4, 4.18, 5)
    stage.place(far, "Distant towers · relief blocks", distance)
    stage.place(small, "Distant towers · roof tiers and finials", far_trim)
    stage.place(voids, "Distant towers · dark recesses", shade)

    donor = asset_prototypes()
    pillar_rows = []
    for side, u, y in ((-1, .028, 8.3), (1, .947, 9.1)):
        x = stage.x_at(u, y, 1.15)
        for i in range(4):
            place_x = x + side * .14 * i
            pillar_rows.append((place_x, y + i * 1.50, .88 + i * .025))
    side_courses, side_trim = Geometry(), Geometry()
    for cluster in (pillar_rows[:4], pillar_rows[4:]):
        x, y, _ = cluster[0]
        deepest = cluster[-1][1]
        for level in range(3):
            side_courses.stone(x, (y + deepest) / 2, level * .089, 1.12 - level * .09, deepest - y + 1.5, .087, .022)
        for z, w, h in ((2.40,.70,.18),(2.57,.79,.072),(2.64,.85,.10),(2.75,.94,.15), (2.91,.82,.13)):
            side_trim.stone(x, (y + deepest) / 2, z, w, deepest - y + .88, h, .035)
        side_courses.stone(x + (-.54 if x < 0 else .54), (y+deepest)/2, .12, .25, deepest-y+1.8, 2.82, .045)
    stage.place(side_courses, "Side galleries · stairs and returning wall", distance)
    stage.place(side_trim, "Side galleries · interlocked stone lintels", distance)
    left_gallery_x = pillar_rows[0][0]
    right_gallery_x = pillar_rows[4][0]
    fill_strength = float(profile.get("background_fill_strength", 1.0))
    if fill_strength > 0:
        stage.area("Court · shoreline haze on left arcade",
                   (left_gallery_x + 1.22, 5.05, 4.2), (left_gallery_x, 8.9, 1.95),
                   122 * fill_strength, (.49, .72, 1.0), 4.0)
        stage.area("Court · upper twilight relief past the bell",
                   (left_tower_x + .4, y_left - 5.7, 6.3), (left_tower_x, y_left + .5, 2.7),
                   464 * fill_strength, (.48, .75, 1.0), 6.1)
        stage.area("Court · upper right terrace above tail",
                   (right_tower_x - 2.4, y_right - 7.0, 6.8), (right_tower_x - .6, y_right, 3.2),
                   481 * fill_strength, (.55, .72, 1.0), 6.1)
        stage.area("Court · low right terrace bounce",
                   (right_gallery_x - 1.55, 5.5, 3.4), (right_gallery_x, 10.1, 1.64),
                   148 * fill_strength, (.63, .80, 1.0), 4.7)
    mats = {"Warm_carved_sandstone": wall, "Pale_limestone": fine, "Indigo_glazed_stone": distance,
            "Aged_brass": metal, "Diyas_warm_emission": glow, "Quiet_stone_inlay": fine}
    stage.donor(donor, "column", mats, pillar_rows)
    stage.donor(donor, "diya", mats, [(stage.x_at(.092, 8.05), 8.05, .39), (stage.x_at(.883, 10.05), 10.05, .40)])

    bowls, flames, cores = Geometry(), Geometry(), Geometry()
    lamp_positions = [(.066, .72, .055, 6), (.875, 2.17, .16, 6), (.14, 7.4, .43, 11),
                      (.32, 10.25, .56, 14), (.786, 10.05, .64, 11),
                      (.044, 8.55, 1.00, 15), (.90, 12.7, 1.37, 23), (.206, 13.1, 1.69, 19)]
    for i, (u, y, z, brightness) in enumerate(lamp_positions):
        x = stage.x_at(u, y, z)
        size = .68 if i < 2 else .74
        scale = lambda values: [(value * size, radius * size) for value, radius in values]
        bowls.lathe(x, y, z, scale(((0, .095), (.018, .096), (.033, .063), (.067, .051), (.10, .105), (.141, .153),
                                   (.151, .153), (.151, .14), (.13,.114), (.113,.075), (.112,.01))), sides=28)
        for j in (-1, 1):
            x_off = x + .051 * j * size
            peak = .104 if j == 1 else .065
            flames.lathe(x_off, y, z + .14 * size, scale(((0,.008), (peak*.32,.018), (peak*.56,.012), (peak,.001))), sides=12)
            cores.lathe(x_off + .004, y - .012, z + .15 * size, scale(((0,.005), (peak*.32,.009), (peak*.73,.001))), sides=10)
        stage.point(f"Court diya · warm pool {i + 1:02d}", (x, y - .032, z + .164), brightness, radius=.085)
    stage.place(bowls, "Diyas · turned bronze basins", metal)
    stage.place(flames, "Diyas · orange flame envelopes", glow)
    stage.place(cores, "Diyas · yellow-white wicks", glow_core)

    bronze = Geometry()
    for u, v, d, scale in ((.045,.807,-.42,.82), (.097,.860,-.30,.78)):
        z = stage.z_at(u, v, d)
        x = stage.x_at(u, d, z)
        bell(bronze, x, d, z, scale)
    stage.place(bronze, "Left foreground · turned bells and alternating chain links", metal)

    tamarind_canopy(stage)

    haze_density = min(.055, float(profile.get("haze_density", .034)))
    if haze_density > 0:
        haze = bpy.data.materials.new("Court · depth-bounded blue haze")
        haze.use_nodes = True
        nodes = haze.node_tree.nodes
        nodes.remove(nodes.get("Principled BSDF"))
        volume = nodes.new("ShaderNodeVolumePrincipled")
        volume.inputs["Color"].default_value = (.29,.51,.67,1)
        volume.inputs["Density"].default_value = haze_density
        volume.inputs["Anisotropy"].default_value = .26
        haze.node_tree.links.new(volume.outputs["Volume"], nodes.get("Material Output").inputs["Volume"])
        volume_geometry = Geometry()
        volume_geometry.stone(0, 15.4, -.045, 33.0, 27.4, 10.6, .038)
        stage.place(volume_geometry, "Court · finite background atmosphere volume", haze)

    bpy.context.view_layer.update()
    return {"collection": stage.collection.name, "pavers": floor_pavers,
            "courtyard_donor_sha256": COURT_SHA,
            "polyhaven_texture_count": len(images),
            "objects": len(stage.collection.objects),
            "lights": sum(o.type == "LIGHT" for o in stage.collection.objects),
            "mesh_triangles": sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                                  for o in stage.collection.objects if o.type == "MESH"),
            "camera_axis_world": [list(stage.right), list(stage.away)],
            "haze_density": haze_density,
            "lotus_pillar_screen_centroid": list(stage.project(near_x, near_y - .32, .63))}
