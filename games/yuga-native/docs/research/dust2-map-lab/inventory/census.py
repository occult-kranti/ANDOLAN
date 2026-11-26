"""Inventory the two local Dust II editions and their jade passes. Outputs are aggregate evidence."""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import struct
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[3] / "tools/source-map-lab"
sys.path.insert(0, str(LAB / "qa"))
sys.path.insert(0, str(LAB / "radiant"))
from finish import LUMP_NAMES, SHADER, SURFACE  # noqa: E402
from finish import lumps as quake_lumps  # noqa: E402
from native import BLOCK, QUOTED, Bsp, texture_chain  # noqa: E402

UNNAMED = "(unassigned)"
SOLID_MODE = {
    0: "none",
    1: "BSP",
    2: "axis-aligned box",
    3: "oriented box",
    4: "oriented box yaw",
    5: "custom",
    6: "VPhysics",
}
SOURCE_BITS = {
    1: "solid",
    2: "window",
    8: "grate",
    128: "block LOS",
    32768: "area portal",
    65536: "player clip",
    131072: "NPC clip",
    0x8000000: "detail",
    0x10000000: "translucent",
}
SETTING_KEYS = {
    "TeamNum",
    "filterteam",
    "Negated",
    "StartDisabled",
    "StartOpen",
    "StartActive",
    "Solidity",
    "solidbsp",
    "spawnflags",
    "wait",
    "radius",
    "soundscape",
    "filtername",
    "vscripts",
    "thinkfunction",
    "physicsmode",
    "skin",
    "jaildoormode",
    "sounds",
    "dmg",
    "skyname",
    "enabledust",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def hash_file(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def csv_text(fields, rows):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(fields)
    writer.writerows(rows)
    return out.getvalue()


def parse_entities(blob):
    return [
        [(k.decode("cp1252"), v.decode("cp1252")) for k, v in QUOTED.findall(block[1])]
        for block in BLOCK.finditer(blob.rstrip(b"\0"))
    ]


def entity_census(entities):
    counts = Counter()
    keys = defaultdict(Counter)
    settings = defaultdict(lambda: defaultdict(Counter))
    output_counts = Counter()
    named = defaultdict(Counter)
    for pairs in entities:
        item = dict(pairs)
        cls = item["classname"]
        counts[cls] += 1
        for key, val in pairs:
            keys[cls][key] += 1
            if key in SETTING_KEYS:
                settings[cls][key][val] += 1
            if key.startswith("On"):
                fields = val.split("\x1b") if "\x1b" in val else val.split(",")
                require(len(fields) == 5, f"Unknown output format in {cls}")
                target, verb, argument, delay, fires = fields
                output_counts[
                    (
                        cls,
                        item.get("targetname", ""),
                        key,
                        target,
                        verb,
                        argument,
                        delay,
                        fires,
                    )
                ] += 1
        for key in (
            "target",
            "targetname",
            "filtername",
            "vscripts",
            "soundscape",
            "team",
            "jaildoormode",
            "NextKey",
        ):
            if item.get(key):
                named[key][item[key]] += 1
    mapped = {
        cls: {
            "count": n,
            "key_occurrences": dict(keys[cls]),
            "selected_settings": dict(settings[cls]),
        }
        for cls, n in counts.items()
    }
    return {
        "count": len(entities),
        "class_count": len(counts),
        "classes": mapped,
        "named_fields": {k: dict(v) for k, v in named.items()},
        "outputs": [
            dict(
                emitter=cls,
                emitter_name=name,
                event=ev,
                target=target,
                input=verb,
                argument=arg,
                delay_seconds=delay,
                fire_limit=fires,
                count=n,
            )
            for (cls, name, ev, target, verb, arg, delay, fires), n in sorted(
                output_counts.items()
            )
        ],
    }


def navigation(go, folder, original_nav, jade_nav, original_bsp, jade_bsp):
    a, b = original_nav.read_bytes(), jade_nav.read_bytes()
    require(
        a[:12] == b[:12] and a[16:] == b[16:],
        "More than NAV paired BSP byte count changed",
    )
    require(
        struct.unpack_from("<I", b, 12)[0] == jade_bsp.stat().st_size,
        "Jade NAV references a different BSP length",
    )
    raw = subprocess.check_output(
        [go, "run", "-mod=readonly", str(HERE / "navgraph.go"), str(original_nav)],
        cwd=folder,
    )
    nav = json.loads(raw)
    require(
        nav["bsp_bytes"] == original_bsp.stat().st_size,
        "Original NAV references a different BSP length",
    )
    areas = nav.pop("areas")
    names = {a["id"]: a["place"] or UNNAMED for a in areas}
    require(len(areas) == len(names), "Duplicate area ID")
    places = defaultdict(
        lambda: {
            "areas": 0,
            "hiding_records": 0,
            "encounter_records": 0,
            "links_within": 0,
            "links_out_to": Counter(),
            "lowest_corner_hu": math.inf,
            "highest_corner_hu": -math.inf,
        }
    )
    all_edges = Counter()
    for row in areas:
        name = names[row["id"]]
        record = places[name]
        record["areas"] += 1
        record["hiding_records"] += row["hiding"]
        record["encounter_records"] += row["encounters"]
        z = [row["bounds"][i] for i in (2, 5, 6, 7)]
        record["lowest_corner_hu"] = min(record["lowest_corner_hu"], *z)
        record["highest_corner_hu"] = max(record["highest_corner_hu"], *z)
        for neighbour in row["neighbours"]:
            other = names[neighbour]
            all_edges[(row["id"], neighbour)] += 1
            if name == other:
                record["links_within"] += 1
            else:
                record["links_out_to"][other] += 1
    for place in places.values():
        for k in ("lowest_corner_hu", "highest_corner_hu"):
            place[k] = round(place[k], 3)
    nav.update(
        areas=len(areas),
        places=dict(places),
        area_attribute_masks=dict(Counter(f"0x{row['flags']:08x}" for row in areas)),
        directed_links=sum(all_edges.values()),
        unique_directed_links=len(all_edges),
        unreciprocated_unique_links=sum((v, k) not in all_edges for k, v in all_edges),
        cross_label_links=sum(sum(p["links_out_to"].values()) for p in places.values()),
        directed_label_pairs=sum(len(p["links_out_to"]) for p in places.values()),
        original_nav_sha256=hashlib.sha256(a).hexdigest(),
        jade_nav_sha256=hashlib.sha256(b).hexdigest(),
        jade_bsp_size_word_only=True,
    )
    return nav, areas


class NavFloor:
    """Associate a prop origin with a NAV label only when close to a floor directly under its XY."""

    def __init__(self, areas):
        self.cells = defaultdict(list)
        for a in areas:
            x1, y1, _, x2, y2, *_ = a["bounds"]
            require(
                x2 > x1 and y2 > y1, "Unexpected NAV orientation or degenerate area"
            )
            for j in range(math.floor(y1 / 256), math.floor(y2 / 256) + 1):
                for i in range(math.floor(x1 / 256), math.floor(x2 / 256) + 1):
                    self.cells[i, j].append(a)

    def near(self, x, y, z):
        matches = []
        for a in self.cells[math.floor(x / 256), math.floor(y / 256)]:
            x1, y1, nw, x2, y2, se, ne, sw = a["bounds"]
            if not (x1 <= x <= x2 and y1 <= y <= y2):
                continue
            u, v = (x - x1) / (x2 - x1), (y - y1) / (y2 - y1)
            floor = (1 - v) * ((1 - u) * nw + u * ne) + v * ((1 - u) * sw + u * se)
            dist = abs(z - floor)
            if dist <= 96:
                matches.append((dist, a["place"] or UNNAMED))
        if not matches:
            return "(outside tolerance)"
        matches.sort()
        near = {name for distance, name in matches if distance <= matches[0][0] + 0.5}
        return near.pop() if len(near) == 1 else "(ambiguous)"


def prop_inventory(bsp, areas):
    game = bsp.get(35)
    (count,) = struct.unpack_from("<I", game)
    subs = list(struct.iter_unpack("<4sHHii", game[4 : 4 + 16 * count]))
    _, flags, version, off, size = next(s for s in subs if s[0] in (b"sprp", b"prps"))
    require(flags == 0 and version == 11, "Expected native CS:GO v11 static props")
    (slots,) = struct.unpack_from("<I", bsp.data, off)
    pointer = off + 4
    paths = [
        bsp.data[i : i + 128]
        .split(b"\0")[0]
        .decode("cp1252")
        .replace("\\", "/")
        .lower()
        for i in range(pointer, pointer + slots * 128, 128)
    ]
    pointer += slots * 128
    (leaves,) = struct.unpack_from("<I", bsp.data, pointer)
    pointer += 4 + leaves * 2
    (placements,) = struct.unpack_from("<I", bsp.data, pointer)
    pointer += 4
    require(pointer + placements * 80 == off + size, "Unexpected static prop stride")
    geo = NavFloor(areas)
    models = defaultdict(
        lambda: {"count": 0, "solidity": Counter(), "skins": Counter()}
    )
    local_families = defaultdict(Counter)
    sol = Counter()
    for i in range(placements):
        at = pointer + i * 80
        xyz = struct.unpack_from("<3f", bsp.data, at)
        (index,) = struct.unpack_from("<H", bsp.data, at + 24)
        prop = paths[index]
        solid = bsp.data[at + 30]
        (skin,) = struct.unpack_from("<i", bsp.data, at + 32)
        models[prop]["count"] += 1
        models[prop]["solidity"][solid] += 1
        models[prop]["skins"][skin] += 1
        sol[solid] += 1
        family = prop.rsplit("/", 1)[0]
        local_families[geo.near(*xyz)][family] += 1
    _, expected = bsp.static_props()
    require(
        {p: r["count"] for p, r in models.items()} == expected,
        "Static dictionary disagrees with native audit",
    )
    rows = [
        (
            p,
            m["count"],
            p.rsplit("/", 1)[0],
            "; ".join(
                f"{SOLID_MODE.get(k, k)}={v}" for k, v in sorted(m["solidity"].items())
            ),
            "; ".join(f"{k}={v}" for k, v in sorted(m["skins"].items())),
        )
        for p, m in sorted(models.items())
    ]
    return {
        "dictionary_slots": slots,
        "normalized_used_models": len(models),
        "placements": placements,
        "placements_by_solidity": {
            SOLID_MODE.get(k, str(k)): v for k, v in sol.items()
        },
        "place_match_method": "Prop origin inside NAV rectangle XY, bilinear corner floor within 96 Source units, closest floor wins. Different labels within 0.5 units of its error remain ambiguous. This association does not assign collision or guarantee visibility.",
        "origin_families_by_nav_label": {k: dict(v) for k, v in local_families.items()},
    }, csv_text(
        [
            "native_model",
            "placements",
            "source_directory",
            "compiled_solidity_and_counts",
            "compiled_skin_and_counts",
        ],
        rows,
    )


def source_materials(bsp):
    names = bsp.texture_names()
    lookup = [names[texture_chain(bsp, i)[1]] for i in range(bsp.count(6, 72))]
    per = {n: Counter() for n in names}
    surface_flags = defaultdict(Counter)
    for slot, name in enumerate(lookup):
        (flags,) = struct.unpack_from("<I", bsp.get(6), slot * 72 + 64)
        per[name]["texture_info_slots"] += 1
        surface_flags[name][flags] += 1
    for i in range(bsp.count(7, 56)):
        idx, disp = struct.unpack_from("<hh", bsp.get(7), i * 56 + 10)
        require(0 <= idx < len(lookup), "Unsupported face material index")
        row = per[lookup[idx]]
        row["faces"] += 1
        if disp >= 0:
            row["dispfaces"] += 1
    for i in range(bsp.count(19, 8)):
        (idx,) = struct.unpack_from("<h", bsp.get(19), i * 8 + 2)
        if idx >= 0:
            per[lookup[idx]]["brushsides"] += 1
    for i in range(bsp.count(45, 352)):
        (idx,) = struct.unpack_from("<h", bsp.get(45), i * 352 + 4)
        require(0 <= idx < len(lookup), "Unsupported overlay material index")
        per[lookup[idx]]["overlays"] += 1
    fields = ["faces", "dispfaces", "brushsides", "overlays", "texture_info_slots"]
    return csv_text(
        ["native_material", *fields, "surface_flags_and_slot_counts"],
        [
            (
                n,
                *(p[f] for f in fields),
                "; ".join(
                    f"0x{flag:08x}={count}"
                    for flag, count in sorted(surface_flags[n].items())
                ),
            )
            for n, p in sorted(per.items())
        ],
    )


def source_inventory(before, after, areas):
    with Bsp(before) as bsp, Bsp(after) as jade:
        native = bsp.inventory()
        pairs = parse_entities(bytes(bsp.get(0)))
        entities = entity_census(pairs)
        require(
            native["entities"]["class_counts"]
            == {k: v["count"] for k, v in entities["classes"].items()},
            "Entity parse disagreement",
        )
        structural = Counter(
            flags & 0xFFFFFFFF
            for _, _, flags in struct.iter_unpack("<iii", bsp.get(18))
        )
        brush_masks = {f"0x{flags:08x}": n for flags, n in structural.items()}
        brushes = [dict(p) for p in pairs if dict(p)["classname"] == "func_brush"]
        entity_summary = {
            "brush_names": dict(
                Counter(e.get("targetname", "(unnamed)") for e in brushes)
            ),
            "initial_brush_disabled": dict(
                Counter(e.get("StartDisabled", "(unset)") for e in brushes)
            ),
            "dynamic_model_paths": dict(
                Counter(
                    dict(p)["model"]
                    for p in pairs
                    if dict(p).get("model", "").lower().endswith(".mdl")
                )
            ),
        }
        changed = [i for i in range(64) if bsp.raw(i) != jade.raw(i)]
        face_changes = []
        for lump in (7, 58):
            fa, fb = bytes(bsp.get(lump)), bytes(jade.get(lump))
            require(len(fa) == len(fb), "Jade face count changed")
            different = []
            for i in range(0, len(fa), 56):
                if fa[i : i + 56] != fb[i : i + 56]:
                    require(
                        fa[i : i + 10] == fb[i : i + 10]
                        and fa[i + 12 : i + 56] == fb[i + 12 : i + 56],
                        "A nonmaterial face field changed",
                    )
                    different.append(i // 56)
            face_changes.append(different)
        require(
            face_changes[0] == face_changes[1], "HDR and LDR restyled different faces"
        )
        props, prop_csv = prop_inventory(bsp, areas)
        metrics = dict(native["record_counts"])
        metrics.update(
            visibility_clusters=struct.unpack_from("<i", bsp.get(4))[0],
            leaves=bsp.count(10, 32),
            visibility_areas=bsp.count(20, 8),
            area_portal_records=bsp.count(21, 12),
            cubemap_capture_points=bsp.count(42, 16),
        )
        return (
            {
                "format": f"VBSP {bsp.version} rev. {bsp.revision}",
                "original_sha256": native["sha256"],
                "jade_sha256": hash_file(after),
                "records": metrics,
                "brush_content_masks": brush_masks,
                "brushes_with_selected_content_flag": {
                    name: sum(n for flags, n in structural.items() if flags & bit)
                    for bit, name in SOURCE_BITS.items()
                },
                "displacement": native["displacement"],
                "pak_by_extension": native["pak_entries_by_extension"],
                "brush_models": native["compiled_model_space"],
                "entities": entities,
                "entity_features": entity_summary,
                "static_props": props,
                "materials_count": len(bsp.texture_names()),
                "jade": {
                    "changed_lumps": changed,
                    "byte_identical_lumps": 64 - len(changed),
                    "faces_reassigned_in_both_lighting_tables": len(face_changes[0]),
                },
            },
            prop_csv,
            source_materials(bsp),
        )


PLANE_TEXTURE = re.compile(r"^\([^)]*\)\s*\([^)]*\)\s*\([^)]*\)\s+(\S+)")
MAP_FIELD = re.compile(r'^"((?:\\.|[^"\\])*)"\s+"((?:\\.|[^"\\])*)"$')


def radiant_map(path):
    entities = []
    geometry = defaultdict(Counter)
    materials = defaultdict(Counter)
    targets = Counter()
    depth = 0
    attrs = []
    per_entity = Counter()
    for number, line in enumerate(path.read_text(encoding="cp1252").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line == "{":
            if depth == 0:
                attrs = []
                per_entity = Counter()
            elif depth == 1:
                material_sides = 0
                patch = False
                expect_shader = False
            depth += 1
            continue
        if line == "}":
            if depth == 2:
                if patch:
                    require(
                        not expect_shader and material_sides == 1,
                        f"Incomplete patch near line {number}",
                    )
                else:
                    require(
                        material_sides >= 4,
                        f"Incomplete convex brush near line {number}",
                    )
                per_entity["patches" if patch else "plane_brushes"] += 1
            elif depth == 1:
                fields = dict(attrs)
                entities.append(attrs)
                geometry[fields["classname"]].update(per_entity)
                if "target" in fields:
                    targets[(fields["classname"], fields["target"])] += 1
            depth -= 1
            require(depth >= 0, "Unbalanced Radiant blocks")
            continue
        if depth == 1:
            field = MAP_FIELD.fullmatch(line)
            require(field is not None, f"Unknown Radiant entity field on line {number}")
            attrs.append(field.groups())
        elif depth == 2 and line == "patchDef2":
            patch = expect_shader = True
        elif depth == 3 and expect_shader:
            require(not line.startswith("("), "Missing patch shader")
            materials[line]["source_patches"] += 1
            material_sides += 1
            expect_shader = False
        elif depth == 2:
            plane = PLANE_TEXTURE.match(line)
            require(plane is not None, f"Unexpected Radiant primitive on line {number}")
            materials[plane[1]]["source_plane_sides"] += 1
            material_sides += 1
    require(
        depth == 0 and any(dict(p)["classname"] == "worldspawn" for p in entities),
        "Incomplete Radiant source",
    )
    return entities, geometry, materials, targets


def radiant_inventory(folder):
    base = "q3dust2-jb-beta6"
    map_path = folder / (base + ".map")
    entities, geometry, materials, targets = radiant_map(map_path)
    rows = [dict(p) for p in entities]
    packages = {
        edition: folder / f"{base}-{edition}.pk3" for edition in ("original", "jade")
    }
    with ZipFile(packages["original"]) as za, ZipFile(packages["jade"]) as zb:
        name = "maps/" + base + ".bsp"
        a = za.read(name)
        b = zb.read(name)
        mapinfo = za.read("maps/" + base + ".mapinfo").decode("ascii")
    original, _ = quake_lumps(a)
    jade, _ = quake_lumps(b)
    changed = [
        LUMP_NAMES[i]
        for i, (before, after) in enumerate(zip(original, jade, strict=True))
        if before != after
    ]
    require(
        set(changed) == {"shaders", "draw_surfaces"},
        "The jade IBSP changed structural geometry or entities",
    )
    compiled = entity_census(parse_entities(original[0]))
    shaders = []
    shader_flags = defaultdict(Counter)
    for name, surface_flags, content_flags in SHADER.iter_unpack(original[1]):
        label = name.split(b"\0")[0].decode("ascii").removeprefix("textures/")
        shaders.append(label)
        materials[label]["native_shader_slots"] += 1
        shader_flags[label][surface_flags & 0xFFFFFFFF, content_flags & 0xFFFFFFFF] += 1
    surfaces = Counter()
    altered = 0
    for before, after in zip(
        SURFACE.iter_unpack(original[13]), SURFACE.iter_unpack(jade[13]), strict=True
    ):
        require(
            before[1:] == after[1:],
            "Surface fields changed beyond native shader assignment",
        )
        label = shaders[before[0]]
        materials[label]["compiled_draw_surfaces"] += 1
        surfaces[before[2]] += 1
        if before[0] != after[0]:
            altered += 1
            materials[label]["jade_reassignments"] += 1
    for _, _, material in struct.iter_unpack("<iii", original[8]):
        materials[shaders[material]]["compiled_brushes"] += 1
    for _, material in struct.iter_unpack("<ii", original[9]):
        require(
            0 <= material < len(shaders), "Unsupported IBSP brush-side shader index"
        )
        materials[shaders[material]]["compiled_brush_sides"] += 1
    totals = sum((Counter(v) for v in geometry.values()), Counter())
    fields = [
        "source_plane_sides",
        "source_patches",
        "native_shader_slots",
        "compiled_draw_surfaces",
        "compiled_brushes",
        "compiled_brush_sides",
        "jade_reassignments",
    ]
    shader_csv = csv_text(
        ["material", *fields, "surface_and_content_flags_and_slot_counts"],
        [
            (
                s,
                *(r[k] for k in fields),
                "; ".join(
                    f"0x{surface:08x}/0x{content:08x}={count}"
                    for (surface, content), count in sorted(shader_flags[s].items())
                ),
            )
            for s, r in sorted(materials.items())
        ],
    )
    target_names = Counter(r["targetname"] for r in rows if "targetname" in r)
    return {
        "source_map_sha256": hash_file(map_path),
        "pack_sha256": {k: hash_file(v) for k, v in packages.items()},
        "source_entities": entity_census(entities),
        "source_shapes": dict(totals),
        "source_shapes_by_class": {k: dict(v) for k, v in geometry.items() if v},
        "target_links": [
            {
                "from_class": cls,
                "to_name": name,
                "source_entities": v,
                "target_entities": target_names[name],
            }
            for (cls, name), v in sorted(targets.items())
        ],
        "declared_modes": {
            s.split()[1]: s.split()[2:]
            for s in mapinfo.splitlines()
            if s.startswith("type ")
        },
        "external_model_references": dict(
            Counter(r["model"] for r in rows if "model" in r)
        ),
        "compiled": {
            "format": "IBSP 46",
            "original_bsp_sha256": hashlib.sha256(a).hexdigest(),
            "jade_bsp_sha256": hashlib.sha256(b).hexdigest(),
            "entities": compiled,
            "models": len(original[7]) // 40,
            "collision_brushes": len(original[8]) // 12,
            "brush_sides": len(original[9]) // 8,
            "vertices": len(original[10]) // 44,
            "visibility_clusters": struct.unpack_from("<i", original[16])[0],
            "draw_surfaces": sum(surfaces.values()),
            "surface_counts_by_native_type": dict(surfaces),
            "base_shaders": len(shaders),
            "jade_changed_lumps": changed,
            "jade_changed_surfaces": altered,
        },
    }, shader_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "local_package",
        type=Path,
        help="Directory containing native/ and radiant/ from the map lab",
    )
    parser.add_argument(
        "--go", default="go", help="Go compiler executable (version 1.20 or newer)"
    )
    parser.add_argument("--output", type=Path, default=HERE)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare in memory with the existing published inventories",
    )
    args = parser.parse_args()
    root = args.local_package.resolve()
    originals = root / "native/original/csgo/maps/de_dust2.bsp"
    edited = root / "native/jade/csgo/maps/de_dust2.bsp"
    nav, areas = navigation(
        args.go,
        LAB / "nav",
        originals.with_suffix(".nav"),
        edited.with_suffix(".nav"),
        originals,
        edited,
    )
    source, props, materials = source_inventory(originals, edited, areas)
    radiant, shaders = radiant_inventory(root / "radiant")
    require(
        sum(r["areas"] for r in nav["places"].values()) == nav["areas"],
        "Incomplete NAV register",
    )
    results = {
        "source.json": json_text(source),
        "source-props.csv": props,
        "source-materials.csv": materials,
        "nav.json": json_text(nav),
        "hanzo.json": json_text(radiant),
        "hanzo-materials.csv": shaders,
    }
    if not args.check:
        args.output.mkdir(parents=True, exist_ok=True)
    for name, text in results.items():
        dest = args.output / name
        if args.check:
            require(dest.read_bytes() == text.encode(), f"Regenerate {name}")
        else:
            dest.write_bytes(text.encode())
    print(
        f"Source: {source['entities']['count']} entities, {source['static_props']['placements']} prop placements, {nav['areas']} NAV areas and {nav['directed_links']} connections."
    )
    print(
        f"Hanzo: {radiant['source_entities']['count']} source entities and {radiant['compiled']['draw_surfaces']} compiled draw surfaces. {len(results)} inventories checked."
    )


if __name__ == "__main__":
    main()
