"""Check that the studio ships an individual painting for every catalog entry."""

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_webp(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Image path escapes the concept directory: {name}")
    data = path.read_bytes()
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError(f"Invalid WebP container: {name}")
    if len(data) != int.from_bytes(data[4:8], "little") + 8:
        raise ValueError(f"Incomplete WebP file: {name}")
    size = None
    pos = 12
    while pos + 8 <= len(data):
        kind, length = struct.unpack_from("<4sI", data, pos)
        pos += 8
        chunk = data[pos:pos + length]
        if len(chunk) != length:
            raise ValueError(f"Incomplete {kind!r} chunk: {name}")
        if kind == b"VP8 " and chunk[3:6] == b"\x9d\x01\x2a":
            width, height = struct.unpack_from("<HH", chunk, 6)
            size = (width & 0x3fff, height & 0x3fff)
        elif kind == b"VP8L" and chunk[:1] == b"\x2f":
            bits = int.from_bytes(chunk[1:5], "little")
            size = ((bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1)
        pos += length + (length % 2)
    if pos != len(data) or size is None or min(size) < 100:
        raise ValueError(f"Missing or unreadable painting: {name}")
    return size, hashlib.sha256(data).digest()


def verify():
    catalog = json.loads((ROOT.parent / "catalog.json").read_text())
    index = json.loads((ROOT / "index.json").read_text())
    entries = {row["id"]: row for row in catalog["elements"]}
    items = index["items"]
    if set(items) != set(entries):
        raise ValueError(f"Catalog entries without matching artwork: {set(entries) ^ set(items)}")
    _, cover_digest = read_webp(index["hero"]["file"])
    brief = json.loads((ROOT / index["hero"]["brief_file"]).read_text())
    if brief["webp_sha256"] != cover_digest.hex():
        raise ValueError("The district painting differs from the recorded cover")

    owners = {}
    board_sizes = {}
    for board in index["boards"]:
        key = board["id"]
        if key in board_sizes or not board["items"]:
            raise ValueError(f"Empty or repeated board: {key}")
        if not all(board.get(field) for field in ("title", "alt", "prompt")):
            raise ValueError(f"Missing art direction for {key}")
        board_sizes[key], _ = read_webp(board["file"])
        if board_sizes[key] != (board["width"], board["height"]):
            raise ValueError(f"Board dimensions changed for {key}")
        for item in board["items"]:
            if item in owners:
                raise ValueError(f"Two cropped paintings are registered to {item}")
            owners[item] = key
    if set(owners) != set(entries):
        raise ValueError("Board subjects differ from the catalog")

    hashes = set()
    for key, item in items.items():
        if owners[key] != item["board"] or not item.get("alt"):
            raise ValueError(f"Missing subject or description for {key}")
        size, digest = read_webp(item["file"])
        if digest in hashes or size != (item["width"], item["height"]):
            raise ValueError(f"Duplicate painting or size mismatch for {key}")
        hashes.add(digest)
        x0, y0, x1, y1 = item["source_box"]
        w, h = board_sizes[item["board"]]
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ValueError(f"Invalid board coordinates for {key}")
        if size != (x1 - x0, y1 - y0):
            raise ValueError(f"Cropped image size differs from its registration for {key}")

    routes = {key for key, item in entries.items() if item["kind"] == "route"}
    if set(index["route_boards"]) != routes:
        raise ValueError("Route context is missing or refers to a retired route")
    for key, context in index["route_boards"].items():
        route = entries[key]
        endpoints = {owners["room-" + route[end]] for end in ("from", "to")}
        if not endpoints.issubset(context) or not set(context).issubset(board_sizes):
            raise ValueError(f"Missing endpoint painting for {key}")
    route_source = json.loads((ROOT / index["route_paintings_file"]).read_text())
    if route_source["items"] != {key: items[key] for key in routes}:
        raise ValueError("Route paintings differ from their source ledger")
    print(f"Verified {len(board_sizes)} boards, {len(items)} individual paintings, "
          f"{len(routes)} routes and the district cover.")


if __name__ == "__main__":
    verify()
