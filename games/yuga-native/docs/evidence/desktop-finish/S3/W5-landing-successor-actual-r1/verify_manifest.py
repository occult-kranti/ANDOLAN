#!/usr/bin/env python3
"""Read-only verification of this sealed packet and its repository references."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "artifact-manifest.json").read_text())
    failures = []
    for category in ("files", "references"):
        for name, pin in manifest[category].items():
            path = root / name
            if not path.is_file() or path.stat().st_size != pin["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
                failures.append({"category": category, "path": name})
    actual = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != "artifact-manifest.json")
    if actual != sorted(manifest["files"]):
        failures.append({"category": "inventory", "actual_count": len(actual)})
    print(json.dumps({"passed": not failures, "owned_files": len(manifest["files"]), "references": len(manifest["references"]), "failures": failures}))
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
