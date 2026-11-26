"""Package the committed map art and authoring inputs for offline use."""

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo


STUDIO = Path(__file__).resolve().parents[1]
GAME = "games/yuga-native"
ART = GAME + "/art"
ATLAS = GAME + "/docs/design/ember-rite-5v5/atlas"


def painting_masters(originals, output):
    """Collect the original image outputs by digest and cut all 53 at their documented bounds."""
    from PIL import Image

    concepts = STUDIO / "concepts"
    index = json.loads((concepts / "index.json").read_text())
    hero = json.loads((concepts / "hero-brief.json").read_text())
    digests = {board["source_png_sha256"] for board in index["boards"]} | {hero["original_png_sha256"]}
    found = {}
    for source in sorted(originals.glob("*.png")):
        digest = sha256(source.read_bytes()).hexdigest()
        if digest in digests:
            found[digest] = source
    if found.keys() != digests:
        raise FileNotFoundError(
            "Missing the following original PNG hashes: " + ", ".join(sorted(digests - found.keys()))
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:

        def add(name, data, compression=ZIP_STORED):
            entry = ZipInfo("Mandala-Rift-Paintings/" + name)
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compress_type=compression)

        add("hero.png", found[hero["original_png_sha256"]].read_bytes())
        add("prompts/hero-brief.json", (concepts / "hero-brief.json").read_bytes(), ZIP_DEFLATED)
        add("prompts/index.json", (concepts / "index.json").read_bytes(), ZIP_DEFLATED)
        count = 0
        for board in index["boards"]:
            source = found[board["source_png_sha256"]]
            add("boards/" + board["id"] + ".png", source.read_bytes())
            with Image.open(source) as original:
                if original.size != (board["width"], board["height"]):
                    raise ValueError("Mismatched original dimensions for " + board["id"])
                for key in board["items"]:
                    item = index["items"][key]
                    crop = original.crop(item["source_box"])
                    if crop.size != (item["width"], item["height"]):
                        raise ValueError("Crop dimensions differ for " + key)
                    buffer = io.BytesIO()
                    crop.save(buffer, "PNG")
                    add("elements/" + key + ".png", buffer.getvalue())
                    count += 1
        if count != len(index["items"]):
            raise ValueError("Some painted elements did not have a source board")
        add(
            "READ-ME-FIRST.txt",
            "hero.png is the district panorama. boards/ contains the original generated PNGs. "
            "elements/ contains lossless crops for all subjects. prompts/ records their board, pixel coordinates, "
            "descriptions, exact original image prompts and source hashes.\n",
            ZIP_DEFLATED,
        )
    with ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError("A painting failed ZIP integrity verification")
    print(f"{len(index['boards'])} original boards, one panorama, {count} lossless subject PNGs")


