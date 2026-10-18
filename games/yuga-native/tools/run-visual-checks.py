#!/usr/bin/env python3
"""Run source-bound native visual or screen contracts after Godot import.

Both cloud setup and CI call this catalog. Strict process lifetime and report
validation come from the existing authoring runner. These tests do not render
pixels or qualify art, hardware performance, online play or a release.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import zlib

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
HELPER_PATH = PROJECT / "tools/run-authoring-checks.py"
spec = importlib.util.spec_from_file_location("visual_authoring_helper", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
LIMITS = "Headless visual component, real resource and native identity contracts only; no rendered-art, continuous-motion, physical-GPU, online or release acceptance."
SUITES = (
    ("surface-finish", "godot", "tests/rama_surface_finish_cases.gd", ("--resources",)),
    ("surface-finish-adversarial", "godot", "tests/rama_finish_adversarial_cases.gd", ()),
    ("courtyard-atmosphere", "godot", "tests/hero_atmosphere_cases.gd", ()),
    ("courtyard-district", "godot", "tests/hero_district_cases.gd", ()),
    ("courtyard-environment-adversarial", "godot", "tests/hero_environment_adversarial_cases.gd", ()),
    ("ability-calligraphy", "godot", "tests/rama_ability_visual_cases.gd", ()),
    ("ability-event-adversarial", "godot", "tests/rama_effect_adversarial_cases.gd", ()),
    ("motion-polish", "godot", "tests/rama_motion_polish_cases.gd", ()),
    ("motion-adversarial", "godot", "tests/rama_motion_adversarial_cases.gd", ()),
    ("optional-character-accents", "godot", "tests/rama_character_accents_cases.gd", ("--resources",)),
    ("native-content-pins", "python", "tools/check-native-contracts.py", ()),
    ("native-contract-admission", "godot", "tests/native_contract_cases.gd", ()),
    ("desktop-release-continuity", "godot", "tests/desktop_s1_release_cases.gd",
     ("--baseline-script=res://docs/evidence/desktop-finish/S1/W5/baseline/rama_motion.gd", "--compact-report")),
    ("desktop-motion-scene-entry", "godot", "tests/desktop_s3_transition_scene_cases.gd",
     ("--hz=60", "--summary-report")),
    ("desktop-motion-transition-guard", "godot", "tests/desktop_s3_transition_guard_cases.gd", ()),
    ("desktop-landing-support-boundary", "godot", "tests/desktop_landing_support_boundary_cases.gd", ()),
    ("desktop-landing-pause", "godot", "tests/desktop_landing_pause_cases.gd", ()),
    ("desktop-world-route-parity", "godot", "tests/desktop_world_route_parity_cases.gd", ()),
    ("desktop-volley-feedback", "godot", "tests/desktop_i02_volley_feedback_cases.gd", ("--warmup-ticks=200",)),
)
SCREEN_SUITES = (
    ("ui-launch", "godot", "tests/launch_shell_cases.gd", ()),
    ("ui-theme", "godot", "tests/ui_theme_cases.gd", ()),
    ("ui-fonts", "godot", "tests/ui_font_cases.gd", ()),
    ("ui-hud-information", "godot", "tests/ui_hud_information_cases.gd", ()),
    ("ui-hud-context", "godot", "tests/ui_hud_context_cases.gd", ()),
    ("ui-controls-state", "godot", "tests/ui_controls_state_cases.gd", ()),
    ("ui-controls-lifecycle", "godot", "tests/ui_controls_lifecycle_cases.gd", ()),
    ("ui-guide-capabilities", "godot", "tests/ui_guide_capability_cases.gd", ()),
    ("ui-focus-recovery", "godot", "tests/ui_focus_recovery_cases.gd", ()),
    ("ui-launch-integration", "godot", "tests/ui_launch_integration_cases.gd", ()),
    ("ui-end-to-end", "godot", "tests/ui_end_to_end_cases.gd", ()),
    ("ui-transition-lifecycle", "godot", "tests/ui_transition_lifecycle_cases.gd", ()),
    ("ui-boot-native", "godot", "tests/ui_boot_cases.gd", ("--native",)),
    ("ui-world-objectives", "godot", "tests/ui_world_objective_cases.gd", ()),
    ("ui-pause-navigation", "godot", "tests/ui_pause_navigation_cases.gd", ()),
    ("ui-map-consistency", "godot", "tests/ui_theme_map_consistency_cases.gd", ()),
    ("ui-independent-modal", "godot", "tests/ui_independent_modal_cases.gd", ()),
    ("ui-resize-navigation", "godot", "tests/ui_resize_navigation_cases.gd", ()),
    ("ui-hud-edges", "godot", "tests/ui_hud_edge_cases.gd", ()),
    ("ui-preference-edges", "godot", "tests/ui_preferences_edge_cases.gd", ()),
    ("ui-independent-theme", "godot", "tests/ui_independent_theme_cases.gd", ()),
    ("ui-independent-lifetime", "godot", "tests/ui_independent_lifecycle_cases.gd", ()),
    ("ui-transition-signals", "fixture", "tools/ui-campaign/check-transition.py", ()),
    ("ui-effects-feedback", "godot", "tests/ui_u5_effect_feedback_cases.gd", ()),
    ("ui-boot-recovery", "fixture", "tests/ui_s1_loading_fixture.py", ()),
    ("ui-title-portrait", "godot", "tests/ui_s1_portrait_cases.gd", ()),
    ("ui-launch-composition", "godot", "tests/desktop_finish_s1_launcher_cases.gd", ()),
    ("ui-world-atlas", "godot", "tests/desktop_finish_s1_atlas_cases.gd", ()),
    ("ui-action-hud", "godot", "tests/desktop_s1_hud_cases.gd", ()),
    ("ui-action-hud-fit", "godot", "tests/desktop_s1_hud_layout_cases.gd", ()),
    ("ui-host-replacement", "fixture", "tests/ui_s1_loading_fixture.py", ("--case", "host-replacement")),
    ("ui-loading-presentation", "godot", "tests/desktop_finish_s2_loading_view_cases.gd", ()),
    ("ui-loading-readiness", "godot", "tests/ui_s3_loading_readiness_cases.gd", ()),
    ("ui-hud-readability", "godot", "tests/desktop_s3_hud_readability_cases.gd", ()),
    ("ui-atlas-layout", "godot", "tests/desktop_s3_atlas_layout_cases.gd", ()),
    ("ui-cancel-focus", "fixture", "tests/ui_s1_loading_fixture.py", ("--case", "cancel-focus")),
    ("ui-preferences-relaunch", "fixture", "tests/desktop_d05_preferences_fixture.py", ()),
    ("ui-compact-navigation-routes", "godot", "tests/desktop_d03_d05_navigation_audit_cases.gd", ()),
    ("ui-world-compact-title", "godot", "tests/desktop_world_compact_title_cases.gd", ()),
    ("ui-title-identity", "godot", "tests/desktop_d01_title_identity_cases.gd", ()),
    ("ui-outcome-shortcuts", "godot", "tests/desktop_d08_outcome_shortcut_cases.gd", ()),
    ("ui-world-compact-first-entry", "godot", "tests/desktop_world_compact_first_entry_cases.gd", ()),
)
SCREEN_LIMITS = "Headless native screen, glyph, input-state and scene-lifecycle checks only; no OS-input, rendered-layout, art, GPU performance, online or packaged-release acceptance."
# Tests inherited by selected scripts and tests invoked by fixture runners are
# sources too. Pin them explicitly instead of claiming every historical archive.
SUITE_DEPENDENCIES = {
    "ui-transition-signals": ("tests/ui_transition_signal_cases.gd",),
    "ui-boot-recovery": ("tests/ui_s1_loading_cases.gd",),
    "ui-host-replacement": ("tests/ui_s2_transition_cases.gd",),
    "ui-cancel-focus": ("tests/ui_s3_cancel_focus_cases.gd",),
    "ui-preferences-relaunch": ("tests/desktop_d05_preferences_cases.gd",),
    "ui-action-hud": ("tests/ui_i1_action_hud_cases.gd",),
    "ui-action-hud-fit": ("tests/desktop_s1_hud_cases.gd", "tests/ui_i1_action_hud_cases.gd"),
    "ui-hud-readability": ("tests/ui_i1_action_hud_cases.gd",),
    "desktop-release-continuity": ("tests/graphics_g1_motion_cases.gd",
                                   "docs/evidence/desktop-finish/S1/W5/baseline/rama_motion.gd"),
    "desktop-motion-scene-entry": ("tests/graphics_g2_support_cases.gd",
                                    "docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd"),
    "desktop-motion-transition-guard": ("tests/graphics_g2_support_cases.gd",
                                        "docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd",
                                        "docs/evidence/desktop-finish/S3/W5/guard-witness.json"),
    "desktop-landing-support-boundary": ("tests/graphics_g2_support_cases.gd",),
    "desktop-landing-pause": ("tests/graphics_g2_support_cases.gd",
                               "docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd"),
}
# These fixtures explicitly use 120 Hz physics; pause/resume observes exactly
# one physics tick per process frame. Preserve their sealed invocation cadence.
SUITE_FIXED_FPS = {"desktop-landing-support-boundary": 120, "desktop-landing-pause": 120}


def sources(selected: list[tuple]) -> dict:
    # Complete runtime bytes, selected tests, historical identity fixtures and
    # runner dependencies are frozen. Imported cache contents are not sources.
    paths = {Path(__file__).resolve(), HELPER_PATH, PROJECT / "project.godot",
             PROJECT / "export_presets.cfg", *(PROJECT / item[2] for item in selected)}
    for item in selected:
        paths.update(PROJECT / name for name in SUITE_DEPENDENCIES.get(item[0], ()))
    for folder in ("scripts", "shaders", "scenes", "assets", "tests/fixtures/contracts"):
        paths.update(path for path in (PROJECT / folder).rglob("*") if path.is_file())
    records = {str(path.relative_to(PROJECT)): {"bytes": path.stat().st_size,
               "sha256": helper.sha(path)} for path in sorted(paths)}
    return records


def motion_trace_problems(report: Path, data: dict) -> list[str]:
    """Bind a bounded CI summary to its adjacent, lossless native pose trace."""
    record = data.get("trace")
    trace = report.with_name(report.name + ".trace.json.gz")
    if not isinstance(record, dict) or record.get("path") != trace.name or record.get("encoding") != "gzip":
        return ["motion_trace_must_be_adjacent_relative_gzip"]
    if trace.is_symlink() or not trace.is_file():
        return ["motion_trace_missing_or_symlink"]
    try:
        size = trace.stat().st_size
        if not 0 < size <= 8 * 1024 * 1024 or record.get("bytes") != size or record.get("sha256") != helper.sha(trace):
            return ["motion_trace_compressed_identity_mismatch"]
        # Bound decompression even when a corrupted child receipt claims a
        # smaller size. This is evidence validation, not another pose replay.
        with gzip.open(trace, "rb") as stream:
            raw = stream.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024 or record.get("uncompressed_bytes") != len(raw) or record.get("uncompressed_sha256") != hashlib.sha256(raw).hexdigest():
            return ["motion_trace_uncompressed_identity_mismatch"]
        full = json.loads(raw)
        if not isinstance(full, dict):
            return ["motion_trace_not_object"]
        rows, bones = full.get("rows"), full.get("bone_names")
        if not isinstance(rows, list) or not rows or not isinstance(bones, list) or not bones or record.get("rows") != len(rows) or record.get("bones") != len(bones):
            return ["motion_trace_census_mismatch"]
        expected = {key: value for key, value in data.items() if key != "trace"}
        actual = {key: value for key, value in full.items() if key not in ("rows", "bone_names")}
        if actual != expected:
            return ["motion_trace_summary_mismatch"]
    except (OSError, EOFError, ValueError, zlib.error):
        return ["motion_trace_unreadable"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="godot")
    parser.add_argument("--python", dest="python_engine", default=sys.executable)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--catalog", choices=["visual", "screens"], default="visual")
    parser.add_argument("--suite", action="append", choices=[item[0] for item in (*SUITES, *SCREEN_SUITES)])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-cpus", type=int, default=2)
    args = parser.parse_args()
    catalog = SUITES if args.catalog == "visual" else SCREEN_SUITES
    limits = LIMITS if args.catalog == "visual" else SCREEN_LIMITS
    if args.suite and not set(args.suite).issubset({item[0] for item in catalog}):
        parser.error("Every --suite must belong to the selected --catalog")
    selected = [item for item in catalog if not args.suite or item[0] in args.suite]
    if args.list:
        print(json.dumps({"suites": [{"id": i, "kind": k, "source": s, "arguments": a}
                         for i, k, s, a in selected], "scope": limits}, indent=2))
        return 0
    if args.output is None or not math.isfinite(args.timeout) or not 0 < args.timeout <= 1800 or not 1 <= args.max_cpus <= 64:
        parser.error("A fresh --output, timeout in (0,1800] and max-cpus in [1,64] are required")
    try:
        engine = helper.executable(args.engine)
        python = helper.executable(args.python_engine)
        output = args.output.absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("Output already exists; use a fresh directory")
        if output.resolve().is_relative_to(REPOSITORY):
            raise ValueError("Generated reports must be outside the checkout")
        output.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for name in ("reports", "logs", "users"):
        (output / name).mkdir()
    if hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:args.max_cpus])
    before = sources(selected)
    helper.write_json(output / "source-before.json", before)
    summary = {"schema": 1, "passed": False, "catalog":args.catalog, "scope": limits, "selected_suites": [item[0] for item in selected],
               "suites": [], "sources_before_sha256": helper.sha(output / "source-before.json")}
    helper.write_json(output / "summary.json", summary)
    env = os.environ.copy()
    env.update(LP_NUM_THREADS="2", PYTHONDONTWRITEBYTECODE="1")
    probe = helper.preparation_process("engine-version", [engine, "--version"], output, env, min(args.timeout, 10))
    summary["engine_probe"] = probe
    summary["engine_version"] = (output / probe["stdout"]).read_text(errors="replace").strip()
    if not probe["passed"] or not summary["engine_version"].startswith("4.6.3.stable."):
        summary["error"] = "Godot4.6.3_standard_required"
        helper.write_json(output / "summary.json", summary)
        return 1
    for suite_id, kind, source, arguments in selected:
        report = output / "reports" / (suite_id + ".json")
        user = output / "users" / suite_id
        user.mkdir()
        suite_env = env.copy()
        suite_env.update(XDG_DATA_HOME=str(user / "data"), XDG_CONFIG_HOME=str(user / "config"), XDG_CACHE_HOME=str(user / "cache"))
        if kind == "godot":
            command = [engine, "--headless", "--single-threaded-scene", "--audio-driver", "Dummy",
                       "--path", str(PROJECT), "--fixed-fps", str(SUITE_FIXED_FPS.get(suite_id, 60)), "--script", "res://" + source,
                       "--", "--report=" + str(report), *arguments]
        elif kind == "fixture":
            command = [python, str(PROJECT / source), "--engine", engine,
                       "--report=" + str(report), *arguments]
        else:
            command = [python, str(PROJECT / source), "--report=" + str(report), *arguments]
        result = helper.execute_suite(suite_id, command, report, output, env=suite_env, timeout=args.timeout)
        # Positive resource flags prevent a synthetic-only invocation from
        # silently substituting for the two actual-resource modes in this catalog.
        if result["passed"] and suite_id in ("surface-finish", "optional-character-accents"):
            data, _ = helper.inspect_report(report)
            key = "real_maps" if suite_id == "surface-finish" else "resources"
            if data.get(key) is not True:
                result["passed"] = False
                result["problems"].append("actual_resource_mode_not_exercised")
        if result["passed"] and suite_id == "desktop-motion-scene-entry":
            data, _ = helper.inspect_report(report)
            problems = motion_trace_problems(report, data)
            result["problems"].extend(problems)
            result["passed"] = not problems
            if not problems:
                result["trace"] = {**data["trace"], "path": "reports/" + data["trace"]["path"]}
        summary["suites"].append(result)
        helper.write_json(output / "summary.json", summary)
        print(json.dumps({"suite": suite_id, "passed": result["passed"], "checks": result.get("checks", 0), "exit_code": result["exit_code"]}), flush=True)
    after = sources(selected)
    helper.write_json(output / "source-after.json", after)
    summary["sources_after_sha256"] = helper.sha(output / "source-after.json")
    summary["checked_sources_unchanged"] = before == after
    summary["checks"] = sum(item.get("checks", 0) for item in summary["suites"])
    summary["passed"] = bool(summary["suites"]) and summary["checked_sources_unchanged"] and all(item["passed"] for item in summary["suites"])
    helper.write_json(output / "summary.json", summary)
    print(json.dumps({"passed": summary["passed"], "suites": len(selected), "checks": summary["checks"], "output": str(output), "scope": limits}))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
