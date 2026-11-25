"""Render a low-resolution, 20 fps Cycles review from the real Blender timeline."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--output", type=Path, default=HERE / "hanuman-motion-review.mp4")
    parser.add_argument("--oidn", type=Path, help="Optional Open Image Denoise CLI")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    timeline = json.loads((HERE / "timeline.json").read_text())
    bpy.ops.wm.open_mainfile(filepath=str((HERE / "hanuman-layered-abilities.blend").resolve()), load_ui=False)
    scene = bpy.context.scene
    if scene.render.fps != 40:
        raise RuntimeError("Expected a 40 fps source timeline")
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 1
    scene.render.resolution_x = args.width
    scene.render.resolution_y = round(args.width * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = "PNG"
    frames = list(range(scene.frame_start, scene.frame_end + 1, 2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="yuga-hanuman-motion-") as temp:
        folder = Path(temp)
        for number, frame in enumerate(frames):
            scene.frame_set(frame)
            scene.render.filepath = str(folder / f"frame-{number:04}.png")
            bpy.ops.render.render(write_still=True)
            print(f"frame {number + 1}/{len(frames)}  source {frame}", flush=True)
        pattern = "frame-%04d.png"
        if args.oidn:
            files = sorted(folder.glob("frame-*.png"))
            subprocess.run([
                "python3", str(NATIVE / "tools/hanuman-art/denoise.py"),
                "--oidn", str(args.oidn.resolve()), *(str(p) for p in files)
            ], check=True)
            pattern = "frame-%04d-denoised.png"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-framerate", "20", "-i", str(folder / pattern),
            "-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(args.output.resolve())
        ], check=True)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
        "-of", "json", str(args.output.resolve())
    ]))
    stream = probe["streams"][0]
    if int(stream["nb_read_frames"]) != len(frames) or stream["r_frame_rate"] != "20/1":
        raise RuntimeError("Encoded clip timing differs from rendered samples")
    result = {
        "source_scene_sha256": sha(HERE / "hanuman-layered-abilities.blend"),
        "timeline_sha256": sha(HERE / "timeline.json"),
        "file_sha256": sha(args.output),
        "fps": 20, "source_fps": timeline["fps"],
        "source_frames": frames, "frame_count": len(frames),
        "size": [stream["width"], stream["height"]], "samples_per_frame": args.samples,
        "renderer": "Blender Cycles CPU",
        "denoiser": "Open Image Denoise, sRGB LDR" if args.oidn else None,
        "scope": "Low-resolution motion review; no sound, runtime capture or hardware performance claim."
    }
    (HERE / "evidence/film.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Saved {args.output} with {len(frames)} frames at 20 fps", flush=True)


if __name__ == "__main__":
    main()
