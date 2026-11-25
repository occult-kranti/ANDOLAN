"""Reconstruct and verify the eight public assets from this tagged studio's two archives."""
from hashlib import sha256
from pathlib import Path
from shutil import copyfileobj
from zipfile import ZipFile
import argparse
import json

ROOT = Path(__file__).resolve().parent
FOCUSED = "YUGA-Hanuman-Hero-Studio.zip"
QUARTET = "YUGA-Four-Hero-Studio.zip"
FINISH = "games/yuga-native/art/hanuman-hero-finish/media/"
MEMBERS = {
    FOCUSED: {
        "games/yuga-rust/downloads/yuga-rust-confluence.zip": "yuga-rust-confluence.zip",
        FINISH + "images/hanuman-beauty.webp": "hanuman-beauty.webp",
        FINISH + "images/matched-studies.webp": "matched-studies.webp",
        FINISH + "video/hanuman-showcase.mp4": "hanuman-showcase.mp4",
    },
    QUARTET: {"animator-book.pdf": "animator-book.pdf"},
}

def assemble(output):
    index = json.loads((ROOT / "distribution.json").read_text())
    output.mkdir(parents=True, exist_ok=True)
    for name, members in MEMBERS.items():
        destination = output / name
        with destination.open("wb") as archive:
            for part in index["parts"][name]:
                with (ROOT / part).open("rb") as chunk:
                    copyfileobj(chunk, archive)
        with ZipFile(destination) as archive:
            for member, filename in members.items():
                with archive.open(member) as source, (output / filename).open("wb") as file:
                    copyfileobj(source, file)
    with ZipFile(output / "yuga-rust-confluence.zip") as game:
        with game.open("yuga-rust.html") as source, (output / "yuga-rust.html").open("wb") as file:
            copyfileobj(source, file)
    for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines():
        expected, filename = line.split("  ")
        actual = sha256((output / filename).read_bytes()).hexdigest()
        if expected != actual:
            raise ValueError(f"Distribution checksum differs for {filename}")
    (output / "SHA256SUMS.txt").write_bytes((ROOT / "SHA256SUMS.txt").read_bytes())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    assemble(parser.parse_args().destination)
