"""Independent VTF texel audit using Pillow's BC decoder and the native image resource directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import numpy as np
from PIL import Image

from native import Bsp, insist, normal, zip_index


def bytes_per_image(fmt, width, height):
    if fmt in (13, 20, 14, 15):
        return (
            max(1, (width + 3) // 4)
            * max(1, (height + 3) // 4)
            * (8 if fmt in (13, 20) else 16)
        )
    sizes = {
        0: 4,
        1: 4,
        2: 3,
        3: 3,
        4: 2,
        5: 1,
        6: 2,
        8: 1,
        9: 3,
        10: 3,
        11: 4,
        12: 4,
        16: 4,
    }
    if fmt == 0xFFFFFFFF:
        return 0
    if fmt not in sizes:
        raise ValueError(f"Unsupported VTF image format {fmt}")
    return width * height * sizes[fmt]


class Vtf:
    def __init__(self, data):
        self.data = data
        insist(data[:4] == b"VTF\0", "Wrong texture signature")
        major, minor, header = struct.unpack_from("<III", data, 4)
        self.ver = [major, minor]
        insist(major == 7 and 0 <= minor <= 5, "Unsupported VTF version")
        self.w, self.h, self.flags, self.frames = struct.unpack_from("<HHIH", data, 16)
        self.fmt, self.mips, thumb_format, tw, th = struct.unpack_from(
            "<IBIBB", data, 52
        )
        self.depth = struct.unpack_from("<H", data, 63)[0] if minor >= 2 else 1
        insist(
            not self.flags & 0x4000 and self.depth in (0, 1),
            "Cubemap/volume is not a ground albedo",
        )
        high = header + (bytes_per_image(thumb_format, tw, th) if tw and th else 0)
        if minor >= 3:
            (count,) = struct.unpack_from("<I", data, 68)
            for i in range(count):
                tag, off = struct.unpack_from("<II", data, 80 + 8 * i)
                if tag & 0xFFFFFF == 0x30:
                    high = off
                    break
        insist(0 <= high <= len(data), "Invalid high-resolution resource offset")
        self.levels = {}
        for level in range(self.mips - 1, -1, -1):
            w, h = max(1, self.w >> level), max(1, self.h >> level)
            step = bytes_per_image(self.fmt, w, h)
            self.levels[level] = (high, w, h, step)
            high += step * self.frames
        insist(high <= len(data), "VTF mip data truncated")

    def rgba(self, level, frame):
        off, w, h, step = self.levels[level]
        body = self.data[off + frame * step : off + (frame + 1) * step]
        if self.fmt == 0:
            return np.frombuffer(body, dtype="u1").reshape(h, w, 4)
        if self.fmt in (11, 12, 1, 16):
            base = np.frombuffer(body, dtype="u1").reshape(h, w, 4)
            channels = {
                11: [1, 2, 3, 0],
                12: [2, 1, 0, 3],
                1: [3, 2, 1, 0],
                16: [2, 1, 0, 3],
            }[self.fmt]
            result = base[:, :, channels].copy()
            if self.fmt == 16:
                result[:, :, 3] = 255
            return result
        if self.fmt in (13, 14, 15, 20):
            codec = {
                13: (1, "DXT1"),
                20: (1, "DXT1"),
                14: (2, "DXT3"),
                15: (3, "DXT5"),
            }[self.fmt]
            padded = ((w + 3) // 4 * 4, (h + 3) // 4 * 4)
            im = Image.frombytes("RGBA", padded, body, "bcn", codec)
            return np.asarray(im)[:h, :w]
        raise ValueError(
            f"No independent color decoder configured for albedo format {self.fmt}"
        )


def lut(gains):
    srgb = np.arange(256, dtype=float) / 255
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    linear = np.minimum(1, np.maximum(0, linear[:, None] * np.array(gains)[None, :]))
    out = np.where(
        linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055
    )
    return np.rint(np.minimum(1, out) * 255).astype("u1")


def inspect(old, new, gains):
    a, b = Vtf(old), Vtf(new)
    insist(
        (a.w, a.h, a.frames, a.mips) == (b.w, b.h, b.frames, b.mips),
        "Texture size, frames or mip count changed",
    )
    insist(b.fmt == 0, "Expected a locally baked RGBA8888 ground texture")
    table = lut(gains)
    total = 0
    alpha_errors = 0
    max_rgb_err = 0
    example = None
    alpha_translucent = 0
    for frame in range(a.frames):
        for level in range(a.mips):
            before = a.rgba(level, frame)
            after = b.rgba(level, frame)
            expected = np.stack([table[before[:, :, i], i] for i in range(3)], axis=2)
            delta = np.abs(expected.astype("i2") - after[:, :, :3].astype("i2"))
            total += before.shape[0] * before.shape[1]
            alpha_errors += int(np.count_nonzero(before[:, :, 3] != after[:, :, 3]))
            alpha_translucent += int(np.count_nonzero(before[:, :, 3] != 255))
            max_rgb_err = max(max_rgb_err, int(delta.max()))
            if level == 0 and frame == 0:
                y, x = before.shape[0] // 3, before.shape[1] // 3
                example = {
                    "frame": 0,
                    "mip": 0,
                    "x": x,
                    "y": y,
                    "before_rgba": before[y, x].tolist(),
                    "expected_rgb": expected[y, x].tolist(),
                    "after_rgba": after[y, x].tolist(),
                }
    return {
        "source_format": a.fmt,
        "new_format": b.fmt,
        "dimensions": [a.w, a.h],
        "frames": a.frames,
        "mips": a.mips,
        "pixels_compared": total,
        "alpha_changed_pixels": alpha_errors,
        "nonopaque_source_texels": alpha_translucent,
        "maximum_rgb_difference_from_srgb_transform": max_rgb_err,
        "representative_texel": example,
        "source_sha256": hashlib.sha256(old).hexdigest(),
        "baked_sha256": hashlib.sha256(new).hexdigest(),
    }


def run(reference, variant, assets, bake):
    plan = json.loads(bake.read_text())
    g = plan["gains_linear"]
    textures = []
    with Bsp(reference) as a, Bsp(variant) as b, a.archive() as za, b.archive() as zb:
        src = zip_index(za)
        dst = zip_index(zb)
        added = set(dst) - set(src)
        originals = {
            normal(item["output"]): normal(item["source"]) for item in plan["textures"]
        }
        insist(
            len(originals) == len(plan["textures"])
            and set(originals) == {x for x in added if x.endswith(".vtf")},
            "Bake list does not cover every newly packed texture exactly once",
        )

        def original_bytes(name):
            insist(
                name.startswith("materials/") and ".." not in name.split("/"),
                "Unsafe original material path",
            )
            return za.read(src[name]) if name in src else (assets / name).read_bytes()

        # Read actual source materials and actual packed patches independently of the bake plan.
        # These original world shaders bind a literal VMT key at a line start.
        bindings = re.compile(
            r'^\s*"?([\$]basetexture2?)"?\s+"?([^"\s{}]+)"?', re.I | re.M
        )
        verified_layers = 0
        for name in sorted(x for x in added if x.endswith(".vmt")):
            patch = zb.read(dst[name]).decode("cp1252")
            include = re.search(r'^\s*"?include"?\s+"([^"]+)"', patch, re.I | re.M)
            insist(include is not None, f"Missing original VMT in {name}")
            old = original_bytes(normal(include.group(1))).decode("cp1252")
            old_layers = {
                k.lower(): "materials/" + normal(v) + ".vtf"
                for k, v in bindings.findall(old)
            }
            new_layers = {
                k.lower(): "materials/" + normal(v) + ".vtf"
                for k, v in bindings.findall(patch)
            }
            insist(
                old_layers and old_layers.keys() == new_layers.keys(),
                f"Original albedo slots differ for {name}",
            )
            for k, target in new_layers.items():
                insist(
                    originals.get(target) == old_layers[k],
                    f"Albedo layer points to a different source for {name} {k}",
                )
                verified_layers += 1
        for entry in plan["textures"]:
            name = normal(entry["source"])
            target = normal(entry["output"])
            raw = original_bytes(name)
            origin = "embedded pak" if name in src else "mounted stock game content"
            record = inspect(raw, zb.read(dst[target]), g)
            textures.append(
                dict(source=name, variant=target, reference=origin, **record)
            )
    return {
        "schema": "yuga.dust2.texture-diff.v1",
        "gains_linear": g,
        "texture_count": len(textures),
        "original_vmt_layer_references_verified": verified_layers,
        "all_mips_all_frames": True,
        "compared_pixels": sum(x["pixels_compared"] for x in textures),
        "alpha_changed_pixels": sum(x["alpha_changed_pixels"] for x in textures),
        "maximum_rgb_error_codes": max(
            x["maximum_rgb_difference_from_srgb_transform"] for x in textures
        ),
        "textures": textures,
        "method": "Pillow BC decoder and a separate VTF mip/resource reader. Compare decoded original sRGB through a linear multiplier against each new raw RGBA8888 mip and frame.",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("variant", type=Path)
    p.add_argument("stock_assets", type=Path)
    p.add_argument("bake_manifest", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    r = run(args.baseline, args.variant, args.stock_assets, args.bake_manifest)
    body = json.dumps(r, indent=2) + "\n"
    if args.output:
        args.output.write_text(body)
    else:
        print(body, end="")
    if r["alpha_changed_pixels"] or r["maximum_rgb_error_codes"]:
        raise SystemExit("Image reconstruction differs from the declared tint")
