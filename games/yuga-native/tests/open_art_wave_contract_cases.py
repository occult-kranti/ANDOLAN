#!/usr/bin/env python3
"""Source/resource boundaries and independent numerical pair contracts.

No Godot, imports, Blender, provider process, candidate publication or pose test.
These are bounded source/fixture checks, never runtime or finished-art approval.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
REPAIR = PROJECT / "art/hero-rama-repair/repair_mesh.py"
DOMAIN = PROJECT / "art/hero-rama-repair/diagnose_domains.py"
ART = PROJECT / "art/open-art-wave"
SHADER = PROJECT / "shaders/rama_secondary_cloth.gdshader"
BINDER = ART / "integration/cloth_candidate.gd"
PINS = {
    "assets/heroes/rama-hero.glb": "de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5",
    "assets/heroes/rama-hero-mid.glb": "40737faf61e660f74dbb97b7a5a507869fdedd1a27cd964bb15e27e445a2d3cd",
    "assets/heroes/rama-hero-far.glb": "d5888a452c2a8b711a7a5d8542652762d73c2608047b0399a2486c9ed650f9aa",
    "shaders/rama_secondary_cloth.gdshader": "c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7",
}
CANDIDATE_PINS = {
    "source-manifest.json": "30d7b5bdd3062aafbcf75185932deadfeced5dd5bc850eeed0acc73fe05aafcb",
    "build-manifest.json": "ef1b0144a113110962c63e60602228298437d019742a4a8f06e02dfb9b1bef20",
    "materials/indigo-woven-cloth.tres": "856809ad52a04360f63d260ea5af1d217b6fb34323ab02fcfb70c754cd6af029",
}
BOOTSTRAP = PROJECT / "tools/native-analysis/setup-rea.sh"
BOOTSTRAP_PINS = {
    "package.json": "04df3d8e8a559cd75824d810268a49519164930cf09386e76b56bc8e086836ed",
    "package-lock.json": "73fa03d670870e8234e7823bca98e8cd846773fb661819ffe48a5bbb6728c7dd",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejected(fn):
    try:
        fn()
    except (ValueError, TypeError, IndexError):
        return
    raise AssertionError("Expected refusal")


def fixture():
    # Vertex0 and1 coincide. Vertex2 is distinct: only that pair can prove
    # persistence. The proof is about exact source channels, not tiny area.
    return {
        "POSITION": np.array([[0, 0, 0], [0, 0, 0], [0, 1, 0]], dtype=np.float32),
        "NORMAL": np.tile([0, 0, 1], (3, 1)).astype(np.float32),
        "TANGENT": np.tile([1, 0, 0, 1], (3, 1)).astype(np.float32),
        "TEXCOORD_0": np.zeros((3, 2), dtype=np.float32),
        "JOINTS_0": np.zeros((3, 4), dtype=np.uint16),
        "WEIGHTS_0": np.tile([1, 0, 0, 0], (3, 1)).astype(np.float32),
        "COLOR_0": np.tile([1, 1, 1, .5], (3, 1)).astype(np.float32),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.report.is_absolute() or args.report.exists():
        parser.error("--report must be a fresh absolute path")
    source_paths = [Path(__file__), REPAIR, DOMAIN, BINDER, SHADER,
                    ART / "source-manifest.json", ART / "build-manifest.json", BOOTSTRAP,
                    BOOTSTRAP.parent / "rea-runtime/package.json",
                    BOOTSTRAP.parent / "rea-runtime/package-lock.json"]
    before = {str(p.relative_to(PROJECT)): sha(p) for p in source_paths}
    repair = load("open_art_contract_repair", REPAIR)
    domain = load("open_art_contract_domain", DOMAIN)
    checks = []

    def check(name, kind, fn):
        try:
            detail = fn()
            checks.append({"name": name, "kind": kind, "passed": True,
                           **({"detail": detail} if detail is not None else {})})
        except Exception as error:
            checks.append({"name": name, "kind": kind, "passed": False,
                           "error": type(error).__name__ + ": " + str(error)})

    def require(value, message="Contract not met"):
        if not value:
            raise AssertionError(message)

    def runtime_pins():
        require(all(sha(PROJECT / p) == expected for p, expected in PINS.items()))
        require(repair.YUGA_SOURCE == PINS["assets/heroes/rama-hero.glb"])
        require(repair.YUGA_SHADER == PINS["shaders/rama_secondary_cloth.gdshader"])
        return {"scope": "Byte/source identity only; no engine behavior.", "pins": PINS}
    check("Accepted runtime GLBs and deformation shader remain pinned", "source_boundary", runtime_pins)

    def licensed_sources():
        require(all(sha(ART / p) == expected for p, expected in CANDIDATE_PINS.items()))
        manifest = json.loads((ART / "source-manifest.json").read_text())
        require(manifest["revision"] == "edc7c9e67c639d230715049ee31f9a96a6babbbe")
        require(manifest["asset_license"] == "CC0-1.0" and manifest["metadata_license"] == "CC-BY-4.0")
        source = ART / "source/microsoft-sheen-cloth"
        for row in manifest["files"]:
            p = source / row["file"]
            require(p.resolve().is_relative_to(source.resolve()))
            require(sha(p) == row["sha256"] and p.stat().st_size == row["bytes"])
            require("/" + manifest["revision"] + "/" in row["url"])
            require(row["license"] == "CC0-1.0" if p.suffix == ".png" else row["license"].startswith("CC-BY-4.0"))
        license_text = (source / "LICENSE.md").read_text()
        require("CC0-1.0" in license_text and "CC-BY-4.0" in license_text)
        metadata = json.loads((source / "metadata.json").read_text())
        require(metadata["legal"][0]["artist"] == "Microsoft")
        require(not list(source.glob("*.glb")))
        return {"scope": "Selected map/license bytes only; no historical-silk or commercial-model claim."}
    check("CC0 texture files and CCBY metadata retain separate exact provenance", "resource_boundary", licensed_sources)

    def candidate_resources():
        manifest = json.loads((ART / "build-manifest.json").read_text())
        require(manifest["source_manifest_sha256"] == sha(ART / "source-manifest.json"))
        for row in manifest["outputs"]:
            p = (PROJECT / row["path"]).resolve()
            require(p.is_relative_to(ART.resolve()))
            require(sha(p) == row["sha256"] and p.stat().st_size == row["bytes"])
        contract = manifest["material_contract"]
        require(contract["allowed_existing_surface_names"] == ["Cobalt handwoven silk"])
        require(set(contract["preserve_surfaces"]) == {"Cobalt lotus brocade", "Worked warm gold", "Swept black hair"})
        text = (ART / "materials/indigo-woven-cloth.tres").read_text()
        paths = re.findall(r'path="([^"]+)"', text)
        require(len(paths) == 3 and all(p.startswith("res://art/open-art-wave/textures/") for p in paths))
        require("transparency = 0" in text and "vertex_color_use_as_albedo = false" in text)
        return {"scope": "Resource/source references, not imported samplers or material appearance."}
    check("Candidate resources stay in authoring tree and retain semantic masks", "resource_boundary", candidate_resources)

    def binder_uniforms():
        text = BINDER.read_text()
        returned = next(line for line in text.splitlines() if line.strip().startswith('return {"base_color":'))
        fields = set(re.findall(r'"([a-z_]+)"\s*:', returned))
        uniforms = set(re.findall(r"uniform\s+\w+\s+(\w+)", SHADER.read_text()))
        require(fields == uniforms - {"secondary_offset"})
        require("secondary_offset" not in fields and 'const SOURCE_NAME := "Cobalt handwoven silk"' in text)
        require('material.shader != CLOTH_SHADER' in text and "func unbind()" in text)
        return {"mapped_uniforms": sorted(fields), "scope": "Static source boundary only; real material lifetime/rollback needs engine cases."}
    check("Optional cloth binder maps fragment uniforms without owning displacement", "source_boundary", binder_uniforms)

    idx = np.array([[0, 1, 2]], dtype=np.uint32)
    def pair_case(attrs, targets, strict_expected, core_expected):
        original = [value.tobytes() for value in attrs.values()]
        for policy, expected in [("strict", strict_expected), ("yuga-secondary-v1", core_expected)]:
            actual, _ = repair.coincident_proof(idx, attrs, targets, policy)
            require(bool(actual[0]) == expected, policy + " pair proof disagrees with independent channel contract")
        skins = [a for key, a in attrs.items() if key.startswith(("JOINTS_", "WEIGHTS_"))]
        classification = domain.classify(attrs["POSITION"], attrs["TEXCOORD_0"], idx.reshape(-1),
            skins, [t["POSITION"] for t in targets if "POSITION" in t], attrs["COLOR_0"],
            tuple(attrs.values()), tuple(a for t in targets for a in t.values()))["summary"]["counts"]
        require(bool(classification["allAttributeMorphByteIdenticalPair"]) == strict_expected)
        require(bool(classification["skeletalMorphColor0CoincidentPair"]) == core_expected)
        require(all(value.tobytes() == raw for value, raw in zip(attrs.values(), original)))

    check("Exact complete records prove the coincident pair", "numerical_fixture", lambda: pair_case(fixture(), [], True, True))
    for label, channel, value in [
        ("position differs despite tiny area", "POSITION", [1e-8, 0, 0]),
        ("primary joint differs", "JOINTS_0", [1, 0, 0, 0]),
        ("primary weight differs", "WEIGHTS_0", [.5, .5, 0, 0]),
        ("semantic alpha mask differs", "COLOR_0", [1, 1, 1, 1]),
    ]:
        def changed(channel=channel, value=value):
            attrs = fixture(); attrs[channel][1] = value
            pair_case(attrs, [], False, False)
        check(label, "numerical_fixture", changed)
    for label, channel, value in [
        ("UV seam blocks default strict proof", "TEXCOORD_0", [1, 0]),
        ("normal seam only permitted by bounded position policy", "NORMAL", [0, 1, 0]),
        ("tangent seam only permitted by bounded position policy", "TANGENT", [-1, 0, 0, -1]),
    ]:
        def seam(channel=channel, value=value):
            attrs = fixture(); attrs[channel][1] = value
            pair_case(attrs, [], False, True)
        check(label, "numerical_fixture", seam)
    for channel in ("JOINTS_1", "WEIGHTS_1"):
        def extra(channel=channel):
            attrs = fixture()
            attrs["WEIGHTS_0"][:, 0] = .75
            attrs["JOINTS_1"] = np.tile([1, 0, 0, 0], (3, 1)).astype(np.uint16)
            attrs["WEIGHTS_1"] = np.tile([.25, 0, 0, 0], (3, 1)).astype(np.float32)
            attrs[channel][1] = [2, 0, 0, 0] if channel == "JOINTS_1" else [.125, .125, 0, 0]
            pair_case(attrs, [], False, False)
        check("Additional " + channel + " is part of position proof", "numerical_fixture", extra)
    for channel, core_expected in [("POSITION", False), ("NORMAL", True)]:
        def morph(channel=channel, core_expected=core_expected):
            delta = np.zeros((3, 3), dtype=np.float32); delta[1] = [0, 0, 1]
            pair_case(fixture(), [{channel: delta}], False, core_expected)
        check("Morph " + channel + " has explicit policy scope", "numerical_fixture", morph)
    def collinear():
        attrs = fixture(); attrs["POSITION"] = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=np.float32)
        pair_case(attrs, [], False, False)
    check("Zero rest area without coincident pair is retained", "numerical_fixture", collinear)

    with tempfile.TemporaryDirectory(prefix="open-art-contract-") as temporary:
        tmp = Path(temporary); source = PROJECT / "assets/heroes/rama-hero.glb"
        check("Report cannot alias source", "output_boundary", lambda: rejected(lambda: repair.fresh_paths(source, tmp / "candidate.glb", source)))
        check("Candidate cannot enter runtime asset tree", "output_boundary", lambda: rejected(lambda: repair.fresh_paths(source, PROJECT / "assets/heroes/UNWRITTEN.glb", tmp / "report.json")))
        alias = tmp / "project-alias"; alias.symlink_to(PROJECT, target_is_directory=True)
        check("Symlink parent cannot hide an in-project candidate", "output_boundary", lambda: rejected(lambda: repair.fresh_paths(source, alias / "assets/UNWRITTEN.glb", tmp / "report.json")))
        existing = tmp / "existing.glb"; existing.write_bytes(b"retain exact prior evidence")
        def no_overwrite():
            prior = existing.read_bytes()
            rejected(lambda: repair.fresh_paths(source, existing, tmp / "report.json"))
            require(existing.read_bytes() == prior)
        check("Existing candidate is refused without overwrite", "output_boundary", no_overwrite)

        def bootstrap_dry_run():
            require(sha(BOOTSTRAP) == "c20d4fdf0586ee36c8dc4587461c416e780447e83dec4a570c4e9b7eeb19f212")
            require(all(sha(BOOTSTRAP.parent / "rea-runtime" / p) == expected for p, expected in BOOTSTRAP_PINS.items()))
            binaries = tmp / "fake-tools"; binaries.mkdir()
            marker = tmp / "unexpected-node-npm-probe"
            for name in ("node", "npm"):
                p = binaries / name
                p.write_text('#!/bin/sh\nprintf x >> "$YUGA_CONTRACT_PROBE"\nexit 91\n')
                p.chmod(0o755)
            destination = tmp / "UNCREATED-bootstrap"
            env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"],
                       YUGA_CONTRACT_PROBE=str(marker))
            run = subprocess.run(["bash", str(BOOTSTRAP), "--dry-run", "--destination", str(destination)],
                                 env=env, capture_output=True, text=True, timeout=15)
            require(run.returncode == 0, run.stderr)
            plan = json.loads(run.stdout)
            require(plan["mode"] == "DRY_RUN" and plan["source_inputs"] == BOOTSTRAP_PINS)
            require(not destination.exists() and not marker.exists())
            require(not plan["runtime_probes_executed"] and not plan["lifecycle_scripts"]
                    and not plan["persistent_agent_configuration"] and not plan["native_providers_installed"])
            return {"scope": "Actual offline dry-run with adversarial node/npm sentinels; no install/provider/network readiness claim."}
        check("REA bootstrap dry-run preserves outside destination and never invokes node/npm", "output_boundary", bootstrap_dry_run)

    after = {str(p.relative_to(PROJECT)): sha(p) for p in source_paths}
    check("All sampled source/resource files stayed unchanged during this run", "source_boundary", lambda: require(before == after))
    passed = all(row["passed"] for row in checks)
    report = {"passed": passed, "checks": checks, "count": len(checks), "sources": before,
              "test_sha256": sha(Path(__file__)), "runtime_pins": PINS,
              "scope": "Source/resource/output guards and analytic exact-channel corner fixtures. Opt-in helper cases do not authorize a different asset; the public repair requires exact source/shader pins. No engine/material rollback/posed deformation/render/provider/runtime promotion acceptance."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": passed, "checks": len(checks), "failed": [c["name"] for c in checks if not c["passed"]]}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
