"""Build an editable, unit-correct glTF reference from a CS:GO v21 map and its original assets."""

import argparse
from collections import Counter, defaultdict
from hashlib import file_digest
import json
import os
from pathlib import Path
import sys
import time
import warnings

import numpy as np

from scene_builder import Assets, Scene
from source_overlays import add_overlays
from source_world import INCH, Nav, SourceWorld, axes, source_transform


def hash_file(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def save_json(path, obj):
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
    )


def number_list(text):
    return [float(v) for v in text.split()]


def world_geometry(scene, w, selected, rendered, report):
    all_nodes = []
    ids = set(selected)
    triangles = 0
    floor_area = 0.0
    for model_id, face_ids in enumerate(rendered):
        model = w.models[model_id]
        entity = w.brush_entities.get(model_id, {})
        name = (
            "Worldspawn"
            if model_id == 0
            else f"Brush model *{model_id} ({entity.get('classname', 'unbound')})"
        )
        groups = defaultdict(list)
        for i in face_ids:
            pts, n, uv, idx, mat = w.surface(i)
            if not len(idx):
                raise ValueError(f"Empty renderable face {i}")
            group = (mat, i in ids)
            groups[group].append((i, pts, n, uv, idx))
            if i in ids:
                v = pts[idx]
                floor_area += (
                    0.5
                    * np.linalg.norm(
                        np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1
                    ).sum()
                    * INCH**2
                )
        prims = []
        for (material, ground), records in groups.items():
            shape = []
            norms = []
            coords = []
            indices = []
            face_ledger = []
            vertices = 0
            for i, pts, n, uv, idx in records:
                shape.append(axes(pts) * INCH)
                norms.append(axes(n))
                coords.append(uv)
                indices.append(idx + vertices)
                vertices += len(pts)
                count = len(idx)
                triangles += count
                face_ledger.append([i, count])
            texinfo = w.texinfo[w.faces[records[0][0]]["texinfo"]]
            td = w.texdata[texinfo["texture"]]
            m = scene.material(material, ground, td["reflectivity"])
            prims.append(
                scene.primitive(
                    np.vstack(shape),
                    np.vstack(norms),
                    np.vstack(coords),
                    np.vstack(indices),
                    m,
                    {"sourceModel": model_id, "faceTriangleRuns": face_ledger},
                )
            )
        node = {
            "name": name,
            "extras": {
                "sourceModel": model_id,
                "sourceFirstFace": int(model["first"]),
                "sourceFaceCount": int(model["count"]),
                "classifiedRenderableFaces": len(face_ids),
                "sourceEntity": entity,
            },
        }
        if prims:
            node["mesh"] = scene.mesh(name, prims)
        if entity.get("origin") or entity.get("angles"):
            node["matrix"] = source_transform(
                number_list(entity.get("origin", "0 0 0")),
                number_list(entity.get("angles", "0 0 0")),
            )
        all_nodes.append(scene.node(**node))
    scene.root("World and brush models", all_nodes)
    report.update(
        worldTriangles=triangles,
        groundSurfaceAreaSquareMetres=round(float(floor_area), 3),
    )


