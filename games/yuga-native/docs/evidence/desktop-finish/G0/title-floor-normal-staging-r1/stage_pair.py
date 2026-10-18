"""Stage one declared uniform-binding diagnostic via existing snapshot API."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
TOOLS = ROOT / "docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools"
PARENT = Path("/tmp/yuga-desktop-recovery-r1/current-project")
CHILD = Path("/tmp/yuga-title-floor-normal-r1/candidate-project")
NAME = "scripts/environment_surface_finish.gd"
OVERLAY = ROOT / "art/world-finish/title-floor-stipple-r1/environment_surface_finish.normal-depth-zero.gd"
PARENT_SHA = "6349218e2507bbf2ed7fd7d82543d464deb7c261defed2930f87995742513a19"
ORIGINAL_SHA = "eb4335695318daedc578cc9cd7e8424d329896b36149e786ae473346b642726a"
CANDIDATE_SHA = "412fed51aa0477aec6549c9d6ed51837d9dd157efa44f1dede3f3b0ae9447e5e"
HELPER_SHA = "cbd72f2b998c885398d8bb2792d610b4e084d009b0513b341d01ecede8cdfa79"
RUNNER_SHA = "6cfcc86a3efb7ed1abb52f3df88a91b39027a88c7759fc70de4657302cfdc34c"
spec = importlib.util.spec_from_file_location("graphics_snapshot", TOOLS / "snapshot.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.digest(PARENT / m.MARKER) == PARENT_SHA
parent = m.verify(PARENT)
assert m.digest(PARENT / NAME) == ORIGINAL_SHA and m.digest(OVERLAY) == CANDIDATE_SHA
assert m.digest(PARENT / "tools/graphics-six/capture_scene_anchors.gd") == HELPER_SHA
assert m.digest(TOOLS / "run_focus.py") == RUNNER_SHA
assert not CHILD.exists()
r = m.refresh(PARENT, CHILD, Path(parent["store"]), "G2-title-floor-normal-r1", OUT / "initial-source.json")
m.atomic_copy(OVERLAY, CHILD / NAME)
actual = m.inventory(CHILD)
delta = sorted(k for k in actual.keys() | parent["files"].keys() if actual.get(k) != parent["files"].get(k))
assert delta == [NAME], delta
r.update(files=actual, canonical_files=parent["files"], parent_snapshot_sha256=PARENT_SHA,
         parent_project=str(PARENT), changed_paths=delta,
         declared_runtime_overlay={NAME: {"path": str(OVERLAY), **actual[NAME]}},
         source_bytes=sum(v["bytes"] for k, v in actual.items() if not k.startswith(".godot/")),
         scope="Diagnostic only: exact four courtyard slab normal_depth bindings zero. Existing shader/maps/roughness/geometry/sky/shadows/helper/cameras unchanged. No import/render or canonical activation.")
receipt = OUT / "candidate-source.json"
assert not receipt.exists()
receipt.write_text(json.dumps(r, indent=2)+"\n")
m.atomic_copy(receipt, CHILD / m.MARKER)
m.verify(CHILD)
m.verify(PARENT)
assert m.digest(PARENT / m.MARKER) == PARENT_SHA and m.digest(ROOT / NAME) == ORIGINAL_SHA
result = {"passed": True, "baseline": str(PARENT), "candidate": str(CHILD),
          "baseline_marker_sha256": PARENT_SHA, "candidate_marker_sha256": m.digest(CHILD / m.MARKER),
          "delta": delta, "files": len(actual), "validated_imports": len(r["validated_imports"]),
          "helper_sha256": HELPER_SHA, "runner_sha256": RUNNER_SHA,
          "snapshot_api_sha256": m.digest(TOOLS / "snapshot.py"), "canonical_activated": False}
(OUT / "stage-result.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
