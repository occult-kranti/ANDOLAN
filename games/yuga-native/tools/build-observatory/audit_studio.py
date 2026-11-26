#!/usr/bin/env python3
"""Exercise the actual public or loopback Mandala art book in Chromium.

Runs the gallery through its UI using the same catalog a visitor sees. Per-file
SHA-256 delivery belongs to audit_public.py; this checks switching and decoding.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import getproxies

from playwright.sync_api import sync_playwright

# Check the source file header. CDNs can otherwise range a compressed
# representation whose first 32 bytes cannot be independently decompressed.
FILE_HEADER = {"Range": "bytes=0-31", "Accept-Encoding": "identity"}


def verify(base, output, chromium):
    output.mkdir(parents=True, exist_ok=False)
    record = {"url": base, "passed": False, "checks": [], "studies": [], "viewports": [],
              "page_errors": [], "http_errors": [], "console_errors": []}

    def check(name, result):
        record["checks"].append({"name": name, "passed": bool(result)})
        if not result:
            raise AssertionError(name)

    try:
        with sync_playwright() as playwright:
            launch = {"executable_path": chromium, "headless": True, "args": ["--no-sandbox"]}
            parsed = urlsplit(base)
            proxy = getproxies().get(parsed.scheme)
            if proxy and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
                launch["proxy"] = {"server": proxy}
            browser = playwright.chromium.launch(**launch)
            record["chromium"] = browser.version
            context = browser.new_context(viewport={"width":1440,"height":900}, reduced_motion="reduce")
            page = context.new_page()

            def observe(tab):
                tab.set_default_timeout(20000)
                tab.on("pageerror", lambda error: record["page_errors"].append(str(error)))
                tab.on("response", lambda r: record["http_errors"].append({"url":r.url,"status":r.status}) if r.status >= 400 else None)
                tab.on("console", lambda m: record["console_errors"].append({"text":m.text,"url":m.location.get("url")}) if m.type == "error" else None)

            observe(page)
            catalog = context.request.get(urljoin(base, "catalog.json")).json()
            concepts = context.request.get(urljoin(base, "concepts/index.json")).json()
            models = context.request.get(urljoin(base, "models/index.json")).json()
            elements = catalog["elements"]
            check("registered model inventory", set(models["models"]) == {item["id"] for item in elements}
                  and models["layout_sha256"] == catalog["layout_sha256"])
            page.goto(base, wait_until="domcontentloaded")
            page.locator(".study").first.wait_for()
            check("full count and initial page", page.locator("#index-count").inner_text() == f"{len(elements)} elements"
                  and page.locator(".study").count() == min(9,len(elements)))
            start = page.locator(".study").count()
            if len(elements) > start:
                page.locator("#more").click()
                check("pagination and keyboard focus", page.locator(".study").count() > start
                      and page.evaluate("document.activeElement === document.querySelectorAll('.study')[" + str(start) + "]"))
            for kind in {e["kind"] for e in elements}:
                page.locator(f'#filters button[data-kind="{kind}"]').click()
                check("filter " + kind, all(e in [r["id"] for r in elements if r["kind"] == kind]
                      for e in page.locator(".study").evaluate_all("ns => ns.map(n => n.dataset.id)")))
            page.locator("#search").fill("zzunmatched-studio-item")
            check("empty query result", page.locator("#empty").is_visible() and not page.locator(".study").count())
            page.locator("#search").fill("")
            page.locator('#filters button[data-kind="all"]').click()
            page.locator("#detail").wait_for(state="hidden")
            card = page.locator(".study").first
            card.focus()
            page.keyboard.press("Enter")
            page.locator("dialog[open]").wait_for()
            page.keyboard.press("Escape")
            page.locator("dialog[open]").wait_for(state="hidden")
            check("index returns keyboard focus", card.evaluate("node => document.activeElement === node"))

            def image_ok(locator):
                locator.scroll_into_view_if_needed()
                return locator.evaluate("async img => { await img.decode(); return img.naturalWidth > 0 && img.naturalHeight > 0; }")

            def video_frame(locator):
                locator.scroll_into_view_if_needed()
                return locator.evaluate("""async v => {
                  v.muted = true;
                  const next = new Promise((resolve,reject) => {
                    const t = setTimeout(() => reject(Error('No presented frame')), 15000);
                    const done = () => {clearTimeout(t); resolve();};
                    if (v.requestVideoFrameCallback) v.requestVideoFrameCallback(done);
                    else v.addEventListener('timeupdate',done,{once:true});
                  });
                  await v.play(); await next; v.pause();
                  return {duration:v.duration,width:v.videoWidth,height:v.videoHeight};
                }""")

            media = page.locator("#media-view")
            for item in elements:
                page.evaluate("id => { location.hash = 'element=' + encodeURIComponent(id); }", item["id"])
                page.get_by_role("heading",name=item["title"],exact=True,level=2).wait_for()
                check("deep link " + item["id"], page.locator("dialog[open]").count() == 1)
                model = page.get_by_role("link", name="Download " + item["title"] + " model")
                model_url = model.get_attribute("href")
                local_model = models["models"][item["id"]]
                check("individual model link " + item["id"], model_url == "./models/" + local_model["file"]
                      and local_model["file"] == item["id"] + ".glb" and model.get_attribute("download") is not None)
                model_header = context.request.get(urljoin(base, model_url),headers=FILE_HEADER)
                check("individual GLB header " + item["id"], model_header.status in {200,206}
                      and model_header.body()[:8] == b"glTF\x02\x00\x00\x00")
                model_header.dispose()
                seen = []
                for label, key in (("Concept art","concept"),("Blender views","render"),("Scale drawing","plate"),("Motion","clip")):
                    if key == "concept" and item["id"] not in concepts.get("items", {}):
                        continue
                    button = page.locator("#media-options").get_by_role("button",name=label,exact=True)
                    button.click()
                    if key == "clip":
                        frame = video_frame(media.locator("video"))
                        if not (frame["duration"] > 0 and frame["width"] and frame["height"]):
                            raise AssertionError(f"Unplayable film for {item['id']}")
                    else:
                        if not image_ok(media.locator("img")):
                            raise AssertionError(f"Unreadable {key} for {item['id']}")
                        if key == "concept":
                            parent = next(b for b in concepts["boards"] if b["id"] == concepts["items"][item["id"]]["board"])
                            assert media.get_by_role("link",name="Original board").get_attribute("href") == "./concepts/" + parent["file"]
                    seen.append(key)
                if item.get("assembly"):
                    page.get_by_role("button",name="Assembly plate").click()
                    check("assembly drawing", image_ok(media.locator("img")))
                    page.get_by_role("button",name="Assembly film").click()
                    frame = video_frame(media.locator("video"))
                    check("assembly sequence and part data", frame["duration"] > 0
                          and media.get_by_role("link",name="Parts and timings").get_attribute("href") == "./" + item["assembly"]["parts"])
                    seen.extend(["assembly-plate","assembly-film"])
                page.locator("#location summary").click()
                check("map registration " + item["id"], page.locator("#locator circle").count()
                      == (len(item["mouths_xyz"]) if item.get("travel_kind") == "fold" else 1))
                record["studies"].append({"id":item["id"],"media":seen})
            last = elements[-1]["id"]
            page.goto(base + "#element=" + last)
            page.reload(wait_until="domcontentloaded")
            page.locator("dialog[open]").wait_for()
            check("shared link survives reload", page.locator("#detail-title").inner_text() == elements[-1]["title"])
            page.locator("#previous").focus()
            page.keyboard.press("ArrowRight")
            check("keyboard paging changes study", page.locator("#detail-title").inner_text() != elements[-1]["title"])
            page.locator("#close").click()
            page.locator("dialog[open]").wait_for(state="hidden")
            check("cover and physically lit image decode", image_ok(page.locator("#cover-image")) and image_ok(page.locator(".lighting img")))
            for board in page.locator("#board-list img").all():
                check("concept board " + board.get_attribute("src"), image_ok(board))
            tour = video_frame(page.locator("#district-film"))
            check("district film plays", tour["duration"] > 0 and tour["width"] > 0)
            for name in ("mandala-rift.blend","mandala-rift.glb"):
                response = context.request.get(urljoin(base,name),headers=FILE_HEADER)
                magic = response.body()[:8]
                starts = (b"BLENDER",b"\x28\xb5\x2f\xfd",b"\x1f\x8b") if name.endswith(".blend") else (b"glTF",)
                check("download " + name, response.status in {200,206} and magic.startswith(starts))
                response.dispose()
            book = page.get_by_role("link",name="Complete art book")
            response = context.request.get(urljoin(base,book.get_attribute("href")),headers=FILE_HEADER)
            check("printable art book download", book.get_attribute("download") is not None
                  and response.status in {200,206} and response.body()[:5] == b"%PDF-")
            response.dispose()
            for width,height in ((1440,900),(390,844),(320,740)):
                page.set_viewport_size({"width":width,"height":height})
                page.evaluate("window.scrollTo(0,0)")
                page.evaluate("document.fonts.ready")
                check(f"home fits {width}", page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                page.screenshot(path=str(output/f"studio-{width}.png"))
                page.locator(".study").first.click()
                page.locator("dialog[open]").wait_for()
                check(f"detail fits {width}", page.locator("dialog").evaluate("d => d.scrollWidth <= d.clientWidth + 1"))
                page.screenshot(path=str(output/f"study-{width}.png"))
                page.locator("#close").click()
                page.locator("dialog[open]").wait_for(state="hidden")
                record["viewports"].append(width)
            folded = next((item for item in elements if item.get("travel_kind") == "fold"), None)
            if folded:
                mobile = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True,
                                             has_touch=True, device_scale_factor=2, reduced_motion="reduce")
                phone = mobile.new_page()
                observe(phone)
                phone.goto(base, wait_until="domcontentloaded")
                phone.locator('#filters button[data-kind="route"]').tap()
                phone.locator("#search").fill(folded["title"])
                phone.locator(f'.study[data-id="{folded["id"]}"]').tap()
                phone.locator("#location summary").tap()
                check("touch navigation opens both fold mouths", phone.locator("#locator circle").count()
                      == len(folded["mouths_xyz"]) and phone.evaluate("navigator.maxTouchPoints > 0"))
                phone.screenshot(path=str(output/"fold-touch-390.png"))
                phone.get_by_role("button",name="Motion",exact=True).tap()
                frame = video_frame(phone.locator("#media-view video"))
                check("touch route film presents a frame", frame["duration"] > 0 and frame["width"] > 0)
                phone.locator("#close").tap()
                phone.locator("dialog[open]").wait_for(state="hidden")
                check("touch returns to the filtered route index", phone.locator("#search").input_value()
                      == folded["title"] and phone.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                mobile.close()
            check("browser console, scripts and HTTP", not any(record[key] for key in ("page_errors","http_errors","console_errors")))
            record["passed"] = True
            browser.close()
    except Exception as err:
        record["failure"] = f"{type(err).__name__}: {err}"
    finally:
        (output/"receipt.json").write_text(json.dumps(record,indent=2)+"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url",required=True)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--chromium",default="/usr/bin/chromium")
    args=parser.parse_args()
    address=urlsplit(args.base_url)
    if address.scheme not in {"http","https"} or not address.hostname or address.username or address.password or address.query or address.fragment:
        parser.error("Expected a credential-free gallery HTTP(S) URL")
    report=verify(args.base_url.rstrip("/")+"/",args.output,args.chromium)
    print(json.dumps({"passed":report["passed"],"checks":len(report["checks"]),"studies":len(report["studies"]),"failure":report.get("failure")}))
    raise SystemExit(0 if report["passed"] else 1)
