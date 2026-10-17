#!/usr/bin/env python3
"""Inspect one accessible ELF component with the pinned REA/Ghidra toolchain.

This runs analysis tools only. It does not execute the input component, recover
an absent server, or establish the behavior of an entire game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def write_json(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def run_bounded(command: list[str], env: dict, timeout: float) -> tuple[int, bytes, bytes]:
    """Own a process group so timeout also stops ordinary provider descendants."""
    process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                pass
            if sig == signal.SIGTERM:
                time.sleep(0.1)
        stdout, stderr = process.communicate(timeout=5)
        return 124, stdout, stderr


def inspect(args: argparse.Namespace) -> int:
    binary, root, rea, output = (p.resolve() for p in
        (args.binary, args.tool_root, args.rea, args.output))
    if not binary.is_file():
        raise ValueError("An accessible ELF input is required")
    with binary.open("rb") as stream:
        magic = stream.read(4)
    if magic != b"\x7fELF":
        raise ValueError("An accessible ELF input is required")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", args.symbol):
        raise ValueError("Select one C identifier, not a command or address expression")
    if output.exists():
        raise ValueError("Use a fresh output directory to preserve prior evidence")
    if not rea.is_file():
        raise ValueError("The pinned REA CLI is not installed at --rea")
    ghidra = root / "ghidra_12.1.4_PUBLIC"
    java = root / "jdk-21.0.12.1+1"
    python = root / "python/bin/python"
    if not (ghidra.is_dir() and (java / "bin/java").is_file() and python.is_file()):
        raise ValueError("Restore the documented pinned Ghidra/JDK/provider environment first")
    output.mkdir(parents=True)
    source_hash = digest(binary)
    env = {**os.environ, "GHIDRA_INSTALL_DIR": str(ghidra),
        "JAVA_HOME": str(java), "GHIDRA_HEADLESS_MAXMEM": "768M",
        "REA_PWNTOOLS_PYTHON": str(python)}
    base = ["node", str(rea)]
    commands = [
        ("binary-layout", base + ["inspect-binary-layout", str(binary), "--format", "json"]),
        ("decompile", base + ["decompile", str(binary), args.symbol,
            "--provider", "ghidra", "--format", "json"]),
        ("function", base + ["function", str(binary), args.symbol,
            "--provider", "ghidra", "--format", "json"]),
    ]
    steps, results, errors = [], {}, []
    for name, command in commands:
        started = time.monotonic()
        code, stdout, stderr = run_bounded(command, env, args.timeout)
        (output / (name + ".stdout")).write_bytes(stdout)
        (output / (name + ".stderr")).write_bytes(stderr)
        step = {"name": name, "command": command, "exit_code": code,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest()}
        steps.append(step)
        write_json(output / "steps.json", steps)
        print(json.dumps({k: step[k] for k in ("name", "exit_code", "duration_seconds")}), flush=True)
        if code:
            errors.append(name + " returned " + str(code))
            break
        try:
            result = json.loads(stdout)
            if result["subject"]["digest"]["sha256"] != source_hash:
                raise ValueError("provider returned a different input identity")
            results[name] = result
        except (ValueError, KeyError, TypeError) as error:
            errors.append(name + ": invalid provider evidence: " + str(error))
            break
    checks = {"all_three_commands_succeeded": len(results) == 3,
        "input_unchanged": digest(binary) == source_hash}
    observations = {}
    if len(results) == 3:
        try:
            layout = results["binary-layout"]["normalized_result"]
            decompiled = results["decompile"]["normalized_result"]
            function = results["function"]["normalized_result"]
            provider = {"id": "ghidra", "name": "Ghidra", "version": "12.1.4"}
            checks.update({
                "elf_layout": layout["format"] == "elf",
                "pinned_decompiler": results["decompile"]["provider"] == provider,
                "pinned_function_provider": results["function"]["provider"] == provider,
                "selected_function": function["procedure"]["name"] == args.symbol,
                "nonempty_pseudocode": isinstance(decompiled, str) and bool(decompiled.strip()),
                "symbol_present_in_pseudocode": isinstance(decompiled, str)
                    and bool(re.search(r"\b" + re.escape(args.symbol) + r"\s*\(", decompiled)),
                "basic_blocks_returned": isinstance(function["basic_blocks"], list)
                    and len(function["basic_blocks"]) > 0,
            })
            observations = {"architecture": layout.get("architecture"),
                "procedure": function["procedure"],
                "basic_blocks": len(function["basic_blocks"]),
                "callers": function.get("callers"), "callees": function.get("callees"),
                "unresolved_calls": function.get("unresolved_calls"),
                "provider_scope": "Returned static relationships only; indirect calls and runtime reachability may remain unknown."}
        except (KeyError, TypeError) as error:
            errors.append("Incomplete normalized provider result: " + str(error))
    passed = not errors and all(checks.values())
    record = {"schema": 1, "passed": passed, "binary": str(binary),
        "binary_sha256": source_hash, "binary_bytes": binary.stat().st_size,
        "symbol": args.symbol, "target_executed": False,
        "runner_sha256": digest(Path(__file__)), "checks": checks,
        "steps": steps, "observations": observations, "errors": errors,
        "scope": "One selected function in this exact accessible component. Pseudocode is reconstructed analysis, not original source or complete game recovery. Behavioral acceptance requires independent execution/source comparisons."}
    write_json(output / "acceptance.json", record)
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("binary", "tool-root", "rea", "output"):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("--timeout must be between 1 and 300 seconds per analysis command")
    try:
        return inspect(args)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
