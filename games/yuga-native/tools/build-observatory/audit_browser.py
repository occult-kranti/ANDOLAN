#!/usr/bin/env python3
"""Inspect an actual published observatory in Chromium, without mocked responses.

Reuses the selectors and keyboard/layout checks from web/verify_ui.py. Explicit
source pins and expected counts make this reusable across saved publications.
This checks dashboard delivery and interaction, not game execution or art quality.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import getproxies

from playwright.sync_api import sync_playwright


def digest(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--source", required=True, help="Full dashboard publication commit")
    parser.add_argument("--observed-source", required=True, help="Full saved snapshot commit")
    parser.add_argument("--snapshot-sha256", required=True)
    for name in ("jobs", "assets", "stages"):
        parser.add_argument(f"--expected-{name}", required=True, type=int)
    parser.add_argument("--blocked-job", action="append", default=[])
    parser.add_argument("--select-job", required=True)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if (parsed.scheme not in {"http", "https"} or not parsed.netloc
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        parser.error("Expected a credential-free HTTP(S) dashboard URL")
    for name, width in (("source", 40), ("observed_source", 40), ("snapshot_sha256", 64)):
        if not re.fullmatch(r"[0-9a-f]{%d}" % width, getattr(args, name)):
            parser.error(f"{name} must be a full lowercase hexadecimal pin")
    if any(not 0 <= getattr(args, f"expected_{key}") <= 1000 for key in ("jobs", "assets", "stages")):
        parser.error("Expected counts must be between zero and 1000")
    if any(not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", item) for item in [args.select_job, *args.blocked_job]):
        parser.error("Job IDs must be bounded alphanumeric identifiers")
    if len(set(args.blocked_job)) != len(args.blocked_job):
        parser.error("Blocked job IDs must be unique")
    args.base_url = args.base_url.rstrip("/") + "/"
    return args


def audit(args):
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {
        "schema": 1, "passed": False,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "arguments": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "auditor": digest(Path(__file__).read_bytes()),
        "checks": [], "screenshots": [], "page_errors": [], "console_errors": [],
        "http_errors": [], "failed_requests": [], "page_snapshots": [], "links": [],
        "limits": ["Actual public saved-snapshot dashboard in Chromium; responses were not mocked.",
                   "Native gameplay, online matches, art acceptance and physical GPU performance are not tested.",
                   "Report outputs without URL fields are display text, not asserted clickable links.",
                   "Media link availability is checked; the separate HTTP auditor verifies the complete delivered-byte inventory."],
    }

    def check(name, condition, detail=None):
        row = {"name": name, "passed": bool(condition)}
        if detail is not None:
            row["detail"] = detail
        receipt["checks"].append(row)
        if not condition:
            raise AssertionError(name)

    def screenshot(page, name, full_page=False):
        path = args.output / name
        page.screenshot(path=str(path), full_page=full_page, timeout=30000)
        receipt["screenshots"].append({"file": name, "full_page": full_page,
                                       "viewport": page.viewport_size, **digest(path.read_bytes())})

    def response_seen(response):
        if response.status >= 400:
            receipt["http_errors"].append({"url": response.url, "status": response.status,
                                           "resource_type": response.request.resource_type})
        if response.url == urljoin(args.base_url, "status.json"):
            try:
                receipt["page_snapshots"].append({"url": response.url, "status": response.status,
                                                   **digest(response.body())})
            except Exception as error:
                receipt["page_snapshots"].append({"url": response.url, "error": str(error)})

    browser = None
    try:
        with sync_playwright() as p:
            # Playwright does not automatically inherit Python's proxy behavior.
            # Use the runtime's configured route, retaining normal TLS validation.
            proxy_url = getproxies().get(urlsplit(args.base_url).scheme)
            launch = {"executable_path": args.chromium, "headless": True, "args": ["--no-sandbox"]}
            if proxy_url:
                parsed_proxy = urlsplit(proxy_url)
                if parsed_proxy.username or parsed_proxy.password:
                    raise ValueError("Use a runtime proxy without credentials embedded in its URL")
                launch["proxy"] = {"server": proxy_url}
            receipt["transport"] = {"inherited_proxy": bool(proxy_url), "TLS_verification": True}
            browser = p.chromium.launch(**launch)
            receipt["browser_version"] = browser.version
            context = browser.new_context(viewport={"width": 1440, "height": 1080}, reduced_motion="reduce")
            page = context.new_page()
            page.set_default_timeout(20000)
            page.on("pageerror", lambda error: receipt["page_errors"].append(str(error)))
            page.on("console", lambda message: receipt["console_errors"].append(message.text) if message.type == "error" else None)
            page.on("response", response_seen)
            page.on("requestfailed", lambda request: receipt["failed_requests"].append({"url": request.url, "failure": request.failure}))
            for name in ("publication.json", "status.json"):
                response = context.request.get(urljoin(args.base_url, name), timeout=45000)
                raw = response.body()
                (args.output / name).write_bytes(raw)
                check(f"{name}_HTTP200", response.status == 200, {"url": response.url, **digest(raw)})
                body = json.loads(raw)
                check(f"{name}_object", isinstance(body, dict))
                if name == "publication.json":
                    check("publication_dashboard_source", body.get("dashboard_source") == args.source)
                else:
                    snapshot = body
                    check("snapshot_exact_bytes", digest(raw)["sha256"] == args.snapshot_sha256)
            check("saved_snapshot_source", snapshot.get("mode") == "snapshot"
                  and snapshot.get("source", {}).get("commit") == args.observed_source
                  and snapshot.get("source", {}).get("dirty") is False)
            jobs = {job["id"]: job for job in snapshot["jobs"]}
            check("selected_job_exists", args.select_job in jobs)
            expected_counts = {"jobs": args.expected_jobs, "assets": args.expected_assets, "milestones": args.expected_stages}
            check("snapshot_counts", all(len(snapshot[key]) == value for key, value in expected_counts.items()), expected_counts)
            check("snapshot_blocked_jobs", sorted(job["id"] for job in jobs.values() if job["status"] == "blocked") == sorted(args.blocked_job))
            navigation = page.goto(args.base_url, wait_until="domcontentloaded", timeout=45000)
            check("dashboard_HTTP200", navigation is not None and navigation.status == 200)
            page.get_by_text("Saved snapshot — not live", exact=True).wait_for()
            check("saved_label_and_source", page.locator("#connection-label").inner_text() == "Saved snapshot — not live"
                  and page.locator("#source-commit").inner_text() == args.observed_source[:12]
                  and page.locator("#source-dirty").inner_text() == "Clean checkout")
            check("run_title_and_branch", page.locator("#run-title").inner_text() == snapshot["run"]["title"]
                  and page.locator("#source-branch").inner_text() == snapshot["source"]["branch"])
            counts = {"jobs": page.locator(".job-row").count(), "assets": page.locator("#artifact-list .artifact").count(),
                      "milestones": page.locator("#milestone-list .milestone").count()}
            check("rendered_counts", counts == expected_counts, counts)
            check("rendered_job_ids", sorted(page.locator(".job-row").evaluate_all("nodes => nodes.map(n => n.dataset.jobId)")) == sorted(jobs))
            page.locator("#status-filter").select_option("blocked")
            blocked = page.locator(".job-row").evaluate_all("nodes => nodes.map(n => n.dataset.jobId)")
            check("blocked_filter_exact_ids", sorted(blocked) == sorted(args.blocked_job), blocked)
            if len(args.blocked_job) == 1:
                check("blocked_inspector", page.locator("#inspector-title").inner_text() == jobs[args.blocked_job[0]]["title"])
            screenshot(page, "blocked-desktop.png")
            page.locator("#clear-filters").click()
            check("clear_filter_restores_jobs", page.locator(".job-row").count() == args.expected_jobs)
            selected = page.locator(f'.job-row[data-job-id="{args.select_job}"]')
            selected.focus()
            page.keyboard.press("Enter")
            keyboard = {"focused_id": page.evaluate("document.activeElement.dataset.jobId"),
                        "pressed": selected.get_attribute("aria-pressed"), "controls": selected.get_attribute("aria-controls"),
                        "inspector": page.locator("#inspector-title").inner_text()}
            check("keyboard_selection_and_focus", keyboard == {"focused_id": args.select_job, "pressed": "true",
                  "controls": "job-detail", "inspector": jobs[args.select_job]["title"]}, keyboard)
            screenshot(page, "keyboard-selected-desktop.png")
            # Scroll naturally through lazy images, then ask the browser decoder
            # to finish the actual image. No responses, sources or pixels change.
            images = page.locator("#lead-image, #artifact-list img")
            decoded = []
            for index in range(images.count()):
                item = images.nth(index)
                item.scroll_into_view_if_needed()
                decoded.append(item.evaluate("async img => { await img.decode(); return {src: img.currentSrc, width: img.naturalWidth, height: img.naturalHeight, complete: img.complete}; }"))
            expected_images = [asset for asset in snapshot["assets"] if asset.get("image_url")]
            check("all_rendered_images_decode", len(decoded) == len(expected_images) + (1 if expected_images else 0)
                  and all(item["complete"] and item["width"] > 0 and item["height"] > 0 for item in decoded), decoded)
            actual_asset_links = page.locator("#artifact-list .artifact-links a").evaluate_all("nodes => nodes.map(n => ({label:n.textContent, url:n.href}))")
            expected_asset_links = [{"label": label, "url": urljoin(args.base_url, asset[key])}
                                    for asset in snapshot["assets"] for key, label in (("image_url", "Open render"), ("model_url", "Open 3D source"))
                                    if asset.get(key)]
            check("actual_asset_links_match_snapshot", actual_asset_links == expected_asset_links, actual_asset_links)
            links = {item["url"] for item in actual_asset_links}
            for job_id, job in jobs.items():
                page.locator(f'.job-row[data-job-id="{job_id}"]').click()
                actual = page.locator("#job-detail a").evaluate_all("nodes => nodes.map(n => n.href)")
                expected = [urljoin(args.base_url, item["url"]) for item in job.get("outputs", []) if item.get("url")]
                check(f"job_output_links_{job_id}", actual == expected, actual)
                links.update(actual)
            origin = urlsplit(args.base_url)
            for url in sorted(links):
                parsed = urlsplit(url)
                check("link_safe_origin", (parsed.scheme, parsed.netloc) == (origin.scheme, origin.netloc)
                      and not parsed.username and not parsed.password, url)
                response = context.request.head(url, timeout=45000)
                row = {"url": url, "final_url": response.url, "status": response.status,
                       "content_type": response.headers.get("content-type")}
                receipt["links"].append(row)
                check("linked_media_available", response.status == 200, row)
            page.locator(f'.job-row[data-job-id="{args.select_job}"]').click()
            for width, height in ((1440, 1080), (390, 844), (320, 740)):
                page.set_viewport_size({"width": width, "height": height})
                page.evaluate("document.fonts.ready")
                page.evaluate("window.scrollTo(0,0)")
                dimensions = page.evaluate("({innerWidth, scrollWidth:document.documentElement.scrollWidth, innerHeight, scrollHeight:document.documentElement.scrollHeight})")
                check(f"no_horizontal_overflow_{width}", dimensions["scrollWidth"] <= width, dimensions)
                screenshot(page, f"public-{width}-top.png")
                screenshot(page, f"public-{width}-full.png", full_page=True)
            check("public_saved_label_after_interactions", page.locator("#connection-label").inner_text() == "Saved snapshot — not live")
            check("browser_loaded_pinned_snapshot", bool(receipt["page_snapshots"]) and all(
                row.get("status") == 200 and row.get("sha256") == args.snapshot_sha256 for row in receipt["page_snapshots"]))
            # A Pages installation has no live /api/status endpoint. Its observed
            # HTTP404 is the designed fallback to the saved snapshot, not a JS error.
            fallback = urljoin(args.base_url, "/api/status")
            unexpected_http = [row for row in receipt["http_errors"] if not (row["url"] == fallback and row["status"] == 404)]
            check("no_unexpected_HTTP_errors", not unexpected_http, unexpected_http)
            check("no_failed_requests", not receipt["failed_requests"])
            check("no_page_JavaScript_errors", not receipt["page_errors"])
            receipt["passed"] = True
            context.close()
            browser.close()
            browser = None
    except Exception as error:
        receipt["failure"] = f"{type(error).__name__}: {error}"
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        receipt["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    result = audit(arguments())
    print(json.dumps({"passed": result["passed"], "checks": len(result["checks"]),
                      "screenshots": len(result["screenshots"]), "failure": result.get("failure")}))
    raise SystemExit(0 if result["passed"] else 1)
