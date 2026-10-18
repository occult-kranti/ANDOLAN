#!/usr/bin/env python3
"""Native XTest states over two backgrounds in an isolated 2D Godot fixture."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[1]
RUNTIME = Path("/workspace/tooling/native-render/runtime")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--display", type=int, required=True)
    args = parser.parse_args()
    out = args.output
    if not out.is_absolute() or out.exists():
        parser.error("Use a fresh absolute output")
    if not 90 <= args.display <= 199 or Path(f"/tmp/.X11-unix/X{args.display}").exists():
        parser.error("Use an unused X display90–199")
    out.mkdir(parents=True)
    fixture = out / "fixture"
    files = ["scripts/hero_ui_theme.gd", "tests/ui_independent_theme_board.gd", "tests/ui_independent_theme_capture.py", "tools/ui-campaign/run.py"]
    files += [str(p.relative_to(PROJECT)) for p in (PROJECT / "assets/fonts").glob("*") if p.is_file()]
    files += [str(p.relative_to(PROJECT)) for p in (PROJECT / ".godot/imported").glob("*.ttf-*") if p.is_file()]
    pins = {}
    for name in files:
        target = fixture / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / name, target)
        pins[name] = sha(target)
    (fixture / "project.godot").write_text('[application]\nconfig/name="YUGA theme fixture"\n[display]\nwindow/size/viewport_width=1280\nwindow/size/viewport_height=720\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    spec = importlib.util.spec_from_file_location("frozen_native_input", fixture / "tools/ui-campaign/run.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    env = os.environ.copy()
    env.update(DISPLAY=f":{args.display}", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", LP_NUM_THREADS="1", LD_LIBRARY_PATH=str(RUNTIME / "usr/lib/x86_64-linux-gnu"))
    for key, folder in [("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")]:
        path = out / "user" / folder
        path.mkdir(parents=True)
        env[key] = str(path)
    command = [shutil.which("godot"), "--path", str(fixture), "--display-driver", "x11", "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy", "--resolution", "1280x720", "--position", "0,0", "--max-fps", "20", "--max-threads", "1", "--script", "res://tests/ui_independent_theme_board.gd", "--", "--output=" + str(out)]
    receipt = {"complete": False, "scope": "Isolated production theme on native 2D controls over bright/dark backgrounds. Actual XTest move/press/release/key events; zero3D scenes or GLBs.", "command": command, "source_pins": pins, "engine_sha256": sha(Path(command[0])), "events": [], "shots": [], "checks": []}
    game = server = native = None
    try:
        with (out / "xvfb.log").open("w") as xl, (out / "godot.log").open("w") as gl:
            server = subprocess.Popen([str(RUNTIME / "usr/bin/Xvfb"), env["DISPLAY"], "-screen", "0", "1280x720x24", "-nolisten", "tcp", "-extension", "MIT-SHM", "-ac"], env=env, stdout=xl, stderr=subprocess.STDOUT)
            helper.wait_for(lambda: Path(f"/tmp/.X11-unix/X{args.display}").exists(), 10)
            game = subprocess.Popen(command, env=env, stdout=gl, stderr=subprocess.STDOUT)
            native = helper.NativeInput(env["DISPLAY"])
            native.focus()
            state = lambda: helper.read(out / "state.json")
            helper.wait_for(lambda: state().get("controls"), 30)

            def event(kind, target=None, key=None):
                native.focus()
                if key:
                    native.event({"key": key})
                else:
                    x, y, w, h = state()["controls"][target]["rect"]
                    native.xt.XTestFakeMotionEvent(native.d, -1, round(x+w/2), round(y+h/2), 0)
                    native.x.XFlush(native.d)
                    if kind in ["down", "up", "click"]:
                        for down in ([1, 0] if kind == "click" else [int(kind == "down")]):
                            native.xt.XTestFakeButtonEvent(native.d, 1, down, 0)
                            native.x.XFlush(native.d)
                            time.sleep(.1)
                receipt["events"].append({"kind": kind, "target": target, "key": key, "time_unix": time.time()})
                time.sleep(.25)

            def capture(name):
                helper.save(out / "capture-request.json", {"name": name})
                shot = helper.wait_for(lambda: helper.read(out / (name + ".json")), 20)
                assert shot["png_status"] == 0 and sha(out / shot["file"]) == shot["sha256"]
                receipt["shots"].append(shot)
                return shot

            def check(name, passed, details=None):
                receipt["checks"].append({"name": name, "passed": passed, "details": details or {}})

            capture("01-normal-focus-disabled")
            event("move", "LightSecondary")
            shot = capture("02-secondary-hover")
            check("Actual mouse hover reaches native HOVER", shot["controls"]["LightSecondary"]["draw_mode"] == 2)
            event("down", "LightSecondary")
            shot = capture("03-secondary-held")
            check("Held pointer reaches native HOVER_PRESSED", shot["controls"]["LightSecondary"]["draw_mode"] == 4)
            event("up", "LightSecondary")
            event("down", "DarkSelected")
            shot = capture("04-selected-held-dark")
            check("Selected style retains native pressed state", shot["controls"]["DarkSelected"]["draw_mode"] == 4)
            event("up", "DarkSelected")
            for side in ["Light", "Dark"]:
                event("click", side + "Option")
                shot = capture("05-option-ltr-open" if side == "Light" else "06-option-rtl-open")
                check(side + " option opens in native HOVER_PRESSED", shot["controls"][side+"Option"]["draw_mode"] == 4 and shot["controls"][side+"Option"]["popup"])
                event("key", key="Escape")
            event("click", "LightPrimaryDisabled")
            shot = capture("07-disabled-click")
            check("Actual disabled click cannot emit primary action", shot["activations"]["LightPrimaryDisabled"] == 0 and shot["controls"]["LightPrimaryDisabled"]["draw_mode"] == 3)
            event("click", "DarkToggle")
            shot = capture("08-toggle-on")
            check("Actual toggle click changes checked state", shot["controls"]["DarkToggle"]["pressed"])
            event("click", "LightSlider")
            before = state()["controls"]["LightSlider"]["value"]
            event("key", key="Right")
            shot = capture("09-slider-keyboard-focus")
            check("Native focused slider responds to keyboard", shot["focus"] == "LightSlider" and shot["controls"]["LightSlider"]["value"] > before)
            event("down", "DarkScroll")
            capture("10-scroll-held")
            event("up", "DarkScroll")
            receipt["source_unchanged"] = all(sha(fixture / name) == digest for name, digest in pins.items())
            receipt["complete"] = receipt["source_unchanged"] and all(row["passed"] for row in receipt["checks"])
    except Exception as exc:
        receipt["failure"] = repr(exc)
        raise
    finally:
        if game and game.poll() is None:
            game.terminate()
            try:
                game.wait(timeout=5)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait()
        if native:
            native.x.XCloseDisplay(native.d)
        if server:
            server.terminate()
            server.wait(timeout=5)
        logs = {name: sha(out / name) for name in ["godot.log", "xvfb.log"] if (out / name).exists()}
        receipt["logs"] = logs
        receipt["engine_errors"] = sum("ERROR:" in line for line in (out / "godot.log").read_text().splitlines()) if (out / "godot.log").exists() else 1
        receipt["complete"] = receipt["complete"] and receipt["engine_errors"] == 0
        helper.save(out / "run.json", receipt)
    print(json.dumps({"complete": receipt["complete"], "checks": len(receipt["checks"]), "shots": len(receipt["shots"]), "output": str(out)}))
    raise SystemExit(0 if receipt["complete"] else 1)


if __name__ == "__main__":
    main()
