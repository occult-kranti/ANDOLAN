"""Fetch a pinned MIT meshoptimizer build; never run from the game's runtime.

Compile only while holding the team's exclusive heavy-work slot. All fetched
bytes are checked before the compiler is invoked. No system install is needed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

COMMIT = "7b2d4f4c817aea55d74dcd65d9763ac2ca608026"  # v0.24
FILES = {
    "src/meshoptimizer.h": "5e87787e43b0ae88878c7d9bb40ebeed79a63123d2f2b714420b66f864544366",
    "src/simplifier.cpp": "7d3dd0f1122ae13667bcc420ac565c709a927ed326cb8076c24ae5e0d1470c99",
    "src/allocator.cpp": "73f4397c469353c71f9c8dc78d96418c5045502302f606403c464d6ac45804fe",
    "LICENSE.md": "e4a26033e3551fb2722888949fbb41e77aee628e8e8f04dcffeee301aa7e5634",
}

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--fetch-only", action="store_true")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, expected in FILES.items():
        path = args.output / name
        if not path.exists():
            payload = urllib.request.urlopen(
                f"https://raw.githubusercontent.com/zeux/meshoptimizer/{COMMIT}/{name}", timeout=30
            ).read()
            if hashlib.sha256(payload).hexdigest() != expected:
                raise ValueError(f"Pinned source mismatch: {name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Existing pinned source mismatch: {name}")
    result = {"commit": COMMIT, "license": "MIT", "files": FILES}
    if not args.fetch_only:
        command = ["c++", "-std=c++11", "-O2", "-DNDEBUG", "-fPIC", "-shared",
                   str(args.output / "src/simplifier.cpp"), str(args.output / "src/allocator.cpp"),
                   "-o", str(args.output / "libmeshoptimizer.so")]
        subprocess.run(command, check=True)
        result["command"] = command
        result["librarySha256"] = hashlib.sha256((args.output / "libmeshoptimizer.so").read_bytes()).hexdigest()
    (args.output / "provenance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
