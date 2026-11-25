"""Review the shipped Hanuman studio edit, registered views and per-frame body framing."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def require(test, message):
    if not test:
        raise ValueError(message)


def presentation():
    # The render team's existing check covers fixed cameras, per-image source digests
    # and RGB movement. The second pass here tests actual full-resolution frame
    # uniqueness, articulated relative distances, and the wide shot's framing.
    artist_check = subprocess.check_output(["python3", str(ROOT / "render/verify.py")], text=True)
    result = {"render_check": json.loads(artist_check)}
    source = ROOT / "models/hanuman-enhanced.glb"
    source_hash = sha(source)
    video = MEDIA / "video/hanuman-showcase.mp4"
    meta = load(video.with_suffix(".json"))
    require(
        meta["source_sha256"] == source_hash and meta["media_sha256"] == sha(video), "Showcase provenance"
    )
    framemd5 = subprocess.check_output(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-threads",
            "1",
            "-i",
            str(video),
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "rawvideo",
            "-threads",
            "1",
            "-f",
            "framemd5",
            "pipe:1",
        ],
        text=True,
    )
    frames = [
        line.rsplit(",", 1)[1].strip() for line in framemd5.splitlines() if line and not line.startswith("#")
    ]
    require(
        len(frames) == meta["total_frames"] and len(set(frames)) == len(frames),
        "Duplicate or absent decoded studio frame",
    )
    result.update(
        source_sha256=source_hash,
        source_vertices=88445,
        distinct_full_resolution_frames=len(set(frames)),
        frame_hash_log_sha256=hashlib.sha256(framemd5.encode()).hexdigest(),
    )
    distances = []
    for shot in meta["shots"]:
        poses = shot["samples"]
        # Compare registered joints to one another. A moving camera or rigid-body
        # transform alone cannot change these distances.
        sampled = []
        for pose in poses:
            points = np.array(list(pose["joint_centers_m"].values()), dtype=float)
            sampled.append(np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2))
        delta = np.ptp(sampled, axis=0).max()
        require(delta > 0.0003, "No measurable relative movement in shot " + shot["action"])
        distances.append(
            dict(
                action=shot["action"], frames=shot["frames"], max_pair_distance_delta_m=round(float(delta), 6)
            )
        )
    result["shots"] = distances
    # Quantify how much of the actual 8-bit close-up hits the display endpoints.
    # This is an exposure measurement only; silhouette and material readability
    # are also inspected on the true final plates.
    beauty = MEDIA / "images/hanuman-beauty.webp"
    with Image.open(beauty) as im:
        rgb = np.asarray(im.convert("RGB"))
    result["beauty_exposure"] = {
        "all_rgb_at_255_fraction": round(float((rgb.min(axis=2) == 255).mean()), 7),
        "all_rgb_at_0_fraction": round(float((rgb.max(axis=2) == 0).mean()), 7),
        "color_bins_4bit": int(len(np.unique((rgb >> 4).reshape(-1, 3), axis=0))),
    }
    # The wide shot has a different purpose than the portrait and tail close-up.
    # Each checks the entire deformed mesh, including the weapon and terminal brush.
    framing = load(MEDIA / "video/hanuman-framing.json")
    require(framing["source_sha256"] == source_hash, "Wrong source in camera bounds")
    bounds = np.array([f["bounds"] for f in framing["frames"]])
    require(
        np.all((bounds > 0) & (bounds < 1)) and np.all(bounds[:, :2] < bounds[:, 2:]),
        "Wide body framing escaped viewport",
    )
    count = distances[1]["frames"]
    require(
        framing["evaluated_vertices"] == 88445 and framing["rig_joints"] == 167 and len(bounds) == count,
        "Incomplete framing evidence",
    )
    start = distances[0]["frames"]
    require(
        [f["movie_frame"] for f in framing["frames"]] == list(range(start, start + count)),
        "Missing or duplicate wide-frame bounds",
    )
    extrema = np.concatenate([bounds[:, :2].min(axis=0), bounds[:, 2:].max(axis=0)])
    require(
        np.allclose(extrema, framing["all_frame_bounds"], atol=2e-7),
        "Combined bounds diverge from individual frames",
    )
    result["wide_shot_model_bounds"] = {
        "evaluated_frames": len(bounds),
        "evaluated_vertices": framing["evaluated_vertices"],
        "normalized_bounds": extrema.tolist(),
        "minimum_top_clearance_pixels": round(float((1 - extrema[3]) * framing["size"][1]), 2),
        "minimum_bottom_clearance_pixels": round(float(extrema[1] * framing["size"][1]), 2),
    }
    result["framing_sha256"] = sha(MEDIA / "video/hanuman-framing.json")
    result["test_sha256"] = sha(Path(__file__))
    result["passed"] = True
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/review-presentation.json")
    args = parser.parse_args()
    args.output.write_text(json.dumps(presentation(), indent=2) + "\n")
    print(args.output)
