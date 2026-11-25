"""Assemble or verify the self-contained Hanuman artist and game handoff."""

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo, Path as ZipPath

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[3]
NATIVE = ROOT / "games/yuga-native"
RUST = ROOT / "games/yuga-rust"
STUDIO = PACK.relative_to(ROOT).as_posix()
GAME = "games/yuga-rust/downloads/yuga-rust-confluence.zip"
DEFAULT = Path("YUGA-Hanuman-Hero-Studio.zip")
SUMS = "SHA256SUMS.txt"
EXCLUDED = {"__pycache__", "node_modules", "target", ".git"}
SOURCES = """
THIRD_PARTY_NOTICES.md
package.json
package-lock.json
games/yuga/THIRD_PARTY_NOTICES.md
games/yuga/client/render-kit.ts
games/yuga/client/environment-light.ts
games/yuga/art/sources/makehuman/manifest.json
games/yuga/art/sources/makehuman/makehuman-assets-license.md
games/yuga-native/NOTICE/MAKEHUMAN-ASSET-LICENSE.md
games/yuga-native/NOTICE/ASSET-NOTICE.md
games/yuga-native/NOTICE/HANUMAN-ABILITY-AUDIO.json
games/yuga-native/NOTICE/HERO-PROVENANCE.json
games/yuga-native/NOTICE/RAMA-HERO-PROVENANCE.json
games/yuga-native/NOTICE/CONFLUENCE-DUEL-PROVENANCE.json
games/yuga-native/NOTICE/CONFLUENCE-WORLD-PROVENANCE.json
games/yuga-native/art/hanuman/NOTICE.md
games/yuga-native/art/hanuman/lookdev/madder-cloth-imagegen-albedo.png
games/yuga-native/art/four-hero-motion/models/hanuman.glb
games/yuga-native/art/four-hero-motion/media/art/hanuman.png
games/yuga-native/art/four-hero-motion/scripts/hanuman.md
games/yuga-native/art/four-hero-motion/README.md
games/yuga-native/art/four-hero-motion/media/video/hanuman.mp4
games/yuga-native/art/hanuman/lookdev/hanuman-imagegen-reference.png
games/yuga-native/tools/hanuman-art/build.py
research/game-resource-library/README.md
games/yuga-native/art/four-hero-motion/tools/blender_stills.py
games/yuga-native/art/four-hero-motion/tools/render/blender_scene.py
games/yuga-native/art/four-hero-motion/tools/render/verify_blend.py
games/yuga-native/art/four-hero-motion/tools/render/shots.json
games/yuga-native/art/hero-rama-lod/glb_lod.py
games/yuga-native/tools/hanuman-review/audit_glb.py
games/yuga-native/tools/hanuman-review/tail_curves.py
games/yuga-native/tools/hanuman-art/denoise.py
games/yuga-native/tools/hanuman-art/author_ability_motion.py
games/yuga-native/assets/design/hanuman-ability-kit.json
games/yuga-native/assets/design/rama-ability-kit.json
games/yuga-native/assets/world/confluence-map.json
games/yuga-native/assets/heroes/hanuman/hanuman-ability-motion.tres
games/yuga-rust/Cargo.toml
games/yuga-rust/Cargo.lock
games/yuga-rust/build.rs
games/yuga-rust/README.md
games/yuga-rust/tools/build_web.py
games/yuga-rust/tools/browser-package.mjs
games/yuga-rust/tools/test_browser.mjs
games/yuga-rust/tools/test_match.mjs
games/yuga-rust/tools/test_squad_rooms.mjs
games/yuga-rust/tools/pack_rama.py
games/yuga-rust/tools/serve_rooms.mjs
games/yuga-rust/tools/room-wasm.mjs
games/yuga-rust/tools/test_groom_detail.mjs
games/yuga-rust/tools/test_groom_visibility.mjs
games/yuga-rust/tools/capture_hanuman_cast.mjs
games/yuga-rust/tools/test_practice_coach.mjs
games/yuga-rust/tools/test_hanuman_release.mjs
games/yuga-rust/tools/test_hanuman_title.mjs
""".split()
FIRST = """# Hanuman Hero Studio

[Play Confluence](games/yuga-rust/downloads/yuga-rust-confluence.zip) · [Open the complete Blender scene]({studio}/blender/hanuman.blend) · [Watch the performance]({studio}/media/video/hanuman-showcase.mp4) · [View the portrait]({studio}/media/images/hanuman-beauty.webp)

**To play**, extract the linked Confluence ZIP, then open `yuga-rust.html` in a WebGL 2 desktop browser. Its `PLAY.txt` includes private matches for two or six players using the bundled Node room server.

**To edit**, open `{studio}/blender/hanuman.blend` in Blender 4.3.2. The [facial action library]({studio}/expressions/README.md) includes its own editable Blender project and rendered expression studies. The finished model and the separate editable groom are in the adjacent `models` directory. The four original tail curves, source rig, garment image, studio scripts and art notices are included under their repository paths. Open `tools/finish.py` in the focused package for the source model build.

The [artist handoff]({studio}/HANDOFF.md), [studio README]({studio}/README.md) and [roadmap]({studio}/ROADMAP.md) explain the deliverables. The game's Rust simulation, browser source, room host and source fixtures accompany the compiled game. The full ANDOLAN checkout provides additional world and Rama art inputs for a complete game rebuild. The game already includes their playable assets and its own third-party notices.

From this extracted directory, verify all entries with `sha256sum -c SHA256SUMS.txt`. To verify the ZIP itself, use `python {studio}/tools/package_finish.py --verify PATH_TO_ZIP`. The adjacent distribution `.sha256` file verifies the whole ZIP.
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def need(condition, message):
    if not condition:
        raise ValueError(message)


def include(path):
    return (
        path.is_file()
        and not path.is_symlink()
        and not any(
            s.startswith(".") or s in EXCLUDED for s in path.relative_to(ROOT).parts
        )
        and not path.name.endswith((".pyc", ".pyo", ".blend1", ".bak", ".part", "~"))
    )


def inputs():
    paths = {ROOT / n for n in [GAME, *SOURCES]}
    for folder in (
        PACK,
        RUST / "src",
        RUST / "assets",
        RUST / "tests",
        RUST / "web",
        NATIVE / "NOTICE/DejaVu-font",
    ):
        paths.update(p for p in folder.rglob("*") if include(p))
    # Include the test fixtures compiled directly into the gameplay/authority
    # sources, preserving the same effective include paths in a fresh checkout.
    fixed = re.compile(r'include_(?:str|bytes)!\(\s*"([^"]+)"\s*\)', re.MULTILINE)
    for source in [p for p in paths if p.suffix == ".rs"]:
        for literal in fixed.findall(source.read_text()):
            target = (source.parent / literal).resolve()
            need(
                target.is_relative_to(ROOT),
                f"Unexpected Rust include outside checkout: {source}",
            )
            paths.add(target)
    for path in paths:
        need(include(path), f"Missing or unsuitable package input: {path}")
    return {p.relative_to(ROOT).as_posix(): p for p in paths}


def check_sources(root):
    focused = root / STUDIO
    for name in (
        "README.md",
        "ROADMAP.md",
        "HANDOFF.md",
        "QA.md",
        "evidence/review-release.json",
    ):
        need((focused / name).is_file(), f"Focused studio document missing: {name}")
    model = digest(focused / "models/hanuman-enhanced.glb")
    build = load(focused / "evidence/build.json")
    need(model == build["playable_sha256"], "Hero GLB differs from assembly receipt")
    need(
        digest(focused / "models/hanuman-groom.blend")
        == build["editable_groom_sha256"],
        "Editable groom mismatch",
    )
    scene = load(focused / "evidence/editable-scene.json")
    need(
        scene["source_glb_sha256"] == model
        and scene["sha256"] == digest(focused / "blender/hanuman.blend"),
        "Editable Blender studio mismatch",
    )
    expressions = load(focused / "expressions/verification.json")
    need(
        expressions["source_sha256"] == model
        and expressions["source_file_unchanged"]
        and expressions["action_library_sha256"]
        == digest(focused / "expressions/hanuman-face-actions.blend"),
        "Expression action library differs from the verified hero study",
    )
    for name in (
        "images/hanuman-beauty.webp",
        "images/matched-studies.webp",
        "video/hanuman-showcase.mp4",
    ):
        media = focused / "media" / name
        proof = load(focused / "media" / Path(name).with_suffix(".json").as_posix())
        need(
            proof["media_sha256"] == digest(media),
            f"Media differs from its render receipt: {name}",
        )
        inputs = (
            [proof["source_sha256"]]
            if "source_sha256" in proof
            else [m["sha256"] for m in proof["models"]]
        )
        need(model in inputs, f"Media references a different hero: {name}")
    game = load(focused / "evidence/packaged-game.json")
    need(
        game["model_sha256"] == model and game["zip_sha256"] == digest(root / GAME),
        "Playable archive differs from the tested model or ZIP",
    )
    review_media = load(focused / "evidence/review-presentation.json")["render_check"]
    need(
        review_media["movie_sha256"]
        == digest(focused / "media/video/hanuman-showcase.mp4")
        and review_media["beauty_sha256"]
        == digest(focused / "media/images/hanuman-beauty.webp")
        and review_media["matched_sha256"]
        == digest(focused / "media/images/matched-studies.webp"),
        "Independent render review and archived media differ",
    )
    coach = load(focused / "evidence/drill-playthrough.json")
    need(
        coach["passed"]
        and coach["zip_sha256"] == game["zip_sha256"]
        and coach["gameplay_png_sha256"]
        == digest(focused / "evidence/drill-playthrough.png")
        and coach["coach_png_sha256"] == digest(focused / "evidence/coach-complete.png")
        and "5/5 techniques demonstrated" in coach["coach_completion"]
        and coach["coach_steps"][-1]["count"] == 0,
        "Coach completion or reset receipt and playthrough images differ",
    )
    review = load(focused / "evidence/review-release.json")
    need(
        review["enhanced"]["sha256"] == model
        and review["release"]["archive_sha256"] == game["zip_sha256"],
        "Independent release review and studio game differ",
    )
    live = load(focused / "evidence/finish-live.json")
    visibility = load(focused / "evidence/groom-visibility.json")
    need(
        live["passed"]
        and live["archive_sha256"] == game["zip_sha256"]
        and visibility["zip_sha256"] == game["zip_sha256"]
        and visibility["embedded_hanuman_sha256"] == model,
        "Live ability or groom visibility check references another game",
    )
    lane = load(focused / "evidence/packaged-lane.json")
    need(
        lane["zip_sha256"] == game["zip_sha256"]
        and lane["html_sha256"] == game["html_sha256"],
        "Lane playthrough covers another release",
    )
    rooms = load(focused / "evidence/packaged-rooms.json")
    need(
        rooms["result"] == "pass"
        and rooms["squad_seats"] == 6
        and rooms["archive"]["sha256"] == game["zip_sha256"],
        "Expected completed six-seat portable room verification",
    )
    with (root / GAME).open("rb") as stream, ZipFile(stream) as nested:
        inner = json.loads(nested.read("build.json"))
        need(
            inner["blobs"]["hero"]["sha256"] == model
            and inner["html_sha256"] == game["html_sha256"]
            and nested.testzip() is None,
            "Playable ZIP has corrupt or stale content",
        )


def entry(name):
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = (
        ZIP_STORED
        if name.endswith((".zip", ".png", ".jpg", ".webp", ".mp4", ".gz"))
        else ZIP_DEFLATED
    )
    return info


def verify(archive):
    with ZipFile(archive) as zipped:
        names = zipped.namelist()
        need(len(set(names)) == len(names), "Duplicate archive entry")
        checks = {}
        for line in zipped.read(SUMS).decode().splitlines():
            value, name = line.split("  ", 1)
            need(
                re.fullmatch("[0-9a-f]{64}", value) and name not in checks,
                "Invalid manifest row",
            )
            checks[name] = value
        need(set(names) == {SUMS, *checks}, "Manifest membership mismatch")
        for name, value in checks.items():
            need(
                not Path(name).is_absolute() and ".." not in Path(name).parts,
                "Unsafe archive path",
            )
            with zipped.open(name) as stream:
                need(
                    hashlib.file_digest(stream, "sha256").hexdigest() == value,
                    f"Digest mismatch: {name}",
                )
        check_sources(ZipPath(zipped))
    return len(names)


def pack(output):
    output = output.resolve()
    need(
        not output.is_relative_to(PACK),
        "Choose an output outside the focused source directory",
    )
    check_sources(ROOT)
    paths = inputs()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
        staged = Path(scratch) / output.name
        checks = {}
        with ZipFile(staged, "w", compression=ZIP_DEFLATED, compresslevel=6) as zipped:
            for name in sorted([*paths, "START_HERE.md"]):
                if name == "START_HERE.md":
                    data = FIRST.format(studio=STUDIO).encode()
                    zipped.writestr(entry(name), data)
                    checks[name] = hashlib.sha256(data).hexdigest()
                else:
                    hasher = hashlib.sha256()
                    with paths[name].open("rb") as stream, zipped.open(
                        entry(name), "w"
                    ) as out:
                        while chunk := stream.read(1024 * 1024):
                            out.write(chunk)
                            hasher.update(chunk)
                    checks[name] = hasher.hexdigest()
            manifest = "".join(f"{checks[k]}  {k}\n" for k in sorted(checks))
            zipped.writestr(entry(SUMS), manifest.encode())
        count = verify(staged)
        checksum = digest(staged)
        sidecar = Path(scratch) / (output.name + ".sha256")
        sidecar.write_text(f"{checksum}  {output.name}\n")
        os.replace(staged, output)
        os.replace(sidecar, output.with_name(sidecar.name))
    print(f"{output}: {count} files, {output.stat().st_size} bytes, SHA-256 {checksum}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--output", type=Path, default=DEFAULT)
    options.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        print(f"{verify(args.verify)} verified entries. SHA-256 {digest(args.verify)}")
    else:
        pack(args.output)
