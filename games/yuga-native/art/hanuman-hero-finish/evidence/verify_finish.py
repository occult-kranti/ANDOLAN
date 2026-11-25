#!/usr/bin/env python3
"""Compare the exported art, rig, action clocks and the model actually shipped in the game ZIP."""

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile
import numpy as np

PACK = Path(__file__).resolve().parents[1]
NATIVE = PACK.parents[1]
REPO = NATIVE.parents[1]
BASE = NATIVE / "art/four-hero-motion/models/hanuman.glb"
FINAL = PACK / "models/hanuman-enhanced.glb"
GAME = NATIVE.parent / "yuga-rust"
ARCHIVE = GAME / "downloads/yuga-rust-confluence.zip"
KIT = NATIVE / "assets/design/hanuman-ability-kit.json"
sys.path.insert(0, str(NATIVE / "tools/hanuman-review"))
from audit_glb import Payload, audit as geometry_audit
from tail_curves import audit as tail_audit


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(path):
    raw = path.read_bytes()
    data = geometry_audit(raw)
    tail = tail_audit(raw)
    doc = Payload(raw).document
    materials = [m.get("name", "") for m in doc["materials"]]
    primitives = [p for mesh in doc["meshes"] for p in mesh["primitives"]]
    return {
        "source": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else path.name,
        "sha256": sha(raw),
        "bytes": len(raw),
        "triangles": data["triangles"],
        "vertices": sum(doc["accessors"][p["attributes"]["POSITION"]]["count"] for p in primitives),
        "skinned_primitives": data["skinned_primitives"],
        "joints": len(data["joint_names"][0]),
        "materials": materials,
        "images": [i["name"] for i in data["images"]],
        "durations_s": {a["name"]: round(a["duration_s"], 6) for a in data["animations"]},
        "tail_curve_sha256": tail["tail_curve_sha256"],
        "tail_joint_names": tail["joints"],
        "tail_weighted_vertices": tail["weighted_vertices"],
    }


def accessor_data(payload, index):
    acc = payload.document["accessors"][index]
    dtypes = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
    widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
    kind = np.dtype(dtypes[acc["componentType"]])
    width = widths[acc["type"]]
    view, data = payload.view(acc["bufferView"])
    arr = np.ndarray(
        (acc["count"], width),
        kind,
        buffer=data,
        offset=acc.get("byteOffset", 0),
        strides=(view.get("byteStride", width * kind.itemsize), kind.itemsize),
    )
    return arr


def data_hash(payload, index):
    return sha(accessor_data(payload, index).tobytes())


def curve_hashes(payload):
    result = {}
    doc = payload.document
    for action in doc["animations"]:
        for c in action["channels"]:
            joint = doc["nodes"][c["target"]["node"]]["name"]
            key = (action["name"], joint, c["target"]["path"])
            s = action["samplers"][c["sampler"]]
            result[key] = (
                data_hash(payload, s["input"]),
                s.get("interpolation", "LINEAR"),
                data_hash(payload, s["output"]),
            )
    return result


def original_geometry(old, new):
    count = 0
    moved = {}
    facial_materials = {
        "Vanara · painted copper anatomy",
        "Eyelids · roasted umber",
        "Face · warm recessed lines",
    }
    for i, mesh in enumerate(old.document["meshes"]):
        for j, p in enumerate(mesh["primitives"]):
            q = new.document["meshes"][i]["primitives"][j]
            material = old.document["materials"][p["material"]]["name"]
            positions = accessor_data(old, p["attributes"]["POSITION"])
            mask = (
                (np.abs(positions[:, 0]) <= 0.119)
                & (positions[:, 1] >= 1.704)
                & (positions[:, 1] <= 1.881)
                & (positions[:, 2] >= 0.184)
            )
            for name, idx in {"indices": p["indices"], **p["attributes"]}.items():
                other = q["indices"] if name == "indices" else q["attributes"][name]
                if material in facial_materials and name in ("POSITION", "NORMAL", "TANGENT"):
                    prev, cur = accessor_data(old, idx), accessor_data(new, other)
                    delta = np.linalg.norm(cur - prev, axis=1)
                    tol = 1e-7 if name == "POSITION" else 1e-4
                    assert (
                        np.max(delta[~mask], initial=0.0) < tol
                    ), f"Edit extends beyond muzzle: {material} {name}"
                    if name == "POSITION":
                        assert delta.max() <= 0.068, f"Unexpected facial displacement: {material}"
                        moved[material] = {
                            "vertices": int(np.sum(delta > 1e-6)),
                            "max_m": round(float(delta.max()), 6),
                        }
                else:
                    assert data_hash(old, idx) == data_hash(new, other), "Original geometry changed: " + name
            count += 1
    assert set(moved) == facial_materials and all(
        v["vertices"] > 0 for v in moved.values()
    ), "Missing localized muzzle change"
    return {"topology_weights_uvs_preserved_for_primitives": count, "localized_face_edits": moved}


