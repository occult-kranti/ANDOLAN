#!/usr/bin/env python3
"""Capture the Hanuman trial through the launcher and ordinary X11 input."""

import argparse
import ctypes
import importlib.util
import os
from pathlib import Path
import subprocess
import time


PROJECT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_ui", PROJECT / "tools/ui-campaign/run.py")
ui = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ui)

ABILITY_INPUTS = (
    ("vajra_gada", "mouse"),
    ("vajra_kavacha", "q"),
    ("maruti_udayana", "e"),
    ("lanka_dahan", "c"),
    ("mountain_pulse", "x"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--display", type=int, default=174)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    output = args.output.resolve()
    socket = Path(f"/tmp/.X11-unix/X{args.display}")
    if output.exists() or socket.exists() or not 90 <= args.display <= 199:
        parser.error("Use a fresh output directory and unused X11 display from 90 to 199.")
    output.mkdir(parents=True)
    display = f":{args.display}"
    env = dict(os.environ, DISPLAY=display, LP_NUM_THREADS="2", OMP_NUM_THREADS="2")
    env["LD_LIBRARY_PATH"] = str(args.runtime / "usr/lib/x86_64-linux-gnu")
    env["VK_ICD_FILENAMES"] = str(args.runtime / "usr/share/vulkan/icd.d/lvp_icd.json")
    command = [
        str(args.engine), "--path", str(PROJECT), "--display-driver", "x11", "--rendering-method", "forward_plus",
        "--audio-driver", "Dummy", "--resolution", "960x600", "--position", "0,0", "--max-fps", "30",
        "--disable-vsync", "--script", str(Path(__file__).with_name("observer.gd")), "--", "--mode=integrated",
        "--output=" + str(output),
    ]
    paths = [
        *PROJECT.glob("scripts/hanuman_*.gd"), *PROJECT.glob("assets/design/hanuman-*.json"),
        *PROJECT.glob("assets/heroes/hanuman/*.glb"), *PROJECT.glob("scenes/hanuman*.tscn"),
        PROJECT / "scripts/launch_shell.gd", PROJECT / "scripts/courtyard.gd",
        PROJECT / "scripts/scene_transition.gd", Path(__file__), Path(__file__).with_name("observer.gd"),
    ]
    receipt = {
        "complete": False, "command": command, "engine_sha256": ui.sha(args.engine),
        "source_sha256": {str(path.relative_to(PROJECT)): ui.sha(path) for path in paths},
        "inputs": [], "screens": {}, "started_unix": time.time(),
    }
    xserver = proc = handler = None

    def state():
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"Godot exited with {proc.returncode} before route finished")
        return ui.read(output / "state.json") or {}

    def wait(check):
        return ui.wait_for(lambda: (s if check(s) else None) if (s := state()) else None, args.timeout)

    def inject(step):
        before = state()
        handler.event(step)
        receipt["inputs"].append({"input": step, "frame": before.get("frame"), "unix": time.time()})
        ui.save(output / "receipt.json", receipt)

    def combat_click():
        before = state()
        handler.focus()
        # A captured pointer must never be repositioned with a UI click.
        for edge in (1, 0):
            handler.xt.XTestFakeButtonEvent(handler.d, 1, edge, 0)
            handler.x.XFlush(handler.d)
            time.sleep(0.15)
        receipt["inputs"].append({"input": {"button": 1, "captured": True}, "frame": before.get("frame")})

    def relative_motion(x, y):
        before = state()
        handler.xt.XTestFakeRelativeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
        handler.xt.XTestFakeRelativeMotionEvent(handler.d, x, y, 0)
        handler.x.XFlush(handler.d)
        receipt["inputs"].append({"relative_mouse": [x, y], "frame": before.get("frame")})
        wait(lambda s: s["frame"] > before["frame"])

    def click(name):
        seen = wait(lambda s: any(c["name"] == name and c["interactive"] for c in s.get("controls", [])))
        item = next(c for c in seen["controls"] if c["name"] == name and c["interactive"])
        x, y, width, height = item["input_rect"]
        inject({"point": [x + width / 2, y + height / 2]})

    def capture(name):
        ui.save(output / "capture-request.json", {"name": name})
        keep_screenshot(name)

    def keep_screenshot(name):
        shot = ui.wait_for(lambda: ui.read(output / f"{name}.json"), args.timeout)
        if shot.get("png_status") != 0 or ui.sha(output / shot["file"]) != shot["sha256"]:
            raise RuntimeError(f"Screenshot failed identity check: {name}")
        receipt["screens"][name] = {"file": shot["file"], "sha256": shot["sha256"], "frame": shot.get("frame")}

    try:
        with (output / "xvfb.log").open("x") as xlog, (output / "godot.log").open("x") as glog:
            xserver = subprocess.Popen(
                [str(args.runtime / "usr/bin/Xvfb"), display, "-screen", "0", "960x600x24", "-nolisten", "tcp", "-ac"],
                env=env, stdout=xlog, stderr=subprocess.STDOUT,
            )
            ui.wait_for(socket.exists, 10)
            proc = subprocess.Popen(command, env=env, stdout=glog, stderr=subprocess.STDOUT)
            handler = ui.NativeInput(display)
            handler.focus()
            wait(lambda s: s.get("panels", {}).get("main_panel"))
            capture("01-launch")
            click("HanumanTrialMode")
            wait(lambda s: s.get("launch", {}).get("selected_mode") == "hanuman")
            capture("01b-hanuman-selected")
            click("ExploreConfluence")
            wait(lambda s: s.get("trial_observed", False))
            if any(c["name"] == "BeginPractice" and c["interactive"] for c in state().get("controls", [])):
                capture("01c-trial-intro")
                click("BeginPractice")
            wait(lambda s: s.get("trial", {}).get("actor", {}).get("grounded") and not s.get("trial", {}).get("paused"))
            capture("02-hanuman-trial")
            inject({"key_down": "w", "immediate": True})
            try:
                wait(lambda s: s.get("actor_z", 9) < 7.1)
            finally:
                inject({"key_up": "w", "immediate": True})
            for ability, key in ABILITY_INPUTS:
                if ability == "maruti_udayana":
                    # Take an open angle around the central practice target.
                    relative_motion(-210, 0)
                if ability == "lanka_dahan" and state().get("actor_z", 2.8) < 2.8:
                    position = state()["actor_z"]
                    inject({"key_down": "s", "immediate": True})
                    try:
                        wait(lambda s: s.get("actor_z", position) > position + 1.1)
                    finally:
                        inject({"key_up": "s", "immediate": True})
                if ability == "mountain_pulse":
                    inject({"key": "F5"})
                    wait(lambda s: s.get("actor_z", 0) > 8.8 and s.get("trial", {}).get("actor", {}).get("grounded"))
                    # Aim the ordinary third-person reticle toward the target
                    # group. Positive XTest mouse Y pitches down in defaults.
                    relative_motion(0, 55)
                if key == "mouse":
                    combat_click()
                else:
                    inject({"key": key})
                keep_screenshot("ability-" + ability)
                wait(lambda s: s.get("trial", {}).get("combat", {}).get("phase") == "ready")
            inject({"key": "Escape"})
            capture("03-trial-paused")
            click("ReturnToTitle")
            wait(lambda s: s.get("panels", {}).get("main_panel"))
            capture("04-back-to-title")
            click("Quit")
            receipt["godot_exit"] = proc.wait(timeout=args.timeout)
            if receipt["godot_exit"] != 0:
                raise RuntimeError("Godot did not exit normally")
            trail = ui.read(output / "abilities.json")["events"]
            impacts = [row["event"] for row in trail if row["event"]["kind"] == "impact"]
            receipt["impacts"] = [{"id": event["ability_id"], "reason": event["reason"], "receipts": event["receipts"]} for event in impacts]
            if {event["ability_id"] for event in impacts} != {ability for ability, _ in ABILITY_INPUTS}:
                raise RuntimeError("The native input route missed an ability impact.")
            primary = next(event for event in impacts if event["ability_id"] == "vajra_gada")
            if not any(hit.get("damage_applied", 0) > 0 for hit in primary["receipts"]):
                raise RuntimeError("The ordinary frontal mace strike missed its training target.")
            receipt["complete"] = True
    except Exception as error:
        receipt["failure"] = str(error)
        raise
    finally:
        if handler is not None:
            handler.x.XCloseDisplay(handler.d)
        for process in (proc, xserver):
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        receipt["ended_unix"] = time.time()
        ui.save(output / "receipt.json", receipt)


if __name__ == "__main__":
    main()
