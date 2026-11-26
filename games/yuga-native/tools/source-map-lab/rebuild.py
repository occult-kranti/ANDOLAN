"""Build both native map mounts and the two full glTFs from the registered Source 1 inputs."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


TOOLS = Path(__file__).resolve().parent
BSP_SHA256 = "b91be410539fbbfc16300423f1e19c024f12addf1429c8cb2f72b53fe0fd6bcc"
NAV_SHA256 = "82d46fb7d3618514e9897d87e5666c0c3f483c4a82060aac03313afad864b649"


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def install_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and source.samefile(target):
        return
    # A separate inode keeps the original and jade mounts independently editable.
    with tempfile.TemporaryDirectory(dir=target.parent) as staging:
        temporary = Path(staging) / target.name
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("bsp", "nav", "assets", "sourceio-parent", "work", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument(
        "--finisher",
        type=Path,
        help="Use an already compiled yuga-map-finish executable",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Also run independent native, texel, mesh and navigation checks",
    )
    parser.add_argument(
        "--go", default="go", help="Go compiler executable (1.20 or newer)"
    )
    args = parser.parse_args()
    version = subprocess.run([args.go, "version"], capture_output=True, text=True)
    if version.returncode or not version.stdout.startswith("go version go"):
        raise SystemExit(
            "Supply the Go compiler with --go or put its bin directory on PATH."
        )
    bsp, nav, out = args.bsp.resolve(), args.nav.resolve(), args.output.resolve()
    if sha256(bsp) != BSP_SHA256 or sha256(nav) != NAV_SHA256:
        raise SystemExit(
            "Expected the Valve depot 731 Dust II BSP and NAV identified in the source guide."
        )
    source_maps = out / "native/original/csgo/maps"
    edited_maps = out / "native/jade/csgo/maps"
    if any(p.parent == edited_maps for p in (bsp, nav)):
        raise SystemExit("Choose an output separate from the source mount.")
    models, evidence = out / "models", out / "evidence"
    scene, overlay = args.work.resolve() / "scene", args.work.resolve() / "overlay"
    for path in (source_maps, edited_maps, models, evidence, scene, overlay):
        path.mkdir(parents=True, exist_ok=True)
    native = edited_maps / "de_dust2.bsp"
    base_model, jade_model = models / "dust2-baseline.glb", models / "dust2-jade.glb"
    nav_csv = evidence / "official-nav.csv"
    with nav_csv.open("w") as csv:
        subprocess.run(
            [args.go, "run", ".", nav, bsp], cwd=TOOLS / "nav", stdout=csv, check=True
        )
    subprocess.run(
        [
            sys.executable,
            TOOLS / "importer/build_scene.py",
            bsp,
            nav_csv,
            scene,
            "--sourceio-parent",
            args.sourceio_parent.resolve(),
            "--assets",
            args.assets.resolve(),
        ],
        check=True,
    )
    floor = scene / "floor-faces.json"
    subprocess.run(
        [
            sys.executable,
            TOOLS / "materials/bake.py",
            bsp,
            args.assets.resolve(),
            floor,
            overlay,
        ],
        check=True,
    )
    if args.finisher:
        finisher = args.finisher.resolve()
    else:
        target = args.work.resolve() / "cargo"
        subprocess.run(
            [
                "cargo",
                "build",
                "--locked",
                "--release",
                "--manifest-path",
                TOOLS / "rust/Cargo.toml",
                "--target-dir",
                target,
            ],
            check=True,
        )
        finisher = target / "release/yuga-map-finish"
    install_file(bsp, source_maps / "de_dust2.bsp")
    install_file(nav, source_maps / "de_dust2.nav")
    install_file(scene / base_model.name, base_model)
    subprocess.run(
        [finisher, "bsp", bsp, BSP_SHA256, floor, overlay, native], check=True
    )
    subprocess.run(
        [finisher, "nav", nav, bsp, native, edited_maps / "de_dust2.nav"], check=True
    )
    subprocess.run([finisher, "glb", base_model, jade_model], check=True)
    for item in (
        floor,
        scene / "floor-support.json",
        scene / "objectives.json",
        scene / "source-entities.json",
        scene / "import-report.json",
        overlay / "bake.json",
    ):
        install_file(item, evidence / item.name)
    if args.verify:
        for name, params, report in [
            ("native.py", ["compare", bsp, native, "--face-ids", floor], "native-diff"),
            (
                "textures.py",
                [bsp, native, args.assets.resolve(), overlay / "bake.json"],
                "texel-diff",
            ),
            (
                "scene.py",
                [base_model, jade_model, "--bsp", bsp, "--face-ids", floor],
                "scene-diff",
            ),
            ("nav.py", [jade_model, nav_csv, "--bsp", bsp], "nav-support"),
        ]:
            subprocess.run(
                [
                    sys.executable,
                    TOOLS / "qa" / name,
                    *params,
                    "--output",
                    evidence / (report + ".json"),
                ],
                check=True,
            )
    print(
        f"Native maps: {out / 'native'}\nBlender-ready models: {models}\nEvidence: {evidence}"
    )


if __name__ == "__main__":
    main()
