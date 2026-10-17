#!/usr/bin/env python3
"""Exercise authoring runner failure boundaries with real isolated child processes."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tools/run-authoring-checks.py"
spec = importlib.util.spec_from_file_location("authoring_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def running(pid: int) -> bool:
    try:
        return Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()[0] not in ("Z", "X")
    except FileNotFoundError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Use a fresh report path")
    checks = []

    def check(name, body):
        try:
            detail = body()
            checks.append({"name": name, "passed": True, "detail": detail})
        except Exception as error:
            checks.append({"name": name, "passed": False, "detail": f"{type(error).__name__}: {error}"})

    def require(condition, message="fixture outcome did not match contract"):
        if not condition:
            raise AssertionError(message)

    with tempfile.TemporaryDirectory(prefix="yuga-authoring-runner-") as folder:
        root = Path(folder)
        serial = 0
        good = {"passed": True, "checks": [{"name": "actually_exercised", "passed": True}], "count": 1}

        def exercise(code, *, timeout=5):
            nonlocal serial
            serial += 1
            output = root / str(serial)
            output.mkdir(); (output / "logs").mkdir(); (output / "reports").mkdir()
            source = output / "child.py"
            source.write_text("import json,os,pathlib,sys,time,signal,subprocess\nreport=pathlib.Path(sys.argv[1])\n" + code + "\n")
            report = output / "reports/result.json"
            result = runner.execute_suite("fixture", [sys.executable, str(source), str(report)], report, output, env=os.environ.copy(), timeout=timeout)
            return result, output

        def accepted():
            result, _ = exercise("report.write_text(" + repr(json.dumps(good)) + ")\nprint('executed-fixture')")
            require(result["passed"] and result["checks"] == 1 and result["exit_code"] == 0)
            return result
        check("actual passing report and native process accepted", accepted)

        def failed_exit():
            result, output = exercise("report.write_text(" + repr(json.dumps(good)) + ")\nprint('preserved-out',flush=True)\nprint('preserved-err',file=sys.stderr,flush=True)\nsys.exit(9)")
            require(not result["passed"] and result["exit_code"] == 9 and "native_process_failed" in result["problems"])
            require((output / "logs/fixture.stdout").read_text() == "preserved-out\n" and (output / "logs/fixture.stderr").read_text() == "preserved-err\n")
            return {"exit_code": result["exit_code"], "problems": result["problems"]}
        check("passing JSON cannot hide nonzero native exit and both logs survive", failed_exit)

        bad_reports = [
            ("failed summary", {"passed": False, "checks": [{"passed": True}]}),
            ("failed assertion", {"passed": True, "checks": [{"passed": False}]}),
            ("empty checks", {"passed": True, "checks": []}),
            ("check is not object", {"passed": True, "checks": [True]}),
            ("checks is count", {"passed": True, "checks": 99}),
            ("truthy nonboolean pass", {"passed": 1, "checks": [{"passed": True}]}),
            ("count mismatch", {"passed": True, "checks": [{"passed": True}], "count": 2}),
            ("boolean count", {"passed": True, "checks": [{"passed": True}], "count": True}),
            ("errors present", {"passed": True, "checks": [{"passed": True}], "errors": ["fixture"]}),
            ("top-level array", []),
        ]
        for name, data in bad_reports:
            def case(data=data):
                result, _ = exercise("report.write_text(" + repr(json.dumps(data)) + ")")
                require(not result["passed"] and result["exit_code"] == 0)
                return result["problems"]
            check("reject " + name + " despite native exit zero", case)
        for name, raw in [("malformed JSON", "{"), ("nonfinite JSON", '{"passed":true,"checks":[{"passed":true}],"untrusted":NaN}'),
                          ("contradictory duplicate summary key", '{"passed":false,"passed":true,"checks":[{"passed":true}],"count":1}'),
                          ("contradictory duplicate nested assertion key", '{"passed":true,"checks":[{"passed":false,"passed":true}],"count":1}')]:
            def case(raw=raw):
                result, _ = exercise("report.write_text(" + repr(raw) + ")")
                require(not result["passed"] and "invalid_suite_json" in result["problems"])
                return result["problems"]
            check("reject " + name, case)

        def absent():
            result, _ = exercise("print('no receipt')")
            require(not result["passed"] and "missing_or_nonregular_suite_report" in result["problems"])
            return result["problems"]
        check("zero exit without report is failure", absent)
        for stream in ("stdout", "stderr"):
            def case(stream=stream):
                target = "sys.stdout" if stream == "stdout" else "sys.stderr"
                result, _ = exercise("report.write_text(" + repr(json.dumps(good)) + ")\nprint('  SCRIPT ERROR: fixture-invalid',file=" + target + ")")
                require(not result["passed"] and result["logged_errors"] == ["  SCRIPT ERROR: fixture-invalid"] and "error_in_child_log" in result["problems"])
                return result["logged_errors"]
            check("engine error on " + stream + " rejects otherwise passing JSON", case)

        def timeout():
            child = "import os,pathlib,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);pathlib.Path(os.environ['YUGA_FIXTURE_CHILD_PID']).write_text(str(os.getpid()));time.sleep(60)"
            pidfile = root / "descendant.pid"
            old = os.environ.get("YUGA_FIXTURE_CHILD_PID")
            os.environ["YUGA_FIXTURE_CHILD_PID"] = str(pidfile)
            try:
                result, output = exercise("signal.signal(signal.SIGTERM,signal.SIG_IGN)\nsubprocess.Popen([sys.executable,'-c'," + repr(child) + "])\nprint('partial-out',flush=True)\nprint('partial-err',file=sys.stderr,flush=True)\ntime.sleep(60)", timeout=.5)
            finally:
                if old is None: os.environ.pop("YUGA_FIXTURE_CHILD_PID", None)
                else: os.environ["YUGA_FIXTURE_CHILD_PID"] = old
            require(result["timed_out"] and not result["passed"] and "suite_timeout" in result["problems"])
            require(pidfile.exists() and not running(int(pidfile.read_text())))
            require("partial-out" in (output / "logs/fixture.stdout").read_text() and "partial-err" in (output / "logs/fixture.stderr").read_text())
            return {"timeout": True, "descendant_running": False, "exit_code": result["exit_code"]}
        check("timeout kills TERM-ignoring parent and ordinary descendant with partial logs retained", timeout)

        def budget():
            out, err = root / "budget.stdout", root / "budget.stderr"
            result = runner.run_process([sys.executable, "-c", "import os,time;os.write(1,b'x'*65536);time.sleep(30)"], cwd=root, env=os.environ.copy(), stdout=out, stderr=err, timeout=5, log_limit=32768)
            require(result["log_limit_exceeded"] and result["exit_code"] != 0 and out.stat().st_size >= 65536)
            return {"log_limit_exceeded": True, "retained_bytes": out.stat().st_size}
        check("excessive child logging is bounded and retained", budget)

        def absent_binary():
            output = root / "missing-binary"; output.mkdir(); (output / "reports").mkdir(); (output / "logs").mkdir()
            result = runner.execute_suite("fixture", [str(root / "not-an-executable")], output / "reports/result.json", output, env=os.environ.copy(), timeout=1)
            require(not result["passed"] and result["process_error"] and "suite_process_error" in result["problems"])
            require((output / "logs/fixture.stdout").exists() and (output / "logs/fixture.stderr").exists())
            return result["problems"]
        check("spawn failure produces a retained failed suite", absent_binary)

        def unit_fixture(name, source, expected):
            directory = root / name; directory.mkdir()
            script, report = directory / "unit.py", directory / "unit.json"
            script.write_text("import unittest\n" + source)
            process = subprocess.run([sys.executable, str(RUNNER), "--unittest-child", str(script), "--report", str(report)], capture_output=True, text=True, timeout=10)
            data = json.loads(report.read_text())
            require(data["passed"] is expected and (process.returncode == 0) is expected)
            return data
        check("real unittest success and positive subtests create JSON assertions", lambda: unit_fixture("unit-pass", "class Tests(unittest.TestCase):\n def test_pass(self):\n  for n in range(3):\n   with self.subTest(n=n):self.assertGreaterEqual(n,0)\n", True))
        def unit_fail():
            data = unit_fixture("unit-fail", "class Tests(unittest.TestCase):\n def test_subtest(self):\n  with self.subTest(n=3):self.assertEqual(3,4)\n def test_error(self):raise RuntimeError('independent-fixture-error')\n", False)
            require({entry["outcome"] for entry in data["checks"]} == {"subtest_failure", "error"})
            return data
        check("real unittest subtest failure and exception are preserved", unit_fail)
        check("empty unittest discovery cannot pass", lambda: unit_fixture("unit-empty", "", False))
        check("skipped unittest cannot establish an exercised gate", lambda: unit_fixture("unit-skip", "class Tests(unittest.TestCase):\n @unittest.skip('not exercised')\n def test_skip(self):pass\n", False))

        def duplicate_builder():
            directory = root / "duplicate-builder"; directory.mkdir()
            source, report = directory / "builder.py", directory / "report.json"
            raw = '{"mode":"check","files":4,"texture_bytes":1,"source_license":"CC0-1.0","exact_mismatches":["wrong"],"exact_mismatches":[]}'
            source.write_text("print(" + repr(raw) + ")\n")
            result = subprocess.run([sys.executable, str(RUNNER), "--material-child", str(source), "--report", str(report)], capture_output=True, text=True, timeout=5)
            data = json.loads(report.read_text())
            require(result.returncode != 0 and data["passed"] is False and data["checks"] == [{"name": "builder_json", "passed": False}])
            return {"exit_code": result.returncode, "duplicate_builder_receipt_rejected": True}
        check("duplicate builder JSON cannot hide an exact reproduction mismatch", duplicate_builder)

        def existing():
            directory = root / "keep-output"; directory.mkdir(); (directory / "keep").write_text("preserve")
            result = subprocess.run([sys.executable, str(RUNNER), "--suite", "mikktspace", "--output", str(directory)], capture_output=True, text=True, timeout=5)
            require(result.returncode != 0 and "fresh directory" in result.stderr and (directory / "keep").read_text() == "preserve" and len(list(directory.iterdir())) == 1)
            return {"exit_code": result.returncode}
        check("existing output directory is refused without replacement", existing)
        def nonfinite_timeout():
            directory = root / "bad-timeout"
            result = subprocess.run([sys.executable, str(RUNNER), "--suite", "mikktspace", "--timeout", "nan", "--output", str(directory)], capture_output=True, text=True, timeout=5)
            require(result.returncode != 0 and not directory.exists())
            return {"exit_code": result.returncode}
        check("nonfinite timeout is refused before output creation", nonfinite_timeout)

        def ignored_material_fixture(name, *, ignored=False, engine_error=False, duplicate_receipt=False):
            # These tiny fake helpers/engines exercise the exact failure seen in
            # integration: exit zero from an editor is not proof of imported maps.
            # They never execute Godot or claim to import a material.
            directory = root / name; directory.mkdir()
            project = directory / "source"; project.mkdir()
            for relative in runner.CLOTH_FILES:
                path = project / relative; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture-source:" + relative)
            helper = project / "tools/stage-open-cloth.py"; helper.parent.mkdir()
            raw_receipt = ('{"passed":false,"passed":true,"source_unchanged":true,"engine_executed":false}' if duplicate_receipt else '{"passed":true,"source_unchanged":true,"engine_executed":false}')
            helper.write_text("import pathlib,sys,shutil,json\nsource=pathlib.Path(__file__).resolve().parents[1]\ndest=pathlib.Path(sys.argv[sys.argv.index('--project-output')+1]);dest.mkdir()\nfor name in " + repr(runner.CLOTH_FILES) + ":\n p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)\n(dest/'project.godot').write_text('config_version=5\\n')\n" + ("(dest/'art/.gdignore').write_text('')\n" if ignored else "") + "receipt=" + repr(raw_receipt) + "\n(dest/'open-cloth-stage-manifest.json').write_text(receipt)\nprint(receipt)\n")
            fake_engine = directory / "fake-engine"
            fake_engine.write_text("#!" + sys.executable + "\nimport sys\n" + ("print('SCRIPT ERROR: fixture-import-failed',file=sys.stderr)\n" if engine_error else ""))
            fake_engine.chmod(0o755)
            output = directory / "output"; output.mkdir(); (output / "logs").mkdir()
            previous = runner.PROJECT
            try:
                runner.PROJECT = project
                result = runner.prepare_cloth_fixture(output, sys.executable, str(fake_engine), os.environ.copy(), 5, True)
            finally:
                runner.PROJECT = previous
            require(not result["passed"])
            return result
        def import_false_success():
            result = ignored_material_fixture("fake-import-exit0")
            require(result["steps"][-1]["exit_code"] == 0)
            require(any(c["name"] == "all_three_maps_have_real_imported_payloads" and not c["passed"] for c in result["checks"]))
            return {"checks": result["checks"], "editor_native_exit": 0}
        check("editor exit zero without real texture payloads rejects material fixture", import_false_success)
        def ignored_ancestor():
            result = ignored_material_fixture("fake-ignored-art", ignored=True)
            require(len(result["steps"]) == 1 and any(c["name"] == "minimal_fixture_has_no_ancestor_art_ignore" and not c["passed"] for c in result["checks"]))
            return result["checks"]
        check("ancestor art ignore rejects staged fixture before engine execution", ignored_ancestor)
        def import_error():
            result = ignored_material_fixture("fake-import-error", engine_error=True)
            require(result["steps"][-1]["exit_code"] == 0 and result["steps"][-1]["logged_errors"] == ["SCRIPT ERROR: fixture-import-failed"])
            return {"error_logged": True, "editor_native_exit": 0}
        check("editor script error cannot hide behind native exit zero", import_error)
        def duplicate_stage():
            result = ignored_material_fixture("fake-duplicate-stage", duplicate_receipt=True)
            require(len(result["steps"]) == 1 and result["steps"][0]["receipt_passed"] is False)
            return {"stage_receipt_rejected_before_engine": True}
        check("duplicate stage JSON cannot hide a failed source receipt", duplicate_stage)

    report = {"schema": 1, "passed": all(c["passed"] for c in checks), "checks": checks, "count": len(checks),
              "sources": {"runner": runner.sha(RUNNER), "cases": runner.sha(Path(__file__))},
              "scope": "Real child-process/report boundary counterexamples; no game rendering or art acceptance."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    runner.write_json(args.report, report)
    print(json.dumps({"passed": report["passed"], "checks": len(checks), "failed": [c["name"] for c in checks if not c["passed"]], "report": str(args.report)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
