#!/usr/bin/env python3
"""Install checksum-pinned official tools locally, without changing system config."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import urllib.request
import zipfile

TOOLS = [
    {
        "name": "ghidra", "directory": "ghidra_12.1.4_PUBLIC",
        "url": "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip",
        "metadata_url": "https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/tags/Ghidra_12.1.4_build",
        "sha256": "ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db",
        "bytes": 569649598, "kind": "zip",
    },
    {
        "name": "jdk", "directory": "jdk-21.0.12.1+1",
        "url": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_x64_linux_hotspot_21.0.12.1_1.tar.gz",
        "metadata_url": "https://api.github.com/repos/adoptium/temurin21-binaries/releases/tags/jdk-21.0.12.1%2B1",
        "sha256": "ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94",
        "bytes": 207473347, "kind": "tar",
    },
]


def install(root: Path, spec: dict) -> dict:
    target = root / spec["directory"]
    receipt = root / (spec["name"] + "-install.json")
    if target.exists():
        if receipt.exists() and json.loads(receipt.read_text())["sha256"] == spec["sha256"]:
            return json.loads(receipt.read_text())
        raise RuntimeError(f"Unverified existing installation: {target}")
    archive = root / (spec["name"] + ".download")
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "YUGA-native-toolchain"})
    # Inherits proxy and CA trust. No credentials or redirected URLs are logged.
    with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > spec["bytes"]:
                raise RuntimeError("Download exceeded pinned size")
            digest.update(chunk)
            output.write(chunk)
    if size != spec["bytes"] or digest.hexdigest() != spec["sha256"]:
        raise RuntimeError("Official release checksum or size mismatch; refusing extraction")
    if spec["kind"] == "zip":
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                destination = (root / member.filename).resolve()
                if not destination.is_relative_to(root):
                    raise RuntimeError("Archive path escapes installation root")
            source.extractall(root)
            for member in source.infolist():
                mode = member.external_attr >> 16
                if mode & 0o111:
                    os.chmod(root / member.filename, mode & 0o777)
    else:
        with tarfile.open(archive) as source:
            source.extractall(root, filter="data")
    if not target.is_dir():
        raise RuntimeError("Official archive did not contain the pinned directory")
    record = {**spec, "download_bytes": size, "checksum_verified": True, "path": str(target)}
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    archive.unlink()
    print(f"Verified and installed {spec['name']} ({size} downloaded bytes)", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < 2_000_000_000:
        raise RuntimeError("Need at least 2 GB free for sequential download and extraction")
    records = [install(root, spec) for spec in TOOLS]
    (root / "installation.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
