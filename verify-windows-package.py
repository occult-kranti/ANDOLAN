"""Exercise the exact Windows release archive using its own launcher and runtime."""
from hashlib import file_digest, sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from urllib.request import urlopen
from zipfile import ZipFile

ZIP_SHA = "6e8c27d8f030d231be80a60102e00eb4bd3732591333ac520b14042b3ac98a80"
SOURCE = "891d231b9e6c71eb484b3debdb3c5464896da5d3"
FIXTURE = "games/yuga-native/tests/hanuman_ability_integration_cases.gd"
FIXTURE_SHA = "0e68a3a280abf12e3caa45af62216443fa31da5239349021864f3339d88ed752"
EXPECTED = {
    "godot.exe": "ef90e929ba1a6a4322860285d97f40f4aa349c90329a91b0e8b55b8df0f4cb00",
    "launch.bat": "e22329e4d3819d8d7e90502e921f6a78518866bd154e13ba61e8a901394b2357",
    "yuga-native.pck": "2c6fbde84b2c1f06ed6cb614413d9d50b48308dbf2e4745360020c6a8cb2bdff",
}


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def adapt_fixture(original):
    if sha256(original).hexdigest() != FIXTURE_SHA:
        raise ValueError("Upstream integration fixture differs from the pinned revision")
    text = original.decode()
    start = text.index("func _source_hashes() -> Dictionary:")
    end = text.index("func _stress_primary()", start)
    text = text[:start] + '''func _source_hashes() -> Dictionary:
	return {"tested_pck": FileAccess.get_sha256(OS.get_environment("YUGA_TEST_PACK_FILE"))}


''' + text[end:]
    return text.replace("All pinned input files are present and unchanged during the run",
                        "The tested PCK is present and unchanged during the run")


def main(archive, out):
    if platform.system() != "Windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise ValueError("This verification requires native x64 Windows")
    out.mkdir(parents=True)
    if digest(archive) != ZIP_SHA:
        raise ValueError("Unexpected Windows archive digest")
    with ZipFile(archive) as release:
        release.extractall(out.parent / "extracted")
    game = out.parent / "extracted" / "yuga-native-windows-x86_64"
    contents = {name: digest(game / name) for name in EXPECTED}
    if contents != EXPECTED:
        raise ValueError("The bundled launcher or runtime payload changed")
    url = f"https://raw.githubusercontent.com/occult-kranti/ANDOLAN/{SOURCE}/{FIXTURE}"
    with urlopen(url, timeout=30) as source:
        fixture = out / "pack-integration.gd"
        fixture.write_bytes(adapt_fixture(source.read()).encode())
    env = {**os.environ, "YUGA_TEST_PACK_FILE": (game / "yuga-native.pck").as_posix()}

    def launch(name, extra):
        log = out / (name + "-engine.log")
        args = [os.environ["COMSPEC"], "/d", "/c", "call", "launch.bat",
                "--headless", "--audio-driver", "Dummy", "--log-file", log.as_posix(), *extra]
        proc = subprocess.run(args, cwd=game, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=150)
        (out / (name + "-process.log")).write_bytes(proc.stdout)
        if proc.returncode:
            raise RuntimeError(f"{name} exited {proc.returncode}, inspect engine and process logs")
        return log.read_text(encoding="utf8", errors="replace") + proc.stdout.decode("utf8", errors="replace")

    boot = launch("launcher", ["--quit-after", "180"])
    if "YUGA_NATIVE_BOOT_READY" not in boot:
        raise ValueError("Bundled launch.bat did not reach the native title")
    report = out / "integration.json"
    launch("trial", ["--fixed-fps", "60", "--script", fixture.as_posix(),
                     "--", "--report=" + report.as_posix()])
    result = json.loads(report.read_text())
    if result["passed"] != 111 or result["failed"] != 0 or result["sources"] != {"tested_pck": EXPECTED["yuga-native.pck"]}:
        raise ValueError("The Windows runtime failed the packaged integration contract")
    scenarios = [s for s in result["scenarios"] if not s["reduced"]]
    if {s["id"] for s in scenarios} != {"vajra_gada", "vajra_kavacha", "maruti_udayana", "lanka_dahan", "mountain_pulse"}:
        raise ValueError("Missing one or more of the five full-effects scenarios")
    receipt = {
        "scope": "Native Windows x64 headless launcher and combat integration through launch.bat",
        "windows": platform.platform(), "machine": platform.machine(),
        "godot": result["godot"], "zip_sha256": ZIP_SHA, "files_sha256": contents,
        "fixture_source": url, "fixture_source_sha256": FIXTURE_SHA, "fixture_tested_sha256": digest(fixture),
        "fixture_adaptation": "Checks the delivered PCK before and after instead of hashing unexported source files; same gameplay assertions.",
        "native_boot_ready": True, "assertions_passed": result["passed"], "assertions_failed": result["failed"],
        "revised_clips": ["fire", "cast2", "cast1", "tail_sweep", "mountain_pulse"], "scenarios": scenarios,
        "run_url": f"https://github.com/{env['GITHUB_REPOSITORY']}/actions/runs/{env['GITHUB_RUN_ID']}",
        "workflow_sha": env["GITHUB_SHA"],
    }
    (out / "windows-qualification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
