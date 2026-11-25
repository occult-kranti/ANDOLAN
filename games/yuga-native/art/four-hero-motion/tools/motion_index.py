"""Index the actual animation samplers in the four GLBs for handoff and DCC import."""
from hashlib import sha256
import json
from pathlib import Path
import struct

PACK = Path(__file__).resolve().parents[1]
HEROES = ("hanuman", "shiva", "rama", "krishna")


def index(path):
    raw = path.read_bytes()
    magic, version, length, json_length, json_type = struct.unpack_from("<4s4I", raw)
    if (magic, version, length, json_type) != (b"glTF", 2, len(raw), 0x4E4F534A):
        raise ValueError(f"Invalid GLB header in {path.name}")
    gltf = json.loads(raw[20:20 + json_length])
    if any("uri" in x for x in gltf.get("buffers", []) + gltf.get("images", [])):
        raise ValueError(f"{path.name} refers to an external buffer or texture")
    actions = []
    for animation in gltf["animations"]:
        samplers = [gltf["accessors"][s["input"]] for s in animation["samplers"]]
        props = sorted({ch["target"]["path"] for ch in animation["channels"]})
        joints = {ch["target"]["node"] for ch in animation["channels"]}
        start = min(s["min"][0] for s in samplers)
        end = max(s["max"][0] for s in samplers)
        actions.append({
            "name": animation["name"],
            "first_key_s": round(start, 6),
            "last_key_s": round(end, 6),
            "key_span_s": round(end - start, 6),
            "target_nodes": len(joints),
            "animated_properties": props,
        })
    return {
        "file": "models/" + path.name,
        "sha256": sha256(raw).hexdigest(),
        "joints": len(gltf["skins"][0]["joints"]),
        "meshes": len(gltf["meshes"]),
        "material_slots": len(gltf["materials"]),
        "embedded_images": len(gltf.get("images", [])),
        "actions": actions,
    }


if __name__ == "__main__":
    result = {hero: index(PACK / "models" / (hero + ".glb")) for hero in HEROES}
    names = {"idle", "run", "jump", "defeat", "fire", "cast", "cast1", "cast2", "cast3"}
    for hero, record in result.items():
        actual = [a["name"] for a in record["actions"]]
        if len(actual) != len(set(actual)) or names.difference(actual):
            raise ValueError(f"Clip inventory mismatch in {hero}")
    output = {
        "format": "glTF 2.0 / binary, metres, Y-up",
        "timing": "Source GLB time is in seconds. first_key_s and last_key_s retain export offsets. Gameplay releases and edited display durations are documented independently.",
        "heroes": result,
    }
    (PACK / "motion-index.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"{sum(len(h['actions']) for h in result.values())} clips across {len(result)} rigs")