def package(revision, output):
    repo = Path(
        subprocess.check_output(
            ["git", "-C", str(STUDIO), "rev-parse", "--show-toplevel"], text=True
        ).strip()
    )
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--end-of-options", revision + "^{commit}"],
        text=True,
    ).strip()
    message = """Mandala Rift | YUGA environment art

Open games/yuga-native/art/mandala-map-studio/mandala-rift-artbook.pdf for the illustrated guide.
Open mandala-rift.blend in Blender or import a single file from models/ into your engine.
To browse offline, run python3 -m http.server 8000 from games/yuga-native/art/
and visit http://localhost:8000/. The film and the individual clips live in mandala-map-studio/.
The README in that directory explains the prompt ledger, registered origins and rebuild steps.

Web edition: https://occult-kranti.github.io/ANDOLAN/production/mandala-art/
Source revision: """
    inputs = [
        ART + "/mandala-map-studio",
        ART + "/ember-rite-5v5",
        ART + "/reuse-library/yuga-world-elements.blend",
        ART + "/reuse-library/README.md",
        ART + "/reuse-library/symbols/DejaVu-LICENSE.txt",
        GAME + "/NOTICE/Noto-fonts/COPYRIGHT.txt",
        GAME + "/docs/design/mandala-rift-5v5/concept-sketch.png",
        GAME + "/tools/research/prepare-gltf-validator.py",
        GAME + "/tools/research/check-gltf.mjs",
        GAME + "/docs/design/ember-rite-5v5/ROUND_AND_TECH.md",
        ATLAS + "/README.md",
        ATLAS + "/audit.py",
        ATLAS + "/maps/mandala.json",
        ATLAS + "/maps/mandala.md",
        ATLAS + "/massing/architecture.py",
        ATLAS + "/massing/architecture-checks.md",
        ATLAS + "/massing/mandala.glb",
        ATLAS + "/massing/mandala-architecture.glb",
        ATLAS + "/RESEARCH_ROUNDS.md",
        ATLAS + "/measurements.md",
        ATLAS + "/blueprints/mandala.svg",
        ATLAS + "/blueprints/mandala-encounters.svg",
        ATLAS + "/blueprints/mandala-architecture.svg",
    ]
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "archive",
            "--format=zip",
            "--prefix=Mandala-Rift/",
            "--add-virtual-file=Mandala-Rift/READ-ME-FIRST.txt:" + message + commit + "\n",
            "-o",
            str(output),
            commit,
            "--",
            *inputs,
        ],
        check=True,
    )
    web = GAME + "/tools/build-observatory/web/"
    siblings = {
        "media/NotoSans-Regular.ttf": web + "media/NotoSans-Regular.ttf",
        "media/NotoSerif-Regular.ttf": web + "media/NotoSerif-Regular.ttf",
        "viewer/favicon.svg": web + "viewer/favicon.svg",
        "ember-rite/rehearsal.html": ATLAS + "/rehearsal.html",
    }
    with ZipFile(output, "a") as archive:
        folder = "Mandala-Rift/" + ART + "/"
        stamp = archive.getinfo(folder + "mandala-map-studio/index.html").date_time

        def append(filename, data):
            entry = ZipInfo(folder + filename, stamp)
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compress_type=ZIP_DEFLATED, compresslevel=6)

        for alias, source in siblings.items():
            data = subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{source}"])
            append(alias, data)
        append(
            "index.html",
            """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mandala Rift | Offline collection</title>
<style>body{max-width:34rem;margin:10vh auto;padding:1rem;background:#f7f1e6;color:#193633;font:1.15rem/1.7 Georgia,serif}a{color:#804a22}</style>
<main><h1>Mandala Rift</h1><p><a href="mandala-map-studio/">Explore the map art</a></p>
<p><a href="ember-rite/rehearsal.html?map=mandala">Walk the district in the solo rehearsal</a></p>
<p><a href="https://occult-kranti.github.io/ANDOLAN/production/">Open the online production dashboard</a></p></main></html>""",
        )
    with ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError("A packaged file failed its ZIP integrity check")
        base = "Mandala-Rift/" + ART + "/mandala-map-studio/"
        required = [
            "mandala-rift-artbook.pdf",
            "mandala-rift.blend",
            "mandala-rift.glb",
            "tour.mp4",
            "verification.json",
            "index.html",
            "assembly/parts.json",
            "models/index.json",
        ]
        for name in ["Mandala-Rift/READ-ME-FIRST.txt", *[base + f for f in required]]:
            if name not in archive.namelist():
                raise ValueError("Missing packaged file " + name)
        print(f"{len(archive.filelist)} entries, {output.stat().st_size:,} bytes, source {commit}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD", help="Committed source to package")
    parser.add_argument("--out", required=True, type=Path, help="Destination ZIP outside the source tree")
    parser.add_argument(
        "--painting-masters-from",
        type=Path,
        help="Build the lossless art edition from original image outputs",
    )
    options = parser.parse_args()
    if options.painting_masters_from:
        painting_masters(options.painting_masters_from, options.out)
    else:
        package(options.ref, options.out)
