"""Recompile Hanzo's 2013 editable Nexuiz Dust II remake and package a floor study.

Run with --help. Copy or link the stock Nexuiz PK3s outside this repository first.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from finish import finish, ground_resources, sha

NAME = "q3dust2-jb-beta6"
SOURCE_HASH = "92d52f60a0c33b0bddc9fb0b534f0dd43d346f0691ef1d947b3034149245ca03"
BASE_HASH = "8b9b0bd7c6cedd0334ecb8a267d870e74de76949468594c5394821983358b6cc"
TEXTURE_HASH = "38ad44a78a9072e575c44174ac82906621631a7531988a0274dc2329505641a5"
MAP = f"maps/{NAME}.map"
BSP = f"maps/{NAME}.bsp"
MINIMAP = f"gfx/{NAME}_mini.tga"


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stage_inputs(pack, base_inputs, data):
    for target, source in zip(("data.pk3", "textures.pk3"), base_inputs):
        (data / target).symlink_to(source.resolve())
    for name in pack.namelist():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe archive name {name!r}")
        if name.endswith("/") or not (name.startswith(("scripts/", "textures/", "env/")) or name == MAP):
            continue
        dest = data / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(pack.read(name))
    with ZipFile(base_inputs[0]) as base:
        shaderlist = base.read("scripts/shaderlist.txt") + b"\ndust-nex\ndust-sky\n"
    (data / "scripts/shaderlist.txt").write_bytes(shaderlist)


def compile_source(tool, data, logs, threads):
    # Keep an installed user map or shader override out of the source-only build.
    isolated_home = logs.parent / "compiler-profile"
    isolated_home.mkdir(exist_ok=True)
    common = ["-game", "nexuiz", "-fs_homepath", str(isolated_home),
              "-fs_basepath", str(data.parent), "-fs_game", "data", "-threads", str(threads)]
    bsp = str(data / BSP)
    phases = [
        ("01-bsp", [*common, "-meta", "-skyfix", "-samplesize", "8", "-minsamplesize", "4",
                    "-mv", "1000000", "-mi", "6000000", str(data / MAP)]),
        ("02-vis", ["-vis", *common, bsp]),
        ("03-light", ["-light", *common, "-deluxe", "-patchshadows", "-samples", "3",
                      "-lightmapsize", "512", "-bounce", "8", "-fastbounce", "-bouncegrid", bsp]),
        ("04-minimap", ["-minimap", *common, bsp]),
        ("05-scale", ["-scale", *common, "1.16", bsp]),
    ]
    for label, args in phases:
        print(f"{label}  {logs / (label + '.log')}", flush=True)
        with (logs / (label + ".log")).open("wb") as log:
            subprocess.run([tool, *args], stdout=log, stderr=subprocess.STDOUT, check=True)
        if label == "01-bsp" and not (data / MAP).with_suffix(".prt").is_file():
            raise ValueError("Compiler did not produce the sealed-map portal file")


def zip_entry(archive, name, data):
    entry = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    entry.external_attr = 0o100644 << 16
    entry.compress_type = ZIP_DEFLATED
    archive.writestr(entry, data, compresslevel=6)


def assemble(pack, data, logs, output):
    expected_map = pack.read(MAP)
    if (data / MAP).read_bytes() != expected_map:
        raise ValueError("Staged geometry differs from the pinned author source")
    scaled = (data / f"maps/{NAME}_s.bsp").read_bytes()
    if scaled == pack.read(BSP):
        raise ValueError("Build points at the author's precompiled BSP")
    jade, audit = finish(scaled)
    resources = ground_resources(pack)
    lightmaps = sorted((data / f"maps/{NAME}").glob("lm_*.tga"))
    if len(lightmaps) != 8:
        raise ValueError(f"Expected eight freshly baked external light and direction maps, got {len(lightmaps)}")
    light_files = {p.relative_to(data).as_posix(): p.read_bytes() for p in lightmaps}
    generated = {**light_files, MINIMAP: (data / MINIMAP).read_bytes()}
    originals = {p: pack.read(p) for p in pack.namelist() if not p.endswith("/")
                 and p not in generated and p != BSP}
    if any("/lm_" in name for name in originals):
        raise ValueError("Unexpected original baked lighting in package")
    audit["source_map_sha256"] = sha(expected_map)
    audit["author_bsp_sha256_reference_only"] = sha(pack.read(BSP))
    audit["lightmaps_sha256"] = {name: sha(raw) for name, raw in light_files.items()}
    audit["minimap_sha256"] = sha(generated[MINIMAP])
    audit["package_sha256"] = {}
    audit["logs"] = {}
    for path in sorted(logs.glob("*.log")):
        content = path.read_text(errors="replace")
        diagnostics = [line for line in content.splitlines() if re.search(r"\b(?:WARNING|ERROR):", line)]
        audit["logs"][path.name] = {"sha256": file_hash(path),
                                    "diagnostics": {d: diagnostics.count(d) for d in sorted(set(diagnostics))}}
    if len(audit["logs"]) != 5:
        raise ValueError("Expected the records of all five compiler passes")
    for variant, entries in [("original", {**originals, **generated, BSP: scaled}),
                             ("jade", {**originals, **generated, **resources, BSP: jade})]:
        target = output / f"{NAME}-{variant}.pk3"
        temporary = target.with_suffix(".tmp")
        with ZipFile(temporary, "w") as archive:
            for name, raw in sorted(entries.items()):
                zip_entry(archive, name, raw)
        with ZipFile(temporary) as archive:
            if archive.testzip() is not None or archive.read(BSP) != entries[BSP]:
                raise ValueError(f"Invalid compiled {variant} package")
        os.replace(temporary, target)
        audit["package_sha256"][target.name] = file_hash(target)
    shader_src = output / "shaders"
    shader_src.mkdir(exist_ok=True)
    (shader_src / "dust-nex.shader").write_bytes(pack.read("scripts/dust-nex.shader"))
    (shader_src / "yuga_dust_lab.shader").write_bytes(resources["scripts/yuga_dust_lab.shader"])
    (output / "geometry-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(f"{audit['draw_surfaces']} draw surfaces, {audit['changed_surfaces']} jade floor surfaces. "
          f"Packages and geometry-audit.json in {output}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author-pack", required=True, type=Path)
    p.add_argument("--q3map2", required=True, type=Path)
    p.add_argument("--base-data", required=True, type=Path)
    p.add_argument("--base-textures", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--threads", type=int, default=2)
    p.add_argument("--package-existing", action="store_true",
                   help="Package the five completed phases already in OUTPUT/game and OUTPUT/logs")
    args = p.parse_args()
    if args.threads < 1:
        p.error("--threads must be positive")
    for path, digest in [(args.author_pack, SOURCE_HASH), (args.base_data, BASE_HASH),
                         (args.base_textures, TEXTURE_HASH)]:
        if file_hash(path) != digest:
            p.error(f"Input {path} does not match the documented release")
    root = args.output.resolve()
    data, logs = root / "game/data", root / "logs"
    root.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.author_pack) as pack:
        if not args.package_existing:
            if data.exists() or logs.exists():
                p.error("Choose a fresh output directory to avoid mixing compiled maps")
            data.mkdir(parents=True)
            logs.mkdir()
            stage_inputs(pack, (args.base_data, args.base_textures), data)
            compile_source(args.q3map2.resolve(), data, logs, args.threads)
        assemble(pack, data, logs, root)


if __name__ == "__main__":
    main()
