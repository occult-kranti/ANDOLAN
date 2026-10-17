#!/usr/bin/env python3
"""Stage one R2-01 skin variable in a fresh external overlay; never edit input."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
REPOSITORY = PROJECT.parents[1]
ROUGH_IMPORT = "assets/materials/rama-finish/skin-roughness.png.import"
FINISH = "scripts/rama_surface_finish.gd"
VARIANTS = {
    "control": None,
    "roughness-mips": (
        ROUGH_IMPORT, "mipmaps/generate=false\n", "mipmaps/generate=true\n"
    ),
    "sss-off-diagnostic": (
        FINISH,
        '"Rama warm skin":{"map":"skin","values":{"metallic_specular":.34,"subsurf_scatter_enabled":true,',
        '"Rama warm skin":{"map":"skin","values":{"metallic_specular":.34,"subsurf_scatter_enabled":false,',
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stage(project: Path, output: Path, variant: str) -> dict:
    project = project.resolve(strict=True)
    # Resolve all parents before touching output, including a symlinked parent.
    output = output.resolve()
    if output.is_relative_to(REPOSITORY) or output.is_relative_to(project):
        raise ValueError("Output must be outside the repository and source project")
    if output.exists():
        raise ValueError("Output must not exist; preserve earlier evidence")
    source = json.loads((HERE / "source-manifest.json").read_text())
    profile = json.loads((HERE / "material-profile.json").read_text())
    variant_spec = VARIANTS[variant]
    inputs = {}
    for relative, expected in source["runtime_inputs"].items():
        path = project / relative
        if not path.resolve(strict=True).is_relative_to(project):
            raise ValueError(f"Input escapes source project: {relative}")
        data = path.read_bytes()
        actual = sha(data)
        if actual != expected["sha256"]:
            raise ValueError(f"Pinned source mismatch: {relative}")
        inputs[relative] = {"sha256": actual, "bytes": len(data)}
    edits = []
    if variant_spec:
        relative, before, after = variant_spec
        original = (project / relative).read_bytes()
        old, new = before.encode(), after.encode()
        if original.count(old) != 1:
            raise ValueError(f"Expected exactly one source property in {relative}")
        candidate = original.replace(old, new, 1)
        edits.append({"path": relative, "source_sha256": sha(original),
                      "candidate_sha256": sha(candidate), "bytes": len(candidate),
                      "old": before.rstrip("\n"), "new": after.rstrip("\n")})
    output.mkdir(parents=True, exist_ok=False)
    (output / "overlay").mkdir()
    if variant_spec:
        target = output / "overlay" / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(candidate)
        patch = difflib.unified_diff(original.decode().splitlines(True),
                                     candidate.decode().splitlines(True),
                                     fromfile="a/" + relative, tofile="b/" + relative)
        (output / "candidate.patch").write_text("".join(patch))
    receipt = {
        "schema": 1, "task": "R2-01", "variant": variant,
        "disposition": "unreviewed diagnostic; no runtime promotion",
        "source_commit_pin": source["source_commit_pin"],
        "project": str(project), "generator_sha256": sha(Path(__file__).read_bytes()),
        "source_manifest_sha256": sha((HERE / "source-manifest.json").read_bytes()),
        "material_profile_sha256": sha((HERE / "material-profile.json").read_bytes()),
        "inputs": inputs, "edits": edits, "material_profile": profile,
        "changed_variable_count": len(edits), "new_maps": 0,
        "source_geometry_and_maps_changed": False,
        "next_step": "Capture owner applies overlay only to a frozen scratch project, imports serially, then captures paired original framebuffers.",
    }
    (output / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "source-notice.md").write_bytes((HERE / "NOTICE.md").read_bytes())
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    args = parser.parse_args()
    result = stage(args.project, args.output, args.variant)
    print(json.dumps({"variant": result["variant"], "edits": result["edits"],
                      "new_maps": 0, "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
