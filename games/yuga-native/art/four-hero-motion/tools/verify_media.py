#!/usr/bin/env python3
"""Decode the released art and films, and check fixed-camera pose evidence against each film."""

import argparse
import hashlib
import json
import re
import struct
import subprocess
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
HEROES = ("hanuman", "rama", "shiva", "krishna")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def describe(path):
    return {"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": digest(path)}


def model_record(path):
    raw = path.read_bytes()
    magic, version, length, json_size, tag = struct.unpack_from("<4s4I", raw)
    require(
        (magic, version, length, tag) == (b"glTF", 2, len(raw), 0x4E4F534A), f"{path.name}: malformed GLB"
    )
    doc = json.loads(raw[20 : 20 + json_size])
    binary_start = 28 + json_size
    require(len(doc.get("skins", [])) >= 1, f"{path.name}: missing skin")
    skins = [len(s["joints"]) for s in doc["skins"]]
    skinned = [
        p
        for m in doc["meshes"]
        for p in m["primitives"]
        if {"POSITION", "JOINTS_0", "WEIGHTS_0"} <= p["attributes"].keys()
    ]
    require(skinned and max(skins) > 4, f"{path.name}: missing weighted body")
    animated = {}
    for clip in doc["animations"]:
        moving = set()
        for channel in clip["channels"]:
            if channel["target"]["path"] not in ("rotation", "translation"):
                continue
            sample = clip["samplers"][channel["sampler"]]
            acc = doc["accessors"][sample["output"]]
            if acc["count"] < 2:
                continue
            require(
                acc["componentType"] == 5126 and acc["type"] in ("VEC3", "VEC4"),
                "unexpected skin animation accessor",
            )
            width = int(acc["type"][-1])
            view = doc["bufferViews"][acc["bufferView"]]
            data = np.ndarray(
                (acc["count"], width),
                "<f4",
                raw,
                offset=binary_start + view.get("byteOffset", 0) + acc.get("byteOffset", 0),
                strides=(view.get("byteStride", width * 4), 4),
            )
            require(np.isfinite(data).all(), "non-finite animation accessor")
            if np.ptp(data, axis=0).max() > 1e-4:
                moving.add(channel["target"]["node"])
        animated[clip["name"]] = len(moving)
    required = {"idle", "run", "jump", "fire", "defeat", "cast", "cast1", "cast2", "cast3"}
    require(
        required <= animated.keys() and all(animated[k] > 0 for k in required),
        f"{path.name}: missing/constant actions: {animated}",
    )
    require(
        all("bufferView" in i for i in doc.get("images", [])), f"{path.name}: unresolved texture dependency"
    )
    return {
        **describe(path),
        "skin_joint_counts": skins,
        "skinned_primitives": len(skinned),
        "embedded_images": len(doc.get("images", [])),
        "moving_nodes_by_clip": animated,
    }


def image_record(path, panels=False):
    with Image.open(path) as im:
        im.load()
        width, height = im.size
        thumb = np.asarray(im.convert("RGB").resize((192, 108)), dtype=np.int16)
        contrast = int(np.percentile(thumb, 95) - np.percentile(thumb, 5))
    require(
        min(width, height) >= 480 and contrast >= 25,
        f"{path.name}: dimensions/contrast {width}×{height}, {contrast}",
    )
    record = {**describe(path), "width": width, "height": height, "rgb_percentile_span": contrast}
    if panels:
        require(width > height, f"{path.name}: expected landscape three-beat sheet")
        cells = np.split(thumb, 3, axis=1)
        deltas = [float(np.abs(a - b).mean()) for a, b in combinations(cells, 2)]
        require(min(deltas) > 5, f"{path.name}: repeated or indistinct storyboard panels")
        record["three_panel_min_rgb_difference"] = round(min(deltas), 3)
    return record


