#!/usr/bin/env python3
"""Record the procedural fallback from an exact local FireRed Rust checkout.

No Cargo crates, game data, ROM, extracted textures or prebuilt executable are
needed. The Rust compiler runs the pinned constructor bodies against a local
geometry sink. The caller chooses where to keep the derived study manifest.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

COMMIT = "6a40d31175f5ce5ba15cdd74a141b1df9e1d0853"
PINS = {
    "presentation": "f2adec1b2522ee1a754834016a6d29ce5a407a5e194534b6cc6ba22dd0fa2e4e",
    "main": "8e870919e2b3d2f5f2d149a01eefa3cef97a4cea528f22543d045b137e57d0c8",
    "models": "07e5bea6cd4d8a67e7b5b7cb384070174e04a6d59f53bccba81e43d6dc8bf664",
}
CONSTRUCTORS = (
    "block",
    "tree",
    "window",
    "building",
    "furniture",
    "character",
    "spawn_map_blocks",
)
PANELS = (
    "wall",
    "roof",
    "lab_wall",
    "lab_roof",
    "window",
    "door",
    "fixture_ground",
    "kit_grass",
    "kit_path",
    "kit_stone",
    "kit_cliff",
)
CUBE_SIGNS = [
    (-1, -1, -1),
    (1, -1, -1),
    (1, 1, -1),
    (-1, 1, -1),
    (-1, -1, 1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, 1, 1),
]
CUBE_FACES = [
    [0, 3, 2, 1],
    [4, 5, 6, 7],
    [0, 1, 5, 4],
    [2, 3, 7, 6],
    [0, 4, 7, 3],
    [1, 2, 6, 5],
]
# Each map is a tiny synthetic fixture. '#' is a neutral terrain byte.
# Two rows/columns let the Rust constructor choose its alternate parity/edge.
FIELDS = {
    "kit_grass_ground": ("#", 0, False),
    "kit_path_ground": ("p", 0, False),
    "kit_stone_block": ("X", 0, False),
    "kit_cliff_ledge": ("L", 0, False),
    "field_ground_panel": ("#", 0, False),
    "field_lawn_light": ("#", 0, False),
    "field_lawn_alternate": ("##", 0, False),
    "field_path": ("p", 0, False),
    "field_water_wave": ("W", 0, False),
    "field_water_alternate": ("#W", 0, False),
    "field_rocks_pale": ("X", 0xE7, False),
    "field_rocks_dark": ("X", 0, False),
    "field_ledge": ("L", 0, False),
    "field_tall_grass": ("g", 0, False),
    "field_flowers": ("f", 0, False),
    "field_tree_tile": ("#", 0x0E, False),
    "interior_floor": ("#", 0, True),
    "interior_tall_wall": ("X", 0, True),
    "interior_cutaway_wall": ("#/X", 0, True),
}
# Width and depth are fixture parameters, not asserted original map dimensions.
SPECIMENS = {
    "foliage": ("tree", {"tree": (1, 1)}),
    "architecture_windows": ("window", {"window_front": (1, 1), "window_side": (1, 1)}),
    "architecture_buildings": (
        "building",
        dict.fromkeys(
            ["house", "house_door_mat", "house_panels", "lab", "lab_panels"], (4, 3)
        ),
    ),
    "furniture": (
        "furniture",
        {"table": (2, 2), "sofa": (2, 2), "bed": (2, 3), "plant": (1, 1)},
    ),
    "actors": ("character", {"player": (1, 1), "npc": (1, 1)}),
    "street": ("spawn_map_blocks", {"fence": (2, 1), "sign": (1, 1)}),
    "field_tiles": ("spawn_map_blocks", dict.fromkeys(FIELDS, (1, 1))),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def function(text, name):
    # Pinned files have module-level closing braces in column zero.
    pattern = rf"^fn {name}\(.*?^}}"
    found = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not found:
        raise ValueError(f"Missing pinned constructor {name}")
    return found.group(0)


def inputs(checkout):
    result = {}
    for name, expected in PINS.items():
        path = checkout / "rust-prototype" / "src" / (name + ".rs")
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError(
                f"Unexpected source bytes in {path}, expected the file from {COMMIT}"
            )
        result[name] = raw.decode()
    return result


def palette(text):
    colors = ast.literal_eval(
        re.search(r"let mut palette = (\[.*?\]);", text, re.DOTALL).group(1)
    )
    constants = re.findall(r"^const (\w+): usize = (\d+);$", text, re.MULTILINE)
    names = {int(i): name.lower() for name, i in constants}
    names.update(
        {i + len(colors): "missing_texture_" + k for i, k in enumerate(PANELS)}
    )
    values = {name: colors[i] for i, name in names.items() if i < len(colors)}
    # Preserve the geometry of texture panels using explicit absent-texture carrier slots.
    values.update({"missing_texture_" + name: (140, 140, 140) for name in PANELS})
    return names, values


def make_part(kind, material, hidden, vertices, faces):
    if any(not math.isfinite(v) for vertex in vertices for v in vertex):
        raise ValueError("Non-finite vertex")
    return {
        "kind": kind,
        "material": material,
        "hidden": hidden,
        "vertices": vertices,
        "faces": faces,
    }


def decode_call(line, materials):
    kind, index, hidden, *numbers = line.split()
    coords = list(map(float, numbers))
    material = materials[int(index)]
    if kind == "box":
        if len(coords) != 6 or min(coords[3:]) <= 0:
            raise ValueError("Invalid box")
        verts = [
            [coords[i] + p[i] * coords[3 + i] / 2 for i in range(3)] for p in CUBE_SIGNS
        ]
        faces = CUBE_FACES
    elif kind == "triangular_prism":
        if len(coords) != 10 or coords[-1] <= 0:
            raise ValueError("Invalid prism")
        x, y, z = coords[:3]
        verts = [
            [x + coords[3 + 2 * i], y + coords[4 + 2 * i], z + sign * coords[-1] / 2]
            for sign in (-1, 1)
            for i in range(3)
        ]
        faces = [[2, 1, 0], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]]
    elif kind == "quad":
        if len(coords) != 12:
            raise ValueError("Invalid panel")
        verts = [coords[i : i + 3] for i in range(0, 12, 3)]
        faces = [[0, 1, 2], [0, 2, 3]]
    else:
        raise ValueError(f"Unexpected Rust draw record {kind!r}")
    part = make_part(kind, material, bool(int(hidden)), verts, faces)
    if kind == "quad":
        # surface() in the hash-checked source emits this UV_0 order.
        part["uv0_by_vertex"] = [[0, 1], [1, 1], [1, 0], [0, 0]]
    return part


def preview_platform(models):
    # This is a parameter read from the pinned Rust preview setup rather than a
    # fake invocation of its cameras, lighting, image allocation, and UI systems.
    constructor = re.search(
        r"Cylinder::new\(([\d.]+), ([\d.]+)\).*?Color::srgb_u8\((\d+), (\d+), (\d+)\).*?origin - Vec3::Y \* ([\d.]+)",
        models,
        re.DOTALL,
    )
    radius, height, *rest = map(float, constructor.groups())
    r, g, b, offset = rest
    sides = 32  # CylinderMeshBuilder default in bevy_mesh 0.17.3.
    verts = [
        [
            radius * math.cos(i * math.tau / sides),
            y - offset,
            radius * math.sin(i * math.tau / sides),
        ]
        for y in (-height / 2, height / 2)
        for i in range(sides)
    ]
    faces = [list(range(sides)), list(reversed(range(sides, 2 * sides)))]
    for i in range(sides):
        j = (i + 1) % sides
        faces.append([i, i + sides, j + sides, j])
    return make_part("cylinder", "preview_platform", False, verts, faces), [
        int(r),
        int(g),
        int(b),
    ]


def record(checkout, rustc):
    sources = inputs(checkout)
    lock_hash = digest((checkout / "rust-prototype" / "Cargo.lock").read_bytes())
    if lock_hash != "4e9dce3cdf459c7114c16a2c8fadb96fcf4c059dd489d03f2f48186aa421b79a":
        raise ValueError("Unexpected Rust dependency lock")
    presentation = sources["presentation"]
    materials, palette_values = palette(presentation)
    declarations = re.findall(r"^const \w+: usize = \d+;$", presentation, re.MULTILINE)
    bodies = [function(presentation, name) for name in CONSTRUCTORS]
    bodies.append(function(sources["main"], "cell_position"))
    sink = Path(__file__).with_name("geometry_sink.rs")
    template = sink.read_text()
    compiled = template.replace(
        "// SOURCE_FUNCTIONS_GO_HERE", "\n".join(declarations + bodies)
    )
    version = subprocess.check_output([rustc, "--version"], text=True).strip()
    result = []
    with tempfile.TemporaryDirectory(prefix="firered-study-") as temp:
        code = Path(temp) / "record.rs"
        binary = Path(temp) / "record"
        code.write_text(compiled)
        subprocess.run(
            [rustc, "--edition=2021", "-C", "opt-level=0", code, "-o", binary],
            check=True,
        )
        for category, (constructor, specs) in SPECIMENS.items():
            for name, (w, d) in specs.items():
                tiles, mid, indoor = FIELDS.get(name, ("#", 0, False))
                out = subprocess.check_output(
                    [
                        binary,
                        name,
                        str(w),
                        str(d),
                        tiles,
                        str(mid),
                        "indoor" if indoor else "outdoor",
                    ],
                    text=True,
                )
                parts = [decode_call(line, materials) for line in out.splitlines()]
                if not parts:
                    raise ValueError(f"Constructor produced no geometry for {name}")
                result.append(
                    dict(
                        id=name,
                        category=category,
                        source_function=constructor,
                        fixture=dict(
                            width=w, depth=d, tiles=tiles, metatile=mid, indoor=indoor
                        ),
                        parts=parts,
                    )
                )
    platform, preview_color = preview_platform(sources["models"])
    palette_values["preview_platform"] = preview_color
    result.append(
        dict(
            id="preview_platform",
            category="display",
            source_function="models::setup",
            fixture={"mode": "read cylinder, color and offset parameters"},
            parts=[platform],
        )
    )
    return {
        "schema_version": 1,
        "axes": "Bevy Y-up",
        "unit": "tile",
        "source_commit": COMMIT,
        "source_sha256": PINS,
        "cargo_lock_sha256": lock_hash,
        "bevy_mesh_lock_version": "0.17.3",
        "rustc": version,
        "adapter_sha256": digest(Path(__file__).read_bytes()),
        "sink_sha256": digest(sink.read_bytes()),
        "compiled_source_sha256": digest(compiled.encode()),
        "materials": palette_values,
        "elements": result,
        "scope": "Untextured Rust fallback constructor outputs on synthetic fixtures. The default palette is taken before optional ROM-based overrides. External texture-panel slots are neutral carriers. Cylinder mesh reconstructed from native preview parameters. No terrain GLBs, character animation systems, battle stages or gameplay data are included.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rustc", default="rustc")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a fresh output path")
    report = record(args.checkout, args.rustc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as f:
        json.dump(report, f, separators=(",", ":"), allow_nan=False)
        f.write("\n")
    print(
        f"Recorded {len(report['elements'])} elements / {sum(len(e['parts']) for e in report['elements'])} parts."
    )


if __name__ == "__main__":
    main()