def package_check(old_sha, expected, archive):
    with ZipFile(archive) as zf:
        assert zf.testzip() is None
        names = zf.namelist()
        entry = next(n for n in names if n.endswith("yuga-rust.html"))
        html = zf.read(entry)
        payload = json.loads(
            re.search(rb'<script id="payload" type="application/json">(.*?)</script>', html, re.S).group(1)
        )
        glbs = {}
        for name, encoded in payload["blobs"].items():
            raw = base64.b64decode(encoded, validate=True)
            if raw.startswith(b"glTF"):
                glbs[name] = sha(raw)
        for name in names:
            if name.endswith(".glb"):
                glbs["archive/" + name] = sha(zf.read(name))
    assert (
        glbs["hero"] == expected and old_sha not in glbs.values() and list(glbs.values()).count(expected) == 1
    ), "Incorrect/duplicated Hanuman in release"
    kit = json.loads(KIT.read_text())["abilities"]
    assert payload["kit"]["abilities"] == kit, "Shipped abilities differ from native gameplay clock"
    return {
        "archive": str(archive.relative_to(REPO)),
        "archive_sha256": sha(archive.read_bytes()),
        "document_sha256": sha(html),
        "bound_glb_digests": glbs,
        "ability_clocks": [
            {"id": a["id"], "clip": a["motion"], "cooldown": a["cooldown_s"], "timing": a["timing"]}
            for a in kit
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline", action="store_true", help="Inspect the frozen four-character Hanuman before sculpting"
    )
    parser.add_argument(
        "--geometry-only", action="store_true", help="Compare the finished GLB before release packaging"
    )
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--model", type=Path, default=FINAL, help="Candidate or integrated GLB")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    old = inspect(BASE)
    report = {"baseline": old, "verifier_sha256": sha(Path(__file__).read_bytes())}
    if not args.baseline:
        model = args.model.resolve()
        new = inspect(model)
        report["enhanced"] = new
        previous, current = Payload(BASE.read_bytes()), Payload(model.read_bytes())
        a, b = previous.document, current.document
        assert (
            old["sha256"] != new["sha256"]
            and new["triangles"] > old["triangles"]
            and new["vertices"] > old["vertices"]
        ), "No added sculpt geometry"
        assert (
            a["skins"] == b["skins"] and old["joints"] == new["joints"] == 167
        ), "Changed skin binding or joint count"
        before, after = curve_hashes(previous), curve_hashes(current)
        assert (
            before.keys() == after.keys() and old["durations_s"] == new["durations_s"]
        ), "Existing clips, paths or durations changed"
        assert all(v[:2] == after[k][:2] for k, v in before.items()), "Key times or interpolation changed"
        differences = sorted(k for k in before if before[k][2] != after[k][2])
        expected = [("mountain_pulse", f"tail_{i:02}", "rotation") for i in range(1, 5)]
        assert differences == expected, f"Unexpected motion edits: {differences}"
        report["comparison"] = {
            "added_triangles": new["triangles"] - old["triangles"],
            "added_vertices": new["vertices"] - old["vertices"],
            "original_surfaces": original_geometry(previous, current),
            "unchanged_key_times": len(before),
            "modified_curves": differences,
        }
        if not args.geometry_only:
            report["release"] = package_check(old["sha256"], new["sha256"], args.archive.resolve())
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
