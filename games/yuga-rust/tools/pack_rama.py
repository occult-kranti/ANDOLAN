"""Pack Rama's original rig and the recorded native controller poses into a browser GLB."""
import argparse
import gzip
import hashlib
import json
import math
import struct
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
NATIVE = GAME.parent / "yuga-native"
CACHE = GAME / "assets/rama-motion.json.gz"
SOURCES = ["scripts/rama_motion.gd", "assets/animations/rama_hero_motion.tres",
           "assets/design/rama-ability-kit.json", "assets/heroes/rama-hero.glb",
           "assets/heroes/rama-hero-far.glb"]
STAGES = {"draw", "release", "piercing_draw", "piercing_release", "dash", "dash_release",
          "circle_draw", "circle_release", "volley_draw", "volley_release"}


def hashes():
    return {name: hashlib.sha256((NATIVE / name).read_bytes()).hexdigest() for name in SOURCES}


def write_cache(capture, dest, muzzles):
    data = json.loads(capture.read_bytes())
    joints = data["bones"]
    if len(set(joints)) != 164 or set(data["clips"]) != STAGES:
        raise ValueError("Expected the original 164-joint controller and ten action stages")
    for clip in data["clips"].values():
        keys = clip.pop("samples")
        if len(keys) < 2 or any(len(row) != len(joints) * 7 for row in keys):
            raise ValueError("Invalid sample extent")
        clip["frames"] = len(keys)
        # Keep constant channels at an exact endpoint. Store float32 (the native precision).
        clip["channels"] = []
        for joint in range(len(joints)):
            for name, offset, width in [("translation", 0, 3), ("rotation", 3, 4)]:
                start = joint * 7 + offset
                values = [row[start:start + width] for row in keys]
                if not all(math.isfinite(x) for key in values for x in key):
                    raise ValueError("Invalid numerical pose")
                if all(key == values[0] for key in values):
                    values = [values[0]]
                raw = struct.pack("<" + "f" * width * len(values), *(x for key in values for x in key))
                clip["channels"].append([joint, name, raw.hex()])
    data["sources"] = hashes()
    with muzzles.open("x") as f:
        f.write(json.dumps(data["muzzles"], indent=2, sort_keys=True) + "\n")
    with dest.open("xb") as f:
        f.write(gzip.compress(json.dumps(data, separators=(",",":"), sort_keys=True).encode(), mtime=0))


def pack(dest, lod):
    data = json.loads(gzip.decompress(CACHE.read_bytes()))
    if data["muzzles"] != json.loads((GAME / "assets/rama-muzzles.json").read_text()):
        raise ValueError("Released-arrow offsets and native pose cache disagree")
    if data["sources"] != hashes():
        raise ValueError("Native art, controller or tuning changed; recapture the stages")
    name = "rama-hero-far.glb" if lod == "far" else "rama-hero.glb"
    raw = (NATIVE / "assets/heroes" / name).read_bytes()
    size = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + size])
    blob = bytearray(raw[28 + size:])
    joints = {doc["nodes"][i]["name"]: i for i in doc["skins"][0]["joints"]}
    if set(data["bones"]) != set(joints):
        raise ValueError("Model and motion stage skeletons differ")

    def accessor(chunk, kind, count, limits=None):
        offset = len(blob)
        blob.extend(chunk)
        doc["bufferViews"].append({"buffer":0, "byteOffset":offset, "byteLength":len(chunk)})
        item = {"bufferView":len(doc["bufferViews"])-1,"type":kind,"count":count,"componentType":5126}
        if limits: item.update(min=[limits[0]],max=[limits[1]])
        doc["accessors"].append(item)
        return len(doc["accessors"]) - 1

    for label, clip in data["clips"].items():
        frames = clip["frames"]
        duration = clip["duration"]
        times = [i * duration / (frames - 1) for i in range(frames)]
        one = accessor(bytes(4),"SCALAR",1,(0,0))
        all_times = accessor(struct.pack("<"+"f"*frames,*times),"SCALAR",frames,(0,duration))
        out = {"name":label,"channels":[],"samplers":[],"extras":{"yuga":{"duration_s":duration, "native_bake_hz":60}}}
        for joint, prop, encoded in clip["channels"]:
            chunk = bytes.fromhex(encoded)
            width = 3 if prop == "translation" else 4
            count = len(chunk)//(4*width)
            if count not in (1,frames): raise ValueError("Invalid channel length")
            output = accessor(chunk, "VEC"+str(width), count)
            out["channels"].append({"sampler":len(out["samplers"]),
                "target":{"node":joints[data["bones"][joint]],"path":prop}})
            out["samplers"].append({"input":one if count==1 else all_times,"output":output,"interpolation":"LINEAR"})
        doc["animations"].append(out)
    doc["buffers"][0]["byteLength"]=len(blob)
    header = json.dumps(doc, separators=(",",":"), allow_nan=False).encode()
    header += b" " * (-len(header)%4)
    with dest.open("xb") as f:
        f.write(struct.pack("<4sIIII",b"glTF",2,28+len(header)+len(blob),len(header),0x4e4f534a))
        f.write(header)
        f.write(struct.pack("<II",len(blob),0x004e4942))
        f.write(blob)
    print(name, len(doc["animations"]), "clips,", dest.stat().st_size, "bytes,", hashlib.sha256(dest.read_bytes()).hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--lod",choices=("near","far"),default="far")
    parser.add_argument("--capture",type=Path,help="Compact Godot capture into a new compressed cache instead")
    parser.add_argument("--muzzles",type=Path,help="Companion gameplay socket offsets when capturing")
    args=parser.parse_args()
    if args.capture:
        if not args.muzzles: parser.error("--capture requires --muzzles <fresh JSON>")
        write_cache(args.capture,args.output,args.muzzles)
    else: pack(args.output,args.lod)