def supported_nav(w, nav, selected, rendered):
    """A direct support test from each official nav patch centre to the chosen BSP triangles."""
    # The projection never credits an adjacent wall or a different storey. A nav area over a crate / mesh
    # can legitimately miss the world geometry.
    centers = []
    for ar, zs in zip(nav.areas, nav.corner_z):
        centers.append([(ar[0] + ar[3]) / 2, (ar[1] + ar[4]) / 2, float(np.mean(zs))])
    centers = np.array(centers)
    best = np.full(len(centers), np.inf)
    closest = np.full(len(centers), -1, dtype=int)
    for fi in rendered[0]:
        _, _, _, norm, _, _ = w.face_meta(fi)
        if norm[2] < 0.5:
            continue
        pts, _, _, tris, _ = w.surface(fi)
        mn = pts.min(axis=0)
        mx = pts.max(axis=0)
        cand = np.flatnonzero(
            (centers[:, 0] >= mn[0] - 0.01)
            & (centers[:, 0] <= mx[0] + 0.01)
            & (centers[:, 1] >= mn[1] - 0.01)
            & (centers[:, 1] <= mx[1] + 0.01)
            & (centers[:, 2] >= mn[2] - 24)
            & (centers[:, 2] <= mx[2] + 24)
        )
        if not len(cand):
            continue
        vv = pts[tris]
        v0 = vv[:, 1] - vv[:, 0]
        v1 = vv[:, 2] - vv[:, 0]
        det = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
        det[np.abs(det) < 1e-8] = np.nan
        for k in cand:
            x, y, z = centers[k]
            dx = x - vv[:, 0, 0]
            dy = y - vv[:, 0, 1]
            u = (dx * v1[:, 1] - dy * v1[:, 0]) / det
            v = (dy * v0[:, 0] - dx * v0[:, 1]) / det
            inside = (u >= -1.0e-5) & (v >= -1.0e-5) & (u + v <= 1.00001)
            if inside.any():
                dz = np.min(
                    np.abs((vv[:, 0, 2] + u * v0[:, 2] + v * v1[:, 2] - z)[inside])
                )
                if dz < best[k]:
                    best[k] = dz
                    closest[k] = fi
    chosen = set(selected)
    covered = np.array([i in chosen for i in closest])
    mask = best <= 18
    by = {}
    for i, place in enumerate(nav.row_names):
        rec = by.setdefault(
            place or "(unnamed)",
            {"samples": 0, "onStructuralGround": 0, "recolored": 0},
        )
        rec["samples"] += 1
        rec["onStructuralGround"] += int(mask[i])
        rec["recolored"] += int(mask[i] and covered[i])
    miss = Counter(int(closest[i]) for i in np.flatnonzero(mask & ~covered))
    return {
        "totalNavAreaCentres": len(centers),
        "structuralSupportWithin18Units": int(mask.sum()),
        "onRecoloredStructuralSupport": int((mask & covered).sum()),
        "navWithoutNearbyStructuralFloor": int((~mask).sum()),
        "missedStructuralFaces": dict(miss),
        "byPlace": by,
    }


def save_renderer_inputs(world, output):
    objectives = []
    for entity in world.original_entities:
        if entity["classname"] != "func_bomb_target":
            continue
        brush = world.models[int(entity["model"][1:])]
        origin = number_list(entity.get("origin", "0 0 0"))
        objectives.append(
            {
                "entity": entity,
                "min": (brush["mins"] + origin).tolist(),
                "max": (brush["maxs"] + origin).tolist(),
            }
        )
    save_json(output / "source-entities.json", world.original_entities)
    save_json(output / "objectives.json", objectives)


