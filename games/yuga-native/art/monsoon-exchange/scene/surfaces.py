"""Generate the district's repeatable painted surfaces. No external image inputs."""

from math import tau
from pathlib import Path
import numpy as np
from PIL import Image

# Each texture has a stated repeat in metres in Blender and glTF.
SURFACES = {
    "jade": ("719c8f", "pavers", 4.0),
    "buff": ("d2b58b", "pavers", 4.0),
    "slate": ("6d8086", "pavers", 4.0),
    "sunstone": ("d8b18a", "pavers", 4.0),
    "brick": ("bd795d", "ashlar", 3.6),
    "brick-dark": ("935846", "ashlar", 3.6),
    "lime": ("dbcaab", "plaster", 3.0),
    "indigo": ("46718b", "plaster", 3.0),
    "sienna": ("ba795c", "plaster", 3.0),
    "turquoise": ("4d9290", "plaster", 3.0),
    "tiles": ("b65d47", "roof", 2.7),
    "copper": ("ba8056", "metal", 2.8),
    "woven-blue": ("315b74", "textile", 2.6),
    "woven-gold": ("d69e50", "textile", 2.6),
    "woven-red": ("ac5246", "textile", 2.6),
    "water": ("3c9091", "water", 5.0),
    "earth": ("969479", "soil", 9.0),
}


def paint(out):
    out.mkdir(parents=True, exist_ok=True)
    side = 384
    y, x = np.mgrid[0:side, 0:side] / side
    for index, (name, (hexrgb, kind, _)) in enumerate(SURFACES.items()):
        rng = np.random.default_rng(707 + index)
        grain = rng.normal(0, 1.3, (side, side))
        # Periodic fields match across all four atlas edges.
        clouds = 0.0
        for freq, amp in [(1, 5.0), (2, 3.2), (4, 1.8), (11, 0.95)]:
            clouds += amp * np.sin(
                tau * (x * freq + 0.8 * np.cos(y * tau * freq)) + rng.uniform(0, tau)
            )
        tone = clouds + grain
        if kind in ("pavers", "ashlar"):
            rows = 5 if kind == "pavers" else 9
            cols = 3 if kind == "pavers" else 4
            row = np.floor(y * rows).astype(int)
            xx = x * cols + (row % 2) / 2
            col = np.floor(xx).astype(int) % cols
            dx = np.minimum(xx % 1, 1 - (xx % 1)) / cols
            dy = np.minimum(y * rows % 1, 1 - (y * rows % 1)) / rows
            seam = np.minimum(dx, dy) + 0.0013 * np.sin(
                x * tau * 17 + np.sin(y * tau * 11)
            )
            tone += rng.uniform(-11.5, 11.5, (rows, cols))[row, col]
            tone -= 28 * np.exp(-np.square(seam / 0.0028))
            tone += 5 * np.exp(-np.square((seam - 0.008) / 0.0035))
        elif kind == "roof":
            tone += 11 * np.cos(x * tau * 8) - 16 * np.power(
                (1 + np.cos(y * tau * 5)) / 2, 22
            )
        elif kind == "textile":
            tri = np.abs((x * 5) % 1 - 0.5) + 0.60 * np.abs((y * 8) % 1 - 0.5)
            tone += 29 * (np.abs(tri - 0.42) < 0.03) + 19 * (np.abs(tri - 0.55) < 0.025)
            tone += 17 * (np.abs((y * 2) % 1 - 0.5) < 0.017) + 2.5 * np.sin(
                x * tau * 125
            )
        elif kind == "metal":
            tone += 7 * np.sin((7 * x + 3 * y) * tau + np.sin(4 * y * tau))
        elif kind == "water":
            tone += 6 * np.cos(y * tau * 12 + 2.5 * np.sin(x * tau * 2))
        elif kind == "soil":
            tone += (
                3.8 * np.sin(tau * (x * 8 + y * 5) + 1.6 * np.cos(tau * y * 7))
                + grain * 1.4
            )
        rgb = np.array(tuple(bytes.fromhex(hexrgb)), dtype=float) + tone[:, :, None]
        Image.fromarray(np.clip(rgb, 0, 255).astype("uint8")).save(
            out / (name + ".png"), optimize=False
        )


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("output", type=Path)
    paint(args.parse_args().output)
