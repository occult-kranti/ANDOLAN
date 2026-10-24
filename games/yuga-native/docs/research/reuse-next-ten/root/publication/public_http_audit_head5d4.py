"""Bounded independent public-byte audit. Run once per new observation directory."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / ".git").exists())
NATIVE = REPO / "games/yuga-native"
WEB = NATIVE / "tools/build-observatory/web"
BASELINE = Path("/workspace/scratch/production-stage-oct23/site-baseline/dist/site")
HEAD = "5d4de822e2078eb9918a44ebf6c10ddd8f024fd0"
SOURCE = "1ad9641e1f08e251c0605ed06bdf31775172bdbf"
BASE_REF = "176b6f8e71fcffd3d570d96e66643d8cb9893603"
SNAPSHOT = "5486ef1790f59d3cd14a85aac3c2969ba5c04452e57bfa30147225b915b7fa73"
RUN_ID = 40050620829
BASE_URL = "https://occult-kranti.github.io/ANDOLAN/"
OUT = HERE / "http-head5d4-r1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def request(url):
    return urllib.request.Request(url, headers={
        "User-Agent": "YUGA-independent-public-byte-audit",
        "Accept-Encoding": "identity", "Cache-Control": "no-cache"})


def main():
    if OUT.exists():
        raise SystemExit("Observation exists; preserve it and use a new explicit audit version.")
    OUT.mkdir(parents=True)
    with urllib.request.urlopen(request(
            f"https://api.github.com/repos/occult-kranti/ANDOLAN/actions/runs/{RUN_ID}"), timeout=30) as response:
        action = json.load(response)
    save("pages-run.json", action)
    assert action["head_sha"] == HEAD and action["status"] == "completed" and action["conclusion"] == "success"
    module_path = NATIVE / "tools/build-observatory/publish_site.py"
    spec = importlib.util.spec_from_file_location("yuga_publisher", module_path)
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)
    rel_publisher = module_path.relative_to(REPO).as_posix()
    pinned_publisher = subprocess.check_output(["git", "show", f"{HEAD}:{rel_publisher}"], cwd=REPO)
    assert pinned_publisher == module_path.read_bytes()
    selected = {name: path for name, path in publisher.files_under(WEB).items() if publisher.approved(name)}
    expected = {}
    for name, path in sorted(selected.items()):
        committed = subprocess.check_output(["git", "show", f"{HEAD}:{path.relative_to(REPO).as_posix()}"], cwd=REPO)
        assert committed == path.read_bytes(), name
        expected[name] = {"bytes": len(committed), "sha256": sha(committed)}
    assert len(expected) == 47 and sum(x["bytes"] for x in expected.values()) == 23170761
    baseline_files = {name: path for name, path in publisher.files_under(BASELINE).items()
                      if not name.startswith("production/")}
    baseline_census = publisher.census(baseline_files)
    baseline_digest = sha(json.dumps(baseline_census, sort_keys=True).encode())
    save("expected-approved-source.json", {"commit": HEAD, "publisher_sha256": sha(pinned_publisher), "files": expected})
    save("assembled-baseline-census.json", baseline_census)
    targets = []
    for name, value in expected.items():
        route = "production/" if name == "index.html" else "production/viewer/" if name == "viewer/index.html" else "production/" + name
        targets.append({"path": "production/" + name, "route": route,
                        "expected": value, "binding": "exact approved source at " + HEAD})
    targets.append({"path": "production/publication.json", "route": "production/publication.json", "expected": None,
                    "binding": "generated additive publication receipt"})
    for name in publisher.REQUIRED_BASELINE:
        route = "" if name == "index.html" else name.removesuffix("index.html")
        targets.append({"path": name, "route": route, "expected": baseline_census[name],
                        "binding": "supplied assembled pinned browser baseline; not historical deployed byte equality"})

    def fetch(target):
        url = BASE_URL + target["route"]
        row = {"path": target["path"], "url": url, "binding": target["binding"],
               "observed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        raw = b""
        try:
            with urllib.request.urlopen(request(url), timeout=45) as response:
                row.update({"http_status": response.status, "final_url": response.url,
                            "content_type": response.headers.get("Content-Type"),
                            "content_encoding": response.headers.get("Content-Encoding"),
                            "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified")})
                raw = response.read(64 * 1024 * 1024 + 1)
                if len(raw) > 64 * 1024 * 1024:
                    raise ValueError("Response exceeds publisher file bound")
            row.update({"bytes": len(raw), "sha256": sha(raw)})
            if target["expected"] is not None:
                row["expected"] = target["expected"]
                row["matches_expected_bytes"] = row["bytes"] == target["expected"]["bytes"] and row["sha256"] == target["expected"]["sha256"]
            if target["path"] in {"production/status.json", "production/publication.json"}:
                target_path = OUT / "captured" / target["path"]
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with target_path.open("xb") as stream:
                    stream.write(raw)
        except Exception as error:
            row["failure"] = type(error).__name__ + ": " + str(error)
        return row

    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(fetch, targets))
    save("http-responses.json", rows)
    checks = []
    def check(name, passed, detail=None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    check("all53 approved/generated/required-route responses return200 without transport failure",
          len(rows) == 53 and all(x.get("http_status") == 200 and "failure" not in x for x in rows))
    check("all47 approved static files exactly match committed source bytes",
          all(x.get("matches_expected_bytes") is True for x in rows if x["binding"].startswith("exact approved source")))
    check("five required browser route entries match supplied assembled baseline",
          all(x.get("matches_expected_bytes") is True for x in rows if not x["path"].startswith("production/")))
    publication = json.loads((OUT / "captured/production/publication.json").read_bytes())
    status_raw = (OUT / "captured/production/status.json").read_bytes()
    status = json.loads(status_raw)
    check("public deployment receipt pins exact Pageshead and separate browser baseline",
          publication["dashboard_source"] == HEAD and publication["baseline_source"] == BASE_REF)
    check("generated manifest binds the complete approved47file census", publication["dashboard_files"] == expected)
    check("generated baseline census matches all90supplied assembled files",
          publication["baseline_files"] == len(baseline_census) == 90 and publication["baseline_census_sha256"] == baseline_digest)
    check("public status exact SHA pins clean snapshot source rather than deploymenthead",
          sha(status_raw) == SNAPSHOT and status["source"] == {"branch": "game/yuga-native-production", "commit": SOURCE, "dirty": False})
    check("observation timestamp and snapshot mode are explicit and consistent",
          publication["data_mode"] == status["mode"] == "snapshot" and publication["observation_time"] == status["collected_at"] == "2026-10-24T01:37:11+00:00")
    jobs = collections.Counter(x.get("status") for x in status["jobs"])
    check("nine saved worker jobs are complete and markedCPU", len(status["jobs"]) == 9 and jobs == {"complete": 9}
          and all(x.get("device") == "CPU" for x in status["jobs"]), dict(jobs))
    check("eleven saved assets are present in the frozen status", len(status["assets"]) == 11)
    check("allthree published MP4s use video media type and exact source bytes",
          sum(x["path"].endswith(".mp4") for x in rows) == 3 and all(x.get("content_type", "").split(";")[0] == "video/mp4" and x.get("matches_expected_bytes") for x in rows if x["path"].endswith(".mp4")))
    result = {"schema": 1, "passed": all(x["passed"] for x in checks), "checks": checks,
              "audit_helper_sha256": sha(Path(__file__).read_bytes()),
              "preserved_predecessor_helper_sha256": "8098f3f3a6084f1e36d3e124e48d5d1698ccc76359cb7201287583f06e1400ad",
              "base_url": BASE_URL, "pages_run": {k: action[k] for k in ["id", "head_sha", "status", "conclusion", "html_url"]},
              "approved_source_files": len(expected), "approved_source_bytes": sum(x["bytes"] for x in expected.values()),
              "audited_http_responses": len(rows), "maximum_parallel_http_requests": 6,
              "snapshot_source": status["source"], "snapshot_sha256": sha(status_raw), "snapshot_observation_time": status["collected_at"],
              "saved_job_statuses": dict(jobs), "saved_assets": len(status["assets"]), "saved_sources": len(status["sources"]),
              "saved_milestone_statuses": dict(collections.Counter(x.get("status") for x in status["milestones"])),
              "scope": "Independent current public HTTP source-byte/provenance/route audit; not live telemetry or a browser interaction replay.",
              "limits": ["Saved worker and hardware records were observed at the snapshot timestamp, not queried as live telemetry.",
                         "Five retained entry bytes are bound to the supplied90file assembled pinned browser baseline; historical deployed-byte equality is not established.",
                         "HTTP200 and exact media bytes do not establish human gameplay, visual target quality, physical GPU timing or sound quality.",
                         "Root owns separate actual public-browser smoke and exported native-package proof."],
              "observed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    save("receipt.json", result)
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "http_responses": len(rows),
                      "failed": [x for x in checks if not x["passed"]], "output": str(OUT)}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
