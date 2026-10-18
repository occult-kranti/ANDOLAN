#!/usr/bin/env python3
"""Read-only I3 preference receipts; pixel review is recorded separately."""
import argparse
import hashlib
import json
import math
import pathlib
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=pathlib.Path, required=True)
    parser.add_argument("--relaunch", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    args = parser.parse_args()
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), "details": details})

    def load(folder, name):
        return json.loads((folder / name).read_text())

    first, second = [load(folder, "run.json") for folder in [args.first, args.relaunch]]
    for label, folder, run in [("first", args.first, first), ("relaunch", args.relaunch, second)]:
        check(label + " completed package process exits via native Quit", run.get("mode") == "package" and run.get("complete") and run.get("verified_exit_code") == 0 and run.get("cleanup_exit") == 0)
        check(label + " exact package and external observer stayed unchanged", all(run.get(key) is True for key in ["package_unchanged", "instrumentation_unchanged", "archive_unchanged", "export_manifest_unchanged", "source_unchanged"]))
        command = run.get("command", [])
        check(label + " executes exported ELF with explicit PCK", "--main-pack" in command and "--path" not in command and len(run.get("package_sha256", {})) == 2 and run.get("engine_sha256") in run.get("package_sha256", {}).values())
        log = (folder / "godot.log").read_text()
        check(label + " engine log contains no runtime errors or leaks", not any(term in log for term in ["SCRIPT ERROR", "\nERROR:", "ObjectDB instances leaked", "resources still in use"]))
    check("separate package processes reuse identical payloads", first.get("package_sha256") == second.get("package_sha256") and first.get("package_archive") == second.get("package_archive") and first.get("finished_unix", 1e30) <= second.get("started_unix", -1))
    check("relaunch uses identical isolated XDG and saved bytes", first["user_state"]["path"] == second["user_state"]["path"] and not first["user_state"]["before"] and len(first["user_state"]["after"]) == 1 and first["user_state"]["after"] == second["user_state"]["before"] == second["user_state"]["after"])

    stems = {
        "P01-native-settings-edited": args.first,
        "P02-native-piercing-dawn-remap": args.first,
        "P03-native-guide-preferences-saved": args.first,
        "P04-world-guide-loaded-preferences": args.first,
        "P05-world-muted-sound-and-return": args.first,
        "P06-returned-title-settings": args.first,
        "R01-relaunched-settings": args.relaunch,
        "R02-relaunched-remapped-control": args.relaunch,
        "R03-relaunched-guide-preferences": args.relaunch,
    }
    shots = {}
    originals = []
    for stem, folder in stems.items():
        shot = load(folder, stem + ".json")
        image = folder / shot["file"]
        content = image.read_bytes()
        dimensions = struct.unpack(">II", content[16:24])
        check(stem + " original matches receipt", content[:8] == b"\x89PNG\r\n\x1a\n" and sha(image) == shot["sha256"] and shot["png_status"] == 0)
        shots[stem] = shot
        originals.append({"path": str(image), "sha256": sha(image), "framebuffer_pixels": dimensions, "native_window_pixels": shot["size"], "frame": shot["frame"], "focus": shot["focus"]})
    for stem in ["P01-native-settings-edited", "P06-returned-title-settings", "R01-relaunched-settings"]:
        shot = shots[stem]
        state, saved = shot["state"], shot["preferences"]
        check(stem + " shows actual saved aim sound and display settings", math.isclose(state["sensitivity"], 2.5, abs_tol=1e-6) and state["volume"] == 0 and state["invert_y"] is True and state["shadows"] is False and saved["controls"]["sensitivity"] == 2.5 and saved["controls"]["invert_y"] is True and saved["audio"]["volume"] == 0 and saved["video"]["shadows"] is False)
    for stem in ["P02-native-piercing-dawn-remap", "R02-relaunched-remapped-control"]:
        shot = shots[stem]
        check(stem + " actual focused remap agrees with saved physical key", shot["focus_text"] == "J" and shot["focus"].endswith("/Binding_pulse") and shot["state"]["capture_action"] == "" and shot["preferences"]["controls"]["bindings"]["pulse"] == 74)
    for stem in ["P03-native-guide-preferences-saved", "P04-world-guide-loaded-preferences", "R03-relaunched-guide-preferences"]:
        shot = shots[stem]
        guide, effects, saved = shot["guide"], shot["effect_options"], shot["preferences"]
        check(stem + " live guide and effect receiver agree with saved pair", guide["key_text"] == "J  /  ABILITY" and guide["effects_enabled"] and guide["receiver_present"] and all(guide[key] is True and effects[key] is True and saved["rama_effects"][key] is True for key in ["reduced_effects", "reduced_motion"]))
    saved_guide = shots["P03-native-guide-preferences-saved"]["guide"]
    check("new save confirmation is fully visible", saved_guide["notice_fully_visible"] and saved_guide["notice"].startswith("Ability effect preferences saved"))
    world = shots["P05-world-muted-sound-and-return"]
    audio = world["audio_state"]
    check("world mute reaches all four actual audio receivers", audio["audio_volume"] == 0 and audio["siege_effects"]["volume"] == 0 and audio["invocation_audio"]["volume"] == 0 and audio["action_audio"]["volume"] == 0)
    check("world aim receiver loads persisted scale and inversion", math.isclose(world["presentation"]["player_sensitivity"], .006, abs_tol=1e-6) and world["presentation"]["player_invert_y"] is True)
    events = first.get("events", []) + second.get("events", [])
    check("native events identify the owned window and actual remap key", bool(events) and all(event.get("window_id", 0) for event in events) and any(event.get("key") == "j" for event in events))
    result = {"passed": all(row["passed"] for row in checks), "checks": checks, "originals": originals, "runs": {str(folder / "run.json"): sha(folder / "run.json") for folder in [args.first, args.relaunch]}, "validator_sha256": sha(pathlib.Path(__file__)), "scope": "Read-only semantic receipt validation of two exact package processes. Hash/state checks do not replace direct original pixel review. No sound listening, global Master mute, hardware FPS or other-platform claim."}
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "report": str(args.report)}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
