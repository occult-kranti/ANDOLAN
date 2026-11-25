"""Assemble the reviewed art, editable rigs, full scripts and offline viewer."""

import argparse
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import tempfile
from urllib.parse import quote, unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

PACK = Path(__file__).resolve().parents[1]
REPO = PACK.parents[3]
DEFAULT_NAME = "YUGA-Four-Hero-Studio.zip"
PROJECT = "https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-hanuman-trial/"
HEROES = ("hanuman", "shiva", "rama", "krishna")


def local_markdown(path, paths):
    """Preserve package links and send repo-only source links to the online checkout."""

    def rewrite(match):
        uri = urlsplit(match[1])
        if uri.scheme or uri.netloc or not uri.path:
            return match[0]
        target = (path.parent / unquote(uri.path)).resolve()
        if target in paths or (
            target.is_dir() and any(p.is_relative_to(target) for p in paths)
        ):
            return match[0].replace("?raw=true", "")
        if not target.is_relative_to(REPO):
            raise ValueError(f"Unexpected markdown target {target} in {path}")
        url = PROJECT + quote(target.relative_to(REPO).as_posix())
        return "](" + url + ("#" + uri.fragment if uri.fragment else "") + ")"

    return re.sub(r"\]\(([^)]+)\)", rewrite, path.read_text()).encode()


def files():
    names = [
        PACK / p
        for p in ("index.html", "chapters.js", "animator-book.pdf", "motion-index.json")
    ]
    names.extend(PACK.glob("*.md"))
    for folder in (
        "media",
        "models",
        "blender",
        "scripts",
        "prompts",
        "viewer",
        "evidence",
        "tools",
    ):
        for path in (PACK / folder).rglob("*"):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
                and not path.name.startswith(".")
            ):
                names.append(path)
    return set(names)


def pack(output):
    paths = files()
    for hero in HEROES:
        for rel in (
            f"models/{hero}.glb",
            f"scripts/{hero}.md",
            f"media/video/{hero}.mp4",
            f"media/video/{hero}.json",
            f"media/stills/{hero}.webp",
            f"media/art/{hero}-beats.webp",
        ):
            if PACK / rel not in paths:
                raise ValueError(f"Missing {rel}")
    indices = json.loads((PACK / "motion-index.json").read_text())["heroes"]
    blend = json.loads((PACK / "blender/manifest.json").read_text())
    scenes = {p["hero"]: p for p in blend["projects"]}
    for hero in HEROES:
        digest = sha256((PACK / indices[hero]["file"]).read_bytes()).hexdigest()
        film = json.loads((PACK / f"media/video/{hero}.json").read_text())
        scene = scenes[hero]
        indexed_scene = PACK / "blender" / scene["file"]
        if (
            sha256(indexed_scene.read_bytes()).hexdigest() != scene["sha256"]
            or scene["source_glb_sha256"] != digest
        ):
            raise ValueError(
                f"{hero} editable Blender project differs from the verified source"
            )
        if digest != indices[hero]["sha256"] or digest != film["source_sha256"]:
            raise ValueError(f"{hero} rig differs from the filmed model")
    credits = {
        "notices/MakeHuman-asset-license.md": REPO
        / "games/yuga-native/NOTICE/MAKEHUMAN-ASSET-LICENSE.md",
        "notices/Native-assets.md": REPO / "games/yuga-native/NOTICE/ASSET-NOTICE.md",
        "notices/Rama-hero-provenance.json": REPO
        / "games/yuga-native/NOTICE/RAMA-HERO-PROVENANCE.json",
        "notices/MakeHuman-source.json": REPO
        / "games/yuga/art/sources/makehuman/manifest.json",
    }
    contents = {
        p.relative_to(PACK).as_posix(): (
            local_markdown(p, paths)
            if p.suffix == ".md" and p.parent.name != "notices"
            else p.read_bytes()
        )
        for p in paths
    }
    contents.update({name: p.read_bytes() for name, p in credits.items()})
    contents["START_HERE.txt"] = (
        "Open index.html to browse the artwork, PDFs and films. For the 3D rig inspector,\n"
        "select a hero and choose its GLB from the models folder if your browser asks.\n"
        "To load each rig automatically, open a terminal in this extracted folder and run:\n"
        "  python3 -m http.server 8000 --bind 127.0.0.1\n"
        "Then visit http://127.0.0.1:8000/ and choose a hero. No internet connection is needed.\n"
        "For editing, open blender/<hero>.blend for each full scene or import the GLBs from models/.\n"
        "The 48 embedded tracks are listed with their source timing in motion-index.json.\n"
        "The PDF contains all four complete animation scripts. Studio production tools that use\n"
        "shared YUGA source assets run from the repository, linked from README.md.\n"
    ).encode()
    contents["SHA256SUMS.txt"] = "".join(
        sha256(data).hexdigest() + "  " + name + "\n"
        for name, data in sorted(contents.items())
    ).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        dest = Path(temp) / output.name
        with ZipFile(dest, "w") as archive:
            for name, data in sorted(contents.items()):
                archive.writestr(
                    ZipInfo(name), data, compress_type=ZIP_DEFLATED, compresslevel=6
                )
        with ZipFile(dest) as archive:
            if archive.testzip() is not None:
                raise ValueError("Archive integrity failure")
            if any(archive.read(n) != data for n, data in contents.items()):
                raise ValueError("Archive member mismatch")
        os.replace(dest, output)
    print(
        f"{len(contents)} files, {output.stat().st_size} bytes, SHA-256 {sha256(output.read_bytes()).hexdigest()}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_NAME))
    pack(parser.parse_args().output.resolve())
