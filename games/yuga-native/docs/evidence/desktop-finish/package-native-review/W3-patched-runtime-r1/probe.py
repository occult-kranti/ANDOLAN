"""Independent exact-variant/notice fixtures. No engine, export or large copy."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKAGER = ROOT / "tools/package-native.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--packager-sha", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists() and sha(PACKAGER) == args.packager_sha
    spec = importlib.util.spec_from_file_location("reviewed_packager", PACKAGER)
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    checks = []

    def check(name, okay, **facts):
        checks.append(dict(name=name, passed=bool(okay), **facts))

    def reject(name, callback, fragment):
        try:
            callback()
        except ValueError as exc:
            check(name, fragment in str(exc), actual_error=str(exc))
        else:
            check(name, False, actual_error=None)

    patched = p.patched_runtime_provenance(ROOT / p.PATCHED_RUNTIME_PROOF)
    original = p.public_runtime_provenance(ROOT / p.PUBLIC_RUNTIME_PROOF)
    check("fixed patched identity and source closure", p.PATCHED_LINUX_RUNTIME == {
        "bytes": 85447128,
        "sha256": "e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e",
        "version": "4.6.3.stable.custom_build",
    } and patched["source_patches"] == 1
        and patched["source_commit"] == "35e80b3a8822a9df9be390814b62f44c0a9c69e8"
        and patched["variant"] == "pipeline-low-priority-v1"
        and patched["patches"][0]["sha256"] == "df9032765f5fd348f3e1ef7f35c6de9148a74734172f94efe562e1753db8b4d7")
    check("unmodified history retains separate identity", original["source_patches"] == 0
        and original["kind"] == "unmodified-public-source-template-debug"
        and p.PUBLIC_LINUX_RUNTIME["sha256"] == "dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f")

    with tempfile.TemporaryDirectory(prefix="yuga-w3-patched-proof-") as folder:
        temp = Path(folder)
        exporter, runtime, old_runtime = [temp / s for s in ("exporter.fixture", "e69.fixture", "dce.fixture")]
        for path in (exporter, runtime, old_runtime):
            path.write_bytes(b"identity-reader fixture only; never executed")
        # Preserve fixed production admission constants. Only the binary I/O
        # reader is stubbed; all committed proof/license bytes are read for real.
        identities = {
            exporter: dict(bytes=1, sha256=p.PUBLIC_RUNTIME_EXPORTER_SHA),
            runtime: {k: p.PATCHED_LINUX_RUNTIME[k] for k in ("bytes", "sha256")},
            old_runtime: {k: p.PUBLIC_LINUX_RUNTIME[k] for k in ("bytes", "sha256")},
        }
        real_record = p.record
        reader = lambda path: copy.deepcopy(identities[path]) if path in identities else real_record(path)
        selected = SimpleNamespace(linux_engine=exporter, linux_runtime=runtime,
            linux_runtime_provenance=ROOT / p.PATCHED_RUNTIME_PROOF,
            linux_runtime_variant="pipeline-low-priority")
        expected = {
            "exporter": {**identities[exporter], "version": p.PUBLIC_RUNTIME_EXPORTER_VERSION,
                         "role": "PCK export and imported-font proof"},
            "linux_runtime": {**identities[runtime], "version": p.PATCHED_LINUX_RUNTIME["version"],
                              "kind": "patched-public-source-template-debug", "provenance": patched},
        }
        with patch.object(p, "record", side_effect=reader), patch.object(
                p.subprocess, "check_output", side_effect=AssertionError("Engine execution prohibited")) as engine:
            actual = p.linux_engine_selection(selected, expected)
            check("explicit exact variant positive final guard", actual == expected)
            changed = copy.copy(selected)
            del changed.linux_runtime_variant
            reject("e69 cannot enter default unmodified path", lambda: p.linux_engine_selection(changed, expected), "unmodified public binary")
            changed = copy.copy(selected); changed.linux_runtime_variant = "arbitrary-patched"
            reject("unknown variant rejected", lambda: p.linux_engine_selection(changed, expected), "Unknown Linux runtime variant")
            changed = copy.copy(selected); changed.linux_runtime = None; changed.linux_runtime_provenance = None
            reject("patched variant cannot be silently ignored", lambda: p.linux_engine_selection(changed, expected), "requires --linux-runtime")
            changed = copy.copy(selected); changed.linux_runtime_provenance = ROOT / p.PUBLIC_RUNTIME_PROOF
            reject("e69 with zero-patch proof rejected", lambda: p.linux_engine_selection(changed, expected), "pipeline-priority build proof")
            changed = copy.copy(selected); changed.linux_runtime = old_runtime
            reject("dce with patched variant rejected", lambda: p.linux_engine_selection(changed, expected), "pipeline-priority patched binary")
            changed = copy.copy(selected); changed.linux_engine = runtime
            reject("patched runtime cannot serve as exporter", lambda: p.linux_engine_selection(changed, expected), "official exporter")
            for name, edit in [
                ("altered manifest runtime kind", lambda d: d["linux_runtime"].update(kind="unmodified-public-source-template-debug")),
                ("altered manifest patch count", lambda d: d["linux_runtime"]["provenance"].update(source_patches=0)),
                ("altered manifest variant", lambda d: d["linux_runtime"]["provenance"].update(variant="pipeline-low-priority-v2")),
                ("altered manifest exporter role", lambda d: d["exporter"].update(role="bundled runtime")),
            ]:
                altered = copy.deepcopy(expected); edit(altered)
                reject(name, lambda: p.linux_engine_selection(selected, altered), "selection or provenance changed")
            check("all selection fixtures avoided subprocess", engine.call_count == 0)

        destination = temp / "bundle"; (destination / "NOTICE").mkdir(parents=True)
        for name in ("GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"):
            shutil.copyfile(ROOT / "NOTICE" / name, destination / "NOTICE" / name)
        p.copy_public_runtime_notice(destination, expected)
        mapping = patched["bundled_evidence"]
        check("all evidence mapping targets distinct and relative",
            len(set(mapping.values())) == len(mapping) and all(
                not Path(x).is_absolute() and ".." not in Path(x).parts for x in mapping.values()),
            evidence_count=len(mapping))
        copied = {source: {"bundle_path": target, **real_record(destination / target)} for source, target in mapping.items()}
        check("every final bundled evidence payload remains exact", all(
            {k: copied[source][k] for k in ("bytes", "sha256")} == pinned
            for source, pinned in patched["evidence"].items()))
        duplicate_names = {}
        for source, target in mapping.items():
            duplicate_names.setdefault(Path(source).name, []).append(target)
        duplicates = {k: v for k, v in duplicate_names.items() if len(v) > 1}
        check("baseline and patched duplicate basenames both survive", len(duplicates) >= 2
            and all(len(set(v)) == len(v) for v in duplicates.values()), mappings=duplicates)
        notice = (destination / "NOTICE/GODOT-RUNTIME.txt").read_text()
        readme = p.start_readme("linux", expected)
        check("readable runtime attribution explicitly patched", "one pipeline-priority patch" in notice
            and "Source patches: 1" in notice and "unmodified" not in notice
            and identities[runtime]["sha256"] in notice and identities[exporter]["sha256"] in notice)
        check("Linux launch text distinguishes patched runtime and official exporter",
            "patch" in readme.lower() and "unmodified" not in readme
            and "official Linux editor used for PCK export and font qualification" in readme)
        check("Windows launch text unaffected", p.start_readme("windows", expected) == p.start_readme("windows"))
        (destination / "NOTICE/GODOT-LICENSE.txt").write_bytes(b"incorrect notice")
        reject("wrong bundled license rejected", lambda: p.copy_public_runtime_notice(destination, expected), "attribution differs")
        shutil.copyfile(ROOT / "NOTICE/GODOT-LICENSE.txt", destination / "NOTICE/GODOT-LICENSE.txt")
        real_copy = shutil.copyfile
        def corrupt_one(source, target):
            value = real_copy(source, target)
            if Path(target).name == "proposed.patch": Path(target).write_bytes(b"wrong patch")
            return value
        with patch.object(p.shutil, "copyfile", side_effect=corrupt_one):
            reject("changed patch during proof copy rejected", lambda: p.copy_public_runtime_notice(destination, expected), "proof copy differs")
        def corrupt_earlier_after_last_copy(source, target):
            value = real_copy(source, target)
            if Path(target).name == "pipeline_hash_map_rd.proposed.h":
                (destination / mapping[p.PUBLIC_RUNTIME_PROOF]).write_bytes(b"earlier proof replaced later")
            return value
        with patch.object(p.shutil, "copyfile", side_effect=corrupt_earlier_after_last_copy):
            reject("late overwrite of earlier proof caught by final closure", lambda: p.copy_public_runtime_notice(destination, expected), "proof closure differs")

    assert sha(PACKAGER) == args.packager_sha
    report = dict(scope="Independent temporary Python fixtures using fixed production admission constants, mocked binary-identity reads and blocked subprocesses. Real committed build/patch/license records and real small notice copies. No engine, archive export or new package execution.",
        packager_sha256=args.packager_sha, reviewer_sha256=sha(Path(__file__)),
        passed=all(c["passed"] for c in checks), count=len(checks), checks=checks,
        evidence_mapping=copied)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "count": len(checks), "failed": [c for c in checks if not c["passed"]]}))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
