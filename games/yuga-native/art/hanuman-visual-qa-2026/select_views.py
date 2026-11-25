"""Copy a named subset of a completed render set, retaining its pose and image hashes."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--views", nargs="+", required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output:
        parser.error("output must differ from source")
    record = json.loads((source / "receipt.json").read_text())
    selected = [view for view in record["views"] if view["name"] in args.views]
    if len(selected) != len(set(args.views)):
        raise ValueError("Requested view missing from receipt")
    output.mkdir(parents=True, exist_ok=True)
    for view in selected:
        path = source / view["image"]
        if digest(path) != view["sha256"]:
            raise ValueError("Input image no longer matches receipt: " + str(path))
        shutil.copyfile(path, output / view["image"])
    record["views"] = selected
    record["selection_source"] = str(source / "receipt.json")
    (output / "receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"output": str(output), "views": [v["name"] for v in selected]}, indent=2))


if __name__ == "__main__":
    main()
