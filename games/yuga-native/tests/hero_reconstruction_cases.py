"""Independent byte-preservation and invalid-input gates for reconstructed Rama.

This checks actual runtime GLB data, not appearance or continuous rendered motion.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import struct
import tempfile
import zlib

GAME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rama_reconstruction", GAME / "art/production/reconstruct_rama.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def png(payload):
    assert payload[:8] == b"\x89PNG\r\n\x1a\n"
    cursor = 8
    data = bytearray()
    dimensions = None
    ended = False
    while cursor < len(payload):
        size = struct.unpack_from(">I", payload, cursor)[0]
        kind = payload[cursor + 4:cursor + 8]
        body = payload[cursor + 8:cursor + 8 + size]
        checksum = struct.unpack_from(">I", payload, cursor + 8 + size)[0]
        assert zlib.crc32(kind + body) & 0xffffffff == checksum
        if kind == b"IHDR":
            dimensions = struct.unpack(">IIBBBBB", body)
        if kind == b"IDAT":
            data.extend(body)
        if kind == b"IEND":
            ended = True
        cursor += size + 12
    assert ended and cursor == len(payload) and dimensions == (256, 256, 8, 2, 0, 0, 0)
    rows = zlib.decompress(data)
    assert len(rows) == 256 * (256 * 3 + 1)
    assert all(rows[y * (256 * 3 + 1)] == 0 for y in range(256))
    return rows


def verify(candidate):
    _base, before, original = GEN.read_glb(GEN.SOURCE)
    assert GEN.sha(_base) == GEN.SOURCE_SHA256, "Pinned baseline changed"
    raw, after, binary = GEN.read_glb(candidate)
    # These assertions deliberately reject structural mutations independently
    # from hashes in a generator-written manifest.
    assert binary[:len(original)] == original, "Original binary data changed"
    for name in ["nodes", "skins", "animations", "scenes", "scene"]:
        assert after.get(name) == before.get(name), "Changed structural section: " + name
    assert after["accessors"][:len(before["accessors"]) ] == before["accessors"]
    assert after["bufferViews"][:len(before["bufferViews"]) ] == before["bufferViews"]
    assert len(after["meshes"]) == len(before["meshes"]) == 1
    assert len(after["materials"]) == len(before["materials"]) == 10
    assert len(after["skins"][0]["joints"]) == 164
    vertices = triangles = tinted = 0
    for previous, current in zip(before["meshes"][0]["primitives"], after["meshes"][0]["primitives"]):
        clean = copy.deepcopy(current)
        color_accessor = clean["attributes"].pop("COLOR_0", None)
        assert clean == previous, "Geometry/skin primitive changed"
        vertices += before["accessors"][previous["attributes"]["POSITION"]]["count"]
        triangles += before["accessors"][previous["indices"]]["count"] // 3
        if color_accessor is not None:
            colors = GEN.values(after, binary, color_accessor)
            assert len(colors) == before["accessors"][previous["attributes"]["POSITION"]]["count"]
            assert all(math.isfinite(c) and .80 <= c <= 1 for color in colors for c in color)
            assert any(min(color) < .999 for color in colors)
            tinted += len(colors)
    assert (vertices, triangles, tinted) == (59759, 100938, 28201)
    expected = {"cast", "cast1", "cast2", "cast3", "defeat", "fire", "idle", "jump", "run"}
    assert {a["name"] for a in after["animations"]} == expected
    animation_values = 0
    for animation in after["animations"]:
        for sampler in animation["samplers"]:
            times = [x[0] for x in GEN.values(after, binary, sampler["input"])]
            assert all(math.isfinite(t) and t >= 0 for t in times)
            assert all(a < b for a, b in zip(times, times[1:]))
            samples = GEN.values(after, binary, sampler["output"])
            assert all(math.isfinite(c) for v in samples for c in v)
            animation_values += len(samples)
    generated = []
    for old, image in zip(before["images"], after["images"]):
        assert image["name"] == old["name"] and image["mimeType"] == "image/png" and "uri" not in image
        if image["bufferView"] != old["bufferView"]:
            view = after["bufferViews"][image["bufferView"]]
            assert view["byteOffset"] >= len(original)
            payload = binary[view["byteOffset"]:view["byteOffset"] + view["byteLength"]]
            png(payload)
            generated.append(image["name"])
    assert len(generated) == 10 and len(after["images"]) == len(before["images"]) == 15
    for material in after["materials"]:
        pbr = material["pbrMetallicRoughness"]
        for field in ["baseColorFactor", "roughnessFactor", "metallicFactor"]:
            if field in pbr:
                values = pbr[field] if isinstance(pbr[field], list) else [pbr[field]]
                assert all(math.isfinite(x) and 0 <= x <= 1 for x in values)
    assert len(raw) < 9 * 1024 * 1024
    return {"vertices": vertices, "triangles": triangles, "joints": 164, "clips": 9,
            "animation_output_samples_finite": animation_values, "generated_images": len(generated),
            "vertex_colors": tinted, "preserved_binary_bytes": len(original), "bytes": len(raw),
            "preserved_binary_sha256": GEN.sha(original),
            "preserved_section_sha256": {key: GEN.sha(json.dumps(before[key], sort_keys=True, separators=(",", ":")).encode()) for key in ["nodes", "skins", "animations", "accessors", "bufferViews"]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, default=GAME / "assets/heroes/rama-production.glb")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    results = []
    def check(name, callback):
        try:
            detail = callback()
            results.append({"name": name, "passed": True, "detail": detail})
        except Exception as error:
            results.append({"name": name, "passed": False, "error": str(error)})
    check("Runtime rig/skin/animation bytes, image CRCs, finite bounded colours and topology preserved", lambda: verify(args.asset))
    def reproducible():
        a, _ = GEN.build(); b, _ = GEN.build()
        assert a == b == args.asset.read_bytes()
        return hashlib.sha256(a).hexdigest()
    check("Two clean generations match each other and the supplied runtime asset byte-for-byte", reproducible)
    def bad_source():
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "bad.glb"
            data = bytearray(GEN.SOURCE.read_bytes()); data[-12] ^= 1; target.write_bytes(data)
            try:
                GEN.build(target)
            except ValueError as error:
                assert "source hash differs" in str(error)
                return "Rejected changed source"
            raise AssertionError("Changed source accepted")
    check("Changed reconstruction input rejected", bad_source)
    def bad_geometry():
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "bad.glb"
            data = bytearray(args.asset.read_bytes()); size = struct.unpack_from("<I", data, 12)[0]
            data[20 + size + 8 + 12] ^= 1; target.write_bytes(data)
            try:
                verify(target)
            except AssertionError as error:
                assert "Original binary" in str(error)
                return "Rejected changed binary geometry/animation data"
            raise AssertionError("Original binary mutation accepted")
    check("Original-data mutation rejected even when GLB length remains valid", bad_geometry)
    def bad_png():
        payload = bytearray(GEN.texture(GEN.PALETTES["Cobalt woven silk"])); payload[50] ^= 1
        try:
            png(bytes(payload))
        except AssertionError:
            return "Rejected corrupt image CRC"
        raise AssertionError("Corrupt generated image accepted")
    check("Corrupt material image rejected", bad_png)
    def encoded_palette():
        _, document, binary = GEN.read_glb(args.asset)
        expected = {
            "warm-living-skin-albedo": ((147, 154), (94, 101), (65, 71)),
            "cobalt-woven-silk-albedo": ((17, 20), (39, 44), (87, 94)),
            "ivory-folded-silk-albedo": ((207, 216), (197, 206), (162, 170)),
        }
        actual = {}
        for name, ranges in expected.items():
            image = next(item for item in document["images"] if item["name"] == name)
            view = document["bufferViews"][image["bufferView"]]
            rows = png(binary[view["byteOffset"]:view["byteOffset"] + view["byteLength"]])
            offset = 128 * (256 * 3 + 1) + 1 + 128 * 3
            rgb = tuple(rows[offset:offset + 3])
            assert all(low <= value <= high for value, (low, high) in zip(rgb, ranges)), (name, rgb)
            actual[name] = rgb
        assert actual["warm-living-skin-albedo"] != (173, 141, 120), "Rejected pale revision1 returned"
        return actual
    check("Encoded sRGB palette ranges prevent the rejected extra-transfer pale skin/pastel cloth", encoded_palette)
    report = {"schema": 1, "passed": all(x["passed"] for x in results), "checks": results,
              "asset": str(args.asset), "asset_sha256": GEN.sha(args.asset.read_bytes()),
              "generator_sha256": GEN.sha(Path(GEN.__file__).read_bytes()),
              "scope": "Actual GLB preservation/reproducibility/negative-input checks. No visual, contact, continuous-motion or commercial-quality acceptance."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
