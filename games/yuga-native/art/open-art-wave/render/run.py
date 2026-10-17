#!/usr/bin/env python3
"""Own a serialized native material comparison. Requires root's heavy slot.

--dry-run starts no processes. Output must be new; old failures are preserved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[3]
SIZE = (1280, 960)
TEXTURES = ["res://art/open-art-wave/textures/indigo-woven-" + name + ".png" for name in ("albedo", "roughness", "normal")]
DIRECT = ["res://project.godot", "res://art/world/confluence-map.json", "res://art/open-art-wave/render/capture.gd", "res://art/open-art-wave/render/run.py", "res://art/open-art-wave/integration/cloth_candidate.gd", "res://art/open-art-wave/materials/indigo-woven-cloth.tres", "res://art/open-art-wave/source-manifest.json", "res://art/open-art-wave/build-manifest.json"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(project: Path, resource: str) -> Path:
    if not resource.startswith("res://"):
        raise ValueError("Expected res:// resource")
    path = (project / resource.removeprefix("res://")).resolve()
    if not path.is_relative_to(project):
        raise ValueError("Resource escapes project")
    return path


def source_identity(project: Path, canonical: Path) -> dict:
    resources = list(DIRECT)
    for directory in ("scripts", "shaders", "assets", "scenes", "art/open-art-wave/textures"):
        resources.extend("res://" + str(path.relative_to(project)) for path in (project / directory).rglob("*") if path.is_file())
    original = {}
    fixture_imports = {}
    for resource in sorted(resources):
        copied = local(project, resource)
        origin = local(canonical, resource)
        if not origin.is_file():
            if resource not in [path + ".import" for path in TEXTURES]:
                raise ValueError("Unexpected fixture-only source: " + resource)
            fixture_imports[resource] = digest(copied)
            continue
        pin = digest(origin)
        if digest(copied) != pin:
            raise ValueError("Fixture differs from original source: " + resource)
        original[resource] = pin
    return {"canonical_source_sha256": original, "fixture_only_texture_imports": fixture_imports,
            "canonical_project": str(canonical), "fixture_project": str(project),
            "scope": "Exact original/copy source equality; cloned cache freshness independently checked by source/destination MD5 and import hashes"}


def validate(report: dict, output: Path, project: Path, preserve_albedo: bool = False) -> dict:
    from PIL import Image, ImageChops
    if report.get("schema") != 1 or report.get("kind") != "actual-open-art-cloth-comparison" or not report.get("complete") or report.get("failure"):
        raise ValueError("Incomplete native comparison: " + str(report.get("failure")))
    if (report.get("width"), report.get("height")) != SIZE or report.get("renderer") != "forward_plus" or report.get("display", "").lower() != "x11":
        raise ValueError("Wrong actual native renderer/display/size")
    profile = report.get("profile", {})
    expected_profile = "preserve-original-albedo_cc0-roughness-normal-v1" if preserve_albedo else "cc0-albedo-roughness-normal-v1"
    if profile.get("id") != expected_profile or profile.get("preserve_albedo") != preserve_albedo:
        raise ValueError("Wrong literal material profile")
    albedo_fields = {"base_color", "base_texture", "use_base_texture"}
    if len(profile.get("owned_uniforms", [])) != (12 if preserve_albedo else 15) or (preserve_albedo and albedo_fields.intersection(profile["owned_uniforms"])):
        raise ValueError("Wrong bounded profile uniform ownership")
    if not report.get("source_unchanged") or report["source_sha256"] != report["source_after_sha256"]:
        raise ValueError("Source changed during take")
    for resource, sha in report["source_sha256"].items():
        if digest(local(project, resource)) != sha:
            raise ValueError("Source pin changed: " + resource)
    for resource, entry in report["imports"].items():
        if not entry["fresh"] or digest(local(project, resource)) != entry["source_sha256"]:
            raise ValueError("Source/import mismatch")
        for path_key, hash_key in (("metadata", "metadata_sha256"), ("imported", "sha256"), ("stamp", "stamp_sha256")):
            if digest(local(project, entry[path_key])) != entry[hash_key]:
                raise ValueError("Imported resource changed: " + entry[path_key])
    for resource in TEXTURES:
        entry = report["imports"].get(resource, {})
        if not entry.get("mipmaps_generate") or not entry.get("actual_has_mipmaps") or entry.get("dimensions") != [1024, 1024]:
            raise ValueError("Imported candidate map lacks actual mip chain")
    for resource in ("rama-hero.glb", "rama-hero-mid.glb", "rama-hero-far.glb"):
        entry = report["imports"].get("res://assets/heroes/" + resource, {})
        if not entry.get("fresh") or entry.get("generate_lods") is not False:
            raise ValueError("Authored hero LOD import invariant failed")
    expected = [("courtyard-day", "courtyard", False, 780, 0), ("courtyard-night", "courtyard", True, 780, 0), ("confluence-day", "confluence", False, 350, 1), ("confluence-night", "confluence", True, 350, 1)]
    if len(report.get("pairs", [])) != 4 or len(report.get("states", [])) != 4:
        raise ValueError("Exactly four matched pairs required")
    images = []
    differences = []
    last_frame = -1
    for pair, state, (name, scene, night, pixels, level) in zip(report["pairs"], report["states"], expected):
        if (pair["id"], pair["scene"], pair["night"], pair["target_hero_pixels"], pair["selected_level"]) != (name, scene, night, pixels, level):
            raise ValueError("Pair order/LOD/lighting contract mismatch")
        if not all(pair.get(key) for key in ("same_camera", "same_frozen_state_except_owned_uniforms", "same_lighting", "full_restore_exact")):
            raise ValueError("Matched state invariant failed")
        a, b = pair["baseline"], pair["candidate"]
        if a["camera"] != b["camera"] or a["lighting"] != b["lighting"] or a["state_sha256"] != b["state_sha256"]:
            raise ValueError("Camera/exposure/state changed within pair")
        if not state["full_restore_exact"] or state["baseline_full"] != state["restored_full"]:
            raise ValueError("Full source materials did not restore exactly")
        frozen = state["frozen_excluding_owned_uniforms"]
        if frozen["live_rigs"] != 1 or len(frozen["bones"]) != 164 or frozen["face_meshes"] != 1 or not frozen["paused"]:
            raise ValueError("Actual frozen unique face/rig invariant failed")
        if not frozen["controllers"]["motion"]["finite"] or not frozen["controllers"]["secondary"]["finite"]:
            raise ValueError("Invalid functional controllers")
        binding, unbind = pair["binding"], pair["unbind"]
        if not binding.get("bound") or binding.get("unique_materials", 0) <= 0 or binding.get("surface_slots", 0) <= 0 or binding.get("candidate_filter") != 3:
            raise ValueError("Actual secondary-owned binding absent")
        if binding["candidate_sha256"] != digest(local(project, binding["candidate_path"])):
            raise ValueError("Candidate binding resource hash mismatch")
        if binding.get("preserve_albedo") != preserve_albedo or set(binding["touched_fields"]) != set(profile["owned_uniforms"]):
            raise ValueError("Bound profile uniform set mismatch")
        if "secondary_offset" in binding["touched_fields"] or unbind["conflicts"] or unbind["invalidated_materials"] or unbind["restored_fields"] <= 0:
            raise ValueError("Fixture overwrote secondary owner or failed restoration")
        if state["baseline_full"] == state["candidate_full"]:
            raise ValueError("Candidate made no material-state change")
        opened = []
        for shot in (a, b):
            filename = Path(shot["file"])
            if filename.name != str(filename) or filename.suffix != ".png":
                raise ValueError("Unsafe framebuffer filename")
            path = output / filename
            if digest(path) != shot["sha256"]:
                raise ValueError("Original PNG hash mismatch")
            with Image.open(path) as image:
                if image.size != SIZE:
                    raise ValueError("Framebuffer dimensions mismatch")
                image.load()
                opened.append(image.convert("RGB"))
            if shot["render_frame"] <= last_frame or not shot["tree_paused"]:
                raise ValueError("Render chronology or freeze failed")
            last_frame = shot["render_frame"]
            lod = shot["lod"]
            if lod["live_rigs"] != 1 or lod["live_bones"] != 164 or lod["visible_levels"] != [level] or lod["errors"]:
                raise ValueError("Rendered LOD/one-rig invariant failed")
            images.append({"file": filename.name, "sha256": shot["sha256"]})
        bounds = ImageChops.difference(*opened).getbbox()
        if bounds is None:
            raise ValueError("Actual framebuffers identical despite material change")
        differences.append({"pair": name, "pixel_difference_bounds": list(bounds), "scope": "Raw difference includes temporal renderer effects; not isolated cloth quality measurement"})
    if len(list(output.glob("*.png"))) != 8:
        raise ValueError("Exactly eight unaltered raw framebuffers required")
    return {"complete": True, "pairs": 4, "raw_images": images, "differences": differences,
            "scope": "Source/import/functional state and actual framebuffer validation; art review remains independent"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--canonical-project", type=Path, default=PROJECT)
    parser.add_argument("--runtime", type=Path, default=Path("/workspace/tooling/native-render/runtime"))
    parser.add_argument("--godot", default=shutil.which("godot"))
    parser.add_argument("--display", type=int, default=147)
    parser.add_argument("--shader-cache-seed", type=Path)
    parser.add_argument("--preserve-albedo", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve(); canonical = args.canonical_project.resolve(); output = args.output.resolve(); runtime = args.runtime.resolve()
    user = output.with_name(output.name + "-user")
    log_path = output.with_name(output.name + ".godot.log")
    xlog_path = output.with_name(output.name + ".xvfb.log")
    if not args.output.is_absolute() or any(path.exists() for path in (output, user, log_path, xlog_path)) or not 90 <= args.display <= 199 or Path(f"/tmp/.X11-unix/X{args.display}").exists():
        parser.error("Require fresh absolute output and unused display90–199")
    command = [args.godot, "--path", str(project), "--display-driver", "x11", "--rendering-method", "forward_plus", "--audio-driver", "Dummy", "--disable-vsync", "--fixed-fps", "15", "--max-threads", "2", "--script", "res://art/open-art-wave/render/capture.gd", "--", "--output=" + str(output)]
    if args.preserve_albedo: command.append("--preserve-albedo")
    if args.dry_run:
        print(json.dumps({"starts_processes": False, "command": command, "expected_pairs": 4, "raw_pngs": 8}, indent=2)); return
    if project == canonical and (project / "art/.gdignore").exists():
        parser.error("Candidate art is deliberately excluded from the real project; stage an isolated review project instead")
    identity_before = source_identity(project, canonical)
    xvfb = runtime / "usr/bin/Xvfb"; icd = runtime / "usr/share/vulkan/icd.d/lvp_icd.json"
    if not args.godot or not xvfb.is_file() or not icd.is_file():
        parser.error("Prepared Godot/render runtime required")
    output.parent.mkdir(parents=True, exist_ok=True); user.mkdir()
    env = os.environ.copy()
    env.update(DISPLAY=f":{args.display}", LP_NUM_THREADS="2", VK_ICD_FILENAMES=str(icd), LD_LIBRARY_PATH=str(runtime / "usr/lib/x86_64-linux-gnu") + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else ""))
    for key, folder in (("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")):
        path = user / folder; path.mkdir(); env[key] = str(path)
    env["MESA_SHADER_CACHE_DIR"] = str(user / "cache/mesa")
    if args.shader_cache_seed:
        if not args.shader_cache_seed.is_dir(): parser.error("Shader cache seed missing")
        shutil.copytree(args.shader_cache_seed, env["MESA_SHADER_CACHE_DIR"])
    with log_path.open("x") as log, xlog_path.open("x") as xlog:
        server = subprocess.Popen([str(xvfb), env["DISPLAY"], "-screen", "0", "1280x960x24", "-nolisten", "tcp", "-extension", "MIT-SHM", "-ac"], env=env, stdout=xlog, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None: raise RuntimeError("Owned display stopped")
                if Path(f"/tmp/.X11-unix/X{args.display}").exists(): break
                time.sleep(.1)
            else: raise RuntimeError("Owned display failed to start")
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1100)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill(); server.wait()
    text = log_path.read_text()
    warnings = [line for line in text.splitlines() if "WARNING:" in line]
    if result.returncode or "SCRIPT ERROR:" in text or "\nERROR:" in text:
        raise RuntimeError("Native capture failed; preserve " + str(log_path))
    report_path = output / "material-capture.json"
    report = json.loads(report_path.read_text())
    validation = validate(report, output, project, args.preserve_albedo)
    identity_after = source_identity(project, canonical)
    if identity_before != identity_after:
        raise ValueError("Original/copy source identity changed during take")
    (output / "source-identity.json").write_text(json.dumps({"complete": True, "before": identity_before, "after": identity_after, "unchanged": True}, indent=2) + "\n")
    snapshots = output / "source"; snapshots.mkdir()
    for resource in report["source_sha256"]:
        path = local(project, resource)
        if path.suffix in (".gd", ".gdshader", ".gdshaderinc", ".py", ".tres", ".tscn", ".json", ".godot", ".import"):
            target = snapshots / path.relative_to(project); target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
    validation.update({"command": command, "godot_exit_code": result.returncode, "runner_sha256": digest(Path(__file__)), "report_sha256": digest(report_path), "godot_log_sha256": digest(log_path), "xvfb_log_sha256": digest(xlog_path), "profile": report.get("profile"), "warnings": warnings, "shader_cache_seed": str(args.shader_cache_seed) if args.shader_cache_seed else None})
    (output / "capture-run.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps({"complete": True, "output": str(output), "pairs": 4, "raw_pngs": 8, "warnings": warnings}))


if __name__ == "__main__":
    main()
