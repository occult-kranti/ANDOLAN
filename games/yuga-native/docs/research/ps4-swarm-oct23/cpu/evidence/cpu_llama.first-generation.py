#!/usr/bin/env python3
"""Explicit, pinned CPU build/download/qualification; no ordinary-setup hook."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


MANIFEST = json.loads(Path(__file__).with_name("manifest.json").read_text())
LIMITS = MANIFEST["limits"]


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cache_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())


def check_budget(root, additional=0):
    size = cache_bytes(root)
    if size + additional > LIMITS["cache_bytes"]:
        raise RuntimeError(f"cache would exceed {LIMITS['cache_bytes']} bytes")
    return size


def save(root, name, value):
    (root / "evidence" / name).write_text(json.dumps(value, indent=2) + "\n")


def checked_file(path, expected_size, expected_sha):
    return path.is_file() and path.stat().st_size == expected_size and digest(path) == expected_sha


def download(root, url, path, expected_size, expected_sha, label):
    if path.exists():
        if not checked_file(path, expected_size, expected_sha):
            raise RuntimeError(f"existing {path.name} fails its pinned size/SHA-256; preserved")
        return {"status": "ALREADY_VERIFIED", "bytes": expected_size, "sha256": expected_sha}
    check_budget(root, expected_size)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    if partial.exists():
        raise RuntimeError(f"partial file exists: {partial}; inspect it before a new attempt")
    started = time.monotonic()
    args = ["curl", "--fail", "--silent", "--show-error", "--location", "--proto", "=https",
            "--proto-redir", "=https", "--connect-timeout", "15", "--max-time", "600",
            "--max-filesize", str(expected_size), "--output", str(partial),
            "--write-out", "%{http_code}\n%{size_download}\n%{time_total}\n", url]
    result = subprocess.run(args, capture_output=True, text=True, timeout=620)
    record = {"checked_at_utc": stamp(), "url": url, "curl_exit": result.returncode,
              "metrics": result.stdout.splitlines(), "stderr": result.stderr,
              "wall_seconds": time.monotonic() - started, "expected_bytes": expected_size,
              "expected_sha256": expected_sha}
    if result.returncode != 0:
        record["status"] = "TRANSFER_FAILED"
        save(root, label + "-transfer.json", record)
        raise RuntimeError(f"{label} transfer failed; no automatic retry or alternate source")
    if not checked_file(partial, expected_size, expected_sha):
        record["status"] = "VERIFICATION_FAILED"
        save(root, label + "-transfer.json", record)
        raise RuntimeError(f"{label} verification failed; partial file preserved and not used")
    partial.rename(path)
    record["status"] = "VERIFIED"
    save(root, label + "-transfer.json", record)
    return record


def run_logged(root, args, label, timeout=1200):
    started = time.monotonic()
    env = {**os.environ, "CMAKE_BUILD_PARALLEL_LEVEL": "2", "OMP_NUM_THREADS": "2"}
    with (root / "evidence" / (label + ".stdout.txt")).open("w") as out, \
            (root / "evidence" / (label + ".stderr.txt")).open("w") as err:
        process = subprocess.Popen(args, stdout=out, stderr=err, env=env, start_new_session=True)
        try:
            while process.poll() is None:
                check_budget(root)
                if time.monotonic() - started > timeout:
                    raise RuntimeError(f"{label} exceeded its time budget")
                time.sleep(0.5)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
    record = {"command": list(map(str, args)), "exit": process.returncode,
              "wall_seconds": time.monotonic() - started, "checked_at_utc": stamp()}
    save(root, label + ".json", record)
    if process.returncode:
        raise RuntimeError(f"{label} failed with exit {process.returncode}; see evidence logs")
    return record


def build(root):
    cmake = MANIFEST["cmake"]
    wheel = root / "downloads" / cmake["filename"]
    download(root, cmake["url"], wheel, cmake["bytes"], cmake["sha256"], "cmake-wheel")
    python = root / ".venv/bin/python"
    cmake_bin = root / ".venv/bin/cmake"
    if not python.exists():
        run_logged(root, [sys.executable, "-m", "venv", str(root / ".venv")], "create-venv")
    if not cmake_bin.exists():
        run_logged(root, [str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)], "install-cmake")
    version = subprocess.run([str(cmake_bin), "--version"], capture_output=True, text=True, check=True)
    if f"cmake version {cmake['version']}\n" not in version.stdout:
        raise RuntimeError("CMake version differs from the pinned version")
    source = root / "llama.cpp"
    commit = MANIFEST["source"]["commit"]
    if not (source / ".git").exists():
        source.mkdir(exist_ok=True)
        run_logged(root, ["git", "init", str(source)], "git-init")
        run_logged(root, ["git", "-c", "fetch.fsckObjects=true", "-c", "transfer.fsckObjects=true",
                          "-C", str(source), "fetch", "--depth", "1", MANIFEST["source"]["repo"], commit], "git-fetch")
        run_logged(root, ["git", "-C", str(source), "checkout", "--detach", commit], "git-checkout")
    head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True, check=True).stdout
    if head != commit or dirty:
        raise RuntimeError("existing source checkout is modified or at another commit; preserved")
    run_logged(root, ["git", "-C", str(source), "fsck", "--full"], "source-fsck")
    run_logged(root, [str(cmake_bin), "-S", str(source), "-B", str(root / "build"), *MANIFEST["cmake_flags"]], "reproduce-configure")
    measured = run_logged(root, [str(cmake_bin), "--build", str(root / "build"), "--target", "llama-server", "--parallel", "2"], "reproduce-build")
    binary = root / "build/bin/llama-server"
    result = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError("built server did not pass --version")
    receipt = {"status": "CPU_SERVER_BUILT", "source_commit": head, "binary_sha256": digest(binary),
               "version_stdout": result.stdout, "version_stderr": result.stderr,
               "build": measured, "cache_bytes": check_budget(root), "gpu_backend_enabled": False,
               "inference_qualified": False, "checked_at_utc": stamp()}
    save(root, "build-receipt.json", receipt)
    return receipt


def fetch_model(root):
    for doc in MANIFEST["model_documents"]:
        download(root, doc["url"], root / "evidence" / ("model-" + doc["name"]),
                 doc["bytes"], doc["sha256"], "model-" + doc["name"])
    model = MANIFEST["model"]
    if model["bytes"] > LIMITS["weight_bytes"]:
        raise RuntimeError("model exceeds the weight budget")
    return download(root, model["url"], root / "models" / model["filename"],
                    model["bytes"], model["sha256"], "model")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, stream, code, message, headers, newurl):
        return None


def local_json(base, path, payload=None):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"},
                                     method="GET" if body is None else "POST")
    with opener.open(request, timeout=60) as response:
        raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise RuntimeError("local response exceeded 1 MiB")
        return json.loads(raw)


def qualify(root, port):
    model = MANIFEST["model"]
    weights = root / "models" / model["filename"]
    if not checked_file(weights, model["bytes"], model["sha256"]):
        result = {"status": "BLOCKED_NO_VERIFIED_WEIGHTS", "real_inference_performed": False,
                  "model_sha256_expected": model["sha256"], "checked_at_utc": stamp(),
                  "health": None, "completion": None, "token_counts": None, "peak_rss_kib": None}
        save(root, "qualification.json", result)
        return result
    binary = root / "build/bin/llama-server"
    receipt_path = root / "evidence/build-receipt.json"
    if not receipt_path.exists() or not binary.exists():
        raise RuntimeError("run the explicit build command before qualification")
    built = json.loads(receipt_path.read_text())
    if built["source_commit"] != MANIFEST["source"]["commit"] or digest(binary) != built["binary_sha256"]:
        raise RuntimeError("server binary does not match its recorded pinned build")
    with socket.socket() as test:
        test.bind(("127.0.0.1", port))
    base = f"http://127.0.0.1:{port}"
    alias = MANIFEST["server_alias"]
    command = [str(binary), "--model", str(weights), "--alias", alias, "--host", "127.0.0.1",
               "--port", str(port), "--ctx-size", "2048", "--threads", "2", "--threads-batch", "2",
               "--parallel", "1", "--threads-http", "2", "--n-gpu-layers", "0", "--no-webui",
               "--offline", "--cache-ram", "0", "--n-predict", "128", "--no-context-shift"]
    prompt = "Write only a JSON object with keys case, steps, expected for one regression test: a player standing at tile (2,2) attempts to move into blocked tile (3,2). Keep every value a short string. The player must remain at (2,2)."
    request = {"model": alias, "messages": [{"role": "system", "content": "You write precise tests for a grid-based game. Return only the requested JSON, without markdown."},
                                           {"role": "user", "content": prompt}],
               "temperature": 0, "seed": 42, "max_tokens": 128, "stream": False, "timings_per_token": True}
    result = {"status": "STARTING", "command": command, "model_sha256": model["sha256"],
              "source_commit": MANIFEST["source"]["commit"], "started_at_utc": stamp(),
              "real_inference_performed": False, "request": request}
    begin = time.monotonic()
    with (root / "evidence/server.stdout.txt").open("w") as out, \
            (root / "evidence/server.stderr.txt").open("w") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, env={**os.environ, "OMP_NUM_THREADS": "2"})
        try:
            deadline = time.monotonic() + 60
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"owned server exited before readiness: {process.returncode}")
                try:
                    health = local_json(base, "/health")
                    if health.get("status") == "ok":
                        break
                except (urllib.error.URLError, OSError):
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("owned server did not become healthy within 60 seconds")
                time.sleep(0.1)
            result["health"] = health
            result["startup_wall_seconds"] = time.monotonic() - begin
            result["models"] = local_json(base, "/v1/models")
            inference_start = time.monotonic()
            answer = local_json(base, "/v1/chat/completions", request)
            result["completion_wall_seconds"] = time.monotonic() - inference_start
            result["completion"] = answer
            result["token_counts"] = answer.get("usage")
            content = answer["choices"][0]["message"]["content"]
            result["real_inference_performed"] = bool(content and answer.get("usage", {}).get("completion_tokens", 0) > 0)
            try:
                data = json.loads(content)
                content_passed = isinstance(data, dict) and set(data) == {"case", "steps", "expected"} and all(isinstance(v, str) and v for v in data.values()) and bool(re.search(r"\(\s*2\s*,\s*2\s*\)", data["expected"]))
            except (json.JSONDecodeError, TypeError):
                content_passed = False
            result["bounded_content_check_passed"] = content_passed
            result["status"] = "REAL_INFERENCE_VERIFIED" if result["real_inference_performed"] else "INFERENCE_NOT_ESTABLISHED"
        except Exception as error:
            result["status"] = "QUALIFICATION_FAILED"
            result["error"] = f"{type(error).__name__}: {error}"
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            else:
                process.wait()
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            result.update({"server_stopped": process.poll() is not None, "server_exit": process.returncode,
                           "peak_child_rss_kib": usage.ru_maxrss, "total_wall_seconds": time.monotonic() - begin,
                           "finished_at_utc": stamp(), "cache_bytes": check_budget(root)})
            save(root, "qualification.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "fetch-model", "qualify"])
    parser.add_argument("--cache-dir", type=Path, default=Path(os.environ.get("LOCAL_LLM_CACHE", "/workspace/.cache/local-llm-cpu")))
    parser.add_argument("--port", type=int, default=8093)
    args = parser.parse_args()
    root = args.cache_dir.expanduser().resolve()
    if any((p / ".git").exists() for p in [root, *root.parents]):
        parser.error("cache directory must be outside a Git checkout")
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(exist_ok=True)
    try:
        check_budget(root)
        result = build(root) if args.command == "build" else fetch_model(root) if args.command == "fetch-model" else qualify(root, args.port)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        result = {"status": "FAILED", "command": args.command, "error": str(error), "checked_at_utc": stamp()}
        print(json.dumps(result, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 2 if result["status"].startswith("BLOCKED") else 1 if result["status"] in ("QUALIFICATION_FAILED", "INFERENCE_NOT_ESTABLISHED") else 0


if __name__ == "__main__":
    sys.exit(main())
