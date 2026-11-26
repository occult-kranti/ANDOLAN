"""Check the published Monsoon Exchange handoff with the Python standard library."""

import json
import struct
from functools import cache
from hashlib import file_digest, sha256
from math import fsum, isclose, isfinite
from operator import itemgetter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "plan"
SCENE = ROOT / "scene"
CONCEPTS = ROOT / "concepts"
RENDERS = ROOT / "renders"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_bytes())


@cache
def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def match_file(path, recorded):
    require(path.stat().st_size == recorded["bytes"], f"Size changed: {path}")
    require(digest(path) == recorded["sha256"], f"Content changed: {path}")


def check_concepts():
    catalog = load(CONCEPTS / "image-assets.json")
    control = catalog["geometry_control"]
    frozen_path = CONCEPTS / control["survey_file"]
    require(
        digest(frozen_path) == control["survey_sha256"], "Changed historical art survey"
    )
    require(
        digest(PLAN / "geometry.json") == control["compiled_geometry_sha256"],
        "The measured floors or walls have changed since art registration",
    )
    frozen, current = load(frozen_path), load(PLAN / "survey.json")
    for group in ("basis", "bounds", "rooms", "links", "spawns", "objectives", "water"):
        require(
            frozen[group] == current[group],
            f"Art registration differs from surveyed {group}",
        )
    # Furnished-scene QA can refine shelter witness points independently of the solid itself.
    for group, fields in (
        ("covers", ("id", "room", "center", "size", "z")),
        ("entries", ("id", "site", "link", "center", "normal", "width", "covers")),
    ):
        dimensions = itemgetter(*fields)
        require(
            sorted(map(dimensions, frozen[group]))
            == sorted(map(dimensions, current[group])),
            f"Art registration differs from physical {group}",
        )
    require(
        digest(CONCEPTS / control["file"]) == control["sha256"],
        "Art control image changed",
    )
    assets = catalog["assets"]
    for asset in assets.values():
        for record in (asset["master"], asset["delivery"], *asset["references"]):
            match_file(CONCEPTS / record["file"], record)
    refs = {r["sha256"] for r in assets["painted-plan"]["references"]}
    require(
        {control["sha256"], assets["district-keyart"]["master"]["sha256"]} <= refs,
        "The painted plan lacks its surveyed guide or district art reference",
    )
    return assets["indigo-cloth"]["delivery"]


def check_textile(glb, cloth, artwork, packed_images):
    """Follow the shipped GLB's embedded image through texture, material, mesh and scene node."""
    require(
        (SCENE / cloth["source"]).resolve() == CONCEPTS / artwork["file"]
        and cloth["sha256"] == artwork["sha256"],
        "The scene uses a different textile from the generated delivery",
    )
    require(
        "Monsoon Exchange / Indigo loom block print" in packed_images,
        "Missing packed Blender textile",
    )
    data = glb.read_bytes()
    magic, version, length, json_size, kind = struct.unpack_from("<4sIII4s", data)
    require(
        (magic, version, length, kind) == (b"glTF", 2, len(data), b"JSON"),
        f"Invalid glTF header: {glb}",
    )
    end = 20 + json_size
    doc = json.loads(data[20:end])
    bin_size, kind = struct.unpack_from("<I4s", data, end)
    require(
        kind == b"BIN\0" and end + 8 + bin_size == len(data),
        "Invalid packed GLB buffer",
    )
    binary = memoryview(data)[end + 8 :]
    matches = set()
    for index, image in enumerate(doc["images"]):
        if image.get("mimeType") != "image/png" or "bufferView" not in image:
            continue
        view = doc["bufferViews"][image["bufferView"]]
        if view["buffer"] != 0 or view["byteLength"] != artwork["bytes"]:
            continue
        start = view.get("byteOffset", 0)
        if (
            sha256(binary[start : start + view["byteLength"]]).hexdigest()
            == artwork["sha256"]
        ):
            matches.add(index)
    textures = {i for i, t in enumerate(doc["textures"]) if t.get("source") in matches}
    materials = {
        i
        for i, m in enumerate(doc["materials"])
        if m.get("pbrMetallicRoughness", {}).get("baseColorTexture", {}).get("index")
        in textures
    }
    meshes = {
        i
        for i, m in enumerate(doc["meshes"])
        if any(
            p.get("material") in materials and "TEXCOORD_0" in p["attributes"]
            for p in m["primitives"]
        )
    }
    actual = {
        (n["name"], n.get("extras", {}).get("element"))
        for n in doc["nodes"]
        if n.get("mesh") in meshes
    }
    expected = {
        (p["object"], p["element"]) for p in cloth["placements"] if p["polygons"] > 0
    }
    require(
        actual and actual == expected,
        "Packed generated cloth is missing from the registered UV-mapped objects",
    )


