#!/usr/bin/env python3
"""Build, query, and verify the game resource library using Python's standard library."""

import argparse
import base64
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FORKS = ROOT.parents[1] / "games/yuga-native/docs/rust-rebuild/deep-search/rea"
DB = ROOT / "library.sqlite"
PAGE = ROOT / "library.html"
CATEGORIES = {
    "ui",
    "graphics",
    "animation",
    "characters",
    "blender",
    "world",
    "gameplay",
    "audio",
    "build",
}
SCHEMA = """
PRAGMA foreign_keys=ON;
PRAGMA user_version=1;
CREATE TABLE projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT, kind TEXT, language TEXT, metadata TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE project_sources(project_id TEXT REFERENCES projects(id), seq INTEGER, name TEXT NOT NULL, url TEXT, observation TEXT NOT NULL, PRIMARY KEY(project_id,seq)) WITHOUT ROWID;
CREATE TABLE elements(id TEXT PRIMARY KEY, name TEXT NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id), project TEXT NOT NULL, revision TEXT NOT NULL, path TEXT NOT NULL, category TEXT NOT NULL, kind TEXT NOT NULL, summary TEXT NOT NULL, adaptation TEXT NOT NULL, evidence TEXT NOT NULL, sha256 TEXT NOT NULL, license TEXT NOT NULL, license_path TEXT, rights_note TEXT NOT NULL, use TEXT NOT NULL, source_url TEXT NOT NULL, license_url TEXT, symbol TEXT) WITHOUT ROWID;
CREATE TABLE element_facets(element_id TEXT REFERENCES elements(id), dimension TEXT, value TEXT, PRIMARY KEY(element_id,dimension,value)) WITHOUT ROWID;
CREATE INDEX by_facet ON element_facets(dimension,value);
CREATE INDEX by_category ON elements(category,use);
CREATE INDEX by_project ON elements(project_id);
CREATE INDEX by_blob ON elements(sha256);
CREATE VIRTUAL TABLE element_search USING fts5(id UNINDEXED,name,project,kind,tags,summary,adaptation, tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE project_search USING fts5(id UNINDEXED,name,description, tokenize='unicode61 remove_diacritics 2');
CREATE TABLE assets(id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id), revision TEXT NOT NULL, path TEXT, source_url TEXT NOT NULL, license TEXT, license_url TEXT, author TEXT, summary TEXT, rights_note TEXT, evidence TEXT NOT NULL, sha256 TEXT, metadata TEXT NOT NULL) WITHOUT ROWID;
CREATE INDEX asset_by_kind ON assets(kind,license);
CREATE VIRTUAL TABLE asset_search USING fts5(id UNINDEXED,name,kind,author,tags,clips,summary,tokenize='unicode61 remove_diacritics 2');
CREATE TABLE rea_forks(id INTEGER PRIMARY KEY, repository TEXT NOT NULL, created_utc TEXT, default_branch TEXT, github_language TEXT, description TEXT, topics TEXT);
CREATE INDEX fork_name ON rea_forks(repository COLLATE NOCASE);
CREATE INDEX fork_language ON rea_forks(github_language);
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_url(url):
    if not isinstance(url, str):
        return None
    parts = urlsplit(url)
    return (
        url
        if parts.scheme in ("http", "https")
        and parts.hostname
        and not parts.username
        and not parts.password
        else None
    )


def anchored(project, revision, path):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", project):
        raise ValueError(f"Invalid GitHub repository: {project}")
    if (
        not re.fullmatch("[0-9a-f]{40}", revision)
        or not path
        or ".." in Path(path).parts
        or path.startswith("/")
    ):
        raise ValueError(f"Invalid source pin for {project}: {revision} {path}")
    return f'https://github.com/{project}/blob/{revision}/{quote(path, safe="/")}'


def load_sources():
    found = {}
    for filename in sorted((ROOT / "sources").glob("*.json")):
        if filename.name == "discovery-inputs.json":
            continue
        for row in json.loads(filename.read_text()):
            identity = row["id"]
            if identity in found or not re.fullmatch("[a-z0-9][a-z0-9._-]*", identity):
                raise ValueError(
                    f"Duplicate or invalid ID {identity} in {filename.name}"
                )
            for key in (
                "name",
                "project",
                "revision",
                "path",
                "category",
                "kind",
                "summary",
                "adaptation",
                "evidence",
                "sha256",
                "license",
                "rights_note",
                "use",
            ):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ValueError(f"{identity} has no {key}")
            if (
                row["category"] not in CATEGORIES
                or row["use"] not in {"adapt", "study", "verify-terms"}
                or row["evidence"]
                not in {"source-read", "format-inspected", "executed"}
                or not re.fullmatch("[0-9a-f]{64}", row["sha256"])
            ):
                raise ValueError(
                    f"{identity} has an invalid classification or checksum"
                )
            for field in ("stack", "formats", "tags"):
                if (
                    not isinstance(row.get(field), list)
                    or not all(isinstance(v, str) and v.strip() for v in row[field])
                    or len(set(row[field])) != len(row[field])
                ):
                    raise ValueError(f"{identity} has invalid {field}")
            if row["use"] == "adapt" and (
                not row.get("license_path")
                or row["license"].lower()
                in {"unknown", "unverified", "unspecified", "noassertion"}
            ):
                raise ValueError(
                    f"{identity} needs file-specific terms evidence for adaptation"
                )
            repo_url = row.get("repo_url") or "https://github.com/" + row["project"]
            host = urlsplit(repo_url).hostname
            gb_path = anchored(row["project"], row["revision"], row["path"])
            if host == "github.com":
                row["source_url"] = gb_path
                row["license_url"] = (
                    anchored(
                        row.get("license_project") or row["project"],
                        row.get("license_revision") or row["revision"],
                        row["license_path"],
                    )
                    if row.get("license_path")
                    else None
                )
                row["project_id"] = "github:" + row["project"].lower()
            elif (
                host in {"projects.blender.org", "codeberg.org"}
                and repo_url == f"https://{host}/" + row["project"]
            ):
                for path_key, link_key in [
                    ("path", "source_url"),
                    ("license_path", "license_url"),
                ]:
                    if row.get(path_key):
                        expected = (
                            repo_url
                            + "/src/commit/"
                            + row["revision"]
                            + "/"
                            + quote(row[path_key], safe="/")
                        )
                        if row.get(link_key) and row[link_key] != expected:
                            raise ValueError(
                                f"{identity}: unexpected pinned URL {row[link_key]}"
                            )
                        row[link_key] = expected
                row["project_id"] = "codeforge:" + host + "/" + row["project"].lower()
            else:
                raise ValueError(f"{identity}: unsupported project identity {repo_url}")
            found[identity] = row
    return list(sorted(found.values(), key=lambda r: (r["name"].casefold(), r["id"])))


def collect():
    with gzip.open(ROOT / "data/discovery.json.gz", "rt", encoding="utf-8") as stream:
        projects = json.load(stream)
    elements = load_sources()
    assets = []
    for name in ("icons", "models"):
        with gzip.open(ROOT / f"data/{name}.json.gz", "rt", encoding="utf-8") as stream:
            assets.extend(json.load(stream))
    by_id = {str(p["id"]): p for p in projects}
    if len(by_id) != len(projects):
        raise ValueError("Duplicate project identities in discovery input")
    for e in elements:
        key = e["project_id"]
        if key not in by_id:
            by_id[key] = {
                "id": key,
                "name": e["project"],
                "url": e.get("repo_url") or "https://github.com/" + e["project"],
                "kind": "inspected repository",
                "language": None,
                "sources": [],
            }
        e["project_id"] = key
    for a in assets:
        key = "github:" + a["project"].lower()
        by_id.setdefault(
            key,
            {
                "id": key,
                "name": a["project"],
                "url": "https://github.com/" + a["project"],
                "kind": "asset repository",
                "language": None,
                "sources": [],
            },
        )
        a["project_id"] = key
    for row in [*elements, *assets]:
        parent = by_id[row["project_id"]]
        if not parent.get("sources"):
            parent["sources"] = [
                {"name": "Inspected source repository", "url": row["source_url"]}
            ]
    return elements, sorted(by_id.values(), key=lambda p: p["id"]), assets


def build():
    elements, projects, assets = collect()
    receipt = json.loads((FORKS / "direct-forks.json").read_text())
    forks = FORKS / receipt["archive"]
    if digest(forks) != receipt["archive_sha256"]:
        raise ValueError("Fork census checksum mismatch")
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        target = Path(tmp) / DB.name
        db = sqlite3.connect(target)
        db.executescript(SCHEMA)
        browser_projects = []
        for p in projects:
            pid = p["id"]
            meta = {
                k: v
                for k, v in p.items()
                if k not in {"name", "url", "id", "sources", "kind", "language"}
            }
            db.execute(
                "INSERT INTO projects VALUES(?,?,?,?,?,?)",
                (
                    pid,
                    p["name"],
                    safe_url(p.get("url")),
                    p.get("kind"),
                    p.get("language"),
                    json.dumps(meta, ensure_ascii=False, separators=(",", ":")),
                ),
            )
            for i, source in enumerate(p.get("sources", [])):
                db.execute(
                    "INSERT INTO project_sources VALUES(?,?,?,?,?)",
                    (
                        pid,
                        i,
                        source["name"],
                        safe_url(source.get("url")),
                        json.dumps(source, ensure_ascii=False, separators=(",", ":")),
                    ),
                )
            labels = []
            for k in (
                "languages",
                "platforms",
                "genres",
                "status",
                "originals",
                "aliases",
            ):
                if p.get(k):
                    labels.append(
                        " ".join(map(str, p[k]))
                        if isinstance(p[k], list)
                        else str(p[k])
                    )
            db.execute(
                "INSERT INTO project_search VALUES(?,?,?)",
                (
                    pid,
                    p["name"],
                    " ".join([p.get("kind") or "", p.get("language") or "", *labels]),
                ),
            )
            browser_projects.append(
                {
                    k: v
                    for k, v in p.items()
                    if k
                    in {
                        "id",
                        "name",
                        "kind",
                        "url",
                        "language",
                        "languages",
                        "genres",
                        "platforms",
                        "status",
                        "originals",
                        "content",
                        "listed_licenses",
                        "development",
                        "aliases",
                    }
                }
                | {
                    "sources": [
                        {"name": s["name"], "url": safe_url(s.get("url"))}
                        for s in p.get("sources", [])
                    ]
                }
            )
        for e in elements:
            values = [
                e.get(k)
                for k in (
                    "id",
                    "name",
                    "project_id",
                    "project",
                    "revision",
                    "path",
                    "category",
                    "kind",
                    "summary",
                    "adaptation",
                    "evidence",
                    "sha256",
                    "license",
                    "license_path",
                    "rights_note",
                    "use",
                    "source_url",
                    "license_url",
                    "symbol",
                )
            ]
            db.execute(
                "INSERT INTO elements VALUES(" + ",".join("?" for _ in values) + ")",
                values,
            )
            for field in ("stack", "formats", "tags"):
                db.executemany(
                    "INSERT INTO element_facets VALUES(?,?,?)",
                    [(e["id"], field, v) for v in e[field]],
                )
            db.execute(
                "INSERT INTO element_search VALUES(?,?,?,?,?,?,?)",
                (
                    e["id"],
                    e["name"],
                    e["project"],
                    e["kind"],
                    " ".join([e["category"], *e["stack"], *e["formats"], *e["tags"]]),
                    e["summary"],
                    e["adaptation"],
                ),
            )
        for a in assets:
            if not safe_url(a["source_url"]) or not re.fullmatch(
                "[0-9a-f]{40}", a["revision"]
            ):
                raise ValueError(f"Asset source pin missing: {a['id']}")
            keys = (
                "id",
                "name",
                "kind",
                "project_id",
                "revision",
                "path",
                "source_url",
                "license",
                "license_url",
                "author",
                "summary",
                "rights_note",
                "evidence",
                "sha256",
            )
            meta = {k: v for k, v in a.items() if k not in keys and k != "preview_data"}
            values = [a.get(k) for k in keys] + [
                json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
            ]
            db.execute(
                "INSERT INTO assets VALUES(" + ",".join("?" for _ in values) + ")",
                values,
            )
            counts = a.get("counts", {})
            terms = list(a.get("tags", [])) + list(a.get("extensions", []))
            if counts.get("skins"):
                terms.extend(["skinned", "rigged", "skeleton"])
            if counts.get("animations"):
                terms.append("animated")
            db.execute(
                "INSERT INTO asset_search VALUES(?,?,?,?,?,?,?)",
                (
                    a["id"],
                    a["name"],
                    a["kind"],
                    a.get("author"),
                    " ".join(terms),
                    " ".join(x for x in a.get("clips", []) if isinstance(x, str)),
                    a.get("summary"),
                ),
            )
        with gzip.open(forks, "rt", encoding="utf-8", newline="") as stream:
            db.executemany(
                "INSERT INTO rea_forks VALUES(?,?,?,?,?,?,?)",
                (
                    (
                        int(r["id"]),
                        r["repository"],
                        r["created_utc"],
                        r["default_branch"],
                        r["github_language"] or None,
                        r["description"] or None,
                        r["topics"] or None,
                    )
                    for r in csv.DictReader(stream, delimiter="\t")
                ),
            )
        db.commit()
        assert (
            db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            and not db.execute("PRAGMA foreign_key_check").fetchall()
        )
        assert (
            db.execute("SELECT count(*) FROM rea_forks").fetchone()[0]
            == receipt["unique_repository_ids"]
        )
        db.close()
        sheet_path = ROOT / "evidence/button-state-contact-sheet.png"
        guide = json.loads((ROOT / "search/button-states.json").read_text())
        button_ids = sorted(
            {
                element_id
                for group in guide["sets"]
                for element_id in group["element_ids"]
            }
        )
        if (
            not button_ids
            or not set(button_ids).issubset({e["id"] for e in elements})
            or not sheet_path.is_file()
        ):
            raise ValueError(
                "The button families and their state comparison must be available together"
            )
        button_sheet = {
            "ids": button_ids,
            "image": "data:image/png;base64,"
            + base64.b64encode(sheet_path.read_bytes()).decode(),
            "label": "Kenney primary and parchment button textures and raygui light-theme button states",
            "credits": guide["credits"],
        }
        payload = (
            json.dumps(
                {
                    "elements": elements,
                    "projects": browser_projects,
                    "assets": assets,
                    "buttonSheet": button_sheet,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            .replace("<", "\\u003c")
            .replace("&", "\\u0026")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )
        template = (ROOT / "web/template.html").read_text()
        marker = "/* RESOURCE_DATA */"
        if template.count(marker) != 1:
            raise ValueError("Expected exactly one offline data marker")
        html = Path(tmp) / PAGE.name
        html.write_text(template.replace(marker, payload))
        target.replace(DB)
        html.replace(PAGE)
    return verify()


def verify():
    with sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True) as db:
        one = lambda sql: db.execute(sql).fetchone()[0]
        assert (
            one("PRAGMA integrity_check") == "ok"
            and not db.execute("PRAGMA foreign_key_check").fetchall()
        )
        assert one("SELECT count(*) FROM elements") == one(
            "SELECT count(*) FROM element_search"
        )
        assert one("SELECT count(*) FROM projects") == one(
            "SELECT count(*) FROM project_search"
        )
        assert one("SELECT count(*) FROM assets") == one(
            "SELECT count(*) FROM asset_search"
        )
        assert not one(
            "SELECT COUNT(*) FROM elements WHERE use='adapt' AND license_url IS NULL"
        )
        stats = {
            k: one("SELECT COUNT(*) FROM " + k)
            for k in ("elements", "projects", "project_sources", "assets", "rea_forks")
        }
        stats["inspected_projects"] = one(
            "SELECT COUNT(DISTINCT project_id) FROM elements"
        )
        stats["unique_element_blobs"] = one(
            "SELECT COUNT(DISTINCT sha256) FROM elements"
        )
        stats["forks_without_reported_language"] = one(
            "SELECT COUNT(*) FROM rea_forks WHERE github_language IS NULL"
        )
        stats["discovery_projects_without_url"] = one(
            "SELECT COUNT(*) FROM projects WHERE url IS NULL"
        )
        for k in ("category", "use", "evidence"):
            stats["by_" + k] = dict(
                db.execute(
                    f"SELECT {k},COUNT(*) FROM elements GROUP BY {k} ORDER BY 2 DESC,1"
                )
            )
        stats["asset_kinds"] = dict(
            db.execute("SELECT kind,COUNT(*) FROM assets GROUP BY kind")
        )
        stats["projects_with_element_or_asset"] = one(
            "SELECT COUNT(*) FROM (SELECT project_id FROM assets UNION SELECT project_id FROM elements)"
        )
        stats["inspected_elements_without_terms_link"] = one(
            "SELECT count(*) FROM elements WHERE license_url IS NULL"
        )
        stats["foreign_key_violations"] = 0
        stats["sqlite_integrity"] = "ok"
        for term in ["button", "animation", "Blender"]:
            assert db.execute(
                "SELECT id FROM element_search WHERE element_search MATCH ? LIMIT 1",
                (term,),
            ).fetchone(), term
    stats["sqlite_sha256"] = digest(DB)
    stats["html_sha256"] = digest(PAGE)
    return stats


def search(args):
    with sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True) as db:
        words = re.findall(r"[\w]+", args.query, re.UNICODE)
        if not words:
            raise ValueError("Enter a search term")
        expression = " AND ".join('"' + w + '"*' for w in words)
        if args.assets:
            sql = "SELECT a.name,a.source_url,a.license FROM asset_search f JOIN assets a ON a.id=f.id WHERE asset_search MATCH ? ORDER BY rank LIMIT ?"
            params = [expression, args.limit]
        elif args.projects:
            sql = "SELECT p.name,p.url,p.kind FROM project_search f JOIN projects p ON p.id=f.id WHERE project_search MATCH ? ORDER BY rank LIMIT ?"
            params = [expression, args.limit]
        else:
            sql = "SELECT e.name,e.source_url,e.use FROM element_search f JOIN elements e ON e.id=f.id WHERE element_search MATCH ?"
            params = [expression]
            if args.category:
                sql += " AND e.category=?"
                params.append(args.category)
            sql += " ORDER BY rank LIMIT ?"
            params.append(args.limit)
        for name, url, kind in db.execute(sql, params):
            print(f'{name}\t{kind or ""}\t{url or ""}')


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("verify")
    q = sub.add_parser("search")
    q.add_argument("query")
    scope = q.add_mutually_exclusive_group()
    scope.add_argument("--projects", action="store_true")
    scope.add_argument("--assets", action="store_true")
    q.add_argument("--category", choices=sorted(CATEGORIES))
    q.add_argument("--limit", type=int, default=20)
    args = p.parse_args()
    if args.cmd == "search":
        search(args)
    else:
        stats = build() if args.cmd == "build" else verify()
        if args.cmd == "build":
            (ROOT / "evidence/quality.json").write_text(
                json.dumps(stats, ensure_ascii=False, indent=2) + "\n"
            )
        print(json.dumps(stats, ensure_ascii=False, indent=2))
