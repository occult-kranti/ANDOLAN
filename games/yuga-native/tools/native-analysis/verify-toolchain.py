#!/usr/bin/env python3
"""Compile an original fixture and retain actual REA provider outputs.

Only the authored fixture is executed. REA statically reads that exact ELF;
this is a toolchain acceptance check, not analysis of a commercial game.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_outputs(output):
    """Check returned facts, not only process success. No claim of full recovery."""
    binary_hash = sha256(output / "combat-fixture")
    results = {name: json.loads((output / (name + ".stdout")).read_text())
               for name in ("binary-layout", "decompile", "function")}
    layout = results["binary-layout"]["normalized_result"]
    decompiled = results["decompile"]["normalized_result"]
    function = results["function"]["normalized_result"]
    checks = {
        "same_binary_digest_in_all_provider_results": all(
            result["subject"]["digest"]["sha256"] == binary_hash for result in results.values()),
        "layout_is_x86_64_elf": layout["format"] == "elf" and layout["architecture"]["machine"] == "EM_X86_64",
        "ghidra_12_1_4_decompiler": results["decompile"]["provider"] == {"id": "ghidra", "name": "Ghidra", "version": "12.1.4"},
        "selected_function_recovered": function["procedure"]["name"] == "combat_damage",
        "pseudocode_calls_clamp": isinstance(decompiled, str) and "clamp_armour(armour)" in decompiled,
        "main_is_recovered_caller": any(item["name"] == "main" for item in function["callers"]),
        "clamp_is_recovered_callee": any(item["name"] == "clamp_armour" for item in function["callees"]),
        "finite_branches_recovered": len(function["basic_blocks"]) >= 3,
        "no_unresolved_calls_in_selected_function": function["unresolved_calls"] == [],
        "five_authored_runtime_cases_pass": (output / "fixture-tests.stdout").read_text().strip() == "original-fixture: 5 cases passed",
    }
    report = {"checks": checks, "passed": all(checks.values()),
              "scope": "one unoptimized original fixture with debug symbols; no commercial game coverage"}
    (output / "acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-root", type=Path, required=True)
    parser.add_argument("--rea", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.tool_root.resolve(), args.output.resolve()
    if output.exists():
        raise SystemExit("Use a new output directory to preserve earlier attempts")
    output.mkdir(parents=True)
    fixture = Path(__file__).with_name("combat-fixture.c").resolve()
    binary = output / "combat-fixture"
    env = {**os.environ,
           "GHIDRA_INSTALL_DIR": str(root / "ghidra_12.1.4_PUBLIC"),
           "JAVA_HOME": str(root / "jdk-21.0.12.1+1"),
           "GHIDRA_HEADLESS_MAXMEM": "768M",
           "REA_PWNTOOLS_PYTHON": str(root / "python/bin/python")}
    base = ["node", str(args.rea.resolve())]
    steps = [
        ("compile", ["cc", "-std=c11", "-O0", "-g", "-fno-inline", "-Wall", "-Wextra", "-Werror", str(fixture), "-o", str(binary)]),
        ("fixture-tests", [str(binary)]),
        ("binary-layout", base + ["inspect-binary-layout", str(binary), "--format", "json"]),
        ("decompile", base + ["decompile", str(binary), "combat_damage", "--provider", "ghidra", "--format", "json"]),
        ("function", base + ["function", str(binary), "combat_damage", "--provider", "ghidra", "--format", "json"]),
    ]
    records = []
    for name, command in steps:
        started = time.monotonic()
        try:
            result = subprocess.run(command, env=env, capture_output=True, timeout=180, check=False)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as failure:
            code, stdout, stderr = 124, failure.stdout or b"", failure.stderr or b""
        (output / (name + ".stdout")).write_bytes(stdout)
        (output / (name + ".stderr")).write_bytes(stderr)
        record = {"name": name, "command": command, "exit_code": code,
                  "duration_seconds": round(time.monotonic() - started, 3),
                  "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                  "stderr_sha256": hashlib.sha256(stderr).hexdigest()}
        records.append(record)
        (output / "steps.json").write_text(json.dumps(records, indent=2) + "\n")
        print(json.dumps({key: record[key] for key in ("name", "exit_code", "duration_seconds")}), flush=True)
        if code != 0 and name in ("compile", "fixture-tests"):
            break
    manifest = {"fixture_source_sha256": sha256(fixture),
                "binary_sha256": sha256(binary) if binary.exists() else None,
                "binary_bytes": binary.stat().st_size if binary.exists() else 0,
                "steps": records,
                "scope": "original authored fixture only; no commercial game inputs",
                "all_commands_exit_zero": len(records) == len(steps) and all(r["exit_code"] == 0 for r in records)}
    if manifest["all_commands_exit_zero"]:
        manifest["acceptance"] = validate_outputs(output)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    raise SystemExit(0 if manifest["all_commands_exit_zero"] and manifest.get("acceptance", {}).get("passed") else 1)


if __name__ == "__main__":
    main()
