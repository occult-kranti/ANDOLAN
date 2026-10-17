#!/usr/bin/env python3
"""Role15 independent report/process/staging boundary probes; no engine use."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[4]
RUNNER = PROJECT / "tools/run-authoring-checks.py"
STAGER = PROJECT / "tools/stage-open-cloth.py"
spec = importlib.util.spec_from_file_location("role15_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def running(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()[0] not in ("Z", "X")
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists() or args.report.is_symlink():
        parser.error("fresh report path required")
    checks = []
    before = {str(path.relative_to(PROJECT)): runner.sha(path) for path in (RUNNER, STAGER, Path(__file__))}

    def require(value, message):
        if not value:
            raise AssertionError(message)

    def check(name, body):
        try:
            checks.append({"name": name, "passed": True, "detail": body()})
        except Exception as error:
            checks.append({"name": name, "passed": False, "detail": f"{type(error).__name__}: {error}"})

    with tempfile.TemporaryDirectory(prefix="yuga-role15-review-") as directory:
        root = Path(directory)
        serial = 0
        good = {"passed": True, "checks": [{"name": "actual", "passed": True}], "count": 1}

        def exercise(code):
            nonlocal serial
            serial += 1
            output = root / str(serial)
            output.mkdir()
            (output / "reports").mkdir()
            (output / "logs").mkdir()
            report = output / "reports/result.json"
            source = output / "child.py"
            source.write_text("import os,pathlib,subprocess,sys,time\nreport=pathlib.Path(sys.argv[1])\n" + code + "\n")
            result = runner.execute_suite("independent", [sys.executable, str(source), str(report)], report, output,
                                          env=os.environ.copy(), timeout=5)
            return result, output

        for name, raw in (
            ("contradictory duplicate summary key is rejected", '{"passed":false,"passed":true,"checks":[{"name":"actual","passed":true}],"count":1}'),
            ("contradictory duplicate check key is rejected", '{"passed":true,"checks":[{"name":"actual","passed":false,"passed":true}],"count":1}'),
        ):
            def duplicate(raw=raw):
                result, _ = exercise("report.write_text(" + repr(raw) + ")")
                require(result["passed"] is False, "exit-zero child with contradictory duplicate keys was accepted: " + raw)
                require("invalid_suite_json" in result["problems"], "duplicate report was not rejected as invalid JSON")
                return {"native_exit": result["exit_code"], "problems": result["problems"], "raw_report": raw}
            check(name, duplicate)

        def symlink_report():
            result, _ = exercise("target=report.parent/'elsewhere.json'\ntarget.write_text(" + repr(json.dumps(good)) + ")\nreport.symlink_to(target)")
            require(not result["passed"] and "missing_or_nonregular_suite_report" in result["problems"], "symlink suite report accepted")
            return {"native_exit": result["exit_code"], "problems": result["problems"]}
        check("real child cannot pass through a symlink report", symlink_report)

        def oversized_report():
            path = root / "oversized.json"
            path.write_bytes(b" " * (8 * 1024 * 1024 + 1))
            data, problems = runner.inspect_report(path)
            require(data is None and problems == ["suite_report_too_large"], "oversized report accepted")
            return {"bytes": path.stat().st_size, "problems": problems}
        check("oversized suite report is rejected before JSON decode", oversized_report)

        def clean_parent():
            code = (
                "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
                "(report.parent/'descendant.pid').write_text(str(child.pid))\n"
                "report.write_text(" + repr(json.dumps(good)) + ")\n"
                "print('clean-parent-complete',flush=True)"
            )
            result, output = exercise(code)
            pid = int((output / "reports/descendant.pid").read_text())
            end = time.monotonic() + 1
            while running(pid) and time.monotonic() < end:
                time.sleep(.02)
            require(result["passed"] and result["exit_code"] == 0, "clean parent did not preserve passing native result")
            require(not running(pid), "ordinary descendant survived a clean parent exit")
            require((output / "logs/independent.stdout").read_text() == "clean-parent-complete\n", "parent output was not retained")
            return {"native_exit": result["exit_code"], "ordinary_descendant_running": False, "timeout": result["timed_out"]}
        check("ordinary process-group descendant is retired after clean parent exit", clean_parent)

        def unit(name, source, expected):
            folder = root / name
            folder.mkdir()
            script, report = folder / "test_case.py", folder / "report.json"
            script.write_text("import unittest\n" + source)
            (folder / "neighbor_fixture.py").write_text("SENTINEL = 17\n")
            command = [sys.executable, str(RUNNER), "--unittest-child", str(script), "--report", str(report)]
            child = subprocess.run(command, capture_output=True, text=True, timeout=10)
            data = json.loads(report.read_text())
            require(data["passed"] is expected and (child.returncode == 0) is expected, "unittest native/report outcomes differ from expected")
            return {"native_exit": child.returncode, "report": data,
                    "stdout_sha256": hashlib.sha256(child.stdout.encode()).hexdigest(),
                    "stderr_sha256": hashlib.sha256(child.stderr.encode()).hexdigest()}
        check("neighboring fixture import is exercised by unittest wrapper", lambda: unit(
            "neighbor", "from neighbor_fixture import SENTINEL\nclass Case(unittest.TestCase):\n def test_neighbor(self):self.assertEqual(SENTINEL,17)\n", True))
        check("expected unittest failure is retained as unaccepted gate", lambda: unit(
            "expected-fail", "class Case(unittest.TestCase):\n @unittest.expectedFailure\n def test_expected(self):self.assertEqual(1,2)\n", False))
        check("unexpected unittest success cannot pass a gate", lambda: unit(
            "unexpected-success", "class Case(unittest.TestCase):\n @unittest.expectedFailure\n def test_unexpected(self):self.assertEqual(1,1)\n", False))

        def actual_stage():
            fixture = root / "actual-cloth-project"
            source_names = (*runner.CLOTH_FILES, "project.godot", "art/.gdignore")
            pins = {name: runner.sha(PROJECT / name) for name in source_names}
            child = subprocess.run([sys.executable, str(STAGER), "--project-output", str(fixture)], capture_output=True, text=True, timeout=10)
            receipt = json.loads(child.stdout)
            require(child.returncode == 0 and receipt["passed"] is True and receipt["engine_executed"] is False, "actual staging failed or invoked an engine")
            require(json.loads((fixture / "open-cloth-stage-manifest.json").read_text()) == receipt, "stdout receipt differs from saved manifest")
            exact = {name: runner.sha(fixture / name) for name in runner.CLOTH_FILES}
            require(all(pins[name] == exact[name] for name in exact), "cloth source copy differs")
            require({name: runner.sha(PROJECT / name) for name in source_names} == pins, "staging changed source or art ignore")
            actual = {str(path.relative_to(fixture)) for path in fixture.rglob("*") if path.is_file()}
            expected = set(runner.CLOTH_FILES) | {"project.godot", "open-cloth-stage-manifest.json"}
            require(actual == expected, "fixture includes an unexpected file")
            require(all(not path.is_symlink() for path in fixture.rglob("*")), "fixture contains a symlink")
            return {"native_exit": child.returncode, "exact_copies": exact, "fixture_files": sorted(actual),
                    "source_art_ignore_sha256": pins["art/.gdignore"], "stage_receipt": receipt}
        check("actual stager preserves eight exact files and product art ignore", actual_stage)

    after = {str(path.relative_to(PROJECT)): runner.sha(path) for path in (RUNNER, STAGER, Path(__file__))}
    result = {"schema": 1, "passed": before == after and all(row["passed"] for row in checks),
              "count": len(checks), "checks": checks, "sources_before": before, "sources_after": after,
              "checked_sources_unchanged": before == after,
              "scope": "Independent Python report/process/unittest/staging probes. No Godot, import, render, package, hardware or art acceptance."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "failed": [row["name"] for row in checks if not row["passed"]], "report": str(args.report)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
