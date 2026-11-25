"""Run the pinned Ski or Die reconstruction's authored gameplay tests without SDL or game data."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

COMMIT = "0eac0671c90e21a16e663da7772b60710101ef7f"
MODULES = ("arena", "data", "game", "input", "participant", "roam", "snowball")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--rustc", default="rustc")
    args = parser.parse_args()
    digests = {}
    with TemporaryDirectory() as root:
        work = Path(root)
        for path in [f"src/{module}.rs" for module in MODULES] + ["tests/gameplay.rs"]:
            data = subprocess.check_output(["git", "-C", args.checkout, "show", f"{COMMIT}:{path}"])
            target = work / path
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(data)
            digests[path] = hashlib.sha256(data).hexdigest()
        # Compile exactly the simulation modules exercised by this integration test.
        # SDL-backed render and the executable each have a separate build path.
        (work / "src" / "lib.rs").write_text("".join(f"pub mod {module};\n" for module in MODULES))
        compiler = [args.rustc, "--edition=2021"]
        subprocess.run(compiler + ["--crate-name", "snowball_war", "--crate-type", "rlib",
                                  "src/lib.rs", "-o", "libsnowball_war.rlib"], cwd=work, check=True)
        subprocess.run(compiler + ["--test", "tests/gameplay.rs", "--extern",
                                  "snowball_war=libsnowball_war.rlib", "-o", "sim-test"], cwd=work, check=True)
        traces = []
        for _ in range(2):
            output = subprocess.check_output([work / "sim-test", "--test-threads=1"], text=True)
            traces.append(re.findall(r"^test (\w+) \.\.\. ok$", output, flags=re.MULTILINE))
        if traces[0] != traces[1] or len(traces[0]) != 18:
            raise ValueError("expected eighteen repeatable named passes at the pinned revision")
    result = {"repository": "tuunanet/rea-ski-or-die-reconstruction", "pin": COMMIT,
              "rustc": subprocess.check_output([args.rustc, "--version"], text=True).strip(),
              "source_sha256": digests, "repetitions": 2, "passing_tests": traces[0]}
    args.report.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
