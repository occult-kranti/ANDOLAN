#!/usr/bin/env python3
"""Read-only replay of the selected catalog receipts and compressed raw report."""
import gzip
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    storage = json.loads((root / "storage.json").read_text())
    summary = json.loads((root / "native/summary.json").read_text())
    failures = []
    if summary["passed"] is not True or summary["checks"] != 34 or summary["selected_suites"] != ["desktop-landing-support-boundary", "desktop-landing-pause"] or len(summary["suites"]) != 2:
        failures.append("selected catalog summary")
    for row in summary["suites"]:
        report_path = "native/" + row["report"]
        if report_path in storage:
            record = storage[report_path]
            encoded = (root / record["gzip_path"]).read_bytes()
            raw = gzip.decompress(encoded)
            if sha(encoded) != record["gzip_sha256"] or len(encoded) != record["gzip_bytes"] or sha(raw) != record["raw_sha256"] or len(raw) != record["raw_bytes"]:
                failures.append(report_path + " storage")
        else:
            raw = (root / report_path).read_bytes()
        report = json.loads(raw)
        if sha(raw) != row["report_sha256"] or report["passed"] is not True or report["count"] != row["checks"] or not all(c["passed"] for c in report["checks"]):
            failures.append(report_path + " report")
        for stream in ("stdout", "stderr"):
            if sha((root / "native" / row[stream]).read_bytes()) != row[stream + "_sha256"]:
                failures.append(row[stream])
        if row["command"][row["command"].index("--fixed-fps") + 1] != "120" or row["exit_code"] != 0 or row["logged_errors"] or row["problems"]:
            failures.append(row["id"] + " execution")
    before = (root / "native/source-before.json").read_bytes()
    after = (root / "native/source-after.json").read_bytes()
    if before != after or sha(before) != summary["sources_before_sha256"] or sha(after) != summary["sources_after_sha256"]:
        failures.append("source closure")
    selfcheck = json.loads((root / "catalog-selfcheck.json").read_text())
    if not selfcheck["passed"] or selfcheck["count"] != 34 or not all(c["passed"] for c in selfcheck["checks"]):
        failures.append("catalog selfcheck")
    result = {"passed": not failures, "catalog_selfchecks": 34, "native_checks": 34, "native_suites": 2, "failures": failures, "scope": "Replay of existing integration receipts; no new engine or rendered acceptance."}
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
