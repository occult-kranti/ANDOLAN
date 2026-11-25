"""Check model provenance, matched cameras and the delivered studio film via FFmpeg.

Run with Python 3, Pillow and NumPy. Prints a compact file-specific receipt.
"""

import argparse
import hashlib
import json
import subprocess
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import numpy as np
from PIL import Image

PACK = Path(__file__).resolve().parents[1]
BASELINE = PACK.parent / "four-hero-motion/models/hanuman.glb"
ENHANCED = PACK / "models/hanuman-enhanced.glb"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def record(path):
    report = json.loads(path.with_suffix(".json").read_text())
    if report["media_sha256"] != digest(path):
        raise ValueError(f"{path.name} changed after its shot record was written")
    return report


def check(condition, message):
    if not condition:
        raise ValueError(message)


def image_size(path, note):
    with Image.open(path) as image:
        image.load()
        check(list(image.size) == note["size"] and image.format == "WEBP", f"{path.name} size/format")
        return np.asarray(image.convert("RGB"))


def stills(media, original, enhanced):
    beauty = media / "images/hanuman-beauty.webp"
    note = record(beauty)
    check(note["source_sha256"] == enhanced and note["action"] == "idle", "Beauty provenance")
    image_size(beauty, note)
    sheet = media / "images/matched-studies.webp"
    studies = record(sheet)
    image = image_size(sheet, studies)
    old, new = studies["models"]
    check([old["sha256"], new["sha256"]] == [original, enhanced], "Matched model sources")
    check([x["study"] for x in old["shots"]] == ["face", "front", "rear", "tail"], "Matched study order")
    changes = {}
    for i, (a, b) in enumerate(zip(old["shots"], new["shots"], strict=True)):
        for field in ("action", "phase", "frame_in_source", "camera_to_world", "width_m", "study"):
            check(a[field] == b[field], f'Unmatched {a["study"]} camera/pose field {field}')
        for joint in ("head", "wrist.R", "wrist.L", "foot.R", "foot.L"):
            check(
                np.allclose(a["joint_centers_m"][joint], b["joint_centers_m"][joint], atol=0.00001),
                f'{a["study"]} body registration drifted at {joint}',
            )
        left = 22 + i * (480 + 8)
        top = image[69 : 69 + 622, left : left + 480].astype(np.int16)
        bottom = image[69 + 664 : 69 + 664 + 622, left : left + 480].astype(np.int16)
        delta = float(np.abs(top - bottom).mean())
        check(delta > 0.6, f'{a["study"]} visible geometry or surface change too small')
        changes[a["study"]] = round(delta, 3)
    return dict(
        beauty_sha256=note["media_sha256"],
        matched_sha256=studies["media_sha256"],
        mean_rgb_change_by_matched_view=changes,
    )


def film(media, enhanced):
    movie = media / "video/hanuman-showcase.mp4"
    note = record(movie)
    check(note["source_sha256"] == enhanced, "Showcase source digest")
    probe = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,avg_frame_rate,nb_frames",
            "-of",
            "json",
            str(movie),
        ],
        text=True,
    )
    (stream,) = json.loads(probe)["streams"]
    check(
        stream["codec_name"] == "h264" and [stream["width"], stream["height"]] == note["size"],
        "Video codec/size",
    )
    check(Fraction(stream["avg_frame_rate"]) == note["fps"], "Video frame rate")
    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-threads",
            "1",
            "-i",
            str(movie),
            "-vf",
            "scale=192:108:flags=area",
            "-threads",
            "1",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "pipe:1",
        ]
    )
    decoded = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 108, 192, 3).astype(np.int16)
    counts = [s["frames"] for s in note["shots"]]
    check(sum(counts) == note["total_frames"] == int(stream["nb_frames"]) == len(decoded), "Decoded frames")
    check(
        [s["action"] for s in note["shots"]] == ["idle", "mountain_pulse", "mountain_pulse"],
        "Showcase action sequence",
    )
    framing = json.loads((media / "video/hanuman-framing.json").read_text())
    check(framing["source_sha256"] == enhanced and framing["size"] == note["size"], "Framing provenance")
    frames = framing["frames"]
    wide = note["shots"][1]
    check(
        [f["movie_frame"] for f in frames] == list(range(counts[0], counts[0] + counts[1])),
        "Framing intervals",
    )
    bounds = np.asarray([f["bounds"] for f in frames])
    check(np.isfinite(bounds).all() and bounds.min() >= 0 and bounds.max() <= 1, "Clipped full-body shot")
    check((bounds[:, 2:] > bounds[:, :2]).all(), "Empty geometry bounds")
    for pose in wide["samples"]:
        sample = frames[pose["movie_frame"] - counts[0]]
        check(
            abs(pose["phase"] - sample["source_phase"]) <= 0.000001,
            "Full-body framing and movie pose clocks differ",
        )
    at = 0
    changes = []
    background_change = []
    for shot in note["shots"]:
        end = at + shot["frames"]
        poses = shot["samples"]
        check(poses[0]["movie_frame"] == at and poses[-1]["movie_frame"] == end - 1, "Pose intervals")
        check(all(a["phase"] < b["phase"] for a, b in pairwise(poses)), "Pose clock")
        check(
            max(
                np.linalg.norm(
                    np.subtract(p["joint_centers_m"]["tail_04"], poses[0]["joint_centers_m"]["tail_04"])
                )
                for p in poses
            )
            > 0.001,
            "Unarticulated tail",
        )
        region = decoded[at:end, 12:96, 30:165]
        movement = np.abs(np.diff(region, axis=0)).mean((1, 2, 3))
        check(np.quantile(movement, 0.75) > 0.45, "Frame sequence appears frozen")
        changes.append(round(float(np.quantile(movement, 0.75)), 3))
        sky = decoded[at:end, :10, -20:]
        background_change.append(round(float(np.abs(np.diff(sky, axis=0)).mean()), 3))
        at = end
    return dict(
        movie_sha256=note["media_sha256"],
        decoded_frames=len(decoded),
        fps=note["fps"],
        upper_quartile_frame_rgb_change_by_shot=changes,
        mean_upper_right_background_rgb_change_by_shot=background_change,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, default=PACK / "media")
    parser.add_argument("--stills-only", action="store_true")
    args = parser.parse_args()
    enhanced = digest(ENHANCED)
    result = stills(args.media, digest(BASELINE), enhanced)
    if not args.stills_only:
        result.update(film(args.media, enhanced))
    print(json.dumps(result, indent=2))