def script_record(path, hero):
    text = path.read_text()
    words = len(text.split())
    links = re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text)
    local = [link.split("#")[0] for link in links if not re.match(r"https?://|#", link)]
    require(
        hero in text.lower() and words >= 40 and re.search(r"\bF\d+", text),
        f"{hero}: missing timed character instructions",
    )
    require(all((path.parent / link).is_file() for link in local), f"{hero}: broken local script reference")
    return {**describe(path), "words": words, "source_links": len(links), "resolved_local_links": len(local)}


def video_frames(path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    meta = json.loads(subprocess.check_output(command))["streams"][0]
    fps = float(Fraction(meta["avg_frame_rate"]))
    width, height = meta["width"], meta["height"]
    require(width > 0 and height > 0 and fps > 0, f"{path.name}: missing video dimensions or frame rate")
    command = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-xerror",
        "-threads",
        "1",
        "-i",
        str(path),
        "-an",
        "-vf",
        "scale=192:108:flags=area",
        "-threads",
        "1",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]
    decoded = subprocess.check_output(command)
    frames = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, 108, 192, 3)
    require(len(frames) >= 3 and len(frames) == int(meta["nb_frames"]), f"{path.name}: decoded frame count")
    require(
        min(width, height) >= 360 and len(frames) >= fps * 2,
        f"{path.name}: insufficient resolution or length",
    )
    # Center only. Border decoration, captions and title changes cannot carry these measurements.
    center = frames[:, 15:85, 38:154].astype(np.int16)
    return (
        {
            **describe(path),
            "width": width,
            "height": height,
            "fps": round(fps, 4),
            "frames": len(frames),
            "seconds": round(len(frames) / fps, 3),
            "codec": meta["codec_name"],
        },
        center,
    )


def visual_motion(frames):
    require(len(frames) >= 3, "A shot requires at least three decoded frames")
    variation = np.abs(np.diff(frames, axis=0)).max(axis=3)
    changed = (variation > 7).mean(axis=(1, 2))
    return {
        "max_changed_percent": round(100 * float(changed.max()), 3),
        "median_changed_percent": round(100 * float(np.median(changed)), 3),
        "transitions_over_quarter_percent": int(np.sum(changed >= 0.0025)),
    }


def pose_motion(poses):
    require(len(poses) >= 3, "A shot requires at least three recorded poses")
    cams = np.asarray([p["camera_world"] for p in poses], dtype=float)
    require(np.isfinite(cams).all(), "Camera matrix contains a non-finite value")
    names = sorted(set.intersection(*(set(p["bones"]) for p in poses)))
    require(len(names) >= 3, "At least three consistently tracked joints are needed")

    def position(bone):
        if isinstance(bone, dict):
            return bone.get("position", bone.get("location", bone.get("pos")))
        return bone[0] if isinstance(bone[0], (list, tuple)) else bone[:3]

    tracks = np.array([[position(p["bones"][j]) for j in names] for p in poses], dtype=float)
    require(
        tracks.shape == (len(poses), len(names), 3) and np.isfinite(tracks).all(),
        "Invalid world joint sample",
    )
    pairs = list(combinations(range(len(names)), 2))
    distances = np.stack([np.linalg.norm(tracks[:, i] - tracks[:, j], axis=1) for i, j in pairs], axis=1)
    changes = np.ptp(distances, axis=0)
    a, b = pairs[int(changes.argmax())]
    return {
        "samples": len(poses),
        "joints": len(names),
        "camera_matrix_span": round(float(np.ptp(cams, axis=0).max()), 8),
        "largest_joint_pair_span": round(float(changes.max()), 6),
        "joint_pair": [names[a], names[b]],
    }


