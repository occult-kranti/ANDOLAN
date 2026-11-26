"""Apply a floor-only material change to a freshly compiled Quake 3 IBSP v46."""
import hashlib
import io
import re
import struct
from collections import Counter
from pathlib import PurePosixPath

from PIL import Image, ImageOps

# Authored floor groups. Walls, trim tops, box lids, scenery and water retain their materials.
FLOORS = {
    "textures/dust-nex_floor/floor_brick1",
    "textures/dust-nex_floor/floor_brick2",
    "textures/dust-nex_floor/floor_jail",
    "textures/dust-nex_floor/floor_jail2",
    "textures/dust-nex_concrete/concrete_ground",
    "textures/dust-nex_nature/grass_ground",
    "textures/dust-nex_misc/dust-eX_floor_mtl_grate_01",
}
MIN_UP = 0.65  # All vertices must be on a walkable face (about 49 degrees or shallower).
LUMP_NAMES = (
    "entities", "shaders", "planes", "nodes", "leaves", "leaf_surfaces", "leaf_brushes",
    "models", "brushes", "brush_sides", "draw_vertices", "draw_indices", "fogs",
    "draw_surfaces", "lightmaps", "light_grid", "visibility",
)
SHADER = struct.Struct("<64sii")
VERTEX = struct.Struct("<10f4B")
SURFACE = struct.Struct("<12i12f2i")
MATERIAL = re.compile(r"^(textures/[^\s]+)\s*\n(\{.*?^\})", re.MULTILINE | re.DOTALL)
JADE_BLACK = (2, 9, 7)
JADE_WHITE = (66, 219, 162)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lumps(data):
    if len(data) < 144 or data[:8] != b"IBSP\x2e\0\0\0":
        raise ValueError("Expected a Quake 3 little-endian IBSP version 46")
    spans = list(struct.iter_unpack("<II", data[8:144]))
    if any(start + size > len(data) for start, size in spans):
        raise ValueError("BSP directory points outside file")
    return [data[start:start + size] for start, size in spans], spans


def shader_names(shader_lump):
    return [name.rstrip(b"\0").decode("ascii") for name, _, _ in SHADER.iter_unpack(shader_lump)]


def shader_key(name):
    return "textures/yuga_dust_lab/" + PurePosixPath(name).name.lower()


def tint_diffuse(source, prefix):
    filenames = {name.lower(): name for name in source.namelist()}
    for suffix in (".tga", ".jpg", ".png"):
        filename = filenames.get((prefix + suffix).lower())
        if filename:
            with Image.open(io.BytesIO(source.read(filename))) as original:
                rgba = original.convert("RGBA")
            color = ImageOps.colorize(ImageOps.grayscale(rgba), JADE_BLACK, JADE_WHITE)
            color.putalpha(rgba.getchannel("A"))
            out = io.BytesIO()
            color.save(out, format="TGA", compression="tga_rle")
            return out.getvalue()
    raise ValueError(f"Missing diffuse image for {prefix}")


def ground_resources(source):
    script = source.read("scripts/dust-nex.shader").decode("ascii")
    blocks = dict(MATERIAL.findall(script))
    changed_blocks, resources = [], {}
    for original in sorted(FLOORS):
        destination = shader_key(original)
        # Keep the author's lightmap stage, shadows, depth and alpha test intact.
        block, matches = re.subn(re.escape(original) + r"\.(?:jpg|tga|png)\b",
                                 destination + ".tga", blocks[original], flags=re.IGNORECASE)
        if matches < 2:
            raise ValueError(f"Missing preview or diffuse stage in {original}")
        changed_blocks.append(destination + "\n" + block)
        resources[destination + ".tga"] = tint_diffuse(source, original)
    resources["scripts/yuga_dust_lab.shader"] = ("\n\n".join(changed_blocks) + "\n").encode()
    return resources


def finish(baseline):
    original, directory = lumps(baseline)
    shader_data = bytearray(original[1])
    names = shader_names(shader_data)
    draw_data = bytearray(original[13])
    vertices = list(VERTEX.iter_unpack(original[10]))
    changes, original_counts = Counter(), Counter()
    used, changed_indices = {}, []
    for index, surface in enumerate(SURFACE.iter_unpack(original[13])):
        shader, first, count = surface[0], surface[3], surface[4]
        name = names[shader]
        if name not in FLOORS:
            continue
        original_counts[name] += 1
        if not count or min(vertices[i][9] for i in range(first, first + count)) < MIN_UP:
            continue
        if shader not in used:
            _, flags, contents = SHADER.unpack_from(original[1], shader * SHADER.size)
            used[shader] = len(shader_data) // SHADER.size
            shader_data.extend(SHADER.pack(shader_key(name).encode(), flags, contents))
        struct.pack_into("<I", draw_data, index * SURFACE.size, used[shader])
        changes[name] += 1
        changed_indices.append(index)
    if set(changes) != FLOORS:
        raise ValueError(f"Expected all seven authored floor materials: {sorted(changes)}")

    # Relocate only the shader table. Every other directory entry and the original offsets survive.
    jade = bytearray(baseline)
    start, size = directory[13]
    jade[start:start + size] = draw_data
    jade.extend(b"\0" * (-len(jade) % 4))
    struct.pack_into("<II", jade, 16, len(jade), len(shader_data))
    jade.extend(shader_data)
    edited, _ = lumps(jade)
    stable = {name: sha(original[i]) for i, name in enumerate(LUMP_NAMES)
              if original[i] == edited[i]}
    if len(stable) != 15 or edited[1][:len(original[1])] != original[1]:
        raise ValueError("Unexpected changes outside the two material-bearing lumps")
    for i in range(len(original[13]) // SURFACE.size):
        off = i * SURFACE.size + 4
        if original[13][off:off + SURFACE.size - 4] != edited[13][off:off + SURFACE.size - 4]:
            raise ValueError(f"Surface {i} changed beyond its material ID")
    expected = set(changed_indices)
    actual = {i for i, (a, b) in enumerate(zip(SURFACE.iter_unpack(original[13]),
                                               SURFACE.iter_unpack(edited[13]))) if a[0] != b[0]}
    if actual != expected:
        raise ValueError("Edited draw surfaces disagree with the audited ground selection")
    report = {
        "format": "IBSP 46", "base_sha256": sha(baseline), "jade_sha256": sha(jade),
        "draw_surfaces": len(original[13]) // SURFACE.size, "vertices": len(vertices),
        "explicitly_indexed_triangles": len(original[11]) // 12,
        "curved_patch_surfaces": sum(s[2] == 2 for s in SURFACE.iter_unpack(original[13])),
        "models": len(original[7]) // 40, "collision_brushes": len(original[8]) // 12,
        "visibility_clusters": struct.unpack_from("<i", original[16])[0],
        "changed_surfaces": len(changed_indices), "changed_materials": dict(sorted(changes.items())),
        "all_orientations_by_ground_material": dict(sorted(original_counts.items())),
        "changed_surface_indices": changed_indices, "unchanged_lump_sha256": stable,
        "minimum_up_normal": MIN_UP, "jade_luminance_endpoints_srgb": [JADE_BLACK, JADE_WHITE],
    }
    return bytes(jade), report
