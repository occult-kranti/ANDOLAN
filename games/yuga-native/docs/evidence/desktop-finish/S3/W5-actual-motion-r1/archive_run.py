#!/usr/bin/env python3
"""Archive a completed original take losslessly; optionally encode its native-speed review video."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--encoder-cpus", default="0,1")
    ap.add_argument("--encoder-threads", type=int, default=2)
    args = ap.parse_args()
    if args.output.exists():
        ap.error("Fresh output required")
    logs = args.source.with_name(args.source.name + "-logs")
    report = json.loads((args.source / "capture.json").read_text())
    run = json.loads((logs / "run.json").read_text())
    if not report["complete"] or not run["complete"]:
        ap.error("Incomplete take cannot be archived as completed")
    expected = 40 if report["case"] == "landing120" else 120
    assert len(report["shots"]) == expected and len(list(args.source.glob("*.png"))) == expected
    assert all(sha(args.source / shot["file"]) == shot["sha256"] for shot in report["shots"])
    assert sha(args.source / "capture.json") == run["report_sha256"]
    args.output.mkdir(parents=True)
    originals = args.output / "originals"
    originals.mkdir()
    files = {}
    for shot in report["shots"]:
        source = args.source / shot["file"]
        target = originals / source.name
        shutil.copy2(source, target)
        assert sha(target) == shot["sha256"]
        files[str(target.relative_to(args.output))] = {"sha256": sha(target), "bytes": target.stat().st_size}
    raw = (args.source / "capture.json").read_bytes()
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    assert gzip.decompress(compressed) == raw
    (args.output / "capture.json.gz").write_bytes(compressed)
    for name in ["godot.log", "xvfb.log", "run.json"]:
        shutil.copy2(logs / name, args.output / name)
        assert sha(logs / name) == sha(args.output / name)
        files[name] = {"sha256": sha(args.output / name), "bytes": (args.output / name).stat().st_size}
    archive = {"passed": True, "source": str(args.source), "originals": files,
               "capture": {"path": "capture.json.gz", "raw_sha256": hashlib.sha256(raw).hexdigest(),
                           "raw_bytes": len(raw), "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
                           "gzip_bytes": len(compressed), "gzip_mtime": 0},
               "scope": "Every original PNG and raw log copied byte-exact; complete raw capture JSON retained losslessly. Source remains in temporary workspace."}
    if args.video:
        video = args.output / "normal-speed.mp4"
        command = ["taskset", "-c", args.encoder_cpus, "ffmpeg", "-nostdin", "-v", "warning", "-n",
                   "-framerate", str(report["fixed_capture_hz"]), "-i", str(originals / "frame-%03d.png"),
                   "-frames:v", str(expected), "-c:v", "libx264", "-threads", str(args.encoder_threads), "-filter_threads", "1",
                   "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(video)]
        with (args.output / "ffmpeg.log").open("wb") as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90)
        probe_command = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                         "stream=codec_name,width,height,nb_read_frames,avg_frame_rate,duration", "-of", "json", str(video)]
        probe = json.loads(subprocess.check_output(probe_command, timeout=30))
        stream = probe["streams"][0]
        assert completed.returncode == 0 and int(stream["nb_read_frames"]) == expected
        assert (stream["width"], stream["height"]) == (1280, 960)
        assert stream["avg_frame_rate"] == str(report["fixed_capture_hz"]) + "/1"
        archive["video"] = {"command": command, "exit_code": completed.returncode, "probe": probe,
                            "sha256": sha(video), "bytes": video.stat().st_size,
                            "scope": "Lossy H.264 viewing aid at recorded simulation cadence, no interpolation or quality changes to retained PNGs. This cadence is not measured wall-time FPS."}
    (args.output / "archive.json").write_text(json.dumps(archive, indent=2) + "\n")
    print(json.dumps({"passed": True, "originals": expected, "output": str(args.output), "raw_capture_bytes": len(raw)}))


if __name__ == "__main__":
    main()
