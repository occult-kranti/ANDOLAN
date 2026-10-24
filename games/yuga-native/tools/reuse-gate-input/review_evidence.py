#!/usr/bin/env python3
"""Verify retained R2 originals, observed states and the explicit Quit correction."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

import run as owner

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--packet", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("Use a fresh output; retain earlier reviews")
packet = args.packet.resolve()
actual = packet / "actual-r2"
r = json.loads((actual / "run.json").read_text())
checks = []


def check(name, value, evidence=None):
    checks.append({"name": name, "passed": bool(value), "evidence": evidence})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


archive = json.loads((actual / "archive.json").read_text())
bad_files = []
for entry in archive["files"]:
    data = (actual / entry["file"]).read_bytes()
    plain = gzip.decompress(data) if entry["file"].endswith(".gz") else data
    if hashlib.sha256(data).hexdigest() != entry["stored_sha256"] or hashlib.sha256(plain).hexdigest() != entry["original_sha256"]:
        bad_files.append(entry["file"])
check("all stored originals and decompressed physics bytes match", not bad_files, bad_files)
for name in ["run.py", "observer.gd"]:
    check("executed R2 " + name + " exact source retained", sha(packet / "source" / ("executed-r2-" + name + ".txt")) == r["source_sha256"]["tools/reuse-gate-input/" + name])
check("runtime source unchanged during observed journey", r["source_unchanged"])
check("imported runtime resources unchanged during journey", r["imports_unchanged"])
check("actual native Quit and cleanup exit zero", r["native_exit"] == r["cleanup_exit"] == 0)
check("native renderer reported no script or engine errors", "SCRIPT ERROR:" not in (actual / "godot.log").read_text() and "\nERROR:" not in (actual / "godot.log").read_text())
correction = json.loads((actual / "quit-keyup-correction.json").read_text())
check("supplementary Return release explicitly retained", correction["sent"] and correction["event"] == {"key_up": "Return"} and correction["before"]["focus_name"] == "Quit" and correction["before"]["navigation_keys_pressed"]["Return"], "R2 was completed with this one ordinary input correction, not an unassisted automation pass.")
check("original runner completion is interpreted with correction", r["complete"] and (actual / "quit-keyup-correction.json").exists())
check("14 manual and 10 automatic originals retained", len(r["shots"]) == 14 and len(r["automatic_shots"]) == 10)
shots = r["shots"] + r["automatic_shots"]
check("all 24 originals have exact hashes and 960x540 dimensions", all(sha(actual / shot["file"]) == shot["sha256"] and struct.unpack(">II", (actual / shot["file"]).read_bytes()[16:24]) == (960, 540) for shot in shots))
expectations = {
    "01-title": {"panels.main_panel": True, "state.hero_ready": True, "transition.phase": "done"},
    "02-world-spawn": {"scene_path": "res://scenes/confluence_world.tscn", "state.world_ready": True, "gate_input.active": True},
    "03-ghat-entry": {"gate_input.active": True, "gate_input.grounded": True},
    "04-north-approach": {"gate_input.active": True, "gate_input.grounded": True, "gate_input.gate_ray.clear": True},
    "05-ordinary-bow-release": {"gate_input.ammo": 11, "kit.release_count": 1},
    "06-north-exit": {"gate_input.active": True, "gate_input.grounded": True},
    "07-south-facing-carved-gate": {"gate_input.active": True, "gate_input.grounded": True},
    "08-south-exit": {"gate_input.active": True, "gate_input.grounded": True},
    "09-tactical-map": {"state.overview": True, "gate_input.active": False, "friendly_camera.faded_units": 0},
    "10-world-pause": {"paused": True, "panels.pause_panel": True, "gate_input.active": False, "friendly_camera.faded_units": 0},
    "11-return-title": {"scene_path": "res://scenes/courtyard.tscn", "panels.main_panel": True, "transition.phase": "done"},
    "12-settings": {"panels.settings_panel": True, "paused": True},
    "13-keyboard-controls": {"panels.controls_overlay": True, "paused": True},
    "14-final-title": {"panels.main_panel": True, "paused": False, "state.started": False},
}
for name, expected in expectations.items():
    shot = json.loads((actual / (name + ".json")).read_text())
    check("actual framebuffer state " + name, owner.ui.matches(shot, expected), expected)
samples = [json.loads(line) for line in gzip.decompress((actual / "physics.jsonl.gz").read_bytes()).decode().splitlines()]
audit = owner.audit_route(samples)
check("raw physics reproduces recorded bidirectional route acceptance", audit == r["route_audit"] and audit["passed"], audit)
check("every near-gate static sightline is clear", audit["near_gate_clear_static_rays"] == audit["near_gate_samples"] == 645)
fade = r["friendly_camera_observation"]
check("normal input triggered bounded friendly fade", fade["actual_live_fade_observed"] and fade["friendly_only"] and fade["bounded_visible_fade"] and fade["maximum_fade"] == .82, {"fading_physics_samples": fade["fading_physics_samples"], "maximum_fade": fade["maximum_fade"]})
check("natural obstruction frame carries live actor mesh details", bool(json.loads((actual / "auto-friendly-occlusion.json").read_text())["friendly_camera"]["details"]))
events = [json.loads(line)["event"] for line in (actual / "ability-events.jsonl").read_text().splitlines()]
releases = [event for event in events if event["kind"] == "release" and event["ability_id"] == "kodanda"]
check("one actual Kodanda release observed", len(releases) == 1)
check("air shot does not claim enemy damage", all(not event.get("receipts") for event in events if event.get("ability_id") == "kodanda"))
short_taps = [event["wall_seconds"] for event in r["events"] if event.get("event", {}).get("key")]
check("menu taps use complete short input edges", bool(short_taps) and max(short_taps) < .5, {"count": len(short_taps), "maximum_seconds": max(short_taps)})
report = {"passed": all(item["passed"] for item in checks), "checks": checks,
          "scope": "Bounded actual route, camera and UI evidence with one explicit supplementary native key release. Not a human playtest, hardware benchmark, new executable-release proof or whole-game acceptance.",
          "git_head": r["git_head"], "run_sha256": sha(actual / "run.json"),
          "reviewer_source_sha256": sha(Path(__file__)), "route_oracle_source_sha256": sha(Path(owner.__file__))}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"passed": report["passed"], "checks": len(checks), "failed": [item["name"] for item in checks if not item["passed"]]}))
raise SystemExit(0 if report["passed"] else 1)
