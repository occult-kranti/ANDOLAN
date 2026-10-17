#!/usr/bin/env python3
"""Read-only skin normal-map evidence. Does not import or render the project."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(native):
    glb = native / "assets/heroes/rama-hero.glb"
    png = native / "assets/heroes/rama-hero_rama-warm-skin-normal.png"
    source = glb.read_bytes()
    size, kind = struct.unpack_from("<II", source, 12)
    assert kind == 0x4E4F534A
    document = json.loads(source[20:20 + size])
    bin_length, bin_kind = struct.unpack_from("<II", source, 20 + size)
    assert bin_kind == 0x004E4942
    binary = source[28 + size:28 + size + bin_length]
    materials = [m for m in document["materials"] if m.get("name") == "Rama warm skin"]
    assert len(materials) == 1
    skin = materials[0]
    texture = document["textures"][skin["normalTexture"]["index"]]
    image = document["images"][texture["source"]]
    view = document["bufferViews"][image["bufferView"]]
    offset = view.get("byteOffset", 0)
    embedded = binary[offset:offset + view["byteLength"]]
    assert embedded == png.read_bytes(), "Extracted external skin map differs from GLB image"
    pixels = np.asarray(Image.open(png).convert("RGB"))
    scale = float(skin["normalTexture"].get("scale", 1))
    xy = (pixels[:, :, :2].astype(np.float64) / 255.0 * 2.0 - 1.0) * scale
    angle = np.degrees(np.arcsin(np.sqrt(np.sum(xy * xy, axis=2))))
    uv_path = native / "docs/evidence/open-art-wave/uv/rama-baseline-domains.json"
    uv = json.loads(uv_path.read_text())
    assert uv["sourceSha256"] == digest(glb)
    domains = []
    for domain in uv["domains"]:
        if domain["material"] == "Rama warm skin":
            domains.append({k: domain[k] for k in ("mesh", "primitive", "meshName", "vertices", "triangles", "counts", "mikkSummary")})
    pins = {str(p.relative_to(native)): digest(p) for p in [
        glb, png, Path(str(glb) + ".import"), Path(str(png) + ".import"), uv_path,
        native / "scripts/production_lighting.gd", native / "scripts/hero_atmosphere.gd",
        native / "scripts/rama_surface_finish.gd",
    ]}
    return {
        "schema": 1,
        "kind": "read-only-skin-normal-map-inspection",
        "source_sha256": pins,
        "skin_material": skin,
        "texture_sampler": document["samplers"][texture["sampler"]],
        "external_equals_glb_embedded_image": True,
        "pixels": {"width": int(pixels.shape[1]), "height": int(pixels.shape[0]),
                   "rgb_min": pixels.min(axis=(0, 1)).tolist(), "rgb_max": pixels.max(axis=(0, 1)).tolist(),
                   "rgb_mean": pixels.mean(axis=(0, 1)).tolist()},
        "estimated_tangent_space_normal_angle_degrees": {str(q): float(np.percentile(angle, q)) for q in [0, 50, 95, 99, 100]},
        "angle_scope": "Estimate using texture XY scaled by GLB normal scale and reconstructed unit Z. Not an executed GPU-shader measurement.",
        "skin_domains_from_source_matched_mikk_evidence": domains,
        "limits": "No import, renderer, GPU state inspection, material mutation or runtime asset promotion. Image-space triangle patches remain a diagnosis pending ablation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.native.resolve())
    with args.report.open("x") as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write("\n")
