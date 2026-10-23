"""Independent read of retained rig-only .blend, without import or source mutation."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

output = Path(sys.argv[sys.argv.index("--") + 1])
assert not output.exists(), "fresh report required"
rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
rig = rigs[0]
rows = [{"name": b.name, "parent": b.parent.name if b.parent else None,
         "rest": [list(row) for row in b.matrix_local]} for b in rig.data.bones]
signature = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
actions = {}
for action in bpy.data.actions:
    curves = [{"path": f.data_path, "index": f.array_index,
               "keys": [[*p.co] for p in f.keyframe_points]} for f in action.fcurves]
    actions[action.name] = hashlib.sha256(json.dumps(curves, sort_keys=True).encode()).hexdigest()
properties = {key: bpy.context.scene[key] for key in bpy.context.scene.keys()}
checks = {"one_rig": len(rigs) == 1, "164_bones": len(rig.data.bones) == 164,
          "nine_embedded_actions": len(actions) == 9,
          "no_meshes_or_images": len(bpy.data.meshes) == 0 and len(bpy.data.images) == 0,
          "external_23_runtime_clips": bool(properties["runtime_23_clips_are_external"]),
          "authoring_only": bool(properties["authoring_template_only"]) and not properties["finished_hero"]}
report = {"schema_version": 1, "scope": "Independent actual saved-Blender reopen; rig-only scaffold, no new mesh/finished hero.",
          "blend_path": bpy.data.filepath, "blend_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "blender": bpy.app.version_string, "rig_signature_sha256": signature,
          "actions": actions, "scene_properties": properties, "checks": checks, "passed": all(checks.values())}
output.write_text(json.dumps(report, indent=2) + "\n")
print("INDEPENDENT_BLENDER_REOPEN", json.dumps(checks))
assert report["passed"]
