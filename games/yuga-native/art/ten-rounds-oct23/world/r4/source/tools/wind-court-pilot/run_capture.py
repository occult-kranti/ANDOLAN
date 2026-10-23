#!/usr/bin/env python3
"""Run the bounded, actual Vulkan court comparison on an owned Xvfb display.

Uses a previously verified runtime directory; downloads nothing. Owns and cleans
up only the two processes it starts. It does not measure GPU performance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--godot", default=Path("/usr/local/bin/godot"), type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--display", type=int, default=121)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output.exists() or not 90 <= args.display <= 199:
        raise ValueError("Fresh output and owned display 90..199 required")
    if Path(f"/tmp/.X11-unix/X{args.display}").exists() or Path(f"/tmp/.X{args.display}-lock").exists():
        raise ValueError("Display already in use")
    output.parent.mkdir(parents=True, exist_ok=True)
    runtime = args.runtime.resolve()
    env = os.environ.copy()
    env.update(DISPLAY=f":{args.display}", LD_LIBRARY_PATH=str(runtime / "usr/lib/x86_64-linux-gnu") + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else ""), VK_ICD_FILENAMES=str(runtime / "usr/share/vulkan/icd.d/lvp_icd.json"), LP_NUM_THREADS="2")
    command = [str(args.godot), "--path", str(project), "--rendering-method", "forward_plus", "--rendering-driver", "vulkan", "--audio-driver", "Dummy", "--fixed-fps", "30", "--disable-vsync", "--script", "tools/wind-court-pilot/capture_pilot.gd", "--", "--output=" + str(output)]
    pinned = [project / p for p in ("project.godot", "scenes/confluence_world.tscn", "scripts/confluence_world.gd", "scripts/traversal_landmarks.gd", "scripts/traversal_stone.gdshader", "scripts/world_render_resources.gd", "assets/world/confluence-map.json", "tools/wind-court-pilot/capture_pilot.gd")]
    receipt = {"command": command, "started_unix": time.time(), "display": args.display, "godot_sha256": sha(args.godot.resolve()), "runtime_setup_sha256": sha(runtime.parent / "setup-report.json"), "input_sha256": {str(path.relative_to(project)): sha(path) for path in pinned}, "scope": "Actual staged full-world art comparison; software Vulkan, no hardware FPS or ordinary input qualification."}
    log_path = output.with_suffix(".log")
    xlog_path = output.with_suffix(".xvfb.log")
    receipt_path = output.with_suffix(".wrapper.json")
    with log_path.open("x") as log, xlog_path.open("x") as xlog:
        xvfb = subprocess.Popen([str(runtime / "usr/bin/Xvfb"), env["DISPLAY"], "-screen", "0", "960x540x24", "-nolisten", "tcp"], env=env, stdout=xlog, stderr=subprocess.STDOUT)
        receipt["xvfb_pid"] = xvfb.pid
        try:
            deadline = time.monotonic() + 10
            while not Path(f"/tmp/.X11-unix/X{args.display}").exists():
                if xvfb.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Owned Xvfb failed to become ready")
                time.sleep(.05)
            engine = subprocess.Popen(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT)
            receipt["engine_pid"] = engine.pid
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
            print(json.dumps({"engine_pid": engine.pid, "xvfb_pid": xvfb.pid, "receipt": str(receipt_path)}), flush=True)
            try:
                receipt["exit_code"] = engine.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                engine.terminate()
                try:
                    engine.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    engine.kill(); engine.wait(timeout=10)
                receipt["exit_code"] = engine.returncode
                raise RuntimeError("Capture exceeded bounded deadline")
            if receipt["exit_code"] != 0:
                raise RuntimeError(f"Godot failed with exit {receipt['exit_code']}; see {log_path}")
            log.flush()
            raw_log = log_path.read_text()
            if "SCRIPT ERROR:" in raw_log or "\nERROR:" in raw_log:
                raise ValueError("Native runtime reported errors; inspect preserved log")
            report = json.loads((output / "capture.json").read_text())
            if not report.get("complete") or len(report["shots"]) != 16 or report["renderer"] != "forward_plus" or report["display"] == "headless":
                raise ValueError("Capture report does not establish actual matched completion")
            for shot in report["shots"]:
                path = output / shot["file"]
                header = path.read_bytes()[:24]
                if header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", header[16:24]) != (960, 540) or sha(path) != shot["sha256"]:
                    raise ValueError("Actual image dimensions/hash mismatch: " + shot["file"])
                if not all(shot[k] > 0 for k in ("objects", "primitives", "draw_calls")) or not shot["state_unchanged"]:
                    raise ValueError("Actual renderer/state evidence failed: " + shot["file"])
            receipt["passed"] = True
            receipt["capture_sha256"] = sha(output / "capture.json")
        except Exception as error:
            receipt["passed"] = False
            receipt["failure"] = str(error)
        finally:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=10)
            except subprocess.TimeoutExpired:
                xvfb.kill(); xvfb.wait(timeout=10)
            receipt["finished_unix"] = time.time()
            receipt["input_after_sha256"] = {str(path.relative_to(project)): sha(path) for path in pinned}
            receipt["inputs_unchanged"] = receipt["input_after_sha256"] == receipt["input_sha256"]
            if not receipt["inputs_unchanged"]:
                receipt["passed"] = False
                receipt["failure"] = "Pinned source inputs changed during capture"
            receipt["partial_image_files"] = [{"file": path.name, "sha256": sha(path), "bytes": path.stat().st_size} for path in sorted(output.glob("*.png"))] if output.exists() else []
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": receipt["passed"], "receipt": str(receipt_path), "failure": receipt.get("failure")}), flush=True)
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
