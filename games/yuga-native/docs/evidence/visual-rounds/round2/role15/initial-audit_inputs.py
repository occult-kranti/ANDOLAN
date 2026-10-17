#!/usr/bin/env python3
"""Hash and bind the originals already inspected by R2-15; no render or import."""
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "role06"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


viewed = []
for phase in ("day", "night"):
    for view in ("front", "three-quarter-left", "three-quarter-right", "profile", "gameplay"):
        viewed.append(f"baseline/courtyard/courtyard-{view}-{phase}.png")
    viewed.append(f"baseline/stone/stone-three-quarter-left-{phase}.png")
for variant in ("roughness-mips", "sss-off", "directional-pcss-off", "taa-on"):
    viewed.append(f"diagnostics/{variant}/courtyard-three-quarter-left-day.png")

inputs = []
for rel in viewed:
    path = CAPTURE / rel
    receipt = path.parent / "capture.json"
    data = json.loads(receipt.read_text())
    shot = next(s for s in data["shots"] if s["file"] == path.name)
    blob = path.read_bytes()
    size = list(struct.unpack(">II", blob[16:24]))
    actual = sha(path)
    checks = {
        "capture_complete": data["complete"] is True,
        "capture_source_unchanged": data["source_unchanged"] is True,
        "source_maps_equal": data["source_sha256"] == data["source_after_sha256"],
        "png_hash_matches": actual == shot["sha256"],
        "png_native_size": size == [1280, 960],
    }
    inputs.append({
        "path": str(path), "sha256": actual, "size": size,
        "review": "Individually viewed with view_image(detail=original)",
        "capture": str(receipt), "capture_sha256": sha(receipt),
        "shot_id": shot["id"], "render_frame": shot["render_frame"],
        "near_asset_sha256": data["source_sha256"].get("res://assets/heroes/rama-hero.glb"),
        "light": shot["light"], "checks": checks,
    })

baseline = json.loads((CAPTURE / "baseline/courtyard/capture.json").read_text())
base_shot = next(s for s in baseline["shots"] if s["id"] == "courtyard-three-quarter-left-day")
pairs = []
for variant in ("roughness-mips", "sss-off", "directional-pcss-off", "taa-on"):
    data = json.loads((CAPTURE / f"diagnostics/{variant}/capture.json").read_text())
    shot = data["shots"][0]
    controls = {key: shot[key] == base_shot[key] for key in (
        "viewport", "camera", "player_transform", "visual_yaw", "night",
        "pose_pin", "face", "motion", "lod", "tree_paused", "ui_visible")}
    lights = {key: shot["light"][key] == value for key, value in base_shot["light"].items()}
    pairs.append({"variant": variant, "controls_equal": controls,
                  "common_light_fields_equal": lights,
                  "added_light_metadata": {k:v for k,v in shot["light"].items() if k not in base_shot["light"]},
                  "note": "Angular distance changes only in directional-pcss-off; baseline pinned source uses 0.7."})

result = {
    "schema": 1, "task": "R2-15", "source_commit": "0437ea91edf6989ff78c1eeadb3661f4825b60f2",
    "checkpoint": "baseline_and_single_variable_diagnostics",
    "reviewed_original_count": len(inputs), "inputs": inputs, "pairs": pairs,
    "checks_pass": all(all(r["checks"].values()) for r in inputs) and all(
        all(p["controls_equal"].values()) and all(p["common_light_fields_equal"].values()) for p in pairs),
    "candidate_form_reviewed": False, "continuous_frames_reviewed": 0,
    "ordinary_speed_recording_reviewed": False,
    "limits": ["Metadata/hash checks establish provenance, not visual improvement.",
               "Form-only, final combined source, foliage, sequence and action originals remain pending."]
}
(HERE / "reviewed-inputs.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"reviewed_original_count": len(inputs), "checks_pass": result["checks_pass"]}))
raise SystemExit(0 if result["checks_pass"] else 1)
