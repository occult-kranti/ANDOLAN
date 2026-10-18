"""Bounded read-only standard GitHub Actions API observer; no artifact download."""
from pathlib import Path
import datetime
import json
import subprocess
import time

HERE = Path(__file__).resolve().parent
RUN = 39119998695
HEAD = "96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12"
PREFIX = "repos/occult-kranti/ANDOLAN/actions/runs/" + str(RUN)


def api(suffix=""):
    result = subprocess.run(["gh", "api", PREFIX + suffix], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    previous = None
    for attempt in range(35):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        run = api()
        assert run["head_sha"] == HEAD
        jobs = api("/jobs?per_page=100")
        assert jobs["total_count"] == len(jobs["jobs"])
        for job in jobs["jobs"]:
            assert job["head_sha"] == HEAD
        compact_run = {k: run.get(k) for k in ["id", "name", "head_sha", "head_branch", "event", "status", "conclusion", "run_attempt", "created_at", "updated_at", "run_started_at", "html_url", "path"]}
        compact_jobs = [{**{k: j.get(k) for k in ["id", "name", "head_sha", "status", "conclusion", "started_at", "completed_at", "html_url"]}, "steps": j["steps"]} for j in jobs["jobs"]]
        observation = dict(observed_at=now, api_run_url="https://api.github.com/" + PREFIX,
                           api_jobs_url="https://api.github.com/" + PREFIX + "/jobs?per_page=100",
                           run=compact_run, total_jobs=jobs["total_count"], jobs=compact_jobs)
        if attempt == 0:
            write("initial-api.json", observation)
        write("latest-api.json", observation)
        failures = [(j["name"], s["number"], s["name"], s["conclusion"]) for j in compact_jobs for s in j["steps"] if s["conclusion"] in ("failure", "timed_out", "cancelled")]
        active = [(j["name"], s["number"], s["name"]) for j in compact_jobs for s in j["steps"] if s["status"] == "in_progress"]
        state = (compact_run["status"], compact_run["conclusion"], active, failures)
        if state != previous:
            print(json.dumps(dict(observed_at=now, status=state[0], conclusion=state[1], active=active, failures=failures)), flush=True)
            with (HERE / "observations.jsonl").open("a") as out:
                out.write(json.dumps(observation) + "\n")
            previous = state
        if failures:
            write("failure-api.json", observation)
        if run["status"] == "completed" and all(j["status"] == "completed" for j in compact_jobs):
            write("terminal-api.json", observation)
            return
        time.sleep(45)
    raise RuntimeError("Observation window ended without a terminal run; no CI conclusion inferred")


if __name__ == "__main__":
    main()
