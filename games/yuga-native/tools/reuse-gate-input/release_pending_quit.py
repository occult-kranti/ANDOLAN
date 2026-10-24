#!/usr/bin/env python3
"""Record one ordinary key release after the R2 driver omitted its final edge.

This never calls engine quit or sends a process signal. It requires the exact
owned process/display, visible title Quit focus, and a held Return key.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import time

PROJECT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ui", PROJECT / "tools/ui-campaign/run.py")
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--engine-pid", type=int, required=True)
parser.add_argument("--wrapper-pid", type=int, required=True)
parser.add_argument("--display", type=int, required=True)
args = parser.parse_args()
out = args.output.resolve()
receipt = out / "quit-keyup-correction.json"
if receipt.exists():
    raise RuntimeError("Do not replay or overwrite an intervention")
run = ui.read(out / "run.json")
state = ui.read(out / "state.json")
proc = Path(f"/proc/{args.engine_pid}")
status = (proc / "status").read_text()
parent = int(next(line.split()[1] for line in status.splitlines() if line.startswith("PPid:")))
env = dict(item.split(b"=", 1) for item in (proc / "environ").read_bytes().split(b"\0") if b"=" in item)
if parent != args.wrapper_pid or env.get(b"DISPLAY") != f":{args.display}".encode():
    raise RuntimeError("Process ownership/display mismatch")
if str((proc / "exe").resolve()) != str(Path(run["command"][0]).resolve()):
    raise RuntimeError("Engine identity mismatch")
if state.get("scene_path") != "res://scenes/courtyard.tscn" or not state.get("panels", {}).get("main_panel") or state.get("focus_name") != "Quit" or not state.get("navigation_keys_pressed", {}).get("Return"):
    raise RuntimeError("This is not the observed pending title Quit release")
record = {"scope": "Supplementary ordinary XTest Return release; the R2 driver omitted its final key-up. Not engine quit, signal termination or an unassisted-run claim.",
          "before": state, "engine_pid": args.engine_pid, "wrapper_pid": args.wrapper_pid,
          "display": args.display, "source_sha256": ui.sha(Path(__file__)),
          "reused_driver_sha256": ui.sha(PROJECT / "tools/ui-campaign/run.py"),
          "started_unix": time.time(), "event": {"key_up": "Return"}, "sent": False}
ui.save(receipt, record)
native = ui.NativeInput(f":{args.display}")
try:
    record["window_id"] = native.event({"key_up": "Return", "immediate": True})
    record["sent"] = True
    record["sent_unix"] = time.time()
finally:
    native.x.XCloseDisplay(native.d)
    ui.save(receipt, record)
print(json.dumps({"sent": record["sent"], "receipt": str(receipt)}))
