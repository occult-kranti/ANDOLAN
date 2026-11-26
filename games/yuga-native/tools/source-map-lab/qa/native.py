"""Inventory and compare CS:GO v21 BSPs without loading the game or running map scripts."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import io
import json
import lzma
import mmap
from pathlib import Path
import re
import struct
from zipfile import ZipFile


NAMES = {
    0: "entities",
    1: "planes",
    2: "texdata",
    3: "vertices",
    4: "visibility",
    5: "nodes",
    6: "texinfo",
    7: "faces",
    8: "lighting",
    9: "occlusion",
    10: "leaves",
    12: "edges",
    13: "surfedges",
    14: "models",
    18: "brushes",
    19: "brushsides",
    26: "dispinfo",
    27: "original_faces",
    29: "physics_collision",
    33: "dispverts",
    35: "game",
    40: "pak",
    43: "texture_names",
    44: "texture_table",
    45: "overlays",
    48: "disptris",
    53: "lighting_hdr",
    55: "worldlights_hdr",
    58: "faces_hdr",
    59: "map_flags",
}
MUTABLE = {2, 6, 7, 40, 43, 44, 58}
QUOTED = re.compile(rb'"((?:\\.|[^"\\])*)"\s*"((?:\\.|[^"\\])*)"')
BLOCK = re.compile(rb'\{((?:"(?:\\.|[^"\\])*"|[^"{}])*)\}', re.DOTALL)
HEADER = struct.Struct("<iii4s")
MODEL = struct.Struct("<9f3i")


def insist(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def chunks(data, width):
    insist(len(data) % width == 0, f"Unexpected {width}-byte record tail")
    for i in range(0, len(data), width):
        yield data[i : i + width]


def normal(name):
    return name.replace("\\", "/").lower()


def cstring(data):
    return bytes(data).split(b"\0", 1)[0].decode("cp1252")


@dataclass(frozen=True)
class Lump:
    offset: int
    size: int
    version: int
    fourcc: bytes


class SliceReader(io.RawIOBase):
    """Allow zipfile to seek the pak central directory without making a 294 MB copy."""

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        pos = (0, self.pos, len(self.data))[whence] + offset
        if pos < 0:
            raise OSError("Negative seek")
        self.pos = pos
        return pos

    def read(self, count=-1):
        start = self.pos
        self.pos = len(self.data) if count < 0 else min(start + count, len(self.data))
        return bytes(self.data[start : self.pos])


class Bsp:
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open("rb")
        self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        insist(self.data[:4] == b"VBSP", "Expected a Source VBSP")
        (self.version,) = struct.unpack_from("<i", self.data, 4)
        insist(
            self.version == 21, "This independent layout reader supports PC CS:GO v21"
        )
        (self.revision,) = struct.unpack_from("<i", self.data, 1032)
        self.lumps = [
            Lump(*HEADER.unpack_from(self.data, 8 + i * 16)) for i in range(64)
        ]
        self.decoded = {}
        for i, r in enumerate(self.lumps):
            insist(
                0 <= r.offset <= len(self.data)
                and 0 <= r.size <= len(self.data) - r.offset,
                f"Lump {i} is outside the file",
            )

    def close(self):
        self.data.close()
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        # A rejected input can leave a memoryview alive in the traceback. Keep
        # the check failure visible and let that last view release its mapping.
        if exc_type is not None:
            self.file.close()
        else:
            self.close()

    def raw(self, index):
        lump = self.lumps[index]
        return memoryview(self.data)[lump.offset : lump.offset + lump.size]

    def get(self, index):
        raw = self.raw(index)
        if raw[:4] != b"LZMA":
            return raw
        if index not in self.decoded:
            expected, length = struct.unpack_from("<II", raw, 4)
            insist(length + 17 <= len(raw), f"Bad compressed lump {index}")
            body = (
                bytes(raw[12:17])
                + struct.pack("<Q", expected)
                + bytes(raw[17 : 17 + length])
            )
            result = lzma.decompress(body, format=lzma.FORMAT_ALONE)
            insist(len(result) == expected, f"Length mismatch on lump {index}")
            self.decoded[index] = result
        return memoryview(self.decoded[index])

    def count(self, index, stride):
        n = len(self.get(index))
        insist(n % stride == 0, f"Lump {index} is not made of {stride}-byte records")
        return n // stride

    def archive(self):
        return ZipFile(SliceReader(self.get(40)))

    def texture_names(self):
        names = bytes(self.get(43))
        offsets = (v for (v,) in struct.iter_unpack("<i", self.get(44)))
        table = []
        for at in offsets:
            end = names.find(b"\0", at)
            insist(0 <= at <= end, "Invalid texture string offset")
            table.append(names[at:end].decode("cp1252"))
        return table

    def entities(self):
        result = []
        for block in BLOCK.finditer(bytes(self.get(0)).strip(b"\0")):
            fields = {
                k.decode("cp1252"): v.decode("cp1252")
                for k, v in QUOTED.findall(block.group(1))
            }
            if "classname" in fields:
                result.append(fields)
        insist(
            sum(v["classname"] == "worldspawn" for v in result) == 1,
            "Missing or duplicate worldspawn",
        )
        return result

    def models(self):
        return list(MODEL.iter_unpack(self.get(14)))

    def static_props(self):
        game = self.get(35)
        (n,) = struct.unpack_from("<I", game)
        descriptors = [
            struct.unpack_from("<4sHHii", game, 4 + 16 * i) for i in range(n)
        ]
        for kind, flags, version, offset, length in descriptors:
            if kind not in (b"prps", b"sprp"):
                continue
            insist(
                not flags and version == 11, "Expected uncompressed static props v11"
            )
            (count,) = struct.unpack_from("<i", self.data, offset)
            at = offset + 4
            paths = [
                normal(cstring(self.data[at + 128 * i : at + 128 * i + 128]))
                for i in range(count)
            ]
            at += 128 * count
            (leaves,) = struct.unpack_from("<i", self.data, at)
            at += 4 + 2 * leaves
            (total,) = struct.unpack_from("<i", self.data, at)
            at += 4
            insist(length + offset - at == 80 * total, "Bad CS:GO statics v11 stride")
            used = Counter()
            for i in range(total):
                (index,) = struct.unpack_from("<H", self.data, at + i * 80 + 24)
                insist(index < len(paths), "Bad static prop dictionary reference")
                used[paths[index]] += 1
            return count, used
        return 0, Counter()

    def inventory(self):
        entities = self.entities()
        classes = Counter(r["classname"] for r in entities)
        models = self.models()
        locations = []
        for v in entities:
            if v["classname"] not in (
                "func_bomb_target",
                "info_player_terrorist",
                "info_player_counterterrorist",
                "sky_camera",
            ):
                continue
            item = {
                "class": v["classname"],
                "entity": v.get("hammerid"),
                "name": v.get("targetname", ""),
            }
            if v.get("origin"):
                item["origin_source_units"] = [float(x) for x in v["origin"].split()]
            if v.get("model", "").startswith("*"):
                i = int(v["model"][1:])
                row = models[i]
                item.update(
                    brush_model=i, local_bounds_source_units=[row[:3], row[3:6]]
                )
            locations.append(item)
        count, used = self.static_props()
        with self.archive() as z:
            members = {normal(x.filename) for x in z.infolist()}
            formats = Counter(n.rsplit(".", 1)[-1] for n in members)
            embedded = {
                p
                for p in used
                if p in members
                and p[:-4] + ".vvd" in members
                and p[:-4] + ".dx90.vtx" in members
            }
            external = {k: v for k, v in used.items() if k not in embedded}
        disp = self.get(26)
        powers = Counter(struct.unpack_from("<i", r, 20)[0] for r in chunks(disp, 176))
        face_data = self.get(7) if self.lumps[7].size else self.get(58)
        numface = len(face_data) // 56
        spans = [(row[10], row[11]) for row in models]
        covered = {i for start, size in spans for i in range(start, start + size)}
        insist(
            covered == set(range(numface)),
            "Brush-model ranges miss or exceed encoded faces",
        )
        vertices = [[(float("inf"))] * 3, [-float("inf")] * 3]
        for vert in struct.iter_unpack("<3f", self.get(3)):
            for k, i in enumerate(vert):
                vertices[0][k] = min(vertices[0][k], i)
                vertices[1][k] = max(vertices[1][k], i)
        layouts = [
            (1, 20),
            (2, 32),
            (3, 12),
            (6, 72),
            (7, 56),
            (12, 4),
            (13, 4),
            (14, 48),
            (18, 12),
            (19, 8),
            (26, 176),
            (27, 56),
            (33, 20),
            (45, 352),
            (48, 2),
            (58, 56),
        ]
        return {
            "schema": "yuga.dust2.source-inventory.v1",
            "file": self.path.name,
            "bytes": len(self.data),
            "sha256": digest(self.data),
            "bsp_version": self.version,
            "map_revision": self.revision,
            "record_counts": {NAMES[i]: self.count(i, k) for i, k in layouts},
            "compiled_model_space": {
                "model_count": len(models),
                "world_face_count": spans[0][1],
                "entity_model_face_count": sum(n for _, n in spans[1:]),
                "world_model_bounds_source_units": [models[0][:3], models[0][3:6]],
                "all_base_vertex_bounds_source_units": vertices,
            },
            "displacement": {
                "powers": dict(sorted(powers.items())),
                "nominal_displacement_triangles": sum(
                    n * 2 * (2**p) ** 2 for p, n in powers.items()
                ),
                "unique_grids": sum(powers.values()),
            },
            "entities": {
                "count": len(entities),
                "class_counts": dict(sorted(classes.items())),
                "registration": locations,
            },
            "static_props": {
                "game_lump_version": 11,
                "dictionary_slots": count,
                "distinct_used_paths": len(used),
                "placements": sum(used.values()),
                "embedded_mesh_sets": len(embedded),
                "placements_with_embedded_mesh": sum(used[k] for k in embedded),
                "external_mesh_sets": len(external),
                "placements_requiring_external_mesh": sum(external.values()),
            },
            "pak_entries_by_extension": dict(sorted(formats.items())),
            "lumps": [
                {
                    "id": i,
                    "name": NAMES.get(i),
                    "bytes": lump.size,
                    "version": lump.version,
                    "sha256": digest(self.raw(i)),
                }
                for i, lump in enumerate(self.lumps)
                if lump.size
            ],
        }


def zip_index(z):
    members = {normal(x.filename): x for x in z.infolist()}
    insist(len(members) == len(z.infolist()), "Ambiguous duplicate pak entry")
    return members


def filehash(z, item):
    with z.open(item) as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def texture_chain(bsp, info_index):
    info = bsp.get(6)
    data = bsp.get(2)
    insist(0 <= info_index < len(info) // 72, "Face has invalid texinfo")
    (texdata_index,) = struct.unpack_from("<i", info, info_index * 72 + 68)
    insist(0 <= texdata_index < len(data) // 32, "Texinfo has invalid texdata")
    (name_index,) = struct.unpack_from("<i", data, texdata_index * 32 + 12)
    return texdata_index, name_index


def compare_native(a, b, face_ids=None):
    """Prove the native map changes texture routing on exactly the selected brush faces."""
    insist(
        a.version == b.version and a.revision == b.revision,
        "BSP version or revision changed",
    )
    preserved = []
    for i in range(64):
        la, lb = a.lumps[i], b.lumps[i]
        if i not in MUTABLE:
            insist(
                la == lb and digest(a.raw(i)) == digest(b.raw(i)),
                f"Unrelated lump changed: {i} {NAMES.get(i)}",
            )
            preserved.append(i)
    for i in (2, 6, 43, 44):
        before = a.get(i)
        after = b.get(i)
        insist(
            len(after) > len(before) and after[: len(before)] == before,
            f"Original texture table {i} changed or had no appended entries",
        )
    oldnames, newnames = a.texture_names(), b.texture_names()
    addednames = {normal(n) for n in newnames[len(oldnames) :]}
    insist(
        addednames and all(n.startswith("yuga_dustlab/jade_") for n in addednames),
        "Unexpected appended material path",
    )
    material_map = {}
    selections = {}
    new_info = a.count(6, 72)
    new_data = a.count(2, 32)
    for lump in (7, 58):
        before = a.get(lump)
        after = b.get(lump)
        insist(len(before) == len(after), "Face count changed")
        changed = []
        for j, (old, new) in enumerate(zip(chunks(before, 56), chunks(after, 56))):
            if new == old:
                continue
            insist(
                old[:10] == new[:10] and old[12:] == new[12:],
                f"Geometry changed on {lump}:{j}",
            )
            (oi,) = struct.unpack_from("<h", old, 10)
            (ni,) = struct.unpack_from("<h", new, 10)
            insist(oi >= 0 and ni >= new_info, "Expected a private texinfo clone")
            od, on = texture_chain(a, oi)
            nd, nn = texture_chain(b, ni)
            insist(
                nd >= new_data and nn >= len(oldnames),
                "Expected a private texdata clone and material name",
            )
            oinfo = a.get(6)[oi * 72 : oi * 72 + 68]
            ninfo = b.get(6)[ni * 72 : ni * 72 + 68]
            insist(
                oinfo == ninfo,
                f"Texture/lightmap coordinates or surface flags changed on {j}",
            )
            odata = a.get(2)[od * 32 : (od + 1) * 32]
            ndata = b.get(2)[nd * 32 : (nd + 1) * 32]
            insist(
                odata[:12] == ndata[:12] and odata[16:] == ndata[16:],
                f"Texture or reflectivity metadata changed on {j}",
            )
            orig = normal(oldnames[on])
            jade = normal(newnames[nn])
            insist(
                jade in addednames and material_map.get(jade, orig) == orig,
                "Ambiguous ground material clone",
            )
            material_map[jade] = orig
            changed.append(j)
        selections[lump] = changed
    active = [v for k, v in selections.items() if a.lumps[k].size]
    insist(
        active and active[0] and all(r == active[0] for r in active),
        "Mismatch between active LDR/HDR ground faces",
    )
    if face_ids is not None:
        insist(
            set(active[0]) == set(face_ids), "Face set differs from selector manifest"
        )
    insist(
        set(material_map) == addednames,
        "Unused or unaccounted new material definitions",
    )
    with a.archive() as za, b.archive() as zb:
        oldset, newset = zip_index(za), zip_index(zb)
        added = set(newset) - set(oldset)
        insist(set(oldset) <= set(newset), "Lost original packed content")
        expected_vmts = {"materials/" + name + ".vmt" for name in addednames}
        new_vtfs = added - expected_vmts
        insist(
            expected_vmts.issubset(added) and new_vtfs,
            "Missing private ground shaders or textures",
        )
        for name in new_vtfs:
            insist(
                re.fullmatch(r"materials/yuga_dustlab/tex_[0-9a-f]+\.vtf", name)
                is not None,
                "Unexpected new packed resource: " + name,
            )
        combined = hashlib.sha256()
        uncompressed = 0
        for name, old in sorted(oldset.items()):
            new = newset[name]
            insist(
                (old.CRC, old.file_size) == (new.CRC, new.file_size),
                f"Packed file changed: {name}",
            )
            sha = filehash(za, old)
            insist(
                sha == filehash(zb, new), f"Decompressed packed bytes changed: {name}"
            )
            combined.update(name.encode() + b"\0" + bytes.fromhex(sha))
            uncompressed += old.file_size
        referenced_textures = set()
        overrides = {}
        for path in sorted(expected_vmts):
            raw = zb.read(newset[path]).decode("utf-8-sig").replace("\\", "/").lower()
            mat = path.removeprefix("materials/").removesuffix(".vmt")
            insist(
                re.search(r'^\s*"?patch"?\s*\{', raw) is not None
                and "materials/" + material_map[mat] + ".vmt" in raw,
                f"{path} does not patch and include its original VMT",
            )
            # Prohibit a change to surface type, normal map, lightmap, roughness or transparency.
            names = set(re.findall(r"\$[a-z_0-9]+", raw))
            targets = re.findall(r'"?(\$basetexture2?)"?\s*"([^"]+)"', raw)
            insist(
                names
                and names.issubset({"$basetexture", "$basetexture2"})
                and set(name for name, _ in targets) == names,
                "Shader properties outside albedo: " + path,
            )
            overrides[mat] = {}
            for prop, texture in targets:
                target = (
                    "materials/"
                    + texture.removeprefix("materials/").removesuffix(".vtf")
                    + ".vtf"
                )
                insist(
                    target in new_vtfs,
                    f"{path} references a missing private texture {target}",
                )
                referenced_textures.add(target)
                overrides[mat][prop] = target
        insist(
            referenced_textures == new_vtfs, "Unreferenced additions in the map archive"
        )
        for texture in new_vtfs:
            with zb.open(newset[texture]) as stream:
                insist(
                    stream.read(4) == b"VTF\0",
                    "A claimed private texture has no VTF header",
                )
    hashed = digest(b"".join(struct.pack("<I", x) for x in active[0]))
    return {
        "schema": "yuga.dust2.native-diff.v1",
        "baseline_sha256": digest(a.data),
        "variant_sha256": digest(b.data),
        "revision": a.revision,
        "immutable_lumps_verified": preserved,
        "stable_lump_count": len(preserved),
        "texinfo_only_face_change": True,
        "changed_face_count": len(active[0]),
        "changed_face_set_sha256": hashed,
        "ldr_hdr_select_same_faces": True,
        "ground_manifest_matches": None if face_ids is None else True,
        "original_pak_entries_verified": len(oldset),
        "original_pak_uncompressed_bytes_verified": uncompressed,
        "original_pak_member_digest": combined.hexdigest(),
        "overridden_shader_properties": sorted(
            {prop for row in overrides.values() for prop in row}
        ),
        "new_vtf_count": len(new_vtfs),
        "replaced_albedo_references": overrides,
        "new_vmt_count": len(addednames),
        "changed_material_sources": dict(sorted(material_map.items())),
        "scope": "Native structural/content comparison. Renderer behavior and installed shared game assets are separate checks.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    cmd = parser.add_subparsers(dest="cmd", required=True)
    i = cmd.add_parser("inventory")
    i.add_argument("source", type=Path)
    c = cmd.add_parser("compare")
    c.add_argument("source", type=Path)
    c.add_argument("variant", type=Path)
    c.add_argument(
        "--face-ids", type=Path, help="JSON array of selected source dface indexes"
    )
    for sub in (i, c):
        sub.add_argument("--output", type=Path)
    args = parser.parse_args()
    with Bsp(args.source) as first:
        if args.cmd == "inventory":
            result = first.inventory()
        else:
            ids = json.loads(args.face_ids.read_text()) if args.face_ids else None
            with Bsp(args.variant) as other:
                result = compare_native(first, other, ids)
    txt = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(txt)
    else:
        print(txt, end="")


if __name__ == "__main__":
    main()
