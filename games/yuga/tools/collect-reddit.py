#!/usr/bin/env python3
"""Bounded public Reddit research. Never evaluates config or mutates an account."""
from __future__ import annotations

import argparse
import ast
import base64
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

SUBREDDIT = "DeadlockTheGame"
REPOSITORY = Path(__file__).resolve().parents[3]
FIELDS = ("client_id", "client_secret", "user_agent", "username", "password")
REQUIRED = FIELDS[:3]
MAX_CONFIG_BYTES = 65_536
MAX_RESPONSE_BYTES = 2_000_000


class SafeError(Exception):
    """Only fixed, non-sensitive messages may cross the command-line boundary."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def invalid_config() -> SafeError:
    return SafeError("invalid_config", "Config must contain only supported literal fields; no expressions or executable statements.")


def literal_config(text: str) -> dict[str, str]:
    """Accept JSON, literal assignments, or literal PRAW constructor keywords."""
    if len(text.encode("utf-8")) > MAX_CONFIG_BYTES:
        raise invalid_config()
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise invalid_config()
            obj[key] = value
        return obj
    try:
        candidate = json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, RecursionError):
        candidate = None
    if candidate is not None:
        if not isinstance(candidate, dict):
            raise invalid_config()
        pairs = list(candidate.items())
    else:
        module = None
        # The second form accepts a bare client_id='...', client_secret='...' list.
        wrapped = "Reddit(\n" + text + "\n)"
        bare = re.match(r"\s*(?:client_id|client_secret|user_agent|username|password|read_only)\s*=", text)
        for source in ((wrapped, text) if bare else (text, wrapped)):
            try:
                module = ast.parse(source, mode="exec")
                break
            except (SyntaxError, ValueError, RecursionError):
                continue
        if module is None or sum(1 for _ in ast.walk(module)) > 200:
            raise invalid_config()
        pairs: list[tuple[str, Any]] = []
        for node in module.body:
            if isinstance(node, ast.Import) and len(node.names) == 1 and node.names[0].name == "praw" and node.names[0].asname is None:
                continue  # Recognize this syntax; never import the package.
            expression = node.value if isinstance(node, (ast.Expr, ast.Assign)) else None
            if isinstance(expression, ast.Call):
                function = expression.func
                allowed = isinstance(function, ast.Name) and function.id == "Reddit" or (
                    isinstance(function, ast.Attribute) and function.attr == "Reddit"
                    and isinstance(function.value, ast.Name) and function.value.id == "praw"
                )
                if not allowed or expression.args:
                    raise invalid_config()
                if isinstance(node, ast.Assign) and (len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name)):
                    raise invalid_config()
                for keyword in expression.keywords:
                    if keyword.arg is None or not isinstance(keyword.value, ast.Constant):
                        raise invalid_config()
                    pairs.append((keyword.arg, keyword.value.value))
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant):
                pairs.append((node.targets[0].id, node.value.value))
            else:
                raise invalid_config()
    result: dict[str, str] = {}
    for name, value in pairs:
        if name == "read_only" and value is True:
            continue
        if name not in FIELDS or name in result or not isinstance(value, str) or len(value) > 4096:
            raise invalid_config()
        result[name] = value
    return result


def outside_repository(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPOSITORY)
        return False
    except ValueError:
        return True


def read_config(path: Path) -> dict[str, str]:
    if not outside_repository(path):
        raise SafeError("config_location", "Keep the credential config outside the repository.")
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_CONFIG_BYTES + 1)
        if len(raw) > MAX_CONFIG_BYTES:
            raise invalid_config()
        return literal_config(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError):
        raise SafeError("config_unreadable", "The external config could not be read as UTF-8.") from None


class Redactor:
    def __init__(self, values: list[str]):
        self.values = set(value for value in values if value)

    def add(self, value: str) -> None:
        if value:
            self.values.add(value)

    def clean(self, value: Any, limit: int) -> str:
        text = value if isinstance(value, str) else ""
        for secret in sorted(self.values, key=len, reverse=True):
            text = text.replace(secret, "[secret omitted]")
        text = re.sub(r"https?://(?:www\.)?reddit\.com/(?:u|user)/[^\s)\]<>]+", "[user profile omitted]", text, flags=re.I)
        text = re.sub(r"(?<![\w])/?u/[A-Za-z0-9_-]+", "[user mention omitted]", text, flags=re.I)
        text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email omitted]", text)
        text = "".join(character for character in text if character in "\n\t" or ord(character) >= 32)
        return text[:limit]


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        # Never send an authorization header to a redirect target.
        return None


class RedditReader:
    def __init__(self, config: dict[str, str], requests: int, runtime: int, redactor: Redactor):
        if not all(config.get(name, "").strip() for name in REQUIRED):
            raise SafeError("missing_config", "client_id, client_secret and user_agent are required.")
        if any(character in config["user_agent"] for character in "\r\n"):
            raise invalid_config()
        self.config = config
        self.redactor = redactor
        self.request_cap = requests
        self.requests = 0
        self.deadline = time.monotonic() + runtime
        self.next_request = 0.0
        self.token = ""
        self.opener = build_opener(NoRedirects())  # Uses configured proxy and system CA trust.

    def _wait(self, seconds: float) -> None:
        if seconds <= 0:
            return
        if seconds > 30 or time.monotonic() + seconds >= self.deadline:
            raise SafeError("rate_limit_wait", "Rate-limit or runtime budget reached; resume with a later bounded run.")
        time.sleep(seconds)

    def _rate_headers(self, headers) -> None:
        try:
            remaining = float(headers.get("x-ratelimit-remaining", "2"))
            reset = float(headers.get("x-ratelimit-reset", "0"))
            if math.isfinite(remaining) and math.isfinite(reset) and remaining < 1:
                self.next_request = max(self.next_request, time.monotonic() + max(0, reset) + 1)
        except (TypeError, ValueError, OverflowError):
            pass

    def _request(self, path: str, query: dict[str, Any] | None = None, oauth: bool = False) -> Any:
        if oauth:
            if path != "/api/v1/access_token":
                raise SafeError("endpoint_rejected", "Only the configured read-only API endpoints are allowed.")
            url = "https://www.reddit.com" + path
            credentials = (self.config["client_id"] + ":" + self.config["client_secret"]).encode("utf-8")
            authorization = "Basic " + base64.b64encode(credentials).decode("ascii")
            body = urlencode({"grant_type": "client_credentials"}).encode("ascii")
            method = "POST"
        else:
            if not re.fullmatch(rf"/r/{SUBREDDIT}/(?:new|top|search|comments/[a-z0-9]+)", path) or not self.token:
                raise SafeError("endpoint_rejected", "Only the configured public subreddit endpoints are allowed.")
            url = "https://oauth.reddit.com" + path + "?" + urlencode(query or {})
            authorization = "Bearer " + self.token
            body = None
            method = "GET"
        for attempt in range(2):
            self._wait(self.next_request - time.monotonic())
            if self.requests >= self.request_cap or time.monotonic() >= self.deadline:
                raise SafeError("request_budget", "Request or runtime budget reached.")
            self.requests += 1
            self.next_request = time.monotonic() + 2.1  # Conservative minimum spacing; server headers take priority.
            request = Request(url, data=body, method=method, headers={"Authorization": authorization, "User-Agent": self.config["user_agent"], "Accept": "application/json"})
            if oauth:
                request.add_header("Content-Type", "application/x-www-form-urlencoded")
            try:
                timeout = max(.1, min(20.0, self.deadline - time.monotonic()))
                with self.opener.open(request, timeout=timeout) as response:
                    self._rate_headers(response.headers)
                    raw = response.read((65_536 if oauth else MAX_RESPONSE_BYTES) + 1)
                if len(raw) > (65_536 if oauth else MAX_RESPONSE_BYTES):
                    raise SafeError("response_size", "API response exceeded the bounded size limit.")
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, UnicodeError, RecursionError):
                    raise SafeError("response_format", "API returned an unsupported response format.") from None
            except HTTPError as error:
                self._rate_headers(error.headers)
                status = int(error.code)
                if status in (429, 502, 503) and attempt == 0:
                    try:
                        retry = float(error.headers.get("Retry-After", "5"))
                    except (TypeError, ValueError):
                        retry = 5.0
                    self._wait(max(2.1, retry) if math.isfinite(retry) else 31)
                    continue
                raise SafeError(f"http_{status}", f"Official API request rejected (HTTP {status}); check network permission, app configuration and API access.") from None
            except (URLError, TimeoutError, OSError, ValueError):
                raise SafeError("network_error", "Network request failed; check the allowlist, proxy and TLS configuration.") from None
        raise SafeError("retry_limit", "Bounded retry limit reached.")

    def authenticate(self) -> None:
        data = self._request("/api/v1/access_token", oauth=True)
        token = data.get("access_token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not token or len(token) > 8192 or "\r" in token or "\n" in token:
            raise SafeError("oauth_rejected", "OAuth did not return a usable application token.")
        self.token = token
        self.redactor.add(token)

    def get(self, path: str, query: dict[str, Any]) -> Any:
        return self._request(path, query)


def integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def utc_date(value: Any) -> str | None:
    try:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def permalink(value: Any) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(r"/r/DeadlockTheGame/comments/[A-Za-z0-9]+/[^\s?#]*", value, re.I):
        return None
    return "https://www.reddit.com" + value


def listing_children(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
        return []
    children = value["data"].get("children")
    return [child for child in children if isinstance(child, dict)] if isinstance(children, list) else []


def collect(reader: RedditReader, args, redactor: Redactor) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    per_stratum = max(1, args.max_posts // 4)
    plans = [
        ("new", "/new", {"sort": "new"}),
        ("top_month", "/top", {"t": "month"}),
        ("feedback_relevance", "/search", {"q": 'frustrating OR confusing OR feedback OR "new player"', "restrict_sr": "on", "sort": "relevance", "t": "year"}),
        ("counterexamples_relevance", "/search", {"q": 'enjoy OR improved OR helpful OR "love this"', "restrict_sr": "on", "sort": "relevance", "t": "year"}),
    ]
    result: dict[str, Any] = {
        "schema": 1, "subreddit": SUBREDDIT, "retrieved_at": now,
        "collection_status": "complete", "content_is_untrusted_data": True,
        "scope": "Bounded public sample; not an exhaustive corpus, representative survey or estimate of community sentiment.",
        "privacy": "Author metadata, standalone Reddit IDs, account mentions and emails omitted; source permalinks retained.",
        "limits": {"requests": args.max_requests, "posts": args.max_posts, "comments": args.max_comments, "comment_posts": args.comment_posts, "comments_per_post": args.comments_per_post, "runtime_seconds": args.max_runtime},
        "strata": [], "posts": [], "comments": [],
        "limitations": ["Search keywords select viewpoints; they do not classify sentiment.", "Top and relevance ranking are platform-selected and time-dependent.", "Comment depth is at most two; more-comment expansion is never requested.", "Scores can be fuzzed, hidden or change after collection.", "Text is bounded and sanitized; consult the permalink before quoting context.", "Absence from this sample is not evidence of absence from the community."],
    }
    ordered: dict[str, dict[str, Any]] = {}
    internal_ids: dict[str, str] = {}
    buckets: list[list[str]] = []
    try:
        reader.authenticate()
        for label, suffix, query in plans:
            params = {"limit": per_stratum, "raw_json": 1, **query}
            data = reader.get(f"/r/{SUBREDDIT}{suffix}", params)
            keys: list[str] = []
            for child in listing_children(data)[:per_stratum]:
                post = child.get("data")
                if child.get("kind") != "t3" or not isinstance(post, dict) or str(post.get("subreddit", "")).casefold() != SUBREDDIT.casefold():
                    continue
                link = permalink(post.get("permalink"))
                internal = post.get("id")
                if not link or not isinstance(internal, str) or not re.fullmatch(r"[a-z0-9]+", internal):
                    continue
                keys.append(link)
                if link in ordered:
                    ordered[link]["sample_strata"].append(label)
                    continue
                body = redactor.clean(post.get("selftext"), 3500)
                ordered[link] = {"permalink": link, "created_at": utc_date(post.get("created_utc")), "score": integer(post.get("score")), "num_comments": integer(post.get("num_comments")), "title": redactor.clean(post.get("title"), 400), "text": body, "excerpt": body[:240], "text_truncated": len(str(post.get("selftext", ""))) > 3500, "sample_strata": [label]}
                internal_ids[link] = internal
            buckets.append(keys)
            result["strata"].append({"name": label, "endpoint": suffix, "query": query, "requested_posts": per_stratum, "usable_posts": len(keys)})
        # Round-robin source strata before choosing which threads receive comment requests.
        selected: list[str] = []
        for offset in range(per_stratum):
            for bucket in buckets:
                if offset < len(bucket) and bucket[offset] not in selected:
                    selected.append(bucket[offset])
        result["posts"] = [ordered[link] for link in selected[:args.max_posts]]
        seen_comments: set[str] = set()
        for index, link in enumerate(selected[:args.comment_posts]):
            if len(result["comments"]) >= args.max_comments:
                break
            count = min(args.comments_per_post, args.max_comments - len(result["comments"]))
            sort = "top" if index % 2 == 0 else "new"
            response = reader.get(f"/r/{SUBREDDIT}/comments/{internal_ids[link]}", {"limit": count, "depth": 2, "sort": sort, "raw_json": 1})
            if not isinstance(response, list) or len(response) < 2:
                continue
            queue = [(child, 0) for child in listing_children(response[1])]
            taken = 0
            while queue and taken < count:
                child, depth = queue.pop(0)
                comment = child.get("data")
                if child.get("kind") != "t1" or not isinstance(comment, dict):
                    continue
                source = permalink(comment.get("permalink"))
                body = comment.get("body")
                if source and source not in seen_comments and isinstance(body, str) and body not in ("[deleted]", "[removed]"):
                    text = redactor.clean(body, 1500)
                    result["comments"].append({"permalink": source, "post_permalink": link, "created_at": utc_date(comment.get("created_utc")), "score": integer(comment.get("score")), "text": text, "excerpt": text[:240], "text_truncated": len(body) > 1500, "sample_sort": sort, "depth": depth})
                    seen_comments.add(source)
                    taken += 1
                if depth < 1:
                    queue.extend((reply, depth + 1) for reply in listing_children(comment.get("replies")))
    except SafeError as error:
        result["collection_status"] = "partial"
        result["failure"] = {"code": error.code, "message": str(error)}
        if not result["posts"]:
            result["posts"] = list(ordered.values())[:args.max_posts]
    result["requests_performed"] = reader.requests
    return result


def save_result(directory: Path, result: dict[str, Any]) -> Path:
    if not outside_repository(directory):
        raise SafeError("output_location", "Public research output must remain outside the repository.")
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, filename = tempfile.mkstemp(prefix="reddit-deadlock-", suffix=".json", dir=directory)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return Path(filename)
    except OSError:
        raise SafeError("output_failed", "The external research output could not be written.") from None


def self_test() -> dict[str, bool]:
    dummy = {"client_id": "dummy-client-DO-NOT-USE", "client_secret": "dummy-secret-DO-NOT-USE", "user_agent": "dummy-research-agent/0.0", "username": "dummy-account", "password": "dummy-password-DO-NOT-USE"}
    parsed_json = literal_config(json.dumps(dummy)) == dummy
    kwargs = ",\n".join(f"{name}={value!r}" for name, value in dummy.items())
    parsed_praw = literal_config("import praw\nreddit = praw.Reddit(\n" + kwargs + "\n)") == dummy
    parsed_bare = literal_config(kwargs) == dummy
    rejected = True
    for unsafe in ["client_id = __import__('os').environ['SECRET']", "reddit = praw.Reddit(client_id=f'{1+1}')", "reddit = praw.Reddit(**{'client_id':'dummy'})", "print('must not execute')", "client_id='one'\nclient_id='two'"]:
        try:
            literal_config(unsafe)
            rejected = False
        except SafeError:
            pass
    redactor = Redactor(list(dummy.values()))
    redactor.add("dummy-token-DO-NOT-USE")
    cleaned = redactor.clean(" ".join(dummy.values()) + " dummy-token-DO-NOT-USE u/example_user /u/another_user https://reddit.com/user/example_user foo@example.test", 5000)
    redacted = all(value not in cleaned for value in [*dummy.values(), "dummy-token-DO-NOT-USE", "example_user", "another_user", "foo@example.test"])
    links_safe = permalink("/r/DeadlockTheGame/comments/abc123/topic/") is not None and permalink("https://evil.invalid/") is None and permalink("/r/Other/comments/a/x/") is None
    return {"json_literals": parsed_json, "praw_literals": parsed_praw, "bare_keyword_literals": parsed_bare, "executable_syntax_rejected": rejected, "secrets_and_mentions_redacted": redacted, "source_link_allowlist": links_safe}


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise SafeError("invalid_arguments", "Invalid arguments; use --help. Credential values are accepted only through an external config file.")


def bounded_integer(minimum: int, maximum: int):
    def parse(value: str) -> int:
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("integer required") from None
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError("outside supported limits")
        return number
    return parse


def main() -> int:
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="External JSON or literal PRAW-style config; never pass credential values as arguments.")
    parser.add_argument("--check-config", action="store_true", help="Print field-presence booleans only; no network request.")
    parser.add_argument("--self-test", action="store_true", help="Verify parsing/redaction with in-memory dummy values only; no network.")
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/yuga-reddit-research"))
    parser.add_argument("--max-requests", type=bounded_integer(1, 24), default=18, help="Includes OAuth, errors and retries; hard cap24.")
    parser.add_argument("--max-posts", type=bounded_integer(4, 40), default=24)
    parser.add_argument("--max-comments", type=bounded_integer(0, 150), default=64)
    parser.add_argument("--comment-posts", type=bounded_integer(0, 12), default=8)
    parser.add_argument("--comments-per-post", type=bounded_integer(1, 15), default=8)
    parser.add_argument("--max-runtime", type=bounded_integer(10, 600), default=240)
    try:
        args = parser.parse_args()
        if args.self_test:
            checks = self_test()
            print(json.dumps(checks, sort_keys=True))
            return 0 if all(checks.values()) else 1
        if args.config is None:
            raise SafeError("missing_config", "Use --config with an external file, or --self-test.")
        config = read_config(args.config)
        if args.check_config:
            print(json.dumps({f"{field}_present": bool(config.get(field)) for field in FIELDS}, sort_keys=True))
            return 0 if all(config.get(field) for field in REQUIRED) else 1
        if not outside_repository(args.output_dir):
            raise SafeError("output_location", "Public research output must remain outside the repository.")
        redactor = Redactor(list(config.values()))
        reader = RedditReader(config, args.max_requests, args.max_runtime, redactor)
        result = collect(reader, args, redactor)
        path = save_result(args.output_dir, result)
        print(json.dumps({"status": result["collection_status"], "posts": len(result["posts"]), "comments": len(result["comments"]), "requests": reader.requests, "output": str(path)}))
        return 0 if result["collection_status"] == "complete" else 2
    except SafeError as error:
        print(json.dumps({"error": error.code, "message": str(error)}), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('{"error":"interrupted","message":"Collection stopped."}', file=sys.stderr)
        return 130
    except Exception:
        # Neither HTTP bodies, exception reprs nor tracebacks are safe credential diagnostics.
        print('{"error":"unexpected_error","message":"Collector failed; no raw exception or credential data was printed."}', file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
