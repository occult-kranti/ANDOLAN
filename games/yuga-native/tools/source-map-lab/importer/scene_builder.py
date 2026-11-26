"""Embedded glTF 2.0 scene writer, with shared model meshes and source-material texture lookup."""

from io import BytesIO
from pathlib import Path
import json
import struct

import numpy as np
from PIL import Image
from srctools import Keyvalues
from srctools.vtf import VTF


class Assets:
    def __init__(self, pak, folders):
        self.pak = pak
        self.zip_names = {self.normalize(x): x for x in pak.namelist()}
        self.folders = [Path(p) for p in folders]
        self.cache = {}

    @staticmethod
    def normalize(name):
        return str(name).replace("\\", "/").lstrip("/").casefold()

    def available(self, name):
        key = self.normalize(name)
        if ".." in key.split("/"):
            raise ValueError("Invalid relative asset " + key)
        return key in self.zip_names or any((p / key).is_file() for p in self.folders)

    def read(self, name):
        key = self.normalize(name)
        if ".." in key.split("/"):
            raise ValueError("Invalid relative asset " + key)
        if key in self.zip_names:
            return self.pak.read(self.zip_names[key])
        for p in self.folders:
            file = p / key
            if file.is_file():
                return file.read_bytes()
        return None

    def vmt(self, name, visiting=()):
        clean = self.normalize(name).removeprefix("materials/").removesuffix(".vmt")
        if clean in self.cache:
            return self.cache[clean]
        if clean in visiting:
            raise ValueError("Material include cycle: " + clean)
        raw = self.read("materials/" + clean + ".vmt")
        params = {}
        if raw is not None:
            data = next(
                iter(
                    Keyvalues.parse(
                        raw.decode("cp1252", errors="replace"),
                        clean + ".vmt",
                        single_line=True,
                        allow_escapes=False,
                    )
                )
            )
            shader = data.name.casefold()
            if shader == "patch":
                params.update(self.vmt(data["include"], (*visiting, clean)))
                for op in ["insert", "replace"]:
                    for group in data.find_all(op):
                        for child in group:
                            if not child.has_children():
                                params[child.name] = child.value
            else:
                params["shader"] = shader
                for child in data:
                    if not child.has_children():
                        params[child.name] = child.value
        self.cache[clean] = params
        return params


