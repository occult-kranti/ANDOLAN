"""Source 1 v21 BSP faces and displacement grids in native Hammer coordinates."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict

import numpy as np
from srctools.bsp import BSP, BSP_LUMPS
from srctools.tokenizer import Token, Tokenizer

INCH = 0.0254
# src/public/bspflags.h, SKY2D | SKY | NODRAW.
NON_RENDER_FLAGS = 0x2 | 0x4 | 0x80
FACE = np.dtype(
    [
        ("plane", "<u2"),
        ("side", "u1"),
        ("on_node", "u1"),
        ("first", "<i4"),
        ("count", "<i2"),
        ("texinfo", "<i2"),
        ("disp", "<i2"),
        ("fog", "<i2"),
        ("styles", "u1", (4,)),
        ("light", "<i4"),
        ("area", "<f4"),
        ("light_uv", "<i4", (4,)),
        ("original", "<i4"),
        ("primitives", "<u2"),
        ("first_primitive", "<u2"),
        ("smoothing", "<u4"),
    ]
)
MODEL = np.dtype(
    [
        ("mins", "<f4", (3,)),
        ("maxs", "<f4", (3,)),
        ("origin", "<f4", (3,)),
        ("head", "<i4"),
        ("first", "<i4"),
        ("count", "<i4"),
    ]
)
TEXINFO = np.dtype(
    [
        ("axes", "<f4", (2, 4)),
        ("lightaxes", "<f4", (2, 4)),
        ("flags", "<i4"),
        ("texture", "<i4"),
    ]
)
TEXDATA = np.dtype(
    [
        ("reflectivity", "<f4", (3,)),
        ("name", "<i4"),
        ("dimensions", "<i4", (2,)),
        ("view", "<i4", (2,)),
    ]
)
PRIMITIVE = np.dtype(
    [
        ("kind", "u1"),
        ("padding", "u1"),
        ("first", "<u2"),
        ("count", "<u2"),
        ("first_vert", "<u2"),
        ("num_verts", "<u2"),
    ]
)
DISP = np.dtype(
    {
        "names": ["start", "first", "tri_first", "power"],
        "formats": [("<f4", 3), "<i4", "<i4", "<i4"],
        "offsets": [0, 12, 16, 20],
        "itemsize": 176,
    }
)


def native_entities(lump):
    """Preserve property spelling and order, including the worldspawn and Source I/O keys."""
    tokens = iter(
        (token, value)
        for token, value in Tokenizer(
            lump.rstrip(b"\0").decode("cp1252"), allow_escapes=False
        )
        if token != Token.NEWLINE
    )
    entities = []
    for token, _ in tokens:
        if token != Token.BRACE_OPEN:
            raise ValueError("Expected opening entity brace")
        entity = {}
        for token, name in tokens:
            if token == Token.BRACE_CLOSE:
                break
            value_token, value = next(tokens)
            if token != Token.STRING or value_token != Token.STRING:
                raise ValueError("Expected entity property pair")
            entity[name] = value
        entities.append(entity)
    return entities


def axes(points):
    """Source x east, y north, z up to glTF x east, y up, z south."""
    return np.asarray(points)[..., [0, 2, 1]] * [1, 1, -1]


def source_transform(origin, angles, scaling=(1.0, 1.0, 1.0)):
    pitch, yaw, roll = np.deg2rad(angles)
    cp, cy, cr = np.cos([pitch, yaw, roll])
    sp, sy, sr = np.sin([pitch, yaw, roll])
    matrix = np.array(
        [
            [cy * cp, -sy * cr + cy * sp * sr, sy * sr + cy * sp * cr],
            [sy * cp, cy * cr + sy * sp * sr, -cy * sr + sy * sp * cr],
            [-sp, cp * sr, cp * cr],
        ]
    ) @ np.diag(scaling)
    s = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)
    transform = np.eye(4)
    transform[:3, :3] = s @ matrix @ s.T
    transform[:3, 3] = axes(origin) * INCH
    return transform.T.ravel().tolist()


def unit_rows(vectors):
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(lengths, 1.0e-12)


class Nav:
    """A spatial index over CS:GO navigation rectangles and their four corner heights."""

    def __init__(self, csv_path, name):
        with open(csv_path, newline="", encoding="utf8") as stream:
            rows = [r for r in csv.DictReader(stream) if r["mapName"] == name]
        self.count = len(rows)
        if not self.count:
            raise ValueError("No area records for " + name)
        starts = np.array(
            [[float(r["northWest" + dim]) for dim in "XYZ"] for r in rows]
        )
        ends = np.array([[float(r["southEast" + dim]) for dim in "XYZ"] for r in rows])
        lo, hi = np.minimum(starts, ends), np.maximum(starts, ends)
        self.areas = np.column_stack((lo, hi))
        self.corner_z = np.array(
            [
                [
                    s0[2],
                    float(r["northEastZ"]),
                    float(r["southWestZ"]),
                    s1[2],
                ]
                for r, s0, s1 in zip(rows, starts, ends)
            ]
        )
        self.row_names = [r["areaName"] for r in rows]
        self.grid = defaultdict(set)
        for i, (low, high) in enumerate(zip(lo, hi)):
            for x in range(
                int(np.floor((low[0] - 80) / 256)),
                int(np.floor((high[0] + 80) / 256)) + 1,
            ):
                for y in range(
                    int(np.floor((low[1] - 80) / 256)),
                    int(np.floor((high[1] + 80) / 256)) + 1,
                ):
                    self.grid[x, y].add(i)

    def nearby(self, positions, radius, height):
        for x, y, z in positions:
            ids = self.grid.get((int(np.floor(x / 256)), int(np.floor(y / 256))))
            if not ids:
                continue
            ids = list(ids)
            areas = self.areas[ids]
            dx = np.maximum(np.maximum(areas[:, 0] - x, x - areas[:, 3]), 0.0)
            dy = np.maximum(np.maximum(areas[:, 1] - y, y - areas[:, 4]), 0.0)
            along_x = np.clip(
                (x - areas[:, 0]) / np.maximum(areas[:, 3] - areas[:, 0], 1.0e-8), 0, 1
            )
            along_y = np.clip(
                (y - areas[:, 1]) / np.maximum(areas[:, 4] - areas[:, 1], 1.0e-8), 0, 1
            )
            nw, ne, sw, se = self.corner_z[ids].T
            target_z = (1 - along_y) * ((1 - along_x) * nw + along_x * ne) + along_y * (
                (1 - along_x) * sw + along_x * se
            )
            dz = np.abs(target_z - z)
            if np.any((dx * dx + dy * dy <= radius * radius) & (dz <= height)):
                return True
        return False


class SourceWorld:
    def __init__(self, path):
        self.bsp = BSP(str(path))
        if self.bsp.version.value != 21:
            raise ValueError("Expected a Source v21 BSP")
        # srctools handles Valve LZMA and preserves the original lump version.
        self.lumps = {
            lump.value: storage.data
            for lump, storage in self.bsp.lumps.items()
            if lump.value
            in {1, 2, 3, 6, 7, 12, 13, 14, 26, 33, 37, 38, 39, 43, 44, 48, 58}
        }

        def array(lump, dtype, shape=None):
            result = np.frombuffer(self.lumps[lump], dtype=dtype)
            return result.reshape(shape) if shape is not None else result

        self.faces = array(7, FACE)
        self.models = array(14, MODEL)
        self.surfedges = array(13, "<i4")
        self.edges = array(12, "<u2", (-1, 2))
        self.verts = array(3, "<f4", (-1, 3))
        self.planes = array(
            1, np.dtype([("normal", "<f4", 3), ("distance", "<f4"), ("kind", "<i4")])
        )
        self.texinfo = array(6, TEXINFO)
        self.texdata = array(2, TEXDATA)
        self.materials = [
            self.lumps[43][idx:]
            .split(b"\0", 1)[0]
            .decode("ascii")
            .replace("\\", "/")
            .lower()
            for idx in array(44, "<i4")
        ]
        self.disps = array(26, DISP)
        self.dispverts = array(33, "<f4", (-1, 5))
        self.primitives = array(37, PRIMITIVE)
        self.primverts = array(38, "<f4", (-1, 3))
        self.primindices = array(39, "<u2")
        self.grids = {}
        self.original_entities = native_entities(
            self.bsp.lumps[BSP_LUMPS.ENTITIES].data
        )
        self.entities = [dict(entity.items()) for entity in self.bsp.ents.entities]
        self.brush_entities = {
            int(e["model"][1:]): e
            for e in self.entities
            if e.get("model", "").startswith("*") and e["model"][1:].isdigit()
        }

    def face_meta(self, i):
        f = self.faces[i]
        ti = self.texinfo[f["texinfo"]]
        td = self.texdata[ti["texture"]]
        n = self.planes[f["plane"]]["normal"] * (-1.0 if f["side"] else 1.0)
        edges = self.surfedges[f["first"] : f["first"] + f["count"]]
        verts = self.verts[self.edges[np.abs(edges), (edges < 0).astype(np.uint8)]]
        return f, ti, td, n, verts, self.materials[td["name"]]

    def draws(self, mat, info, model):
        if mat.startswith("tools/") or (int(info["flags"]) & NON_RENDER_FLAGS):
            return False
        entity = self.brush_entities.get(model, {})
        if entity.get("classname", "") in {
            "func_areaportal",
            "func_occluder",
            "func_buyzone",
            "func_bomb_target",
            "func_clip_vphysics",
        } or entity.get("classname", "").startswith("trigger_"):
            return False
        return True

    def displacement(self, f, base, uv):
        d = self.disps[f["disp"]]
        size = (1 << int(d["power"])) + 1
        if len(base) != 4:
            raise ValueError("Displacement base must have four corners")
        first = int(np.argmin(np.linalg.norm(base - d["start"], axis=1)))
        a, b, c, e = np.roll(base, -first, axis=0)
        ua, ub, uc, ue = np.roll(uv, -first, axis=0)
        if size not in self.grids:
            s, t = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
            s, t = s.ravel()[:, None], t.ravel()[:, None]
            indices = []
            for y in range(size - 1):
                for x in range(size - 1):
                    p = y * size + x
                    if (x + y) % 2 == 0:
                        indices.extend(
                            [[p, p + size, p + 1], [p + size, p + size + 1, p + 1]]
                        )
                    else:
                        indices.extend(
                            [[p, p + size, p + size + 1], [p, p + size + 1, p + 1]]
                        )
            self.grids[size] = (s, t, np.asarray(indices, dtype=np.uint32))
        s, t, indices = self.grids[size]
        offset = d["first"]
        dv = self.dispverts[offset : offset + size * size]

        def patch(a, b, c, e):
            return (1 - t) * ((1 - s) * a + s * e) + t * ((1 - s) * b + s * c)

        points = patch(a, b, c, e) + dv[:, :3] * dv[:, 3, None]
        return points, patch(ua, ub, uc, ue), indices

    def surface(self, i):
        f, ti, td, n, verts, mat = self.face_meta(i)
        projection = ti["axes"]
        uv = (verts @ projection[:, :3].T + projection[:, 3]) / np.maximum(
            1, td["dimensions"]
        )
        if f["disp"] >= 0:
            coords, uv, indices = self.displacement(f, verts, uv)
        elif f["primitives"] & 0x7FFF:
            coords = verts
            indices = []
            for p in self.primitives[
                f["first_primitive"] : f["first_primitive"] + (f["primitives"] & 0x7FFF)
            ]:
                if p["num_verts"]:
                    raise ValueError(f"Special primitive vertices on face {i}")
                ii = self.primindices[p["first"] : p["first"] + p["count"]].astype(
                    np.uint32
                )
                if p["kind"] == 0:
                    indices.extend(ii.reshape(-1, 3))
                elif p["kind"] == 1:
                    indices.extend(
                        [
                            (ii[k + 1], ii[k], ii[k + 2])
                            if k % 2
                            else (ii[k], ii[k + 1], ii[k + 2])
                            for k in range(len(ii) - 2)
                        ]
                    )
                else:
                    raise ValueError(f"Unknown BSP primitive kind {p['kind']}")
            indices = np.asarray(indices, dtype=np.uint32)
        else:
            coords = verts
            indices = np.asarray(
                [[0, j, j + 1] for j in range(1, len(verts) - 1)], dtype=np.uint32
            )
        if not len(indices):
            return coords, np.zeros_like(coords), uv, indices, mat
        # Source windings face the opposite way from glTF. Align each triangle with the signed original plane.
        v = coords[indices]
        tri_norm = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
        reverse = (tri_norm @ n) < 0
        if reverse.any():
            indices = indices.copy()
            indices[reverse] = indices[reverse][:, [0, 2, 1]]
            tri_norm[reverse] *= -1
        normals = np.zeros_like(coords, dtype=np.float64)
        for k in range(3):
            np.add.at(normals, indices[:, k], tri_norm)
        invalid = np.linalg.norm(normals, axis=1) < 1.0e-8
        normals = unit_rows(normals)
        normals[invalid] = n
        return coords, normals, uv, indices, mat

    def classify(self, nav):
        selected = []
        summary = Counter()
        rendered = []
        for model_id, model in enumerate(self.models):
            rendered_model = []
            for i in range(model["first"], model["first"] + model["count"]):
                f, ti, td, n, verts, mat = self.face_meta(i)
                if not self.draws(mat, ti, model_id):
                    continue
                rendered_model.append(i)
                if (
                    model_id
                    or n[2] < 0.55
                    or any(
                        t in mat
                        for t in (
                            "ceiling",
                            "roof",
                            "antenna",
                            "skybox/",
                            "rollupdoor",
                            "building_ornament",
                            "trim",
                        )
                    )
                ):
                    continue
                if f["disp"] >= 0:
                    points, _, _ = self.displacement(
                        f, verts, np.zeros((len(verts), 2))
                    )
                else:
                    points = verts
                # Original displacement vertices carry the real elevation. Face centres and inset edge samples cover long stair treads.
                mid = points.mean(axis=0)
                box_samples = np.concatenate(
                    ([mid], (points[:: max(1, len(points) // 8)] * 0.80 + mid * 0.20))
                )
                authored = any(
                    t in mat
                    for t in (
                        "ground",
                        "asphalt",
                        "sand",
                        "floor",
                        "cobble",
                        "pavement",
                        "stair",
                        "sidewalk",
                    )
                )
                if nav.nearby(
                    box_samples, 72.0 if authored else 12.0, 32.0 if authored else 12.0
                ):
                    selected.append(i)
                    summary[mat] += 1
            rendered.append(rendered_model)
        return selected, rendered, dict(summary)
