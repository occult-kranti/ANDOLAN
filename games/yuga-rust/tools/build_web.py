#!/usr/bin/env python3
"""Build the same Rust drill as a self-contained, offline desktop-browser game."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
NATIVE = ROOT / "games/yuga-native"
BROWSER = ROOT / "games/yuga"
WEB = PROJECT / "web"
TARGET = "wasm32-unknown-unknown"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def capture(args):
    return subprocess.check_output(args, cwd=PROJECT, text=True)

def playable_hanuman(stage):
    finish = NATIVE / "art/hanuman-hero-finish/models/hanuman-enhanced.glb"
    if finish.is_file():
        model = finish
        edition = "hero-finish"
    else:
        base = NATIVE / "assets/heroes/hanuman"
        model = stage / "hanuman.glb"
        subprocess.run(
            ["cargo", "run", "--locked", "--bin", "hero_export", "--",
             base / "hanuman.glb", base / "hanuman-ability-motion.tres", model],
            cwd=PROJECT, check=True,
        )
        edition = "native-motion-export"
    with model.open("rb") as handle:
        magic, version, size, size_json, chunk = struct.unpack("<4sIII4s", handle.read(20))
        if (magic, version, size, chunk) != (b"glTF", 2, model.stat().st_size, b"JSON"):
            raise ValueError(f"Invalid Hanuman GLB: {model}")
        header = json.loads(handle.read(size_json))
    tracks = {action["name"] for action in header.get("animations", [])}
    rules = json.loads((NATIVE / "assets/design/hanuman-ability-kit.json").read_text())
    required = {"idle", "run", "defeat", *(r["motion"] for r in rules["abilities"])}
    if not header.get("skins") or not required <= tracks:
        raise ValueError(f"Hanuman needs a skin and all match actions, missing {required - tracks}")
    return model, {"edition": edition, "clips": sorted(tracks)}


def notices(workspace):
    resolved = json.loads(
        capture(
            [
                "cargo",
                "metadata",
                "--locked",
                "--format-version=1",
                "--filter-platform",
                TARGET,
            ]
        )
    )
    blocks = {}
    names = []

    def include(label, content):
        content = content.strip()
        key = sha(content.encode())
        if key not in blocks:
            blocks[key] = content
        names.append(f"{label} [{key[:12]}]")

    for p in sorted(resolved["packages"], key=lambda p: (p["name"], p["version"])):
        if p["name"] == "yuga-rust":
            continue
        folder = Path(p["manifest_path"]).parent
        paths = sorted(
            f
            for f in folder.iterdir()
            if f.is_file()
            and f.name.lower().startswith(("license", "licence", "copying", "notice"))
        )
        if p.get("license_file"):
            extra = folder / p["license_file"]
            if extra.is_file() and extra not in paths:
                paths.append(extra)
        label = f"{p['name']} {p['version']} · {p.get('license') or 'upstream license file'}"
        if not paths:
            names.append(
                f"{label} · registry metadata · https://crates.io/crates/{p['name']}/{p['version']}"
            )
        for path in paths:
            include(label, path.read_text(errors="replace"))
    for label, path in {
        "OpenBF stereo limiter (MIT)": PROJECT / "src/vendor/openbf/LICENSE",
        "Rama original instrument cues": NATIVE
        / "assets/audio/rama-quality/manifest.json",
        "ws WebSocket transport": ROOT / "node_modules/ws/LICENSE",
        "PlayCanvas": ROOT / "node_modules/playcanvas/LICENSE",
        "DM Sans": ROOT / "node_modules/@fontsource/dm-sans/LICENSE",
        "Barlow Condensed": ROOT / "node_modules/@fontsource/barlow-condensed/LICENSE",
        "YUGA browser models and environment": BROWSER / "THIRD_PARTY_NOTICES.md",
        "YUGA Hanuman art": NATIVE / "art/hanuman/NOTICE.md",
        "YUGA Rama rig": NATIVE / "NOTICE/RAMA-HERO-PROVENANCE.json",
        "YUGA original cues": NATIVE / "NOTICE/HANUMAN-ABILITY-AUDIO.json",
    }.items():
        include(label, path.read_text())
    if (NATIVE / "art/hanuman-hero-finish/models/hanuman-enhanced.glb").is_file():
        include("YUGA playable Hanuman finish", "The YUGA team adapted the credited Hanuman body and native motions with a compact muzzle, revised surface textures, weighted copper guard hair and a tail recoil pass. The downloadable model retains the base asset terms listed in Hanuman asset provenance.")
    if (NATIVE / "art/hanuman-hero-finish/design/hanuman-portrait-target.webp").is_file():
        include("YUGA title illustration", "Original image-generated Hanuman title art for this game. Source and prompt: games/yuga-native/art/hanuman-hero-finish/design/PORTRAIT.md.")
    text = (
        "\n".join(names)
        + "\n\n"
        + "\n\n".join(f"[{key[:12]}]\n{value}" for key, value in blocks.items())
    )
    (workspace / "THIRD-PARTY.txt").write_text(text, encoding="utf-8")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT / "dist")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=True, parents=True)
    subprocess.run(
        ["cargo", "build", "--locked", "--release", "--target", TARGET, "--lib"],
        cwd=PROJECT,
        check=True,
    )
    metadata = json.loads(
        capture(["cargo", "metadata", "--no-deps", "--locked", "--format-version=1"])
    )
    with TemporaryDirectory(dir=out) as staging:
        stage = Path(staging)
        hero, hero_info = playable_hanuman(stage)
        cover = NATIVE / "art/hanuman-hero-finish/design/hanuman-portrait-target.webp"
        if not cover.is_file():
            cover = NATIVE / "art/hanuman/match/hanuman-keyframe-denoised.png"
        rama = stage / "rama.glb"
        subprocess.run(
            [sys.executable, PROJECT / "tools/pack_rama.py", "--lod", "far", rama],
            cwd=PROJECT,
            check=True,
        )
        runner = """require('esbuild').buildSync({entryPoints:[process.argv[1]],outfile:process.argv[2],bundle:true,minify:true,legalComments:'inline',target:'es2022',logLevel:'error'});"""
        subprocess.run(
            ["node", "-e", runner, str(WEB / "main.ts"), str(stage / "client.js")],
            cwd=ROOT,
            check=True,
        )
        host_runner = """require('esbuild').buildSync({
            entryPoints:[process.argv[1]],outfile:process.argv[2],bundle:true,platform:'node',
            format:'esm',target:'node22',external:['bufferutil','utf-8-validate'],legalComments:'inline',
            banner:{js:"import { createRequire as __roomRequire } from 'node:module'; const require = __roomRequire(import.meta.url);"}
        });"""
        subprocess.run(
            [
                "node",
                "-e",
                host_runner,
                str(PROJECT / "tools/serve_rooms.mjs"),
                str(stage / "serve_rooms.mjs"),
            ],
            cwd=ROOT,
            check=True,
        )
        (stage / "room-wasm.mjs").write_bytes(
            (PROJECT / "tools/room-wasm.mjs").read_bytes()
        )
        assets = {
            "wasm": Path(metadata["target_directory"])
            / TARGET
            / "release/yuga_rust.wasm",
            "hero": hero,
            "rama": rama,
            "vehicles": WEB / "art/army-vehicles.glb",
            "soldier": BROWSER / "client/assets/units/soldier.glb",
            "architecture": NATIVE / "assets/world/architecture.glb",
            "nature": NATIVE / "assets/world/nature.glb",
            "cover": cover,
            "display-font": ROOT
            / "node_modules/@fontsource/barlow-condensed/files/barlow-condensed-latin-600-normal.woff2",
            "body-font": ROOT
            / "node_modules/@fontsource/dm-sans/files/dm-sans-latin-400-normal.woff2",
        }
        for cue in sorted((NATIVE / "assets/audio/hanuman-trial").glob("*.wav")):
            assets["audio/" + cue.stem] = cue
        for cue in sorted((NATIVE / "assets/audio/rama-quality").glob("*.wav")):
            assets["audio/rama/" + cue.stem] = cue
        blobs = {name: path.read_bytes() for name, path in assets.items()}
        (stage / "yuga-rust.wasm").write_bytes(blobs["wasm"])
        payload = {
            "coverMime": "image/webp" if cover.suffix == ".webp" else "image/png",
            "map": json.loads(
                (NATIVE / "assets/world/confluence-map.json").read_text()
            ),
            "mixWorklet": (WEB / "mix-worklet.js").read_text(),
            "kit": json.loads(
                (NATIVE / "assets/design/hanuman-ability-kit.json").read_text()
            ),
            "ramaKit": json.loads(
                (NATIVE / "assets/design/rama-ability-kit.json").read_text()
            ),
            "notices": notices(stage),
            "blobs": {
                name: base64.b64encode(raw).decode("ascii")
                for name, raw in blobs.items()
            },
        }
        script = (stage / "client.js").read_text().replace("</script", r"<\/script")
        document = (
            (WEB / "index.html")
            .read_text()
            .replace("/* STYLES */", (WEB / "style.css").read_text())
            .replace("/* GAME */", script)
            .replace(
                "/* PAYLOAD */",
                json.dumps(payload, separators=(",", ":")).replace("<", r"\u003c"),
            )
        )
        filename = "yuga-rust.html"
        (stage / filename).write_text(document, encoding="utf-8")
        report = {
            "hanuman": hero_info,
            "cover": {"source": str(cover.relative_to(ROOT)), "mime": payload["coverMime"]},
            "rustc": capture(["rustc", "--version"]).strip(),
            "target": TARGET,
            "tick_hz": 20,
            "hosts": {
                name: sha((stage / name).read_bytes())
                for name in ["serve_rooms.mjs", "room-wasm.mjs", "yuga-rust.wasm"]
            },
            "html_sha256": sha((stage / filename).read_bytes()),
            "blobs": {
                key: {"bytes": len(raw), "sha256": sha(raw)}
                for key, raw in blobs.items()
            },
        }
        (stage / "build.json").write_text(json.dumps(report, indent=2) + "\n")
        (stage / "PLAY.txt").write_text(
            "Extract and open yuga-rust.html in a desktop browser with WebGL 2 and WebAssembly. All assets are embedded.\nIf your browser blocks local HTML, open a terminal in the extracted folder, run python3 -m http.server 8000 --bind 127.0.0.1, and visit http://127.0.0.1:8000/yuga-rust.html.\nChoose a hero and play a lane match, or choose Hanuman practice to defeat three Moon guards. Move with WASD, aim with the mouse and cast with LMB / Q / E / C / X. Advance your soldiers to the opposing core. For private duels or 3v3 rooms install Node 22.12 or newer. In this extracted folder run node serve_rooms.mjs, then open http://127.0.0.1:8787. To play across a trusted LAN, run node serve_rooms.mjs --host 0.0.0.0 and each player opens http://HOST-LAN-IP:8787. The host chooses a duel or 3v3 room and shares the code. The match starts when all two or six seats are filled. Leave the terminal running while playing. For Hanuman, click Mountain Pulse and point at the floor to see its footprint. A gold center means the landing is clear. A crossed center and the status text explain an unavailable landing. X quick-casts. Escape cancels targeting or pauses.\n"
        )
        with ZipFile(stage / "yuga-rust-confluence.zip", "w") as archive:
            for name in [
                filename,
                "PLAY.txt",
                "build.json",
                "THIRD-PARTY.txt",
                "serve_rooms.mjs",
                "room-wasm.mjs",
                "yuga-rust.wasm",
            ]:
                archive.writestr(
                    ZipInfo(name),
                    (stage / name).read_bytes(),
                    compress_type=ZIP_DEFLATED,
                    compresslevel=7,
                )
        for name in [filename, "build.json", "yuga-rust-confluence.zip"]:
            os.replace(stage / name, out / name)
        print(f"{out/filename}    {report['html_sha256']}")


if __name__ == "__main__":
    main()
