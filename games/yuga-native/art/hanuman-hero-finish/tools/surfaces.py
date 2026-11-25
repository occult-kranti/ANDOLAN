"""Finish the original Hanuman costume materials without reimporting geometry or animation.

python surfaces.py source.glb output.glb
Optional --maps DIRECTORY writes the exact embedded PNGs for artist inspection.
"""
import argparse
import hashlib
import io
import json
import os
import struct
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PACK = Path(__file__).resolve().parents[1]
CLOTH = PACK.parent / "hanuman/lookdev/madder-cloth-imagegen-albedo.png"
SIZE = 512
PI = np.pi
MATERIALS = {
    "Armor · hammered bell metal": "Cuirass",
    "Edges · warm antiqued brass": "Binding",
    "Drapery · red madder dyed weave": "Madder",
    "Drapery · woven saffron silk": "Saffron",
}
PREFIX = "YUGA Hanuman finish / "


def read_gltf(path):
    data = Path(path).read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data)
    if (magic, version, length) != (b"glTF", 2, len(data)):
        raise ValueError("Expected one glTF 2.0 binary file")
    n, kind = struct.unpack_from("<I4s", data, 12)
    if kind != b"JSON":
        raise ValueError("Expected a glTF JSON chunk")
    doc = json.loads(data[20:20 + n])
    size, kind = struct.unpack_from("<I4s", data, 20 + n)
    if kind != b"BIN\0" or len(doc["buffers"]) != 1 or "uri" in doc["buffers"][0]:
        raise ValueError("Expected one embedded binary buffer")
    return doc, bytearray(data[28 + n:28 + n + size])


def write_gltf(path, doc, buf):
    buf.extend(bytes((-len(buf)) % 4))
    doc["buffers"][0]["byteLength"] = len(buf)
    meta = json.dumps(doc, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    meta += b" " * ((-len(meta)) % 4)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(struct.pack("<4sIII4s", b"glTF", 2, 28 + len(meta) + len(buf), len(meta), b"JSON"))
        tmp.write(meta)
        tmp.write(struct.pack("<I4s", len(buf), b"BIN\0"))
        tmp.write(buf)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, path)


def original_image(doc, buf, texture):
    image = doc["images"][doc["textures"][texture]["source"]]
    view = doc["bufferViews"][image["bufferView"]]
    start = view.get("byteOffset", 0)
    with Image.open(io.BytesIO(buf[start:start + view["byteLength"]])) as source:
        return np.asarray(source.convert("RGB").resize((SIZE, SIZE), Image.Resampling.LANCZOS), dtype=float) / 255


def band(d, width):
    return np.exp(-np.square(d / width))


def coords():
    return np.meshgrid((np.arange(SIZE) + .5) / SIZE, (np.arange(SIZE) + .5) / SIZE)


