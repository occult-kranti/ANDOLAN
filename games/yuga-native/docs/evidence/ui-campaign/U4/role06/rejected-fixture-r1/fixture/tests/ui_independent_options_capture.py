#!/usr/bin/env python3
"""Independently capture real guide effect preferences with native XTest input."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

PROJECT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--display", required=True, type=int)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    args = parser.parse_args()
    if not args.output.is_absolute() or args.output.exists():
        parser.error("Use a fresh absolute output directory")
    args.output.mkdir(parents=True)
    fixture = args.output / "fixture"
    for directory in ["scripts", "scenes", "shaders", "assets", "NOTICE", "tools/ui-campaign", "tests"]:
        (fixture / directory).mkdir(parents=True, exist_ok=True)
    files = [
        "scripts/rama_hero_panel.gd", "scripts/input_bindings.gd",
        "scripts/hero_ui_theme.gd", "scripts/launch_shell.gd", "scripts/scene_transition.gd",
        "assets/design/rama-ability-kit.json", "tests/ui_campaign_flow_cases.gd",
        "tests/ui_independent_options_board.gd", "tests/ui_independent_options_capture.py",
        "tests/ui_independent_options_observer.gd", "scripts/rama_ability_effects.gd",
        "shaders/rama_ribbon.gdshader", "shaders/rama_ability_calligraphy.gdshader",
        "shaders/rama_ability_boundary.gdshader",
        "tools/ui-campaign/observer.gd", "tools/ui-campaign/board.gd", "tools/ui-campaign/run.py",
    ]
    files += [str(p.relative_to(PROJECT)) for p in (PROJECT / "assets/fonts").glob("*") if p.is_file()]
    files += [str(p.relative_to(PROJECT)) for p in (PROJECT / ".godot/imported").glob("*.ttf-*") if p.is_file()]
    pins = {}
    for file in files:
        target = fixture / file
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / file, target)
        pins[file] = sha(target)
    shutil.copy2(fixture / "tools/ui-campaign/observer.gd", fixture / "tests/ui_independent_base_observer.gd")
    shutil.copy2(fixture / "tests/ui_independent_options_observer.gd", fixture / "tools/ui-campaign/observer.gd")
    pins["tests/ui_independent_base_observer.gd"] = sha(fixture / "tests/ui_independent_base_observer.gd")
    pins["tools/ui-campaign/observer.gd"] = sha(fixture / "tools/ui-campaign/observer.gd")
    (fixture / "project.godot").write_text(
        '[application]\nconfig/name="YUGA independent 2D guide fixture"\n'
        'run/main_scene="res://scenes/guide.tscn"\n[display]\n'
        f'window/size/viewport_width={args.width}\nwindow/size/viewport_height={args.height}\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
    )
    (fixture / "scenes/guide.tscn").write_text(
        '[gd_scene load_steps=2 format=3]\n'
        '[ext_resource type="Script" path="res://tests/ui_independent_options_board.gd" id="1"]\n'
        '[node name="IndependentGuideHost" type="Control"]\nscript = ExtResource("1")\n'
    )
    (fixture / "export_presets.cfg").write_text("")
    plan = [
        {"capture":"01-bow-initial", "expect":{"panels.hero_panel":True,"independent.ability_scroll":0,"independent.effects_enabled":True}},
        {"key":"End","capture":"02-options-enabled","expect":{"independent.motion_enabled":True}},
        {"click_name":"reduced_effects","capture":"03-fewer-layers-saved","expect":{"independent.effects_checked":True,"independent.receiver_effects":True,"independent.saved_effects":True}},
        {"key":"Tab","key_unused":"none","capture":"04-motion-focus","expect":{"focus_text":"Still ornamental motion"}},
        {"key":"space","capture":"05-motion-saved","expect":{"independent.motion_checked":True,"independent.receiver_motion":True,"independent.saved_motion":True}},
        {"key":"Home","capture":"06-bow-return","expect":{"independent.detail_scroll":0,"independent.saved_effects":True,"independent.saved_motion":True,"independent.receiver_meshes":0,"independent.receiver_casts":0}},
    ]
    plan_path = args.output / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    command = [
        "python3", str(fixture / "tools/ui-campaign/run.py"), "--project", str(fixture),
        "--mode", "integrated", "--plan", str(plan_path), "--output", str(args.output / "window"),
        "--display", str(args.display), "--width", str(args.width), "--height", str(args.height),
        "--renderer", "gl_compatibility", "--timeout", "45", "--render-threads", "1",
    ]
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", LP_NUM_THREADS="1")
    result = subprocess.run(command, env=env, check=False)
    receipt = {
        "scope": "Isolated 2D production guide and bundled fonts, actual XTest input and PNG pixels. Observer integrated mode only starts this 2D fixture; no world, hero mesh, GLB or cast is loaded. An idle production effect receiver retains real options without allocating any mesh.",
        "command": command, "exit_code": result.returncode, "source_pins": pins,
        "copied_sources_unchanged": all(sha(fixture / name) == digest for name, digest in pins.items()),
        "raw_3d_assets": list(map(str, fixture.rglob("*.glb"))),
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
