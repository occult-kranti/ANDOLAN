#!/usr/bin/env python3
"""Recheck the complete motion archive without temporary source files or an engine."""
import gzip
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    rows = []
    for case in ("landing120", "full"):
        comparison = json.loads((root / (case + "-comparison.json")).read_text())
        for role in ("baseline", "candidate"):
            path = root / case / role
            archive = json.loads((path / "archive.json").read_text())
            compressed = (path / archive["capture"]["path"]).read_bytes()
            raw = gzip.decompress(compressed)
            capture = json.loads(raw)
            run = json.loads((path / "run.json").read_text())
            identities = all(sha((path / name).read_bytes()) == pin["sha256"] and
                             (path / name).stat().st_size == pin["bytes"]
                             for name, pin in archive["originals"].items())
            identities &= sha(compressed) == archive["capture"]["gzip_sha256"]
            identities &= len(compressed) == archive["capture"]["gzip_bytes"]
            identities &= sha(raw) == archive["capture"]["raw_sha256"] == run["report_sha256"]
            identities &= len(raw) == archive["capture"]["raw_bytes"]
            identities &= comparison["inputs"][role]["capture_sha256"] == sha(raw)
            identities &= comparison["inputs"][role]["run_sha256"] == sha((path / "run.json").read_bytes())
            identities &= all(sha((path / "originals" / shot["file"]).read_bytes()) == shot["sha256"]
                              for shot in capture["shots"])
            identities &= sha((path / "normal-speed.mp4").read_bytes()) == archive["video"]["sha256"]
            rows.append({"case": case, "role": role, "passed": bool(identities),
                         "original_pngs": len(capture["shots"]), "raw_capture_sha256": sha(raw),
                         "complete": capture["complete"] and run["complete"],
                         "native_gates": len(capture["checks"]),
                         "native_gates_passed": all(x["passed"] for x in capture["checks"]),
                         "matched_control_checks": len(comparison["checks"]),
                         "matched_controls_passed": comparison["passed"]})
    result = {"passed": all(r["passed"] and r["complete"] and r["native_gates_passed"] and
                            r["matched_controls_passed"] for r in rows), "runs": rows,
              "original_pngs": sum(r["original_pngs"] for r in rows),
              "scope": "Portable byte identity and completed receipt audit; no rerender, image scoring or motion acceptance."}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
