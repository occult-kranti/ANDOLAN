#!/usr/bin/env python3
"""Read-only comparison of recorded export inventories; no engine/network use."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def category(path):
    if path.endswith(".gdc"):
        return "compiled_script"
    if path.endswith(".gd.remap"):
        return "script_remap"
    if path.startswith(".godot/exported/") and path.endswith(".scn"):
        return "generated_exported_scene"
    if path.startswith(".godot/imported/") and path.endswith(".scn"):
        return "generated_imported_scene"
    if path.startswith(".godot/imported/") and path.endswith(".ctex"):
        return "imported_texture"
    if path.startswith(".godot/imported/") and path.endswith(".sample"):
        return "imported_audio"
    if path.endswith(".import"):
        return "import_descriptor"
    if path.endswith(".remap"):
        return "other_resource_remap"
    if path == "project.binary":
        return "exported_project_configuration"
    if path.startswith(".godot/"):
        return "other_generated_metadata"
    return "other_exported_resource"


def entry_map(pack):
    rows = pack["entries"]
    mapped = {row["path"]: row for row in rows}
    if len(rows) != len(mapped) or len(rows) != pack["entry_count"]:
        raise ValueError("Duplicate paths or inconsistent entry count")
    return mapped


def inventory_delta(local, public):
    added = sorted(public.keys() - local.keys())
    removed = sorted(local.keys() - public.keys())
    changed = []
    for path in sorted(local.keys() & public.keys()):
        a, b = local[path], public[path]
        if a["sha256"] != b["sha256"] or a["bytes"] != b["bytes"]:
            changed.append({
                "path": path,
                "category": category(path),
                "local": {key: a[key] for key in ("bytes", "sha256")},
                "public": {key: b[key] for key in ("bytes", "sha256")},
                "public_minus_local_bytes": b["bytes"] - a["bytes"],
            })
    return {
        "local_count": len(local), "public_count": len(public),
        "added_paths": added, "removed_paths": removed,
        "changed_count": len(changed),
        "unchanged_count": len(local.keys() & public.keys()) - len(changed),
        "changed": changed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--public", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    local = json.loads(args.local.read_text())
    public = json.loads(args.public.read_text())
    source_delta = inventory_delta(local["source"]["files"], public["source"]["files"])
    platforms = sorted(local["packs"].keys() | public["packs"].keys())
    packs = {}
    for platform in platforms:
        a, b = local["packs"][platform], public["packs"][platform]
        am, bm = entry_map(a), entry_map(b)
        row = inventory_delta(am, bm)
        row.update({
            "local_pack": {k: a[k] for k in ("sha256", "bytes", "format", "engine")},
            "public_pack": {k: b[k] for k in ("sha256", "bytes", "format", "engine")},
            "whole_pack_equal": a["sha256"] == b["sha256"] and a["bytes"] == b["bytes"],
            "public_minus_local_pack_bytes": b["bytes"] - a["bytes"],
            "public_minus_local_entry_payload_bytes": sum(x["bytes"] for x in bm.values()) - sum(x["bytes"] for x in am.values()),
            "category_counts_local": dict(sorted(Counter(category(p) for p in am).items())),
            "category_counts_public": dict(sorted(Counter(category(p) for p in bm).items())),
            "changed_category_counts": dict(sorted(Counter(x["category"] for x in row["changed"]).items())),
            "all_recorded_md5_checks_passed": all(x.get("stored_md5_verified") is True for x in [*am.values(), *bm.values()]),
        })
        packs[platform] = row
    source_equal = local["source"]["files"] == public["source"]["files"]
    script = Path(__file__).resolve()
    result = {
        "schema": 1,
        "kind": "local_public_export_manifest_comparison",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Read-only comparison of per-source and per-PCK-entry byte lengths and SHA-256 values in the two export manifests. No downloads, engine execution, imports, or resource mutation.",
        "script": {"path": str(script), "sha256": digest(script)},
        "inputs": {
            "local": {"path": str(args.local.resolve()), "sha256": digest(args.local), "git": local["git"], "godot_version": local["godot_version"]},
            "public": {"path": str(args.public.resolve()), "sha256": digest(args.public), "git": public["git"], "godot_version": public["godot_version"]},
        },
        "source": {
            "exact_file_records_equal": source_equal,
            "local_inventory_sha256": local["source"]["sha256"],
            "public_inventory_sha256": public["source"]["sha256"],
            **source_delta,
        },
        "packs": packs,
        "cross_platform": {
            label: {
                "linux_windows_pack_sha256_equal": data["packs"]["linux"]["sha256"] == data["packs"]["windows"]["sha256"],
                "linux_windows_entry_records_equal": entry_map(data["packs"]["linux"]) == entry_map(data["packs"]["windows"]),
            } for label, data in (("local", local), ("public", public))
        },
        "findings": {
            "source_inventory_identity": source_equal,
            "same_godot_version": local["godot_version"] == public["godot_version"],
            "same_pck_path_sets": all(not p["added_paths"] and not p["removed_paths"] for p in packs.values()),
            "all_differences_limited_to_generated_scenes": all(c["category"] in ("generated_exported_scene", "generated_imported_scene") for p in packs.values() for c in p["changed"]),
            "compiled_script_payloads_equal": all(not any(c["category"] == "compiled_script" for c in p["changed"]) and not p["added_paths"] and not p["removed_paths"] for p in packs.values()),
        },
        "limits": [
            "Generated-resource classification follows exact export paths and extensions. This comparison does not decode scene internals or attribute changed scene bytes to a specific serializer field.",
            "Equal source inventories and unchanged compiled scripts do not establish byte-for-byte or visual equivalence of changed imported/exported scenes. Parent separately reviews the actual public Linux package.",
            "This report reads export manifests. Independent public ZIP/PCK byte verification is recorded separately in public-verification.json; it is not rerun here.",
            "Different whole-PCK SHA-256 values are reported as factual build deltas, not automatic failures. Source identity refers to the 233 native runtime files, not equality of the two complete Git trees.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"report": str(args.report), "source_equal": source_equal, "source_files": len(local["source"]["files"]), "packs": {k: {f: p[f] for f in ("local_count", "public_count", "changed_count", "unchanged_count", "changed_category_counts", "public_minus_local_pack_bytes", "public_minus_local_entry_payload_bytes")} for k, p in packs.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
