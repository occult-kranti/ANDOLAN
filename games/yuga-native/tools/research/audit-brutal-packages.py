#!/usr/bin/env python3
"""Inspect two pinned BRUTAL archives without extracting or executing code."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

PACKAGES = (
    ("ahwoo.brutal.core", "2026.10.1", "074ed2fde25c42548c283626c2b89d2028f349203dc2d2927d4ab0999a2386c4"),
    ("ahwoo.brutal.gltf", "2026.10.2", "0bbf18f4988e7dbbd7fee02ea3b93965e6515f59277f977a1e7edafebb38d144"),
)
NS = {"n": "http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"}


def inspect(name, version, expected, cache):
    filename = f"{name}.{version}.nupkg"
    url = f"https://api.nuget.org/v3-flatcontainer/{name}/{version}/{filename}"
    local = cache / filename
    if local.exists():
        if local.stat().st_size > 2_000_000:
            raise ValueError("Oversized cached archive")
        raw = local.read_bytes()
    else:
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read(2_000_001)
    if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Integrity/size mismatch: {filename}")
    local.write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if sum(item.file_size for item in archive.infolist()) > 8_000_000 or archive.testzip():
            raise ValueError("Expanded size or CRC failure")
        names = archive.namelist()
        nuspecs = [item for item in names if item.endswith(".nuspec")]
        if len(nuspecs) != 1:
            raise ValueError("Expected one nuspec")
        metadata = ET.fromstring(archive.read(nuspecs[0])).find("n:metadata", NS)
        if metadata is None or metadata.findtext("n:id", namespaces=NS).lower() != name or metadata.findtext("n:version", namespaces=NS) != version:
            raise ValueError("Package identity mismatch")
        notices = {item: {"bytes": len(archive.read(item)), "sha256": hashlib.sha256(archive.read(item)).hexdigest()}
                   for item in names if item in ("LICENSE.txt", "NOTICE.txt") or item.startswith("LICENSES/")}
        if not {"LICENSE.txt", "NOTICE.txt"}.issubset(notices):
            raise ValueError("Missing notices")
        return {"id": name, "version": version, "url": url, "bytes": len(raw), "sha256": expected,
                "crc_passed": True, "assemblies": [item for item in names if item.startswith("lib/") and item.endswith(".dll")],
                "dependencies": [{"framework": group.attrib["targetFramework"], "packages": [dict(item.attrib) for item in group.findall("n:dependency", NS)]}
                                 for group in metadata.findall("n:dependencies/n:group", NS)], "notices": notices}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    report = {"schema": 1, "scope": "Pinned package metadata/integrity/notices only; no vendor code executed.",
              "compiled": False, "rendered": False,
              "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "packages": [inspect(*package, args.cache) for package in PACKAGES]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"packages_inspected": len(report["packages"]), "report": str(args.report), "compiled": False, "rendered": False}))


if __name__ == "__main__":
    main()
