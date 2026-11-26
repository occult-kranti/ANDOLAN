"""Build native Source patch VMTs and jade base-colour VTFs for a registered face set.

Install srctools and Pillow. The originals remain in the input BSP and game mount.
Every mip/frame's unmodified alpha and expected RGB are checked after re-encoding.
"""

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
import mmap
from pathlib import Path
import struct
import zipfile

from srctools.filesys import FileSystemChain, RawFileSystem, ZipFileSystem
from srctools.vmt import Material
from srctools.vtf import Frame, ImageFormats, ResourceID, VTF, VTFFlags

GAINS = (0.035, 0.52, 0.31)


def source_path(value, extension):
    path = (
        value.replace("\\", "/")
        .lower()
        .removeprefix("materials/")
        .removesuffix(extension)
    )
    if (
        not path
        or any(part in ("..", ".", "") for part in path.split("/"))
        or '"' in path
        or "\n" in path
    ):
        raise ValueError(f"Invalid engine material path {value!r}")
    return "materials/" + path + extension


def tint_lut(gain):
    def change(value):
        s = value / 255
        linear = (s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4) * gain
        encoded = (
            12.92 * linear
            if linear <= 0.0031308
            else 1.055 * linear ** (1 / 2.4) - 0.055
        )
        return min(255, max(0, round(255 * encoded)))

    return [change(value) for value in range(256)]


LUT = sum((tint_lut(gain) for gain in GAINS), []) + list(range(256))


