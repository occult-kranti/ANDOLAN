#!/usr/bin/env python3
"""Validate a six-worker plan or inspect a literal local models endpoint.

This module does not launch agents, generate tokens, or select model weights.
"""

import argparse
import http.client
import json
import math
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


WORKER_IDS = {f"W{i}" for i in range(1, 7)}
ROLES = {"QA", "UI", "hero", "world", "motion", "models"}
LOCAL_ENDPOINTS = {
    "http://127.0.0.1:11434/v1",
    "http://localhost:11434/v1",
}
PROBE_URLS = {endpoint + "/models" for endpoint in LOCAL_ENDPOINTS}
MAX_RESPONSE_BYTES = 1024 * 1024


def _keys(value, expected, label, errors):
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    if set(value) != set(expected):
        errors.append(f"{label} must contain exactly: {', '.join(sorted(expected))}")
    return True


def _literal_path(value):
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    if any(char in value for char in "\\:*?[]{}~"):
        return False
    parts = value.split("/")
    return not any(part in ("", ".", "..") for part in parts)


def _cloud_endpoint(value):
    if not isinstance(value, str) or value != value.strip():
        return False
    if any(char.isspace() or ord(char) < 32 for char in value):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        _ = parsed.port
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and "?" not in value
            and "#" not in value
        )
    except ValueError:
        return False


def validate_plan(plan):
    """Check a lexical ownership plan; no filesystem or runtime is inspected."""
    errors = []
    unresolved = []
    top_keys = {"schema_version", "gpu_parallelism", "routing", "workers"}
    if not _keys(plan, top_keys, "plan", errors):
        return _validation_result(errors, unresolved)
    if type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        errors.append("schema_version must be integer 1")
    if type(plan.get("gpu_parallelism")) is not int or plan["gpu_parallelism"] != 1:
        errors.append("gpu_parallelism must be integer 1")

    routes = {}
    routing = plan.get("routing")
    if _keys(routing, {"default", "fallback", "routes"}, "routing", errors):
        if routing.get("default") != "local":
            errors.append("routing.default must be local")
        if routing.get("fallback") is not None:
            errors.append("routing.fallback must be null; automatic fallback is forbidden")
        route_defs = routing.get("routes")
        if _keys(route_defs, {"local", "cloud"}, "routing.routes", errors):
            routes = route_defs
            for route in ("local", "cloud"):
                config = routes.get(route)
                if not _keys(config, {"endpoint", "model_id"}, f"route {route}", errors):
                    continue
                endpoint = config.get("endpoint")
                if route == "local" and (not isinstance(endpoint, str) or endpoint not in LOCAL_ENDPOINTS):
                    errors.append("local endpoint must be a literal supported loopback /v1 URL")
                if route == "cloud" and endpoint is not None and not _cloud_endpoint(endpoint):
                    errors.append("cloud endpoint must be null or HTTPS without credentials, query, or fragment")
                model = config.get("model_id")
                if model is not None and (
                    not isinstance(model, str)
                    or not model.strip()
                    or model != model.strip()
                    or any(ord(char) < 32 or ord(char) == 127 for char in model)
                ):
                    errors.append(f"route {route} model_id must be null or a nonempty literal string")

    workers = plan.get("workers")
    if not isinstance(workers, list):
        errors.append("workers must be a list")
        workers = []
    if len(workers) != 6:
        errors.append("exactly six workers are required")
    ids, roles, owners, used_routes = [], [], [], set()
    for index, worker in enumerate(workers):
        label = f"workers[{index}]"
        if not _keys(worker, {"id", "role", "route", "paths"}, label, errors):
            continue
        worker_id, role, route = worker.get("id"), worker.get("role"), worker.get("route")
        if not isinstance(worker_id, str) or worker_id not in WORKER_IDS:
            errors.append(f"{label}.id must be one of W1 through W6")
        else:
            ids.append(worker_id)
        if not isinstance(role, str) or role not in ROLES:
            errors.append(f"{label}.role is not a supported specialist role")
        else:
            roles.append(role)
        if not isinstance(route, str) or route not in ("local", "cloud"):
            errors.append(f"{label}.route must explicitly select local or cloud")
        else:
            used_routes.add(route)
        paths = worker.get("paths")
        if not isinstance(paths, list) or not paths:
            errors.append(f"{label}.paths must be a nonempty list")
            continue
        for path in paths:
            if not _literal_path(path):
                errors.append(f"{label} contains an invalid literal relative path: {path!r}")
                continue
            parts = tuple(path.split("/"))
            for prior_parts, prior_id, prior_path in owners:
                prefix_length = min(len(parts), len(prior_parts))
                if parts[:prefix_length] == prior_parts[:prefix_length]:
                    errors.append(f"path ownership overlaps: {prior_id}:{prior_path} and {worker_id}:{path}")
            owners.append((parts, worker_id, path))
    if len(ids) != 6 or set(ids) != WORKER_IDS:
        errors.append("worker IDs must be unique and exactly W1 through W6")
    if len(roles) != 6 or set(roles) != ROLES:
        errors.append("each specialist role must appear exactly once")

    for route in sorted(used_routes):
        config = routes.get(route)
        if not isinstance(config, dict):
            continue
        if config.get("model_id") is None:
            unresolved.append(f"route {route}: model_id is null")
        if config.get("endpoint") is None:
            unresolved.append(f"route {route}: endpoint is null")
    return _validation_result(errors, unresolved)


