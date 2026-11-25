#!/usr/bin/env python3
"""Index the whole Game-icons SVG tree at a pinned commit and render attributable previews."""

import argparse
import base64
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PIN = "82d948812bfe3f269ef8f731dcdb07b08160edc4"
REPO = "game-icons/icons"
BASE = f"https://github.com/{REPO}/blob/{PIN}/"
ARCHIVE = f"https://codeload.github.com/{REPO}/tar.gz/{PIN}"
INPUT_HASH = "6ede4bfaed3bbe3cbe4b188b46ab2d62a28bcf737cbfcd1f0edcfdf12c124cff"


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def artwork(xml):
    root = ET.fromstring(xml)
    namespace = "{http://www.w3.org/2000/svg}"
    allowed = {
        "svg": {"viewBox"},
        "path": {"d", "fill"},
        "circle": {"cx", "cy", "r", "stroke", "stroke-width", "fill"},
    }
    for elem in root.iter():
        name = elem.tag.removeprefix(namespace)
        if name not in allowed or not set(elem.attrib).issubset(allowed[name]):
            raise ValueError("Unexpected SVG element or attribute")
        for attr in ("fill", "stroke"):
            if attr in elem.attrib and not re.fullmatch(
                r"#[\da-fA-F]{3,8}|black|white|none", elem.attrib[attr]
            ):
                raise ValueError("Unexpected paint in SVG")
    if root.tag != namespace + "svg":
        raise ValueError("Missing SVG root")
    dim = list(map(float, root.attrib["viewBox"].split()))
    return dim, Counter(e.tag.removeprefix(namespace) for e in root.iter())


def render(xml):
    import cairosvg
    from PIL import Image

    png = cairosvg.svg2png(bytestring=xml, output_width=72, output_height=72)
    with Image.open(io.BytesIO(png)) as img:
        webp = io.BytesIO()
        img.convert("RGB").save(webp, format="WEBP", quality=76, method=4)
    return "data:image/webp;base64," + base64.b64encode(webp.getvalue()).decode()


def build(archive):
    buf = (
        archive.read_bytes()
        if archive
        else urllib.request.urlopen(ARCHIVE, timeout=90).read()
    )
    if checksum(buf) != INPUT_HASH:
        raise ValueError("Upstream archive checksum mismatch")
    rows = []
    shapes = Counter()
    contributor = {}
    labels = Counter()
    with tarfile.open(fileobj=io.BytesIO(buf), mode="r:gz") as upstream:
        entries = sorted((m for m in upstream if m.isfile()), key=lambda m: m.name)
        terms = (
            upstream.extractfile(
                next(m for m in entries if m.name.endswith("/license.txt"))
            )
            .read()
            .decode()
        )
        for line in terms.splitlines():
            if line.startswith("- "):
                name = line[2:].split(",")[0].split(" - CC0")[0]
                key = re.sub("[^a-z0-9]", "", name.lower())
                contributor["lucasms" if key == "lucas" else key] = (
                    name,
                    "CC0-1.0" if " - CC0" in line else "CC-BY-3.0",
                )
        for entry in entries:
            if not entry.name.endswith(".svg"):
                continue
            _, folder, filename = entry.name.split("/")
            path = folder + "/" + filename
            body = upstream.extractfile(entry).read()
            dimensions, geometry = artwork(body)
            shapes.update(geometry)
            name = filename[:-4].replace("-", " ")
            author, license_id = contributor.get(
                folder.replace("-", ""), (None, "CC-BY-3.0")
            )
            rights = (
                (
                    f"Icons made by {author}. Credit the artist, link the Creative Commons license and identify modifications."
                    if license_id == "CC-BY-3.0"
                    else f"Icons made by {author}. The project license lists this contributor under CC0."
                )
                if author
                else "The repository specifies CC BY 3.0 by default. This folder has no matching individual credit in its contributor list. Verify the original artist before redistribution."
            )
            row = {
                "id": f"icon:{folder}/{filename[:-4]}",
                "name": name.title(),
                "kind": "Icon",
                "project": REPO,
                "revision": PIN,
                "path": path,
                "source_url": BASE + path,
                "license": license_id,
                "license_url": BASE + "license.txt",
                "rights_note": rights,
                "author": author,
                "summary": f'{name.capitalize()} silhouette. {geometry["path"]} vector paths on a {dimensions[2]:g} × {dimensions[3]:g} canvas.',
                "tags": list(dict.fromkeys(["SVG", "icon", *name.split()])),
                "sha256": checksum(body),
                "bytes": len(body),
                "dimensions": dimensions,
                "paths": geometry["path"],
                "circles": geometry["circle"],
                "evidence": "svg-inspected",
                "terms_url": (
                    "https://creativecommons.org/publicdomain/zero/1.0/"
                    if license_id == "CC0-1.0"
                    else "https://creativecommons.org/licenses/by/3.0/"
                ),
            }
            if author:
                row["preview_data"] = render(body)
            rows.append(row)
            labels[license_id] += 1
    dest = ROOT / "data/icons.json.gz"
    dest.write_bytes(
        gzip.compress(
            json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    report = {
        "project": REPO,
        "revision": PIN,
        "upstream_archive": ARCHIVE,
        "source_archive_sha256": INPUT_HASH,
        "license_file": BASE + "license.txt",
        "license_sha256": checksum(terms.encode()),
        "files": len(rows),
        "by_license": dict(labels),
        "attributed_thumbnails": sum("preview_data" in r for r in rows),
        "unresolved_individual_credit": sum(not r["author"] for r in rows),
        "shapes": dict(shapes),
        "preview": "72 px WebP thumbnails rasterized from the actual self-contained shapes, no external resources or scripts. The source file is linked for full vector resolution. No previews are reproduced for unresolved individual credits.",
        "dataset_sha256": checksum(dest.read_bytes()),
    }
    (ROOT / "evidence/icons.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    build(parser.parse_args().archive)
