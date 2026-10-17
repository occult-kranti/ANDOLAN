#!/usr/bin/env python3
"""Build the staged CC0 cloth material, without network or Godot imports.

Requires Python 3, NumPy and Pillow. --check verifies exact reproducibility
without writing. This is an authoring tool, not a runtime dependency.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, __version__ as PILLOW_VERSION

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "art/open-art-wave"
SOURCE = ROOT / "source/microsoft-sheen-cloth"
TEXTURES = ROOT / "textures"
MATERIAL = ROOT / "materials/indigo-woven-cloth.tres"
REPEATS = 4
INDIGO_SRGB = np.array([49.0, 73.0, 148.0]) / 255.0
NORMAL_XY_STRENGTH = 0.28


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def srgb_to_linear(value: np.ndarray) -> np.ndarray:
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(value: np.ndarray) -> np.ndarray:
    return np.where(value <= 0.0031308, value * 12.92, 1.055 * value ** (1.0 / 2.4) - 0.055)


def png_bytes(array: np.ndarray) -> bytes:
    out = io.BytesIO()
    Image.fromarray(array).save(out, format="PNG", optimize=False, compress_level=9)
    return out.getvalue()


def output_candidates() -> tuple[dict[Path, bytes], dict]:
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    if manifest["asset_license"] != "CC0-1.0" or manifest["source_textures_bytes"] >= 10_000_000:
        raise ValueError("Unexpected source license or acquisition budget")
    for record in manifest["files"]:
        body = (SOURCE / record["file"]).read_bytes()
        if len(body) != record["bytes"] or digest(body) != record["sha256"]:
            raise ValueError("Source identity mismatch: " + record["file"])

    base = np.asarray(Image.open(SOURCE / "technicalFabricSmall_basecolor_256.png").convert("RGB"), dtype=np.float64) / 255.0
    normal = np.asarray(Image.open(SOURCE / "technicalFabricSmall_normal_256.png").convert("RGB"), dtype=np.float64) / 255.0
    orm = np.asarray(Image.open(SOURCE / "technicalFabricSmall_orm_256.png").convert("RGB"), dtype=np.float64) / 255.0
    if any(value.shape != (256, 256, 3) for value in (base, normal, orm)):
        raise ValueError("Expected the three pinned 256-pixel source tiles")

    # Original YUGA calibration: recolor in linear light, not gamma-space tint.
    # Reduce the technical sample's large diamond contrast; retain thread values.
    luminance = srgb_to_linear(base) @ np.array([0.2126, 0.7152, 0.0722])
    variation = np.clip((luminance / luminance.mean()) ** 0.18, 0.90, 1.10)
    albedo = np.rint(np.clip(linear_to_srgb(srgb_to_linear(INDIGO_SRGB) * variation[..., None]), 0, 1) * 255).astype(np.uint8)

    # glTF ORM G is linear roughness. R is AO; B is metallic and is not reused.
    roughness = np.rint((0.58 + 0.22 * orm[..., 1]) * 255).astype(np.uint8)
    normal_vector = normal * 2.0 - 1.0
    normal_vector /= np.linalg.norm(normal_vector, axis=2)[..., None]
    xy = normal_vector[..., :2] * NORMAL_XY_STRENGTH
    z = np.sqrt(np.maximum(0.0, 1.0 - np.sum(xy * xy, axis=2)))
    calibrated_normal = np.dstack((xy, z))
    normals = np.rint(np.clip(calibrated_normal * 0.5 + 0.5, 0, 1) * 255).astype(np.uint8)

    # Bake repetition to keep the existing secondary shader's identity UV contract.
    # These are repeated real source texels, not an upscale or new texture detail.
    arrays = {
        "indigo-woven-albedo.png": np.tile(albedo, (REPEATS, REPEATS, 1)),
        "indigo-woven-roughness.png": np.tile(roughness, (REPEATS, REPEATS)),
        "indigo-woven-normal.png": np.tile(normals, (REPEATS, REPEATS, 1)),
    }
    output = {TEXTURES / name: png_bytes(value) for name, value in arrays.items()}
    material = '''[gd_resource type="StandardMaterial3D" load_steps=4 format=3]

[ext_resource type="Texture2D" path="res://art/open-art-wave/textures/indigo-woven-albedo.png" id="1_albedo"]
[ext_resource type="Texture2D" path="res://art/open-art-wave/textures/indigo-woven-roughness.png" id="2_roughness"]
[ext_resource type="Texture2D" path="res://art/open-art-wave/textures/indigo-woven-normal.png" id="3_normal"]

[resource]
resource_local_to_scene = true
resource_name = "YUGA indigo woven cloth (CC0 adaptation)"
transparency = 0
shading_mode = 1
diffuse_mode = 0
specular_mode = 0
cull_mode = 2
vertex_color_use_as_albedo = false
albedo_color = Color(1, 1, 1, 1)
albedo_texture = ExtResource("1_albedo")
metallic = 0.0
metallic_specular = 0.5
roughness = 1.0
roughness_texture = ExtResource("2_roughness")
roughness_texture_channel = 0
normal_enabled = true
normal_scale = 1.0
normal_texture = ExtResource("3_normal")
texture_filter = 3
texture_repeat = true
uv1_scale = Vector3(1, 1, 1)
uv1_offset = Vector3(0, 0, 0)
uv2_scale = Vector3(1, 1, 1)
uv2_offset = Vector3(0, 0, 0)
'''
    output[MATERIAL] = material.encode()
    decoded_normals = normals.astype(np.float64) / 255.0 * 2.0 - 1.0
    report = {
        "schema": 1,
        "purpose": "Staged material candidate only; no runtime scene or mesh changes",
        "source_manifest_sha256": digest((ROOT / "source-manifest.json").read_bytes()),
        "source_revision": manifest["revision"],
        "texture_derivatives_license": "CC0-1.0",
        "authored_recipe": {
            "author": "YUGA contributors", "adaptation": "2026-10-17",
            "albedo_target_srgb_8bit": [49, 73, 148],
            "source_luminance_power": 0.18, "linear_variation_bounds": [0.9, 1.1],
            "roughness_from_orm_green": "0.58 + 0.22 * G",
            "source_normal_xy_scale": NORMAL_XY_STRENGTH,
            "normal_convention": "X+,Y+,Z+ tangent space; no V inversion",
            "baked_repeat_uv": [REPEATS, REPEATS], "resampling": "none; integer tile repetition",
        },
        "material_contract": {
            "candidate": "res://art/open-art-wave/materials/indigo-woven-cloth.tres",
            "allowed_existing_surface_names": ["Cobalt handwoven silk"],
            "preserve_surfaces": ["Cobalt lotus brocade", "Worked warm gold", "Swept black hair"],
            "secondary_motion": "Preserve existing ShaderMaterial owner and vertex masks; copy supported PBR inputs only",
            "filter": "linear mipmap; actual import mipmaps must be verified by root",
            "uv_transforms": "identity", "culling": "disabled, matching existing thin cloth shader",
        },
        "measured_uncompressed_texels": {
            "albedo_srgb_min": albedo.min(axis=(0, 1)).tolist(),
            "albedo_srgb_max": albedo.max(axis=(0, 1)).tolist(),
            "roughness_min": float(roughness.min() / 255),
            "roughness_max": float(roughness.max() / 255),
            "normal_length_min": float(np.linalg.norm(decoded_normals, axis=2).min()),
            "normal_length_max": float(np.linalg.norm(decoded_normals, axis=2).max()),
            "normal_xy_absolute_max": float(np.abs(decoded_normals[..., :2]).max()),
        },
        "memory_scope": {"dimensions_each": [1024, 1024], "texture_count": 3,
                         "conservative_rgba8_with_full_mip_chain_bytes": 16777216,
                         "actual_imported_vram": "UNMEASURED; depends on root import compression"},
        "outputs": [{"path": str(path.relative_to(PROJECT)), "bytes": len(body), "sha256": digest(body)} for path, body in output.items()],
        "not_established": ["historical Indian silk authenticity", "KHR_materials_sheen equivalence", "mesh tangent-frame repair", "native visual acceptance", "real-time hardware performance"],
    }
    output[ROOT / "build-manifest.json"] = (json.dumps(report, indent=2) + "\n").encode()
    return output, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare regenerated bytes; do not write")
    args = parser.parse_args()
    output, report = output_candidates()
    mismatches = []
    for path, body in output.items():
        if args.check:
            if not path.exists() or path.read_bytes() != body:
                mismatches.append(str(path.relative_to(PROJECT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
    print(json.dumps({"mode": "check" if args.check else "build", "files": len(output), "exact_mismatches": mismatches,
                      "source_license": "CC0-1.0", "pillow": PILLOW_VERSION, "numpy": np.__version__,
                      "texture_bytes": sum(item["bytes"] for item in report["outputs"] if item["path"].endswith(".png"))}, indent=2))
    return 1 if mismatches else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError) as error:
        print("Open-art build refused: " + str(error), file=sys.stderr)
        sys.exit(1)
