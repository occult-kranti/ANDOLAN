"""Publish a labelled sheet and archive from the 15 completed studio renders."""
from __future__ import annotations

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


NATIVE = Path(__file__).resolve().parents[2]
FONT_ROOT = Path("/usr/share/fonts/truetype/dejavu")
FRAME_ORDER = ("vajra_gada", "vajra_kavacha", "maruti_udayana", "lanka_dahan", "mountain_pulse")
SHEET_NAME = "hanuman-ability-poses.jpg"
ARCHIVE_NAME = "studio-poses.zip"
RENDER_FIELDS = ("studio_scene_sha256", "actions_scene_sha256", "kit_sha256", "samples", "image_size", "blender")
POSE_FIELDS = ("id", "name", "action", "phase", "normalized_time", "source_frame", "camera_yaw_degrees", "file")


def digest(data):
    return sha256(data).hexdigest()


def read_capture(folder, reframe=None):
    original = (folder / "studio-poses.json").read_bytes()
    receipt = json.loads(original)
    size = tuple(receipt["image_size"])
    frames = receipt["frames"]
    if len(frames) != 3 * len(FRAME_ORDER):
        raise ValueError("Expected all five abilities with three poses each.")
    members = {"studio-poses.json": original}
    runs = [{"id": "original", "receipt": "studio-poses.json", "receipt_sha256": digest(original),
             "script_sha256": receipt["script_sha256"], "rendered_frames": len(frames), "selected_frames": len(frames)}]
    replacement = []
    if reframe is not None:
        payload = (reframe / "studio-poses.json").read_bytes()
        correction = json.loads(payload)
        replacement = correction["frames"]
        if any(correction[key] != receipt[key] for key in RENDER_FIELDS) or len(replacement) != 3:
            raise ValueError("The Mountain reframe must use the same source, action, image size and samples.")
        for before, after in zip(frames[-3:], replacement):
            if any(before[key] != after[key] for key in POSE_FIELDS):
                raise ValueError("The reframe must preserve the three Mountain Pulse poses.")
            if after["gada_frame_bounds"]["edge_margin"] < .05:
                raise ValueError("The corrected frame cuts too close to the posed gada.")
        corrected_member = "receipts/mountain-reframe.json"
        members[corrected_member] = payload
        runs[0]["selected_frames"] -= len(replacement)
        runs.append({"id": "mountain-reframe", "receipt": corrected_member, "receipt_sha256": digest(payload),
                     "script_sha256": correction["script_sha256"], "rendered_frames": 3, "selected_frames": 3})
    records, images = [], []
    for row, ability in enumerate(FRAME_ORDER):
        for column in range(3):
            frame = frames[row * 3 + column]
            filename = f"{ability}-{column + 1}.png"
            cleaned = f"{ability}-{column + 1}-denoised.png"
            if frame["id"] != ability or frame["file"] != filename:
                raise ValueError(f"Receipt is out of order at {filename}.")
            frame_folder = folder
            run = "original"
            if replacement and ability == "mountain_pulse":
                frame = replacement[column]
                frame_folder = reframe
                run = "mountain-reframe"
            raw_bytes = (frame_folder / filename).read_bytes()
            clean_bytes = (frame_folder / cleaned).read_bytes()
            raw_hash = digest(raw_bytes)
            clean_hash = digest(clean_bytes)
            if raw_hash != frame["sha256"] or clean_hash == raw_hash:
                raise ValueError(f"Raw checksum or denoised derivative mismatch at {filename}.")
            for data in (raw_bytes, clean_bytes):
                with Image.open(BytesIO(data)) as img:
                    if img.size != size or img.format != "PNG":
                        raise ValueError(f"Unexpected frame format or dimensions at {filename}.")
                    img.verify()
            with Image.open(BytesIO(clean_bytes)) as img:
                images.append(img.convert("RGB"))
            raw_member = f"raw/{filename}"
            clean_member = f"denoised/{cleaned}"
            members[raw_member] = raw_bytes
            members[clean_member] = clean_bytes
            record = {
                "ability": ability,
                "name": frame["name"],
                "run": run,
                "action": frame["action"],
                "beat": frame["phase"],
                "phase": frame["normalized_time"],
                "frame": frame["source_frame"],
                "yaw_degrees": frame["camera_yaw_degrees"],
                "raw": {"path": raw_member, "sha256": raw_hash},
                "denoised": {"path": clean_member, "sha256": clean_hash},
            }
            for key in ("camera_lens_mm", "camera_target_m", "gada_frame_bounds"):
                if frame.get(key) is not None:
                    record[key] = frame[key]
            records.append(record)
    return receipt, runs, records, images, members


