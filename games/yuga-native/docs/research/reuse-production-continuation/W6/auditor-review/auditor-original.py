#!/usr/bin/env python3
"""Audit a published checkpoint against its committed static bytes.

Adapted from the repository's frozen public_http_audit_head5d4.py. Historical
receipts stay immutable; this version accepts exact revisions and a fresh output
directory instead of copying a new validator for every publication. It checks
public delivery, not live workers, visual quality or game performance.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import publish_site as publisher


def digest(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def expected_files(root, source):
    prefix = "games/yuga-native/tools/build-observatory/web/"
    publisher_path = "games/yuga-native/tools/build-observatory/publish_site.py"
    if git(root, "show", f"{source}:{publisher_path}") != Path(publisher.__file__).read_bytes():
        raise ValueError("Use the publisher from the exact audited source")
    selected = {}
    for entry in git(root, "ls-tree", "-rz", source, "--", prefix).split(b"\0"):
        if not entry:
            continue
        meta, name_bytes = entry.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        name = name_bytes.decode().removeprefix(prefix)
        if publisher.approved(name):
            if mode != "100644" or kind != "blob":
                raise ValueError(f"Unsupported published Git object: {name}")
            raw = git(root, "cat-file", "blob", blob)
            if len(raw) > publisher.MAX_FILE:
                raise ValueError("Committed file exceeds publication bound")
            selected[name] = digest(raw)
    if not publisher.REQUIRED_WEB <= selected.keys():
        raise ValueError("Incomplete committed publication")
    if sum(item["bytes"] for item in selected.values()) > publisher.MAX_WEB_TOTAL:
        raise ValueError("Committed publication exceeds total bound")
    snapshot = json.loads(git(root, "show", f"{source}:{prefix}status.json"))
    return selected, snapshot


def fetch(base, route, expected=None):
    url = base.rstrip("/") + "/" + route
    row = {"route": route, "url": url}
    raw = b""
    try:
        request = Request(url, headers={"User-Agent": "YUGA-public-byte-audit",
                                       "Accept-Encoding": "identity", "Cache-Control": "no-cache"})
        with urlopen(request, timeout=45) as response:
            row.update(http_status=response.status, final_url=response.url,
                       content_type=response.headers.get("Content-Type"))
            raw = response.read(publisher.MAX_FILE + 1)
        if len(raw) > publisher.MAX_FILE:
            raise ValueError("Response exceeds publication bound")
        row.update(digest(raw))
        if expected is not None:
            row["matches_expected"] = digest(raw) == expected
    except Exception as error:
        row["failure"] = f"{type(error).__name__}: {error}"
    return row, raw


def audit(root, source, baseline_ref, base_url, output):
    if not publisher.SHA.fullmatch(source) or not publisher.SHA.fullmatch(baseline_ref):
        raise ValueError("Full source and browser-baseline commit IDs required")
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Expected an explicit credential-free site URL")
    expected, frozen_snapshot = expected_files(root, source)
    output.mkdir(parents=True, exist_ok=False)
    targets = [("production/" + name, value) for name, value in sorted(expected.items())]
    targets += [("production/publication.json", None)]
    targets += [(name, None) for name in publisher.REQUIRED_BASELINE]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda target: fetch(base_url, *target), targets))
    rows = [row for row, _ in results]
    bodies = {row["route"]: raw for row, raw in results}
    checks = []
    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})
    check("Every requested static, receipt and browser entry returned HTTP200",
          all(row.get("http_status") == 200 and "failure" not in row for row in rows))
    check("Every approved static file exactly matches committed bytes",
          all(row.get("matches_expected") is True for row in rows[:len(expected)]))
    try:
        published = json.loads(bodies["production/publication.json"])
        snapshot = json.loads(bodies["production/status.json"])
    except (ValueError, KeyError):
        published, snapshot = {}, {}
    check("Publication pins exact dashboard and separate browser source",
          published.get("dashboard_source") == source and published.get("baseline_source") == baseline_ref)
    check("Publication inventory matches the complete committed approved census",
          published.get("dashboard_files") == expected)
    check("Snapshot is exact saved data with clean observed source",
          snapshot == frozen_snapshot and snapshot.get("mode") == "snapshot"
          and snapshot.get("source", {}).get("dirty") is False)
    check("Observation time remains the original saved observation",
          bool(snapshot.get("collected_at")) and published.get("observation_time") == snapshot.get("collected_at")
          and published.get("data_mode") == "snapshot")
    receipt = {"schema": 1, "passed": all(c["passed"] for c in checks),
               "source": source, "baseline_source": baseline_ref,
               "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "checks": checks, "responses": rows, "expected_files": expected,
               "snapshot_source": snapshot.get("source"),
               "auditor_sha256": digest(Path(__file__).read_bytes())["sha256"],
               "limits": ["Browser entry availability is checked; full baseline census preservation belongs to the publisher receipt.",
                          "This is saved snapshot delivery, not live worker activity, game execution or art acceptance."]}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    for name in ("publication.json", "status.json"):
        (output / name).write_bytes(bodies.get("production/" + name, b""))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.workspace, args.source, args.baseline_ref, args.base_url, args.output)
    print(json.dumps({"passed": result["passed"], "checks": result["checks"], "responses": len(result["responses"])}))
    raise SystemExit(0 if result["passed"] else 1)
