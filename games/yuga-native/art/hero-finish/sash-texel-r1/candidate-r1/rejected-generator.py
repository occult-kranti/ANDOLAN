"""Isolated UV correction for the original cross-body sash; never writes runtime assets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "art/hero-rama-lod"))
from glb_lod import GLB

SOURCE = ROOT / "art/hero-finish/s4-diadem-smooth/candidate-r2"
PINS = {
    "rama-hero.glb": "e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82",
    "rama-hero-mid.glb": "dfa9a41adab7cfd5c60416a66d2b95c4d1ab06d081b64ee7a9f5ff5c7744474b",
    "rama-hero-far.glb": "8b74504c07d38416032ea22e37061d69061baaf0b86e78dec27417c8927e39f9",
}
# One common mapping across LODs. Positive diagonal scaling preserves tangent
# directions/handedness; anisotropy is measured below, not described as perfect.
SCALE = np.array([0.25, 1.1875], dtype=np.float64)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def select_sash(g):
    matches = []
    for mi, pi, p in g.primitives():
        if g.doc["materials"][p["material"]].get("name") != "Cobalt handwoven silk":
            continue
        x = g.array(p["attributes"]["POSITION"])
        t = g.array(p["indices"]).reshape(-1, 3)
        _, weld = np.unique(np.round(x, 6), axis=0, return_inverse=True)
        wt = weld[t]
        edges = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
        count, labels = connected_components(coo_matrix(
            (np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
            shape=(int(weld.max()) + 1,) * 2), directed=False)
        for label in range(count):
            ids = np.flatnonzero(labels[weld] == label)
            lo, hi = x[ids].min(0), x[ids].max(0)
            if (1.02 < lo[1] < 1.08 and 1.49 < hi[1] < 1.56
                    and lo[2] > .05 and hi[2] < .21
                    and -.25 < lo[0] < -.18 and .20 < hi[0] < .27):
                touched = t[np.any(np.isin(t, ids), axis=1)]
                assert np.all(np.isin(touched, ids)), "sash shares a primitive boundary"
                matches.append((mi, pi, p, ids, touched, lo, hi))
    assert len(matches) == 1, f"expected one complete sash volume, found {len(matches)}"
    return matches[0]


def metric(x, uv, t):
    a, b = x[t[:, 1]] - x[t[:, 0]], x[t[:, 2]] - x[t[:, 0]]
    u, v = uv[t[:, 1]] - uv[t[:, 0]], uv[t[:, 2]] - uv[t[:, 0]]
    determinant = u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    ok = (abs(determinant) > 1e-9) & (np.linalg.norm(np.cross(a, b), axis=1) > 1e-9)
    a, b, u, v, determinant = a[ok], b[ok], u[ok], v[ok], determinant[ok]
    du = (a * v[:, 1, None] - b * u[:, 1, None]) / determinant[:, None]
    dv = (-a * v[:, 0, None] + b * u[:, 0, None]) / determinant[:, None]
    ratio = np.linalg.norm(dv, axis=1) / np.linalg.norm(du, axis=1)
    return {"nondegenerate_triangles": int(ok.sum()),
            "excluded_triangles": int((~ok).sum()),
            "v_over_u_metres_per_uv_p10_p50_p90": np.percentile(ratio, [10, 50, 90]).tolist()}


def build(name, pin, output):
    g = GLB(SOURCE / name)
    assert sha(g.raw) == pin, "input differs from reviewed smooth-crown source"
    mi, pi, p, ids, triangles, lo, hi = select_sash(g)
    accessor = g.doc["accessors"][p["attributes"]["TEXCOORD_0"]]
    assert accessor["componentType"] == 5126 and accessor["type"] == "VEC2"
    assert "sparse" not in accessor and "min" not in accessor and "max" not in accessor
    view = g.doc["bufferViews"][accessor["bufferView"]]
    uv = g.array(p["attributes"]["TEXCOORD_0"])
    candidate_uv = uv.copy()
    candidate_uv[ids] = (uv[ids].astype(float) * SCALE).astype("<f4")
    assert np.isfinite(candidate_uv).all()
    binary = bytearray(g.binary)
    allowed = np.zeros(len(binary), dtype=bool)
    for i in ids:
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + int(i) * view.get("byteStride", 8)
        binary[offset:offset + 8] = candidate_uv[i].astype("<f4").tobytes()
        allowed[offset:offset + 8] = True
    before = np.frombuffer(g.binary, dtype="u1")
    after = np.frombuffer(binary, dtype="u1")
    assert np.array_equal(before[~allowed], after[~allowed]), "unexpected non-UV mutation"
    raw = g.raw[:-len(g.binary)] + binary
    target = output / name
    target.write_bytes(raw)
    out = GLB(target)
    assert out.doc == g.doc and len(out.raw) == len(g.raw)
    assert np.array_equal(out.array(p["attributes"]["TEXCOORD_0"]), candidate_uv)
    x = g.array(p["attributes"]["POSITION"])
    return {"file": name, "input_sha256": pin, "output_sha256": sha(raw),
            "mesh": mi, "primitive": pi, "selected_vertices": len(ids),
            "selected_triangles": len(triangles), "bounds_m": [lo.tolist(), hi.tolist()],
            "changed_bytes": int((before != after).sum()),
            "outside_selected_uv_bytes_exact": True, "json_exact": True,
            "before": metric(x, uv, triangles), "after": metric(x, candidate_uv, triangles)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"schema": 1, "status": "inactive; private import and matched pixels required",
              "generator_sha256": sha(Path(__file__).read_bytes()),
              "scale_uv": SCALE.tolist(),
              "scope": "Only selected sash TEXCOORD_0. Exact geometry, rig, morphs, tangent basis, materials, images, crown and every other byte preserved.",
              "lods": [build(name, pin, args.output) for name, pin in PINS.items()]}
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
