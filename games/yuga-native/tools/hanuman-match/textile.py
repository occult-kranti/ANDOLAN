"""Handloom and brocade finish for the existing fitted Hanuman drapery.

The input swatch supplies the woven color and fine relief. Original UV masks
place the red selvedge, supplementary gold threads and tabard lotus across
the actual folded surfaces. All layers stay on the weighted garment meshes.
"""
from pathlib import Path

import bpy
import numpy as np


ART = Path(__file__).resolve().parents[2] / "art" / "hanuman"
SWATCH = ART / "lookdev" / "madder-cloth-imagegen-albedo.png"
ROLES = {
    "Ref · gathered dhoti leg ": ("Madder main weave", "body", (.50, .36), True),
    "Ref · diagonal hip fold ": ("Crossed silk brocade", "crossover", (.16, .29), False),
    "Ref · deep embroidered hem ": ("Gold-woven calf hem", "hem", (.50, .10), True),
    "Ref · hanging center panel": ("Lotus tabard brocade", "tabard", (.14, .27), False),
    "Ref · inner crossover tabard": ("Under-panel brocade", "lining", (.16, .36), False),
}


def fade(low, high, point):
    t = np.clip((point - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


def band(point, start, end, softness=.004):
    return fade(start - softness, start + softness, point) * (
        1 - fade(end - softness, end + softness, point)
    )


def stroke(point, center, width, softness=.003):
    return 1 - fade(width * .53, width + softness, np.abs(point - center))


def brocade(cross, along, repeats):
    """A winding stem, split leaves and two bound threads in the selvedge."""
    phase = (along * repeats) % 1
    # The leaf width narrows to its tips. Alternate the hook around the stem.
    spine = .50 + .16 * np.sin(2 * np.pi * phase)
    vein = stroke(cross, spine, .026, .015)
    turn = (phase + .24) % 1
    leaf_width = .16 * np.maximum(0, np.sin(2 * np.pi * turn))
    leaf_side = np.where(phase < .5, 1, -1)
    leaf = band(cross, spine + leaf_side * .11 - leaf_width,
                spine + leaf_side * .11 + leaf_width, .016)
    leaf *= fade(.016, .044, leaf_width)
    edging = np.maximum(stroke(cross, .14, .028, .015), stroke(cross, .85, .028, .015))
    wash = band(cross, .01, .99, .017)
    pattern = np.maximum(edging * .88, np.maximum(vein * .84, leaf * .68)) * wash
    knots = stroke(cross, .07, .021, .012) * stroke(phase, .21, .21, .03)
    knots = np.maximum(knots, stroke(cross, .93, .021, .012) * stroke(phase, .67, .21, .03))
    return wash * .88, pattern, np.maximum(edging * .46, knots)


def lotus(u, v):
    """Seven original tapered petals and their vein on the front tabard."""
    x = (u - .5) / .29
    y = (.811 - v) / .169
    angle = np.arctan2(x, y + .25)
    radius = np.hypot(x, y + .25)
    petals = np.zeros_like(radius)
    vein = np.zeros_like(radius)
    for index, spread in enumerate((-.98, -.65, -.32, 0, .32, .65, .98)):
        length = .93 - .083 * abs(index - 3)
        width = .20 * np.maximum(0, np.sin(np.pi * np.clip(radius / length, 0, 1)))
        lateral = np.abs(angle - spread)
        fill = 1 - fade(width * .66, width + .018, lateral)
        active = band(radius, .09, length, .025)
        petals = np.maximum(petals, fill * active)
        vein = np.maximum(vein, stroke(lateral, 0, .025, .014) * active)
    stem = stroke(x, 0, .042, .014) * band(y, -.46, -.12, .025)
    return np.maximum(petals * .86, stem), vein * .78


def pack_mask(label, rgba):
    height, width = rgba.shape[:2]
    image = bpy.data.images.new(label, width, height, alpha=True)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(rgba.ravel())
    image.update()
    image.pack()
    return image


def visible_yarns():
    size = 512
    samples = (np.arange(size, dtype=np.float32) + .5) / size
    u, v = samples[None, :], samples[:, None]
    # Alternating exposed warp and weft, with the irregularities of handspun yarn.
    warp_phase = 35 * u + .15 * np.sin(2 * np.pi * 3 * v)
    weft_phase = 33 * v + .11 * np.sin(2 * np.pi * 5 * u)
    warp = stroke(warp_phase % 1, .37, .129, .025)
    weft = stroke(weft_phase % 1, .61, .128, .026)
    over = (np.floor(warp_phase) + np.floor(weft_phase)) % 2
    fuzz = .72 + .14 * np.sin(2 * np.pi * (u * 7 + v * 5))
    worn = fuzz * np.maximum(warp * (.55 + .45 * over), weft * (1 - .45 * over))
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = worn[:, :, None]
    return pack_mask("Hanuman handloom · visible woven crossings", rgba)


def ornament(kind):
    width, height = 768, 1024
    u = (np.arange(width, dtype=np.float32)[None, :] + .5) / width
    v = (np.arange(height, dtype=np.float32)[:, None] + .5) / height
    if kind == "hem":
        channels = brocade(v, u, 26)
    elif kind == "crossover":
        channels = brocade((np.minimum(u, 1 - u) - .021) / .143, v, 13)
    elif kind == "lining":
        channels = brocade((v - .804) / .171, u, 11)
    else:
        long_edge = brocade((np.minimum(u, 1 - u) - .038) / .139, v, 12)
        point_edge = brocade((v - .895) / .093, u, 10)
        dye, embroidery, glint = (np.maximum(a, b) for a, b in zip(long_edge, point_edge))
        petals, veins = lotus(u, v)
        # Broad woven register between the patterned margins and below the buckle.
        field = band(u, .179, .821, .014) * band(v, .031, .852, .013)
        channels = (np.maximum(dye, field * .38),
                    np.maximum(embroidery, petals),
                    np.maximum(glint, veins))
    rgba = np.ones((height, width, 4), dtype=np.float32)
    for channel, mask in enumerate(channels):
        rgba[:, :, channel] = mask
    return pack_mask("Hanuman handloom · " + kind + " brocade UV mask", rgba)


class ClothNodes:
    """Small socket helpers keep the material graph editable and labeled."""

    def __init__(self, material):
        self.nodes, self.links = material.node_tree.nodes, material.node_tree.links
        self.nodes.clear()
        self.serial = 0

    def node(self, kind, label):
        item = self.nodes.new(kind)
        item.label = label
        item.location = (-1420 + (self.serial // 4) * 225, -(self.serial % 4) * 193)
        self.serial += 1
        return item

    def set(self, value, socket):
        if isinstance(value, bpy.types.NodeSocket):
            self.links.new(value, socket)
        else:
            socket.default_value = value

    def vector_scale(self, vector, factors, label):
        node = self.node("ShaderNodeVectorMath", label)
        node.operation = "MULTIPLY"
        self.links.new(vector, node.inputs[0])
        node.inputs[1].default_value = factors
        return node.outputs["Vector"]

    def image(self, image, uv, label, extension):
        node = self.node("ShaderNodeTexImage", label)
        node.image = image
        node.interpolation = "Linear"
        node.extension = extension
        self.links.new(uv, node.inputs["Vector"])
        return node.outputs["Color"]

    def noise(self, vector, scale, detail, label):
        node = self.node("ShaderNodeTexNoise", label)
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        self.links.new(vector, node.inputs["Vector"])
        return node.outputs["Fac"]

    def mix(self, mode, factor, a, b, label):
        node = self.node("ShaderNodeMixRGB", label)
        node.blend_type = mode
        for value, socket in zip((factor, a, b), node.inputs):
            self.set(value, socket)
        return node.outputs[0]


def fabric_material(name, role, swatch, yarns, weave, density, gilt):
    mat = bpy.data.materials.new("Hanuman handloom · " + name)
    mat.use_nodes = True
    mat.diffuse_color = (.132, .022, .015, 1)
    graph = ClothNodes(mat)
    coord = graph.node("ShaderNodeTexCoord", "Fitted garment loop UV")
    uv = coord.outputs["UV"]
    textile_uv = graph.vector_scale(uv, (weave[0], weave[1] * density, 1), "ImageGen warp and weft scale")
    original = graph.image(swatch, textile_uv, "Packed madder-cloth swatch", "REPEAT")
    warp = graph.noise(graph.vector_scale(uv, (67, 7, 1), "Long warp yarns"), 1, 2, "Irregular warp slubs")
    weft = graph.noise(graph.vector_scale(uv, (8, 81, 1), "Crossing weft yarns"), 1, 2, "Irregular weft slubs")
    gross = graph.noise(coord.outputs["Object"], 8.3, 2, "Madder dye lot variation")
    spun = graph.mix("MULTIPLY", .82, warp, weft, "Crossed cotton thread variation")
    toning = graph.mix("MIX", gross, (.42, .36, .32, 1), (.97, .82, .69, 1), "Uneven aged red dye")
    dyed = graph.mix("MULTIPLY", .74, original, toning, "Dyed yarn base")
    base = graph.mix("MIX", .46, dyed, (.099, .019, .013, 1), "Preserve rich dyed red through folds")
    # The irregular low-contrast crossings read at full figure distance.
    yarn = graph.mix("MIX", spun, (.64, .62, .60, 1), (1.30, 1.24, 1.14, 1), "Warp-to-weft pigment difference")
    base = graph.mix("MULTIPLY", .74, base, yarn, "Readable weave at presentation distance")
    mask_uv = graph.vector_scale(uv, (.5, .5, 1), "Map existing 0–2 UV to unit ornament")
    crossing = graph.image(yarns, mask_uv, "Visible thread crossings", "REPEAT")
    warm_yarn = graph.mix("MIX", gross, (.111, .026, .015, 1), (.238, .073, .033, 1), "Faded exposed rust yarn")
    crossed = graph.mix("MIX", crossing, base, warm_yarn, "Alternating over-and-under yarn color")
    base = graph.mix("MIX", .53 if role == "body" else .35, base, crossed, "Woven crossover amount")
    height = graph.mix("ADD", .65, original, spun, "Swatch and slub thread relief")
    metallic = .025
    roughness = .79
    if role != "body":
        mask = graph.image(ornament(role), mask_uv, "Packed original brocade mask", "EXTEND")
        separate = graph.node("ShaderNodeSeparateColor", "Selvedge, motifs and binding threads")
        graph.links.new(mask, separate.inputs["Color"])
        dye, gilt_mask, binding = (separate.outputs[channel] for channel in ("Red", "Green", "Blue"))
        dark, light = (tuple(c * gilt for c in color) + (1,) for color in
                       ((.066, .026, .009), (.157, .059, .019)))
        tinted = graph.mix("MIX", spun, dark, light, "Madder-dyed ochre supplementary weft")
        base = graph.mix("MIX", dye, base, tinted, "Wide woven selvedge")
        gold = graph.mix("MIX", spun, (.226*gilt, .103*gilt, .026*gilt, 1),
                         (.459*gilt, .259*gilt, .089*gilt, 1), "Aged gold filament")
        base = graph.mix("MIX", gilt_mask, base, gold, "Woven gold lotus and creeper motifs")
        bound = graph.mix("MIX", spun, (.234*gilt, .119*gilt, .032*gilt, 1),
                          (.398*gilt, .226*gilt, .081*gilt, 1), "Paler silk edge binding")
        base = graph.mix("MIX", binding, base, bound, "Bound gold thread edging")
        height = graph.mix("ADD", .38, height, gilt_mask, "Raised embroidery in the fabric normal")
        metal = graph.node("ShaderNodeMath", "Small gold content inside the embroidery")
        metal.operation = "MULTIPLY_ADD"
        graph.set(gilt_mask, metal.inputs[0])
        metal.inputs[1].default_value = .23
        metal.inputs[2].default_value = .025
        metallic = metal.outputs[0]
        wear = graph.node("ShaderNodeMath", "Braided gold roughness")
        wear.operation = "MULTIPLY_ADD"
        graph.set(gilt_mask, wear.inputs[0])
        wear.inputs[1].default_value = -.19
        wear.inputs[2].default_value = .79
        roughness = wear.outputs[0]
    bump = graph.node("ShaderNodeBump", "Submillimeter interlaced threads")
    bump.inputs["Strength"].default_value = .37
    bump.inputs["Distance"].default_value = .00062
    graph.links.new(height, bump.inputs["Height"])
    cloth = graph.node("ShaderNodeBsdfPrincipled", "Fibrous cloth with worn gold filament")
    graph.set(base, cloth.inputs["Base Color"])
    graph.set(metallic, cloth.inputs["Metallic"])
    graph.set(roughness, cloth.inputs["Roughness"])
    cloth.inputs["Sheen Weight"].default_value = .12
    cloth.inputs["Sheen Tint"].default_value = (.29, .055, .032, 1)
    cloth.inputs["Sheen Roughness"].default_value = .84
    cloth.inputs["Specular IOR Level"].default_value = .25
    graph.links.new(bump.outputs["Normal"], cloth.inputs["Normal"])
    output = graph.node("ShaderNodeOutputMaterial", "Handwoven drapery surface")
    graph.links.new(cloth.outputs["BSDF"], output.inputs["Surface"])
    return mat


def repair_wrap(obj):
    """Preserve the 0–2 UV convention without interpolating across a full wrap."""
    layer = obj.data.uv_layers.active
    seams = 0
    for face in obj.data.polygons:
        coordinates = [layer.data[i].uv for i in face.loop_indices]
        if max(c.x for c in coordinates) - min(c.x for c in coordinates) > 1:
            for coordinate in coordinates:
                if coordinate.x < .25:
                    coordinate.x += 2
            seams += 1
    obj.data.update()
    return seams


def apply(scene, profile):
    """Bind the original brocade to the existing drapery and retain its geometry."""
    config = (profile or {}).get("textile", {})
    if not config.get("enabled", True):
        return {"enabled": False}
    if scene != bpy.context.scene:
        raise ValueError("Activate Hanuman's assembled wardrobe scene")
    density = float(config.get("weft_density", 1.0))
    gilt = float(config.get("gold_value", 1.0))
    if not .60 <= density <= 1.4 or not .55 <= gilt <= 1.30:
        raise ValueError("Textile density and gold value must stay in their reviewed ranges")
    swatch_path = (profile or {}).get("wardrobe", {}).get("cloth_texture") or SWATCH
    if not Path(swatch_path).is_absolute():
        swatch_path = ART / swatch_path
    swatch = bpy.data.images.load(str(Path(swatch_path).resolve()), check_existing=True)
    if not swatch.packed_file:
        swatch.pack()
    yarns = visible_yarns()
    report = {}
    for prefix, (name, role, weave, wrapped) in ROLES.items():
        parts = [obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith(prefix)]
        if not parts:
            raise ValueError(f"Run the fitted wardrobe stage before finishing {name}")
        material = fabric_material(name, role, swatch, yarns, weave, density, gilt)
        seams = 0
        for obj in parts:
            if obj.data.users > 1:
                obj.data = obj.data.copy()
            if wrapped:
                seams += repair_wrap(obj)
            obj.data.materials[0] = material
        report[role] = {"surfaces": len(parts), "repaired_uv_seam_faces": seams}
    return {"enabled": True, "materials": len(ROLES), "added_geometry": 0,
            "packed_ornament_masks": 4, "packed_weave_masks": 1, "swatch": swatch.name, "region": report}
