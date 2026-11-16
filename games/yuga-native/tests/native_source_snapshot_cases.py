#!/usr/bin/env python3
"""Temporary-source counterexamples for snapshot package provenance, without Godot."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
PACKAGER = PROJECT / "tools/package-native.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Use a fresh report; failed results are retained")
    checks = []
    source_before = sha(PACKAGER)
    with tempfile.TemporaryDirectory(prefix="native-snapshot-cases-") as folder:
        repository = Path(folder) / "frozen-repository"
        project = repository / "games/yuga-native"
        (project / "tools").mkdir(parents=True)
        copied_packager = project / "tools/package-native.py"
        shutil.copyfile(PACKAGER, copied_packager)
        spec = importlib.util.spec_from_file_location("snapshot_packager_under_test", copied_packager)
        packaging = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packaging)
        files = {"project.godot": b"config_version=5\n", "export_presets.cfg": b"# fixture\n",
                 "scripts/authority.gd": b"extends Node\n# uncommitted fixture bytes\n",
                 "shaders/fixture.gdshader": b"shader_type spatial;\n",
                 "scenes/fixture.tscn": b"[gd_scene format=3]\n",
                 "assets/design/fixture.json": b'{"offline":true}\n'}
        for relative, data in files.items():
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        marker_path = repository / "SOURCE_SNAPSHOT.json"
        manifest_path = repository / "SNAPSHOT-MANIFEST.json"
        git = {"head": "7162b5d0b666e4422b0bc73100e1fba947d3323f", "branch": "work/dirty-snapshot-fixture",
               "native_worktree_status": " M games/yuga-native/scripts/authority.gd\n?? games/yuga-native/assets/design/fixture.json"}
        manifest = {"schema": 1, "complete": True, "files": packaging.source_state()["files"]}
        manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        manifest_path.write_bytes(manifest_bytes)
        valid = {"schema": 1, "kind": "yuga-native-source-snapshot", "complete": True,
                 "source_repository": "/original/dirty-repository", "snapshot_repository": str(repository.resolve()),
                 "git": git, "runtime_source": packaging.source_state(),
                 "packaging_script": packaging.record(copied_packager),
                 "snapshot_manifest": packaging.record(manifest_path)}

        def write_marker(value):
            marker_path.write_text(json.dumps(value) + "\n")

        def restore():
            for name in ["SOURCE_SNAPSHOT.json", "SNAPSHOT-MANIFEST.json", "SNAPSHOT-PENDING.json", "SNAPSHOT-FAILED.json"]:
                path = repository / name
                if path.exists() or path.is_symlink():
                    path.unlink()
            for relative, data in files.items():
                (project / relative).write_bytes(data)
            extra = project / "assets/design/added.json"
            if extra.exists():
                extra.unlink()
            shutil.copyfile(PACKAGER, copied_packager)
            manifest_path.write_bytes(manifest_bytes)
            write_marker(valid)

        def synthetic_live_git(command, **_kwargs):
            if command[1:3] == ["rev-parse", "HEAD"]:
                return "0" * 40
            if command[1:3] == ["branch", "--show-current"]:
                return "unrelated-live-branch"
            return ""

        def reject(name, mutate):
            restore()
            candidate = copy.deepcopy(valid)
            mutate(candidate)
            rejected = False
            error = None
            with patch.object(packaging.subprocess, "check_output", side_effect=synthetic_live_git) as live:
                try:
                    packaging.git_context()
                except (ValueError, TypeError, AttributeError) as caught:
                    rejected = True
                    error = str(caught)
            checks.append({"case": name, "passed": rejected and live.call_count == 0,
                           "rejected": rejected, "live_git_calls": live.call_count, "error": error})

        restore()
        with patch.object(packaging.subprocess, "check_output", side_effect=synthetic_live_git) as live:
            actual = packaging.git_context()
        checks.append({"case": "valid_snapshot_preserves_exact_original_dirty_context",
                       "passed": all(actual[key] == value for key, value in git.items()) and live.call_count == 0
                       and actual["source_snapshot"]["marker_sha256"] == sha(marker_path),
                       "live_git_calls": live.call_count})

        def marker_edit(field, value):
            def change(candidate):
                candidate[field] = value
                write_marker(candidate)
            return change

        reject("wrong_snapshot_location", marker_edit("snapshot_repository", str(repository.parent / "elsewhere")))
        reject("changed_runtime_bytes", lambda _: (project / "scripts/authority.gd").write_bytes(b"extends Node\n# changed\n"))
        reject("added_runtime_file", lambda _: (project / "assets/design/added.json").write_text("{}"))
        reject("removed_runtime_file", lambda _: (project / "scripts/authority.gd").unlink())
        reject("marker_runtime_digest_mismatch", marker_edit("runtime_source", {"sha256": "0" * 64, "files": {}}))
        reject("marker_packaging_script_mismatch", marker_edit("packaging_script", {"bytes": 1, "sha256": "0" * 64}))
        reject("packaging_file_changed_after_marker", lambda _: copied_packager.write_bytes(PACKAGER.read_bytes() + b"\n# changed\n"))
        reject("snapshot_manifest_changed", lambda _: manifest_path.write_bytes(manifest_bytes + b"\n"))
        reject("malformed_git_container", marker_edit("git", []))
        reject("malformed_git_head", marker_edit("git", {**git, "head": "bad-head"}))
        reject("malformed_git_dirty_status", marker_edit("git", {**git, "native_worktree_status": []}))
        reject("missing_git_branch", marker_edit("git", {key: value for key, value in git.items() if key != "branch"}))
        reject("incomplete_marker", marker_edit("complete", False))
        reject("wrong_marker_kind", marker_edit("kind", "unrelated-copy"))
        reject("invalid_marker_json", lambda _: marker_path.write_text("{"))

        def journal_only(name):
            def change(_):
                marker_path.unlink()
                manifest_path.unlink()
                (repository / name).write_text('{"complete":false}')
            return change

        reject("pending_without_completed_marker", journal_only("SNAPSHOT-PENDING.json"))
        reject("failed_without_completed_marker", journal_only("SNAPSHOT-FAILED.json"))
        reject("manifest_without_completed_marker", lambda _: marker_path.unlink())
        reject("failed_journal_overrides_even_otherwise_valid_marker", lambda _: (repository / "SNAPSHOT-FAILED.json").write_text('{"complete":false}'))

        def dangling_marker(_):
            marker_path.unlink()
            manifest_path.unlink()
            marker_path.symlink_to(repository / "missing-marker.json")

        reject("dangling_marker_must_not_fall_back_to_live_clean_git", dangling_marker)
        checks.append({"case": "original_packager_source_unchanged", "passed": sha(PACKAGER) == source_before})
    result = {"task_id": "YUGA-HERO-6R", "round": 6, "passed": all(row["passed"] for row in checks),
              "count": len(checks), "checks": checks, "packager_sha256": source_before,
              "probe_sha256": sha(Path(__file__)),
              "scope": "Real copied package git_context/source_state in temporary minimal source trees. Only live-git fallback is replaced by an unrelated clean-context witness; any fallback for marked/failed input fails the test. No Godot, export, source mutation or package execution."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": result["passed"], "count": len(checks), "failures": [r["case"] for r in checks if not r["passed"]]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
