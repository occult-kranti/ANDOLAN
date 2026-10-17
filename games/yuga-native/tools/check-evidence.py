#!/usr/bin/env python3
"""Check archived evidence bytes, optionally from a committed Git tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
MANIFESTS = [
    "games/yuga-native/docs/evidence/mythic-published/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-batch2/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-ultimates-render-r1-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-ultimates-render-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-ultimates-render-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-ultimates-render-r3/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-traversal-render-r1-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-traversal-render-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-traversal-render-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-window-r1-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-window-r2-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-window-r3/archive-manifest.json",
    "games/yuga-native/docs/evidence/mythic-batch1/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-published/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-window-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-orientation-fix/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-window-r1-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-relay-render-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-siege-render-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-traversal-render-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-relay-render-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-siege-render-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-traversal-render-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-setup/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-render-r1-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-integration/archive-manifest.json",
    "games/yuga-native/docs/evidence/triad-qa/evidence-manifest.json",
    "games/yuga-native/docs/evidence/siege-published/archive-manifest.json",
    "games/yuga-native/docs/evidence/siege-window-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/siege-traversal-render-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/siege-setup/archive-manifest.json",
    "games/yuga-native/docs/evidence/siege-integration/archive-manifest.json",
    "games/yuga-native/docs/evidence/siege-render-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/siege-qa/evidence-manifest.json",
    "games/yuga-native/tests/evidence/native-network-final/manifest.json",
    "games/yuga-native/docs/evidence/motion-carry-restored/archive-manifest.json",
    "games/yuga-native/docs/evidence/confluence-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/confluence-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/confluence-package/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-poses-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-poses-r3/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-scene-r1/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-scene-r2/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-guard-r3-rejected/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-film-r4/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-film-package/archive-manifest.json",
    "games/yuga-native/docs/evidence/combat-film-published-r2/evidence-manifest.json",
    "games/yuga-native/tests/evidence/combat-film-qa-revision3-manifest.json",
    "games/yuga-native/tests/evidence/combat-film-qa-final-manifest.json",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-ref", help="Validate committed bytes instead of the working directory")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "rev-parse", "--verify", args.git_ref + "^{commit}"], cwd=ROOT, text=True).strip() if args.git_ref else None

    def read(relative):
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe evidence path")
        if revision:
            result = subprocess.run(["git", "show", revision + ":" + path.as_posix()], cwd=ROOT, capture_output=True)
            if result.returncode:
                raise FileNotFoundError(path.as_posix())
            return result.stdout
        return (ROOT / path).read_bytes()

    errors, checked = [], 0
    for name in MANIFESTS:
        try:
            manifest = json.loads(read(name))
            entries = manifest["files"]
            # Team QA reports pin repository-relative paths, while capture
            # archives pin members relative to their own manifest directory.
            members = [(Path(row["path"]), row) for row in entries] if isinstance(entries, list) else [
                (Path(name).parent / filename, item) for filename, item in entries.items()]
            for relative, item in members:
                try:
                    raw = read(relative)
                    expected = item["sha256"] if isinstance(item, dict) else item
                    if hashlib.sha256(raw).hexdigest() != expected:
                        raise ValueError("digest mismatch")
                    if isinstance(item, dict) and len(raw) != item["bytes"]:
                        raise ValueError("byte count mismatch")
                    checked += 1
                except (OSError, ValueError) as error:
                    errors.append({"path": str(relative), "error": str(error)})
        except (OSError, ValueError, KeyError) as error:
            errors.append({"path": name, "error": str(error)})
    report = {"passed": not errors, "revision": revision or "working directory", "files_checked": checked,
        "scope": "Archived bundle completeness and exact bytes; historical source pins are not asserted to match current runtime", "errors": errors}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
