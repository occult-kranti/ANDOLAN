"""Package the Blender library and the files an artist needs alongside it."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo


FILES = ("OPEN-IN-BLENDER.txt", "yuga-world-elements.blend", "blender_assets.cats.txt",
         "catalog.json", "preview.jpg", "verification.json", "symbols/DejaVu-LICENSE.txt",
         "symbols/DejaVuSans-Bold-symbols.ttf", "symbols/manifest.json")


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("library_dir", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    folder = args.library_dir
    evidence = json.loads((folder / "verification.json").read_text())
    source = (folder / "yuga-world-elements.blend").read_bytes()
    if hashlib.sha256(source).hexdigest() != evidence["library_sha256"]:
        raise ValueError("The library differs from its verified artifact")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.output.parent) as scratch:
        candidate = Path(scratch) / "elements.zip"
        with ZipFile(candidate, "w") as bundle:
            for name in FILES:
                entry = ZipInfo("YUGA/" + name)
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                payload = (folder / name).read_bytes()
                bundle.writestr(entry, payload, compress_type=ZIP_STORED if name.endswith(".blend") else ZIP_DEFLATED)
        with ZipFile(candidate) as bundle:
            if bundle.testzip() or any(bundle.read("YUGA/" + n) != (folder / n).read_bytes() for n in FILES):
                raise ValueError("Invalid Blender distribution archive")
        candidate.replace(args.output)


if __name__ == "__main__":
    main()
