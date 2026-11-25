#!/usr/bin/env python3
"""Package the current offline reader, SQLite database, executable notebook and notices."""

from hashlib import sha256
from pathlib import Path
import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "game-resource-library.zip"
START = """Game resource library

Extract this ZIP and open library.html in a desktop or mobile browser. If your
browser blocks local HTML, run python3 -m http.server 8000 --bind 127.0.0.1
in the extracted folder, then open http://127.0.0.1:8000/library.html.
Searching all three collections works offline. Following an upstream source
or license link requires a connection.

Elements: reviewed code, graphics, rigs, UI components and authoring techniques.
Asset files: SVG icon previews, authors, and glTF models with component credits.
Projects: source ports, engine rebuilds and projects with catalog observations.

Open library.sqlite in DB Browser for SQLite or an FTS5-enabled SQLite client.
The rea_forks table holds the enumerated public fork metadata. Open analysis.ipynb
beside the database in Jupyter to inspect the recorded counts and SQL examples.
The evidence directory contains verification records. The notices directory
contains credits and upstream terms. Individual records carry source-specific terms.

Code, collection methods and updates:
https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-hanuman-trial/research/game-resource-library
"""


def package():
    names = [
        "library.html",
        "library.sqlite",
        "analysis.ipynb",
        "evidence/quality.json",
        "evidence/icons.json",
        "evidence/model-coverage.json",
        "evidence/source-pin-audit.json",
        "evidence/browser-qa.json",
        "notices/game-icons.txt",
        "notices/osgameclones.txt",
    ]
    for optional in (
        "evidence/button-state-contact-sheet.png",
        "search/button-states.json",
    ):
        if (ROOT / optional).exists():
            names.append(optional)
    content = {name: (ROOT / name).read_bytes() for name in names}
    content["START_HERE.txt"] = START.encode()
    manifest = "".join(
        f"{sha256(data).hexdigest()}  {path}\n"
        for path, data in sorted(content.items())
    )
    content["SHA256SUMS.txt"] = manifest.encode()
    with TemporaryDirectory(dir=ROOT) as tmp:
        archive = Path(tmp) / OUTPUT.name
        with ZipFile(archive, "w") as out:
            for path, data in sorted(content.items()):
                out.writestr(
                    ZipInfo(path), data, compress_type=ZIP_DEFLATED, compresslevel=9
                )
        with ZipFile(archive) as zipped:
            assert zipped.testzip() is None
            for path, data in content.items():
                assert sha256(zipped.read(path)).digest() == sha256(data).digest(), path
        os.replace(archive, OUTPUT)
    print(
        f"{OUTPUT.name}  {OUTPUT.stat().st_size} bytes  {sha256(OUTPUT.read_bytes()).hexdigest()}"
    )


if __name__ == "__main__":
    package()
