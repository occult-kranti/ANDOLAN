"""Small adversarial fixtures for one-edit proof and sub-block VTF mip decoding."""

from pathlib import Path
import json
import struct
import tempfile
import unittest

from scene import Glb, compare_materials
from textures import Vtf, inspect, lut


def glb(path, ground=(0.5, 0.6, 0.7, 1), other=(1, 1, 1, 1), binary=b"BASE"):
    def mat(color, marked):
        return {
            "pbrMetallicRoughness": {"baseColorFactor": list(color)},
            "extras": {"yugaGround": marked},
        }

    document = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(binary)}],
        "materials": [mat(ground, True), mat(other, False)],
    }
    raw = json.dumps(document, separators=(",", ":")).encode()
    raw += b" " * (-len(raw) % 4)
    path.write_bytes(
        struct.pack("<4sII", b"glTF", 2, 28 + len(raw) + len(binary))
        + struct.pack("<I4s", len(raw), b"JSON")
        + raw
        + struct.pack("<I4s", len(binary), b"BIN\0")
        + binary
    )


def vtf(width, height, fmt, payload):
    header = bytearray(80)
    struct.pack_into("<4sIIIHHIH", header, 0, b"VTF\0", 7, 2, 80, width, height, 0, 1)
    struct.pack_into("<IBIBBH", header, 52, fmt, 1, 0xFFFFFFFF, 0, 0, 1)
    return bytes(header) + payload


class GroundPolicyTests(unittest.TestCase):
    def test_ground_only_diff_accepts_one_material_and_rejects_unrelated_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.glb"
            b = Path(tmp) / "b.glb"
            glb(a)
            glb(b, ground=(0.1, 0.8, 0.2, 1))
            self.assertEqual(len(compare_materials(Glb(a), Glb(b))[0]), 1)
            glb(b, ground=(0.1, 0.8, 0.2, 1), other=(0.9, 1, 1, 1))
            with self.assertRaisesRegex(ValueError, "Non-ground"):
                compare_materials(Glb(a), Glb(b))
            glb(b, ground=(0.1, 0.8, 0.2, 1), binary=b"BASX")
            with self.assertRaisesRegex(ValueError, "Binary chunks differ"):
                compare_materials(Glb(a), Glb(b))
            glb(b, ground=(0.1, 0.8, 0.2, 0.5))
            with self.assertRaisesRegex(ValueError, "RGB-only"):
                compare_materials(Glb(a), Glb(b))

    def test_partial_bc_block_and_srgb_alpha(self):
        # Four texels address one 4x4 BC block even when the stored mip measures 2x2.
        # The active 2x2 texels select the two endpoints, their mix and transparency.
        codes = (0 << 0) | (1 << 2) | (2 << 8) | (3 << 10)
        data = vtf(2, 2, 20, struct.pack("<HHI", 0x001F, 0xF800, codes))
        original = Vtf(data).rgba(0, 0)
        self.assertEqual(original[0, 0].tolist(), [0, 0, 255, 255])
        self.assertEqual(original[0, 1].tolist(), [255, 0, 0, 255])
        self.assertEqual(int(original[1, 1, 3]), 0)
        gains = (0.035, 0.52, 0.31)
        table = lut(gains)
        converted = original.copy()
        for c in range(3):
            converted[:, :, c] = table[original[:, :, c], c]
        report = inspect(data, vtf(2, 2, 0, converted.tobytes()), gains)
        self.assertEqual(report["pixels_compared"], 4)
        self.assertEqual(report["nonopaque_source_texels"], 1)
        self.assertEqual(report["maximum_rgb_difference_from_srgb_transform"], 0)
        converted[1, 1, 3] = 255
        self.assertEqual(
            inspect(data, vtf(2, 2, 0, converted.tobytes()), gains)[
                "alpha_changed_pixels"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()