def placements(scene, w, report):
    from source_props import ModelMeshes

    models = ModelMeshes(scene)
    static_nodes = []
    entity_nodes = []
    entities_out = []
    for i, prop in enumerate(w.bsp.props):
        mesh = models.load(prop.model, prop.skin)
        scale = tuple(prop.scaling)
        node = {
            "name": f"static {i}: {Path(prop.model).stem}",
            "matrix": source_transform(tuple(prop.origin), tuple(prop.angles), scale),
            "extras": {
                "sourceStaticPropIndex": i,
                "sourceMdl": prop.model,
                "sourceSkin": prop.skin,
                "sourceTint": list(prop.tint),
            },
        }
        if mesh is not None:
            node["mesh"] = mesh
        static_nodes.append(scene.node(**node))
        if i % 500 == 0:
            print(f"Studio placements {i + 1}/{len(w.bsp.props)}", flush=True)
    scene.root("Static prop instances", static_nodes)
    for i, e in enumerate(w.entities):
        classname = e["classname"]
        model = e.get("model", "")
        origin = number_list(e.get("origin", "0 0 0"))
        if model.startswith("*"):
            idx = int(model[1:])
            b = w.models[idx]
            centroid = (b["mins"] + b["maxs"]) / 2
            centre = centroid + origin
        else:
            centre = origin
        entities_out.append(
            {
                "id": i,
                "class": classname,
                "sourceOrigin": list(map(float, origin)),
                "sourceCentre": list(map(float, centre)),
                "target": e.get("targetname", ""),
                "model": model,
            }
        )
        if not model.lower().endswith(".mdl"):
            continue
        skin = int(e.get("skin", "0"))
        mesh = models.load(model, skin)
        point = scene.node(
            name=f"entity {i}: {classname}",
            matrix=source_transform(origin, number_list(e.get("angles", "0 0 0"))),
            extras={
                "sourceEntity": i,
                "class": classname,
                "sourceMdl": model,
                "sourceSkin": skin,
            },
            **({"mesh": mesh} if mesh is not None else {}),
        )
        entity_nodes.append(point)
    scene.root("External-model entity placements", entity_nodes)
    canonical_models = {
        Assets.normalize(path): triangles
        for path, triangles in models.model_stats.items()
    }
    report.update(
        staticPropPlacements=len(static_nodes),
        staticPropsWithMeshes=sum("mesh" in scene.g["nodes"][i] for i in static_nodes),
        uniquePropPaths=len(
            canonical_models.keys()
            | {Assets.normalize(path) for path in models.missing}
        ),
        sourcePropPathSpellings=len(models.model_stats.keys() | models.missing),
        uniqueStudioLod0Triangles=sum(canonical_models.values()),
        emittedStudioLod0Triangles=models.converted_triangles,
        entityMdls=len(entity_nodes),
        sourceOutOfRangeSkinsUsingFamilyZero=models.fallback_skins,
        missingModels=sorted(models.missing),
        uniqueMeshSkinPairs=sum(v is not None for v in models.cached.values()),
    )
    return entities_out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bsp", type=Path)
    ap.add_argument("nav_csv", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--assets", type=Path, action="append", default=[])
    ap.add_argument("--sourceio-parent", type=Path)
    ap.add_argument("--texture-size", type=int, default=512)
    ap.add_argument("--world-only", action="store_true")
    ap.add_argument("--selection-only", action="store_true")
    args = ap.parse_args()
    if args.texture_size < 1:
        ap.error("--texture-size must be positive")
    if args.sourceio_parent:
        sys.path.insert(0, str(args.sourceio_parent.resolve()))
    args.output.mkdir(parents=True, exist_ok=True)

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=UserWarning, module="SourceIO")
    start = time.monotonic()
    w = SourceWorld(args.bsp)
    nav = Nav(args.nav_csv, args.bsp.stem)
    selected, rendered, classes = w.classify(nav)
    support = supported_nav(w, nav, selected, rendered)
    save_json(args.output / "floor-faces.json", selected)
    save_json(args.output / "floor-support.json", support)
    report = {
        "schema": 1,
        "bspSha256": hash_file(args.bsp),
        "navCsvSha256": hash_file(args.nav_csv),
        "nativeAxis": "X east, Y north, Z up",
        "gltfAxis": "X east, Y up, Z south; metres",
        "unitMetres": INCH,
        "sourceFaces": len(w.faces),
        "renderableFaces": sum(map(len, rendered)),
        "sourceBrushModels": len(w.models),
        "sourceDisplacements": len(w.disps),
        "sourceGroundFaces": len(selected),
        "groundFaceMaterialCounts": classes,
        "worldFacesExcluded": len(w.faces) - sum(map(len, rendered)),
        "skyCamera": next(
            (e for e in w.entities if e["classname"] == "sky_camera"), {}
        ),
        "originalMaterials": len(w.materials),
        "textureMipLimit": args.texture_size,
    }
    if args.selection_only:
        print(json.dumps(support))
        return
    save_renderer_inputs(w, args.output)
    scene = Scene(Assets(w.bsp.pakfile, args.assets), args.texture_size)
    world_geometry(scene, w, selected, rendered, report)
    print("All brush/displacement render surfaces built", flush=True)
    add_overlays(scene, w, report)
    if args.world_only:
        file = "dust2-world.glb"
    else:
        ents = placements(scene, w, report)
        save_json(args.output / "entities.json", ents)
        file = "dust2-baseline.glb"
    report.update(
        materials=len(scene.g["materials"]),
        images=len(scene.g["images"]),
        materialIssues=scene.material_issues,
        textureIssues=scene.texture_issues,
    )
    scene.g["extras"] = {
        "sourceBspSha256": report["bspSha256"],
        "units": "metres",
        "sourceGame": "Counter-Strike: Global Offensive",
    }
    tmp = args.output / (file + ".partial")
    scene.save(tmp)
    os.replace(tmp, args.output / file)
    report["glb"] = file
    report["glbSha256"] = hash_file(args.output / file)
    report["glbBytes"] = (args.output / file).stat().st_size
    save_json(
        args.output
        / ("world-report.json" if args.world_only else "import-report.json"),
        report,
    )
    print(
        f"Wrote {file} ({report['glbBytes']:,} bytes, {time.monotonic() - start:.1f}s).",
        flush=True,
    )


if __name__ == "__main__":
    main()
