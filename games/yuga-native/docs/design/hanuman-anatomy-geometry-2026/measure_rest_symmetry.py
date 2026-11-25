#!/usr/bin/env python3
"""Measure an explicitly bounded Hanuman face ROI before skinning.

Nearest reflected neighbors are a geometric diagnostic, not vertex correspondence,
an anatomical rule or a deformed/animated result. Uses the existing GLB reader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "games/yuga-native/art/hero-rama-lod"))
from glb_lod import GLB

DEFAULT_SOURCE = ROOT / "games/yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb"
FACE_MATERIALS = (
    "Vanara · painted copper anatomy",
    "Eyes · warm sclera",
    "Face lines and pupil",
    "Eyes · dark amber iris",
    "Eyelids · roasted umber",
    "Ear · warm inner skin",
    "Face · warm recessed lines",
)


def nearest_distance_mm(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Map negative-X samples to +X and take nearest opposite-side distance."""
    reflect = left.copy()
    reflect[:, 0] *= -1
    distances = []
    for block in np.array_split(reflect, max(1, (len(reflect) + 127) // 128)):
        # Float64 distance avoids cancellation for millimetre-scale comparisons.
        diff = block[:, None, :] - right[None, :, :]
        distances.extend(np.sqrt(np.sum(diff * diff, axis=2).min(axis=1)) * 1000)
    return np.asarray(distances)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--output", type=Path, help="Optional JSON receipt")
    args = p.parse_args()
    glb = GLB(args.input)
    materials = glb.doc.get("materials", [])
    groups: dict[str, list[np.ndarray]] = {name: [] for name in FACE_MATERIALS}
    for _, _, primitive in glb.primitives():
        material = materials[primitive["material"]].get("name", "")
        if material in groups:
            points = glb.array(primitive["attributes"]["POSITION"]).astype(np.float64)
            # Explicit local-space ROI in glTF coordinates, not a semantic segmentation.
            keep = ((points[:, 1] >= 1.79) & (points[:, 1] <= 1.92) &
                    (np.abs(points[:, 0]) <= 0.14) & (points[:, 2] >= 0.0))
            groups[material].append(points[keep])
    rows = []
    for name, parts in groups.items():
        pts = np.concatenate(parts, axis=0) if parts else np.empty((0, 3))
        # Center-plane points lack a distinct anatomical partner; omit them.
        left = pts[pts[:, 0] < -0.001]
        right = pts[pts[:, 0] > 0.001]
        if not len(left) or not len(right):
            raise ValueError(f"{name}: missing left or right samples within ROI")
        d = nearest_distance_mm(left, right)
        rows.append({"material": name, "roi_vertices": len(pts),
                     "left_samples": len(left), "right_samples": len(right),
                     "nearest_reflected_distance_mm": {
                         "median": round(float(np.median(d)), 4),
                         "p95": round(float(np.percentile(d, 95)), 4),
                         "maximum": round(float(np.max(d)), 4)},
                     "left_within_0_5mm": round(float(np.mean(d <= .5)), 5)})
    try:
        source_path = str(args.input.resolve().relative_to(ROOT))
    except ValueError:
        source_path = str(args.input.resolve())
    report = {
        "source": source_path,
        "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "coordinate_space": "GLB mesh-local POSITION, glTF x/y/z; y up; before node transforms and skinning",
        "comparison": "reflect x across the local x=0 plane; nearest neighbor in the same material",
        "roi": {"y_min": 1.79, "y_max": 1.92, "abs_x_max": 0.14,
                "z_min": 0, "exclude_abs_x_lte": .001},
        "measurements": rows,
        "limits": ["The ROI is an approximate spatial window, not semantic face topology.",
                   "Nearest-neighbor matching is one-way and ignores vertex IDs, connectivity, UVs and weights.",
                   "This is not deformed or animated geometry; asymmetrical pose, hair, tail, gear and grip need visual review.",
                   "Distance is reported in millimetres using this asset's metre-scale coordinates."]}
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
