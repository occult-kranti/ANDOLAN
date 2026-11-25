"""Render the seven Hanuman review views from one packed scene and record their provenance."""

from __future__ import annotations

import argparse
from hashlib import file_digest, sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont, ImageOps


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[3]
ART = ROOT / "games" / "yuga-native" / "art" / "hanuman"
DETAIL_RENDERER = TOOLS / "render_detail.py"
DENOISER = TOOLS.parent / "hanuman-art" / "denoise.py"
DEFAULT_PREVIOUS = "6b505f0414827732f58456778162b515797afbeb"
DETAIL_SAMPLES = 28
KEYFRAME = "hanuman-keyframe.png"
FILTERED_KEYFRAME = "hanuman-keyframe-denoised.png"
VIEWS = {
    "face": "hanuman-face-detail.png",
    "grip": "hanuman-grip-detail.png",
    "feet": "hanuman-feet-detail.png",
    "torso": "hanuman-torso.png",
    "belt_hand": "hanuman-belt-hand.png",
    "tail": "hanuman-tail.png",
    "alternate": "hanuman-alternate.png",
}


def digest(path):
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def checked_run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} exited with status {result.returncode}\n{result.stdout[-3500:]}")


def image_record(path, relative_to):
    with Image.open(path) as image:
        size = list(image.size)
    return {"file": path.relative_to(relative_to).as_posix(), "size_px": size, "sha256": digest(path)}


def compared_image_record(data):
    with Image.open(BytesIO(data)) as image:
        size = list(image.size)
    return {"size_px": size, "sha256": sha256(data).hexdigest()}


