#!/usr/bin/env python3
"""Bind originals directly inspected by R2-15; no render or import."""
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "role06"
PINS = {
    "res://assets/heroes/rama-hero.glb": "140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a",
    "res://assets/heroes/rama-hero-mid.glb": "44bf3961fa52aef0b1a212dff05dcc6bda5c3cae7c9eaf00303aba9f39d45416",
    "res://assets/heroes/rama-hero-far.glb": "62e65520da49d4f81d8cf0755f77df214f7ce0929d4818c13f62555b300a8f43",
}
LIGHT = {
    "res://scripts/production_lighting.gd": "09eb9203a41b4047742c95155512d41e8df8fadfb08cfae8f3bea82b7c24cb58",
    "res://scripts/world_lighting.gd": "2020458f8e8174f1906a0b5b23a78f56a2408f5a8dd604cf5db4c7382e7a0d51",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Explicit groups document actual view_image testimony, not automatic discovery.
viewed = []
for source in ("baseline", "candidate"):
    for phase in ("day", "night"):
        for view in ("front", "three-quarter-left", "three-quarter-right", "profile", "gameplay"):
            viewed.append((f"{source}/courtyard/courtyard-{view}-{phase}.png", "final_pair"))
        for context in ("stone", "foliage"):
            viewed.append((f"{source}/{context}/{context}-three-quarter-left-{phase}.png", "final_pair"))
    for frame in range(36):
        viewed.append((f"{source}/continuity/frame-{frame:03}.png", "adjacent_frame"))
for view in ("front", "three-quarter-left", "profile"):
    viewed.append((f"candidate/form-only/courtyard-{view}-day.png", "form_only"))
for variant in ("roughness-mips", "sss-off", "directional-pcss-off", "taa-on"):
    viewed.append((f"diagnostics/{variant}/courtyard-three-quarter-left-day.png", "single_variable"))
for action in ("kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"):
    viewed.append((f"candidate/actions/action-{action}-windup.png", "rejected_cropped_action"))

# Flip only after all ten corrected originals have actually been inspected.
CORRECTED_ACTIONS_REVIEWED = True
if CORRECTED_ACTIONS_REVIEWED:
    for source in ("baseline", "candidate"):
        for action in ("kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"):
            viewed.append((f"{source}/actions-corrected/action-{action}-windup.png", "corrected_action_pair"))

inputs, shots, receipts = [], {}, {}
for rel, kind in viewed:
    path = CAPTURE / rel
    receipt = path.parent / "capture.json"
    if receipt not in receipts:
        receipts[receipt] = json.loads(receipt.read_text())
    data = receipts[receipt]
    shot = next(s for s in data["shots"] if s["file"] == path.name)
    shots[rel] = shot
    size = list(struct.unpack(">II", path.read_bytes()[16:24]))
    checks = {
        "capture_complete": data["complete"] is True,
        "capture_source_unchanged": data["source_unchanged"] is True,
        "source_maps_equal": data["source_sha256"] == data["source_after_sha256"],
        "png_hash_matches": sha(path) == shot["sha256"],
        "png_native_size": size == [1280, 960],
    }
    if rel.startswith("candidate/"):
        checks["exact_reviewed_r6_all_lods"] = all(data["source_sha256"].get(k) == v for k, v in PINS.items())
        if kind != "form_only":
            checks["exact_combined_lighting"] = all(data["source_sha256"].get(k) == v for k, v in LIGHT.items())
    inputs.append({
        "path": str(path), "relative_to_role06": rel, "kind": kind,
        "sha256": sha(path), "size": size,
        "review": "Individually viewed with view_image(detail=original)",
        "capture": str(receipt), "capture_sha256": sha(receipt),
        "shot_id": shot["id"], "render_frame": shot["render_frame"],
        "near_asset_sha256": data["source_sha256"].get("res://assets/heroes/rama-hero.glb"),
        "light": shot["light"], "checks": checks,
    })

pairs = []
for rel, kind in viewed:
    if kind in ("final_pair", "adjacent_frame", "corrected_action_pair") and rel.startswith("candidate/"):
        base, mode = rel.replace("candidate/", "baseline/", 1), "combined_form_and_zero_angular"
    elif kind == "form_only":
        base, mode = rel.replace("candidate/form-only/", "baseline/courtyard/", 1), "form_only"
    elif kind == "single_variable":
        base, mode = "baseline/courtyard/courtyard-three-quarter-left-day.png", rel.split("/")[1]
    else:
        continue
    a, b = shots[base], shots[rel]
    controls = {k: a[k] == b[k] for k in ("viewport", "camera", "player_transform", "visual_yaw", "night", "pose_pin", "face", "motion", "lod", "tree_paused", "ui_visible")}
    lights = {k: a["light"][k] == b["light"][k] for k in a["light"] if k in b["light"]}
    allowed = ["angular_distance"] if mode in ("combined_form_and_zero_angular", "directional-pcss-off") else []
    extra = {k + "_equal": a[k] == b[k] for k in ("render_settings", "skin_materials") if k in a and k in b} if mode in ("combined_form_and_zero_angular", "form_only") else {}
    pairs.append({
        "baseline": base, "candidate": rel, "mode": mode, "controls_equal": controls,
        "common_light_fields_equal": lights, "explicit_allowed_light_difference": allowed,
        "baseline_angular_distance": a["light"].get("angular_distance", "not recorded; courtyard pinned source uses 0.7"),
        "candidate_angular_distance": b["light"].get("angular_distance"),
        "unexplained_light_difference": [k for k, equal in lights.items() if not equal and k not in allowed],
        "extra_checks": extra,
    })

result = {
    "schema": 2, "task": "R2-15", "source_commit": "0437ea91edf6989ff78c1eeadb3661f4825b60f2",
    "checkpoint": "corrected_r6_final_visual_review", "reviewed_original_count": len(inputs),
    "rejected_cropped_original_count": 5, "accepted_scope_original_count": len(inputs) - 5,
    "inputs": inputs, "pairs": pairs,
    "checks_pass": all(all(r["checks"].values()) for r in inputs) and all(all(p["controls_equal"].values()) and not p["unexplained_light_difference"] and all(p["extra_checks"].values()) for p in pairs),
    "candidate_form_reviewed": True, "continuous_frames_reviewed": {"baseline": 36, "candidate": 36},
    "corrected_action_originals_reviewed": 10 if CORRECTED_ACTIONS_REVIEWED else 0,
    "ordinary_speed_recording_reviewed": False,
    "limits": ["Metadata/hash checks establish provenance, not visual improvement.",
               "72 adjacent sequence originals reviewed; ordinary-speed playback not reviewed.",
               "Named foliage station shows mixed sea/architecture, not dark foliage silhouette.",
               "Rejected cropped action originals cannot establish whole-face action quality.",
               "Review pins identify rendered source; later LOD bounds reconciliation needs its own identity/import receipt."]
}
(HERE / "reviewed-inputs.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"reviewed_original_count": len(inputs), "comparison_count": len(pairs), "checks_pass": result["checks_pass"]}))
raise SystemExit(0 if result["checks_pass"] else 1)
