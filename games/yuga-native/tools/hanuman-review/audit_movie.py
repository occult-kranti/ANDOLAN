#!/usr/bin/env python3
"""Pair a Blender or native PNG sequence with its encoded video."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics
import struct
import subprocess

from audit_glb import require


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_video(path):
    command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_frames",
               "-show_entries", "stream=codec_name,width,height,avg_frame_rate,time_base,duration,nb_frames:frame=best_effort_timestamp",
               "-of", "json", str(path)]
    return json.loads(subprocess.check_output(command, timeout=35))


def luminance_decode(input_args, expected):
    size = (96, 72)
    command = ["ffmpeg", "-v", "error", "-threads", "1", "-filter_threads", "1", *input_args,
               "-map", "0:v:0", "-vf", "scale=96:72:flags=area,format=gray", "-fps_mode", "passthrough",
               "-frames:v", str(expected + 1), "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"]
    raw = subprocess.check_output(command, timeout=35)
    rows = size[0] * size[1]
    require(len(raw) == rows * expected, "decoded frame count disagrees with manifest")
    return [raw[i : i + rows] for i in range(0, len(raw), rows)]


def native_plan(receipt, project):
    sources = {}
    for uri, expected in receipt["source_sha256"].items():
        require(uri.startswith("res://"), "invalid resource source pin")
        path = (project / uri.removeprefix("res://")).resolve()
        require(path.is_relative_to(project), "resource source pin escapes project")
        observed = digest(path)
        require(observed == expected, f"source asset mismatch for {uri}")
        sources[uri] = observed
    plan_uri = "res://tools/hanuman-capture/native-storyboard.json"
    require(plan_uri in sources, "native storyboard was not pinned")
    plan = json.loads((project / plan_uri.removeprefix("res://")).read_text())
    require(plan["frame_count"] == len(receipt["frames"]) and plan["size"] == receipt["size"] and plan["fps"] == receipt["fps"], "native plan metadata mismatch")
    slots = {"fire": "strike", "pulse": "guard", "dash": "vault", "guardian_circle": "sweep", "ultimate": "mountain"}
    sections = [("approach", 0)] + [(slots[step["action"]], step["frame"]) for step in plan["steps"] if step.get("action") in slots]
    ends = [start for _, start in sections[1:]] + [plan["frame_count"]]
    shots = [{"id": name, "clip": "native trial", "first_frame": start, "frame_count": end - start}
             for (name, start), end in zip(sections, ends, strict=True)]
    timeline = [row["physics_frame"] for row in receipt["frames"]]
    require(all(2 <= b-a <= 5 for a, b in zip(timeline, timeline[1:])), "native physics timeline stalled or skipped")
    impacts = [event["ability_id"] for event in receipt["events"] if event["kind"] == "impact"]
    require(impacts == ["vajra_gada", "vajra_kavacha", "maruti_udayana", "lanka_dahan", "mountain_pulse"], "native effect order missing or duplicates impact")
    return shots, sources, impacts


def audit(directory, video, source_paths, native_project=None):
    receipt_path = directory / "render.json"
    receipt = json.loads(receipt_path.read_text())
    require(receipt.get("complete") is True and not receipt.get("midpoints_only", False), "requires the complete real frame sequence")
    fps = receipt["fps"]
    size = tuple(receipt["size"])
    require(type(fps) is int and 1 <= fps <= 120 and all(32 <= x <= 4096 for x in size), "unsupported resolution or sample rate")
    frame_rows = receipt["frames"]
    impacts = []
    if native_project:
        shots, sources, impacts = native_plan(receipt, native_project)
    else:
        sources = {}
        for key, path in source_paths.items():
            observed = digest(path)
            require(receipt[key] == observed, f"source mismatch for {key}")
            sources[key] = {"name": path.name, "sha256": observed}
        shots = receipt["shots"]
    expected = sum(shot["frame_count"] for shot in shots)
    require(2 <= expected <= 1024 and len(frame_rows) == expected, "missing or excessive source frames")
    all_files = sorted(directory.glob("frame-*.png"))
    require(len(all_files) == expected, "unexpected source file census")
    metrics = []
    next_frame = 0
    for shot in shots:
        require(shot["frame_count"] > 1 and shot["first_frame"] == next_frame, "shot timing has a gap or overlap")
        end = next_frame + shot["frame_count"]
        clip_frames = []
        for index in range(next_frame, end):
            row = frame_rows[index]
            name = f"frame-{index:05}.png"
            require(row["frame"] == index and row["file"] == name, "frame identity drift")
            path = directory / name
            with path.open("rb") as stream:
                header = stream.read(24)
            require(header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack_from(">II", header, 16) == size, "PNG resolution mismatch")
            require(digest(path) == row["sha256"], "PNG contents disagree with render receipt")
            if not native_project:
                require(row["shot"] == shot["id"], "scene frames moved between shots")
                clip_frames.append(row["clip_frame"])
        if not native_project:
            require(all(a < b for a, b in zip(clip_frames, clip_frames[1:])), "source take timeline does not advance")
            require(clip_frames[0] == shot["source_range"][0] and abs(clip_frames[-1] - shot["source_range"][1]) < .000001, "source take endpoints missing")
        metrics.append({"id": shot["id"], "clip": shot["clip"], "first_frame": next_frame, "frame_count": shot["frame_count"]})
        next_frame = end

    probe = probe_video(video)
    stream = probe["streams"][0]
    pts = [int(frame["best_effort_timestamp"]) for frame in probe["frames"]]
    require(len(pts) == expected and (stream["width"], stream["height"]) == size, "video resolution/count mismatch")
    require(Fraction(stream["avg_frame_rate"]) == fps, "encoded frame rate disagrees with receipt")
    time_base = Fraction(stream["time_base"])
    require(pts[0] == 0 and all(abs(Fraction(frame, fps) - timestamp * time_base) <= time_base for frame, timestamp in enumerate(pts)), "missing or mis-timed video frame")
    duration = Fraction(stream["duration"])
    require(abs(duration - Fraction(expected, fps)) <= time_base, "encoded duration mismatch")
    originals = luminance_decode(["-framerate", str(fps), "-i", str(directory / "frame-%05d.png")], expected)
    encoded = luminance_decode(["-i", str(video)], expected)
    errors = [sum(abs(a-b) for a, b in zip(src, enc, strict=True)) / len(src) for src, enc in zip(originals, encoded, strict=True)]
    require(max(errors) < 6.0, "video frames are perceptually inconsistent with source PNGs")
    for shot in metrics:
        first = shot["first_frame"]
        section = encoded[first : first + shot["frame_count"]]
        changes = [sum(abs(a-b) >= 8 for a, b in zip(p, q, strict=True)) / len(p) for p, q in zip(section, section[1:])]
        distinct = len(set(section))
        require(distinct >= max(2, (len(section) + 1) // 2) and max(changes) > .005, f"frozen or uniform shot {shot['id']}")
        shot["distinct_luminance_frames"] = distinct
        shot["adjacent_changed_fraction_median"] = statistics.median(changes)
        shot["adjacent_changed_fraction_max"] = max(changes)
    return {
        "receipt_sha256": digest(receipt_path), "video_sha256": digest(video), "source_pins": sources,
        "codec": stream["codec_name"], "size": size, "fps": fps, "frames": expected, "duration_s": float(duration),
        "max_frame_mean_luminance_difference": max(errors), "shots": metrics, "native_impacts": impacts,
        "scope": "Source PNG alignment, timing and image variation. Visual continuity, animation quality and authoring source require separate inspection.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("video", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--project", type=Path, help="Validate a native reel against this project root")
    for key in ("blend", "storyboard", "profile", "script"):
        parser.add_argument(f"--{key}", type=Path)
    args = parser.parse_args()
    sources = {f"{key}_sha256": getattr(args, key) for key in ("blend", "storyboard", "profile", "script")}
    if not args.project and not all(sources.values()):
        parser.error("Studio reel requires --blend, --storyboard, --profile and --script")
    if args.project and any(sources.values()):
        parser.error("Native reel source pins come from --project and its receipt")
    answer = audit(args.directory, args.video, sources, args.project.resolve() if args.project else None)
    with args.report.open("x") as stream:
        json.dump(answer, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: answer[k] for k in ("video_sha256", "fps", "frames", "duration_s", "max_frame_mean_luminance_difference")}))


if __name__ == "__main__":
    main()
