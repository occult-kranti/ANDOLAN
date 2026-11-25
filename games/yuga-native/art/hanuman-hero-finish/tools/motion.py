"""Layer a tail recoil onto the four existing Mountain Pulse rotation curves.

python motion.py INPUT.glb OUTPUT.glb [--receipt result.json]
python motion.py FINISHED.glb RESTORED.glb --restore
Requires the ANDOLAN checkout; uses its independent glTF reader.
"""

import argparse
import hashlib
import json
import math
import os
import struct
import sys
import tempfile
from pathlib import Path

ART = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ART.parent / "tools/hanuman-review"))
from audit_glb import Payload, require

REFERENCE = ART / "four-hero-motion/models/hanuman.glb"
CLIP = "mountain_pulse"
TAIL = tuple(f"tail_{i:02}" for i in range(1, 5))
IDENTITY = (0, 0, 0, 1)


def product(a, b):
    x, y, z, w = a
    i, j, k, r = b
    return (
        w * i + x * r + y * k - z * j,
        w * j - x * k + y * r + z * i,
        w * k + x * j - y * i + z * r,
        w * r - x * i - y * j - z * k,
    )


def normalized(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v)


def in_bind_space(document, index, axis):
    parents = {
        child: i
        for i, node in enumerate(document["nodes"])
        for child in node.get("children", ())
    }
    chain = []
    while index is not None:
        node = document["nodes"][index]
        require("matrix" not in node, "expected decomposed skeleton node")
        chain.append(node.get("rotation", IDENTITY))
        index = parents.get(index)
    bind = IDENTITY
    for q in reversed(chain):
        bind = product(bind, q)
    x, y, z, w = normalized(bind)
    return normalized(product(product((-x, -y, -z, w), (*axis, 0)), (x, y, z, w))[:3])


def lobe(t, start, end):
    if not start < t < end:
        return 0.0
    return math.sin(math.pi * (t - start) / (end - start)) ** 2


def recoil(phase, link):
    # A delayed elastic swing after remote impact, followed by a smaller opposing
    # counter-swing. Both envelope ends have zero value and zero slope.
    delay = link * 0.013
    primary = lobe(phase, 0.78 + delay, 0.895 + delay)
    settle = lobe(phase, 0.895 + delay, 0.979 + 0.005 * link)
    return (7 + link * 1.25) * (primary - 0.31 * settle)


def rotation_tracks(payload):
    doc = payload.document
    (clip,) = (a for a in doc["animations"] if a["name"] == CLIP)
    tracks = {}
    for channel in clip["channels"]:
        target = channel["target"]
        index = target["node"]
        name = doc["nodes"][index]["name"]
        if name not in TAIL or target["path"] != "rotation":
            continue
        sampler = clip["samplers"][channel["sampler"]]
        output = sampler["output"]
        acc = doc["accessors"][output]
        vi = acc["bufferView"]
        view, data = payload.view(vi)
        require(
            name not in tracks and sampler.get("interpolation", "LINEAR") == "LINEAR",
            "unexpected curve",
        )
        require(
            acc["componentType"] == 5126
            and acc["type"] == "VEC4"
            and not any(k in acc for k in ("min", "max", "sparse"))
            and acc.get("byteOffset", 0) == 0
            and view.get("byteStride", 16) == 16
            and len(data) == 16 * acc["count"],
            "expected tightly packed quaternion samples",
        )
        used = sum(
            s["output"] == output or s["input"] == output
            for a in doc["animations"]
            for s in a["samplers"]
        )
        require(
            used == 1 and sum(a.get("bufferView") == vi for a in doc["accessors"]) == 1,
            "quaternion samples shared with another track or attribute",
        )
        begin = view.get("byteOffset", 0)
        end = begin + len(data)
        require(
            all(
                i == vi
                or max(begin, v.get("byteOffset", 0))
                >= min(end, v.get("byteOffset", 0) + v["byteLength"])
                for i, v in enumerate(doc["bufferViews"])
            ),
            "target buffer range aliases another view",
        )
        times = tuple(t for t, in payload.accessor(sampler["input"]))
        require(
            len(times) == acc["count"]
            and all(t1 < t2 for t1, t2 in zip(times, times[1:])),
            "expected increasing original key times",
        )
        tracks[name] = (begin, bytes(data), times, in_bind_space(doc, index, (0, 1, 0)))
    require(set(tracks) == set(TAIL), "missing Mountain Pulse tail rotation channels")
    return tracks


def enhance_curve(samples, times, axis, link):
    out = bytearray(samples)
    angles = []
    for i, (t, q) in enumerate(
        zip(times, struct.iter_unpack("<4f", samples), strict=True)
    ):
        phase = (t - times[0]) / (times[-1] - times[0])
        degrees = recoil(phase, link)
        if abs(degrees) < 1e-5:
            continue
        angle = math.radians(degrees) / 2
        turn = (*[x * math.sin(angle) for x in axis], math.cos(angle))
        corrected = normalized(product(q, turn))
        struct.pack_into("<4f", out, i * 16, *corrected)
        angles.append((i, phase, degrees))
    return bytes(out), angles


def improve_motion(source_path, output_path, *, restore=False):
    source_path, output_path = Path(source_path), Path(output_path)
    # The canonical delivery also makes removal exact down to individual bytes.
    # Grooms and surface changes are permitted; unexpected competing motion is not.
    baseline = rotation_tracks(Payload(REFERENCE.read_bytes()))
    original = source_path.read_bytes()
    payload = Payload(original)
    current = rotation_tracks(payload)
    result = bytearray(original)
    binary_offset = len(original) - len(payload.binary)
    metadata = {}
    for link, name in enumerate(TAIL):
        offset, present, times, axis = current[name]
        _, canonical, source_times, source_axis = baseline[name]
        require(
            times == source_times and math.dist(axis, source_axis) < 1e-5,
            "skeleton or timing changed",
        )
        enhanced, angles = enhance_curve(canonical, times, source_axis, link)
        require(
            present in (canonical, enhanced),
            f"{name} contains unrecognized competing motion",
        )
        start = binary_offset + offset
        result[start : start + len(present)] = canonical if restore else enhanced
        metadata[name] = {
            "original_keys": len(times),
            "changed_keys": len(angles),
            "peak_added_degrees": round(max(a[2] for a in angles), 4),
            "peak_phase": round(max(angles, key=lambda a: a[2])[1], 5),
        }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_path.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            temp.write(result)
            temp.flush()
        except OSError:
            temp.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "animation": CLIP,
        "restored": restore,
        "curves": metadata,
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "output_sha256": hashlib.sha256(result).hexdigest(),
        "changed_bytes": sum(a != b for a, b in zip(original, result, strict=True)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    info = improve_motion(args.source, args.output, restore=args.restore)
    text = json.dumps(info, indent=2) + "\n"
    if args.receipt:
        args.receipt.write_text(text)
    else:
        print(text, end="")
