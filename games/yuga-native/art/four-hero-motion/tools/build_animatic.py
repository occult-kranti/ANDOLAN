#!/usr/bin/env python3
"""Build the four-hero illustrated action review. Requires Pillow and FFmpeg with libx264."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT.parents[1] / "assets/fonts"
SIZE = (1280, 720)
FPS = 24
OVERVIEW_FRAMES = 46
BEAT_FRAMES = 62
PHASES = ("Anticipation", "Release", "Recovery")
PAPER = "#eee9dc"
MUTED = "#a9aaa2"
BACKGROUND = "#171d1d"
HAIRLINE = "#43504d"
HEROES = {
    "hanuman": {
        "title": "Mountain Descent", "edition": "Classic Sangam", "accent": "#f0b072",
        "beats": [
            ("0.00–0.70 s", "Set both heels. Coil the hips over the low gada and let the tail sweep back."),
            ("0.70–1.15 s", "Tuck the mace close. The body travels first and the long tail trails the arc."),
            ("1.15 s  ·  Landing", "Fold the knees into contact. The ground ring spreads as the tail curls up."),
        ],
    },
    "rama": {
        "title": "Dawn Volley", "edition": "Classic Sangam", "accent": "#e2c678",
        "beats": [
            ("0.00–1.00 s", "Set the lead foot. Hold the string at the cheek and keep the firing line still."),
            ("1.00 s  ·  Volley", "Open the draw fingers. Three arrows leave together along the locked aim."),
            ("After release", "Let the elbow drop. The bow lowers as the cobalt hem settles behind the legs."),
        ],
    },
    "shiva": {
        "title": "Tandava Downbeat", "edition": "Proposed action", "accent": "#8bd0d5",
        "beats": [
            ("0.00–0.80 s", "Lift the left knee from a planted right foot. Keep the trident upright and the gaze level."),
            ("0.80 s  ·  Contact", "Plant the left sole once. The radial pulse breaks outward from that contact."),
            ("0.80–1.40 s", "Release the shoulders. Let the drum beaters and loose hair settle after the staff."),
        ],
    },
    "krishna": {
        "title": "Govardhan Canopy", "edition": "Proposed action", "accent": "#d1cf81",
        "beats": [
            ("0.00–1.00 s", "Set the flute at the sash. Look up before the left elbow opens toward the canopy."),
            ("1.00 s  ·  Ward", "Reach the left forefinger to its apex. Keep the open right hand and chakra low."),
            ("1.00–1.60 s", "Lower the arm, then return the gaze to allies. The granted ward can outlast the pose."),
        ],
    },
}


@lru_cache(maxsize=32)
def font(family, size):
    return ImageFont.truetype(str(FONT_DIR / f"Noto{family}-Regular.ttf"), size)


def tracked(draw, xy, text, fill, size=15, space=2):
    x, y = xy
    face = font("Sans", size)
    for character in text:
        draw.text((x, y), character, font=face, fill=fill, anchor="lt")
        x += draw.textlength(character, font=face) + space


def wrap(draw, text, face, width):
    lines = []
    for word in text.split():
        candidate = f"{lines[-1]} {word}" if lines else word
        if lines and draw.textlength(candidate, font=face) > width:
            lines.append(word)
        elif lines:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines


def chrome(hero, edition, accent, number):
    frame = Image.new("RGB", SIZE, BACKGROUND)
    d = ImageDraw.Draw(frame)
    tracked(d, (53, 28), "YUGA", PAPER, size=20, space=5)
    d.line((146, 30, 146, 49), fill=HAIRLINE)
    tracked(d, (164, 33), "SIGNATURE MOTION", MUTED, size=13)
    d.text((1225, 32), f"{number:02d} / 04", fill=accent, font=font("Sans", 17), anchor="rt")
    d.line((53, 66, 1226, 66), fill=HAIRLINE)
    d.line((53, 662, 1226, 662), fill=HAIRLINE)
    d.text((54, 681), hero.title(), fill=PAPER, font=font("Sans", 16), anchor="lt")
    d.text((1226, 681), edition, fill=MUTED, font=font("Sans", 16), anchor="rt")
    return frame


def compose_card(base, hero, entry, strip):
    frame = base.copy()
    d = ImageDraw.Draw(frame)
    d.text((54, 82), hero.title(), fill=PAPER, font=font("Serif", 53), anchor="lt")
    d.text((1226, 101), entry["title"], fill=entry["accent"], font=font("Serif", 37), anchor="rt")
    # The master sheet is always displayed in full; Shiva's three portrait panels have a 2:1 outer ratio.
    max_width, max_height = 1172, 416
    scale = min(max_width / strip.width, max_height / strip.height)
    w, h = round(strip.width * scale), round(strip.height * scale)
    x, y = (SIZE[0] - w)//2, 158 + (max_height - h)//2
    frame.paste(strip.resize((w, h), Image.Resampling.LANCZOS), (x, y))
    for i, phase in enumerate(PHASES):
        midpoint = x + (i + .5) * w / 3
        d.text((midpoint, y + h + 16), phase, font=font("Sans", 17), fill=MUTED, anchor="mt")
    return frame


def focus_layout(base, entry, phase, time, direction):
    frame = base.copy()
    d = ImageDraw.Draw(frame)
    accent = entry["accent"]
    tracked(d, (54, 118), "ILLUSTRATED ACTION", MUTED, size=14)
    # Fit long action names without altering glyph proportions.
    title_size = 51
    while d.textlength(entry["title"], font=font("Serif", title_size)) > 495:
        title_size -= 1
    d.text((52, 166), entry["title"], fill=PAPER, font=font("Serif", title_size), anchor="lt")
    d.line((54, 253, 488, 253), fill=HAIRLINE)
    tracked(d, (54, 288), PHASES[phase].upper(), accent, size=17)
    body = font("Sans", 26)
    lines = wrap(d, direction, body, 445)
    assert len(lines) <= 4
    for i, line in enumerate(lines):
        d.text((53, 338 + 39*i), line, fill=PAPER, font=body, anchor="lt")
    d.text((54, 547), time, fill=accent, font=font("Serif", 27), anchor="lt")
    tracked(d, (54, 599), "ACTION TIMING", MUTED, size=12)
    return frame


def crop_panels(strip):
    bounds = [round(i * strip.width / 3) for i in range(4)]
    return [strip.crop((bounds[i] + 2, 1, bounds[i+1] - 2, strip.height-1)) for i in range(3)]


def focused_frames(base, panel, phase, accent):
    # A very slow optical push stays within the dark matte throughout. The full costume, feet
    # and weapon are retained, including the tall Shiva panels.
    left, top, right, bottom = 532, 82, 1227, 646
    scale = min((right-left) / panel.width, (bottom-top) / panel.height)
    previous_size = None
    resized = None
    for i in range(BEAT_FRAMES):
        t = i / (BEAT_FRAMES-1)
        ease = t*t*(3-2*t)
        factor = scale*(.972 + .028*ease)
        size = (round(panel.width*factor), round(panel.height*factor))
        if size != previous_size:
            resized = panel.resize(size, Image.Resampling.LANCZOS)
            previous_size = size
        x, y = (left+right-size[0])//2, (top+bottom-size[1])//2
        frame = base.copy()
        frame.paste(resized, (x,y))
        d = ImageDraw.Draw(frame)
        for beat in range(3):
            start = 54 + beat*53
            d.line((start, 508, start+43, 508), fill=HAIRLINE, width=3)
            progress = 1 if beat<phase else ease if beat==phase else 0
            if progress:
                d.line((start, 508, start+round(progress*43), 508), fill=accent, width=3)
        yield frame


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output, evidence):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".mp4", delete=False) as f:
        tmp = Path(f.name)
    try:
        cmd = ["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24",
               "-s","1280x720","-r",str(FPS),"-i","-","-map","0:v","-an",
               "-threads","1","-c:v","libx264","-preset","veryfast","-crf","19",
               "-maxrate","1550k","-bufsize","3100k","-pix_fmt","yuv420p","-g","48",
               "-fflags","+bitexact","-flags:v","+bitexact","-map_metadata","-1",
               "-movflags","+faststart",str(tmp)]
        timeline = []
        n = 0
        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as encoder:
            try:
                for number,(hero,entry) in enumerate(HEROES.items(),1):
                    source = ROOT / "media/art" / f"{hero}-beats.webp"
                    with Image.open(source) as artwork:
                        strip = artwork.convert("RGB")
                    chrome_frame = chrome(hero,entry["edition"],entry["accent"],number)
                    overview = compose_card(chrome_frame,hero,entry,strip).tobytes()
                    row = {"hero":hero,"ability":entry["title"],"edition":entry["edition"],
                           "art":str(source.relative_to(ROOT)),"sha256":digest(source),
                           "art_dimensions":strip.size,"overview_start":n,"beats":[]}
                    for _ in range(OVERVIEW_FRAMES):
                        encoder.stdin.write(overview)
                        n += 1
                    for phase,(panel,(time,direction)) in enumerate(zip(crop_panels(strip),entry["beats"],strict=True)):
                        text_frame = focus_layout(chrome_frame,entry,phase,time,direction)
                        row["beats"].append({"phase":PHASES[phase],"frame_start":n,"frames":BEAT_FRAMES,
                                             "script_time":time,"direction":direction})
                        for frame in focused_frames(text_frame,panel,phase,entry["accent"]):
                            encoder.stdin.write(frame.tobytes())
                            n += 1
                    timeline.append(row)
            finally:
                encoder.stdin.close()
            if encoder.wait() != 0:
                raise RuntimeError("FFmpeg could not finish the signature animatic")
        probe = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams",
                            "-show_format","-of","json",str(tmp)],text=True))
        video, = probe["streams"]
        assert (video["codec_name"],video["pix_fmt"],video["width"],video["height"],
                video["avg_frame_rate"],int(video["nb_frames"])) == ("h264","yuv420p",*SIZE,"24/1",n)
        subprocess.run(["ffmpeg","-v","error","-xerror","-threads","1","-i",str(tmp),"-f","null","-"],check=True)
        if tmp.stat().st_size > 10_000_000:
            raise ValueError("Movie exceeds the 10 MB download budget")
        receipt = {"kind":"Illustrated signature animatic","width":SIZE[0],"height":SIZE[1],
                   "fps":FPS,"frames":n,"seconds":n/FPS,"bytes":tmp.stat().st_size,
                   "sha256":digest(tmp),"video":"H.264, yuv420p, faststart","audio":"silent",
                   "tools":{"pillow":pillow_version,"ffmpeg":subprocess.check_output(
                       ["ffmpeg","-version"],text=True).splitlines()[0]},
                   "timing":"Captions use the design's action clock. The edit holds each pose longer for reading.",
                   "timeline":timeline}
        os.replace(tmp,output)
        if evidence:
            evidence.parent.mkdir(parents=True,exist_ok=True)
            evidence.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
        print(f"{n} frames at {FPS} fps, {receipt['bytes']} bytes, sha256 {receipt['sha256']}")
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,default=ROOT/"media/video/signature-animatic.mp4")
    cli.add_argument("--evidence",type=Path,default=ROOT/"evidence/animatic.json")
    args = cli.parse_args()
    build(args.output,args.evidence)
