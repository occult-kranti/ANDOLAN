"""Photograph the actual Nexuiz client from the same three positions in both rebuilt maps."""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from build import NAME, file_hash

# Positions and angles are in the scaled engine space. The first two follow the
# mapper's intermission views. The last is at player height in the adjoining court.
CAMERAS = [
    ("west-courtyard", "-1280 -928 390", "15 154 0"),
    ("high-crossing", "1846 2524 267", "14 149 0"),
    ("arches", "1336 1188 105", "12 -90 0"),
]


def player_course(data):
    """Sample the stock player's walk and jump on a sloped part of the jade court."""
    (data / "qa-spawn.cfg").write_text(
        'prvm_edictset server 1 origin "-2152 -817 255"\n'
        'prvm_edictset server 1 v_angle "0 90 0"\n'
        'prvm_edictset server 1 angles "0 90 0"\nprvm_edictset server 1 fixangle 1\n')
    for label in ("standing", "moved", "airborne", "landed"):
        (data / f"qa-{label}.cfg").write_text(f"echo QA_STATE_{label}\n" + "".join(
            f"prvm_edictget server 1 {field}\n" for field in ("origin", "velocity", "health", "flags")))
    return ['defer 16 "cmd join"', 'defer 18 "exec qa-spawn.cfg"', 'defer 19 "exec qa-standing.cfg"',
            'defer 19.1 "+forward"', 'defer 19.8 "-forward"', 'defer 20.5 "exec qa-moved.cfg"',
            'defer 21 "+jump"', 'defer 21.08 "-jump"', 'defer 21.3 "exec qa-airborne.cfg"',
            'defer 24 "exec qa-landed.cfg"', 'defer 25 "quit"']


def player_receipt(log):
    result = {}
    fields = r"\s*\n([^\n]+)\n([^\n]+)\n([^\n]+)\n([^\n]+)"
    for label in ("standing", "moved", "airborne", "landed"):
        match = re.search(f"QA_STATE_{label}" + fields, log)
        if not match:
            raise ValueError(f"Missing sampled player state {label}")
        pos, vel, hp, flags = match.groups()
        result[label] = {"origin": list(map(float, pos.split())), "velocity": list(map(float, vel.split())),
                         "health": float(hp), "on_ground": bool(int(flags) & 512)}
    distance = math.dist(result["standing"]["origin"][:2], result["moved"]["origin"][:2])
    lift = result["airborne"]["origin"][2] - result["moved"]["origin"][2]
    if (distance <= 48 or lift <= 6 or result["airborne"]["on_ground"] or
            not result["standing"]["on_ground"] or not result["landed"]["on_ground"] or
            any(v["health"] <= 0 for v in result.values())):
        raise ValueError(f"Player failed the slope walk and jump check: {result}")
    return {"planar_walk_units": distance, "sampled_jump_rise_units": lift, "samples": result}


def capture(engine, rebuild, work, variant):
    base = work / variant
    data = base / "data"
    profile = base / "profile"
    data.mkdir(parents=True)
    profile.mkdir()
    game_data = rebuild / "game/data"
    sources = [game_data / "data.pk3", game_data / "textures.pk3",
               rebuild / f"{NAME}-{variant}.pk3"]
    for item in sources:
        (data / item.name).symlink_to(item.resolve(strict=True))
    schedule = []
    for index, (name, origin, angles) in enumerate(CAMERAS):
        config = f"""r_draw2d 0
r_drawviewmodel 0
prvm_edictset server 1 origin "{origin}"
prvm_edictset server 1 v_angle "{angles}"
prvm_edictset server 1 angles "{angles}"
prvm_edictset server 1 fixangle 1
"""
        (data / f"{name}.cfg").write_text(config)
        second = 4 + 4 * index
        schedule.extend([f'defer {second} "exec {name}.cfg"', f'defer {second + 2} "screenshot"'])
    schedule.extend(player_course(data) if variant == "jade" else ['defer 16 "quit"'])
    (data / "photo.cfg").write_text("\n".join(schedule) + "\n")
    (data / "autoexec.cfg").write_text("sv_public 0\nsv_cheats 1\ng_warmup 0\nbot_number 0\n"
                                     "cl_showfps 0\ncl_bob 0\ncrosshair 0\nr_drawviewmodel 0\n")
    log = base / "client.log"
    with log.open("wb") as output:
        subprocess.run([engine, "-nexuiz", "-basedir", base, "-userdir", profile, "-window",
                        "-width", "1024", "-height", "576", "-nosound", "+sv_public", "0",
                        "+sv_cheats", "1", "+map", NAME, "+exec", "photo.cfg"], stdout=output,
                       stderr=subprocess.STDOUT, timeout=150, check=True)
    recorded = sorted((profile / "data/screenshots").glob("*.jpg"))
    if len(recorded) != len(CAMERAS) or "is spectating now" not in log.read_text(errors="replace"):
        raise ValueError(f"{variant}: missing game connection or one of the scheduled captures, see {log}")
    frames = []
    for (name, _, _), src in zip(CAMERAS, recorded):
        dest = work / f"{variant}-{name}.jpg"
        shutil.copyfile(src, dest)
        with Image.open(dest) as frame:
            if frame.size != (1024, 576):
                raise ValueError(f"Unexpected screenshot size for {dest}: {frame.size}")
        frames.append(dest)
    return frames, player_receipt(log.read_text(errors="replace")) if variant == "jade" else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", required=True, type=Path, help="Path to the DarkPlaces executable")
    ap.add_argument("--build", required=True, type=Path, help="Completed build.py output directory")
    ap.add_argument("--output", required=True, type=Path, help="Fresh capture directory")
    args = ap.parse_args()
    work = args.output.resolve()
    if work.exists():
        ap.error("Use a fresh capture directory")
    if not os.environ.get("DISPLAY"):
        ap.error("Set DISPLAY to an X server or launch this script with xvfb-run")
    work.mkdir(parents=True)
    canvas = Image.new("RGB", (1024, 900), (20, 22, 24))
    draw = ImageDraw.Draw(canvas)
    receipt = {"camera_positions_and_angles": CAMERAS, "screenshots_sha256": {}}
    for col, variant in enumerate(("original", "jade")):
        paths, movement = capture(args.engine.resolve(), args.build.resolve(), work, variant)
        if movement:
            receipt["jade_player_movement"] = movement
        draw.text((14 + col * 512, 12), ("Original source rebuild", "Jade ground")[col], fill="white")
        for row, path in enumerate(paths):
            with Image.open(path) as im:
                canvas.paste(im.resize((512, 288)), (col * 512, 36 + row * 288))
            receipt["screenshots_sha256"][path.name] = file_hash(path)
    canvas.save(work / "nexuiz-courtyards.jpg", quality=90)
    (work / "engine-captures.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(work / "nexuiz-courtyards.jpg")


if __name__ == "__main__":
    main()
