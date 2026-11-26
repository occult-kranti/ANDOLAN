"""Read Source studio model LOD0 with SourceIO's MIT format implementations."""

import numpy as np
from SourceIO.library.models.mdl.v49.mdl_file import MdlV49
from SourceIO.library.models.vtx.v7.vtx import Vtx
from SourceIO.library.models.vvd import Vvd
from SourceIO.library.utils import MemoryBuffer

from source_world import INCH, axes, unit_rows
from scene_builder import Assets


def model_material(assets, name, folders):
    name = Assets.normalize(name).removeprefix("materials/").removesuffix(".vmt")
    parents = [Assets.normalize(f).rstrip("/") for f in folders]
    candidates = [name] + [f + "/" + name for f in parents if f]
    for key in candidates:
        if assets.available("materials/" + key + ".vmt"):
            return key
    return name


class ModelMeshes:
    def __init__(self, scene):
        self.scene = scene
        self.cached = {}
        self.missing = set()
        self.converted_triangles = 0
        self.attributes = {}
        self.model_stats = {}
        self.fallback_skins = {}

    def load(self, path, skin=0):
        cache = (path, skin)
        if cache in self.cached:
            return self.cached[cache]
        # The map has one packaging dictionary per shared .mdl, plus skin-dependent material assignments.
        base = Assets.normalize(path).removesuffix(".mdl")
        streams = [
            self.scene.assets.read(base + s) for s in [".mdl", ".dx90.vtx", ".vvd"]
        ]
        if any(s is None for s in streams):
            self.missing.add(path)
            self.cached[cache] = None
            return None
        mdl = MdlV49.from_buffer(MemoryBuffer(streams[0]))
        vtx = Vtx.from_buffer(MemoryBuffer(streams[1]))
        vvd = Vvd.from_buffer(MemoryBuffer(streams[2]))
        if mdl.header.version not in [48, 49]:
            raise ValueError(
                f"Unhandled studio model version {mdl.header.version} on {path}"
            )
        if (
            len(
                {
                    int(check) & 0xFFFFFFFF
                    for check in (
                        mdl.header.checksum,
                        vtx.header.checksum,
                        vvd.header.checksum,
                    )
                }
            )
            != 1
        ):
            raise ValueError(f"MDL/VTX/VVD checksum mismatch on {path}")
        full = vvd.lod_data[0]
        if not 0 <= skin < mdl.header.skin_family_count:
            self.fallback_skins[f"{path}#{skin}"] = mdl.header.skin_family_count
            skin = 0
        # SourceIO truncates shared skin-table tails. The Studio header gives the full family for this LOD.
        skin_ref = np.frombuffer(
            streams[0],
            dtype="<u2",
            count=mdl.header.skin_reference_count * mdl.header.skin_family_count,
            offset=mdl.header.skin_family_offset,
        ).reshape(mdl.header.skin_family_count, mdl.header.skin_reference_count)
        primitives = []
        triangles = 0
        for part_idx, (mp, vp) in enumerate(
            zip(mdl.body_parts, vtx.body_parts, strict=True)
        ):
            if len(mp.models) != len(vp.models):
                raise ValueError("Unequal body part tables on " + path)
            if not mp.models:
                continue
            # Static props use body value zero: first model in each body part. Alternatives are not stacked.
            model, tm = mp.models[0], vp.models[0]
            if model.vertex_count == 0:
                continue
            top = tm.model_lods[0]
            for sub_idx, (sm, vm) in enumerate(
                zip(model.meshes, top.meshes, strict=True)
            ):
                out = []
                for group in vm.strip_groups:
                    local = (
                        group.vertexes["original_mesh_vertex_index"]
                        .ravel()
                        .astype(np.uint32)
                    )
                    for strip in group.strips:
                        ids = group.indices[
                            strip.index_mesh_offset : strip.index_mesh_offset
                            + strip.index_count
                        ].astype(np.uint32)
                        if strip.flags.value & 1:
                            tris = ids.reshape(-1, 3)
                        elif strip.flags.value == 0:
                            tris = np.array(
                                [
                                    (
                                        [ids[k + 1], ids[k], ids[k + 2]]
                                        if k % 2
                                        else [ids[k], ids[k + 1], ids[k + 2]]
                                    )
                                    for k in range(len(ids) - 2)
                                ],
                                dtype=np.uint32,
                            )
                        else:
                            raise ValueError(
                                f"Unexpected strip flags {strip.flags} on {path}"
                            )
                        if not len(tris):
                            continue
                        out.append(
                            local[tris] + sm.vertex_index_start + model.vertex_offset
                        )
                if not out:
                    continue
                raw_idx = np.concatenate(out)
                count = len(raw_idx)
                triangles += count
                # Source MDL front faces use clockwise winding; glTF front faces are counterclockwise.
                source_vertex_ids, indices = np.unique(
                    raw_idx[:, [0, 2, 1]], return_inverse=True
                )
                indices = indices.reshape(-1, 3).astype(np.uint32)
                v = full[source_vertex_ids]
                mat_id = (
                    skin_ref[skin, sm.material_index]
                    if skin_ref.size
                    else sm.material_index
                )
                material = model_material(
                    self.scene.assets, mdl.materials[mat_id].name, mdl.materials_paths
                )
                # Different skins of one model share geometry accessor bytes.
                ident = (path, part_idx, sub_idx)
                if ident in self.attributes:
                    prim = dict(self.attributes[ident])
                    prim["material"] = self.scene.material(material)
                else:
                    prim = self.scene.primitive(
                        axes(v["vertex"]) * INCH,
                        unit_rows(axes(v["normal"])),
                        v["uv"],
                        indices,
                        self.scene.material(material),
                        {
                            "sourceMdl": path,
                            "sourceLod": 0,
                            "bodygroup": part_idx,
                            "mesh": sub_idx,
                        },
                    )
                    self.attributes[ident] = prim
                    self.converted_triangles += count
                primitives.append(prim)
        if not primitives:
            self.cached[cache] = None
            self.model_stats[path] = 0
            return None
        mesh = self.scene.mesh(path + " #" + str(skin), primitives)
        self.cached[cache] = mesh
        self.model_stats[path] = triangles
        return mesh
