#!/usr/bin/env python3
"""Client of the existing snapshot API; no engine, import or raster operations."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/evidence/desktop-finish/G0/paving-pair-staging-r1"
TOOLS = ROOT / "docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools"
PARENT = Path("/tmp/yuga-desktop-recovery-r1/compact-project-r1")
CHILD = Path("/tmp/yuga-paving-pair-r1/candidate-project")
INCLUDE = "scripts/world_ground_common.gdshaderinc"
CANDIDATE = ROOT / "art/world-finish/slab-distance-filter-r1/world_ground_common.candidate.gdshaderinc"
EXPECTED_PARENT = "a02bc44bcb09cd9b80c0afd4d5a18d42a72664e23aa4961875cb572bfb39e2b5"
EXPECTED_ORIGINAL = "b4657976ebc3f41379b05d00048bedb68269579de3956f1e25d88e841b795611"
EXPECTED_CANDIDATE = "2e84ddd1afe67c70db6d8bdc700adaa0e34bee644a20825d4ecde0a7a0f88641"
EXPECTED_HELPER = "5df5914d8cb52db79ae60ac5566fdf2314e6e1d84032832166f9fc800c2242cc"
EXPECTED_RUNNER = "6cfcc86a3efb7ed1abb52f3df88a91b39027a88c7759fc70de4657302cfdc34c"

spec = importlib.util.spec_from_file_location("graphics_snapshot", TOOLS / "snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)
assert snapshot.digest(PARENT / snapshot.MARKER) == EXPECTED_PARENT
parent = snapshot.verify(PARENT)
assert snapshot.digest(PARENT / INCLUDE) == EXPECTED_ORIGINAL
assert snapshot.digest(CANDIDATE) == EXPECTED_CANDIDATE
assert snapshot.digest(PARENT / "tools/graphics-six/capture_compact_screens.gd") == EXPECTED_HELPER
assert snapshot.digest(TOOLS / "run_focus.py") == EXPECTED_RUNNER
assert not CHILD.exists()
EVIDENCE.mkdir(parents=True, exist_ok=True)
initial = EVIDENCE / "initial-child-source.json"
assert not initial.exists()
record = snapshot.refresh(PARENT, CHILD, Path(parent["store"]),
                          "G2-paving-distance-pair-r1", initial)
snapshot.atomic_copy(CANDIDATE, CHILD / INCLUDE)
actual = snapshot.inventory(CHILD)
delta = sorted(name for name in actual.keys() | parent["files"].keys()
               if actual.get(name) != parent["files"].get(name))
assert delta == [INCLUDE], delta
record.update(files=actual, canonical_files=parent["files"],
              parent_snapshot_sha256=EXPECTED_PARENT, parent_project=str(PARENT),
              changed_paths=delta,
              declared_runtime_overlay={INCLUDE: {"path": str(CANDIDATE), **actual[INCLUDE]}},
              harness_overlays=parent.get("harness_overlays", {}),
              source_bytes=sum(v["bytes"] for k, v in actual.items() if not k.startswith(".godot/")),
              scope="Paving-only immutable child. Original eight-shot helper, authority, camera, scene timing, project, assets and read-only shared imports unchanged. No engine/import executed by staging.")
receipt = EVIDENCE / "candidate-source.json"
assert not receipt.exists()
receipt.write_text(json.dumps(record, indent=2)+"\n")
snapshot.atomic_copy(receipt, CHILD / snapshot.MARKER)
snapshot.verify(CHILD)
snapshot.verify(PARENT)
assert snapshot.digest(PARENT / snapshot.MARKER) == EXPECTED_PARENT
assert snapshot.digest(ROOT / INCLUDE) == EXPECTED_ORIGINAL
result = {"passed": True, "baseline_project": str(PARENT), "candidate_project": str(CHILD),
          "baseline_marker_sha256": EXPECTED_PARENT,
          "candidate_marker_sha256": snapshot.digest(CHILD / snapshot.MARKER),
          "pair_delta": delta, "files": len(actual),
          "validated_imports": len(record["validated_imports"]),
          "helper_sha256": EXPECTED_HELPER, "runner": str(TOOLS / "run_focus.py"),
          "runner_sha256": EXPECTED_RUNNER,
          "snapshot_api_sha256": snapshot.digest(TOOLS / "snapshot.py"),
          "compiled_store": parent["store"], "runtime_activated": False}
(EVIDENCE / "stage-result.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
