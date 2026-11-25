"""Build the isolated, digest-pinned GunZRs animation probe using rustc and Python 3.12+."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
PIN = "485575b7451912ed1d62661c388663b08dce4faf"
DEST = Path(sys.argv[1]).resolve()
DEST.mkdir(parents=True, exist_ok=True)


def fetch(name, url, digest):
    target = DEST / name
    if not target.exists():
        req = Request(url, headers={"User-Agent": "YUGA-animation-reference/1.0"})
        with urlopen(req, timeout=60) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError(f"Download digest mismatch for {name}")
        target.write_bytes(content)
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Cached digest mismatch for {name}")
    return target


anim = fetch("gunz-anim.rs", f"https://raw.githubusercontent.com/OpenRsG/GunZRs/{PIN}/src/anim.rs",
             "dff5581defcfaeb4b350a03b5e31d85b8b738d116c73176452efeeeaa14373e5")
archive = fetch("glam-0.32.1.crate", "https://static.crates.io/crates/glam/glam-0.32.1.crate",
                "f70749695b063ecbf6b62949ccccde2e733ec3ecbbd71d467dca4e5c6c97cca0")
with tarfile.open(archive) as tar:
    tar.extractall(DEST, filter="data")

lines = anim.read_bytes().splitlines(keepends=True)


def original(start, end):
    return b"".join(lines[start - 1:end])


source = original(29, 59) + original(337, 357) + original(528, 548)
source += b"fn advance_upper(u: &mut Upper, a: &Speeds, uend: f32, dt: f32) {\n"
source += original(642, 651) + b"}\n"
(DEST / "original.rs").write_bytes(source)
subprocess.run(["rustc", "--edition=2021", "--crate-name", "glam", "--crate-type=rlib",
                "--cfg", 'feature="std"', "-C", "opt-level=2", str(DEST / "glam-0.32.1/src/lib.rs"),
                "-o", str(DEST / "libglam.rlib")], check=True)
subprocess.run(["rustc", "--edition=2021", "-C", "opt-level=2", str(HERE / "driver.rs"),
                "--extern", f"glam={DEST}/libglam.rlib", "-o", str(DEST / "probe")],
               env=dict(os.environ, GUNZ_FUNCTIONS=str(DEST / "original.rs")), check=True)
