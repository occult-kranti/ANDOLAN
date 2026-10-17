#!/usr/bin/env python3
"""Verify the immutable reversal packet; optional checks pin current native inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "archive-manifest.json").read_text())
    for row in manifest["files"]:
        path = root / row["path"]
        assert path.is_file() and not path.is_symlink(), row["path"]
        data = path.read_bytes()
        assert len(data) == row["bytes"] and sha(data) == row["sha256"], row["path"]
    assert manifest["file_count"] == len(manifest["files"])
    assert manifest["bytes"] == sum(row["bytes"] for row in manifest["files"])
    summary = json.loads((root / "summary.json").read_text())
    handoff_data = (root / "handoff.json").read_bytes()
    assert sha(handoff_data) == summary["handoff_sha256"]
    handoff = json.loads(handoff_data)
    bundle = root / summary["archive"]["path"]
    assert bundle.stat().st_size == summary["archive"]["bytes"]
    assert sha(bundle.read_bytes()) == summary["archive"]["sha256"]
    expected = {row["path"]: row for row in handoff["archive_files"]}
    assert len(expected) == len(handoff["archive_files"])
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == summary["archive"]["members"]
        assert set(names) == set(expected) | {"handoff.json"}
        for name, row in expected.items():
            data = archive.read(name)
            assert len(data) == row["size"] and sha(data) == row["sha256"], name
        assert archive.read("handoff.json") == handoff_data
        assert sha(archive.read("rama_motion.before.gd")) == handoff["canonical_sha256"]
    if args.native:
        for relative, digest in summary["native_source_pins"].items():
            assert sha((args.native / relative).read_bytes()) == digest, relative
    assert summary["status"] == "OPEN"
    assert summary["acceptance"]["runtime_promoted"] is False
    print(json.dumps({"verified": True, "archive_files": manifest["file_count"],
                      "zip_members": summary["archive"]["members"],
                      "current_native_checked": bool(args.native),
                      "motion_issue": "OPEN", "prototypes_accepted": 0}))


if __name__ == "__main__":
    main()
