"""Reopen the saved Blender study and sample its actual rigs and control path."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
scene_file = HERE / "vanara-sena-study.blend"
out = HERE / "scene-verification.json"
if "--" in sys.argv:
    opts = sys.argv[sys.argv.index("--") + 1:]
    if opts:
        scene_file = Path(opts[0])
    if len(opts) > 1:
        out = Path(opts[1])
bpy.ops.wm.open_mainfile(filepath=str(scene_file.resolve()), load_ui=False)
scene = bpy.context.scene
rig = bpy.data.objects["YugaHeroRig"]
hero = bpy.data.objects["Hanuman skinned hero"]
target = bpy.data.objects["Left wrist · hair-to-breath path"]
ghosts = [o for o in scene.objects if o.type == "ARMATURE" and o.name.startswith("Sena guardian ")]
assert len(rig.pose.bones) == 167 and len(ghosts) == 5
assert hero.parent == rig and len(hero.material_slots) == 18
assert scene.render.fps == 30 and scene.frame_end == 91
assert all(len(g.pose.bones) == 167 for g in ghosts)
assert len(bpy.data.libraries) == 0
samples = []
for frame in (1, 7, 12, 17, 19, 20, 24, 30, 48, 69, 79, 91):
    scene.frame_set(frame)
    graph = bpy.context.evaluated_depsgraph_get()
    e = rig.evaluated_get(graph)
    wrist = e.matrix_world @ e.pose.bones["wrist.L"].head
    head = e.matrix_world @ e.pose.bones["head"].head
    target_position = target.evaluated_get(graph).matrix_world.translation
    scale = [round(g.evaluated_get(graph).scale.x, 5) for g in ghosts]
    guard = ghosts[2].evaluated_get(graph)
    guard_wrist = guard.matrix_world @ guard.pose.bones["wrist.R"].head
    samples.append({"frame":frame,"seconds":round((frame - 1) / 30,4),
                    "wrist_m":[round(v,5) for v in wrist],"head_m":[round(v,5) for v in head],
                    "target_m":[round(v,5) for v in target_position],
                    "wrist_target_distance_m":round((wrist-target_position).length,5),
                    "wrist_head_distance_m":round((wrist-head).length,5),"ghost_scale":scale,
                    "guard_wrist_m":[round(v,5) for v in guard_wrist],
                    "camera_ortho_scale":scene.camera.data.ortho_scale})
    assert all(math.isfinite(v) for v in wrist)
by_frame={s["frame"]:s for s in samples}
assert all(x < .01 for x in by_frame[1]["ghost_scale"])
assert sum(x > .4 for x in by_frame[48]["ghost_scale"]) == 5
assert all(x < .01 for x in by_frame[79]["ghost_scale"])
assert by_frame[19]["camera_ortho_scale"] == 2.75
assert abs(by_frame[20]["camera_ortho_scale"] - 8.4) < 1e-5
assert math.dist(by_frame[30]["guard_wrist_m"],by_frame[48]["guard_wrist_m"]) > .01
report = {
    "scene_sha256": hashlib.file_digest(scene_file.open("rb"), "sha256").hexdigest(),
    "blender":bpy.app.version_string,"source_joint_count":len(rig.pose.bones),
    "hero_material_slots":len(hero.material_slots),"ghost_rigs":len(ghosts),
    "packed_images":sum(bool(i.packed_file) for i in bpy.data.images),
    "unpacked_file_images":[i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file],
    "linked_libraries":len(bpy.data.libraries),"samples":samples,
    "scope":"Sampled editor scene and animated controls only; no runtime integration, exact hand/finger contact or visual quality is established."
}
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