def check_qa(scene_files):
    drawings = load(ROOT / "qa/drawing-verification.json")
    geometry = load(ROOT / "qa/geometry-verification.json")
    require(
        drawings["result"] == geometry["result"] == "pass",
        "Drawing or geometry QA did not pass",
    )
    drawing_hashes = drawings["source_sha256"]
    require(
        {
            "survey.json",
            "geometry.json",
            "floorplans.pdf",
            "floorplan.png",
            "floorplan.svg",
            "sun-court.svg",
            "indigo-cistern.svg",
            "sections.svg",
        }
        <= drawing_hashes.keys(),
        "Drawing QA is missing a delivered sheet or survey input",
    )
    for name, previous in drawing_hashes.items():
        require(digest(PLAN / name) == previous, f"Drawing QA predates {name}")
    inputs = {
        name: PLAN / name for name in ("survey.json", "geometry.json", "metrics.json")
    }
    inputs.update({name: SCENE / name for name in scene_files})
    inputs["field-rig"] = (
        ROOT.parents[1] / "docs/design/ember-rite-5v5/atlas/vertical-play/heroes.json"
    )
    require(
        geometry["source_sha256"]
        == {name: digest(path) for name, path in inputs.items()},
        "Geometry QA describes a different survey, rig or scene",
    )


def check_film(glb):
    film = ROOT / "film" / "district-tour.mp4"
    recording = load(film.with_name("recording.json"))
    require(recording["file"] == film.name, "Tour recording points to a different film")
    match_file(film, recording)
    require(
        recording["inputs_sha256"][glb.relative_to(ROOT).as_posix()] == digest(glb),
        "The tour uses a different map export",
    )
    chapters = recording["chapters"]
    titles = [chapter["name"].strip() for chapter in chapters]
    require(
        all(titles) and len(set(titles)) == len(titles) >= 4,
        "The tour needs at least four uniquely named shots",
    )
    seconds = [chapter["duration_s"] for chapter in chapters]
    require(
        all(isfinite(t) and t > 0 for t in seconds)
        and isclose(fsum(seconds), recording["duration_s"], abs_tol=0.001),
        "Shot durations do not cover the exported tour",
    )


def main():
    artwork = check_concepts()
    scene = load(SCENE / "scene-register.json")
    for name in ("survey", "geometry"):
        require(
            scene[name + "_sha256"] == digest(PLAN / (name + ".json")),
            f"Scene predates {name}",
        )
    blend = SCENE / "monsoon-exchange.blend"
    glb = SCENE / "monsoon-exchange.glb"
    require(
        {blend.name, glb.name} <= scene["files"].keys(),
        "Native or portable scene missing from register",
    )
    for name, record in scene["files"].items():
        match_file(SCENE / name, record)
    check_textile(glb, scene["cloth"], artwork, scene["packed_images"])
    check_qa((blend.name, glb.name))

    renders = load(RENDERS / "render-register.json")
    require(
        (RENDERS / renders["source"]).resolve() == blend
        and renders["source_sha256"] == digest(blend),
        "Rendered views belong to a different Blender scene",
    )
    shots = renders["shots"]
    require(
        shots and shots.keys() == scene["cameras"].keys(),
        "Missing or additional registered camera views",
    )
    for name, record in shots.items():
        require(
            record["file"] == name + ".webp",
            f"Rendered camera and file name differ: {name}",
        )
        match_file(RENDERS / record["file"], record)

    check_film(glb)
    atlas = ROOT / "monsoon-exchange-atlas.pdf"
    with atlas.open("rb") as pdf:
        require(pdf.read(5) == b"%PDF-", "Field guide is missing its PDF signature")
        pdf.seek(-min(1024, atlas.stat().st_size), 2)
        require(
            pdf.read().rstrip().endswith(b"%%EOF"),
            "Field guide is missing its PDF end marker",
        )
    print(
        f"Verified map survey, generated artwork, packed textile, native and portable scene, drawings, {len(shots)} rendered views, film and illustrated atlas."
    )


if __name__ == "__main__":
    main()