def verify_hero(hero):
    art = ROOT / "media/art"
    concept = next((art / (hero + ext) for ext in (".webp", ".png") if (art / (hero + ext)).is_file()), None)
    require(concept is not None, f"{hero}: concept art missing")
    beats = next(
        (
            art / (hero + "-beats" + ext)
            for ext in (".webp", ".png")
            if (art / (hero + "-beats" + ext)).is_file()
        ),
        None,
    )
    require(beats is not None, f"{hero}: beat sheet missing")
    script = ROOT / "scripts" / (hero + ".md")
    movie = ROOT / "media/video" / (hero + ".mp4")
    trace = movie.with_suffix(".json")
    info, frames = video_frames(movie)
    stage = json.loads(trace.read_text())
    require(
        stage["hero"] == hero and stage["media_sha256"] == info["sha256"],
        f"{hero}: pose trace belongs to a different movie",
    )
    require(
        (stage["total_frames"], stage["width"], stage["height"], stage["fps"])
        == (info["frames"], info["width"], info["height"], info["fps"]),
        f"{hero}: trace disagrees with decoded stream",
    )
    require(
        stage["environment_sha256"] == digest(ROOT.parents[1] / "assets/environment/lanka_courtyard.glb"),
        f"{hero}: court source hash",
    )
    model = ROOT / "models" / (hero + ".glb")
    native_reports = ROOT.parents[1] / "docs/rust-rebuild"
    if hero == "hanuman":
        source_sha = json.loads((native_reports / "HERO-POSE-EVIDENCE.json").read_text())["build"][
            "export_sha256"
        ]
    elif hero == "rama":
        source_sha = json.loads((native_reports / "deep-search/RAMA-PORT-EVIDENCE.json").read_text())[
            "packs"
        ]["near"]["output_sha256"]
    else:
        source_sha = digest(model)
    require(stage["source_sha256"] == source_sha, f"{hero}: source model differs from tested animation rig")
    require(digest(model) == source_sha, f"{hero}: downloadable model differs from rendered model")
    shots = stage["shots"]
    plan = json.loads((ROOT / "tools/render/shots.json").read_text())["heroes"][hero]["shots"]
    require(
        [(s["clip"], s["label"], s["frames"]) for s in shots]
        == [(s["clip"], s["label"], s["frames"]) for s in plan],
        f"{hero}: rendered shot list diverges from production script",
    )
    require(len(shots) >= 2, f"{hero} requires a sequence of actions")
    evidence = []
    for shot in shots:
        start, end = shot["start_frame"], shot["end_frame"]
        require(start <= end and start >= 0, f"{hero}: invalid shot frame limits")
        first = start - shots[0]["start_frame"]
        last = end - shots[0]["start_frame"]
        require(first >= 0 and last < len(frames), f"{hero}: shot lies outside decoded movie")
        evidence.append(
            {
                "clip": shot["clip"],
                "start_frame": start,
                "end_frame": end,
                **visual_motion(frames[first : last + 1]),
                **pose_motion(shot["poses"]),
            }
        )
    require(
        shots[-1]["end_frame"] - shots[0]["start_frame"] + 1 == len(frames),
        f"{hero}: shot coverage vs decode",
    )
    require(
        all(b["start_frame"] == a["end_frame"] + 1 for a, b in zip(shots, shots[1:])),
        f"{hero}: shot gaps/overlap",
    )
    # A rigid whole-character translation or rotating camera preserves all inter-joint distances.
    fixed = [
        s
        for s in evidence
        if s["camera_matrix_span"] < 1e-5
        and s["largest_joint_pair_span"] > 0.001
        and s["transitions_over_quarter_percent"] >= 2
    ]
    require(fixed, f"{hero}: no fixed-camera shot shows both moving rendered pixels and articulated joints")
    result = {
        "hero": hero,
        "concept": image_record(concept),
        "storyboard": image_record(beats, panels=True),
        "script": script_record(script, hero),
        "blender_still": image_record(ROOT / "media/stills" / (hero + ".webp")),
        "renderer": stage["renderer"],
        "source_sha256": source_sha,
        "joint_count": stage["joint_count"],
        "video": info,
        "pose_trace": describe(trace),
        "shots": evidence,
        "fixed_camera_articulated_clips": [s["clip"] for s in fixed],
    }
    result["model"] = model_record(model)
    blend_manifest = json.loads((ROOT / "blender/manifest.json").read_text())
    require(
        blend_manifest["shots_sha256"] == digest(ROOT / "tools/render/shots.json"),
        f"{hero}: editable timeline uses a different production shot list",
    )
    blend_record = next(p for p in blend_manifest["projects"] if p["hero"] == hero)
    blend = describe(ROOT / "blender" / blend_record["file"])
    require(
        blend["sha256"] == blend_record["sha256"]
        and blend_record["source_glb_sha256"] == source_sha
        and blend_record["frames"] == info["frames"]
        and not blend_record["external_libraries"],
        f"{hero}: editable source or timeline differs from renderer",
    )
    result["blender_project"] = blend
    still_trace = json.loads((ROOT / "evidence/blender-stills.json").read_text())["heroes"][hero]
    still = result["blender_still"]
    require(
        still_trace["sha256"] == still["sha256"]
        and still_trace["source_sha256"] == source_sha
        and still_trace["size"] == [still["width"], still["height"]]
        and len(still_trace["views"]) == 4,
        f"{hero}: Blender board differs from its four-camera source",
    )
    return result


