#!/usr/bin/env python3
"""Find review candidates in public GitHub game projects and pin them to source commits."""
import argparse
from datetime import datetime, timezone
import hashlib
import heapq
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

LIB = Path(__file__).resolve().parents[1]
RECIPES = json.loads((LIB / "search/scout-recipes.json").read_text())
SAMPLE = LIB / "search/scout-sample.json"
API = "https://api.github.com"
REPO = re.compile(r"[\w.-]+/[\w.-]+", re.ASCII)
SHA = re.compile(r"[a-f0-9]{40}")
IGNORED_DIRS = {".git", ".github", ".idea", "node_modules", "vendor", "vendors", "third_party", "thirdparty", ".venv"}
LICENSE_NAME = re.compile(r"^(?:licen[cs]e[s]?|copying|copyright|notice[s]?|credits?|attribution[s]?)(?:$|[-_. ])", re.I)
COMMON_DIRS = {"src", "source", "sources", "lib", "libs", "game", "assets", "addons", "packages", "core", "dev", "runtime", "modules", "engine", "engines"}
GENERAL_EXTS = set().union(*(r["extensions"] for r in RECIPES.values()))
BYTE_LIMIT = 5 * 1024 * 1024


class ScoutError(Exception):
    pass


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False, encoding="utf-8") as f:
        tmp = Path(f.name)
        try:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    tmp.replace(path)


