#!/usr/bin/env python3
"""Source-integrity, texture-domain and deterministic-build checks; no engine."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[4]
ROOT = PROJECT / "art/open-art-wave"
checks = []


def check(name, condition):
    checks.append({"name": name, "pass": bool(condition)})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    args_parser = argparse.ArgumentParser(description=__doc__)
    args_parser.add_argument("--report", type=Path)
    args = args_parser.parse_args()
    source = json.loads((ROOT / "source-manifest.json").read_text())
    build = json.loads((ROOT / "build-manifest.json").read_text())
    for record in source["files"]:
        path = ROOT / "source/microsoft-sheen-cloth" / record["file"]
        check(record["file"] + " original hash", sha(path) == record["sha256"])
        check(record["file"] + " original length", path.stat().st_size == record["bytes"])
    check("three image maps acquired below10MB", source["source_textures_bytes"] == 384181 < 10_000_000)
    check("source metadata exception preserved", all(item["license"].startswith("CC-BY-4.0") for item in source["files"] if item["file"] in ("metadata.json", "LICENSE.md")))
    check("image asset CC0 independently recorded", all(item["license"] == "CC0-1.0" for item in source["files"] if item["file"].endswith(".png")))
    check("no model downloaded", source["model_geometry_downloaded"] is False)
    for record in build["outputs"]:
        check(record["path"] + " derived hash", sha(PROJECT / record["path"]) == record["sha256"])
    arrays = {}
    for name in ("albedo", "roughness", "normal"):
        image = Image.open(ROOT / "textures" / ("indigo-woven-" + name + ".png"))
        check(name + " native dimensions", image.size == (1024, 1024))
        check(name + " opaque source domain", image.mode in ("RGB", "L"))
        value = np.asarray(image)
        arrays[name] = value
        tile = value[:256, :256]
        repeats = (4, 4, 1) if value.ndim == 3 else (4, 4)
        check(name + " exact integer repetition no resample", np.array_equal(value, np.tile(tile, repeats)))
    base = arrays["albedo"]
    check("indigo channels bounded", base[..., 0].min() >= 46 and base[..., 0].max() <= 52 and base[..., 1].min() >= 69 and base[..., 1].max() <= 77 and base[..., 2].min() >= 141 and base[..., 2].max() <= 155)
    check("roughness linear non-glossy interval", arrays["roughness"].min() / 255 >= 0.66 and arrays["roughness"].max() / 255 <= 0.80)
    normals = arrays["normal"].astype(float) / 255 * 2 - 1
    lengths = np.linalg.norm(normals, axis=2)
    check("normal quantization within1percent unit", lengths.min() > 0.99 and lengths.max() < 1.01)
    check("positive normal hemisphere", normals[..., 2].min() > 0.97)
    check("normal amplitude restrained", np.abs(normals[..., :2]).max() < 0.18)
    material = (ROOT / "materials/indigo-woven-cloth.tres").read_text()
    check("three file resource references", material.count('[ext_resource type="Texture2D"') == 3)
    check("fixture exact opaque material profile", all(line in material.splitlines() for line in ("transparency = 0", "shading_mode = 1", "diffuse_mode = 0", "specular_mode = 0", "cull_mode = 2", "vertex_color_use_as_albedo = false", "metallic = 0.0", "metallic_specular = 0.5", "texture_filter = 3", "texture_repeat = true", "roughness_texture_channel = 0")))
    spec = importlib.util.spec_from_file_location("material_builder", PROJECT / "tools/build-open-art-materials.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output, _ = module.output_candidates()
    check("all5 regenerated files byte identical", len(output) == 5 and all(path.read_bytes() == body for path, body in output.items()))
    # A corrupted acquired source is rejected before producing any derivatives.
    with tempfile.TemporaryDirectory(prefix="yuga-material-counterexample-") as temporary:
        copied = Path(temporary) / "open-art-wave"
        shutil.copytree(ROOT / "source", copied / "source")
        shutil.copy2(ROOT / "source-manifest.json", copied / "source-manifest.json")
        bad = copied / "source/microsoft-sheen-cloth/technicalFabricSmall_normal_256.png"
        bad.write_bytes(bad.read_bytes() + b"counterexample")
        module.ROOT = copied
        module.SOURCE = copied / "source/microsoft-sheen-cloth"
        refused = False
        try:
            module.output_candidates()
        except ValueError as error:
            refused = str(error) == "Source identity mismatch: technicalFabricSmall_normal_256.png"
        check("counterexample corrupt source refuses build", refused)
    report = {"schema": 1, "scope": "Python source-integrity/texture-domain/determinism only; no Godot import or art acceptance", "checks": checks, "passed": sum(item["pass"] for item in checks), "failed": sum(not item["pass"] for item in checks), "source_manifest_sha256": sha(ROOT / "source-manifest.json"), "build_manifest_sha256": sha(ROOT / "build-manifest.json"), "generator_sha256": sha(PROJECT / "tools/build-open-art-materials.py"), "verifier_sha256": sha(Path(__file__)), "unrun": ["Godot resource load/import", "mipmap/compression flags", "native same-camera day/night images", "hardware performance"]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "failed": report["failed"], "scope": report["scope"]}, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
