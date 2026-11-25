#!/usr/bin/env python3
"""Inventory a pinned Khronos catalog from glTF JSON, model credits and terms."""
import argparse
import gzip
import hashlib
import io
import json
import os
import posixpath
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import urlopen

LIB = Path(__file__).resolve().parents[1]
PROJECT = "KhronosGroup/glTF-Sample-Assets"
REV = "e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea"
RAW = f"https://raw.githubusercontent.com/{PROJECT}/{REV}/"
TREE = f"https://api.github.com/repos/{PROJECT}/git/trees/{REV}?recursive=1"
BLOB = f"https://github.com/{PROJECT}/blob/{REV}/"
INDEX = "Models/model-index.json"
INPUTS = LIB / "evidence/model-inputs.json.gz"
OUTPUT = LIB / "data/models.json.gz"
REPORT = LIB / "evidence/model-coverage.json"


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def git_blob(b):
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def packed(obj):
    blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    result = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=result, mode="wb", mtime=0) as stream:
        stream.write(blob)
    return result.getvalue()


def retrieve(url):
    for attempt in range(3):
        try:
            with urlopen(url, timeout=45) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(0.5 * 2**attempt)


def refresh_inputs():
    tree = json.loads(retrieve(TREE))
    if tree["sha"] != REV or tree["truncated"]:
        raise ValueError("Incomplete or unexpected upstream Git tree")
    # Tree metadata contains names and identities only. Media binaries are never requested.
    files = {r["path"]: [r["sha"], r["size"]] for r in tree["tree"] if r["type"] == "blob"
             and (r["path"].startswith("Models/") or r["path"].startswith("LICENSES/"))}
    return {"project": PROJECT, "revision": REV, "url": TREE, "files": dict(sorted(files.items()))}


class Reader:
    def __init__(self, files, cache, offline):
        self.files, self.cache, self.offline = files, cache, offline

    def get(self, path):
        if path not in self.files:
            raise ValueError(f"Absent from the pinned tree: {path}")
        is_descriptor = path.endswith(".gltf") and "/glTF/" in path
        if not (is_descriptor or path.endswith(("/metadata.json", "/LICENSE.md")) or path == INDEX):
            raise ValueError(f"Unsupported bulk input type: {path}")
        expected_hash, expected_size = self.files[path]
        dest = self.cache / path
        if dest.is_file():
            blob = dest.read_bytes()
        else:
            if self.offline:
                raise FileNotFoundError(f"Missing offline cache file: {path}")
            blob = retrieve(RAW + quote(path))
        if len(blob) != expected_size or git_blob(blob) != expected_hash:
            raise ValueError(f"Git blob mismatch at {REV}: {path}")
        if not dest.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as f:
                f.write(blob)
                tmp = f.name
            os.replace(tmp, dest)
        return blob


def asset_stats(d):
    if str(d.get("asset", {}).get("version")) != "2.0":
        raise ValueError("Unsupported glTF descriptor version")
    counts = {k: len(d.get(k, [])) for k in ("meshes", "materials", "nodes", "skins",
              "animations", "scenes", "images", "textures", "buffers", "cameras")}
    counts["mesh_primitives"] = sum(len(m["primitives"]) for m in d.get("meshes", []))
    counts["mesh_nodes"] = sum("mesh" in n for n in d.get("nodes", []))
    counts["joints"] = len({n for s in d.get("skins", []) for n in s["joints"]})
    counts["joint_bindings"] = sum(len(s["joints"]) for s in d.get("skins", []))
    counts["animation_channels"] = sum(len(a["channels"]) for a in d.get("animations", []))
    counts["animation_samplers"] = sum(len(a["samplers"]) for a in d.get("animations", []))
    counts["declared_buffer_bytes"] = sum(b["byteLength"] for b in d.get("buffers", []))
    counts["inline_resources"] = sum(obj.get("uri", "").startswith("data:") for group in
                                     ("images", "buffers") for obj in d.get(group, []))
    clips = [a.get("name") for a in d.get("animations", [])]
    return {"counts": counts, "clips": clips,
            "scenes": [{"name": s.get("name"), "root_nodes": len(s.get("nodes", []))}
                       for s in d.get("scenes", [])], "default_scene": d.get("scene"),
            "extensions": d.get("extensionsUsed", []), "required_extensions": d.get("extensionsRequired", []),
            "animated_properties": sorted({c["target"]["path"] for a in d.get("animations", [])
                                           for c in a["channels"]}),
            "sampler_interpolations": sorted({s.get("interpolation", "LINEAR")
                                              for a in d.get("animations", []) for s in a["samplers"]})}


def quoted(path):
    return BLOB + quote(path)


def resolve_terms(folder, url, files):
    if urlsplit(url).scheme in ("http", "https"):
        return url
    path = posixpath.normpath(posixpath.join(folder, url))
    if path not in files:
        raise ValueError(f"Terms reference is absent from the pinned tree: {path}")
    return quoted(path)