def verify_animatic():
    path = ROOT / "media/video/signature-animatic.mp4"
    film, frames = video_frames(path)
    source = json.loads((ROOT / "evidence/animatic.json").read_text())
    require(
        all(source[k] == film[k] for k in ("sha256", "width", "height", "fps", "frames")),
        "Animatic digest or stream mismatch",
    )
    timeline = source["timeline"]
    require(
        {s["hero"] for s in timeline} == set(HEROES) and len(timeline) == 4, "Expected four unique chapters"
    )
    chapters = []
    starts = [s["overview_start"] for s in timeline] + [film["frames"]]
    require(starts[0] == 0 and starts == sorted(set(starts)), "Chapter boundary mismatch")
    for section, stop in zip(timeline, starts[1:]):
        hero = section["hero"]
        require(section["sha256"] == digest(ROOT / section["art"]), f"{hero}: wrong animatic storyboard")
        beats = section["beats"]
        require(
            [b["phase"].lower() for b in beats] == ["anticipation", "release", "recovery"],
            f"{hero}: missing narrative beat",
        )
        require(
            beats[0]["frame_start"] > section["overview_start"]
            and beats[-1]["frame_start"] + beats[-1]["frames"] == stop,
            f"{hero}: missing frames in chapter",
        )
        require(
            all(a["frame_start"] + a["frames"] == b["frame_start"] for a, b in zip(beats, beats[1:])),
            f"{hero}: beat interval gap",
        )
        # Compare the visible pictures during each hold, independently of the captions.
        images = [frames[b["frame_start"] + b["frames"] // 2] for b in beats]
        delta = min(float(np.abs(a - b).mean()) for a, b in combinations(images, 2))
        require(delta > 5, f"{hero}: chapter repeats a single still")
        chapters.append(
            {
                "hero": hero,
                "ability": section["ability"],
                "edition": section["edition"],
                "start_frame": section["overview_start"],
                "beats": [b["frame_start"] for b in beats],
                "min_rgb_difference": round(delta, 3),
            }
        )
    return {**film, "type": "Illustrated animatic using timed storyboard images", "chapters": chapters}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hero", action="append", choices=HEROES, help="Limit inspection to one or more heroes")
    ap.add_argument("--output", type=Path, default=ROOT / "evidence/media-qa.json")
    args = ap.parse_args()
    heroes = [verify_hero(h) for h in (args.hero or HEROES)]
    for kind in ("concept", "storyboard", "script", "video"):
        require(len({h[kind]["sha256"] for h in heroes}) == len(heroes), f"Duplicate {kind} across heroes")
    report = {
        "verifier_sha256": digest(Path(__file__)),
        "heroes": heroes,
        "method": "Full ffmpeg decode plus per-shot center-region motion and pairwise world joint distances. Subjective likeness and gameplay balance require separate review.",
    }
    if not args.hero:
        report["illustrated_reel"] = verify_animatic()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("Verified", ", ".join(h["hero"] for h in heroes))


if __name__ == "__main__":
    main()
