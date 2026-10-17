#!/usr/bin/env python3
"""Stage the exact cloth review dependencies without importing the product art tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
import zlib

PROJECT = Path(__file__).absolute().parents[1]
SOURCES = (
    "scripts/rama_secondary_motion.gd",
    "shaders/rama_secondary_cloth.gdshader",
    "tests/open_cloth_material_cases.gd",
    "art/open-art-wave/integration/cloth_candidate.gd",
    "art/open-art-wave/materials/indigo-woven-cloth.tres",
    *("art/open-art-wave/textures/indigo-woven-" + name + ".png"
      for name in ("albedo", "roughness", "normal")),
    "project.godot",
)
MANIFEST = "open-cloth-stage-manifest.json"
MINIMAL_PROJECT = b'''config_version=5

[application]
config/name="YUGA isolated open cloth review"
config/features=PackedStringArray("4.6", "GL Compatibility")

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"

[debug]
gdscript/warnings/treat_warnings_as_errors=false
'''
LIMITATIONS = [
    "Only the eight explicit cloth source dependencies and a generated minimal project are staged.",
    "The product art/.gdignore is preserved; no ignore files, caches, assets, scenes or full world are copied.",
    "No Godot process is executed. The caller must run a bounded editor import and the actual material test.",
    "The minimal compatibility-renderer project is for resource/lifecycle checks, not hero appearance, gameplay or performance acceptance.",
    "Source envelope and dependency checks do not replace the Godot parser or PNG importer.",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_symlinks(path: Path) -> None:
    for part in reversed((path, *path.parents)):
        if part.is_symlink():
            raise ValueError(f"Symlinks are not allowed: {part}")


def snapshot(path: Path) -> tuple[bytes, tuple[int, ...]]:
    no_symlinks(path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"Source is not a regular file: {path}")
        if before.st_size <= 0 or before.st_size > 16 * 1024 * 1024:
            raise ValueError(f"Source size is outside the review bound: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as source:
            data = source.read(16 * 1024 * 1024 + 1)
        after = os.fstat(descriptor)
        identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if identity(before) != identity(after) or len(data) != before.st_size:
            raise ValueError(f"Source changed while reading: {path}")
        return data, identity(after)
    finally:
        os.close(descriptor)


def validate_png(data: bytes, relative: str) -> None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Invalid PNG signature: {relative}")
    offset, kinds = 8, []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f"Truncated PNG chunk: {relative}")
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset + length + 12
        if end > len(data):
            raise ValueError(f"Truncated PNG payload: {relative}")
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:end - 4]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != struct.unpack_from(">I", data, end - 4)[0]:
            raise ValueError(f"Invalid PNG chunk checksum: {relative}")
        if not kinds:
            if kind != b"IHDR" or length != 13:
                raise ValueError(f"Invalid PNG header: {relative}")
            width, height = struct.unpack_from(">II", body)
            if not 0 < width <= 8192 or not 0 < height <= 8192:
                raise ValueError(f"PNG dimensions exceed the review bound: {relative}")
        kinds.append(kind)
        offset = end
        if kind == b"IEND":
            if length or offset != len(data):
                raise ValueError(f"Invalid PNG end: {relative}")
            break
    if not kinds or kinds[-1] != b"IEND" or b"IDAT" not in kinds:
        raise ValueError(f"Incomplete PNG: {relative}")


def validate_sources(pinned: dict[str, tuple[bytes, tuple[int, ...]]]) -> None:
    identities = [identity[:2] for _, identity in pinned.values()]
    if len(set(identities)) != len(identities):
        raise ValueError("Source aliases are not allowed")
    for relative, (data, _) in pinned.items():
        if relative.endswith(".png"):
            validate_png(data, relative)
            continue
        text = data.decode("utf-8")
        if "\0" in text:
            raise ValueError(f"NUL in text source: {relative}")
        marker = ("config_version=5" if relative == "project.godot" else
                  "[gd_resource" if relative.endswith(".tres") else
                  "shader_type spatial;" if relative.endswith(".gdshader") else "extends ")
        if marker not in text:
            raise ValueError(f"Unrecognized source envelope: {relative}")
        for reference in re.findall(r'''res://([^"'\n]+)''', text):
            if reference not in SOURCES:
                # The original product configuration is pinned, not copied.
                if relative != "project.godot":
                    raise ValueError(f"Unstaged dependency in {relative}: {reference}")


def stage(project_output: Path) -> dict:
    if not project_output.is_absolute():
        raise ValueError("--project-output must be an absolute path")
    no_symlinks(project_output)
    no_symlinks(PROJECT)
    project = PROJECT.resolve(strict=True)
    checkout = next((parent for parent in (project, *project.parents)
                     if (parent / ".git").exists()), project)
    destination = project_output.resolve(strict=False)
    if destination.is_relative_to(checkout) or checkout.is_relative_to(destination):
        raise ValueError("--project-output must be outside the source checkout")
    if os.path.lexists(destination):
        raise ValueError("--project-output must be a fresh directory; existing destinations are never overwritten")
    if not destination.parent.is_dir():
        raise ValueError("--project-output parent must be an existing real directory")
    pinned = {relative: snapshot(project / relative) for relative in SOURCES}
    validate_sources(pinned)
    # All inputs are pinned before creating output. Exclusive creation is also
    # used for every payload and the receipt; a failed fixture is never reused.
    destination.mkdir(mode=0o700, exist_ok=False)
    receipt = {
        "schema_version": 1, "passed": False, "project_output": str(destination),
        "manifest": MANIFEST, "files": [], "engine_executed": False,
        "source_project_sha256": sha(pinned["project.godot"][0]),
        "limitations": LIMITATIONS,
    }
    try:
        for relative, (source, _) in pinned.items():
            payload = MINIMAL_PROJECT if relative == "project.godot" else source
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as staged:
                staged.write(payload)
            if target.is_symlink() or target.read_bytes() != payload:
                raise ValueError(f"Staged payload differs from pinned bytes: {relative}")
            receipt["files"].append({
                "source": relative, "staged": relative, "sha256": sha(payload),
                "source_sha256": sha(source), "bytes": len(payload),
                "mode": "generated_minimal" if relative == "project.godot" else "exact_copy",
            })
        for relative, before in pinned.items():
            if snapshot(project / relative) != before:
                raise ValueError(f"Source changed during staging: {relative}")
        expected = {row["staged"] for row in receipt["files"]}
        actual = {str(path.relative_to(destination)) for path in destination.rglob("*") if path.is_file()}
        if expected != actual:
            raise ValueError("Fixture contains unexpected files")
        receipt["source_unchanged"] = True
        receipt["passed"] = True
    except (OSError, ValueError) as error:
        receipt["error"] = str(error)
        raise
    finally:
        with (destination / MANIFEST).open("x", encoding="utf-8") as manifest:
            manifest.write(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = stage(arguments.project_output)
    except (OSError, ValueError) as error:
        print(json.dumps({"passed": False, "project_output": str(arguments.project_output),
                          "error": str(error)}, allow_nan=False))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