def small_bc_frames(raw, tex):
    """Decode partial BC tiles on a 4x4 boundary with srctools, then crop.

    A VTF 1x1 or 2x2 BC image still stores the complete compressed tile.
    Handing these logical dimensions to srctools' native decoder misreads its edge.
    """
    if tex.format.name not in {"DXT1", "DXT1_ONEBITALPHA", "DXT3", "DXT5"}:
        return {}
    header_size = struct.unpack_from("<I", raw, 12)[0]
    high = header_size
    if tex.version[1] < 3:
        low_width, low_height = raw[61:63]
        if low_width and low_height:
            high += tex.low_format.frame_size(low_width, low_height)
    else:
        count = struct.unpack_from("<I", raw, 68)[0]
        for i in range(count):
            tag, flags, offset = struct.unpack_from("<3sBI", raw, 80 + i * 8)
            if tag == b"\x30\0\0":
                high = offset
                break
        else:
            raise ValueError("VTF high-resolution resource missing")
    clipped = {}
    for mip in reversed(range(tex.mipmap_count)):
        w, h = max(1, tex.width >> mip), max(1, tex.height >> mip)
        full_w, full_h = ((w + 3) // 4) * 4, ((h + 3) // 4) * 4
        stride = tex.format.frame_size(full_w, full_h)
        for frame in range(tex.frame_count):
            if w != full_w or h != full_h:
                padded = Frame(full_w, full_h)
                padded.copy_from(raw[high : high + stride], tex.format)
                clipped[frame, mip] = padded.to_PIL().crop((0, 0, w, h))
            high += stride
    return clipped


def bake_vtf(fsys, key, root):
    original = fsys[key]
    with original.open_bin() as stream:
        raw = stream.read()
    tex = VTF.read(BytesIO(raw))
    tex.load()
    if VTFFlags.ENVMAP in tex.flags or tex.depth != 1:
        raise ValueError("Ground shader base texture must be a 2D surface: " + key)
    alias = (
        "materials/yuga_dustlab/tex_" + sha256(key.encode()).hexdigest()[:16] + ".vtf"
    )
    path = root / alias
    path.parent.mkdir(parents=True, exist_ok=True)
    expected = {}
    partial = small_bc_frames(raw, tex)
    for frame in range(tex.frame_count):
        for mip in range(tex.mipmap_count):
            pic = tex.get(frame=frame, mipmap=mip)
            before = partial.get((frame, mip)) or pic.to_PIL()
            after = before.point(LUT)
            if after.getchannel("A").tobytes() != before.getchannel("A").tobytes():
                raise ValueError("Alpha changed")
            rgba = after.tobytes()
            expected[frame, mip] = sha256(rgba).digest()
            pic.copy_from(rgba)
    # These files are private derivatives. Lossless RGBA avoids changed alpha in a second BC encode.
    tex.format = ImageFormats.RGBA8888
    tex.resources.pop(ResourceID.CRC, None)
    with path.open("wb") as out:
        tex.save(out)
    with path.open("rb") as stream:
        decoded = VTF.read(stream)
        for (frame, mip), digest in expected.items():
            pixels = decoded.get(frame=frame, mipmap=mip).to_PIL().tobytes()
            if sha256(pixels).digest() != digest:
                raise ValueError(f"Mip round-trip failed for {key} {mip}")
    return dict(
        source=key,
        source_sha256=sha256(raw).hexdigest(),
        output=alias,
        sha256=sha256(path.read_bytes()).hexdigest(),
        width=tex.width,
        height=tex.height,
        frames=tex.frame_count,
        mips=tex.mipmap_count,
        verified_frames_and_mips=len(expected),
        encoding="RGBA8888",
    )


def material_ids(bsp, ids):
    def lump(index):
        offset, n, _, compressed = struct.unpack_from("<4I", bsp, 8 + 16 * index)
        if compressed:
            raise ValueError("Compressed editable lump")
        return memoryview(bsp)[offset : offset + n]

    infos, texdata, strings, offsets = lump(6), lump(2), bytes(lump(43)), lump(44)
    uses = defaultdict(int)
    for entry in ids:
        for faces in (lump(7), lump(58)):
            if not len(faces):
                continue
            info = struct.unpack_from("<h", faces, entry * 56 + 10)[0]
            texid = struct.unpack_from("<i", infos, info * 72 + 68)[0]
            uses[texid] += 1
    result = {}
    for key in sorted(uses):
        idx = struct.unpack_from("<i", texdata, key * 32 + 12)[0]
        pos = struct.unpack_from("<i", offsets, idx * 4)[0]
        result[key] = (
            strings[pos : strings.index(b"\x00", pos)]
            .decode()
            .lower()
            .replace("\\", "/")
        )
    return result


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("bsp", type=Path)
    arg.add_argument("assets", type=Path)
    arg.add_argument("faces", type=Path)
    arg.add_argument("output", type=Path)
    opts = arg.parse_args()
    opts.output.mkdir(parents=True, exist_ok=True)
    ids = json.loads(opts.faces.read_text())
    if not ids or ids != sorted(set(ids)):
        raise ValueError("expected sorted unique face ids")
    with (
        opts.bsp.open("rb") as handle,
        mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as bsp,
    ):
        sources = material_ids(bsp, ids)
        off, n = struct.unpack_from("<II", bsp, 8 + 16 * 40)
        pak_hash = sha256(bsp).hexdigest()
        source_pak = BytesIO(bsp[off : off + n])
    with zipfile.ZipFile(source_pak) as pack:
        fsys = FileSystemChain(
            ZipFileSystem(opts.bsp, pack), RawFileSystem(opts.assets)
        )
        textures = {}
        materials = []
        for texid, name in sources.items():
            path = source_path(name, ".vmt")
            with fsys[path].open_str() as f:
                parsed = Material.parse(f, path).apply_patches(fsys)
            body = ['"Patch"', "{", f'    "include" "{path}"', '    "replace"', "    {"]
            layers = {}
            for prop in ("$basetexture", "$basetexture2"):
                if prop not in parsed:
                    continue
                source = source_path(parsed[prop], ".vtf")
                if source not in textures:
                    textures[source] = bake_vtf(fsys, source, opts.output)
                output = (
                    textures[source]["output"]
                    .removeprefix("materials/")
                    .removesuffix(".vtf")
                )
                body.append(f'        "{prop}" "{output}"')
                layers[prop] = source
            if "$basetexture" not in layers:
                raise ValueError(f"{name} lacks a base texture")
            body += ["    }", "}", ""]
            alias = f"materials/yuga_dustlab/jade_{texid}.vmt"
            (opts.output / alias).write_text("\n".join(body))
            materials.append(
                dict(
                    id=texid,
                    source=name,
                    shader=parsed.shader,
                    output=alias,
                    layers=layers,
                )
            )
    data = dict(
        source_bsp_sha256=pak_hash,
        selection_sha256=sha256(opts.faces.read_bytes()).hexdigest(),
        gains_linear=list(GAINS),
        materials=materials,
        textures=list(textures.values()),
    )
    (opts.output / "bake.json").write_text(json.dumps(data, indent=2) + "\n")
    print(
        f"{len(ids)} original faces, {len(materials)} original shaders, {len(textures)} private VTFs; all frames, mip RGB and alpha checked after native encoding."
    )


if __name__ == "__main__":
    main()
