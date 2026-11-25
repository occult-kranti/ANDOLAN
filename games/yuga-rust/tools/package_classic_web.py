#!/usr/bin/env python3
"""Package the existing production YUGA site, including the classic Rust sparring lab."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[3]
CLASSIC = ROOT / "games/yuga"
RUST = ROOT / "games/yuga-rust"
DEFAULT_ZIP = RUST / "downloads/yuga-rust-classic.zip"
DEFAULT_REPORT = ROOT / "games/yuga-native/docs/rust-rebuild/deep-search/classic-web-package.json"
WASM = CLASSIC / "client/assets/classic-roster.wasm"
RUST_NOTICES = RUST / "classic-wasm/THIRD-PARTY.txt"

PLAY = """YUGA • Classic hero sparring

Extract the entire ZIP. From the directory containing index.html, run

    python3 -m http.server 8000 --bind 127.0.0.1

On Windows you can use py -m http.server 8000 --bind 127.0.0.1.
Open http://127.0.0.1:8000/ in a desktop browser with WebGL 2 and WebAssembly.
The same files can be uploaded to a static HTTP(S) host, including a subdirectory.
Keep index.html and assets/ together.

Choose one of the fourteen heroes, then select Hero sparring. This mode runs the
classic Rust combat simulation locally. Move with WASD, aim with the mouse,
fire with the primary button, and use Q, E and R for the three abilities. The
roster and in-game controls show the selected hero's kit and any changed bindings.

The lobby also provides the classic bot match. Online team matches use a
separately hosted YUGA arena server. This download includes the static site.
See Credits & licenses in the game and THIRD-PARTY-RUST.txt for attribution.
BUILD_INFO.json lists the packaged game files and their SHA-256 hashes.
"""

WASM_PROBE = """
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const ids = JSON.parse(process.argv[1]);
const {instance} = await WebAssembly.instantiate(readFileSync(0), {});
const e = instance.exports;
for (const name of ['roster_input_ptr','roster_input_capacity','roster_reset','roster_command',
  'roster_snapshot_ptr','roster_snapshot_len','roster_error_ptr','roster_error_len'])
    assert.equal(typeof e[name], 'function', name);