def save_sheet(path, receipt, records, images):
    margin, gap = 32, 14
    frame_width, frame_height = receipt["image_size"]
    top, row_height = 132, frame_height + 87
    width = frame_width * 3 + gap * 2 + margin * 2
    height = top + row_height * len(FRAME_ORDER) + 40
    sheet = Image.new("RGB", (width, height), "#192127")
    draw = ImageDraw.Draw(sheet)
    ivory, muted, gold, line = "#f0e8d9", "#c2c9ce", "#deb282", "#53616b"
    title = ImageFont.truetype(str(FONT_ROOT / "DejaVuSerif-Bold.ttf"), 44)
    title_secondary = ImageFont.truetype(str(FONT_ROOT / "DejaVuSans.ttf"), 18)
    name_font = ImageFont.truetype(str(FONT_ROOT / "DejaVuSans-Bold.ttf"), 26)
    beat_font = ImageFont.truetype(str(FONT_ROOT / "DejaVuSans-Bold.ttf"), 17)
    note_font = ImageFont.truetype(str(FONT_ROOT / "DejaVuSans.ttf"), 16)
    draw.text((margin, 24), "Hanuman ability poses", fill=ivory, font=title)
    draw.text((margin + 2, 86), "Five abilities on the editable Blender rig", fill=muted, font=title_secondary)
    draw.line((margin, 118, width - margin, 118), fill=line, width=1)
    for row in range(len(FRAME_ORDER)):
        first = row * 3
        y = top + row * row_height
        draw.text((margin, y), records[first]["name"], fill=gold, font=name_font)
        for column, offset in enumerate(range(first, first + 3)):
            frame_record = records[offset]
            x = margin + column * (frame_width + gap)
            image_y = y + 38
            sheet.paste(images[offset], (x, image_y))
            draw.rectangle((x, image_y, x + frame_width - 1, image_y + frame_height - 1), outline=line)
            label_y = image_y + frame_height + 10
            draw.text((x, label_y), frame_record["beat"], fill=ivory, font=beat_font)
            detail = f"Frame {frame_record['frame']:.2f}"
            draw.text((x + frame_width - draw.textlength(detail, font=note_font), label_y),
                      detail, fill=muted, font=note_font)
    footer = f"Blender {receipt['blender']} · Cycles · {receipt['samples']} samples · Open Image Denoise"
    draw.text((margin, height - 31), footer, fill=muted, font=note_font)
    sheet.save(path, "JPEG", quality=94, subsampling=0, optimize=True)
    return width, height


def save_archive(path, members):
    with ZipFile(path, "w", compression=ZIP_STORED) as archive:
        for name, data in sorted(members.items()):
            info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with ZipFile(path) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(members):
            raise ValueError("Archive membership or CRC validation failed.")
        for member, data in members.items():
            if archive.read(member) != data:
                raise ValueError(f"Archived bytes differ for {member}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studio", type=Path, required=True)
    parser.add_argument("--mountain-reframe", type=Path, help="Use the corrected three Mountain Pulse renders.")
    parser.add_argument("--original-renderer", type=Path, help="Archive the exact original render script.")
    parser.add_argument("--reframe-renderer", type=Path, help="Archive the exact Mountain reframe script.")
    parser.add_argument("--art", type=Path, default=NATIVE / "art/hanuman/abilities")
    parser.add_argument("--evidence", type=Path, default=NATIVE / "docs/research/hanuman-ability-production")
    args = parser.parse_args()
    receipt, runs, records, images, members = read_capture(args.studio, args.mountain_reframe)
    for run, source in zip(runs, (args.original_renderer, args.reframe_renderer)):
        if source is not None:
            payload = source.read_bytes()
            if digest(payload) != run["script_sha256"]:
                raise ValueError(f"The {run['id']} render script differs from its receipt.")
            member = f"receipts/{run['id']}-renderer.py"
            members[member] = payload
            run["script"] = member
    args.art.mkdir(parents=True, exist_ok=True)
    args.evidence.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="studio-pack-", dir=args.art) as directory:
        sheet = Path(directory) / SHEET_NAME
        archive = Path(directory) / ARCHIVE_NAME
        sheet_size = save_sheet(sheet, receipt, records, images)
        save_archive(archive, members)
        index = {
            **{key: receipt[key] for key in RENDER_FIELDS},
            "runs": runs,
            "pack_script_sha256": digest(Path(__file__).read_bytes()),
            "pillow": pillow_version,
            "sheet": {"file": SHEET_NAME, "size": sheet_size, "sha256": digest(sheet.read_bytes())},
            "archive": {"file": ARCHIVE_NAME, "bytes": archive.stat().st_size, "members": len(members),
                        "sha256": digest(archive.read_bytes())},
            "frames": records,
        }
        for path in (sheet, archive):
            path.chmod(0o644)
            path.replace(args.art / path.name)
        (args.evidence / "studio-poses.json").write_text(json.dumps(index, indent=2) + "\n")


if __name__ == "__main__":
    main()
