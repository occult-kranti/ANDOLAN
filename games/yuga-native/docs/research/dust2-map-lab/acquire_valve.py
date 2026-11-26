#!/usr/bin/env python3
"""Acquire one pinned CS:GO map and its actual render dependencies from Valve.

Example: python3 acquire_valve.py /tmp/dust-local --downloader /opt/DepotDownloader
Requires Python 3.10+ and SteamRE DepotDownloader. All retail data goes to WORK.
"""

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib

APP = "740"
DEPOT = "731"
MANIFEST = "1224088799001669801"
# Values from the official, anonymously accessible CS:GO dedicated server manifest.
OFFICIAL = {
    "csgo/maps/de_dust2.bsp": "d905c6f7dd694a0dace9380a8558ca8a177cbd91",
    "csgo/maps/de_dust2.nav": "4f53ff186ee3532b681943724d81a6e27f835cc3",
    "csgo/resource/overviews/de_dust2.txt": "94d3b051c64cf5663ad60d91d72473c7fe94f936",
    "csgo/resource/overviews/de_dust2_radar.dds": "c21ff88830cc29a3f0e0f03cc1055df2d3cb4f99",
    "csgo/resource/overviews/de_dust2_higher_radar.dds": "e197e131924782724ed1180893cb61e3d2beda5b",
    "csgo/pak01_dir.vpk": "fe38c13f82ae49ec1a7a613465271b13a9a1636c",
}
BSP_SHA256 = "b91be410539fbbfc16300423f1e19c024f12addf1429c8cb2f72b53fe0fd6bcc"
VPK_DIR = 0x7FFF


def digest(file, algorithm):
    h = hashlib.new(algorithm)
    with file.open("rb") as stream:
        while block := stream.read(2**20):
            h.update(block)
    return h.hexdigest()


def atomic_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        staged = Path(output.name)
        try:
            output.write(data)
        except Exception:
            staged.unlink(missing_ok=True)
            raise
    staged.replace(path)


def normalize(name):
    # A real Dust II model and its corresponding material contain a trailing space.
    return name.replace("\\", "/").lower()


def local_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError(f"Invalid Source asset path: {name!r}")
    return path


def material(name, extension):
    base = normalize(name).lstrip("/").removeprefix("materials/")
    return "materials/" + base.removesuffix(".vmt").removesuffix(".vtf") + extension


@dataclass(frozen=True)
class Entry:
    crc: int
    archive: int
    offset: int
    size: int
    preload: bytes


def vpk_index(path):
    data = path.read_bytes()
    magic, version, tree_size = struct.unpack_from("<III", data)
    if magic != 0x55AA1234 or version not in (1, 2):
        raise ValueError("Unsupported Valve VPK directory")
    pos = 28 if version == 2 else 12
    end = pos + tree_size
    entries = {}

    def take_name():
        nonlocal pos
        finish = data.index(0, pos, end)
        val = data[pos:finish].decode("latin-1")
        pos = finish + 1
        return val

    while extension := take_name():
        while folder := take_name():
            while filename := take_name():
                crc, preload, archive, offset, size, terminator = struct.unpack_from(
                    "<IHHIIH", data, pos
                )
                pos += 18
                if terminator != 0xFFFF or pos + preload > end:
                    raise ValueError("Malformed Valve VPK entry")
                name = normalize(
                    ("" if folder == " " else folder + "/")
                    + filename
                    + ("" if extension == " " else "." + extension)
                )
                local_path(name)
                entries[name] = Entry(
                    crc,
                    archive,
                    offset + (end if archive == VPK_DIR else 0),
                    size,
                    data[pos : pos + preload],
                )
                pos += preload
    if pos != end:
        raise ValueError("VPK directory size mismatch")
    return entries


def download(args, paths):
    if not paths:
        return
    if not args.downloader:
        raise SystemExit(
            "Supply --downloader PATH to SteamRE DepotDownloader to fetch the missing depot files."
        )
    # The file list and tool's resume state are local. Never send a Steam login.
    with tempfile.TemporaryDirectory(dir=args.work) as temp:
        selection = Path(temp) / "files.txt"
        selection.write_text(
            "".join(name + "\n" for name in sorted(paths)), encoding="utf-8"
        )
        subprocess.run(
            [
                str(args.downloader),
                "-app",
                APP,
                "-depot",
                DEPOT,
                "-manifest",
                MANIFEST,
                "-filelist",
                str(selection),
                "-dir",
                str(args.work / "valve-depot"),
                "-validate",
                "-max-downloads",
                "12",
            ],
            check=True,
        )


def official_assets(args):
    depot = args.work / "valve-depot"
    missing = []
    for name, sha in OFFICIAL.items():
        local = depot / name
        if not local.exists() or digest(local, "sha1") != sha:
            missing.append(name)
    download(args, missing)
    for name, sha in OFFICIAL.items():
        if digest(depot / name, "sha1") != sha:
            raise ValueError("Unexpected official content: " + name)
    return depot / "csgo"