function command(op, value) {
  const data = new TextEncoder().encode(value);
  assert.ok(data.length <= e.roster_input_capacity());
  new Uint8Array(e.memory.buffer,e.roster_input_ptr(),data.length).set(data);
  assert.equal(op(data.length), 1);
  return JSON.parse(new TextDecoder().decode(
    new Uint8Array(e.memory.buffer,e.roster_snapshot_ptr(),e.roster_snapshot_len())));
}
let casts = 0;
for (const id of ids) {
  for (let slot=0;slot<3;slot++) {
    const reset=command(e.roster_reset,id);
    assert.equal(reset.tick,0);
    assert.equal(reset.units.find(u=>u.id==='self').hero,id);
    const action=command(e.roster_command,JSON.stringify({cast:slot,ticks:1}));
    assert.equal(action.accepted,true,id+' slot '+slot);
    assert.equal(action.tick,1);
    casts++;
  }
}
console.log(JSON.stringify({heroes:ids.length,accepted_casts:casts}));
"""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_text(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def checked_assets():
    # Same pinned original Blender rig manifests checked in games/yuga/tools/package-browser.py.
    groups = {}
    for key in ("hero", "unit"):
        models = json.loads((CLASSIC / f"art/{key}-assets.json").read_text())["models"]
        groups[key] = {m["id"]: m["sha256"] for m in models}
        require(len(groups[key]) == len(models), f"Duplicate {key} model IDs")
    require(len(groups["hero"]) == 14, "Expected all fourteen original hero models")
    return groups


def inspect(files, groups):
    html = files["index.html"]
    for marker in (b"sparring-play", b"RUST SPARRING", b"yuga-notices"):
        require(marker in html, f"Missing sparring entry or notices in built index: {marker!r}")
    models = {name: sha(data) for name, data in files.items() if name.endswith(".glb")}
    expected = sorted(h for group in groups.values() for h in group.values())
    require(sorted(models.values()) == expected, "Exported rigs differ from the two canonical art manifests")
    require(all(name.encode() in html for name in models), "An emitted model URL is missing from the application")
    wasm = WASM.read_bytes()
    encoded = base64.b64encode(wasm)
    if encoded in html:
        storage = "index.html (inline data URL)"
        # Instantiate bytes recovered from the packaged HTML, as the game does.
        offset = html.index(encoded)
        actual = base64.b64decode(html[offset:offset+len(encoded)], validate=True)
    else:
        matching = [k for k, v in files.items() if k.endswith(".wasm") and v == wasm]
        require(len(matching) == 1 and matching[0].encode() in html,
                "The built application does not reference the pinned WebAssembly module")
        storage = matching[0]
        actual = files[storage]
    require(actual == wasm, "Different Rust authority in the website")
    probe = run(["node", "--input-type=module", "-e", WASM_PROBE, json.dumps(list(groups["hero"]))],
                input=actual, stdout=subprocess.PIPE)
    return {"hero_models": len(groups["hero"]), "unit_models": len(groups["unit"]),
            "glb_bytes": sum(len(files[path]) for path in models),
            "wasm": {"storage": storage, "bytes": len(actual), "sha256": sha(actual),
                     "extracted_abi_check": json.loads(probe.stdout)}}


def write_archive(dest, files):
    # Stable permissions, member order and modification dates across clean checkouts.
    with ZipFile(dest, "w") as archive:
        for name in sorted(files):
            entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, files[name], compress_type=ZIP_DEFLATED, compresslevel=7)


def package(output, report, check):
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    groups = checked_assets()
    require(WASM.is_file() and RUST_NOTICES.is_file(), "Restore the tracked classic WebAssembly and its license notices")
    with TemporaryDirectory(prefix=".classic-build-", dir=output.parent) as tmp:
        stage = Path(tmp) / "site"
        # Existing production settings inline JS, CSS, audio and fonts; GLBs retain relative URLs.
        run(["node", "node_modules/vite/bin/vite.js", "build", "--config", "vite.yuga.config.ts",
             "--outDir", str(stage), "--emptyOutDir"])
        run(["node", "games/yuga/tools/attach-notices.mjs", str(stage / "index.html")])
        files = {p.relative_to(stage).as_posix(): p.read_bytes() for p in stage.rglob("*") if p.is_file()}
        files["PLAY.txt"] = PLAY.encode()
        files["THIRD-PARTY-RUST.txt"] = RUST_NOTICES.read_bytes()
        entries = {k: {"bytes": len(v), "sha256": sha(v)} for k, v in sorted(files.items())}
        manifest = {"schema": 1, "format": "static HTTP site", "entry": "index.html",
                    "sparring_button": "Hero sparring", "models_sha256": groups, "files": entries}
        files["BUILD_INFO.json"] = json_text(manifest).encode()
        candidate = Path(tmp) / "classic.zip"
        write_archive(candidate, files)
        require(candidate.stat().st_size < 100_000_000, "Archive exceeds 100 MB")
        with ZipFile(candidate) as archive:
            require(archive.testzip() is None, "ZIP integrity check failed")
            require(archive.namelist() == sorted(files), "Unexpected archive entries")
            restored = {name: archive.read(name) for name in archive.namelist()}
            require(restored == files, "Reopened archive differs from production build")
            evidence = inspect(restored, groups)
        evidence.update({"schema": 1, "filename": output.name, "archive_bytes": candidate.stat().st_size,
                         "sha256": sha(candidate.read_bytes()), "files": len(files)})
        if check:
            require(output.is_file() and sha(output.read_bytes()) == evidence["sha256"],
                    "Rebuild differs from the published ZIP")
        else:
            os.replace(candidate, output)
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json_text(evidence), encoding="utf-8")
        print(json_text(evidence))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check-rebuild", action="store_true",
                        help="Rebuild into a temporary directory and compare with the existing ZIP")
    options = parser.parse_args()
    package(options.output, options.report, options.check_rebuild)
