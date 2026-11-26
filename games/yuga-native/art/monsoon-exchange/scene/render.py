"""Render the cameras stored in the native scene. Photographs use CPU Cycles."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import shutil
from tempfile import TemporaryDirectory
from PIL import Image, ImageStat
import bpy
import _cycles

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "mandala-map-studio/src"))
from light_study import filtered_hdr

SIZES = {
    "overview": (1500, 1110),
    "sun-court": (1280, 800),
    "indigo-cistern": (1280, 800),
    "weavers-gate": (1280, 800),
    "north-up": (1180, 1260),
}


def render(args):
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.blend.resolve()
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    sc = bpy.context.scene
    sc.cycles.samples = args.samples
    sc.cycles.use_denoising = bool(_cycles.with_openimagedenoise)
    sc.render.threads_mode = "FIXED"
    sc.render.threads = args.threads
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.10 if args.samples < 10 else 0.045
    if not args.preview:
        sc.cycles.use_light_tree = True
    records = {}
    with TemporaryDirectory() as temp:
        for shot in args.shots:
            marker = sc.timeline_markers[shot]
            sc.frame_set(marker.frame)
            sc.camera = marker.camera
            width, height = SIZES[shot]
            sc.render.resolution_x = width
            sc.render.resolution_y = height
            sc.render.resolution_percentage = 50 if args.preview else 100
            sc.render.image_settings.file_format = "PNG"
            sc.render.image_settings.color_mode = "RGB"
            sc.render.filepath = str(Path(temp) / (shot + ".png"))
            print("EXCHANGE RENDER START " + shot, flush=True)
            image_path = Path(sc.render.filepath)
            if not sc.cycles.use_denoising and args.denoiser:
                filtered_hdr(sc, image_path, args.denoiser)
            else:
                bpy.ops.render.render(write_still=True)
            output = args.output / (shot + ".webp")
            im = Image.open(image_path).convert("RGB")
            im.save(output, "WEBP", quality=91, method=6)
            stat = ImageStat.Stat(im.convert("L"))
            records[shot] = {
                "file": output.name,
                "size": list(im.size),
                "bytes": output.stat().st_size,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "luma_mean": round(stat.mean[0], 2),
                "luma_sd": round(stat.stddev[0], 2),
            }
            print("EXCHANGE RENDERED", shot, records[shot], flush=True)
    if not args.preview:
        register = args.output / "render-register.json"
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
            raise RuntimeError(
                "The source was replaced while its cameras were rendering."
            )
        previous = json.loads(register.read_text()) if register.exists() else {}
        combined = (
            dict(previous.get("shots", {}))
            if previous.get("source_sha256") == source_hash
            else {}
        )
        combined.update(records)
        register.write_text(
            json.dumps(
                {
                    "source": "../scene/monsoon-exchange.blend",
                    "source_sha256": source_hash,
                    "renderer": "Blender " + bpy.app.version_string + " Cycles CPU",
                    "samples_per_pixel_max": args.samples,
                    "denoised": bool(sc.cycles.use_denoising or args.denoiser),
                    "shots": combined,
                },
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--denoiser",
        default=shutil.which("oidnDenoise"),
        help="Optional Intel Open Image Denoise command on Blender builds without embedded OIDN",
    )
    cli.add_argument("--blend", default=HERE / "monsoon-exchange.blend", type=Path)
    cli.add_argument("--output", default=HERE.parent / "renders", type=Path)
    cli.add_argument("--shots", nargs="+", default=list(SIZES), choices=list(SIZES))
    cli.add_argument("--samples", type=int, default=14)
    cli.add_argument("--threads", type=int, default=3)
    cli.add_argument("--preview", action="store_true")
    args = cli.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    render(args)