def comparison_sheet(output, panels):
    """Join the full frames on equal mattes without cropping any source frame."""
    panels = tuple(panels)
    panel_width, panel_height, caption_height, gutter = 560, 420, 48, 8
    sheet = Image.new("RGB", ((panel_width + gutter) * len(panels) - gutter, panel_height + caption_height), "#14171d")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    for index, (label, data) in enumerate(panels):
        left = index * (panel_width + gutter)
        with Image.open(BytesIO(data)) as source:
            panel = ImageOps.contain(source.convert("RGB"), (panel_width, panel_height), Image.Resampling.LANCZOS)
        sheet.paste(panel, (left + (panel_width - panel.width) // 2, caption_height + (panel_height - panel.height) // 2))
        draw.text((left + panel_width // 2, caption_height // 2), label, fill="#edf0f4", font=font, anchor="mm")
    sheet.save(output, quality=95, subsampling=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_dir", type=Path, help="directory containing the packed blend, raw full PNG and build report")
    parser.add_argument("out", type=Path, help="new or empty output directory for the review images and manifest")
    parser.add_argument("--oidn", type=Path, required=True, help="path to the OIDN command-line executable")
    parser.add_argument("--threads", type=int, default=2, help="Blender worker limit, default 2")
    parser.add_argument("--previous-ref", default=DEFAULT_PREVIOUS, help="Git revision containing the earlier reviewed PNG")
    parser.add_argument("--profile", type=Path, default=TOOLS / "reference-profile.json", help="the exact profile used by the builder")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    build, out = args.build_dir.resolve(), args.out.resolve()
    if out == build or (out.exists() and (not out.is_dir() or any(out.iterdir()))):
        parser.error("OUT must be a new or empty directory separate from BUILD_DIR")
    oidn, profile = args.oidn.resolve(), args.profile.resolve()
    if not oidn.is_file() or shutil.which(str(oidn)) is None:
        parser.error("--oidn must name an executable file")
    blender = shutil.which("blender")
    if blender is None:
        parser.error("Blender is unavailable on PATH")

    scene, raw_keyframe, report = (build / name for name in ("hanuman-keyframe.blend", KEYFRAME, "build-report.json"))
    if not all(path.is_file() for path in (scene, raw_keyframe, report, profile)):
        parser.error("BUILD_DIR requires the packed .blend, original PNG and build-report.json, plus a readable profile")
    build_report = json.loads(report.read_text())
    profile_hash = digest(profile)
    if build_report.get("profile_sha256") != profile_hash:
        parser.error("--profile does not match the recorded build profile SHA-256")
    config = json.loads(profile.read_text())
    concept = ART / config["reference"]
    concept_data = concept.read_bytes()
    if build_report.get("reference_sha256") != sha256(concept_data).hexdigest():
        parser.error("the reference image does not match the build report SHA-256")
    with Image.open(raw_keyframe) as image:
        if list(image.size) != build_report.get("resolution"):
            parser.error("the original PNG dimensions do not match the build report")
    scene_hash = digest(scene)
    report_hash = digest(report)
    if build_report.get("scene_sha256", scene_hash) != scene_hash:
        parser.error("the packed scene does not match the build report SHA-256")

    previous_commit = git("rev-parse", "--verify", "--end-of-options", f"{args.previous_ref}^{{commit}}").decode().strip()
    previous_path = (ART / "match" / FILTERED_KEYFRAME).relative_to(ROOT).as_posix()
    previous_spec = f"{previous_commit}:{previous_path}"
    previous_blob = git("rev-parse", "--verify", previous_spec).decode().strip()
    previous_data = git("cat-file", "blob", previous_blob)
    concept_source = {"path": concept.relative_to(ROOT).as_posix(), **compared_image_record(concept_data)}
    previous_source = {"revision": previous_commit, "path": previous_path, "git_blob": previous_blob,
                       **compared_image_record(previous_data)}
    blender_version = subprocess.check_output([blender, "--version"], text=True).splitlines()[0]

    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f".{out.name}-", dir=out.parent) as work:
        stage = Path(work)
        originals = stage / "originals"
        originals.mkdir()
        shutil.copyfile(raw_keyframe, stage / KEYFRAME)
        for view, name in VIEWS.items():
            print(f"Rendering {view} at {DETAIL_SAMPLES} samples", flush=True)
            checked_run([blender, "--background", "--factory-startup", str(scene), "-t", str(args.threads),
                         "--python-exit-code", "1", "--python", str(DETAIL_RENDERER), "--", "--view", view,
                         "--samples", str(DETAIL_SAMPLES), "--profile", str(profile), "--output", str(originals / name)])

        print("Denoising the original keyframe and seven views", flush=True)
        checked_run([sys.executable, str(DENOISER), "--oidn", str(oidn), str(stage / KEYFRAME),
                     *(str(originals / name) for name in VIEWS.values())])
        views = {}
        review_config = config["review_views"]
        for view, name in VIEWS.items():
            raw = originals / name
            filtered = originals / f"{raw.stem}-denoised.png"
            filtered.rename(stage / name)
            settings = ({name: value for name, value in review_config.items() if name.startswith("alternate_")}
                        if view == "alternate" else {"region_left_top_right_bottom": review_config["regions"][view],
                                                     "crop_full_width_px": review_config["crop_full_width"]})
            views[view] = {"label": view.replace("_", " ").title(), "settings": settings,
                           "raw": image_record(raw, stage), "denoised": image_record(stage / name, stage)}

        labels = ["Generated concept", f"Previous render {previous_commit[:8]}", "Current render"]
        filtered_current = stage / FILTERED_KEYFRAME
        comparison = stage / "hanuman-comparison.jpg"
        comparison_sheet(comparison, zip(labels, (concept_data, previous_data, filtered_current.read_bytes())))
        if digest(scene) != scene_hash or digest(report) != report_hash or digest(profile) != profile_hash:
            raise RuntimeError("A build input changed while its review images were being generated")
        manifest = {
            "schema": 1,
            "scene": {"file": scene.name, "sha256": scene_hash, "build_report_sha256": report_hash,
                      "profile_sha256": profile_hash, "build_blender": build_report.get("blender")},
            "tools": {"blender": blender_version, "blender_threads": args.threads, "detail_samples": DETAIL_SAMPLES,
                      "detail_renderer_sha256": digest(DETAIL_RENDERER), "denoiser_sha256": digest(DENOISER),
                      "oidn_sha256": digest(oidn), "denoiser_color_input": "display-encoded sRGB"},
            "keyframe": {"label": "Hanuman temple court keyframe", "samples": build_report.get("samples"),
                         "raw": image_record(stage / KEYFRAME, stage), "denoised": image_record(filtered_current, stage)},
            "views": views,
            "comparison": {**image_record(comparison, stage), "labels_left_to_right": labels,
                           "concept": concept_source, "previous": previous_source, "current_file": filtered_current.name},
        }
        (stage / "review-manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
        stage.rename(out)
    print(out)


if __name__ == "__main__":
    main()
