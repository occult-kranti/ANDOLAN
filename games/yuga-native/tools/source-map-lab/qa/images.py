"""Measure the recolor inside a camera-matched ground material mask for each rendered view."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, binary_erosion


def inspect_view(where, view, threshold=12):
    names = [f"{view}-{tag}.png" for tag in ("baseline", "jade", "ground-mask")]
    hashes = {}
    arrays = []
    for name, mode in zip(names, ("RGB", "RGB", "L")):
        path = where / name
        with path.open("rb") as f:
            hashes[name] = hashlib.file_digest(f, "sha256").hexdigest()
        with Image.open(path) as im:
            arrays.append(np.asarray(im.convert(mode), dtype=np.int16))
    before, after, alpha = arrays
    if before.shape != after.shape or alpha.shape != before.shape[:2]:
        raise ValueError(f"{view}: unmatched camera framing dimensions")
    mask = alpha >= 128
    if not mask.any() or mask.all():
        raise ValueError(
            f"{view}: ground-ID mask must contain both ground and other surfaces"
        )
    pixel_delta = after - before
    peak = np.abs(pixel_delta).max(axis=2)
    changed = peak >= threshold
    core = binary_erosion(mask, iterations=1)
    away = ~binary_dilation(mask | (alpha > 0), iterations=2)
    if not core.any():
        raise ValueError(f"{view}: no interior ground pixels")
    if not np.any(changed & core):
        raise ValueError(f"{view}: color change is invisible on ground")
    strong = int(changed.sum())
    spill = int((changed & away).sum())
    return {
        "view": view,
        "dimensions_px": [before.shape[1], before.shape[0]],
        "sha256": hashes,
        "material_mask_pixels": int(mask.sum()),
        "ground_percent": round(100 * mask.mean(), 3),
        "ground_core_percent_changed": round(100 * changed[core].mean(), 3),
        "ground_core_mean_delta_rgb_8bit": np.round(
            pixel_delta[core].mean(axis=0), 2
        ).tolist(),
        "strong_changed_pixels": strong,
        "strong_pixels_away_from_mask": spill,
        "strong_spill_percent_of_image": round(100 * spill / changed.size, 5),
        "strong_spill_percent_of_changes": round(100 * spill / strong, 4),
        "any_above_two_rgb_codes_percent": round(100 * (peak > 2).mean(), 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--views", nargs="+", default=["overview", "site-a", "site-b"])
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--threshold", type=int, default=12, help="8-bit max-channel change to count"
    )
    args = parser.parse_args()
    if not 1 <= args.threshold <= 255:
        parser.error("threshold must be 1..255")
    result = {
        "schema": "yuga.dust2.masked-render-diff.v1",
        "threshold_rgb_codes": args.threshold,
        "method": "Ground core erodes the >=128 mask by one pixel. Spill counts strong changes more than two pixels outside the material mask (excluding nonzero antialiasing samples). Geometric and material identity are independently verified in the GLB and BSP.",
        "views": [inspect_view(args.directory, v, args.threshold) for v in args.views],
    }
    body = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(body)
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
