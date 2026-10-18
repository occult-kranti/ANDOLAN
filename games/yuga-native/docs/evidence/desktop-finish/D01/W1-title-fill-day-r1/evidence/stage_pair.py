"""Stage one declared uniform-binding diagnostic via existing snapshot API."""
import importlib.util
import json
from pathlib import Path

ROOT = Path('/workspace/ANDOLAN/games/yuga-native')
OUT = Path(__file__).resolve().parent
TOOLS = ROOT / "docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools"
PARENT = Path("/tmp/yuga-desktop-recovery-r1/current-project")
CHILD = Path("/tmp/yuga-title-fill-r1/candidate-project")
NAME = "scripts/courtyard.gd"
OVERLAY = ROOT / "art/lookdev/title-portrait-fill-r1/courtyard.candidate.gd"
PARENT_SHA = "6349218e2507bbf2ed7fd7d82543d464deb7c261defed2930f87995742513a19"
ORIGINAL_SHA = "1cd6661b3d38ac77944b308293adfb02902e1f6f05adbb6efa8d786f09c9747f"
CANDIDATE_SHA = "43f512dc6509aba77c1d7055f0fd8404054df07fc700d6261f05a725c4e80a57"
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
r = m.refresh(PARENT, CHILD, Path(parent["store"]), "G2-title-portrait-fill-r1", OUT / "initial-source.json")
m.atomic_copy(OVERLAY, CHILD / NAME)
actual = m.inventory(CHILD)
delta = sorted(k for k in actual.keys() | parent["files"].keys() if actual.get(k) != parent["files"].get(k))
assert delta == [NAME], delta
r.update(files=actual, canonical_files=parent["files"], parent_snapshot_sha256=PARENT_SHA,
         parent_project=str(PARENT), changed_paths=delta,
         declared_runtime_overlay={NAME: {"path": str(OVERLAY), **actual[NAME]}},
         source_bytes=sum(v["bytes"] for k, v in actual.items() if not k.startswith(".godot/")),
         scope="Review-only: three existing title-light parameter assignments; unchanged other source, geometry, camera, materials, sky/shadows and helper. No import/render or canonical activation.")
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
