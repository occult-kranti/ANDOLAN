"""Assemble the enhanced playable Hanuman and editable groom from the pinned four-hero source.

Run with Python, Pillow, NumPy and Blender on PATH. The playable GLB can be
imported directly in Blender, or the smaller named groom patch opened for editing.
"""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from motion import improve_motion
from surfaces import finish_glb

PACK = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PACK / "models/hanuman-enhanced.glb")
    parser.add_argument("--groom-blend", type=Path, default=PACK / "models/hanuman-groom.blend")
    parser.add_argument("--evidence", type=Path, default=PACK / "evidence")
    parser.add_argument("--blender", default="blender")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.groom_blend.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output.parent, prefix=".assemble-") as temp:
        folder = Path(temp)
        groom, shaded, final = [
            folder / (name + ".glb") for name in ("sculpt", "surfaces", "finished")
        ]
        pose = folder / "groom.blend"
        receipt = folder / "sculpt.json"
        subprocess.run(
            [
                args.blender,
                "-b",
                "-t",
                "2",
                "--python-exit-code",
                "1",
                "-P",
                str(PACK / "tools/sculpt.py"),
                "--",
                "--output",
                str(groom),
                "--blend",
                str(pose),
                "--receipt",
                str(receipt),
            ],
            check=True,
        )
        finish_glb(groom, shaded)
        motion = improve_motion(shaded, final)
        sculpt = json.loads(receipt.read_text())
        audit = {
            "source_sha256": sculpt["source_sha256"],
            "sculpt_sha256": sha(groom),
            "pbr_sha256": sha(shaded),
            "playable_sha256": sha(final),
            "playable_bytes": final.stat().st_size,
            "editable_groom_sha256": sha(pose),
            "material": "Hanuman | swept copper guard hair",
            "added_draws": 1,
            "added_vertices": sum(r["vertices"] for r in sculpt["groom"]),
            "added_triangles": sum(r["triangles"] for r in sculpt["groom"]),
            "tuned_action": motion["animation"],
            "tuned_curves": motion["curves"],
        }
        summary = folder / "build.json"
        summary.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
        os.replace(pose, args.groom_blend)
        os.replace(receipt, args.evidence / "sculpt.json")
        os.replace(summary, args.evidence / "build.json")
        os.replace(final, args.output)
    print(f"{args.output} • {audit['playable_bytes']:,} bytes • {audit['playable_sha256']}")


if __name__ == "__main__":
    main()
