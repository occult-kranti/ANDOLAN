"""Check the source catalog, image bytes, rights flags and generated offline gallery."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json

from PIL import Image

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "met-37960", "met-37986", "met-37988", "met-53684",
    "met-39329", "met-448183", "met-436535", "nga-74796",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "img":
            self.images.append(values)
        if tag == "a":
            self.links.append(values.get("href"))


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text())
    works = catalog["objects"]
    assert len(works) == len(EXPECTED)
    assert {item["id"] for item in works} == EXPECTED
    gallery = Gallery()
    gallery.feed((ROOT / "gallery.html").read_text())
    assert len(gallery.images) == len(works)
    details = []
    for work in works:
        image = ROOT / work["image_file"]
        metadata = ROOT / work["metadata_file"]
        assert digest(image) == work["image_sha256"], work["id"]
        assert image.stat().st_size == work["image_bytes"], work["id"]
        assert digest(metadata) == work["metadata_sha256"], work["id"]
        assert work["image_file"] in gallery.links and work["object_url"] in gallery.links
        assert any(i.get("src") == work["image_file"] and i.get("alt") for i in gallery.images)
        with Image.open(image) as content:
            content.verify()
        with Image.open(image) as content:
            width, height = content.size
        assert min(width, height) >= 320, work["id"]
        data = json.loads(metadata.read_text())
        if work["id"].startswith("met-"):
            assert data["isPublicDomain"] is True and data["objectID"] == int(work["id"][4:])
            artist = " ".join(part for part in (
                data["artistPrefix"], data["artistDisplayName"], data["artistSuffix"]
            ) if part) or "Artist not identified in Met record"
            assert work["artist"] == artist, work["id"]
        else:
            assert data["id"] == "nga-74796"
            assert data["rights"] == "This object’s media is free and in the public domain."
        details.append({"id": work["id"], "width": width, "height": height, "sha256": work["image_sha256"]})
    print(json.dumps({"result": "pass", "objects": len(details), "images": details}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
