#!/usr/bin/env python3
"""Independent analytic UV derivatives; no production asset or candidate writes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

NATIVE_ROOT = Path(__file__).resolve().parents[4]
ART = NATIVE_ROOT / "art/hero-rama-tangents"
sys.path.insert(0, str(ART))
from mikk_frames import NativeMikk, diagnose, strict_vertex_frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if not args.report.is_absolute() or args.report.exists():
        parser.error("Require a fresh absolute report")
    native = NativeMikk(args.library)
    p = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [-1, 0, 0]], dtype=np.float32)
    n = np.tile(np.array([0, 0, 1], dtype=np.float32), (4, 1))
    uv = np.array([[0, 0], [1, 0], [0, 1], [1, 0]], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    original = [x.tobytes() for x in (p, n, uv, indices)]
    checks = []
    # Analytically: the first UV chart has dP/du=+X,dP/dv=+Y;
    # the second has dP/du=-X,dP/dv=+Y. Both normals are+Z.
    result = diagnose(native, p, n, uv, indices)
    expected = np.array([[1, 0, 0, 1]] * 3 + [[-1, 0, 0, -1]] * 3, dtype=np.float32)
    assert np.allclose(result["corner_tangents"], expected, atol=1e-6, rtol=0)
    assert result["summary"]["handednessConflictVertices"] == 2
    rejected = False
    try:
        strict_vertex_frames(native, p, n, uv, indices)
    except ValueError:
        rejected = True
    assert rejected and not result["compatible"]
    checks.append({"name": "two_shared_vertices_keep_analytic_opposite_corner_frames_and_reject_collapse",
                   "passed": True, "actual_corner_frames": result["corner_tangents"].tolist()})
    # Explicitly author BOTH shared vertices as seam duplicates, without averaging.
    split_p = np.vstack([p, p[0], p[2]])
    split_n = np.tile(np.array([0, 0, 1], dtype=np.float32), (6, 1))
    split_uv = np.vstack([uv, uv[0], uv[2]])
    split_indices = np.array([0, 1, 2, 4, 5, 3], dtype=np.uint32)
    split = strict_vertex_frames(native, split_p, split_n, split_uv, split_indices)
    assert np.allclose(split, expected, atol=1e-6, rtol=0)
    checks.append({"name": "explicit_two_vertex_seam_split_preserves_distinct_frames", "passed": True})
    # Independent 45-degree tangent in a plane containing the Z axis.
    a = np.sqrt(0.5)
    rotated_p = np.array([[0, 0, 0], [a, a, 0], [0, 0, 1]], dtype=np.float32)
    rotated_n = np.tile(np.array([a, -a, 0], dtype=np.float32), (3, 1))
    rotated_uv = np.array([[0, 0], [1, 0], [0, 1]], dtype=np.float32)
    tangent = strict_vertex_frames(native, rotated_p, rotated_n, rotated_uv,
                                   np.array([0, 1, 2], dtype=np.uint32))
    assert np.allclose(tangent, [a, a, 0, 1], atol=1e-6, rtol=0)
    checks.append({"name": "rotated_plane_matches_independent_closed_form_derivative",
                   "passed": True, "expected": [a, a, 0, 1]})
    mixed = diagnose(native, p[:3], n[:3], uv[:3],
                     np.array([0, 1, 2, 0, 0, 0], dtype=np.uint32))
    assert np.allclose(mixed["corner_tangents"][:3], [1, 0, 0, 1], atol=1e-6, rtol=0)
    assert np.isnan(mixed["corner_tangents"][3:]).all() and not mixed["compatible"]
    assert mixed["summary"]["degenerateGeometryFaces"] == 1
    checks.append({"name": "degenerate_triangle_is_unresolved_without_contaminating_analytic_clean_triangle",
                   "passed": True})
    assert all(x.tobytes() == before for x, before in zip((p, n, uv, indices), original))
    report = {"passed": True, "checks": checks, "input_arrays_unchanged": True,
              "binary_sha256": hashlib.sha256(args.library.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Four independent analytic corner-domain properties only. No production GLB rewrite, renderer, source-equivalence or art-quality inference."}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "properties": len(checks)}))


if __name__ == "__main__":
    main()
