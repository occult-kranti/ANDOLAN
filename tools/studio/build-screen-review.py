#!/usr/bin/env python3
"""Encode a labeled, silent review of actual static captures (not gameplay footage)."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/research/evidence/studio"
SHOTS = [
    ("final-r2/title/01-r2-qualified-title.png", "YUGA native / launch briefing"),
    ("forward-probe/04-qualified-world.png", "YUGA native / offline world / Forward+ / first candidate"),
    ("final-r2/map/01-r2-map-ground.png", "Relay Foundry / separate original map-study prototype"),
    ("final-r2/map/02-r2-map-overview.png", "Relay Foundry / three-lane blockout / overview"),
    ("browser-yuga-title.png", "Browser YUGA / original roster"),
    ("browser-yuga-practice.png", "Browser YUGA / local bot practice"),
    ("browser-yuga-lab-title.png", "Original mechanics lab / local experiment"),
    ("browser-yuga-lane-lab-title.png", "Lane-economy lab / local experiment"),
    ("browser-yuga-control-lab-title.png", "Hybrid control lab / local experiment"),
    ("browser-standalone-title.png", "ANDOLAN / separate City Reform game"),
]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    output = ROOT / "dist/studio-static-screen-review.mp4"
    output.parent.mkdir(exist_ok=True)
    if output.exists():
        raise SystemExit("Preserve the existing review; choose a new version before rebuilding.")
    records = []
    command = ["ffmpeg", "-nostdin", "-v", "error"]
    with tempfile.TemporaryDirectory(prefix="yuga-screen-review-") as temp:
        folder = Path(temp)
        filters = []
        for index, (name, caption) in enumerate(SHOTS):
            source = EVIDENCE / name
            if not source.is_file() or not source.stat().st_size:
                raise SystemExit("Required original missing or empty: " + str(source))
            records.append({"path": str(source.relative_to(ROOT)), "sha256": digest(source), "caption": caption})
            command += ["-loop", "1", "-framerate", "12", "-t", "4", "-i", str(source)]
            text = folder / f"caption-{index}.txt"
            text.write_text("STATIC CAPTURE / " + caption)
            filters.append(f"[{index}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,drawbox=x=0:y=672:w=1280:h=48:color=black@0.9:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile={text}:fontsize=21:fontcolor=white:x=20:y=686[v{index}]")
        filters.append("".join(f"[v{i}]" for i in range(len(SHOTS))) + f"concat=n={len(SHOTS)}:v=1:a=0[out]")
        command += ["-filter_complex_threads", "4", "-filter_complex", ";".join(filters), "-map", "[out]", "-an", "-c:v", "libx264", "-threads", "8", "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
        subprocess.run(command, check=True)
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)]))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    if video["width"] != 1280 or video["height"] != 720 or abs(float(probe["format"]["duration"]) - 40) > 0.2:
        raise SystemExit("Unexpected encoded review geometry/duration")
    receipt = {"scope": "Silent labeled static-capture slideshow. Not advancing gameplay, animation, FPS or audio evidence.", "shots": records, "output": str(output.relative_to(ROOT)), "bytes": output.stat().st_size, "sha256": digest(output), "duration_s": float(probe["format"]["duration"]), "codec": video["codec_name"], "size": [video["width"], video["height"]], "encoder_threads": 8}
    (EVIDENCE / "static-screen-review.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in ["output", "bytes", "duration_s", "codec"]}))

if __name__ == "__main__":
    main()
