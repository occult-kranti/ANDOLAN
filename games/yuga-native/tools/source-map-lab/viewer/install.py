"""Assemble the offline level viewer beside the built models and registered renders."""

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
from urllib.request import urlopen


PACKAGE = "https://registry.npmjs.org/three/-/three-0.180.0.tgz"
INTEGRITY = "o+qycAMZrh+TsE01GqWUxUIKR1AL0S8pq7zDkYOQw8GqfX8b8VoCKYUoHbhiX5j+7hr8XsuHDVU6+gkQJQKg9w=="
FILES = [
    "build/three.module.min.js",
    "build/three.core.min.js",
    "examples/jsm/loaders/GLTFLoader.js",
    "examples/jsm/controls/OrbitControls.js",
    "examples/jsm/utils/BufferGeometryUtils.js",
    "LICENSE",
]
TITLES = {"overview": "District overview", "site-a": "Site A", "site-b": "Site B"}


def gltf(point):
    east, north, up = point
    return [east, up, -north]


def install(root, renders, package):
    register = json.loads((renders / "cameras-and-render.json").read_text())
    views = {}
    images = []
    for key, title in TITLES.items():
        cam = register["cameras"][key]
        view = {
            "title": title,
            "eye": gltf(cam["eye_m"]),
            "target": gltf(cam["target_m"]),
        }
        for finish in ("baseline", "jade"):
            image = renders / f"{key}-{finish}.png"
            if not image.is_file():
                raise FileNotFoundError(image)
            view[finish] = f"renders/{image.name}"
            images.append(image)
        if key == "overview":
            view["span"] = cam["ortho_span_m"]
        views[key] = view
    if package is not None:
        payload = package.read_bytes()
    else:
        with urlopen(PACKAGE, timeout=60) as response:
            payload = response.read()
    if base64.b64encode(hashlib.sha512(payload).digest()).decode() != INTEGRITY:
        raise ValueError(
            "Three.js package checksum differs from the npm 0.180.0 release."
        )
    root.mkdir(parents=True, exist_ok=True)
    vendor = root / "vendor"
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for name in FILES:
            entry = archive.getmember("package/" + name)
            if not entry.isfile():
                raise ValueError(f"Expected ordinary file in Three.js package: {name}")
            output = vendor / name
            output.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(entry) as source, output.open("wb") as dest:
                shutil.copyfileobj(source, dest)
    (root / "renders").mkdir(exist_ok=True)
    for image in images:
        dest = root / "renders" / image.name
        if dest.resolve() != image.resolve():
            shutil.copyfile(image, dest)
    for name in ("index.html", "viewer.css", "viewer.js"):
        shutil.copyfile(Path(__file__).with_name(name), root / name)
    shutil.copyfile(Path(__file__).with_name("local-guide.md"), root / "README.md")
    (root / "views.json").write_text(
        json.dumps({"gains": [0.035, 0.52, 0.31], "views": views}, indent=2) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("renders", type=Path)
    parser.add_argument(
        "--three-tgz",
        type=Path,
        help="Verified Three.js 0.180.0 npm archive for a fully offline install",
    )
    args = parser.parse_args()
    install(args.output, args.renders, args.three_tgz)
