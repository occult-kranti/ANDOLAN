#!/usr/bin/env python3
"""Read-only verification of an explicitly sealed checkpoint file list."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
manifest = json.loads(Path(__file__).with_name("ready-manifest.json").read_text())
failures = []
for row in manifest["ready"]:
    path = root / row["path"]
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
        failures.append({"path": row["path"], "reason": "missing_or_unsafe"})
        continue
    if (path.stat().st_size != row["bytes"]
            or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]
            or oct(path.stat().st_mode & 0o777) != row["mode"]):
        failures.append({"path": row["path"], "reason": "identity_changed"})
print(json.dumps({"passed": not failures, "files": len(manifest["ready"]), "failures": failures}))
raise SystemExit(1 if failures else 0)