class Client:
    def __init__(self, args):
        self.args = args
        self.hits = 0
        self.calls = 0

    def get(self, route, immutable=False):
        cache = self.args.cache / (hashlib.sha256(route.encode()).hexdigest() + ".json")
        if cache.exists():
            recent = time.time() - cache.stat().st_mtime <= self.args.cache_hours * 3600
            if self.args.offline or (not self.args.refresh and (immutable or recent)):
                self.hits += 1
                return json.loads(cache.read_text())
        if self.args.offline:
            raise ScoutError("offline cache miss: " + route)
        if self.calls >= self.args.max_requests:
            raise ScoutError("request budget reached")
        self.calls += 1
        headers = {"User-Agent": "game-resource-scout/1", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.args.use_token:
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
            if not token:
                raise ScoutError("--use-token requires GITHUB_TOKEN or GH_TOKEN")
            headers["Authorization"] = "Bearer " + token
        req = Request(API + route, headers=headers)
        try:
            with urlopen(req, timeout=20) as r:
                blob = r.read(BYTE_LIMIT + 1)
        except HTTPError as e:
            detail = f"HTTP {e.code}"
            if e.headers.get("Retry-After"):
                detail += f" (retry after {e.headers['Retry-After']} seconds)"
            if e.headers.get("X-RateLimit-Remaining") == "0":
                detail += " (GitHub rate limit exhausted)"
            raise ScoutError(f"{detail} at {route}") from e
        except (URLError, TimeoutError) as e:
            raise ScoutError(f"network error at {route}: {e.reason if isinstance(e, URLError) else e}") from e
        if len(blob) > BYTE_LIMIT:
            raise ScoutError(f"response exceeded {BYTE_LIMIT} bytes at {route}")
        data = json.loads(blob)
        save(cache, data)
        return data


def words(value):
    # Split separators, PascalCase and acronym boundaries before case folding.
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def matching(value, terms):
    tokens = words(value)
    return sorted(t for t in terms if words(t) and words(t) <= tokens)


def url_for(repo, sha, path):
    return f"https://github.com/{repo}/blob/{sha}/{quote(path, safe='/')}"


def path_terms(path):
    p = PurePosixPath(path)
    stem = p.name.lower()
    if LICENSE_NAME.match(stem) or stem.endswith((".license", ".licence")):
        return True
    return any(x.lower() in {"licenses", "licences", "legal", "reuse", ".reuse"} for x in p.parts[:-1])


def candidate(path, size, spec):
    p = PurePosixPath(path)
    ext = p.suffix.lstrip(".").lower()
    stem = p.stem.lower()
    if not ext or size == 0 or (stem == "__init__" and (size or 0) < 256) or p.name.startswith(".") or stem in {"license", "readme", "changelog", "authors"} or path_terms(path):
        return None
    filename = matching(p.stem, spec["terms"])
    directory = matching(str(p.parent), spec["terms"])
    allowed = ext in spec["extensions"]
    special = ext in spec["formats"]
    # A named source file can be interesting in any language, even one absent from the recipe.
    if not (special or filename or (directory and allowed)):
        return None
    # Each reason explains a fixed component of the score.
    score = (6 if special else 0) + (2 if allowed else 0) + min(len(filename), 3) * 4 + min(len(directory), 3) * 2
    reasons = []
    if filename: reasons.append("filename: " + ", ".join(filename))
    if directory: reasons.append("directory: " + ", ".join(directory))
    if allowed: reasons.append("matching extension: ." + ext)
    if special: reasons.append("specialized format: ." + ext)
    return {"path": path, "extension": ext, "bytes": size, "score": score, "reasons": reasons}


def dir_priority(path, spec):
    p = PurePosixPath(path)
    leaf = p.name.lower()
    related = matching(leaf, spec["terms"] | spec["directories"])
    # Depth costs keep generic top-level asset/source containers competitive with nested matches.
    source_ancestors = min(3, sum(part.lower() in COMMON_DIRS for part in p.parts[:-1]))
    return (len(p.parts) * 2 - (10 if related else 0) - (7 if leaf in COMMON_DIRS else 0)
            - 3 * source_ancestors - (7 if leaf in {"licenses", "licences", "legal"} else 0)
            + (7 if leaf in {"tests", "test", "docs", "dist"} else 0))


def locate_files(api, repo, commit, args, spec):
    queue = [(0, "", commit)]
    visited, candidates, notices = [], [], []
    tree_truncated = False
    excluded = entries = 0
    errors, reasons = [], set()
    while queue and len(visited) < args.tree_calls and entries < args.tree_limit:
        _, prefix, ref = heapq.heappop(queue)
        visited.append(prefix or ".")
        try:
            response = api.get(f"/repos/{repo}/git/trees/{ref}", immutable=True)
        except ScoutError as exc:
            errors.append(str(exc))
            if "budget reached" in str(exc): break
            continue
        if response.get("truncated"):
            tree_truncated = True
            reasons.add("GitHub truncated at least one directory listing")
        children = sorted(response["tree"], key=lambda n: n["path"].casefold())
        for item in children:
            if entries >= args.tree_limit:
                reasons.add("entry limit reached within directory")
                break
            entries += 1
            name = item["path"]
            path = str(PurePosixPath(prefix, name))
            if item["type"] == "tree":
                if name.lower() in IGNORED_DIRS or (name.startswith(".") and name.lower() != ".reuse"):
                    excluded += 1
                else:
                    heapq.heappush(queue, (dir_priority(path, spec), path, item["sha"]))
            elif item["type"] == "blob" and item.get("mode") in {"100644", "100755"}:
                if path_terms(path):
                    notices.append({"path": path, "url": url_for(repo, commit, path)})
                else:
                    hit = candidate(path, item.get("size"), spec)
                    if hit:
                        hit["blob_oid"] = item["sha"]
                        hit["url"] = url_for(repo, commit, path)
                        candidates.append(hit)
    if queue: reasons.add("unvisited directories remain")
    if errors: reasons.add("one or more tree reads failed")
    if excluded: reasons.add("dependency or metadata directories excluded")
    ordered = sorted(candidates, key=lambda r: (-r["score"], len(PurePosixPath(r["path"]).parts), r["path"]))
    return {"directories_attempted": visited, "entries_examined": entries, "excluded_dependency_or_metadata_directories": excluded,
            "github_truncated": tree_truncated, "partial": bool(reasons or excluded), "limits": sorted(reasons),
            "errors": errors, "queued_directories_remaining": len(queue), "candidate_count": len(ordered),
            "terms_paths": sorted(notices, key=lambda r: (len(PurePosixPath(r["path"]).parts), r["path"])),
            "candidates": ordered[:args.files]}


def search(args):
    if not args.recipe and not args.query:
        raise ScoutError("select a --recipe or provide --query")
    api = Client(args)
    requested = {}
    for name in dict.fromkeys(args.recipe):
        for q in RECIPES[name]["queries"]:
            requested.setdefault(q, []).append(name)
    for q in args.query:
        requested.setdefault(q, []).append("custom")
    if not 1 <= len(requested) <= 12:
        raise ScoutError("specify between 1 and 12 distinct queries")
    results, repos, ranked_lists = [], {}, []
    for q, names in requested.items():
        if not q.strip() or len(q) > 240 or any(s in q.lower() for s in ("is:private", "is:internal")):
            raise ScoutError("queries must describe public repositories, up to 240 characters")
        effective = q.strip() + " is:public"
        row = {"query": q, "effective_query": effective, "recipes": names, "urls": [], "total_count": None,
               "github_incomplete": False, "ranked_hits": [], "errors": []}
        search_seen = set()
        for page in range(1, args.pages + 1):
            params = urlencode({"q": effective, "sort": "stars", "order": "desc", "per_page": args.per_page, "page": page})
            route = "/search/repositories?" + params
            row["urls"].append(API + route)
            try:
                page_data = api.get(route)
            except ScoutError as exc:
                row["errors"].append(str(exc))
                break
            row["total_count"] = page_data["total_count"]
            row["github_incomplete"] |= page_data.get("incomplete_results", False)
            for raw in page_data["items"]:
                full = raw["full_name"]
                if raw["private"] or not REPO.fullmatch(full) or full.casefold() in search_seen: continue
                key = full.casefold()
                search_seen.add(key)
                rank = len(row["ranked_hits"]) + 1
                row["ranked_hits"].append(full)
                if key not in repos:
                    repos[key] = {"project": full, "default_branch": raw["default_branch"], "language": raw.get("language"),
                                  "topics": raw.get("topics", []), "stars_at_search": raw["stargazers_count"], "matched_queries": []}
                repos[key]["matched_queries"].append({"query": q, "recipes": names, "rank": rank})
            if len(page_data["items"]) < args.per_page or page * args.per_page >= row["total_count"]:
                break
        row["partial"] = bool(row["errors"] or row["github_incomplete"] or len(search_seen) < (row["total_count"] or 0))
        results.append(row)
        ranked_lists.append([r.casefold() for r in row["ranked_hits"]])
    # Round-robin selection prevents the first recipe monopolizing a small inspection budget.
    selected = []
    for rank in range(max(map(len, ranked_lists), default=0)):
        for ranking in ranked_lists:
            if rank < len(ranking) and ranking[rank] not in selected:
                selected.append(ranking[rank])
    inspections = []
    for key in selected[:args.inspect]:
        repo = dict(repos[key])
        name = repo["project"]
        recipe_names = {n for hit in repo["matched_queries"] for n in hit["recipes"] if n != "custom"}
        if any("custom" in hit["recipes"] for hit in repo["matched_queries"]): recipe_names.update(args.recipe)
        spec = {k: set().union(*(RECIPES[n][k] for n in recipe_names)) for k in ("terms", "extensions", "formats", "directories")}
        if not recipe_names:
            free = [t.strip('"') for hit in repo["matched_queries"] for t in hit["query"].split() if ":" not in t]
            spec["terms"].update(t for t in free if len(t) >= 2)
            spec["extensions"].update(GENERAL_EXTS)
        spec["terms"].update(args.match)
        spec["extensions"].update(e.lower().lstrip(".") for e in args.ext)
        spec["formats"].update(e.lower().lstrip(".") for e in args.ext)
        repo["reasons"] = [f"rank {hit['rank']} for {hit['query']}" for hit in repo["matched_queries"]]
        try:
            ref = api.get(f"/repos/{name}/git/ref/heads/{quote(repo['default_branch'],safe='/')}")
            rev = ref["object"]["sha"]
            if ref["object"]["type"] != "commit" or not SHA.fullmatch(rev):
                raise ScoutError("default branch did not resolve to a commit")
            repo["revision"] = rev
            repo["commit_url"] = f"https://github.com/{name}/commit/{rev}"
            repo["tree"] = locate_files(api, name, rev, args, spec)
        except ScoutError as exc:
            repo["error"] = str(exc)
        inspections.append(repo)
    return {"version": 1, "observed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "selection": "round robin by per-query star rank, deduplicated case-insensitively",
            "scope": "Public search candidates and path-based matches. Review the pinned bytes and applicable asset-specific terms before reuse.",
            "settings": {k: getattr(args, k) for k in ("recipe", "query", "match", "ext", "per_page", "pages", "inspect", "files", "tree_calls", "tree_limit", "max_requests")},
            "counts": {"unique_repositories_returned": len(repos), "repositories_inspected": len(inspections),
                       "network_requests": api.calls, "cache_hits": api.hits},
            "queries": results, "repositories": inspections}


def display(report, project=None):
    if report.get("version") != 1:
        raise ScoutError("unsupported report version")
    counts = report["counts"]
    print(f"{counts['unique_repositories_returned']} unique search results, {counts['repositories_inspected']} selected for file inspection.")
    for q in report["queries"]:
        state = "partial" if q["partial"] else "complete"
        print(f"  {q['query']}: {len(q['ranked_hits'])} of {q['total_count']}, {state}")
        for error in q["errors"]: print(f"    {error}")
    selected = [r for r in report["repositories"] if not project or project.casefold() in r["project"].casefold()]
    if project and not selected:
        raise ScoutError(f"no inspected project matches {project!r} in this report")
    for repo in selected:
        if "tree" not in repo:
            print(f"  {repo['project']}: {repo['error']}")
            continue
        tree = repo["tree"]
        print(f"\n{repo['project']} @ {repo['revision'][:12]} · {repo['language'] or 'language unreported'}")
        print(f"  {tree['entries_examined']} tree entries, {tree['candidate_count']} candidate paths; "
              f"tree coverage {'partial' if tree['partial'] else 'complete'}")
        if tree["terms_paths"]: print("  Terms paths: " + ", ".join(r["path"] for r in tree["terms_paths"][:5]))
        for c in tree["candidates"]: print(f"  {c['score']:>2}  {c['path']} · {'; '.join(c['reasons'])}")
        for error in tree["errors"]: print(f"  {error}")


def bounded(low, high):
    def parse(s):
        value = int(s)
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f"must be in [{low}, {high}]")
        return value
    return parse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("recipes", help="list designer domains and their repository queries")
    replay = sub.add_parser("replay", help="display a saved report locally (the checked-in sample by default)")
    replay.add_argument("report", nargs="?", default=SAMPLE, type=Path)
    replay.add_argument("--project", help="filter displayed project names")
    run = sub.add_parser("run", help="query GitHub and inspect candidate file trees")
    run.add_argument("--recipe", action="append", choices=sorted(RECIPES), default=[])
    run.add_argument("--query", action="append", default=[], help="add a public repository search query")
    run.add_argument("--match", action="append", default=[], help="add a filename/path ranking term")
    run.add_argument("--ext", action="append", default=[], help="rank an additional specialized extension")
    run.add_argument("--per-page", type=bounded(1, 50), default=5)
    run.add_argument("--pages", type=bounded(1, 3), default=1)
    run.add_argument("--inspect", type=bounded(1, 30), default=4)
    run.add_argument("--tree-calls", type=bounded(1, 30), default=7, help="maximum directories to inspect per repository")
    run.add_argument("--tree-limit", type=bounded(1, 50000), default=2500, help="maximum tree entries examined per repository")
    run.add_argument("--files", type=bounded(1, 50), default=6)
    run.add_argument("--max-requests", type=bounded(1, 250), default=44, help="maximum network requests across the whole run")
    run.add_argument("--cache", type=Path, default=Path(os.getenv("XDG_CACHE_HOME", str(Path.home()/".cache"))) / "game-resource-scout")
    run.add_argument("--cache-hours", type=bounded(0, 8760), default=24, help="reuse live search and branch responses for this long")
    mode = run.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="refresh even if cached")
    mode.add_argument("--offline", action="store_true", help="only use existing API cache")
    run.add_argument("--use-token", action="store_true", help="send GITHUB_TOKEN or GH_TOKEN to GitHub for a higher quota")
    run.add_argument("--out", required=True, type=Path, help="destination JSON report")
    args = parser.parse_args()
    if args.command == "recipes":
        for name, recipe in RECIPES.items():
            print(f"{name:18} {recipe['label']}\n                   {'; '.join(recipe['queries'])}")
    elif args.command == "replay":
        display(json.loads(args.report.read_text()), args.project)
    else:
        report = search(args)
        save(args.out, report)
        display(report)
        if any(q["errors"] for q in report["queries"]) or any(r.get("error") or r.get("tree", {}).get("errors") for r in report["repositories"]):
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ScoutError, OSError, ValueError, KeyError) as error:
        sys.exit(f"scout: {error}")
