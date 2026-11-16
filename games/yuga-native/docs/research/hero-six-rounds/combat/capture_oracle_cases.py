#!/usr/bin/env python3
"""Independent adverse cases for the corrected capture HUD phase oracle."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[6]
PROJECT = ROOT / "games/yuga-native"
CAPTURE = PROJECT / "docs/research/hero-six-rounds/root/hero-capture-r1"
SNAPSHOT = ROOT / ".local-tools/review/hero-six-r1-source"
spec = importlib.util.spec_from_file_location("capture_runner_under_test", PROJECT / "tools/run-rama-gameplay.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
report = json.loads((CAPTURE / "rama-gameplay-review.json").read_text())
rules = json.loads((SNAPSHOT / "assets/design/rama-ability-kit.json").read_text())
labels = {row["id"]: row["label"] for row in rules["abilities"]}
checks = []


def check(name, passed):
    checks.append({"case": name, "passed": passed})


runner.validate(report, CAPTURE, SNAPSHOT, False)
check("all_363_original_frames_and_25_stills_validate", True)
for index in [0, 5, 45, 64, 100, 121, 153, 270, 287, 288, 316, 362]:
    truth = report["frames"][index]["truth"]
    check(f"independent_phase_expected_frame_{index}", runner.expected_hud_notice(truth, labels) == truth["displayed_notice"])

adverse = [
    ("premature_recovery_during_windup", 0, lambda t: t.update(displayed_notice="Kodanda · RECOVERING")),
    ("stale_drawing_after_authority_release", 5, lambda t: t.update(displayed_notice="Kodanda · DRAWING")),
    ("old_event_label_is_not_current_hud_phase", 5, lambda t: t.update(displayed_notice="Kodanda · released")),
    ("foreign_ability_label", 64, lambda t: t.update(displayed_notice="Dawn Volley · RECOVERING")),
    ("false_release_flag", 64, lambda t: t["casts"][0].update(released=False)),
    ("runtime_event_disagrees_with_phase", 64, lambda t: t.update(runtime_notice="Piercing Dawn · drawing")),
    ("duplicate_committed_action", 0, lambda t: t["casts"].append(copy.deepcopy(t["casts"][0]))),
    ("stale_recovery_after_return_to_ready", 287, lambda t: t.update(displayed_notice="Guardian Circle · RECOVERING")),
]
for name, index, mutate in adverse:
    candidate = copy.deepcopy(report["frames"][index]["truth"])
    mutate(candidate)
    try:
        rejected = runner.expected_hud_notice(candidate, labels) != candidate["displayed_notice"]
    except ValueError:
        rejected = True
    check(name, rejected)

candidate = copy.deepcopy(report)
candidate["frames"][0]["image"]["sha256"] = "0" * 64
try:
    runner.validate(candidate, CAPTURE, SNAPSHOT, False)
    rejected = False
except ValueError:
    rejected = True
check("original_image_hash_guard_still_rejects_mutation", rejected)

result = {"task_id": "YUGA-HERO-6R", "round": 5, "passed": all(c["passed"] for c in checks),
          "count": len(checks), "checks": checks,
          "runner_sha256": hashlib.sha256((PROJECT / "tools/run-rama-gameplay.py").read_bytes()).hexdigest(),
          "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "capture_report_sha256": hashlib.sha256((CAPTURE / "rama-gameplay-review.json").read_bytes()).hexdigest(),
          "scope": "Strict phase-copy correction tested against existing frozen original capture and adverse in-memory reports. Frozen runtime, images and report remain unchanged."}
destination = Path(__file__).parent / "round5/capture-oracle-cases.json"
with destination.open("x") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
print(json.dumps({"passed": result["passed"], "checks": len(checks), "report": str(destination)}))
raise SystemExit(0 if result["passed"] else 1)
