"""Acquire eight museum-identified public-domain art references for YUGA.

The downloaded JPEGs are for the art-reference library. The script checks
each work's institution-supplied rights status before writing its image.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import re

ROOT = Path(__file__).resolve().parent
MET_IDS = (37960, 37986, 37988, 53684, 39329, 448183, 436535)
NGA_PAGE = "https://www.nga.gov/artworks/74796-japanese-footbridge"
NGA_IIIF = "https://api.nga.gov/iiif/0b9cefb5-1ee4-401a-8154-8d4039191a28/full/!1200,1200/0/default.jpg"
COMMONS_TITLE = "File:Claude Monet, The Japanese Footbridge, 1899, NGA 74796.jpg"
COMMONS = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "YUGA-Art-History-Research/1.0 (source attribution study)"


def request(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as response:
        return response.read()


def digest(value):
    return sha256(value).hexdigest()


def save(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def met(object_id):
    api = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
    raw = request(api)
    record = json.loads(raw)
    if record["objectID"] != object_id or not record["isPublicDomain"]:
        raise ValueError(f"Met record {object_id} is not marked public domain")
    image_url = record["primaryImageSmall"]
    if not image_url.startswith("https://images.metmuseum.org/") or not image_url.endswith(".jpg"):
        raise ValueError(f"Met record {object_id} lacks the expected open JPEG")
    jpeg = request(image_url)
    if not jpeg.startswith(b"\xff\xd8\xff"):
        raise ValueError(f"Met record {object_id} is not a JPEG")
    image_path = f"images/met-{object_id}.jpg"
    metadata_path = f"metadata/met-{object_id}.json"
    record_summary = {
        "id": f"met-{object_id}",
        "institution": "The Metropolitan Museum of Art",
        "title": record["title"],
        "artist": " ".join(part for part in (record["artistPrefix"], record["artistDisplayName"], record["artistSuffix"]) if part) or "Artist not identified in Met record",
        "date": record["objectDate"],
        "culture": record["culture"],
        "medium": record["medium"],
        "credit": record["creditLine"],
        "rights": "Met API isPublicDomain=true, eligible for the Met Open Access CC0 policy",
        "object_url": record["objectURL"],
        "metadata_url": api,
        "metadata_file": metadata_path,
        "metadata_sha256": digest(raw),
        "image_url": image_url,
        "image_file": image_path,
        "image_sha256": digest(jpeg),
        "image_bytes": len(jpeg),
    }
    return record_summary, {image_path: jpeg, metadata_path: raw}


class TextAndMeta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.tags = {}

    def handle_data(self, data):
        self.text.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            values = dict(attrs)
            key = values.get("property") or values.get("name")
            if key and values.get("content"):
                self.tags[key] = values["content"]


def nga():
    page = request(NGA_PAGE)
    html = page.decode("utf-8")
    parser = TextAndMeta()
    parser.feed(html)
    text = re.sub(r"\s+", " ", unescape(" ".join(parser.text)))
    rights_line = "This object’s media is free and in the public domain."
    if rights_line not in text or "The Japanese Footbridge by Claude Monet" not in parser.tags.get("og:title", ""):
        raise ValueError("The NGA page no longer provides the expected title and rights statement")
    if not re.search(r'"dateCreated"\s*:\s*"1899"', html):
        raise ValueError("The NGA page no longer states the expected artwork date")
    query = urlencode({"action": "query", "format": "json", "prop": "revisions",
                       "rvprop": "content", "rvslots": "main", "titles": COMMONS_TITLE})
    commons_url = COMMONS + "?" + query
    commons = request(commons_url)
    pages = json.loads(commons)["query"]["pages"].values()
    page_record = next(iter(pages))
    wiki = page_record["revisions"][0]["slots"]["main"]["*"]
    if "{{CC0}}" not in wiki or "https://purl.org/nga/collection/artobject/74796" not in wiki:
        raise ValueError("Wikimedia provenance no longer records NGA and CC0")
    jpeg = request(NGA_IIIF)
    if not jpeg.startswith(b"\xff\xd8\xff"):
        raise ValueError("NGA image is not a JPEG")
    metadata = {
        "id": "nga-74796",
        "institution": "National Gallery of Art",
        "title": "The Japanese Footbridge",
        "artist": "Claude Monet",
        "date": "1899",
        "credit": "Gift of Victoria Nebeker Coberly, in memory of her son John W. Mudd, and Walter H. and Leonore Annenberg",
        "rights": rights_line,
        "commons_rights": "CC0 on the institution-donated Wikimedia Commons file",
        "object_url": NGA_PAGE,
        "object_page_sha256": digest(page),
        "commons_file": "https://commons.wikimedia.org/wiki/" + COMMONS_TITLE.replace(" ", "_"),
        "commons_api_url": commons_url,
        "commons_api_sha256": digest(commons),
        "image_url": NGA_IIIF,
    }
    raw = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode()
    metadata.update({
        "metadata_file": "metadata/nga-74796.json",
        "metadata_sha256": digest(raw),
        "image_file": "images/nga-74796.jpg",
        "image_sha256": digest(jpeg),
        "image_bytes": len(jpeg),
    })
    return metadata, {"metadata/nga-74796.json": raw, "images/nga-74796.jpg": jpeg}


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        fetched = list(pool.map(met, MET_IDS))
    fetched.append(nga())
    works = [record for record, _ in fetched]
    manifest = {
        "collected_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "Eight museum-verified art-reference images; examples, not an exhaustive survey.",
        "met_open_access_policy": "https://www.metmuseum.org/about-the-met/policies-and-documents/open-access",
        "nga_open_access_policy": "https://www.nga.gov/artworks/free-images-and-open-access",
        "objects": works,
    }
    for _, files in fetched:
        for name, contents in files.items():
            save(ROOT / name, contents)
    save(ROOT / "catalog.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode())
    print(f"Verified {len(works)} museum images, {sum(x['image_bytes'] for x in works):,} bytes")


if __name__ == "__main__":
    main()
