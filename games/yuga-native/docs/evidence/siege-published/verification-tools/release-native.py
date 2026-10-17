#!/usr/bin/env python3
"""Tag-gated portable release preparation; never renders or replaces archived film."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
FILM = PROJECT / "docs/evidence/combat-film-r4"
TAG = re.compile(r"yuga-(?:confluence-duel|traversal-armies)-[A-Za-z0-9][A-Za-z0-9._-]{0,100}\Z")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,160}\Z")
CHECKS = ("archive", "media", "script", "film", "motion", "vfx", "audio", "native",
          "world-scene", "world-flow", "world-lighting")
TRAVERSAL_CHECKS = ("traversal", "traversal-pose", "army", "controls", "traversal-audio", "stress",
                    "security", "release-gates", "siege-army", "vehicle-art", "siege-effects", "siege-audio", "siege-ui", "siege-release-gates", "siege-pose")
TRAVERSAL_CAPTURE_DIRECTORY = "docs/evidence/siege-traversal-render-r1"
SIEGE_CAPTURE_DIRECTORY = "docs/evidence/siege-render-r2"
SIEGE_CAPTURE_ASSETS = {"yuga-siege-preview.mp4", "siege-render-review.json", "siege-video.json", "SIEGE-RENDER-REVIEW.md"}
SIEGE_SELECTED_FRAMES = (45, 90, 145)
SIEGE_CAPTURE_ASSETS |= {f"siege-frame-{index:05d}.png" for index in SIEGE_SELECTED_FRAMES}
TRAVERSAL_STILLS = {
    "still-05-actual-take-hud.png", "still-city-overview.png",
    "still-sun-landing-courts.png", "still-army-engagement.png",
    "still-moonlit-confluence.png",
}
TRAVERSAL_CAPTURE_ASSETS = {"yuga-traversal-preview.mp4", "traversal-render-review.json",
                            "traversal-video.json", "TRAVERSAL-RENDER-REVIEW.md"} | TRAVERSAL_STILLS
CAPTURE_FIXED_SOURCES = {"project.godot", "tools/capture-traversal.gd",
                         "tools/run-traversal-capture.py", "art/world/confluence-map.json"}
CAPTURE_REQUIRED_RUNTIME = {"scripts/confluence_world.gd", "scripts/player.gd",
                            "scripts/player_traversal.gd", "scripts/lane_army.gd",
                            "scripts/lane_minion.gd", "scripts/traversal_pose.gd",
                            "scripts/traversal_landmarks.gd", "scripts/traversal_audio.gd",
                            "scenes/confluence_world.tscn", "assets/world/confluence-map.json",
                            "assets/heroes/rama-production.glb"}


def traversal_release(tag):
    return tag.startswith("yuga-traversal-armies-")


def siege_release(tag):
    return traversal_release(tag) and tag.endswith("-siege")
REQUIRED_ARCHIVE = {
    "yuga-confluence-duel.mp4", "combat-film-render.json", "combat-film-video.json",
    "confluence-duel.json", "capture-combat-film.gd", "cinematic_actor.gd",
    "combat_film.gd", "duel_effects.gd", "film_lighting.gd", "run-combat-film.py",
    "media-release-check.json", "REVIEW.md", "godot-log.txt",
}
BASE_URL = "https://github.com/godotengine/godot-builds/releases/download/4.6.3-stable/"
ENGINES = {
    "linux": {
        "archive": "Godot_v4.6.3-stable_linux.x86_64.zip",
        "archive_sha256": "d0bc2113065e481c9c2c2b2c37daa4e8be3fe9e27f0ab9ab0b6096e9a37907f3",
        "files": [{"name": "Godot_v4.6.3-stable_linux.x86_64", "bytes": 138981968,
                   "sha256": "f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3"}],
    },
    "windows": {
        "archive": "Godot_v4.6.3-stable_win64.exe.zip",
        "archive_sha256": "e39986a178d585ce7ac198fb8de6ea436366dc0cc00e594810c2e3e104c04b90",
        "archive_bytes": 79844616,
        "official_release_asset_id": 425485542,
        "files": [
            {"name": "Godot_v4.6.3-stable_win64.exe", "bytes": 172409864,
             "sha256": "ef90e929ba1a6a4322860285d97f40f4aa349c90329a91b0e8b55b8df0f4cb00"},
            {"name": "Godot_v4.6.3-stable_win64_console.exe", "bytes": 198152,
             "sha256": "63b3b2208819714c9677fbfdd8217c5b7dee8ecf5f383502e826bc9e2227ff5a"},
        ],
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def record(path):
    return {"bytes": Path(path).stat().st_size, "sha256": digest(path)}


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def member(root, name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts and "\\" not in name, "Unsafe archive member")
    result = root / path
    require(result.is_file() and not result.is_symlink(), "Missing/nonregular file: " + name)
    require(result.resolve().is_relative_to(root.resolve()), "Archive member escapes root")
    return result


def install_engines(destination):
    destination.mkdir(parents=True, exist_ok=True)
    results = {}
    for platform, spec in ENGINES.items():
        archive = destination / spec["archive"]
        url = BASE_URL + spec["archive"]
        if not archive.exists():
            with urllib.request.urlopen(url, timeout=90) as response, archive.open("xb") as output:
                shutil.copyfileobj(response, output)
        require(digest(archive) == spec["archive_sha256"], "Official engine archive digest mismatch: " + platform)
        if "archive_bytes" in spec:
            require(archive.stat().st_size == spec["archive_bytes"], "Engine archive size mismatch")
        with zipfile.ZipFile(archive) as bundle:
            require(set(bundle.namelist()) == {row["name"] for row in spec["files"]}, "Unexpected engine ZIP members")
            for row in spec["files"]:
                require(bundle.getinfo(row["name"]).file_size == row["bytes"], "Engine member size mismatch")
                target = destination / row["name"]
                with bundle.open(row["name"]) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                require(record(target) == {"bytes": row["bytes"], "sha256": row["sha256"]}, "Engine payload digest mismatch")
                if platform == "linux":
                    target.chmod(0o755)
        provenance = {**spec, "source": url, "verification": "Pinned official archive and extracted payload SHA-256 verified by this run; no live GitHub API assertion."}
        results[platform] = provenance
        if platform == "windows":
            # package-native.py requires this exact file beside its Windows engine.
            write_json(destination / "godot-windows-provenance.json", provenance)
    write_json(destination / "engine-downloads.json", results)
    return {"passed": True, "platforms": list(results)}


def validate_evidence(working_tree=False):
    manifest_path = FILM / "archive-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    files = manifest["files"]
    require(isinstance(files, dict), "Film archive must list exact file records")
    require(REQUIRED_ARCHIVE <= set(files), "Film archive omits required movie, reports or captured source records")
    actual = {path.relative_to(FILM).as_posix() for path in FILM.rglob("*") if path.is_file()}
    require(actual == set(files) | {"archive-manifest.json"}, "Film archive file set differs from manifest")
    for name, expected in files.items():
        require(record(member(FILM, name)) == expected, "Archived film payload differs: " + name)
    if not working_tree:
        paths = [str(manifest_path.relative_to(REPO))] + [str((FILM / name).relative_to(REPO)) for name in files]
        for path in paths:
            git("ls-files", "--error-unmatch", path)
        subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *paths], cwd=REPO, check=True, stdout=subprocess.DEVNULL)
    render = json.loads(member(FILM, "combat-film-render.json").read_text())
    video = json.loads(member(FILM, "combat-film-video.json").read_text())
    require(render.get("complete") is True and not render.get("failure") and render.get("preview") is False, "Film capture is incomplete or preview-only")
    require(render.get("frame_count") == 576 and render.get("sample_hz") == 24 and render.get("duration_seconds") == 24, "Film capture rate/count/duration mismatch")
    frames = render["frames"]
    require(len(frames) == 576, "Capture report does not list 576 samples")
    for index, frame in enumerate(frames):
        require(frame["file"] == f"frame-{index:05d}.png" and abs(frame["t_seconds"] - index / 24) < 1e-9, "Capture timeline discontinuity")
        if frame["file"] in files:
            require(frame["sha256"] == files[frame["file"]]["sha256"], "Selected capture frame mismatch")
    movie = member(FILM, "yuga-confluence-duel.mp4")
    require(video.get("complete") is True and video["video"]["file"] == movie.name, "Movie report incomplete or wrong file")
    require(record(movie) == {key: video["video"][key] for key in ("bytes", "sha256")}, "Movie differs from accepted video record")
    require(video["render_report_sha256"] == digest(FILM / "combat-film-render.json"), "Movie is linked to a different render report")
    return {"passed": True, "archive_files_checked": len(files), "movie": record(movie),
            "listed_capture_samples_checked": len(frames), "selected_pngs_checked": sum(name.endswith(".png") for name in files),
            "scope": "Committed archived bytes and recorded timeline checked; unarchived raw PNGs were not rechecked and CI did not render this film."}


def traversal_probe_signature(probe):
    streams = probe.get("streams", [])
    require(isinstance(streams, list) and len(streams) == 1 and isinstance(streams[0], dict),
            "Traversal video must contain one silent video stream")
    stream = streams[0]
    require(stream.get("codec_type") == "video" and stream.get("codec_name") == "h264",
            "Traversal preview is not the expected silent H.264 video")
    require((stream.get("width"), stream.get("height")) == (1280, 720) and
            str(stream.get("nb_read_frames")) == "180" and stream.get("avg_frame_rate") == "30/1",
            "Traversal video dimensions, decoded frames or frame rate differ")
    try:
        duration = float(probe["format"]["duration"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Traversal video duration is missing or invalid") from error
    require(math.isfinite(duration) and abs(duration - 6.0) <= .02, "Traversal video must be six seconds")
    return {"width":1280,"height":720,"frames":180,"fps":30,"duration_seconds":duration}


def probe_traversal_movie(path):
    command = ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)]
    probe = json.loads(subprocess.check_output(command, timeout=60))
    return traversal_probe_signature(probe)


def validate_traversal_capture(directory, exported, decode=False):
    """Check retained capture facts and bind them to this checkout/export source.

    Raw sequential PNGs need not be distributed. Their recorded sequence and the
    decoded movie frame count are checked; the five retained stills are byte-checked.
    A source comparison is required even for a self-consistent release inventory.
    """
    render_path = member(directory, "traversal-render-review.json")
    render = json.loads(render_path.read_text())
    video = json.loads(member(directory, "traversal-video.json").read_text())
    require(render.get("complete") is True and not render.get("failure") and render.get("preview") is False,
            "Traversal capture is incomplete, failed or preview-only")
    require(render.get("kind") == "actual-staged-native-traversal-input" and
            render.get("renderer") == "forward_plus" and render.get("display") not in (None, "", "headless"),
            "Traversal capture does not identify an actual Forward+ display")
    require((render.get("expected_frames"), render.get("take_physics_ticks"), render.get("physics_hz"),
             render.get("fps"), render.get("width"), render.get("height")) == (180, 360, 60, 30, 1280, 720),
            "Traversal capture frame/tick count, timing or dimensions differ")
    frames = render.get("frames")
    require(isinstance(frames, list) and len(frames) == 180, "Traversal capture omits sequential frames")
    start = render.get("take_start_tick")
    require(type(start) is int and start >= 0, "Traversal capture starting tick is invalid")
    previous_draw = -1

    def image_metadata(image, expected_name):
        require(image.get("file") == expected_name and (image.get("width"), image.get("height")) == (1280, 720),
                "Traversal image name/dimensions differ")
        require(isinstance(image.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", image["sha256"]),
                "Traversal image lacks a SHA-256 record")
        require(all(type(image.get(key)) is int and image[key] > 0
                    for key in ("draw_calls", "rendered_objects", "rendered_primitives")),
                "Traversal image lacks actual renderer counters")

    for index, frame in enumerate(frames):
        require(frame.get("index") == index and frame.get("physics_tick_delta") == 2 and
                frame.get("physics_tick") == start + 2 * (index + 1), "Traversal capture tick sequence is discontinuous")
        require(type(frame.get("render_frame")) is int and frame["render_frame"] > previous_draw,
                "Traversal rendered frame counter did not advance")
        previous_draw = frame["render_frame"]
        require(frame.get("finite") is True and isinstance(frame.get("pose_sha256"), str) and
                re.fullmatch(r"[0-9a-f]{64}", frame["pose_sha256"]), "Traversal skeletal pose evidence is invalid")
        for key, expected in (("presentation_seconds", index / 30), ("sample_end_simulation_seconds", (index+1) / 30)):
            value = frame.get(key)
            require(type(value) in (int, float) and math.isfinite(value) and abs(value-expected) < 1e-5,
                    "Traversal frame timing differs: " + key)
        image_metadata(frame["image"], f"frame-{index:05d}.png")
    outcomes = render.get("outcomes", {})
    require(all(outcomes.get(key) is True for key in ("grapple", "flight", "visible_rope", "pose_overlay", "pose_finite")),
            "Traversal capture did not observe required mechanics/finite poses")
    stills = render.get("stills", [])
    require(len(stills) == 5 and {row["image"]["file"] for row in stills} == TRAVERSAL_STILLS,
            "Traversal capture must retain the five specified stills")
    for still in stills:
        image = still["image"]
        image_metadata(image, image["file"])
        path = member(directory, image["file"])
        with path.open("rb") as stream:
            header = stream.read(24)
        require(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and
                struct.unpack(">II", header[16:24]) == (1280, 720) and digest(path) == image["sha256"],
                "Traversal retained PNG differs: " + image["file"])
        if image["file"] == "still-05-actual-take-hud.png":
            require(still.get("take_frame") == 145 and image["sha256"] == frames[145]["image"]["sha256"],
                    "Traversal HUD still is not the recorded take frame")
    require(render.get("army_staging", {}).get("observed_queued_attack") is True,
            "Traversal army still lacks a recorded engagement")

    source_hashes = render.get("source_sha256", {})
    expected_sources = set(CAPTURE_FIXED_SOURCES)
    for folder in ("scripts", "scenes", "assets"):
        expected_sources.update(path.relative_to(PROJECT).as_posix() for path in (PROJECT / folder).rglob("*") if path.is_file())
    require(CAPTURE_REQUIRED_RUNTIME <= expected_sources and isinstance(source_hashes, dict) and
            set(source_hashes) == {"res://" + name for name in expected_sources},
            "Traversal capture source inventory differs from the checkout")
    export_files = exported.get("source", {}).get("files", {})
    shared = {name for name in expected_sources if name == "project.godot" or name.split("/")[0] in ("scripts", "scenes", "assets")}
    export_shared = {name for name in export_files if name == "project.godot" or name.split("/")[0] in ("scripts", "scenes", "assets")}
    require(shared == export_shared, "Traversal capture/export runtime source sets differ")
    for name in expected_sources:
        actual = record(member(PROJECT, name))
        require(source_hashes["res://" + name] == actual["sha256"], "Traversal captured source differs from checkout: " + name)
        if name in shared:
            require(export_files[name] == actual, "Traversal exported source differs from captured checkout: " + name)
    movie = member(directory, "yuga-traversal-preview.mp4")
    require(video.get("complete") is True and video.get("file") == movie.name and
            record(movie) == {key: video[key] for key in ("bytes", "sha256")}, "Traversal movie bytes or completion differ")
    require(video.get("capture_report_sha256") == digest(render_path), "Traversal movie links a different capture report")
    signature = traversal_probe_signature(video.get("probe", {}))
    if decode:
        actual_signature = probe_traversal_movie(movie)
        require(actual_signature == signature, "Fresh decoded traversal video differs from its recorded probe")
    return {"passed":True,"frames":180,"physics_ticks":360,"retained_stills":5,"source_files":len(expected_sources),
            "video":record(movie),"decoded_this_run":decode,
            "scope":"Full recorded input take, retained still bytes and current/exported source verified. No rerender, OS-input, audio or realtime-performance claim."}


def validate_siege_capture(directory, exported, decode=False):
    render_path = member(directory, "siege-render-review.json")
    render = json.loads(render_path.read_text())
    video = json.loads(member(directory, "siege-video.json").read_text())
    require(render.get("complete") is True and not render.get("failure"), "Siege capture failed or incomplete")
    require(render.get("renderer") == "forward_plus" and str(render.get("display", "")).lower() == "x11", "Siege capture lacks actual display")
    require((render.get("fps"), render.get("physics_hz"), render.get("take_physics_ticks"), render.get("width"), render.get("height")) == (30,60,360,1280,720), "Siege capture timing/resolution differs")
    require(render.get("time_scale") == 1.0, "Siege time scale differs")
    require(all(render.get("outcomes", {}).get(key) is True for key in ("windup","impact","vehicles_moved","finite")), "Siege mechanics missing from capture")
    frames = render.get("frames", [])
    start = render.get("take_start_tick")
    require(len(frames) == 180 and type(start) is int and start >= 0, "Siege frame count/start invalid")
    require(member(directory,"SIEGE-RENDER-REVIEW.md").is_file(), "Siege review is missing")
    previous_draw = -1
    for index, frame in enumerate(frames):
        require(frame.get("index") == index and frame.get("physics_tick_delta") == 2 and frame.get("physics_tick") == start+2*(index+1) and frame.get("finite") is True, "Siege frame sequence invalid")
        image = frame.get("image", {})
        require(type(frame.get("render_frame")) is int and frame["render_frame"] > previous_draw, "Siege render counter regressed")
        previous_draw = frame["render_frame"]
        require(image.get("file") == f"frame-{index:05d}.png" and (image.get("width"),image.get("height")) == (1280,720), "Siege frame image metadata invalid")
        require(isinstance(image.get("sha256"),str) and re.fullmatch(r"[a-f0-9]{64}",image["sha256"]) is not None, "Siege frame hash invalid")
        require(all(type(image.get(key)) is int and image[key] > 0 for key in ("draw_calls","rendered_objects","rendered_primitives")), "Siege frame lacks actual render counters")
        if index in SIEGE_SELECTED_FRAMES:
            path = member(directory, f"siege-frame-{index:05d}.png")
            header = path.read_bytes()[:24]
            require(header[:8] == b"\x89PNG\r\n\x1a\n" and len(header) == 24 and struct.unpack(">II",header[16:24]) == (1280,720) and digest(path) == image.get("sha256"), "Retained siege frame differs")
    expected = set(CAPTURE_FIXED_SOURCES) | {"tools/capture-siege.gd","tools/run-siege-capture.py"}
    for folder in ("scripts","scenes","assets"):
        expected.update(path.relative_to(PROJECT).as_posix() for path in (PROJECT/folder).rglob("*") if path.is_file())
    sources = render.get("source_sha256", {})
    require(set(sources) == {"res://"+name for name in expected}, "Siege source inventory differs")
    exported_sources = exported.get("source", {}).get("files", {})
    shared = {name for name in expected if name == "project.godot" or name.split("/")[0] in ("scripts","scenes","assets")}
    require(shared == {name for name in exported_sources if name == "project.godot" or name.split("/")[0] in ("scripts","scenes","assets")}, "Siege exported runtime set differs")
    for name in expected:
        actual = record(member(PROJECT,name))
        require(sources["res://"+name] == actual["sha256"], "Siege source changed: "+name)
        if name in shared: require(exported_sources.get(name) == actual, "Siege exported source changed: "+name)
    movie = member(directory,"yuga-siege-preview.mp4")
    require(video.get("complete") is True and video.get("file") == movie.name and video.get("sha256") == digest(movie) and video.get("bytes") == movie.stat().st_size, "Siege video bytes differ")
    require(video.get("capture_report_sha256") == digest(render_path), "Siege movie links different capture")
    signature = traversal_probe_signature(video.get("probe", {}))
    if decode: require(probe_traversal_movie(movie) == signature, "Decoded siege media differs")
    return {"passed":True,"frames":180,"physics_ticks":360,"source_files":len(expected),"decoded_this_run":decode}


def stage(args):
    require(TAG.fullmatch(args.tag), "Unexpected release tag")
    commit = git("rev-parse", "HEAD")
    require(commit == git("rev-parse", args.commit + "^{commit}"), "Checkout differs from requested release commit")
    require(commit == git("rev-parse", "refs/tags/" + args.tag + "^{commit}"), "Release tag differs from checkout")
    validate_evidence()
    args.output.mkdir(parents=True, exist_ok=True)
    require(not any(args.output.iterdir()), "Release output must be empty")
    sources = {}

    def copy(path, name=None):
        name = name or path.name
        require(NAME.fullmatch(name) and name not in sources, "Unsafe/duplicate release filename")
        require(path.is_file() and not path.is_symlink(), "Missing release input: " + str(path))
        shutil.copyfile(path, args.output / name)
        sources[name] = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

    package = json.loads((args.build / "native-package-manifest.json").read_text())
    exported = json.loads((args.build / "native-export-manifest.json").read_text())
    require(package["git"]["head"] == commit and exported["git"]["head"] == commit, "Packages were built from a different commit")
    for platform in ("linux", "windows"):
        row = package["packages"][platform]
        require(NAME.fullmatch(row["filename"]), "Unsafe package filename")
        path = args.build / row["filename"]
        require(record(path) == {key: row[key] for key in ("bytes", "sha256")}, "Portable ZIP changed after package validation")
        copy(path)
    for name in ("native-package-manifest.json", "native-export-manifest.json"):
        copy(args.build / name)
    copy(args.engines / "engine-downloads.json")
    for name in CHECKS + (TRAVERSAL_CHECKS if traversal_release(args.tag) else ()):
        path = args.checks / (name + ".json")
        require(json.loads(path.read_text()).get("passed") is True, "Required release check failed/missing: " + name)
        copy(path, "ci-" + name + ".json")
    archive = json.loads((FILM / "archive-manifest.json").read_text())
    for name in archive["files"]:
        if "/" not in name and (name.endswith(".json") or name.endswith(".mp4")):
            copy(FILM / name)
    copy(FILM / "archive-manifest.json")
    copy(FILM / "REVIEW.md", "FILM-REVIEW.md")
    if traversal_release(args.tag):
        copy(PROJECT / "assets/audio/traversal/lane-procession-loop.wav")
        copy(PROJECT / "NOTICE/TRAVERSAL-AUDIO-PROVENANCE.json")
        copy(PROJECT / "docs/TRAVERSAL_ARMY_VERIFICATION.md", "TRAVERSAL-VERIFICATION.md")
        capture = PROJECT / TRAVERSAL_CAPTURE_DIRECTORY
        validate_traversal_capture(capture, exported, decode=True)
        archive_names = (TRAVERSAL_CAPTURE_ASSETS - {"TRAVERSAL-RENDER-REVIEW.md"}) | {"REVIEW.md"}
        captured_sources = json.loads(member(capture, "traversal-render-review.json").read_text())["source_sha256"]
        tracked = [str(member(capture, name).relative_to(REPO)) for name in sorted(archive_names)]
        tracked += [str(member(PROJECT, name.removeprefix("res://")).relative_to(REPO)) for name in sorted(captured_sources)]
        git("ls-files", "--error-unmatch", "--", *tracked)
        require(not git("diff", "--name-only", "HEAD", "--", *tracked), "Traversal capture/source differs from committed checkout")
        for name in sorted(archive_names):
            copy(capture / name, "TRAVERSAL-RENDER-REVIEW.md" if name == "REVIEW.md" else name)
    if siege_release(args.tag):
        capture = PROJECT / SIEGE_CAPTURE_DIRECTORY
        validate_siege_capture(capture, exported, decode=True)
        tracked = [str(member(capture,name).relative_to(REPO)) for name in sorted(SIEGE_CAPTURE_ASSETS)]
        git("ls-files", "--error-unmatch", "--", *tracked)
        require(not git("diff", "--name-only", "HEAD", "--", *tracked), "Siege capture differs from committed checkout")
        for name in sorted(SIEGE_CAPTURE_ASSETS): copy(capture/name)
        copy(PROJECT/"docs/SIEGE_MILESTONE.md", "SIEGE-MILESTONE.md")
        copy(PROJECT/"assets/audio/siege/provenance.json", "SIEGE-AUDIO-PROVENANCE.json")
    notes = PROJECT / ("docs/RELEASE_TRAVERSAL_ARMIES.md" if traversal_release(args.tag) else "docs/RELEASE_CONFLUENCE_DUEL.md")
    text = notes.read_text() if notes.exists() else (
        "# YUGA — Confluence duel preview\n\nDownload yuga-confluence-duel.mp4 for the original 24-second film. "
        "Extract either native ZIP and run launch.sh (Linux) or launch.bat (Windows). Windows is packaged, not execution-verified here.\n\n"
        "This is a scripted film, offline world explorer and training preview. Full native multiplayer and commercial visual parity remain open work. "
        "Floor aliasing and animation/art limitations remain. See FILM-REVIEW.md.\n")
    text += (f"\n\nPackages were rebuilt and checked at `{commit}`. The MP4 and archived render reports retain their original captured source hashes; "
             "later tested playback fixes can differ from captured source. CI checks decoded media/audio correspondence and native headless scenarios; "
             "it does not rerender the film, listen to its sound, run Windows or measure hardware-GPU performance.\n")
    if traversal_release(args.tag):
        text += ("\nThe separate yuga-traversal-preview.mp4 contains 180 consecutive rendered frames (six seconds at simulated 30 FPS). "
                 "Its captured source inventory matches this checkout and the shared exported runtime sources. Five retained stills include separately staged city/army views. "
                 "The traversal video is silent; real OS-input testing and hardware performance are separate evidence.\n")
    (args.output / "RELEASE-NOTES.md").write_text(text)
    sources["RELEASE-NOTES.md"] = "Generated release scope with committed notes when available"
    files = {name: record(args.output / name) for name in sorted(sources)}
    inventory = {"schema": 1, "tag": args.tag, "commit": commit, "prerelease": True,
                 "files": files, "sources": sources,
                 "scope": "Fresh tagged native packages plus unchanged archived movie; capture-source and current-package provenance intentionally remain separate."}
    write_json(args.output / "release-manifest.json", inventory)
    checksums = {**files, "release-manifest.json": record(args.output / "release-manifest.json")}
    (args.output / "SHA256SUMS").write_text("".join(f"{row['sha256']}  {name}\n" for name, row in sorted(checksums.items())))
    return verify(args.output, args.tag, commit)


def verify(directory, tag, commit):
    require(TAG.fullmatch(tag), "Unexpected release tag")
    inventory = json.loads(member(directory, "release-manifest.json").read_text())
    require(inventory["tag"] == tag and inventory["commit"] == commit and inventory["prerelease"] is True, "Release identity mismatch")
    expected = set(inventory["files"]) | {"release-manifest.json", "SHA256SUMS"}
    require({p.name for p in directory.iterdir()} == expected, "Release asset set differs from manifest")
    for name, row in inventory["files"].items():
        require(NAME.fullmatch(name), "Unsafe release filename")
        require(record(member(directory, name)) == row, "Release asset checksum mismatch: " + name)
    if traversal_release(tag):
        required = {"native-package-manifest.json", "native-export-manifest.json", "engine-downloads.json",
                    "RELEASE-NOTES.md", "TRAVERSAL-VERIFICATION.md", "TRAVERSAL-AUDIO-PROVENANCE.json",
                    "lane-procession-loop.wav"} | {"ci-" + name + ".json" for name in CHECKS + TRAVERSAL_CHECKS}
        required |= TRAVERSAL_CAPTURE_ASSETS
        require(required <= set(inventory["files"]), "Feature release omits required assets/reports")
        for name in CHECKS + TRAVERSAL_CHECKS:
            require(json.loads(member(directory, "ci-" + name + ".json").read_text()).get("passed") is True,
                    "Feature release report failed: " + name)
        packages = json.loads(member(directory, "native-package-manifest.json").read_text())
        exported = json.loads(member(directory, "native-export-manifest.json").read_text())
        validate_traversal_capture(directory, exported)
        if siege_release(tag):
            require(SIEGE_CAPTURE_ASSETS | {"SIEGE-MILESTONE.md","SIEGE-AUDIO-PROVENANCE.json"} <= set(inventory["files"]), "Siege release omits required assets")
            validate_siege_capture(directory, exported)
        require(packages["git"]["head"] == commit and exported["git"]["head"] == commit,
                "Feature package source mismatch")
        for platform in ("linux", "windows"):
            row = packages["packages"][platform]
            require(row["filename"] == "yuga-native-" + platform + "-x86_64.zip" and row["filename"] in inventory["files"], "Missing or aliased platform package")
            require(record(member(directory, row["filename"])) == {key: row[key] for key in ("bytes", "sha256")},
                    "Platform package differs from package manifest")
        notice = json.loads(member(directory, "TRAVERSAL-AUDIO-PROVENANCE.json").read_text())
        loop = [row for row in notice["assets"] if row["asset"] == "assets/audio/traversal/lane-procession-loop.wav"]
        require(len(loop) == 1 and record(member(directory, "lane-procession-loop.wav")) ==
                {key: loop[0][key] for key in ("bytes", "sha256")}, "Audio provenance mismatch")
    rows = {**inventory["files"], "release-manifest.json": record(directory / "release-manifest.json")}
    expected_sums = "".join(f"{row['sha256']}  {name}\n" for name, row in sorted(rows.items()))
    require(member(directory, "SHA256SUMS").read_text() == expected_sums, "Checksum inventory differs")
    return {"passed": True, "tag": tag, "commit": commit, "assets": len(expected)}


def verify_remote_tag(repository, tag, commit):
    endpoint = "repos/" + repository + "/git/ref/tags/" + urllib.parse.quote(tag, safe="")
    response = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, check=True)
    obj = json.loads(response.stdout)["object"]
    # Git refs may point directly to commits or to annotated tag objects.
    for _ in range(8):
        if obj["type"] == "commit":
            require(obj["sha"] == commit, "Remote release tag differs from verified artifact")
            return
        require(obj["type"] == "tag" and re.fullmatch(r"[0-9a-f]{40}", obj["sha"]), "Unexpected remote tag object")
        response = subprocess.run(["gh", "api", "repos/" + repository + "/git/tags/" + obj["sha"]], capture_output=True, text=True, check=True)
        obj = json.loads(response.stdout)["object"]
    raise ValueError("Remote annotated tag nesting exceeds limit")


def publish(args):
    verify(args.directory, args.tag, args.commit)
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository), "Invalid GitHub repository")
    require(git("rev-parse", "HEAD") == args.commit, "Publication checkout differs from artifact")
    require(git("rev-parse", "refs/tags/" + args.tag + "^{commit}") == args.commit, "Publication tag differs from artifact")
    verify_remote_tag(args.repository, args.tag, args.commit)
    endpoint = "repos/" + args.repository + "/releases/tags/" + urllib.parse.quote(args.tag, safe="")
    existing = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if existing.returncode == 0:
        release = json.loads(existing.stdout)
        require(release["draft"] is True, "Refusing to modify an already published release")
        require(release["target_commitish"] == args.commit, "Existing draft targets a different commit")
    else:
        require("HTTP 404" in existing.stderr, "Cannot determine release state; refusing publication")
        subprocess.run(["gh", "release", "create", args.tag, "--repo", args.repository,
                        "--draft", "--prerelease", "--verify-tag", "--target", args.commit,
                        "--title", ("YUGA traversal and lane armies — native preview" if traversal_release(args.tag) else "YUGA Confluence duel — native preview"),
                        "--notes-file", str(args.directory / "RELEASE-NOTES.md")], check=True)
    assets = sorted(str(path) for path in args.directory.iterdir())
    subprocess.run(["gh", "release", "upload", args.tag, "--repo", args.repository, "--clobber", *assets], check=True)
    with tempfile.TemporaryDirectory(prefix="yuga-release-download-") as temporary:
        subprocess.run(["gh", "release", "download", args.tag, "--repo", args.repository,
                        "--dir", temporary, "--pattern", "*"], check=True)
        downloaded = Path(temporary)
        verify(downloaded, args.tag, args.commit)
        require({path.name for path in downloaded.iterdir()} == {path.name for path in args.directory.iterdir()}, "Downloaded asset set differs from the verified build artifact")
        for original in args.directory.iterdir():
            require(record(downloaded / original.name) == record(original), "Downloaded asset differs from the verified build artifact: " + original.name)
    verify_remote_tag(args.repository, args.tag, args.commit)
    # Final fallible mutation only after remote asset-set and byte verification.
    subprocess.run(["gh", "release", "edit", args.tag, "--repo", args.repository,
                    "--draft=false", "--prerelease", "--latest=false"], check=True)
    return {"published": True, "url": f"https://github.com/{args.repository}/releases/tag/{args.tag}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install-engines")
    install.add_argument("--destination", type=Path, required=True)
    evidence = commands.add_parser("validate-evidence")
    evidence.add_argument("--working-tree", action="store_true", help="Local precommit review only; CI omits this")
    evidence.add_argument("--report", type=Path, required=True)
    staging = commands.add_parser("stage")
    for name in ("build", "engines", "checks", "output"):
        staging.add_argument("--" + name, type=Path, required=True)
    for name in ("tag", "commit"):
        staging.add_argument("--" + name, required=True)
    for name in ("verify", "publish"):
        command = commands.add_parser(name)
        command.add_argument("--directory", type=Path, required=True)
        command.add_argument("--tag", required=True)
        command.add_argument("--commit", required=True)
        if name == "publish":
            command.add_argument("--repository", required=True)
    args = parser.parse_args()
    if args.command == "install-engines": result = install_engines(args.destination.resolve())
    elif args.command == "validate-evidence":
        result = validate_evidence(args.working_tree)
        write_json(args.report, result)
    elif args.command == "stage": result = stage(args)
    elif args.command == "verify": result = verify(args.directory, args.tag, args.commit)
    else: result = publish(args)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(f"Release stopped: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
