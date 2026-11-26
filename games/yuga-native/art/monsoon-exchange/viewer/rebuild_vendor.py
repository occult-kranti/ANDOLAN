"""Bundle the pinned Three.js subset used by the Dust map viewer for the YUGA district."""

import argparse
import base64
import hashlib
import io
from pathlib import Path
import runpy
import subprocess
import tarfile
import tempfile
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[2]
REPO = NATIVE.parents[1]
DUST_VIEWER = runpy.run_path(str(NATIVE / "tools/source-map-lab/viewer/install.py"))
EXPORTS = """
export { ACESFilmicToneMapping, Box3, CanvasTexture, DirectionalLight, EquirectangularReflectionMapping, HemisphereLight, MathUtils,
  PerspectiveCamera, PMREMGenerator, Scene, Spherical, SRGBColorSpace, Vector3, WebGLRenderer } from 'three';
export { GLTFLoader } from './examples/jsm/loaders/GLTFLoader.js';
export { OrbitControls } from './examples/jsm/controls/OrbitControls.js';
export { RoomEnvironment } from './examples/jsm/environments/RoomEnvironment.js';
"""
BUNDLE = """
const esbuild = require('esbuild');
const path = require('node:path');
const [folder, output] = process.argv.slice(1);
esbuild.buildSync({entryPoints:[path.join(folder,'entry.mjs')], bundle:true, minify:true,
  alias: {three: path.join(folder,'build/three.module.min.js')}, format:'esm', target:'es2022',
  outfile:output, legalComments:'inline', banner:{js:'/* Three.js 0.180.0 • MIT • see THREE-LICENSE.txt */'}});
"""


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument(
        "--three-tgz", type=Path, help="Use an existing npm package offline"
    )
    args = arg.parse_args()
    if args.three_tgz:
        payload = args.three_tgz.read_bytes()
    else:
        with urlopen(DUST_VIEWER["PACKAGE"], timeout=60) as response:
            payload = response.read()
    if (
        base64.b64encode(hashlib.sha512(payload).digest()).decode()
        != DUST_VIEWER["INTEGRITY"]
    ):
        raise ValueError("Three.js archive failed the pinned package integrity check")
    with (
        tempfile.TemporaryDirectory() as temp,
        tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive,
    ):
        root = Path(temp)
        for name in [
            *DUST_VIEWER["FILES"],
            "examples/jsm/environments/RoomEnvironment.js",
        ]:
            member = archive.getmember("package/" + name)
            if not member.isfile():
                raise ValueError(f"Unexpected package member {name}")
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source:
                target.write_bytes(source.read())
        (root / "entry.mjs").write_text(EXPORTS, encoding="utf-8")
        subprocess.run(
            ["node", "-e", BUNDLE, str(root), str(HERE / "three.bundle.mjs")],
            cwd=REPO,
            check=True,
        )
        (HERE / "THREE-LICENSE.txt").write_bytes((root / "LICENSE").read_bytes())


if __name__ == "__main__":
    main()
