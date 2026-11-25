"""Exercise hero_export from the public CLI and audit the binary against its source."""
import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERO = ROOT / "yuga-native/assets/heroes/hanuman"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("executable", type=Path)
exe = parser.parse_args().executable.resolve()
base = HERO / "hanuman.glb"
motion = HERO / "hanuman-ability-motion.tres"
source = motion.read_text()


def unpack(blob):
    json_end = 20 + struct.unpack_from("<I", blob, 12)[0]
    return json.loads(blob[20:json_end]), blob[json_end + 8:]


def run(*args):
    return subprocess.run([str(exe), *map(str, args)], text=True, capture_output=True)


def require(condition, label):
    if not condition:
        raise ValueError(label)


with tempfile.TemporaryDirectory(prefix="yuga-hero-cli-") as folder:
    stage = Path(folder)
    out = stage / "first.glb"
    run(base, motion, out).check_returncode()
    exported = out.read_bytes()
    other = stage / "second.glb"
    run(base, motion, other).check_returncode()
    require(other.read_bytes() == exported, "Different bytes for duplicate run")
    require(run(base, motion, out).returncode != 0 and out.read_bytes() == exported,
            "Existing destination was modified")
    wrong = stage / "wrong.glb"
    wrong.write_bytes(b"unrelated hero")
    missing = stage / "missing.glb"
    require(run(wrong, motion, missing).returncode != 0 and not missing.exists(),
            "Wrong source model accepted")
    malformed = {
        "unknown_joint": ("Skeleton3D:pelvis.L", "Skeleton3D:nonexistent"),
        "nonunit_rotation": ("0, 1, 6.619666e-08,", "0, 1, 9.0,"),
        "unsupported_interpolation": ("/interp = 1", "/interp = 3"),
        "remapped_resource": ('&"cast1": SubResource("Animation_2sum5")',
                              '&"cast1": SubResource("Animation_3l7al")'),
        "missing_impact": ("metadata/hanuman_impact_phase =", "metadata/omitted ="),
        "truncated": (source, source[:1500]),
    }
    for name, (old, new) in malformed.items():
        require(old in source, "Update mutation fixture for " + name)
        bad = stage / "bad.tres"
        bad.write_text(source.replace(old, new, 1))
        require(run(base, bad, missing).returncode != 0 and not missing.exists(), name)
    old, old_bin = unpack(base.read_bytes())
    new, new_bin = unpack(exported)
    modified = {"animations", "accessors", "bufferViews", "buffers"}
    require(old.keys() == new.keys(), "New or missing top-level asset fields")
    for field in old.keys() - modified:
        require(old[field] == new[field], "Changed visual field " + field)
    require(new_bin.startswith(old_bin), "Changed visual binary bytes")
    for field in ["accessors", "bufferViews"]:
        require(new[field][:len(old[field])] == old[field], "Changed existing " + field)
    retained = [a["name"] for a, b in zip(old["animations"], new["animations"]) if a == b]
    require(sorted(retained) == sorted(["jump", "defeat", "idle", "run", "cast", "cast3"]),
            "Unexpected changed clips")
    print(json.dumps({"export_sha256": hashlib.sha256(exported).hexdigest(), "bytes": len(exported),
        "retained_binary_bytes": len(old_bin), "retained_animation_definitions": retained,
        "retained_visual_fields": sorted(old.keys() - modified), "malformed_inputs_rejected": sorted(malformed),
        "existing_destination_preserved": True, "deterministic": True}, indent=2))
