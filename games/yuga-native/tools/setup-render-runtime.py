#!/usr/bin/env python3
"""Restore the tested Debian 13 software renderer outside the source checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import urllib.request

PACKAGES = [
    ("pool/main/m/mesa/mesa-vulkan-drivers_25.0.7-2+deb13u1_amd64.deb", 14185752,
     "caf2f7d296b7522efe74e40a74bce762a3ce84c33b53b5e54e1248ac2e0a13a5"),
    ("pool/main/x/xorg-server/xvfb_21.1.16-1.3+deb13u3_amd64.deb", 3198040,
     "365da2b6c93339f34337c434a9489bb6411a240fa47b9f49693d3091745f28c2"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/workspace/tooling/native-render"))
    args = parser.parse_args()
    if platform.machine() != "x86_64" or 'VERSION_ID="13"' not in Path("/etc/os-release").read_text():
        raise RuntimeError("This tested runtime is for Debian 13 x86_64; qualify other platforms separately")
    root = args.root.resolve()
    checkout = Path(__file__).resolve().parents[3]
    if root.is_relative_to(checkout):
        raise ValueError("Install task-local runtime outside the source checkout")
    cache, runtime = root / "verified-archives", root / "runtime"
    cache.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    receipts = []
    for relative, length, expected in PACKAGES:
        archive = cache / Path(relative).name
        if not archive.exists():
            with urllib.request.urlopen("https://deb.debian.org/debian/" + relative, timeout=60) as response:
                contents = response.read(length + 1)
            if len(contents) != length or hashlib.sha256(contents).hexdigest() != expected:
                raise ValueError("Official package byte count or pinned digest mismatch")
            archive.write_bytes(contents)
        contents = archive.read_bytes()
        if len(contents) != length or hashlib.sha256(contents).hexdigest() != expected:
            raise ValueError("Cached package byte count or digest mismatch")
        subprocess.run(["dpkg-deb", "-x", str(archive), str(runtime)], check=True)
        receipts.append({"url": "https://deb.debian.org/debian/" + relative, "bytes": length, "sha256": expected})
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(runtime / "usr/lib/x86_64-linux-gnu")
    for binary in [runtime / "usr/bin/Xvfb", runtime / "usr/lib/x86_64-linux-gnu/libvulkan_lvp.so"]:
        result = subprocess.run(["ldd", str(binary)], env=environment, capture_output=True, text=True, check=True)
        if "not found" in result.stdout + result.stderr:
            raise RuntimeError("Required base-image libraries are missing: " + str(binary))
    subprocess.run([str(runtime / "usr/bin/Xvfb"), "-help"], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    report = {"passed": True, "platform": "Debian 13 x86_64", "packages": receipts,
        "verification_basis": "Exact hashes from Debian package indexes authenticated by apt using the system Debian archive keyring; checked again on every extraction",
        "scope": "Xvfb startup and linked-library availability; actual Vulkan rendering requires the separate capture command. Base image provides remaining dependencies."}
    (root / "setup-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "report": str(root / "setup-report.json"), "runtime": str(runtime)}))


if __name__ == "__main__":
    main()
