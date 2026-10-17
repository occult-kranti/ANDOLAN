#!/usr/bin/env python3
"""Run offline hero/open-art authoring gates without rendering or installing tools.

Run after the normal Godot import. Each suite has a wall deadline, private XDG
state, fresh JSON output and retained stdout/stderr. A successful process alone
cannot pass a suite. These gates do not establish visual or runtime promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
import unittest

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
LIMITS = "Offline authoring and headless material contracts only; no rendered-art, hardware-performance, human-feel, native-online or asset-promotion acceptance."
SUITES = (
    ("mikktspace", "report", "tests/hero_tangent_cases.py"),
    ("native-component-lifetime", "report", "tests/native_component_analysis_cases.py"),
    ("uv-domain-diagnostic", "self-test", "art/hero-rama-repair/diagnose_domains.py"),
    ("mesh-repair", "unittest", "tests/hero_mesh_repair_cases.py"),
    ("seam-repair", "report", "tests/hero_seam_cases.py"),
    ("deformation-proof", "report", "tests/hero_deformation_proof_cases.py"),
    ("open-art-contract", "report", "tests/open_art_wave_contract_cases.py"),
    ("open-art-reproducible", "material", "tools/build-open-art-materials.py"),
    ("cloth-stage-guards", "unittest", "tests/open_cloth_stage_cases.py"),
    ("cloth-material-lifecycle", "godot", "tests/open_cloth_material_cases.gd"),
)
ERROR_LINE = re.compile(r"^\s*(?:(?:SCRIPT )?ERROR:|Traceback \(most recent call last\):)", re.MULTILINE)
LOG_LIMIT = 16 * 1024 * 1024
CLOTH_FILES = (
    "scripts/rama_secondary_motion.gd", "shaders/rama_secondary_cloth.gdshader",
    "tests/open_cloth_material_cases.gd", "art/open-art-wave/integration/cloth_candidate.gd",
    "art/open-art-wave/materials/indigo-woven-cloth.tres",
    *("art/open-art-wave/textures/indigo-woven-" + name + ".png" for name in ("albedo", "roughness", "normal")),
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def strict_json(text: str):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON member: " + key)
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Nonfinite JSON value: " + value)

    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=nonfinite)


def authoring_sources(selected: list[tuple[str, str, str]]) -> dict:
    paths = {Path(__file__), *(PROJECT / s[2] for s in selected)}
    for folder in ("art/hero-rama-tangents", "art/hero-rama-repair", "art/open-art-wave"):
        paths.update(path for path in (PROJECT / folder).rglob("*")
                     if path.is_file() and path.suffix in (".py", ".c", ".h", ".json", ".md", ".txt", ".gd", ".tres", ".png"))
    paths.update(PROJECT / value for value in ("project.godot", "art/hero-rama-lod/glb_lod.py", "tools/build-open-art-materials.py", "tools/stage-open-cloth.py",
                 "tools/native-analysis/inspect-component.py", "scripts/rama_secondary_motion.gd", "shaders/rama_secondary_cloth.gdshader"))
    return {str(p.relative_to(PROJECT)): sha(p) if p.is_file() else None for p in sorted(paths)}


def executable(value: str) -> str:
    found = shutil.which(value)
    if found is None:
        raise ValueError("Required executable is unavailable: " + value)
    return os.path.abspath(found)  # Keep the selected venv's executable path.


def run_process(command: list[str], *, cwd: Path, env: dict, stdout: Path,
                stderr: Path, timeout: float, log_limit: int = LOG_LIMIT) -> dict:
    """Bound one dedicated POSIX process group and keep both partial streams."""
    if not math.isfinite(timeout) or timeout <= 0 or log_limit <= 0:
        raise ValueError("Positive finite timeout and log limit required")
    started = time.monotonic()
    result = {"exit_code": None, "timed_out": False, "log_limit_exceeded": False,
              "process_error": None}
    process = None
    with stdout.open("wb") as out, stderr.open("wb") as err:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=out,
                                       stderr=err, start_new_session=True)
            while process.poll() is None:
                if time.monotonic() - started >= timeout:
                    result["timed_out"] = True
                    break
                if stdout.stat().st_size > log_limit or stderr.stat().st_size > log_limit:
                    result["log_limit_exceeded"] = True
                    break
                time.sleep(.02)
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=.15)
                except subprocess.TimeoutExpired:
                    pass
            # Also retire ordinary descendants if their parent returned early.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            result["exit_code"] = process.wait(timeout=5)
        except (OSError, subprocess.SubprocessError) as error:
            result["process_error"] = f"{type(error).__name__}: {error}"
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
    result["wall_seconds"] = round(time.monotonic() - started, 3)
    result["log_limit_exceeded"] |= stdout.stat().st_size > log_limit or stderr.stat().st_size > log_limit
    return result


def inspect_report(report: Path) -> tuple[dict | None, list[str]]:
    problems = []
    if not report.is_file() or report.is_symlink():
        return None, ["missing_or_nonregular_suite_report"]
    if report.stat().st_size > 8 * 1024 * 1024:
        return None, ["suite_report_too_large"]
    try:
        data = strict_json(report.read_text())
    except (OSError, UnicodeError, ValueError):
        return None, ["invalid_suite_json"]
    if not isinstance(data, dict):
        return None, ["suite_report_is_not_object"]
    if data.get("passed") is not True:
        problems.append("suite_report_not_passed")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        problems.append("empty_or_unrecognized_suite_checks")
    elif any(not isinstance(check, dict) or check.get("passed") is not True for check in checks):
        problems.append("suite_contains_failed_or_unrecognized_check")
    if "count" in data and (type(data["count"]) is not int or not isinstance(checks, list) or data["count"] != len(checks)):
        problems.append("suite_check_count_mismatch")
    if data.get("errors"):
        problems.append("suite_reports_errors")
    return data, problems


def execute_suite(suite_id: str, command: list[str], report: Path, output: Path,
                  *, env: dict, timeout: float, cwd: Path = REPOSITORY) -> dict:
    out, err = output / "logs" / (suite_id + ".stdout"), output / "logs" / (suite_id + ".stderr")
    result = {"id": suite_id, "command": command, "report": str(report.relative_to(output)),
              "stdout": str(out.relative_to(output)), "stderr": str(err.relative_to(output)),
              "passed": False, "executed": True, **run_process(command, cwd=cwd, env=env, stdout=out, stderr=err, timeout=timeout)}
    data, problems = inspect_report(report)
    if result["exit_code"] != 0:
        problems.append("native_process_failed")
    if result["timed_out"]:
        problems.append("suite_timeout")
    if result["log_limit_exceeded"]:
        problems.append("suite_log_budget_exceeded")
    if result["process_error"]:
        problems.append("suite_process_error")
    result["logged_errors"] = [line for path in (out, err) for line in path.read_text(errors="replace").splitlines() if ERROR_LINE.match(line)]
    if result["logged_errors"]:
        problems.append("error_in_child_log")
    result["stdout_sha256"], result["stderr_sha256"] = sha(out), sha(err)
    if report.is_file():
        result["report_sha256"] = sha(report)
    if data is not None:
        result["checks"] = len(data["checks"]) if isinstance(data.get("checks"), list) else 0
    result["problems"], result["passed"] = problems, not problems
    return result


def preparation_process(name: str, command: list[str], output: Path, env: dict, timeout: float) -> dict:
    out, err = output / "logs" / (name + ".stdout"), output / "logs" / (name + ".stderr")
    result = {"command": command, "stdout": str(out.relative_to(output)), "stderr": str(err.relative_to(output)),
              **run_process(command, cwd=REPOSITORY, env=env, stdout=out, stderr=err, timeout=timeout)}
    result["logged_errors"] = [line for path in (out, err) for line in path.read_text(errors="replace").splitlines() if ERROR_LINE.match(line)]
    result["stdout_sha256"], result["stderr_sha256"] = sha(out), sha(err)
    result["passed"] = result["exit_code"] == 0 and not any(result[key] for key in ("timed_out", "log_limit_exceeded", "process_error", "logged_errors"))
    return result


def prepare_cloth_fixture(output: Path, python: str, engine: str, env: dict,
                          timeout: float, import_maps: bool) -> dict:
    """Stage exact minimal sources; never remove the product art/.gdignore."""
    fixture = output / "cloth-project"
    result = {"project": str(fixture.relative_to(output)), "passed": False, "steps": [], "checks": []}
    stage = preparation_process("cloth-stage", [python, str(PROJECT / "tools/stage-open-cloth.py"), "--project-output", str(fixture)], output, env, timeout)
    result["steps"].append(stage)
    if stage["passed"]:
        try:
            receipt = strict_json((output / stage["stdout"]).read_text())
            manifest = fixture / "open-cloth-stage-manifest.json"
            stage["receipt_passed"] = (isinstance(receipt, dict) and receipt.get("passed") is True
                and receipt.get("source_unchanged") is True and receipt.get("engine_executed") is False
                and manifest.is_file() and not manifest.is_symlink()
                and strict_json(manifest.read_text()) == receipt)
            if stage["receipt_passed"]:
                result["stage_manifest_sha256"] = sha(manifest)
        except (OSError, UnicodeError, ValueError):
            stage["receipt_passed"] = False
        stage["passed"] = stage["receipt_passed"]
    if not stage["passed"]:
        result["checks"].append({"name": "minimal_fixture_staging", "passed": False})
        return result
    copies = {source: {"source_sha256": sha(PROJECT / source), "staged_sha256": sha(fixture / source) if (fixture / source).is_file() else None} for source in CLOTH_FILES}
    result["source_copies"] = copies
    config = fixture / "project.godot"
    result["checks"].append({"name": "minimal_fixture_exact_source_copies", "passed": all(value["source_sha256"] == value["staged_sha256"] for value in copies.values())})
    result["checks"].append({"name": "minimal_fixture_project_configuration", "passed": config.is_file() and not config.is_symlink()})
    ignored = any((fixture / source).is_file() for source in (".gdignore", "art/.gdignore", "art/open-art-wave/.gdignore", "art/open-art-wave/textures/.gdignore"))
    result["checks"].append({"name": "minimal_fixture_has_no_ancestor_art_ignore", "passed": not ignored})
    if not all(check["passed"] for check in result["checks"]):
        return result
    result["config_sha256"] = sha(config)
    if import_maps:
        imported = preparation_process("cloth-import", [engine, "--headless", "--single-threaded-scene", "--path", str(fixture), "--editor", "--import", "--quit"], output, env, timeout)
        result["steps"].append(imported)
        if not imported["passed"]:
            result["checks"].append({"name": "minimal_fixture_editor_import", "passed": False})
            return result
        maps = []
        for source in CLOTH_FILES:
            if not source.endswith(".png"):
                continue
            metadata = fixture / (source + ".import")
            record = {"source": source, "passed": False}
            if metadata.is_file():
                text = metadata.read_text()
                match = re.search(r'^path="res://([^"\n]+)"$', text, re.MULTILINE)
                if match:
                    packed = fixture / match.group(1)
                    record["packed_path"] = match.group(1)
                    record["passed"] = packed.resolve().is_relative_to(fixture / ".godot/imported") and packed.is_file() and packed.stat().st_size > 0 and f'source_file="res://{source}"' in text
                    if record["passed"]:
                        record["packed_sha256"] = sha(packed)
                record["metadata_sha256"] = sha(metadata)
            maps.append(record)
        result["imported_maps"] = maps
        result["checks"].append({"name": "all_three_maps_have_real_imported_payloads", "passed": len(maps) == 3 and all(record["passed"] for record in maps)})
    result["passed"] = all(check["passed"] for check in result["checks"])
    return result


def verify_cloth_fixture(output: Path, preparation: dict) -> bool:
    fixture = output / preparation["project"]
    try:
        return (preparation.get("config_sha256") == sha(fixture / "project.godot")
            and preparation.get("stage_manifest_sha256") == sha(fixture / "open-cloth-stage-manifest.json")
            and all(value["source_sha256"] == sha(PROJECT / source) == sha(fixture / source)
                    for source, value in preparation.get("source_copies", {}).items()))
    except OSError:
        return False


class JsonResult(unittest.TextTestResult):
    """Preserve the real unittest outcomes, including errors, skips and subtests."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checks = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.checks.append({"name": test.id(), "passed": True})

    def _record(self, test, kind, error=None):
        entry = {"name": test.id(), "passed": False, "outcome": kind}
        if error is not None:
            entry["detail"] = self._exc_info_to_string(error, test)
        self.checks.append(entry)

    def addFailure(self, test, err):
        super().addFailure(test, err); self._record(test, "failure", err)

    def addError(self, test, err):
        super().addError(test, err); self._record(test, "error", err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason); self._record(test, "unexercised_skip")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err); self._record(test, "expected_failure", err)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test); self._record(test, "unexpected_success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._record(subtest, "subtest_failure", err)


def unittest_child(source: Path, report: Path) -> int:
    try:
        # Tests may intentionally import a neighboring fixture module.
        sys.path.insert(0, str(source.parent))
        spec = importlib.util.spec_from_file_location("authoring_suite", source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        result = unittest.TextTestRunner(verbosity=2, resultclass=JsonResult).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        checks = result.checks
        data = {"passed": result.wasSuccessful() and bool(checks) and all(c["passed"] for c in checks),
                "checks": checks, "tests_run": result.testsRun, "count": len(checks), "source_sha256": sha(source)}
    except Exception:
        data = {"passed": False, "checks": [{"name": "load_unittest_suite", "passed": False, "detail": traceback.format_exc()}]}
    write_json(report, data)
    return 0 if data["passed"] else 1


def material_child(source: Path, report: Path) -> int:
    # The builder has stdout JSON rather than --report. Its process still gets
    # the outer suite's independent deadline, log retention and native exit gate.
    process = subprocess.run([sys.executable, str(source), "--check"], capture_output=True, text=True)
    sys.stdout.write(process.stdout); sys.stderr.write(process.stderr)
    try:
        data = strict_json(process.stdout)
        checks = [
            {"name": "builder_native_exit", "passed": process.returncode == 0},
            {"name": "exact_material_reproduction", "passed": data.get("mode") == "check" and data.get("exact_mismatches") == []},
            {"name": "nonempty_pinned_cc0_material_outputs", "passed": type(data.get("files")) is int and data["files"] > 0 and data.get("source_license") == "CC0-1.0" and type(data.get("texture_bytes")) is int and data["texture_bytes"] > 0},
        ]
        report_data = {"passed": all(c["passed"] for c in checks), "checks": checks, "builder_report": data}
    except (ValueError, AttributeError):
        report_data = {"passed": False, "checks": [{"name": "builder_json", "passed": False}]}
    write_json(report, report_data)
    return 0 if report_data["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable, dest="python_engine")
    parser.add_argument("--engine", default="godot")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--suite", action="append", choices=[s[0] for s in SUITES])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--cloth-resource", action="store_true", help="Also load the committed material after the normal Godot import")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-cpus", type=int, default=2)
    parser.add_argument("--unittest-child", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--material-child", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--report", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.unittest_child or args.material_child:
        if args.report is None or args.report.exists() or args.report.is_symlink() or bool(args.unittest_child) == bool(args.material_child):
            parser.error("One child source and a fresh --report are required")
        return unittest_child(args.unittest_child, args.report) if args.unittest_child else material_child(args.material_child, args.report)
    selected = [s for s in SUITES if not args.suite or s[0] in args.suite]
    if args.list:
        print(json.dumps({"suites": [{"id": i, "kind": k, "source": s} for i, k, s in selected], "scope": LIMITS}, indent=2)); return 0
    if args.output is None or not math.isfinite(args.timeout) or not 0 < args.timeout <= 1800 or not 1 <= args.max_cpus <= 64:
        parser.error("A fresh --output, timeout in (0,1800] and max-cpus in [1,64] are required")
    try:
        python = executable(args.python_engine)
        engine = executable(args.engine) if any(s[1] == "godot" for s in selected) else None
        output = args.output.absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("Output already exists; use a fresh directory")
        if output.resolve().is_relative_to(REPOSITORY):
            raise ValueError("Generated reports and fixture projects must be outside the checkout")
        output.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for name in ("reports", "logs", "users"):
        (output / name).mkdir()
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:args.max_cpus])
    before = authoring_sources(selected)
    summary = {"schema": 1, "passed": False, "scope": LIMITS, "selected_suites": [s[0] for s in selected],
               "sources_before": before, "suites": [], "cloth_resource_requested": args.cloth_resource}
    write_json(output / "summary.json", summary)
    if engine is not None:
        version_out, version_err = output / "logs/engine-version.stdout", output / "logs/engine-version.stderr"
        probe = run_process([engine, "--version"], cwd=REPOSITORY, env=os.environ.copy(), stdout=version_out, stderr=version_err, timeout=min(10, args.timeout))
        summary["engine_version"] = version_out.read_text(errors="replace").strip()
        probe["stdout_sha256"], probe["stderr_sha256"] = sha(version_out), sha(version_err)
        probe["logged_errors"] = [line for path in (version_out, version_err) for line in path.read_text(errors="replace").splitlines() if ERROR_LINE.match(line)]
        summary["engine_probe"] = probe
        if probe["exit_code"] != 0 or probe["timed_out"] or probe["process_error"] or probe["log_limit_exceeded"] or probe["logged_errors"] or not summary["engine_version"].startswith("4.6.3.stable."):
            summary["error"] = "Godot4.6.3_standard_required"
            write_json(output / "summary.json", summary)
            return 1
    for suite_id, kind, source in selected:
        report = output / "reports" / (suite_id + ".json")
        env = os.environ.copy()
        user = output / "users" / suite_id
        user.mkdir()
        env.update(XDG_DATA_HOME=str(user / "data"), XDG_CONFIG_HOME=str(user / "config"), XDG_CACHE_HOME=str(user / "cache"), LP_NUM_THREADS="2", PYTHONDONTWRITEBYTECODE="1")
        preparation = None
        if kind == "godot":
            preparation = prepare_cloth_fixture(output, python, engine, env, args.timeout, args.cloth_resource)
            if not preparation["passed"]:
                write_json(report, {"passed": False, "checks": preparation["checks"], "preparation": preparation})
                summary["suites"].append({"id": suite_id, "passed": False, "executed": False, "exit_code": None, "checks": 0, "problems": ["minimal_fixture_preparation_failed"], "report": str(report.relative_to(output)), "preparation": preparation})
                write_json(output / "summary.json", summary)
                print(json.dumps({"suite": suite_id, "passed": False, "executed": False, "error": "minimal_fixture_preparation_failed"}), flush=True)
                continue
            command = [engine, "--headless", "--single-threaded-scene", "--audio-driver", "Dummy", "--path", str(output / preparation["project"]), "--script", "res://" + source, "--", "--report=" + str(report)]
            if args.cloth_resource: command.append("--candidate-resource")
        elif kind in ("unittest", "material"):
            command = [python, str(Path(__file__)), "--" + kind + "-child", str(PROJECT / source), "--report", str(report)]
        else:
            command = [python, str(PROJECT / source), "--report=" + str(report)]
            if kind == "self-test": command.append("--self-test")
        result = execute_suite(suite_id, command, report, output, env=env, timeout=args.timeout)
        if preparation is not None:
            result["preparation"] = preparation
            result["fixture_sources_unchanged"] = verify_cloth_fixture(output, preparation)
            if not result["fixture_sources_unchanged"]:
                result["passed"] = False
                result["problems"].append("fixture_sources_changed")
        summary["suites"].append(result)
        write_json(output / "summary.json", summary)
        print(json.dumps({"suite": suite_id, "passed": summary["suites"][-1]["passed"], "exit_code": summary["suites"][-1]["exit_code"]}), flush=True)
    summary["sources_after"] = authoring_sources(selected)
    summary["checked_sources_unchanged"] = before == summary["sources_after"]
    summary["passed"] = summary["checked_sources_unchanged"] and all(s["passed"] for s in summary["suites"])
    summary["checks"] = sum(s.get("checks", 0) for s in summary["suites"])
    write_json(output / "summary.json", summary)
    print(json.dumps({"passed": summary["passed"], "suites": len(selected), "checks": summary["checks"], "output": str(output), "scope": LIMITS}))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