class MapResources:
    def __init__(self, bsp):
        with bsp.open("rb") as source:
            header = source.read(1036)
            if header[:8] != b"VBSP\x15\0\0\0":
                raise ValueError("Expected Source 1 BSP version 21")
            self.revision = struct.unpack_from("<i", header, 1032)[0]
            lumps = [struct.unpack_from("<4i", header, 8 + i * 16) for i in range(64)]

            def read_lump(index):
                offset, size, _, compression = lumps[index]
                if compression:
                    raise ValueError("Compressed lump unexpected in the pinned map")
                source.seek(offset)
                data = source.read(size)
                if len(data) != size:
                    raise EOFError("Truncated BSP lump")
                return data

            entities = read_lump(0)
            self.entity_models = {
                normalize(s.decode("latin-1"))
                for s in re.findall(rb'"model"\s*"([^"]+?\.mdl)"', entities, flags=re.I)
            }
            self.world_materials = {
                mat.decode("latin-1") for mat in read_lump(43).split(b"\0") if mat
            }
            self.sky = (
                re.search(rb'"skyname"\s*"([^"]+)"', entities)
                .group(1)
                .decode("latin-1")
            )
            games = read_lump(35)
            for i in range(struct.unpack_from("<i", games)[0]):
                kind, flags, _, offset, length = struct.unpack_from(
                    "<4sHHii", games, 4 + i * 16
                )
                if kind == b"prps":
                    if flags & 1:
                        raise ValueError("Unexpected packed static-prop lump")
                    source.seek(offset)
                    prop = source.read(length)
                    break
            else:
                raise ValueError("Map has no static-prop dictionary")
            self.static_slots = struct.unpack_from("<I", prop)[0]
            self.static_models = {
                normalize(
                    prop[4 + i * 128 : 4 + (i + 1) * 128]
                    .split(b"\0", 1)[0]
                    .decode("latin-1")
                )
                for i in range(self.static_slots)
            }
            self.pak = zipfile.ZipFile(io.BytesIO(read_lump(40)))
            self.packed_paths = {normalize(n): n for n in self.pak.namelist()}

    def close(self):
        self.pak.close()


def model_materials(data, available):
    if data[:4] != b"IDST":
        raise ValueError("Invalid Studio model")
    count, offset, path_count, path_offset = struct.unpack_from("<4i", data, 204)

    def cstring(at):
        return normalize(data[at : data.index(0, at)].decode("latin-1"))

    directories = [
        cstring(struct.unpack_from("<i", data, path_offset + i * 4)[0])
        for i in range(path_count)
    ]
    found = set()
    for i in range(count):
        base = offset + 64 * i
        name = cstring(base + struct.unpack_from("<i", data, base)[0])
        paths = [
            *(material(d.rstrip("/") + "/" + name, ".vmt") for d in directories if d),
            material(name, ".vmt"),
        ]
        for path in paths:
            if path in available:
                found.add(path)
                break
        else:
            raise ValueError(f"Unresolved model material {name!r}")
    return count, found


def vmt_dependencies(data, available):
    text = re.sub(r"//[^\r\n]*", "", data.decode("cp1252", "replace"))
    tokens = [
        quoted or bare for quoted, bare in re.findall(r'"([^"\n]*)"|([^\s{}"]+)', text)
    ]
    vmts = set()
    vtfs = set()
    for raw_key, raw_value in zip(tokens, tokens[1:]):
        key = raw_key.lower()
        value = normalize(raw_value)
        if key != "include" and not key.startswith(("$", "%")):
            continue
        if not re.fullmatch(r"[a-z0-9_./ -]+", value) or value.startswith(
            ("_rt_", "env_cubemap")
        ):
            continue
        for extension, bucket in ((".vmt", vmts), (".vtf", vtfs)):
            path = material(value, extension)
            if path in available:
                bucket.add(path)
        if (
            key in ("$basetexture", "$basetexture2")
            and material(value, ".vtf") not in available
        ):
            raise ValueError(f"Unresolved declared albedo {raw_value!r}")
    return vmts, vtfs


