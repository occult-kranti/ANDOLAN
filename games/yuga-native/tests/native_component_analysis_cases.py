#!/usr/bin/env python3
"""Linux input-preservation and provider-process timeout counterexamples."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tools/native-analysis/inspect-component.py"
spec = importlib.util.spec_from_file_location("native_component_analysis", RUNNER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def running(pid: int) -> bool:
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()[0]
        return state not in ("Z", "X")
    except FileNotFoundError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        parser.error("These native-toolchain process tests require Linux /proc")
    checks = []
    def check(name: str, value: bool, **evidence) -> None:
        checks.append({"name": name, "passed": bool(value), **evidence})
    with tempfile.TemporaryDirectory(prefix="yuga-component-analysis-") as tmp:
        work = Path(tmp)
        plain = work / "not-elf.txt"
        plain.write_text("not an ELF component\n")
        existing = work / "existing"
        existing.mkdir()
        (existing / "keep.txt").write_text("preserve\n")
        base = [sys.executable, str(RUNNER), "--binary", "/bin/true", "--symbol", "example",
            "--rea", str(work / "missing-rea.mjs"), "--tool-root", str(work / "missing-tools"),
            "--output", str(work / "new-output")]
        for name, changes, reason in [
            ("non_ELF_input", {"--binary": str(plain)}, "An accessible ELF input is required"),
            ("invalid_symbol", {"--symbol": "invalid/symbol"}, "Select one C identifier"),
            ("preserve_existing_output", {"--output": str(existing)}, "Use a fresh output directory"),
            ("missing_REA", {}, "The pinned REA CLI is not installed"),
        ]:
            command = base.copy()
            for flag, value in changes.items():
                command[command.index(flag) + 1] = value
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            check(name, result.returncode != 0 and reason in result.stderr
                and not (work / "new-output").exists()
                and (existing / "keep.txt").read_text() == "preserve\n",
                exit_code=result.returncode, diagnostic=result.stderr.strip())
    code, out, err = module.run_bounded([sys.executable, "-c", "print('provider-ok')"], os.environ.copy(), 5)
    check("normal_provider_output", code == 0 and out == b"provider-ok\n" and not err)
    code, out, err = module.run_bounded([sys.executable, "-c",
        "import sys; print('rejected'); print('provider-error', file=sys.stderr); sys.exit(7)"], os.environ.copy(), 5)
    check("preserve_provider_failure", code == 7 and out == b"rejected\n" and err == b"provider-error\n")
    child = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('child-ready',flush=True); time.sleep(60)"
    parent = ("import os,signal,subprocess,sys,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        "p=subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); "
        "print('pids=%d,%d'%(os.getpid(),p.pid),flush=True); time.sleep(60)")
    started = time.monotonic()
    code, out, err = module.run_bounded([sys.executable, "-c", parent], os.environ.copy(), 1)
    elapsed = time.monotonic() - started
    match = re.search(rb"pids=(\d+),(\d+)", out)
    pids = [int(v) for v in match.groups()] if match else []
    deadline = time.monotonic() + 1
    while pids and any(running(pid) for pid in pids) and time.monotonic() < deadline:
        time.sleep(0.01)
    check("timeout_stops_TERM_ignoring_parent_and_child", code == 124 and len(pids) == 2
        and b"child-ready" in out and not any(running(pid) for pid in pids) and elapsed < 5,
        exit_code=code, pids=pids, elapsed_seconds=round(elapsed, 3), retained_stdout=out.decode())
    report = {"passed": all(c["passed"] for c in checks), "checks": checks,
        "runner_sha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Linux CLI preservation and owned process-group timeout checks. No REA/Ghidra provider, game target or decompilation-equivalence acceptance."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": len(checks), "report": str(args.report)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
