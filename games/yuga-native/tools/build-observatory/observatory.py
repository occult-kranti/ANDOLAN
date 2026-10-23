#!/usr/bin/env python3
"""Read-only, local production telemetry and explicitly recorded job progress."""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import http.server
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from urllib.parse import unquote, urlsplit

MAX_BYTES = 2 * 1024 * 1024
MAX_JOBS = 256
MAX_ITEMS = 128
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}\Z")
STATUSES = {"queued", "running", "review", "complete", "blocked", "failed", "stale"}
PRIVATE = {".git", ".ssh", ".aws", ".azure", ".config", ".env", "credentials", "id_rsa", "id_ed25519"}
STATE_LOCK = threading.RLock()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def stamp(value: str) -> dt.datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Invalid timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamps need a timezone")
    return parsed


def text(value, limit=3000):
    if not isinstance(value, str) or len(value) > limit or "\x00" in value:
        raise ValueError("Invalid or oversized text")
    return value


def ident(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("Invalid identifier")
    return value


def relative_path(value):
    text(value, 500)
    if not value or "\\" in value or any(c in value for c in ("?", "#", "%", ":")):
        raise ValueError("Expected safe relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {"", ".", ".."} for x in value.split("/")):
        raise ValueError("Expected safe relative path")
    if any(x.casefold() in PRIVATE or x.casefold().startswith(".env.") for x in p.parts):
        raise ValueError("Protected path")
    return value


def safe_url(value):
    text(value, 1500)
    if value.startswith("https://"):
        u = urlsplit(value)
        if not u.hostname or u.username is not None or u.password is not None or u.fragment:
            raise ValueError("Unsafe HTTPS URL")
        if any(c.isspace() for c in value):
            raise ValueError("Unsafe HTTPS URL")
        return value
    if value in {"viewer/", "viewer/index.html"}:
        return value
    if not value.startswith("media/"):
        raise ValueError("Only media-relative, exact viewer or HTTPS URLs are public")
    return relative_path(value)


def safe_existing(path: Path, *, directory=False):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise ValueError("Symlink components are not allowed")
    if directory and not path.is_dir():
        raise ValueError("Directory is absent")
    return path


def workspace_path(value):
    p = safe_existing(Path(value), directory=True)
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(p), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, timeout=5)
    if r.returncode or Path(r.stdout.strip()) != p:
        raise ValueError("Workspace must be its actual Git root")
    return p


def state_directory(workspace, value=None):
    p = Path(value) if value else workspace / ".local-swarm" / "observatory"
    p = safe_existing(p)
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return safe_existing(p, directory=True)


@contextlib.contextmanager
def locked(directory):
    # The process lock supplements the interprocess file lock (flock or Windows byte lock).
    with STATE_LOCK:
        p = safe_existing(directory / "state.lock")
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(p, flags, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("State lock must be a regular file")
            if os.name == "nt":
                import msvcrt
                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"\0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            if os.name == "nt":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


def read_json(path):
    p = safe_existing(path)
    with p.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("JSON exceeds 2 MiB limit")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("JSON record must be an object")
    return value


def atomic_json(path, value):
    p = safe_existing(path)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("State exceeds 2 MiB limit")
    safe_existing(p.parent, directory=True)
    fd, temporary = tempfile.mkstemp(prefix=".observatory-", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # Refuse a destination changed into a symlink before atomic replacement.
        safe_existing(p)
        os.replace(temporary, p)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)


def new_state(run_id, title):
    return {"schema_version": 1, "run": {"id": ident(run_id), "title": text(title, 200), "updated_at": now()},
            "jobs": [], "milestones": [], "assets": [], "sources": []}


def process_identity(pid):
    if isinstance(pid, bool) or not isinstance(pid, int) or pid < 1:
        raise ValueError("PID must be a positive integer")
    # Linux PID start ticks + boot ID distinguish an exited/reused PID. Never read argv/env.
    try:
        folder = Path("/proc") / str(pid)
        if folder.stat().st_uid != os.geteuid():
            return None
        raw = (folder / "stat").read_text()
        fields = raw[raw.rfind(")") + 2:].split()
        if fields[0] == "Z":
            return None
        return {"pid": pid, "start_ticks": fields[19],
                "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}
    except (OSError, IndexError, AttributeError):
        return None


def validate_job(record, previous=None):
    allowed = {"kind", "id", "title", "owner", "stage", "status", "device", "model", "started_at", "updated_at",
               "finished_at", "summary", "outputs", "next_step", "pid", "heartbeat_ttl_seconds"}
    if set(record) - allowed:
        raise ValueError("Unknown job field")
    job = copy.deepcopy(previous) if previous else {}
    for key, value in record.items():
        if key not in {"kind", "pid", "heartbeat_ttl_seconds"}:
            job[key] = value
    ident(job.get("id"))
    for key in ("title", "owner", "stage", "device", "summary", "next_step"):
        job[key] = text(job.get(key, ""), 3000 if key in {"summary", "next_step"} else 200)
    model = job.get("model")
    if model is not None:
        job["model"] = text(model, 200)
    else:
        job["model"] = None
    if job.get("status") not in STATUSES:
        raise ValueError("Unknown job status")
    job["updated_at"] = record.get("updated_at", now())
    for key in ("started_at", "updated_at", "finished_at"):
        if job.get(key) is not None:
            stamp(job[key])
        else:
            job[key] = None
    outputs = job.get("outputs", [])
    if not isinstance(outputs, list) or len(outputs) > 24:
        raise ValueError("Too many outputs")
    cleaned = []
    for item in outputs:
        if not isinstance(item, dict) or set(item) - {"label", "path", "kind", "url"}:
            raise ValueError("Invalid output")
        output = {"label": text(item.get("label", "Output"), 200), "kind": text(item.get("kind", "file"), 80)}
        if item.get("path"):
            output["path"] = relative_path(item["path"])
        if item.get("url"):
            output["url"] = safe_url(item["url"])
        if "path" not in output and "url" not in output:
            raise ValueError("Output needs an evidence path or URL")
        cleaned.append(output)
    job["outputs"] = cleaned
    job.pop("_tracking", None)
    if job["status"] == "running":
        if "pid" in record and "heartbeat_ttl_seconds" in record:
            raise ValueError("Choose process or heartbeat tracking")
        if "pid" in record:
            identity = process_identity(record["pid"])
            if identity is None:
                raise ValueError("PID is absent, ended, unsupported or not owned by this OS user")
            job["_tracking"] = {"kind": "process", "identity": identity}
        elif "heartbeat_ttl_seconds" in record:
            ttl = record["heartbeat_ttl_seconds"]
            if isinstance(ttl, bool) or not isinstance(ttl, int) or not 5 <= ttl <= 300:
                raise ValueError("Heartbeat TTL must be 5..300 seconds")
            job["_tracking"] = {"kind": "heartbeat", "received_at": now(), "ttl_seconds": ttl}
        elif previous and previous.get("_tracking"):
            job["_tracking"] = copy.deepcopy(previous["_tracking"])
        else:
            raise ValueError("Running jobs require owned PID or bounded heartbeat")
        job["started_at"] = job.get("started_at") or now()
        job["finished_at"] = None
    elif job["status"] in {"complete", "failed"}:
        job["finished_at"] = job.get("finished_at") or now()
        if job["status"] == "complete" and (not job["summary"].strip() or not cleaned):
            raise ValueError("Completion needs a summary and at least one evidence output")
    return job


def configure_value(record):
    if set(record) - {"milestones", "assets", "sources"}:
        raise ValueError("Unknown context field")
    result = {}
    for key, rows in record.items():
        if not isinstance(rows, list) or len(rows) > MAX_ITEMS:
            raise ValueError("Context list exceeds limit")
        normalized = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Context entries must be objects")
            fields = ({"id", "title", "status", "evidence"} if key == "milestones" else
                      {"id", "title", "status", "image_url", "model_url", "summary"} if key == "assets" else
                      {"name", "url", "license", "status"})
            if set(row) - fields:
                raise ValueError("Unknown context item field")
            item = {}
            for field, value in row.items():
                if field == "id":
                    item[field] = ident(value)
                elif field.endswith("url") or field == "url":
                    item[field] = safe_url(value)
                else:
                    item[field] = text(value, 3000)
            if key == "sources":
                if not item.get("name") or not item.get("url"):
                    raise ValueError("Source needs name and URL")
            elif not item.get("id") or not item.get("title") or not item.get("status"):
                raise ValueError("Context item needs id, title and status")
            normalized.append(item)
        result[key] = normalized
    return result


def update_state(directory, record=None, *, context=False, initialize=None):
    with locked(directory):
        path = directory / "state.json"
        if initialize:
            if path.exists():
                raise ValueError("Run already exists; use a fresh --state-dir for another run")
            state = new_state(*initialize)
        else:
            state = read_json(path)
            validate_state(state)
            if context:
                state.update(configure_value(record))
            else:
                if record.get("kind", "job") != "job":
                    raise ValueError("Only job records accepted")
                job_id = ident(record.get("id"))
                index = next((i for i, x in enumerate(state["jobs"]) if x["id"] == job_id), None)
                job = validate_job(record, state["jobs"][index] if index is not None else None)
                if index is None:
                    if len(state["jobs"]) >= MAX_JOBS:
                        raise ValueError("Too many jobs")
                    state["jobs"].append(job)
                else:
                    state["jobs"][index] = job
            state["run"]["updated_at"] = now()
        atomic_json(path, state)
        return state


def validate_state(state):
    if set(state) != {"schema_version", "run", "jobs", "milestones", "assets", "sources"} or state["schema_version"] != 1:
        raise ValueError("Invalid state schema")
    run = state["run"]
    if not isinstance(run, dict) or set(run) != {"id", "title", "updated_at"}:
        raise ValueError("Invalid run")
    ident(run["id"])
    text(run["title"], 200)
    stamp(run["updated_at"])
    if not isinstance(state["jobs"], list) or len(state["jobs"]) > MAX_JOBS:
        raise ValueError("Invalid jobs")
    seen = set()
    for job in state["jobs"]:
        if not isinstance(job, dict):
            raise ValueError("Invalid job")
        clean = {k: v for k, v in job.items() if k != "_tracking"}
        track = job.get("_tracking")
        if clean.get("status") == "running":
            if not isinstance(track, dict) or track.get("kind") not in {"process", "heartbeat"}:
                raise ValueError("Invalid running tracking")
            if track["kind"] == "heartbeat":
                if set(track) != {"kind", "received_at", "ttl_seconds"}:
                    raise ValueError("Invalid heartbeat tracking")
                stamp(track["received_at"])
                ttl = track["ttl_seconds"]
                if isinstance(ttl, bool) or not isinstance(ttl, int) or not 5 <= ttl <= 300:
                    raise ValueError("Invalid heartbeat TTL")
            else:
                identity = track.get("identity")
                if set(track) != {"kind", "identity"} or not isinstance(identity, dict) or set(identity) != {"pid", "start_ticks", "boot_id"}:
                    raise ValueError("Invalid process tracking")
                if isinstance(identity["pid"], bool) or not isinstance(identity["pid"], int) or identity["pid"] < 1:
                    raise ValueError("Invalid process identity")
                text(identity["start_ticks"], 80)
                text(identity["boot_id"], 80)
            # Validate public fields without refreshing the persisted heartbeat or process identity.
            clean["status"] = "stale"
        validate_job(clean)
        if job["id"] in seen:
            raise ValueError("Duplicate job ID")
        seen.add(job["id"])
    configure_value({k: state[k] for k in ("milestones", "assets", "sources")})


def public_job(job, sampled_at):
    result = {k: copy.deepcopy(v) for k, v in job.items() if not k.startswith("_")}
    tracking = job.get("_tracking", {})
    result["verification"] = {"kind": tracking.get("kind", "explicit_record")}
    if job["status"] == "running":
        live = False
        if tracking.get("kind") == "process":
            expected = tracking.get("identity", {})
            live = process_identity(expected.get("pid")) == expected if expected.get("pid") else False
        elif tracking.get("kind") == "heartbeat":
            try:
                age = (stamp(sampled_at) - stamp(tracking["received_at"])).total_seconds()
                live = 0 <= age <= tracking["ttl_seconds"] <= 300
                result["verification"]["heartbeat_age_seconds"] = max(0, round(age))
            except (KeyError, TypeError, ValueError):
                live = False
        if not live:
            result["status"] = "stale"
            result["verification"]["reason"] = "Liveness expired or process identity no longer matches; inspect before recording a finish."
    return result


def command(args, timeout=2):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 and len(r.stdout) <= 65536 else None
    except (OSError, subprocess.SubprocessError):
        return None


def source_info(workspace):
    prefix = ["git", "--no-optional-locks", "-C", str(workspace)]
    status = command(prefix + ["status", "--porcelain", "--untracked-files=normal"])
    return {"branch": command(prefix + ["symbolic-ref", "--short", "HEAD"]),
            "commit": command(prefix + ["rev-parse", "HEAD"]),
            "dirty": bool(status) if status is not None else None}


def host_info():
    info = {"logical_cpus": os.cpu_count(), "quota_cpus": None,
            "memory_total_bytes": None, "memory_available_bytes": None,
            "gpu": {"available": False, "devices": [], "reason": "No NVIDIA telemetry executable; other GPU backends are unmeasured."}}
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            info["quota_cpus"] = int(quota) / int(period)
    except (OSError, ValueError, ZeroDivisionError):
        pass
    try:
        mem = {x.split(":")[0]: int(x.split()[1]) * 1024 for x in Path("/proc/meminfo").read_text().splitlines() if ":" in x and len(x.split()) > 1}
        info["memory_total_bytes"] = mem.get("MemTotal")
        info["memory_available_bytes"] = mem.get("MemAvailable")
        cap = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        if cap != "max":
            used = int(Path("/sys/fs/cgroup/memory.current").read_text())
            info["memory_total_bytes"] = min(info["memory_total_bytes"] or int(cap), int(cap))
            info["memory_available_bytes"] = min(info["memory_available_bytes"] or int(cap), max(0, int(cap) - used))
    except (OSError, ValueError):
        pass
    executable = shutil.which("nvidia-smi")
    if executable:
        raw = command([executable, "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], 2)
        if raw is None:
            info["gpu"]["reason"] = "NVIDIA telemetry request failed or timed out."
        else:
            try:
                devices = []
                for line in raw.splitlines()[:16]:
                    name, total, used, utilization = (x.strip() for x in line.split(","))
                    numbers = [float(total), float(used), float(utilization)]
                    if not all(math.isfinite(x) and x >= 0 for x in numbers) or numbers[2] > 100:
                        raise ValueError("Invalid GPU values")
                    devices.append({"name": text(name, 200), "memory_total_bytes": int(numbers[0] * 1048576),
                                    "memory_used_bytes": int(numbers[1] * 1048576), "utilization_percent": numbers[2]})
                info["gpu"] = {"available": bool(devices), "devices": devices,
                               "reason": "Measured NVIDIA telemetry." if devices else "NVIDIA reported no devices."}
            except ValueError:
                info["gpu"]["reason"] = "NVIDIA telemetry format was unsupported."
    return info


class Observatory:
    def __init__(self, workspace, directory):
        self.workspace = workspace
        self.directory = directory
        self.web = Path(__file__).parent / "web"
        self._cache = None
        self._cache_time = 0.0
        self._lock = threading.Lock()

    def snapshot(self, mode="live"):
        state = read_json(self.directory / "state.json")
        validate_state(state)
        sampled = now()
        with self._lock:
            if self._cache is None or time.monotonic() - self._cache_time > 2:
                self._cache = {"source": source_info(self.workspace), "host": host_info()}
                self._cache_time = time.monotonic()
            result = copy.deepcopy(self._cache)
        result.update({"schema_version": 1, "mode": mode, "collected_at": sampled, "run": state["run"],
                       "jobs": [public_job(x, sampled) for x in state["jobs"]],
                       "milestones": state["milestones"], "assets": state["assets"], "sources": state["sources"]})
        return result


def static_path(web, url):
    if url.startswith("//"):
        raise ValueError("Invalid static path")
    decoded = unquote(urlsplit(url).path)
    if len(decoded) > 1000 or any(c in decoded for c in ("\\", "\x00", "%")):
        raise ValueError("Invalid static path")
    value = "viewer/index.html" if decoded == "/viewer/" else decoded.lstrip("/") or "index.html"
    if decoded.startswith("//"):
        raise ValueError("Invalid static path")
    relative_path(value)
    p = safe_existing(web / value)
    if not p.is_relative_to(safe_existing(web, directory=True)) or not p.is_file():
        raise FileNotFoundError("Static file absent")
    if p.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("Static file exceeds limit")
    return p


def make_server(observatory, port):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "YUGAObservatory/1"

        def log_message(self, *_):
            pass  # Never copy arbitrary request paths or headers to logs.

        def send_body(self, status, payload, kind="application/json; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' https:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            host = self.headers.get("Host", "")
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if host not in allowed or len(self.path) > 2048:
                self.send_body(400, b'{"error":"Invalid local request"}')
                return
            try:
                path = urlsplit(self.path).path
                if path == "/api/health":
                    self.send_body(200, b'{"ok":true,"read_only":true}')
                elif path == "/api/status":
                    raw = json.dumps(observatory.snapshot(), allow_nan=False).encode()
                    self.send_body(200, raw)
                elif path.startswith("/api/"):
                    self.send_body(404, b'{"error":"Unknown API route"}')
                else:
                    p = static_path(observatory.web, self.path)
                    kinds = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                             ".json": "application/json; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                             ".webp": "image/webp", ".svg": "image/svg+xml", ".glb": "model/gltf-binary", ".woff2": "font/woff2", ".ttf": "font/ttf", ".txt": "text/plain; charset=utf-8"}
                    if p.suffix not in kinds:
                        raise ValueError("Static type not allowed")
                    self.send_body(200, p.read_bytes(), kinds[p.suffix])
            except FileNotFoundError:
                self.send_body(404, b'{"error":"Not found or run not initialized"}')
            except (ValueError, KeyError, TypeError, UnicodeError):
                self.send_body(422, b'{"error":"Invalid state or path; inspect local source"}')
            except (OSError, subprocess.SubprocessError):
                self.send_body(503, b'{"error":"Telemetry temporarily unavailable"}')

        def do_POST(self):
            self.send_body(405, b'{"error":"Read-only service"}')

        do_PUT = do_POST
        do_DELETE = do_POST
        do_PATCH = do_POST

    class Server(http.server.ThreadingHTTPServer):
        daemon_threads = True
        request_queue_size = 8
        slots = threading.BoundedSemaphore(8)

        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(5)
            return connection, address

        def process_request(self, request, client_address):
            if not self.slots.acquire(blocking=False):
                self.shutdown_request(request)
                return
            try:
                super().process_request(request, client_address)
            except BaseException:
                self.slots.release()
                raise

        def process_request_thread(self, request, client_address):
            try:
                super().process_request_thread(request, client_address)
            finally:
                self.slots.release()

    return Server(("127.0.0.1", port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "emit", "configure", "serve", "export"):
        p = commands.add_parser(name)
        p.add_argument("--workspace", type=Path, required=True)
        p.add_argument("--state-dir", type=Path)
        if name == "init":
            p.add_argument("--run-id", required=True)
            p.add_argument("--title", required=True)
        if name in {"emit", "configure"}:
            p.add_argument("--record", type=Path, required=True)
        if name == "serve":
            p.add_argument("--port", type=int, default=8765)
        if name == "export":
            p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        workspace = workspace_path(args.workspace)
        directory = state_directory(workspace, args.state_dir)
        if args.command == "init":
            update_state(directory, initialize=(args.run_id, args.title))
        elif args.command in {"emit", "configure"}:
            update_state(directory, read_json(args.record), context=args.command == "configure")
        elif args.command == "export":
            output = args.output if args.output.is_absolute() else workspace / args.output
            atomic_json(output, Observatory(workspace, directory).snapshot("snapshot"))
        else:
            if not 1 <= args.port <= 65535:
                raise ValueError("Invalid port")
            observer = Observatory(workspace, directory)
            observer.snapshot()  # Verify state before declaring service ready.
            server = make_server(observer, args.port)
            print(json.dumps({"status": "ready", "bind": "127.0.0.1", "port": args.port, "read_only": True}), flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
        if args.command != "serve":
            print(json.dumps({"status": "ok", "command": args.command}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "blocked", "error": type(exc).__name__, "message": str(exc)[:200]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