class AssetLibrary:
    def __init__(self, args, retail, resources):
        self.args = args
        self.retail = retail
        self.resources = resources
        self.output = args.work / "assets"
        self.index = vpk_index(retail / "pak01_dir.vpk")
        self.available = set(self.index) | set(resources.packed_paths)
        self.checked = set()
        self.verified_archives = set()

    def data(self, name):
        packed = self.resources.packed_paths.get(name)
        return (
            self.resources.pak.read(packed)
            if packed
            else (self.output / local_path(name)).read_bytes()
        )

    def archive_file(self, archive):
        return self.retail / (
            "pak01_dir.vpk" if archive == VPK_DIR else f"pak01_{archive:03d}.vpk"
        )

    def fetch(self, names, keep=False):
        requested = set(names) - self.checked - self.resources.packed_paths.keys()
        groups = defaultdict(list)
        for name in sorted(requested):
            rec = self.index[name]
            out = self.output / local_path(name)
            if (
                out.is_file()
                and out.stat().st_size == rec.size + len(rec.preload)
                and zlib.crc32(out.read_bytes()) & 0xFFFFFFFF == rec.crc
            ):
                self.checked.add(name)
                continue
            groups[rec.archive].append(name)
        archive_ids = sorted(groups)
        for start in range(0, len(archive_ids), 3):
            batch = archive_ids[start : start + 3]
            missing = [a for a in batch if not self.archive_file(a).exists()]
            if missing and shutil.disk_usage(self.retail).free < 700_000_000:
                raise SystemExit("Less than 700 MB free for the next depot batch")
            verify = (
                [a for a in batch if a not in self.verified_archives]
                if self.args.downloader
                else missing
            )
            download(self.args, ["csgo/" + self.archive_file(a).name for a in verify])
            self.verified_archives.update(batch)
            for archive in batch:
                file = self.archive_file(archive)
                with file.open("rb") as src:
                    for name in groups[archive]:
                        record = self.index[name]
                        src.seek(record.offset)
                        body = record.preload + src.read(record.size)
                        if (
                            len(body) != record.size + len(record.preload)
                            or zlib.crc32(body) & 0xFFFFFFFF != record.crc
                        ):
                            raise ValueError(
                                f"VPK size or CRC mismatch for {name!r} in {file}"
                            )
                        atomic_bytes(self.output / local_path(name), body)
                        self.checked.add(name)
                # Keep the first geometry groups for likely VMTs. Only evict files this call fetched.
                if not keep and archive in missing:
                    file.unlink()
                    self.verified_archives.discard(archive)
        return requested

    def resolve(self):
        r = self.resources
        models = r.static_models | r.entity_models
        mesh_files = set()
        for name in models:
            stem = name.removesuffix(".mdl")
            for suffix in (".mdl", ".dx90.vtx", ".vvd"):
                path = stem + suffix
                if path not in self.available:
                    raise ValueError(f"Missing model component {path}")
                mesh_files.add(path)
            if stem + ".phy" in self.available:
                mesh_files.add(stem + ".phy")
        self.fetch(mesh_files, keep=True)
        vmts = {material(k, ".vmt") for k in r.world_materials}
        vmts.update(
            path
            for path in self.available
            if path.startswith("materials/skybox/" + r.sky) and path.endswith(".vmt")
        )
        model_slots = 0
        model_vmts = set()
        for name in sorted(models):
            slots, names = model_materials(self.data(name), self.available)
            model_slots += slots
            model_vmts |= names
        vmts |= model_vmts
        seen = set()
        vtfs = set()
        while pending := vmts - seen:
            self.fetch(pending)
            for path in sorted(pending):
                material_refs, texture_refs = vmt_dependencies(
                    self.data(path), self.available
                )
                vmts |= material_refs
                vtfs |= texture_refs
            seen |= pending
        self.fetch(vtfs)
        return {
            "static_dictionary_slots": r.static_slots,
            "unique_static_stems": len(r.static_models),
            "entity_model_stems": sorted(r.entity_models),
            "unique_model_stems": len(models),
            "surface_material_names": len(r.world_materials),
            "material_slots": model_slots,
            "model_vmt_count": len(model_vmts),
            "vmts": sorted(vmts),
            "vtfs": sorted(vtfs),
            "model_components": sorted(mesh_files),
            "external_verified_files": len(self.checked),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--downloader", type=Path)
    args = parser.parse_args()
    args.work = args.work.resolve()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.downloader:
        args.downloader = args.downloader.resolve()
    retail = official_assets(args)
    bsp = retail / "maps/de_dust2.bsp"
    if digest(bsp, "sha256") != BSP_SHA256:
        raise ValueError("Unexpected Dust II revision")
    resources = MapResources(bsp)
    try:
        result = AssetLibrary(args, retail, resources).resolve()
    finally:
        resources.close()
    result.update(
        app=APP,
        depot=DEPOT,
        manifest=MANIFEST,
        bsp_sha256=BSP_SHA256,
        bsp_revision=resources.revision,
    )
    atomic_bytes(
        args.work / "valve-closure.json",
        (json.dumps(result, indent=2) + "\n").encode("utf-8"),
    )
    print(
        f"Verified {result['unique_model_stems']} model stems, {len(result['vmts'])} VMTs and {len(result['vtfs'])} VTFs."
    )
    print("Content root for external assets:", args.work / "assets")


if __name__ == "__main__":
    main()