def _validation_result(errors, unresolved):
    status = "INVALID" if errors else "UNRESOLVED" if unresolved else "CONFIGURED"
    return {
        "status": status,
        "valid": not errors,
        "runnable": not errors and not unresolved,
        "runtime_qualified": False,
        "errors": errors,
        "unresolved": unresolved,
        "note": "runnable describes plan bindings only; no client, model, or hardware was qualified",
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe_models(url, timeout=3.0, max_bytes=MAX_RESPONSE_BYTES):
    """GET only a fixed local /v1/models URL, ignoring environment proxies."""
    if not isinstance(url, str) or url not in PROBE_URLS:
        raise ValueError("URL must be exactly http://127.0.0.1:11434/v1/models or http://localhost:11434/v1/models")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or not 0.1 <= timeout <= 10:
        raise ValueError("timeout must be between 0.1 and 10 seconds")
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_RESPONSE_BYTES:
        raise ValueError("max_bytes must be between 1 and 1048576")
    # Even the accepted localhost spelling uses a literal address on the wire.
    request_url = "http://127.0.0.1:11434/v1/models"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(request_url, headers={"Accept": "application/json"}, method="GET")
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                return _probe_error(url, f"unexpected HTTP status {response.status}")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return _probe_error(url, "response exceeded the byte limit")
    except urllib.error.HTTPError as error:
        error.close()
        return _probe_error(url, f"HTTP {error.code}; redirects are not followed")
    except urllib.error.URLError as error:
        reason = error.reason if isinstance(error.reason, Exception) else error
        return _probe_error(url, f"request failed: {type(reason).__name__}")
    except (OSError, TimeoutError, http.client.HTTPException) as error:
        return _probe_error(url, f"request failed: {type(error).__name__}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _probe_error(url, "response was not UTF-8 JSON")
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip()
        for item in data
    ):
        return _probe_error(url, "response must contain a data list of model objects with nonempty string IDs")
    return {
        "status": "MODELS_LISTED" if data else "NO_MODELS",
        "url": url,
        "request_url": request_url,
        "models": [item["id"] for item in data],
        "model_count": len(data),
        "generation_performed": False,
        "runtime_qualified": False,
    }


def _probe_error(url, message):
    safe_url = url if isinstance(url, str) and url in PROBE_URLS else None
    return {"status": "ERROR", "url": safe_url, "error": message, "generation_performed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a six-specialist plan")
    validate.add_argument("plan", type=Path)
    probe = commands.add_parser("probe", help="GET local /v1/models without generation")
    probe.add_argument("--url", default="http://127.0.0.1:11434/v1/models")
    probe.add_argument("--timeout", type=float, default=3.0)
    probe.add_argument("--max-bytes", type=int, default=MAX_RESPONSE_BYTES)
    args = parser.parse_args(argv)
    if args.command == "validate":
        try:
            result = validate_plan(json.loads(args.plan.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            result = _validation_result([f"could not read plan: {type(error).__name__}"], [])
        code = 1 if not result["valid"] else 2 if result["unresolved"] else 0
    else:
        try:
            result = probe_models(args.url, args.timeout, args.max_bytes)
        except ValueError as error:
            result = _probe_error(args.url, str(error))
        code = 1 if result["status"] == "ERROR" else 0
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
