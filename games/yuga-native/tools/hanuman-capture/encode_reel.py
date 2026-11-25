#!/usr/bin/env python3
"""Verify consecutive original frames and encode a downloadable MP4."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--name", default="hanuman-motion")
    args = parser.parse_args()
    directory = args.frames.resolve()
    source = directory / "render.json"
    report = json.loads(source.read_text())
    frames = report["frames"]
    if not report.get("complete") or report.get("midpoints_only") or len(frames) < 2:
        raise ValueError("A completed continuous render sequence is required")
    fps = report["fps"]
    if not 8 <= fps <= 60 or any(
        frame["frame"] != i or frame["file"] != f"frame-{i:05}.png"
        or digest(directory / frame["file"]) != frame["sha256"]
        for i, frame in enumerate(frames)
    ):
        raise ValueError("A source frame is omitted, reordered or altered")
    distinct = len({frame["sha256"] for frame in frames})
    if distinct < len(frames) * 0.75:
        raise ValueError("The sequence contains too few distinct frames")
    if not args.name or not all(ch.isascii() and (ch.isalnum() or ch in "-_") for ch in args.name):
        parser.error("Use an alphanumeric output name")
    target = directory / (args.name + ".mp4")
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n", "-framerate", str(fps),
        "-i", str(directory / "frame-%05d.png"), "-frames:v", str(len(frames)), "-threads", "2",
    ]
    if report["scope"].startswith("Blender software"):
        command += ["-vf", "hqdn3d=1.4:1.2:1.0:0.8", "-filter_threads", "1"]
    command += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
    ]
    subprocess.run(command, check=True, timeout=90)
    metadata = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,nb_read_frames,avg_frame_rate,duration",
        "-of", "json", str(target),
    ], text=True))["streams"][0]
    if (metadata["codec_name"] != "h264" or int(metadata["nb_read_frames"]) != len(frames)
            or metadata["avg_frame_rate"] != f"{fps}/1"
            or [metadata["width"], metadata["height"]] != report["size"]
            or abs(float(metadata["duration"]) - len(frames) / fps) > .01):
        raise ValueError("Decoded video does not match the original sequence")
    output = {
        "complete": True, "scope": report["scope"], "frame_count": len(frames), "distinct_source_frames": distinct,
        "render_receipt_sha256": digest(source), "video_sha256": digest(target), "video_bytes": target.stat().st_size,
        "metadata": metadata, "encode_command": command,
    }
    (directory / (args.name + ".json")).write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
