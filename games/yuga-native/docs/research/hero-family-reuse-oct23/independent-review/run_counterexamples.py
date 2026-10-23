"""Bounded independent actual-GLB intake probes; never changes donor/product files."""
import argparse
import copy
import hashlib
import importlib.util
import json
import struct
import time
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(project, output):
    output.mkdir(parents=True, exist_ok=True)
    tool = project / "tools/hero-family-reuse/intake.py"
    spec = importlib.util.spec_from_file_location("independent_intake", tool)
    intake = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intake)
    manifest_path = project / "docs/research/hero-family-reuse-oct23/rama-family-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source = project / intake.DONOR
    raw = source.read_bytes()
    json_length, _ = struct.unpack_from("<II", raw, 12)
    original = json.loads(raw[20:20 + json_length])
    remainder = raw[20 + json_length:]
    results = []

    def fixture(name, mutate, expected):
        doc = copy.deepcopy(original)
        tail = bytearray(remainder)
        detail = mutate(doc, tail)
        encoded = json.dumps(doc, separators=(",", ":")).encode()
        encoded += b" " * (-len(encoded) % 4)
        data = struct.pack("<4sII", b"glTF", 2, 20 + len(encoded) + len(tail))
        data += struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + tail
        path = output / (name + ".glb")
        path.write_bytes(data)
        started = time.monotonic()
        try:
            verdict = intake.compatible(manifest, "arjuna", path, expected_source_sha=digest(path))
            result = {"ok": verdict["ok"], "errors": verdict["errors"], "exception": None}
        except Exception as exc:
            result = {"ok": False, "errors": [], "exception": type(exc).__name__ + ": " + str(exc)}
        results.append({"name": name, "expected": expected, "mutation": detail,
                        "fixture_path": str(path), "fixture_sha256": digest(path),
                        "elapsed_seconds": time.monotonic() - started, **result,
                        "false_accept": result["ok"] and expected == "reject"})

    def mesh_node(doc):
        return next(n for n in doc["nodes"] if n.get("name") == "RamaHero")

    def primitive(doc):
        return doc["meshes"][mesh_node(doc)["mesh"]]["primitives"][0]

    def binary_float(doc, tail, accessor_index, value):
        entry = doc["accessors"][accessor_index]
        view = doc["bufferViews"][entry["bufferView"]]
        offset = 8 + view.get("byteOffset", 0) + entry.get("byteOffset", 0)
        struct.pack_into("<f", tail, offset, value)
        return {"accessor": accessor_index, "component": 0, "value": str(value)}

    fixture("bone-order", lambda d, t: (d["skins"][0]["joints"].__setitem__(slice(1, 3), list(reversed(d["skins"][0]["joints"][1:3]))), "swap skin.joints[1:3]")[1], "reject")

    def detach_joint(d, t):
        child = d["skins"][0]["joints"][1]
        parent = next(n for n in d["nodes"] if child in n.get("children", []))
        parent["children"].remove(child)
        return {"joint_detached": child}
    fixture("bone-parent", detach_joint, "reject")

    def rest_shift(d, t):
        node = d["nodes"][d["skins"][0]["joints"][0]]
        translation = node.setdefault("translation", [0, 0, 0])
        translation[0] += .02
        return "root translation.x += 0.02"
    fixture("bone-rest", rest_shift, "reject")
    fixture("skin-bind", lambda d, t: binary_float(d, t, d["skins"][0]["inverseBindMatrices"], 2.0), "reject")
    fixture("material-name", lambda d, t: d["materials"][4].update(name="UNREVIEWED SKIN") or "materials[4].name changed", "reject")
    fixture("mesh-unskinned", lambda d, t: {"removed_skin": mesh_node(d).pop("skin")}, "reject")
    fixture("mesh-missing-joints", lambda d, t: {"removed_JOINTS_0": primitive(d)["attributes"].pop("JOINTS_0")}, "reject")
    fixture("mesh-missing-weights", lambda d, t: {"removed_WEIGHTS_0": primitive(d)["attributes"].pop("WEIGHTS_0")}, "reject")

    def invalid_joints(d, tail):
        index = primitive(d)["attributes"]["JOINTS_0"]
        entry = d["accessors"][index]
        view = d["bufferViews"][entry["bufferView"]]
        offset = 8 + view.get("byteOffset", 0) + entry.get("byteOffset", 0)
        fmt = {5121: "B", 5123: "H"}[entry["componentType"]]
        value = 255 if fmt == "B" else 65535
        struct.pack_into("<" + fmt, tail, offset, value)
        return {"JOINTS_0_accessor": index, "first_index": value, "skin_joint_count": 164}
    fixture("mesh-invalid-joint-index", invalid_joints, "reject")
    fixture("mesh-displaced", lambda d, t: mesh_node(d).update(translation=[50, 0, 0]) or "RamaHero translation = [50,0,0]", "reject")

    def material_swap(d, t):
        p = primitive(d)
        before = p["material"]
        p["material"] = (before + 1) % len(d["materials"])
        return {"surface_material_before": before, "surface_material_after": p["material"]}
    fixture("mesh-material-role", material_swap, "reject")

    def extra_anatomy(d, t):
        new_index = len(d["nodes"])
        d["nodes"].append({"name": "HanumanTailUnreviewed", "mesh": mesh_node(d)["mesh"], "skin": 0})
        d["scenes"][d.get("scene", 0)]["nodes"].append(new_index)
        return {"new_mesh_node": new_index, "name": "HanumanTailUnreviewed", "extra_anatomy_argument": False}
    fixture("mesh-extra-anatomy", extra_anatomy, "reject")
    # JSON 1e999 is parsed as infinity by Python, without non-standard NaN spelling.
    fixture("mesh-nonfinite-transform", lambda d, t: mesh_node(d).update(matrix=[float("inf")] + [0] * 15) or "RamaHero matrix[0] = Infinity", "reject")
    fixture("rest-nonfinite", lambda d, t: d["nodes"][d["skins"][0]["joints"][0]].update(translation=[float("inf"), 0, 0]) or "root translation.x = Infinity", "reject")
    fixture("bind-nonfinite", lambda d, t: binary_float(d, t, d["skins"][0]["inverseBindMatrices"], float("nan")), "reject")

    requests = [("accepted-canonical", {"source": source}),
                ("unknown-socket", {"sockets": ["mace_grip"]}),
                ("unknown-motion", {"motions": ["mace_slam"]}),
                ("weapon", {"weapon": "mace"}),
                ("extra-anatomy-declared", {"extra_anatomy": True}),
                ("finished-claim", {"finished": True}),
                ("wrong-source-sha", {"source": source, "expected_source_sha": "0" * 64})]
    for name, arguments in requests:
        verdict = intake.compatible(manifest, "arjuna", **arguments)
        results.append({"name": name, "expected": "accept-authoring-only" if name == "accepted-canonical" else "reject", **verdict})
    changed_manifest = copy.deepcopy(manifest)
    changed_manifest["source_pins"][0]["sha256"] = "0" * 64
    results.append({"name": "source-pin-drift", "expected": "reject", **intake.compatible(changed_manifest, "arjuna")})
    report = {"schema_version": 1, "scope": "Independent actual-GLB authoring intake counterexamples; no renderer, new hero art or roster acceptance.",
              "intake_path": str(tool), "intake_sha256": digest(tool), "manifest_sha256": digest(manifest_path),
              "donor_sha256": digest(source), "generator_sha256": digest(__file__),
              "case_count": len(results), "false_accept_count": sum(r.get("false_accept", False) for r in results), "cases": results}
    (output / "counterexamples.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"case_count": len(results), "false_accept_count": report["false_accept_count"], "report": str(output / "counterexamples.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.project.resolve(), args.output.resolve())
