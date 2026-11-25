"""Reopen the assembled enhanced Hanuman studio with Blender and inspect the saved data."""

import json
import sys
from pathlib import Path

import bpy

finish = Path(__file__).resolve().parents[1]
shared = finish.parent / "four-hero-motion" / "tools" / "render"
sys.path.insert(0, str(shared))
from verify_blend import inspect

plan = json.loads((shared / "shots.json").read_text())["heroes"]["hanuman"]
model = finish / "models" / "hanuman-enhanced.glb"
receipt = inspect(finish / "blender", "hanuman", plan, model)
build = json.loads((finish / "evidence" / "build.json").read_text())
groom_materials = [m.name for m in bpy.data.materials if m.name.startswith(build["material"])]
if len(groom_materials) != 1 or receipt["rig_bones"] != 167 or receipt["source_glb_sha256"] != build["playable_sha256"]:
    raise RuntimeError("Assembled scene does not match the enhanced hero build")
receipt["groom_material"] = groom_materials[0]
receipt["blender_version"] = bpy.app.version_string
(finish / "evidence" / "editable-scene.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
