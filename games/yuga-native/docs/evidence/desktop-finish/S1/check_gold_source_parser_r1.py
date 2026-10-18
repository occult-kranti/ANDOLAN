#!/usr/bin/env python3
"""S1 gold source/preservation and malformed-input checks. No engine invocation."""
import configparser
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops, ImageStat

PROJECT = Path(__file__).resolve().parents[4]
CHECKPOINT = "613ff5ca84313edfbcc2a70987919fa03bed5226"
MAP = PROJECT / "assets/hero-finish/s1-hammered-gold-roughness.png"
GENERATOR = PROJECT / "art/hero-finish/build_s1_gold.py"
checks = []


def check(name, passed, observed=None):
    checks.append({"name": name, "passed": bool(passed), "observed": observed})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline(relative):
    return subprocess.check_output(["git", "show", CHECKPOINT+":games/yuga-native/"+relative], cwd=PROJECT)


sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("s1_gold", GENERATOR)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
check("actual candidate passes original scalar admission", bool(generator.verify(MAP)))
manifest = json.loads(MAP.with_name("s1-manifest.json").read_text())
check("manifest pins generator and lossless source bytes",
      manifest["generator_sha256"] == sha(GENERATOR)
      and manifest["generator_source"] == "art/hero-finish/build_s1_gold.py"
      and manifest["maps"][0]["sha256"] == sha(MAP)
      and manifest["maps"][0]["bytes"] == MAP.stat().st_size)
finish = PROJECT / "scripts/rama_surface_finish.gd"
expected = baseline("scripts/rama_surface_finish.gd").replace(
    b'DETAIL_ROOT+"forged-gold-roughness.png"', b'DETAIL_ROOT+"s1-hammered-gold-roughness.png"')
check("finish differs only in gold map path", finish.read_bytes() == expected)
notice = PROJECT / "assets/hero-finish/NOTICE.md"
check("prior notice retained as exact prefix", notice.read_bytes().startswith(baseline("assets/hero-finish/NOTICE.md")))
preserved = ["assets/hero-finish/forged-gold-roughness.png", "assets/hero-finish/forged-gold-roughness.png.import",
             "assets/hero-finish/hair-bundle-roughness.png", "assets/hero-finish/hair-bundle-roughness.png.import",
             "assets/hero-finish/g1-manifest.json", "art/hero-finish/build_g1_maps.py",
             "assets/materials/rama-finish/woven-roughness.png", "assets/materials/rama-finish/woven-roughness.png.import",
             "assets/hero-finish/upper-hair-layers.json", "scripts/rama_upper_hair_layers.gd",
             "scripts/rama_surface_materials.gd", "shaders/rama_secondary_cloth.gdshader",
             "assets/heroes/rama-hero.glb", "assets/heroes/rama-hero-mid.glb", "assets/heroes/rama-hero-far.glb"]
pins = {}
for relative in preserved:
    path = PROJECT / relative
    pins[relative] = sha(path)
    check("checkpoint bytes preserved: "+relative, path.read_bytes() == baseline(relative))
config = configparser.ConfigParser(interpolation=None, strict=True)
config.read(MAP.with_name(MAP.name+".import"))
target = config["remap"]["path"].strip('"')
check("actual import source and destination are exact",
      config["deps"]["source_file"] == '"res://assets/hero-finish/'+MAP.name+'"'
      and target == "res://.godot/imported/"+MAP.name+"-c93c92f35fe086748d0140298caef508.ctex"
      and (PROJECT/target.removeprefix("res://")).is_file())
check("linear lossless full-mip import settings",
      all(config["params"][key] == value for key, value in {
          "compress/mode": "0", "compress/normal_map": "0", "process/hdr_as_srgb": "false",
          "process/channel_remap/red": "0", "mipmaps/generate": "true", "mipmaps/limit": "-1"}.items()))
image = Image.open(MAP)
old = Image.open(PROJECT/"assets/hero-finish/forged-gold-roughness.png")
delta = ImageChops.subtract(image, old)
check("higher roughness across every corresponding original UV texel",
      delta.getextrema()[0] > 0,
      {"delta_u8_range": delta.getextrema(), "old_mean": ImageStat.Stat(old).mean[0], "new_mean": ImageStat.Stat(image).mean[0],
       "scope": "Scalar comparison, not visible quality."})
with tempfile.TemporaryDirectory(prefix="s1-gold-adversaries-") as directory:
    scratch = Path(directory)
    cases = {"wrong dimensions": image.resize((256,256)), "wrong RGB format": image.convert("RGB"),
             "black roughness": Image.new("L", (512,512), 0), "repeat seam changed": image.copy(),
             "interior scalar changed": image.copy()}
    cases["repeat seam changed"].putpixel((0,17), 123)
    cases["interior scalar changed"].putpixel((253,271), 123)
    for i, (label, bad) in enumerate(cases.items()):
        path = scratch / (str(i)+".png")
        bad.save(path)
        rejected = False
        try:
            generator.verify(path)
        except ValueError:
            rejected = True
        check("rejects "+label, rejected)
    altered = scratch / "noncanonical-bytes.png"
    image.save(altered, compress_level=1)
    rejected = False
    try:
        generator.verify(altered)
    except ValueError:
        rejected = True
    check("rejects different PNG bytes despite identical decoded pixels", rejected)
record = {"passed": all(row["passed"] for row in checks), "checks": checks, "checkpoint": CHECKPOINT,
          "test_sha256": sha(Path(__file__)), "generator_sha256": sha(GENERATOR), "map_sha256": sha(MAP),
          "finish_sha256": sha(finish), "preserved_source_pins": pins,
          "scope": "CPU source identity, deterministic regeneration, authored scalar constraints and six malformed-input controls. Actual rendering and actual all-LOD runtime material sharing remain separate."}
output = Path(__file__).with_name("gold-source-check-r1.json")
output.write_text(json.dumps(record, indent=2, sort_keys=True)+"\n")
print(json.dumps({"passed": sum(row["passed"] for row in checks), "checks": len(checks), "report": str(output)}))
raise SystemExit(0 if record["passed"] else 1)