class Scene:
    def __init__(self, assets, max_texture_size):
        self.assets = assets
        self.max_texture_size = max_texture_size
        self.data = bytearray()
        self.g = {
            "asset": {
                "version": "2.0",
                "generator": "YUGA Source map lab · srctools + SourceIO",
            },
            "scene": 0,
            "scenes": [{"name": "Dust II · full Source map", "nodes": []}],
            "nodes": [],
            "meshes": [],
            "materials": [],
            "textures": [],
            "images": [],
            "bufferViews": [],
            "accessors": [],
        }
        self.mat_by_key = {}
        self.tex_by_key = {}
        self.texture_issues = {}
        self.material_issues = {}

    def node(self, **data):
        idx = len(self.g["nodes"])
        self.g["nodes"].append(data)
        return idx

    def root(self, name, child):
        if child:
            self.g["scenes"][0]["nodes"].append(self.node(name=name, children=child))

    def view(self, data, target=None):
        self.data.extend(b"\0" * (-len(self.data) % 4))
        offset = len(self.data)
        self.data.extend(data)
        v = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target:
            v["target"] = target
        i = len(self.g["bufferViews"])
        self.g["bufferViews"].append(v)
        return i

    def accessor(self, x, kind, dims, target, bounds=False):
        array = np.ascontiguousarray(x, dtype="<f4" if kind == 5126 else "<u4")
        data = {
            "bufferView": self.view(array.tobytes(), target),
            "componentType": kind,
            "count": len(array),
            "type": dims,
        }
        if bounds:
            data["min"] = array.min(axis=0).tolist()
            data["max"] = array.max(axis=0).tolist()
        i = len(self.g["accessors"])
        self.g["accessors"].append(data)
        return i

    def texture(self, key, alpha):
        key = Assets.normalize(key).removeprefix("materials/").removesuffix(".vtf")
        cache = (key, alpha)
        if cache in self.tex_by_key:
            return self.tex_by_key[cache]
        data = self.assets.read("materials/" + key + ".vtf")
        if data is None:
            self.texture_issues[key] = "unresolved VTF"
            self.tex_by_key[cache] = None
            return None
        with BytesIO(data) as stream:
            tex = VTF.read(stream)
            mip = 0
            while (
                mip + 1 < tex.mipmap_count
                and max(tex.width >> mip, tex.height >> mip) > self.max_texture_size
            ):
                mip += 1
            im = tex.get(mipmap=mip).to_PIL()
            if max(im.size) > self.max_texture_size:
                im.thumbnail(
                    (self.max_texture_size, self.max_texture_size),
                    Image.Resampling.LANCZOS,
                )
            with BytesIO() as encoded:
                if alpha:
                    im.convert("RGBA").save(encoded, "PNG", compress_level=2)
                    mime = "image/png"
                else:
                    im.convert("RGB").save(encoded, "JPEG", quality=85, subsampling=0)
                    mime = "image/jpeg"
                payload = encoded.getvalue()
        vi = self.view(payload)
        ii = len(self.g["images"])
        self.g["images"].append({"bufferView": vi, "mimeType": mime, "name": key})
        ti = len(self.g["textures"])
        self.g["textures"].append({"source": ii})
        self.tex_by_key[cache] = ti
        return ti

    def material(self, name, ground=False, fallback=None):
        name = Assets.normalize(name)
        key = (name, ground)
        if key in self.mat_by_key:
            return self.mat_by_key[key]
        params = self.assets.vmt(name)
        alpha_test = params.get("$alphatest", "0").strip() not in ("0", "")
        translucent = params.get("$translucent", "0").strip() not in ("0", "")
        two_sided = params.get("$nocull", "0").strip() not in ("0", "")
        keytex = params.get("$basetexture", "")
        texture = self.texture(keytex, alpha_test or translucent) if keytex else None
        if texture is None:
            self.material_issues[name] = (
                "base texture unavailable" if params else "material unavailable"
            )
        color = (
            [1.0, 1.0, 1.0]
            if texture is not None
            else list(
                np.maximum(
                    0.075,
                    np.minimum(
                        0.9, fallback if fallback is not None else [0.65, 0.59, 0.48]
                    ),
                )
            )
        )
        pbr = {
            "baseColorFactor": [*map(float, color), 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.85,
        }
        if texture is not None:
            pbr["baseColorTexture"] = {"index": texture}
        m = {
            "name": name + (" / ground" if ground else ""),
            "pbrMetallicRoughness": pbr,
            "doubleSided": two_sided,
            "extras": {
                "sourceMaterial": name,
                "yugaGround": ground,
                "sourceShader": params.get("shader", "unknown"),
            },
        }
        if "$basetexture2" in params:
            m["extras"]["sourceSecondaryTexture"] = params["$basetexture2"]
        if alpha_test:
            m.update(
                alphaMode="MASK",
                alphaCutoff=float(
                    params.get("$alphatestreference", ".5").strip() or ".5"
                ),
            )
        elif translucent:
            m["alphaMode"] = "BLEND"
        idx = len(self.g["materials"])
        self.g["materials"].append(m)
        self.mat_by_key[key] = idx
        return idx

    def primitive(self, coords, normals, uv, indices, material, extras):
        if (
            not len(indices)
            or len(normals) != len(coords)
            or len(uv) != len(coords)
            or not np.isfinite(coords).all()
            or not np.isfinite(normals).all()
            or not np.isfinite(uv).all()
        ):
            raise ValueError("Invalid mesh geometry")
        if indices.min() < 0 or indices.max() >= len(coords):
            raise ValueError("Invalid mesh index")
        attr = {
            "POSITION": self.accessor(coords, 5126, "VEC3", 34962, True),
            "NORMAL": self.accessor(normals, 5126, "VEC3", 34962),
            "TEXCOORD_0": self.accessor(uv, 5126, "VEC2", 34962),
        }
        return {
            "attributes": attr,
            "indices": self.accessor(indices.ravel(), 5125, "SCALAR", 34963),
            "material": material,
            "extras": extras,
        }

    def mesh(self, name, primitives):
        i = len(self.g["meshes"])
        self.g["meshes"].append({"name": name, "primitives": primitives})
        return i

    def save(self, path):
        if not self.g["images"]:
            del self.g["textures"]
            del self.g["images"]
        self.g["buffers"] = [{"byteLength": len(self.data)}]
        body = json.dumps(self.g, separators=(",", ":"), ensure_ascii=False).encode()
        body += b" " * (-len(body) % 4)
        self.data.extend(b"\0" * (-len(self.data) % 4))
        with open(path, "wb") as stream:
            stream.write(
                struct.pack("<4sII", b"glTF", 2, 28 + len(body) + len(self.data))
            )
            stream.write(struct.pack("<I4s", len(body), b"JSON"))
            stream.write(body)
            stream.write(struct.pack("<I4s", len(self.data), b"BIN\0"))
            stream.write(self.data)