def tiles(image, repeat):
    part = image.resize((SIZE // repeat, SIZE // repeat), Image.Resampling.LANCZOS)
    data = np.asarray(part.convert("RGB"), dtype=float) / 255
    return np.tile(data, (repeat, repeat, 1))[:SIZE, :SIZE]


def normal_map(height, source, strength):
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * strength
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * strength
    normal = np.stack((-dx, dy, np.ones_like(dx)), -1)
    normal[..., :2] += (source[..., :2] * 2 - 1) * .5
    normal /= np.linalg.norm(normal, axis=-1)[..., None]
    return .5 + .5 * normal


def packed_roughness(roughness, metal):
    return np.stack((np.ones_like(roughness), np.clip(roughness, .04, .99),
                     np.broadcast_to(metal, roughness.shape)), -1)


def blend(base, overlay, weight):
    return base * (1 - weight[..., None]) + np.asarray(overlay) * weight[..., None]


def cloth(kind, donor, base_normal, swatch, u, v):
    # A plain field carries a narrow supplementary-weft band and repeating leaf pendants.
    turns = 10
    center = np.mod(u * turns, 1) - .5
    a = v - .79
    # Mirrored tips meet at the two ends of the leaf and the center remains open.
    t = np.clip((a + .045) / .09, 0, 1)
    width = .255 * np.sin(PI * t) ** .77
    leaf = band(abs(center) - width, .038) * ((a > -.045) & (a < .045))
    ribs = band(center + .13 * np.sin(t * PI), .027) * ((a > -.028) & (a < .030))
    braid = band(v - (.710 + .005 * np.sin(2 * PI * 20 * u)), .0038)
    braid = np.maximum(braid, band(v - (.710 - .005 * np.sin(2 * PI * 20 * u)), .0038))
    pinstripes = np.maximum(band(v - .853, .0045), band(v - .866, .0023))
    motif = np.maximum.reduce((leaf, .64 * ribs, braid, pinstripes))
    luma = swatch @ np.array([.2126, .7152, .0722])
    mottling = np.clip(luma / luma.mean(), .70, 1.31)
    if kind == "Madder":
        dyed = .39 * donor + .61 * swatch
        gold = (.66, .33, .16)
    else:
        dyed = .55 * donor + .45 * np.array([.70, .345, .106]) * mottling[..., None]
        gold = (.87, .61, .29)
    warp = .45 * np.cos(2*PI * 92*u) + .55 * np.cos(2*PI * (76*v + .042*np.sin(2*PI*13*u)))
    thread_weight = .60 if kind == "Madder" else .83
    brocade = np.clip((thread_weight + .065*warp)*motif, 0, 1)
    color = blend(dyed * (.96+.025*warp)[..., None], gold, brocade)
    height = .32*motif + .045*warp + .10*(mottling-1)
    rough = .73 - .20*motif + .057*warp - .07*(mottling-1)
    return color, normal_map(height, base_normal, 1.02), packed_roughness(rough, .04+.23*motif)


def metal(kind, donor, base_normal, u, v):
    # Chased petal pairs, bead-punched rims and sparse hammer marks. Each repeats in UV space.
    fu = u * (7 if kind == "Cuirass" else 12)
    x = np.mod(fu, 1) - .5
    y = np.mod(2*v + .15, 1)
    t = np.clip((y - .13) / .72, 0, 1)
    width = .34 * np.sin(PI*t) ** .76 * (.83+.17*t)
    petals = band(abs(x)-width, .032) * ((y>.13) & (y<.85))
    midrib = band(x - .055*np.sin(2*PI*t), .027) * ((y>.25) & (y<.72))
    rim = np.maximum(band(y-.065, .018), band(y-.938, .012))
    beading = np.exp(-np.square(np.sin(PI * fu * 3)/.41) - np.square((y-.884)/.034))
    if kind == "Binding":
        pattern = np.maximum(.63*beading, rim)
    else:
        pattern = np.maximum.reduce((petals, .64*midrib, .68*rim, beading))
    hammer = np.cos(2*PI*(11*u + .45*np.sin(2*PI*6*v))) * np.sin(2*PI*(9*v + .33*np.cos(2*PI*4*u)))
    fine = np.sin(2*PI*(59*u+17*v)) * np.cos(2*PI*(35*v-5*u))
    depression = np.maximum(0, -hammer)
    # Fresh high points retain warm alloy. Recesses oxidize to russet brown.
    patina = np.array([.58, .64, .69]) if kind=="Cuirass" else np.array([.77,.79,.76])
    base = donor*patina*(.95+.052*hammer)[...,None]
    color = blend(base, (.78,.55,.285) if kind=="Cuirass" else (.83,.63,.35), np.clip(.88*pattern,0,1))
    rough = .45+.13*depression+.026*fine-.20*pattern
    metallic = .73+.16*pattern-.10*depression
    return color, normal_map(.57*pattern + .09*hammer + .018*fine, base_normal, 1.75), packed_roughness(rough, metallic)


def accessor_values(doc, buf, index):
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    components = {"SCALAR":1, "VEC2":2, "VEC3":3}[accessor["type"]]
    dtype = np.dtype({5121:"u1", 5123:"<u2", 5125:"<u4", 5126:"<f4"}[accessor["componentType"]])
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return np.ndarray((accessor["count"],components), dtype=dtype, buffer=buf, offset=offset,
                      strides=(view.get("byteStride", components*dtype.itemsize), dtype.itemsize))


def anatomy_roughness(doc, buf, material, u, v):
    """Bake rest-space muzzle, brows, deltoids and hand polish into the donor's existing UV0."""
    parts = [prim for mesh in doc["meshes"] for prim in mesh["primitives"] if prim.get("material")==material]
    atlas = Image.new("L",(SIZE,SIZE),176)
    brush=ImageDraw.Draw(atlas)
    for primitive in parts:
        pos = accessor_values(doc,buf,primitive["attributes"]["POSITION"])
        uv = accessor_values(doc,buf,primitive["attributes"]["TEXCOORD_0"])
        tri = accessor_values(doc,buf,primitive["indices"]).reshape(-1,3)
        x,y,z = pos.T
        muzzle = np.exp(-((y-1.79)/.065)**2-((z-.235)/.13)**2-(x/.145)**2)
        cheek = np.exp(-((y-1.85)/.095)**2-((abs(x)-.118)/.075)**2-((z-.15)/.14)**2)
        shoulder = np.exp(-((y-1.50)/.16)**2-((abs(x)-.30)/.18)**2)
        forearm = np.exp(-((y-1.30)/.16)**2-((abs(x)-.55)/.25)**2)
        skin = np.clip(.71-.27*muzzle-.13*cheek-.14*shoulder-.11*forearm, .38,.79)
        coords = np.rint(uv*(SIZE-1)).astype(int)
        for indices,rough in zip(tri,skin[tri].mean(axis=1)):
            brush.polygon([tuple(p) for p in coords[indices]], fill=round(rough*255))
    soft = np.asarray(atlas.filter(ImageFilter.GaussianBlur(1.6)),dtype=float)/255
    pores = .008*np.sin(2*PI*(117*u+12*v))*np.sin(2*PI*(93*v-7*u))
    return packed_roughness(soft+pores,0.)


def png_bytes(values):
    array = np.rint(np.clip(values, 0, 1) * 255).astype(np.uint8)
    handle = io.BytesIO()
    Image.fromarray(array).save(handle, format="PNG", compress_level=6)
    return handle.getvalue()


def append_map(doc, buf, name, values, sampler, maps):
    encoded = png_bytes(values)
    if maps:
        maps.mkdir(parents=True, exist_ok=True)
        (maps / (name + ".png")).write_bytes(encoded)
    buf.extend(bytes((-len(buf)) % 4))
    view = len(doc["bufferViews"])
    doc["bufferViews"].append(dict(buffer=0, byteOffset=len(buf), byteLength=len(encoded)))
    buf.extend(encoded)
    image = len(doc["images"])
    doc["images"].append(dict(name=PREFIX+name, bufferView=view, mimeType="image/png"))
    idx = len(doc["textures"])
    doc["textures"].append(dict(source=image, sampler=sampler))
    return idx


def finish_glb(input_path, output_path, maps=None):
    """Return the output path. Preserve every original geometry/skin/motion accessor and buffer range."""
    doc, buf = read_gltf(input_path)
    if any(x.get("name","").startswith(PREFIX) for x in doc["images"]):
        raise ValueError("This asset already has the Hanuman surfacing stage")
    by_name = {m.get("name"):m for m in doc["materials"]}
    missing = set(MATERIALS) - by_name.keys()
    if missing:
        raise ValueError("Missing original Hanuman materials: " + ", ".join(sorted(missing)))
    with Image.open(CLOTH) as source:
        # The earlier matched camera review established a dense yarn scale. Four repeats
        # keep a square power-of-two tile seamless and preserve the existing donor's color.
        swatch = tiles(source, 4)
    u, v = coords()
    outdir = Path(maps) if maps else None
    for source_name, kind in MATERIALS.items():
        mat = by_name[source_name]
        pbr = mat["pbrMetallicRoughness"]
        col = pbr["baseColorTexture"]; normal = mat["normalTexture"]
        source_color = original_image(doc, buf, col["index"])
        source_normal = original_image(doc, buf, normal["index"])
        if kind in ("Madder", "Saffron"):
            color, normals, mr = cloth(kind, source_color, source_normal, swatch, u, v)
        else:
            color, normals, mr = metal(kind, source_color, source_normal, u, v)
        sampler = doc["textures"][col["index"]].get("sampler", 0)
        indices = [append_map(doc, buf, kind+'-'+key, value, sampler, outdir)
                   for key,value in (("basecolor",color),("normal",normals),("metal-rough",mr))]
        col["index"], normal["index"], pbr["metallicRoughnessTexture"] = indices[0], indices[1], {"index":indices[2]}
        pbr["metallicFactor"] = pbr["roughnessFactor"] = 1.
        normal["scale"] = .84 if kind in ("Madder","Saffron") else .89
    # The painted MakeHuman body and the new clump groom retain their original pigmentation.
    body_mat = by_name["Vanara · painted copper anatomy"]
    body = body_mat["pbrMetallicRoughness"]
    body_idx = doc["materials"].index(body_mat)
    rough = anatomy_roughness(doc, buf, body_idx, u, v)
    ri = append_map(doc, buf, "Anatomy-metal-rough", rough, 0, outdir)
    body["metallicRoughnessTexture"] = {"index": ri}
    body["roughnessFactor"] = 1.
    body_mat["normalTexture"]["scale"] = .255
    by_name["Eyes · warm sclera"]["pbrMetallicRoughness"].update(baseColorFactor=[.365,.265,.181,1],roughnessFactor=.27)
    by_name["Eyes · dark amber iris"]["pbrMetallicRoughness"].update(baseColorFactor=[.194,.060,.012,1],roughnessFactor=.25)
    write_gltf(output_path, doc, buf)
    return Path(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--maps", type=Path)
    args = parser.parse_args()
    path = finish_glb(args.source, args.output, args.maps)
    print("Wrote", path, hashlib.sha256(path.read_bytes()).hexdigest())
