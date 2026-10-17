#!/usr/bin/env python3
"""Read-only pixel audit of archived title PNGs; never edits source images."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ascii", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.report, args.ascii):
        if not output.is_absolute() or output.exists():
            parser.error("Require fresh absolute output paths")
    native = Path(__file__).resolve().parents[5]
    bounds = (160, 314, 400, 348)
    expected = "d9fe0d724cc0a29d899488a004a7b715b0a931e35f6c593e99b56eef9cfa75dc"
    rows, first_bytes, first_crop = [], None, None
    for take in ("r1", "r2"):
        folder = native / "docs/evidence/rama-quality/lookdev" / ("capture-" + take)
        manifest = json.loads((folder / "lookdev-capture.json").read_text())
        for name in ("title-day-before", "title-day-after", "title-night-before", "title-night-after"):
            shot = next(row for row in manifest["shots"] if row["id"] == name)
            path = folder / shot["file"]
            original_sha = sha256(path.read_bytes())
            assert original_sha == shot["sha256"], path
            with Image.open(path) as source:
                crop = source.convert("RGB").crop(bounds)
            raw = crop.tobytes()
            dark = sum(max(crop.getpixel((x, y))) < 100
                       for y in range(crop.height) for x in range(crop.width))
            if first_bytes is None:
                first_bytes, first_crop = raw, crop
            assert raw == first_bytes and sha256(raw) == expected and dark == 630, path
            assert sha256(path.read_bytes()) == original_sha, "Source image changed"
            rows.append({"path": str(path.relative_to(native)), "original_png_sha256": original_sha,
                         "decoded_rgb_sha256": sha256(raw), "dark_pixels_max_rgb_lt_100": dark,
                         "byte_identical_to_first": raw == first_bytes})
    raster = "\n".join("".join("#" if max(first_crop.getpixel((x, y))) < 100 else " "
                                  for x in range(first_crop.width)).rstrip()
                       for y in range(first_crop.height)) + "\n"
    args.ascii.write_text(raster)
    report = {"passed": True, "scope": "Exact label-region pixel equality only; not whole-screen UX acceptance.",
              "roi_xyxy": list(bounds), "decoded_mode": "RGB", "roi_size": [240, 34],
              "decoded_rgb_bytes": len(first_bytes), "expected_rgb_sha256": expected,
              "threshold": "max(R,G,B)<100", "ascii_raster_sha256": sha256(raster.encode()),
              "images_checked": len(rows), "all_source_png_hashes_match_captured_manifests": True,
              "all_roi_bytes_identical": True, "original_images_unchanged": True, "images": rows}
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "images_checked": len(rows), "decoded_rgb_sha256": expected,
                      "dark_pixels_per_roi": 630}))


if __name__ == "__main__":
    main()
