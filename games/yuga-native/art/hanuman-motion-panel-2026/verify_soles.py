"""Measure foot-weighted vertices against the studio floor at key action frames."""
import hashlib
import json
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
SCENE = HERE / "hanuman-layered-abilities.blend"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SCENE.resolve()), load_ui=False)
    scene = bpy.context.scene
    obj = next(item for item in scene.objects
               if item.type == "MESH" and any(m.type == "ARMATURE" for m in item.modifiers))
    selected = {}
    for side in ("L", "R"):
        groups = {g.index for g in obj.vertex_groups
                  if g.name.endswith("." + side) and
                  (g.name.startswith("foot.") or g.name.startswith("toe"))}
        selected[side] = [v.index for v in obj.data.vertices
                          if sum(g.weight for g in v.groups if g.group in groups) > 0.65]
        if not selected[side]:
            raise RuntimeError("No foot-weighted vertices on " + side)
    shots = json.loads((HERE / "timeline.json").read_text())["shots"]
    samples = []
    for shot in shots:
        phases = ["start", "release", "impact", "recovery"]
        if shot["id"] == "maruti_udayana":
            phases.insert(2, "travel_midpoint")
        for phase in phases:
            if phase == "travel_midpoint":
                frame = (shot["frames"]["release"] + shot["frames"]["impact"]) // 2
            else:
                frame = shot["frames"][phase]
            scene.frame_set(frame)
            graph = bpy.context.evaluated_depsgraph_get()
            actor = obj.evaluated_get(graph)
            mesh = actor.to_mesh()
            try:
                feet = {side: min((actor.matrix_world @ mesh.vertices[i].co).z for i in indices)
                        for side, indices in selected.items()}
            finally:
                actor.to_mesh_clear()
            samples.append({"ability": shot["id"], "phase": phase, "frame": frame,
                            "lowest_foot_vertices_m": {side: round(z, 5) for side, z in feet.items()}})
    result = {
        "scene_sha256": digest(SCENE),
        "blender_version": bpy.app.version_string,
        "floor_z_m": 0.0,
        "selection": "Vertices with >0.65 combined foot and toe weights for each side.",
        "selected_vertices": {side: len(indices) for side, indices in selected.items()},
        "samples": samples,
        "limitation": "Studio-floor vertex screening, not shoe-triangle contact, collision or an in-game floor measurement."
    }
    (HERE / "evidence/sole_samples.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
