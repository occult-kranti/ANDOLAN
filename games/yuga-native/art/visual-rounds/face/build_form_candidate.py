"""R2-08 bounded principal-form stage on the reviewed original Rama GLB.

Only eligible dense POSITION/NORMAL/TANGENT records may change. Topology,
UVs, morphs, skinning, materials and the original animation data stay exact.
The editable Blender companion is a separate import, never a runtime exporter.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np

ART = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ART / "hero-rama-lod"))
from glb_lod import GLB

PIN = "de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5"
HELD_RING_PIN = "71cc40e8f5eb732382255cbb9ca2eca88f6306429c2c649f8223dbe5b4db0ccd"
ELIGIBLE = {(1, 0): "Rama warm skin", (2, 11): "Rama warm skin", (2, 12): "Natural lips"}
PARAMETERS = [
    # name, center XYZ in original glTF metres, compact ellipsoid radii, offset,
    # mirrored across X. These are original art decisions, not literary anatomy.
    ("upper_lid_shelf", (.03279, 1.7365, .145), (.025, .007, .025), (0, 0, .00085), True),
    ("superior_fold_relief", (.034, 1.745, .140), (.026, .010, .025), (0, 0, -.00060), True),
    ("malar_plane", (.050, 1.695, .137), (.035, .026, .040), (.0004, 0, .0018), True),
    ("lower_cheek_transition", (.050, 1.662, .134), (.035, .024, .040), (0, 0, -.0008), True),
    ("upper_lip_support", (0, 1.651, .165), (.024, .008, .021), (0, 0, .00085), False),
    ("lower_lip_plane", (0, 1.639, .166), (.022, .007, .016), (0, 0, .00050), False),
    ("labiomental_transition", (0, 1.630, .160), (.025, .008, .026), (0, 0, -.00080), False),
    ("chin_plane", (0, 1.613, .154), (.036, .021, .035), (0, 0, .00160), False),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smooth(low, high, values):
    t = np.clip((values - low) / (high - low), 0, 1)
    return t * t * t * (10 + t * (-15 + 6 * t))


def displacement(points, boundary):
    """Compact C2 field, with a held 4 mm collar and 16 mm smooth recovery."""
    points = np.asarray(points, dtype=np.float64)
    result = np.zeros_like(points)
    selected = (points[:, 1] > 1.585) & (points[:, 1] < 1.780) & (abs(points[:, 0]) < .100) & (points[:, 2] > .095)
    p = points[selected]
    if not len(p):
        return result
    delta = np.zeros_like(p)
    for _, center, radii, offset, mirror in PARAMETERS:
        for sign in (-1, 1) if mirror else (1,):
            c = np.array(center) * (sign, 1, 1)
            r2 = np.sum(((p - c) / radii) ** 2, axis=1)
            influence = np.maximum(0, 1 - r2) ** 3
            delta += influence[:, None] * (np.array(offset) * (sign, 1, 1))
    distance = np.sqrt(np.min(np.sum((p[:, None, :] - boundary[None, :, :]) ** 2, axis=2), axis=1))
    gate = smooth(.004, .016, distance)
    gate *= smooth(1.585, 1.600, p[:, 1]) * (1 - smooth(1.765, 1.780, p[:, 1]))
    gate *= 1 - smooth(.085, .100, abs(p[:, 0]))
    gate *= smooth(.095, .120, p[:, 2])
    result[selected] = delta * gate[:, None]
    return result


def jacobian(points, boundary):
    # Central difference of the authored C2 field. 10 micrometres is much
    # smaller than the smallest 7 mm brush radius, without float32 subtraction.
    result = np.broadcast_to(np.eye(3), (len(points), 3, 3)).copy()
    epsilon = 1e-5
    for axis in range(3):
        step = np.zeros(3)
        step[axis] = epsilon
        result[:, :, axis] += (displacement(points + step, boundary) - displacement(points - step, boundary)) / (2 * epsilon)
    return result


def normalize(values):
    return values / np.linalg.norm(values, axis=1)[:, None]


def writable_array(raw, glb, index):
    a = glb.doc["accessors"][index]
    assert a["componentType"] == 5126 and "sparse" not in a
    v = glb.doc["bufferViews"][a["bufferView"]]
    width = {"VEC3": 3, "VEC4": 4}[a["type"]]
    start = 28 + struct.unpack_from("<I", raw, 12)[0]
    offset = start + v.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = v.get("byteStride", width * 4)
    view = np.ndarray((a["count"], width), dtype="<f4", buffer=raw, offset=offset, strides=(stride, 4))
    return view, offset, stride


def build(source, partition, held_ring, output):
    if sha(source) != PIN:
        raise ValueError("Input must be the pinned original near hero")
    if sha(held_ring) != HELD_RING_PIN:
        raise ValueError("Held ring must be the pinned original native quad-ring extraction")
    if output.exists():
        raise ValueError("A fresh external output directory is required")
    resolved = output.resolve()
    if ART.parents[2] in resolved.parents or resolved == ART.parents[2]:
        raise ValueError("Candidate outputs must stay outside the repository")
    output.mkdir(parents=True)
    glb = GLB(source)
    metadata = json.loads(partition.read_text())
    boundary = np.array([[p["position"][0], p["position"][2], -p["position"][1]] for p in metadata["boundary"]])
    ring_source = json.loads(held_ring.read_text())
    ring = np.array(ring_source['positions_gltf_m'], dtype=np.float64)
    assert ring.shape == (288, 3) and np.isfinite(ring).all()
    assert ring_source['source_sha256'] == 'c541b2bf233843634db27de1768953756f2821d08b23242dd0ddacc29b66f351'
    raw = bytearray(glb.raw)
    allowed = np.zeros(len(raw), dtype=bool)
    rows = []
    changed_records = []
    for mi, pi, primitive in glb.primitives():
        if (mi, pi) not in ELIGIBLE:
            continue
        assert glb.doc["materials"][primitive["material"]]["name"] == ELIGIBLE[mi, pi]
        attrs = primitive["attributes"]
        positions = glb.array(attrs["POSITION"]).astype(np.float64)
        delta = displacement(positions, boundary)
        # The original quad ring is a topological constraint, not a distance
        # approximation. Freeze exact exported copies, including shading frames.
        held = np.zeros(len(positions), dtype=bool)
        local = np.flatnonzero((positions[:, 1] > 1.69) & (positions[:, 1] < 1.77) & (abs(positions[:, 0]) < .08))
        held[local] = np.min(np.max(abs(positions[local, None, :] - ring[None, :, :]), axis=2), axis=1) < 1e-7
        delta[held] = 0
        moved = np.flatnonzero(np.linalg.norm(delta, axis=1) > 1e-9)
        # The true stored float32 displacement is the reported result.
        proposed = (positions + delta).astype(np.float32)
        moved = moved[np.any(proposed[moved] != positions[moved], axis=1)]
        j = jacobian(positions[moved], boundary)
        assert np.min(np.linalg.det(j)) > .75, "Local orientation must stay positive"
        n = glb.array(attrs["NORMAL"]).astype(np.float64)
        t = glb.array(attrs["TANGENT"]).astype(np.float64)
        new_n = normalize(np.linalg.solve(j.transpose(0, 2, 1), n[moved, :, None])[:, :, 0])
        new_t = np.einsum("nij,nj->ni", j, t[moved, :3])
        new_t = normalize(new_t - new_n * np.sum(new_t * new_n, axis=1)[:, None])
        updates = {"POSITION": proposed[moved], "NORMAL": new_n.astype(np.float32), "TANGENT": np.column_stack((new_t, t[moved, 3])).astype(np.float32)}
        for semantic, values in updates.items():
            array, offset, stride = writable_array(raw, glb, attrs[semantic])
            array[moved] = values
            for index in moved:
                allowed[offset + int(index) * stride:offset + int(index) * stride + array.shape[1] * 4] = True
        actual = proposed[moved].astype(np.float64) - positions[moved]
        triangles = glb.array(primitive["indices"]).reshape(-1, 3)
        tri_active = np.any(np.isin(triangles, moved), axis=1)
        a, b = positions[triangles[tri_active]], proposed[triangles[tri_active]].astype(np.float64)
        an, bn = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]), np.cross(b[:, 1] - b[:, 0], b[:, 2] - b[:, 0])
        area_before, area_after = np.linalg.norm(an, axis=1), np.linalg.norm(bn, axis=1)
        valid = area_before > 1e-14
        ratio = area_after[valid] / area_before[valid]
        cosines = np.sum(an[valid] * bn[valid], axis=1) / (area_before[valid] * area_after[valid])
        assert np.min(cosines) > .96 and np.min(ratio) > .75 and np.max(ratio) < 1.25, (mi, pi, float(np.min(cosines)), float(np.min(ratio)), float(np.max(ratio)), float(np.min(area_before[valid])))
        assert np.max(np.linalg.norm(actual, axis=1)) < .002
        rows.append({"mesh": mi, "primitive": pi, "material": ELIGIBLE[mi, pi], "changed_vertices": len(moved), "maximum_displacement_m": float(np.max(np.linalg.norm(actual, axis=1))), "rms_displacement_m": float(np.sqrt(np.mean(np.sum(actual ** 2, axis=1)))), "edit_bounds_min": positions[moved].min(axis=0).tolist(), "edit_bounds_max": positions[moved].max(axis=0).tolist(), "minimum_jacobian_determinant": float(np.min(np.linalg.det(j))), "affected_triangles": int(np.sum(tri_active)), "minimum_triangle_normal_cosine": float(np.min(cosines)), "triangle_area_ratio": [float(np.min(ratio)), float(np.max(ratio))], "maximum_normal_rotation_degrees": float(np.degrees(np.arccos(np.clip(np.sum(normalize(n[moved]) * new_n, axis=1), -1, 1))).max())})
        changed_records.append({"mesh": mi, "primitive": pi, "vertices": moved.tolist(), "delta_xyz_m": actual.tolist()})
    different = np.frombuffer(glb.raw, dtype=np.uint8) != np.frombuffer(raw, dtype=np.uint8)
    assert np.all(allowed[different]) and np.any(different)
    # POSITION extrema are normative glTF data. Lip projection changes its
    # forward bound; preserve every other JSON value while updating exact bounds.
    document = copy.deepcopy(glb.doc)
    bounds_changes = []
    for mi, pi in ELIGIBLE:
        index = document['meshes'][mi]['primitives'][pi]['attributes']['POSITION']
        values, _, _ = writable_array(raw, glb, index)
        for key, value in [('min', values.min(axis=0).tolist()), ('max', values.max(axis=0).tolist())]:
            old = document['accessors'][index][key]
            if old != value:
                bounds_changes.append({'accessor': index, 'field': key, 'before': old, 'after': value})
                document['accessors'][index][key] = value
    binary_start = 28 + struct.unpack_from('<I', raw, 12)[0]
    binary = bytes(raw[binary_start:])
    encoded = json.dumps(document, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    complete = struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary)) + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + struct.pack('<II', len(binary), 0x004e4942) + binary
    candidate = output / "candidate.glb"
    candidate.write_bytes(complete)
    mask = output / "vertex-edits.json"
    mask.write_text(json.dumps(changed_records, separators=(",", ":")) + "\n")
    report = {"schema": 1, "task": "R2-08", "stage": "principal-facial-form-v1", "status": "isolated-candidate-awaiting-independent-visual-review", "source_commit": "0437ea91edf6989ff78c1eeadb3661f4825b60f2", "generator_sha256": sha(__file__), "input": str(source.resolve()), "input_sha256": PIN, "partition_sha256": sha(partition), "output_sha256": sha(candidate), "vertex_edits_sha256": sha(mask), "bytes": len(raw), "changed_bytes": int(np.sum(different)), "all_other_bytes_exact": True, "json_chunk_exact": True, "topology_uv_skin_morph_images_materials_rig_and_embedded_clips_exact": True, "bones": len(glb.doc["skins"][0]["joints"]), "embedded_clips": [a["name"] for a in glb.doc["animations"]], "external_states": 23, "external_library_changed": False, "frame_method": "Jacobian inverse-transpose normal transport and tangent push-forward with Gram-Schmidt; existing tangent handedness retained. No UV regeneration or independent tangent solver.", "parameters": [{"name": n, "center_xyz_m": c, "radii_xyz_m": r, "delta_xyz_m": o, "mirror_x": m} for n, c, r, o, m in PARAMETERS], "held_attachment": {"source_boundary_vertices": len(boundary), "exact_hold_radius_m": .004, "full_influence_distance_m": .016}, "primitives": rows, "limitations": ["New local rest form plus unchanged morph deltas requires posed aperture and visual validation.", "The existing LOD bodies remain unchanged; runtime promotion requires refreshed corresponding body positions/frames or explicit near-only isolation.", "Candidate import into Blender supplies editable reconstructed data, not original modeling history.", "No new face writer, dialogue performance, groom, costume or bow edits."]}
    report.update(bytes=len(complete), all_other_bytes_exact=False, all_other_binary_bytes_exact=True, json_chunk_exact=False, json_exact_except_position_bounds=True, position_bounds_changes=bounds_changes, original_held_ring_sha256=sha(held_ring), original_held_ring_input=str(held_ring.resolve()), original_held_ring_vertices=288, held_ring_policy='Every source-ring position match excluded from POSITION/NORMAL/TANGENT edits, independent of distance collar')
    (output / "edit-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--partition", type=Path, default=ART / "hero-rama-face/candidate.json")
    p.add_argument("--held-ring", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    build(a.input, a.partition, a.held_ring, a.output)
