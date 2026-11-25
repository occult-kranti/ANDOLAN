"""Exercise the manifest contracts with existing YUGA art and an independent Blender reopen."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
FILES = {
    "models/hero.glb": "assets/heroes/rama.glb",
    "letsgo/kit/tree.glb": "assets/world/nature.glb",
    "letsgo/kit/ground.png": "assets/vfx/hanuman-invocation-masks.png",
    "variant/b/paint.png": "assets/world/architecture_Confluence_warm_ivory_albedo.png",
}
UPSTREAM_COMMIT = "6a40d31175f5ce5ba15cdd74a141b1df9e1d0853"


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


def make_fixture(assets):
    for dest, src in FILES.items():
        out = assets / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(NATIVE / src, out)
    # Two aliases differ only after Blender's ID name byte budget.
    long_name = "river court arcade " * 5
    kit = {name: {"path": "letsgo/kit/tree.glb", "source": "YUGA nature"} for name in
           ("tree", long_name + "east", long_name + "west")}
    kit.update({"ground": {"path": "letsgo/kit/ground.png"}, "missing": {"path": "missing.glb"},
                "escape": {"path": "../outside.glb"}, "link": {"path": "link.glb"},
                "bad-checksum": {"path": "letsgo/kit/tree.glb", "sha256": "0" * 64},
                "external": {"path": "models/external.glb"}, "outside-image": {"path": "models/outside.glb"},
                "notes": {"path": "notes.md"}})
    # These two GLBs have identical bytes but resolve one image differently.
    nature = (assets / "letsgo/kit/tree.glb").read_bytes()
    json_size = struct.unpack_from("<I", nature, 12)[0]
    doc = json.loads(nature[20:20 + json_size])
    doc["images"] = [{"uri": "paint.png"}]
    doc["textures"] = [{"source": 0}]
    doc["materials"][0].setdefault("pbrMetallicRoughness", {})["baseColorTexture"] = {"index": 0}
    chunk = json.dumps(doc).encode()
    chunk += b" " * (-len(chunk) % 4)
    binary_chunk = nature[20 + json_size:]
    variant = struct.pack("<4sIII4s", b"glTF", 2, 20 + len(chunk) + len(binary_chunk),
                          len(chunk), b"JSON") + chunk + binary_chunk
    for key in ("a", "b"):
        directory = assets / "variant" / key
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "piece.glb").write_bytes(variant)
        kit["paint-" + key] = {"path": f"variant/{key}/piece.glb"}
    shutil.copyfile(assets / "letsgo/kit/ground.png", assets / "variant/a/paint.png")
    save(assets / "letsgo/kit/kit.json", kit)
    (assets / "notes.md").write_text("A fixture file")
    shutil.copyfile(assets / "letsgo/kit/tree.glb", assets.parent / "outside.glb")
    (assets / "link.glb").symlink_to(assets.parent / "outside.glb")
    for filename, uri in [("external.glb", "missing-texture.png"), ("outside.glb", "../../outside.png")]:
        # No scene data need be decoded for these missing/out-of-root dependencies.
        payload = json.dumps({"asset": {"version": "2.0"}, "images": [{"uri": uri}]}).encode()
        payload += b" " * (-len(payload) % 4)
        (assets / "models" / filename).write_bytes(
            struct.pack("<4sIII4s", b"glTF", 2, 20 + len(payload), len(payload), b"JSON") + payload)
    (assets.parent / "outside.png").write_bytes((assets / "letsgo/kit/ground.png").read_bytes())
    # A second actual file holding the same GLB must share geometry with the first.
    shutil.copyfile(assets / "letsgo/kit/tree.glb", assets / "letsgo/court.glb")
    scenery = {"court": {"scenes": [
        {"path": "letsgo/court.glb", "sha256": file_hash(assets / "letsgo/court.glb")}],
        "overlay": True, "heights": "letsgo/court_height.json"}}
    valid = {"width": 1, "height": 1, "res": 2, "grid": [[0, .1], [.2, None]], "trees": [[0, 1]]}
    save(assets / "letsgo/court_height.json", valid)
    for key, update in {"zero": {"width": 0}, "bool": {"res": True}, "short": {"grid": [[0], [1]]},
                        "rows": {"grid": [[0, 1]]}, "nonfinite": {"grid": [[0, .1], [float("inf"), 0]]},
                        "tree": {"trees": [[1, None]]}}.items():
        name = f"letsgo/{key}_height.json"
        save(assets / name, {**valid, **update})
        scenery[key] = {"scenes": [], "heights": name}
    save(assets / "letsgo/scenery.json", scenery)
    save(assets / "models/slice-models.json", [{"key": "hero", "file": "models/hero.glb",
                                               "clip_speed": [0, 1, 2]}])
    save(assets / "letsgo/battle/battle.json", {"stage": {"path": "letsgo/court.glb",
                                                           "maps": ["court"], "sha256": file_hash(assets / "letsgo/court.glb")}})


def inspect_in_blender(output, result):
    import bpy
    report = json.loads((output / "intake.json").read_text())
    lib = output / report["library"]
    data = {row["id"]: row for row in report["entries"]}
    bpy.ops.wm.open_mainfile(filepath=str(lib))
    ready = [row for row in data.values() if row["status"] == "available"]
    chunks = {r["resource"] for r in ready}
    assert len(chunks) == 6 and len(ready) == 10
    coll = bpy.data.collections
    tree = coll[data["kit/tree"]["blender_name"]]
    for row in ready:
        if row["resource"] != data["kit/tree"]["resource"]:
            continue
        alias = coll[row["blender_name"]]
        assert alias.asset_data and alias.get("intake_id") == row["id"]
        assert alias.children[0] == tree.children[0]
    paint_a, paint_b = data["kit/paint-a"], data["kit/paint-b"]
    assert paint_a["sha256"] == paint_b["sha256"] and paint_a["resource"] != paint_b["resource"]
    for row, original in ((paint_a, FILES["letsgo/kit/ground.png"]), (paint_b, FILES["variant/b/paint.png"])):
        expected = file_hash(NATIVE / original)
        assert report["resources"][row["resource"]]["dependencies"] == {"paint.png": expected}
        objects = coll[row["blender_name"]].all_objects
        packed = [n.image for obj in objects for slot in obj.material_slots if slot.material and slot.material.use_nodes
                  for n in slot.material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.image.packed_file]
        assert any(sha256(im.packed_file.data).hexdigest() == expected for im in packed)
    assert len({r["blender_name"] for r in ready}) == len(ready)
    height_text = bpy.data.texts[data["scenery/court/heights"]["blender_name"]].as_string()
    assert json.loads(height_text)["grid"] == [[0, .1], [.2, None]]
    assert data["scenery/court/heights"]["grid"] == {
        "width": 1, "height": 1, "res": 2, "sample_count": 4, "tree_count": 1, "null_samples": 1}
    for key in ("zero", "bool", "short", "rows", "nonfinite", "tree"):
        assert data[f"scenery/{key}/heights"]["status"] == "invalid"
    image_node = next(n for n in bpy.data.materials[data["kit/ground"]["blender_name"]].node_tree.nodes
                      if n.type == "TEX_IMAGE")
    assert image_node.image.packed_file and image_node.image.size[0] > 0
    assert {i: data["kit/" + i]["status"] for i in ("escape", "link", "bad-checksum", "outside-image")} == {
        "escape": "invalid", "link": "invalid", "bad-checksum": "invalid", "outside-image": "invalid"}
    assert data["kit/external"]["status"] == data["kit/missing"]["status"] == "missing"
    assert data["kit/notes"]["status"] == "unsupported"
    # Append through the normal library API with the originals physically moved away.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(lib), link=False) as (available, requested):
        requested.collections = [data["model/hero"]["blender_name"]]
    hero = requested.collections[0]
    bpy.context.scene.collection.children.link(hero)
    rig = next(obj for obj in hero.all_objects if obj.type == "ARMATURE")
    skinned = [obj for obj in hero.all_objects if any(mod.type == "ARMATURE" and mod.object == rig
                                                       for mod in obj.modifiers)]
    assert skinned and len(rig.data.bones) > 100 and any(obj.parent for obj in hero.all_objects)
    actions = sorted(action.name for action in bpy.data.actions)
    assert len(actions) == 9
    packed = [image for image in bpy.data.images if image.packed_file]
    assert packed and all(image.size[0] > 0 for image in packed)
    save(result, {"blender": bpy.app.version_string, "available_manifest_entries": len(ready),
                  "unique_resources": len(chunks), "standalone_image_and_height_grid_reopened": True,
                  "identical_glbs_with_distinct_external_texture_bytes_verified": True,
                  "physical_and_semantic_aliases_share_geometry": True, "long_name_collisions_checked": True,
                  "missing_inputs": 2, "rejected_inputs": 10, "unsupported_inputs": 1,
                  "height_grid": {"six_malformed_cases_rejected": True, "null_hole_preserved": True,
                                  "upsampled_spacing_checked": True},
                  "appended_model_after_removing_source_directory": {
                      "bones": len(rig.data.bones), "bound_skinned_objects": len(skinned),
                      "packed_images": len(packed), "actions": actions}})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blender", default="blender")
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--upstream-checkout", type=Path, help="also inventory a clean pinned upstream Git checkout")
    args = p.parse_args()
    importer = HERE / "import_manifests.py"
    def run(command, ok=True):
        proc = subprocess.run(command, capture_output=True, text=True)
        if (proc.returncode == 0) != ok:
            raise RuntimeError(proc.stdout[-6000:] + proc.stderr[-500:])
    with TemporaryDirectory() as tmp:
        work = Path(tmp)
        assets, library = work / "assets", work / "library"
        make_fixture(assets)
        blender = [args.blender, "-b", "--factory-startup", "--python-exit-code", "1", "-P"]
        call = [*blender, str(importer), "--", "--assets", str(assets), "--output"]
        run([*call, str(library)])
        run([*call, str(library)], ok=False)
        assets.rename(work / "assets-moved-away")
        result = work / "checks.json"
        run([*blender, str(Path(__file__).resolve()), "--", "--reopen", str(library), str(result)])
        empty = work / "empty-assets"
        empty.mkdir()
        run([*blender, str(importer), "--", "--assets", str(empty), "--output", str(work / "inventory")])
        inventory = json.loads((work / "inventory/intake.json").read_text())
        assert not inventory["library"] and not inventory["resources"] and not inventory["entries"]
        assert len(inventory["manifests"]) == 4 and all(v["status"] == "absent" for v in inventory["manifests"].values())
        receipt = json.loads(result.read_text())
        if args.upstream_checkout:
            checkout = args.upstream_checkout.resolve()
            head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
            if head != UPSTREAM_COMMIT:
                raise ValueError("upstream checkout differs from the pinned contract")
            run([*blender, str(importer), "--", "--checkout", str(checkout), "--output", str(work / "upstream")])
            upstream = json.loads((work / "upstream/intake.json").read_text())
            receipt["pinned_upstream_checkout"] = upstream
            assert not upstream["library"] and not upstream["resources"] and not upstream["entries"]
            assert all(manifest["status"] == "absent" for manifest in upstream["manifests"].values())
    receipt.update(upstream_contract_commit=UPSTREAM_COMMIT, no_manifests_gives_inventory_only=True,
                   existing_output_preserved=True, importer_sha256=file_hash(importer),
                   fixture_sha256=file_hash(Path(__file__)),
                   yuga_inputs={p: file_hash(NATIVE / p) for p in FILES.values()})
    save(args.report, receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    if "--reopen" in sys.argv:
        index = sys.argv.index("--reopen")
        inspect_in_blender(Path(sys.argv[index + 1]), Path(sys.argv[index + 2]))
    else:
        main()