def inspect(entry, reader):
    folder = "Models/" + entry["name"]
    metadata_path = folder + "/metadata.json"
    terms_path = folder + "/LICENSE.md"
    meta_bytes, terms_bytes = reader.get(metadata_path), reader.get(terms_path)
    meta = json.loads(meta_bytes)
    preview = folder + "/" + meta["screenshot"] if meta.get("screenshot") else None
    variants = {k: f"{folder}/{k}/{v}" for k, v in entry["variants"].items()}
    descriptor_path = variants.get("glTF")
    credits = []
    for split in meta.get("legal", []):
        credit = {k: split[k] for k in ("license", "spdx", "artist", "owner", "year", "what", "text") if k in split}
        if split.get("licenseUrl"):
            credit["terms_url"] = resolve_terms(folder, split["licenseUrl"], reader.files)
        credits.append(credit)
    licenses = list(dict.fromkeys(c.get("spdx") or c["license"] for c in credits))
    scope = [f"{c['what']} — {c['artist']} ({c.get('spdx') or c['license']})" for c in credits]
    asset = {"id": "khronos-gltf:" + entry["name"], "name": meta["name"], "kind": "3D model",
             "source_url": quoted(descriptor_path or metadata_path), "project": PROJECT, "revision": REV,
             "path": descriptor_path or metadata_path, "metadata_url": quoted(metadata_path),
             "metadata_sha256": sha256(meta_bytes), "license_url": quoted(terms_path),
             "license_sha256": sha256(terms_bytes), "license": " + ".join(licenses) or "unspecified",
             "licenses": licenses, "rights_note": ". ".join(scope) or "See the per-model terms.",
             "credits": credits, "author": ", ".join(dict.fromkeys(c["artist"] for c in credits if c.get("artist"))),
             "summary": meta.get("summary", ""), "tags": meta.get("tags", []),
             "variants": variants, "preview_url": RAW + quote(preview) if preview in reader.files else None,
             "evidence": "index-only", "counts": None, "clips": None, "extensions": None,
             "inspection_reason": "Canonical glTF JSON descriptor is absent from the pinned tree."}
    if descriptor_path and descriptor_path in reader.files:
        blob = reader.get(descriptor_path)
        asset.update(asset_stats(json.loads(blob)))
        asset.update(evidence="descriptor-inspected", sha256=sha256(blob), descriptor_bytes=len(blob))
        del asset["inspection_reason"]
    return asset


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", type=Path, default=Path.home() / ".cache/yuga-library/khronos" / REV)
    p.add_argument("--offline", action="store_true", help="require cached descriptor and metadata bytes")
    p.add_argument("--refresh-inputs", action="store_true", help="refetch and repin the exact Git tree manifest")
    p.add_argument("--verify", action="store_true", help="compare rebuilt inventory and coverage to the saved bytes")
    args = p.parse_args()
    outputs = {}
    if args.refresh_inputs:
        if args.offline:
            p.error("Refreshing the upstream Git tree requires network access")
        manifest = refresh_inputs()
        outputs[INPUTS] = packed(manifest)
    else:
        manifest = json.loads(gzip.decompress(INPUTS.read_bytes()))
    if manifest["revision"] != REV or manifest["project"] != PROJECT:
        raise ValueError("Unexpected manifest identity")
    reader = Reader(manifest["files"], args.cache, args.offline)
    catalog = reader.get(INDEX)
    entries = json.loads(catalog)
    with ThreadPoolExecutor(max_workers=12) as workers:
        models = list(workers.map(lambda e: inspect(e, reader), entries))
    names = {e["name"] for e in entries}
    folders = {p.split("/")[1] for p in reader.files if p.endswith("/metadata.json")}
    if len(names) != len(models) or names != folders:
        raise ValueError("Canonical catalog and model metadata folder set differ.")
    models.sort(key=lambda m: m["id"])
    done = [m for m in models if m["evidence"] == "descriptor-inspected"]
    uninspected = [m["id"] for m in models if m["evidence"] == "index-only"]
    coverage = {"project": PROJECT, "revision": REV, "source": quoted(INDEX),
                "index_sha256": sha256(catalog), "index_rows": len(entries),
                "distinct_metadata_directories": len(folders), "descriptor_inspected": len(done),
                "uninspected": uninspected, "models_with_previews_in_git_tree": sum(bool(m["preview_url"]) for m in models),
                "models_with_animations": sum(bool(m["counts"]["animations"]) for m in done),
                "models_with_skins": sum(bool(m["counts"]["skins"]) for m in done),
                "models_with_extension": sum(bool(m["extensions"]) for m in done),
                "animations": sum(len(m["clips"]) for m in done),
                "named_animations": sum(n is not None for m in done for n in m["clips"]),
                "credits": sum(len(m["credits"]) for m in models),
                "license_identifiers_by_model": dict(sorted(Counter(v for m in models for v in m["licenses"]).items())),
                "models_without_legal_entries": [m["id"] for m in models if not m["credits"]],
                "descriptor_input_bytes": sum(m["descriptor_bytes"] for m in done),
                "inline_resources_listed": sum(m["counts"]["inline_resources"] for m in done),
                "external_geometry_buffers_textures_or_previews_downloaded": 0,
                "scope": "glTF 2.0 JSON, official model metadata and per-model terms. Previews and binary variants are pinned tree references. Joint counts use distinct node indices per model. Missing clip names remain null."}
    outputs[OUTPUT] = packed(models)
    outputs[REPORT] = (json.dumps(coverage, indent=2, ensure_ascii=False) + "\n").encode()
    for path, blob in outputs.items():
        if args.verify:
            if path.read_bytes() != blob:
                p.exit(1, f"Regenerated bytes differ: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
    print(f"Inspected {len(done)}/{len(models)} glTF descriptors. {coverage['animations']} animations. "
          f"SHA-256 {sha256(outputs[OUTPUT])}")


if __name__ == "__main__":
    main()
