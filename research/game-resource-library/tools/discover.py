#!/usr/bin/env python3
"""Rebuild the searchable game/engine directory from pinned catalog evidence."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import string
import sys
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

import yaml

LIB = Path(__file__).resolve().parents[1]
ROOT = LIB.parents[1]
SNAPSHOT = LIB / "sources/osgameclones.zip"
MANIFEST = LIB / "sources/discovery-inputs.json"
OUTPUT = LIB / "data/discovery.json.gz"
SUMMARY = LIB / "data/discovery-counts.json"
CATALOG = "opengaming/osgameclones"
PIN = "3a6994d85c9e007325a1040f439d778a7ca49a26"
CHECKOUT = "ef80a7d15f0c7e346b04826958f5c4b4195db972"
EXISTING = "games/yuga-native/docs/rust-rebuild/deep-search/"
FILES = {"engines": "rea/engine-rebuild-index.tsv",
         "curated": "rea/curated-title-index.json", "topics": "catalog/topic-search.json",
         "primary": "rea/primary-source-index.json", "modules": "catalog/module-index.json"}
PARTS = ["LICENSE",
         *(f"games/{c}.yaml" for c in "0" + string.ascii_lowercase),
         *(f"originals/{c}.yaml" for c in ["0scumm", *string.ascii_lowercase])]
LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
LABELS = {"clones": "Open Source Game Clones", "engines": "Engine reimplementations",
          "curated": "Awesome REA Games", "topics": "GitHub topic search",
          "primary": "Primary repository inspection", "modules": "Inspected code modules"}
COLUMNS = ["languages", "platforms", "genres", "originals", "status", "development",
           "content", "listed_licenses", "frameworks", "multiplayer", "asset_notes"]
GITHUB = re.compile(r"^/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/?$")
SOCIAL = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "youtu.be",
          "youtube.com", "www.youtube.com", "reddit.com", "www.reddit.com"}


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def pretty(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()


def packed(blob):
    out = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=out, mode="wb", mtime=0, compresslevel=9) as f:
        f.write(blob)
    return out.getvalue()


def github(repo, pin, path):
    return f"https://github.com/{repo}/blob/{pin}/{path}"


def checked_source(family):
    return github("occult-kranti/ANDOLAN", CHECKOUT, EXISTING + FILES[family])


def ensure_snapshot(manifest, refresh):
    if refresh:
        def fetch(part):
            url = f"https://raw.githubusercontent.com/{CATALOG}/{PIN}/{part}"
            with urlopen(url, timeout=45) as f:
                blob = f.read()
            if digest(blob) != manifest["upstream"]["sha256"][part]:
                raise ValueError(f"Downloaded shard differs from pinned input: {part}")
            return part, blob
        with ThreadPoolExecutor(max_workers=8) as workers:
            rows = list(workers.map(fetch, PARTS))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as archive:
            for part, blob in rows:
                meta = zipfile.ZipInfo(part, (1980, 1, 1, 0, 0, 0))
                meta.create_system = 3
                meta.external_attr = 0o100644 << 16
                archive.writestr(meta, blob, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        SNAPSHOT.write_bytes(out.getvalue())
    with zipfile.ZipFile(SNAPSHOT) as archive:
        if sorted(archive.namelist()) != sorted(PARTS):
            raise ValueError("Missing, extra or repeated upstream shard")
        data = {part: archive.read(part) for part in PARTS}
    for part, blob in data.items():
        if digest(blob) != manifest["upstream"]["sha256"][part]:
            raise ValueError(f"Upstream snapshot checksum mismatch: {part}")
    return data


def entries(blob):
    """Safe load records and retain exact source line indexes from the YAML parser."""
    loader = LOADER(blob)
    try:
        node = loader.get_single_node()
        items = loader.construct_document(node)
        for index, (entry, item_node) in enumerate(zip(items, node.value, strict=True)):
            yield index, item_node.start_mark.line + 1, entry
    finally:
        loader.dispose()


def values(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def url_key(url):
    if not url:
        return None
    # One upstream repo field has an explicit www host and no scheme.
    if url.startswith("www."):
        url = "https://" + url
    parts = urlsplit(url)
    if not parts.hostname or parts.scheme.lower() not in ("http", "https"):
        return None
    host = parts.hostname.lower()
    if host in SOCIAL or parts.username or parts.password:
        return None
    if host in ("codeberg.org", "projects.blender.org"):
        match = GITHUB.fullmatch(parts.path)
        if match and not parts.query and not parts.fragment:
            owner, repo = match.groups()
            return "codeforge:" + host + "/" + owner.lower() + "/" + repo.lower().removesuffix(".git")
    if host in ("github.com", "www.github.com"):
        match = GITHUB.fullmatch(parts.path)
        if match and not parts.query and not parts.fragment:
            owner, repo = match.groups()
            return "github:" + owner.lower() + "/" + repo.lower().removesuffix(".git")
    # Preserve meaningful query/fragment, path case and host/port. An archive.org
    # snapshot and its currently advertised website are distinct references.
    return "url:" + urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                                parts.path.rstrip("/"), parts.query, parts.fragment))


def front_url(url):
    return "https://" + url if url.startswith("www.") else url


class Index:
    def __init__(self):
        self.rows = []

    def add(self, family, locator, name, url, kind, source_url, *, aliases=(), alt=(), **meta):
        key = url_key(url)
        source = {"name": LABELS[family], "url": source_url, "family": family,
                  "record": locator, "title": name}
        source.update({k: v for k, v in meta.items() if v})
        if alt:
            source["links"] = list(dict.fromkeys(alt))
        self.rows.append({"family": family, "key": key or f"source:{family}:{locator}",
                          "url": front_url(url) if key else "", "name": name, "kind": kind,
                          "aliases": [url_key(u) for u in aliases if url_key(u)], "source": source})

    def projects(self):
        # A site explicitly paired with one repository can join a site-only row.
        # Showcases, alternative tools and ambiguous shared home pages are never aliases.
        repo_for_site = defaultdict(set)
        for row in self.rows:
            for alias in row["aliases"]:
                if alias != row["key"] and alias.startswith("url:"):
                    repo_for_site[alias].add(row["key"])
        unique_sites = {site: next(iter(repos)) for site, repos in repo_for_site.items()
                        if len(repos) == 1}
        groups = defaultdict(list)
        for row in self.rows:
            key = unique_sites.get(row["key"], row["key"])
            groups[key].append(row)
        output = []
        for key, rows in sorted(groups.items()):
            first = rows[0]
            canonical = next((r for r in rows if r["key"] == key), first)
            names = list(dict.fromkeys(r["name"] for r in rows))
            sources = [r["source"] for r in rows]
            merged = {col: sorted({v for s in sources for v in values(s.get(col))},
                                  key=lambda s: (s.casefold(), s)) for col in COLUMNS}
            project = {"id": key, "name": names[0], "url": canonical["url"],
                       "kind": first["kind"], "language": ", ".join(merged["languages"]),
                       "sources": sources, "kinds": list(dict.fromkeys(r["kind"] for r in rows))}
            if len(names) > 1:
                project["aliases"] = names[1:]
            project.update({k: v for k, v in merged.items() if v})
            output.append(project)
        return output, [site for site, repos in repo_for_site.items() if len(repos) > 1]


def import_clones(index, data):
    originals = {}
    for path in PARTS:
        if not path.startswith("originals/"):
            continue
        for _, line, row in entries(data[path]):
            name = row["name"]
            if name in originals:
                raise ValueError(f"Ambiguous upstream original reference: {name}")
            originals[name] = (row.get("meta", {}).get("genres", []),
                               github(CATALOG, PIN, path) + f"#L{line}")
    for path in PARTS:
        if not path.startswith("games/"):
            continue
        for number, line, row in entries(data[path]):
            repo, site = row.get("repo"), row.get("url")
            urls = [u for u in [repo, site] if u]
            primary = next((u for u in urls if url_key(u)), "")
            refs = {name: originals[name] for name in row["originals"]}
            genres = sorted({genre for gen, _ in refs.values() for genre in gen})
            index.add("clones", f"{path}[{number}]", row["name"], primary, row["type"],
                      github(CATALOG, PIN, path) + f"#L{line}", alt=urls,
                      aliases=[site] if site and repo and url_key(repo) else [],
                      languages=row["langs"], platforms=row["platforms"], status=row["status"],
                      development=row.get("development"), originals=row["originals"],
                      content=row.get("content"), listed_licenses=row["licenses"], genres=genres,
                      frameworks=row.get("frameworks"), multiplayer=row.get("multiplayer"),
                      original_sources={n: u for n, (_, u) in refs.items()})
    return len(originals)


def import_local(index, local):
    curated = json.loads(local["curated"])
    engine = curated["broader_tools"]
    engine_source = github(engine["repo"], engine["pin"], engine["path"])
    reader = csv.DictReader(io.StringIO(local["engines"].decode()), delimiter="\t")
    for i, row in enumerate(reader, start=2):
        langs = row["listed_language"].strip()
        index.add("engines", f"tsv:L{i}", row["project"], row["url"], "engine reimplementation",
                  checked_source("engines") + f"#L{i}", languages=[langs] if langs else [],
                  catalog_url=engine_source)
    games = curated["games_list"]
    games_source = github(games["repo"], games["pin"], "README.md")
    for i, game in enumerate(games["games"]):
        for j, row in enumerate(game["projects"]):
            links = row["project_urls"]
            repos = [u for u in links if (url_key(u) or "").startswith("github:")]
            primary = next(iter(repos), next((u for u in links if url_key(u)), ""))
            site = links[0] if links and primary in repos and links[0] not in repos else None
            index.add("curated", f"games[{i}].projects[{j}]", row["name"], primary,
                      "curated game project", games_source, alt=links, aliases=[site] if site else [],
                      originals=[game["title"]], genres=[game["category"]],
                      receipt=checked_source("curated"))
    topics = json.loads(local["topics"])
    for i, query in enumerate(topics["queries"]):
        for j, repo in enumerate(query["top_repos"]):
            # A query language is a dated repository-search filter rather than a code audit.
            language = re.search(r"\blanguage:([\w+#.-]+)", query["q"])
            index.add("topics", f"queries[{i}].top_repos[{j}]", repo, "https://github.com/" + repo,
                      "repository search hit", checked_source("topics"), query=query["q"],
                      languages=[language.group(1)] if language else [], search_url=query["url"])
    for i, row in enumerate(json.loads(local["primary"])["inspections"]):
        index.add("primary", f"inspections[{i}]", row["repo"], "https://github.com/" + row["repo"],
                  "inspected repository", row["readme_url"], languages=values(row["primary_language"]),
                  receipt=checked_source("primary"), readme_sha256=row["readme_sha256"],
                  license_path=row.get("root_license_path"), license_sha256=row.get("license_sha256"))
    for i, row in enumerate(json.loads(local["modules"])):
        index.add("modules", f"[{i}]", row["repo"], "https://github.com/" + row["repo"],
                  "inspected game module", row["readme"], receipt=checked_source("modules"),
                  classification=row["classification"], asset_notes=[row["license_media_scope"]],
                  terms_url=row.get("terms"), inspected_files=row["inspected_files"])


def build(data, local):
    index = Index()
    originals = import_clones(index, data)
    import_local(index, local)
    projects, ambiguous = index.projects()
    families = Counter(r["family"] for r in index.rows)
    joined = Counter()
    combinations = Counter()
    for p in projects:
        fs = sorted({s["family"] for s in p["sources"]})
        combinations[" + ".join(fs)] += 1
        joined.update(fs)
    no_url = [p["id"] for p in projects if not p["url"]]
    counts = {
        "unique_project_locations": len(projects), "observations": len(index.rows),
        "original_titles_available_for_genre_join": originals,
        "observations_by_source": dict(sorted(families.items())),
        "distinct_locations_by_source": dict(sorted(joined.items())),
        "projects_in_multiple_sources": sum(v for k, v in combinations.items() if " + " in k),
        "source_family_intersections": dict(sorted(combinations.items())),
        "ambiguous_shared_urls_excluded_from_alias_join": sorted(ambiguous),
        "locations_without_project_url": no_url,
        "distinct_locations_with_listed_language_Rust": sum("Rust" in p.get("languages", []) for p in projects),
        "projects_with_originals": sum(bool(p.get("originals")) for p in projects),
        "projects_with_genre": sum(bool(p.get("genres")) for p in projects),
        "projects_with_content_classification": sum(bool(p.get("content")) for p in projects),
    }
    if families != {"clones": 3304, "engines": 845, "curated": 140, "topics": 126,
                    "primary": 56, "modules": 21} or joined["topics"] != 114 or originals != 2005:
        raise ValueError("Pinned coverage changed. Inspect both input files and joins.")
    return projects, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-inputs", action="store_true",
                        help="replace the upstream snapshot with the same pinned files after hashing")
    parser.add_argument("--verify", action="store_true", help="compare computed outputs to the checked-in bytes")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_bytes())
    data = ensure_snapshot(manifest, args.refresh_inputs)
    local = {key: (ROOT / EXISTING / name).read_bytes() for key, name in FILES.items()}
    for key, blob in local.items():
        if digest(blob) != manifest["local"][key]["sha256"]:
            sys.exit(f"Local catalog receipt checksum mismatch: {FILES[key]}")
    projects, counts = build(data, local)
    outputs = {OUTPUT: packed(compact(projects)), SUMMARY: pretty(counts)}
    for path, blob in outputs.items():
        if args.verify:
            if not path.exists() or path.read_bytes() != blob:
                sys.exit(f"Output differs: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
    print(f"{len(projects):,} unique locations from {counts['observations']:,} observations. "
          f"SHA-256 {digest(outputs[OUTPUT])}")


if __name__ == "__main__":
    main()
