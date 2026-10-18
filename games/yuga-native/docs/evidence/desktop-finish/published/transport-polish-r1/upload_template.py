#!/usr/bin/env python3
"""Exact existing bytes -> fixed draft assets. No build, execution or publication."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import urllib.parse

REPO = "occult-kranti/ANDOLAN"
RELEASE_ID = None  # Await the separately created successor draft.
PART_COUNTS = None  # Await exact qualified five-asset census.
TAG = "yuga-desktop-polish-2026-10-18"
TARGET = "85d5831dd8586a264caa93a7ba4625d1ec0b7f21"
MANIFEST_SHA256 = "@@MANIFEST_SHA256@@"
NAMES = (
    "yuga-native-linux-x86_64.zip", "yuga-native-windows-x86_64.zip",
    "native-export-manifest.json", "native-package-manifest.json", "SHA256SUMS.txt",
)
CHUNK_LIMIT = 48 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_bound():
    require(isinstance(RELEASE_ID, int) and not isinstance(RELEASE_ID, bool)
            and RELEASE_ID > 0 and RELEASE_ID != 416367666, "UNBOUND: new draft ID required")
    require(isinstance(PART_COUNTS, tuple) and len(PART_COUNTS) == 5
            and all(isinstance(n, int) and n > 0 for n in PART_COUNTS), "UNBOUND: qualified part census required")
    require(isinstance(MANIFEST_SHA256, str) and len(MANIFEST_SHA256) == 64
            and all(c in "0123456789abcdef" for c in MANIFEST_SHA256), "UNBOUND: exact generated manifest required")


def read_manifest(path):
    require_bound()
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, "manifest digest")
    manifest = json.loads(raw)
    require(manifest["schema"] == 1 and manifest["repository"] == REPO, "manifest identity")
    require(manifest["release_id"] == RELEASE_ID and manifest["tag"] == TAG
            and manifest["target"] == TARGET, "manifest release identity")
    require(manifest["transport_branch"] == "transport/yuga-desktop-polish-2026-10-18-r1"
            and manifest["chunk_limit"] == CHUNK_LIMIT, "transport identity")
    require(tuple(a["name"] for a in manifest["assets"]) == NAMES, "exact asset allowlist")
    paths = [p["path"] for a in manifest["assets"] for p in a["parts"]]
    require(len(paths) == sum(PART_COUNTS) and len(set(paths)) == sum(PART_COUNTS), "exact qualified payload census")
    for i, asset in enumerate(manifest["assets"]):
        require(len(asset["parts"]) == PART_COUNTS[i], "part count")
        require(sum(p["size"] for p in asset["parts"]) == asset["size"], "part lengths")
        for part in asset["parts"]:
            path = PurePosixPath(part["path"])
            require(not path.is_absolute() and ".." not in path.parts
                    and str(path) == part["path"] and path.parts[0] == "transport", "part path")
            require(0 < part["size"] <= CHUNK_LIMIT, "part size")
    return manifest


def verify_streams(manifest, reader, output=None):
    """Shared verifier: reader returns a context manager containing a binary stream."""
    verified = []
    for asset in manifest["assets"]:
        total = 0
        digest = hashlib.sha256()
        sink = (output / asset["name"]).open("xb") if output else contextlib.nullcontext()
        with sink as dst:
            for part in asset["parts"]:
                part_total = 0
                part_digest = hashlib.sha256()
                with reader(part) as src:
                    while block := src.read(1024 * 1024):
                        part_total += len(block)
                        require(part_total <= part["size"], "oversized part: " + part["path"])
                        part_digest.update(block)
                        digest.update(block)
                        total += len(block)
                        if dst is not None:
                            dst.write(block)
                require(part_total == part["size"] and part_digest.hexdigest() == part["sha256"],
                        "part bytes: " + part["path"])
        require(total == asset["size"] and digest.hexdigest() == asset["sha256"],
                "assembled bytes: " + asset["name"])
        verified.append({k: asset[k] for k in ("name", "size", "sha256")})
    return verified


def local_reader(root):
    root = root.resolve(strict=True)
    def reader(part):
        path = root / part["path"]
        require(not path.is_symlink() and path.is_file(), "regular part file")
        require(path.resolve(strict=True).is_relative_to(root), "part containment")
        return path.open("rb")
    return reader


def verify_output(manifest, output):
    require(not output.is_symlink() and output.is_dir(), "output directory")
    require({p.name for p in output.iterdir()} == set(NAMES), "exact output files")
    for asset in manifest["assets"]:
        p = output / asset["name"]
        require(not p.is_symlink() and p.is_file() and p.stat().st_size == asset["size"], "output size")
        h = hashlib.sha256()
        with p.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(block)
        require(h.hexdigest() == asset["sha256"], "output digest")


def check_asset(actual, expected):
    require(actual.get("name") == expected["name"], "asset name")
    require(actual.get("size") == expected["size"], "asset size")
    require(actual.get("state") == "uploaded", "asset state")
    require(actual.get("digest") == "sha256:" + expected["sha256"], "asset digest")
    require(isinstance(actual.get("id"), int) and actual["id"] > 0, "asset id")


def check_release(release, manifest):
    require_bound()
    require(release.get("id") == RELEASE_ID and release.get("draft") is True,
            "fixed draft release required")
    require(release.get("tag_name") == TAG and release.get("target_commitish") == TARGET,
            "tag/source mismatch")
    require(release.get("prerelease") is True, "prerelease required")
    expected = {a["name"]: a for a in manifest["assets"]}
    found = {}
    for asset in release.get("assets", []):
        name = asset.get("name")
        require(name in expected and name not in found, "unexpected/duplicate asset")
        check_asset(asset, expected[name])
        found[name] = asset
    return found


def api(arguments):
    # Token is inherited by gh, never read, copied or printed by this program.
    result = subprocess.run(["gh", "api", *arguments], check=True, stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def upload(manifest, output, call_api=api):
    require_bound()
    verify_output(manifest, output)
    endpoint = f"repos/{REPO}/releases/{RELEASE_ID}"
    for expected in manifest["assets"]:
        found = check_release(call_api([endpoint]), manifest)
        if expected["name"] in found:
            continue
        url = (f"https://uploads.github.com/repos/{REPO}/releases/{RELEASE_ID}/assets?"
               + urllib.parse.urlencode({"name": expected["name"]}))
        actual = call_api(["--method", "POST", url, "--input", str(output / expected["name"]),
                           "--header", "Content-Type: application/octet-stream"])
        check_asset(actual, expected)
    final = call_api([endpoint])
    found = check_release(final, manifest)
    require(set(found) == set(NAMES), "incomplete release assets")
    receipt = {"repository": REPO, "release_id": RELEASE_ID, "draft": True,
               "tag": TAG, "target": TARGET, "manifest_sha256": MANIFEST_SHA256,
               "transport_commit": os.environ.get("GITHUB_SHA"),
               "assets": [{k: found[n][k] for k in ("id", "name", "size", "digest", "state")}
                          for n in NAMES]}
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("verify", "upload"))
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = read_manifest(args.manifest)
    if args.mode == "verify":
        args.output.mkdir(parents=False, exist_ok=False)
        receipt = verify_streams(manifest, local_reader(Path.cwd()), args.output)
        verify_output(manifest, args.output)
        print(json.dumps({"verified": receipt}, indent=2, sort_keys=True))
    else:
        require(os.environ.get("GITHUB_REPOSITORY") == REPO, "runner repository")
        require(os.environ.get("GITHUB_REF") == "refs/heads/transport/yuga-desktop-polish-2026-10-18-r1",
                "runner branch")
        require(os.environ.get("GITHUB_EVENT_NAME") == "push", "runner event")
        upload(manifest, args.output)


if __name__ == "__main__":
    main()
