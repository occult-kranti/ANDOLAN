#!/usr/bin/env python3
"""Reproduce the independent negative by changing only positive JOINTS_0 bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SOURCE_SHA256 = "a7add6b73b690f9fd8e5c88d7d0eaa36e248ad3368a1bdbc2a06d5d73bd038d9"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original = args.source.read_bytes()
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise SystemExit("Expected the exact reviewed R3 card candidate")
    raw = bytearray(original)
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(raw[20:20 + size])
    binary_start = 28 + size
    primitive = doc["meshes"][0]["primitives"][0]
    joints = doc["accessors"][primitive["attributes"]["JOINTS_0"]]
    jview = doc["bufferViews"][joints["bufferView"]]
    weights = doc["accessors"][primitive["attributes"]["WEIGHTS_0"]]
    wview = doc["bufferViews"][weights["bufferView"]]
    assert joints["componentType"] == 5121 and joints["type"] == "VEC4"
    assert weights["componentType"] == 5126 and weights["count"] == joints["count"] == 2304
    names = [doc["nodes"][joint]["name"] for joint in doc["skins"][0]["joints"]]
    head, wrong = names.index("head"), names.index("spine05")
    changes = 0
    for vertex in range(joints["count"]):
        for slot in range(4):
            joint_offset = binary_start + jview.get("byteOffset", 0) + joints.get("byteOffset", 0) + vertex * jview.get("byteStride", 4) + slot
            weight_offset = binary_start + wview.get("byteOffset", 0) + weights.get("byteOffset", 0) + vertex * wview.get("byteStride", 16) + slot * 4
            if struct.unpack_from("<f", raw, weight_offset)[0] > 0:
                assert raw[joint_offset] == head
                raw[joint_offset] = wrong
                changes += 1
    assert changes == 2304 and sum(a != b for a, b in zip(raw, original)) == changes
    with args.output.open("xb") as output:
        output.write(raw)
    print(json.dumps({"source_sha256": SOURCE_SHA256, "negative_sha256": hashlib.sha256(raw).hexdigest(),
                      "changed_bytes": changes, "from_joint": head, "to_joint": wrong}))


if __name__ == "__main__":
    main()
