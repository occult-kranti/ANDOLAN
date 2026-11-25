#!/usr/bin/env python3
"""Check a native ability reel, index sampled beats, and show decoded frames."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import file_digest
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont


LABELS = {
    "vajra_gada": "Vajra Gada",
    "vajra_kavacha": "Vajra Kavacha",
    "maruti_udayana": "Maruti Udayana",
    "lanka_dahan": "Lanka Dahan",
    "mountain_pulse": "Mountain Pulse",
}
PHASES = ("begin", "release", "impact", "recovery", "end")
REVISED_CLIPS = {"fire", "cast2", "cast1", "tail_sweep", "mountain_pulse"}
PROJECT = Path(__file__).resolve().parents[2]


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def decode_columns(movie, selections, contact_path, fps):
    selected = sorted({index for beats in selections.values() for index in beats.values()})
    clause = "+".join(f"eq(n\\,{index})" for index in selected)
    with TemporaryDirectory() as directory:
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-threads", "2",
            "-i", str(movie), "-an", "-vf", f"select={clause}",
            "-fps_mode", "vfr", "-threads", "1", str(Path(directory) / "decoded-%03d.png"),
        ], check=True, timeout=60)
        slices = sorted(Path(directory).glob("decoded-*.png"))
        if len(slices) != len(selected):
            raise ValueError("Playback is missing a selected phase frame")
        screenshots = {index: Image.open(path).convert("RGB") for index, path in zip(selected, slices, strict=True)}

    frame_w, frame_h, row_h = 376, 211, 275
    canvas = Image.new("RGB", (1568, 1490), "#11171b")
    draw = ImageDraw.Draw(canvas)
    sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    serif = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    title, label, stamp = (ImageFont.truetype(serif, 32), ImageFont.truetype(sans, 19),
                           ImageFont.truetype(sans, 14))
    ink, dim = "#f1eadb", "#acb7bf"
    draw.text((22, 15), "Hanuman Trial ability reel", fill=ink, font=title)
    draw.text((23, 62), "Decoded native footage at the sampled windup, release, result and recovery frames.",
              fill=dim, font=label)
    for row, (ability, picks) in enumerate(selections.items()):
        top = 103 + row * row_h
        draw.text((22, top), LABELS[ability], fill=ink, font=label)
        for column, (phase, index) in enumerate(picks.items()):
            left = 22 + (frame_w + 7) * column
            decoded = screenshots[index].resize((frame_w, frame_h), Image.Resampling.LANCZOS)
            canvas.paste(decoded, (left, top + 28))
            draw.text((left, top + 246), f"{phase}  ·  {index / fps:05.2f} s", fill=dim, font=stamp)
    canvas.save(contact_path, quality=91, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--movie", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--contact", type=Path)
    args = parser.parse_args()
    receipt_path = args.frames / "render.json"
    render = json.loads(receipt_path.read_text())
    if not render["complete"] or not render["scope"].startswith("Rendered native"):
        raise ValueError("Use the completed graphical capture")
    fps, frames = render["fps"], render["frames"]
    if any(token["frame"] != index or not token.get("sha256") for index, token in enumerate(frames)):
        raise ValueError("Capture samples must be contiguous with original frame hashes")
    if any(set(row["actor"].get("revised_motion_clips", [])) != REVISED_CLIPS
           or row["actor"].get("ability_motion_error") for row in frames):
        raise ValueError("The capture did not load all five revised animations")
    for resource, recorded_hash in render["source_sha256"].items():
        if digest(PROJECT / resource.removeprefix("res://")) != recorded_hash:
            raise ValueError(f"Capture source changed after startup: {resource}")

    stream = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(args.movie),
    ], text=True))
    video = next(item for item in stream["streams"] if item["codec_type"] == "video")
    audio = [item for item in stream["streams"] if item["codec_type"] == "audio"]
    assert video["codec_name"] == "h264"
    assert video["avg_frame_rate"] == f"{fps}/1" and int(video["nb_read_frames"]) == len(frames)
    assert [video["width"], video["height"]] == render["size"]
    assert abs(float(video["duration"]) - len(frames) / fps) < .01

    phases = render["ability_beats"]
    starts = {shot["ability"]: shot["frame"] for shot in render["capture_cameras"]}
    selected, planned_shots = {}, {}
    for ability in LABELS:
        beats = phases[ability]
        begin, release, impact, recovery, end = (beats[phase]["frame"] for phase in PHASES)
        assert 0 <= starts[ability] <= begin < release <= impact < recovery <= end < len(frames), (ability, beats)
        assert all(frames[beats[phase]["frame"]]["shot"] == ability for phase in PHASES)
        assert len({(beat["generation"], beat["cast_id"]) for beat in beats.values()}) == 1
        result_label, result_frame = "Impact", impact
        if ability == "maruti_udayana":
            result_label = "Landing"
            result_frame = next(i for i in range(release, recovery)
                                if frames[i]["actor"]["last_vault"].get("blocked") is False)
        elif impact == release:
            result_label, result_frame = "Visible result", min(impact + 3, recovery - 1)
        recovery_view = min(recovery + 5, len(frames) - 1)
        assert frames[recovery_view]["shot"] == ability
        selected[ability] = {
            "Windup": (begin + release - 1) // 2,
            "Release": release,
            result_label: result_frame,
            "Recovery": recovery_view,
        }
        impact_event = next(event for event in render["events"]
                            if event["kind"] == "impact" and event["ability_id"] == ability)
        planned_shots[ability] = {
            "shot_start_frame": starts[ability], "shot_start_s": starts[ability] / fps,
            "motion": impact_event["motion"], "events": beats, "impact_reason": impact_event["reason"],
            "affected_ids": [effect["unit_id"] for effect in impact_event["receipts"]],
            "decoded_frame_selection": selected[ability],
        }
        if ability == "maruti_udayana":
            airborne = [i for i in range(release, result_frame) if frames[i]["actor"]["vault"]]
            peak = min(airborne, key=lambda i: abs(
                frames[i]["actor"]["vault"]["age"] / frames[i]["actor"]["vault"]["duration"] - .5))
            planned_shots[ability]["vault_witness"] = {
                "airborne_near_apex_frame": peak, "landing_frame": result_frame,
                "landing": frames[result_frame]["actor"]["last_vault"],
            }

    deltas = Counter(b["physics_frame"] - a["physics_frame"] for a, b in zip(frames, frames[1:]))
    result = {
        "scope": render["scope"], "renderer": render["renderer"], "renderer_device": render["renderer_device"],
        "godot_version": render["godot_version"],
        "audio": {"captured_from_game": render["audio_recorded"], "muxed_audio_streams": len(audio)},
        "sampled_and_encoded_fps": fps, "physics_ticks_per_second": render["physics_ticks_per_second"],
        "size": render["size"], "seconds": len(frames) / fps, "decoded_frame_count": int(video["nb_read_frames"]),
        "distinct_source_frames": len({frame["sha256"] for frame in frames}),
        "physics_tick_steps_between_sampled_frames": dict(sorted(deltas.items())),
        "storyboard": render["storyboard"], "input": "InputEventAction plus scripted player aim and separate capture cameras",
        "revised_motion_clips": sorted(REVISED_CLIPS),
        "runtime_source_sha256": render["source_sha256"], "review_script_sha256": digest(Path(__file__)),
        "raw_render_receipt_sha256": digest(receipt_path), "movie_sha256": digest(args.movie),
        "movie_bytes": args.movie.stat().st_size, "shots": planned_shots,
        "original_frames": [{key: row[key] for key in ("frame", "physics_frame", "sha256")} for row in frames],
    }
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.contact:
        decode_columns(args.movie, selected, args.contact, fps)


if __name__ == "__main__":
    main()
