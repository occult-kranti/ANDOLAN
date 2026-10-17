#!/usr/bin/env python3
"""Prepare one integrity-pinned Khronos validator outside the game dependencies."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

VERSION = "2.0.0-dev.3.10"
URL = f"https://registry.npmjs.org/gltf-validator/-/gltf-validator-{VERSION}.tgz"
INTEGRITY = "sha512-odJ4k0tRkGXiDGn78yDBg+fBbAIvBnXxh3RwAta0emSxGtyagFE8B4xELB1oYe3S5RD8Ci3uZAsZaascH2LAEQ=="


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    destination = args.destination.resolve()
    with urllib.request.urlopen(URL, timeout=30) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Archive exceeds bounded size")
    integrity = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode()
    if integrity != INTEGRITY:
        raise ValueError("Pinned package integrity mismatch")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        if sum(member.size for member in members) > 2_000_000:
            raise ValueError("Expanded package exceeds bounded size")
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "package":
                raise ValueError("Unexpected package member path")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Links and special files are not accepted")
            relative = Path(*path.parts[1:])
            contents = archive.extractfile(member).read()
            files[str(relative)] = contents
    metadata = json.loads(files["package.json"])
    if metadata["name"] != "gltf-validator" or metadata["version"] != VERSION:
        raise ValueError("Package identity mismatch")
    if metadata.get("dependencies"):
        raise ValueError("Unexpected transitive dependencies")
    destination.mkdir(parents=True, exist_ok=True)
    for relative, contents in files.items():
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(contents)
    manifest = {
        "package": "gltf-validator", "version": VERSION, "url": URL,
        "integrity": integrity, "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        "scope": "Verified package acquisition; no npm lifecycle scripts or runtime dependency edits.",
    }
    (destination / "yuga-package-provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"destination": str(destination), "version": VERSION, "files": len(files), "integrity_verified": True}))


if __name__ == "__main__":
    main()
