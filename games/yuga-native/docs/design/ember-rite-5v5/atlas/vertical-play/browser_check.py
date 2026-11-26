"""Exercise the published fieldbook in Chromium at desktop and phone widths."""

import argparse
import json
import re
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright


def check(browser, url, width, height, photos):
    page = browser.new_page(
        viewport=dict(width=width, height=height), reduced_motion="reduce"
    )
    failures = []
    page.on("pageerror", lambda error: failures.append(str(error)))
    response = page.goto(url, wait_until="networkidle")
    assert response and response.ok
    page.wait_for_selector("#pockets .pocket")
    page.locator("#setup table tr").nth(4).wait_for()
    assert page.locator(".lead-art img").evaluate("(img)=>img.naturalWidth>0")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if photos:
        page.screenshot(path=str(photos / f"fieldbook-{width}.png"))
    c = 0
    reverse = 0
    for district in page.locator("#district option").evaluate_all(
        "(o)=>o.map(x=>x.value)"
    ):
        page.select_option("#district", district)
        for court in ("a", "b"):
            page.select_option("#court", court)
            for door in page.locator("#door option").evaluate_all(
                "(o)=>o.map(x=>x.value)"
            ):
                page.select_option("#door", door)
                assert page.locator("#pockets .pocket").count() == 2
                assert page.locator("#plan circle").count() >= 5
                page.locator("#walk").click()
                actor = page.locator("#actor-marker")
                assert actor.get_attribute("visibility") == "visible"
                origin = actor.get_attribute("cx"), actor.get_attribute("cy")
                page.locator("#walk").press("ArrowUp")
                page.locator("[data-step=east]").click()
                if origin == (actor.get_attribute("cx"), actor.get_attribute("cy")):
                    page.locator("[data-step=west]").click()
                    page.locator("[data-step=south]").click()
                assert origin != (
                    actor.get_attribute("cx"),
                    actor.get_attribute("cy"),
                ), (district, door)
                if district == "mandala":
                    page.select_option("#face", "reverse")
                    assert not page.locator("#face-label").is_hidden()
                    page.locator("#walk").click()
                    assert actor.get_attribute("visibility") == "visible"
                    page.select_option("#face", "approach")
                    reverse += 1
                c += 1
    traces = page.locator("#trace option").evaluate_all("(o)=>o.map(x=>x.value)")
    for tracer in traces:
        page.select_option("#trace", tracer)
        assert page.locator("#elevation polyline").get_attribute("points")
        assert page.locator("#trace-plan polyline").get_attribute("points")
        page.locator("#scrub").press("End")
        assert (
            str(page.locator("#scrub").get_attribute("max"))
            in page.locator("#playhead").inner_text()
        )
        assert (
            page.locator("#events li").count()
            and page.locator("#trace-result").inner_text()
        )
    page.locator("#play-trace").click()
    page.locator("#playhead").filter(has_text=re.compile(r"tick [1-9]")).wait_for(timeout=5000)
    page.locator("#play-trace").click()
    page.select_option("#district", "mandala")
    page.select_option("#court", "b")
    page.select_option("#door", "b-pyramid_n")
    assert (
        "6 of 9" in page.locator("#pockets").inner_text()
        and "0 of 9" in page.locator("#pockets").inner_text()
    )
    assert not failures, failures
    result = dict(
        viewport=[width, height],
        entrances_walked=c,
        reverse_observers=reverse,
        recorded_plays_inspected=len(traces),
        page_errors=failures,
        horizontal_overflow=False,
    )
    page.close()
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url")
    p.add_argument("--screenshots", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium")
            or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        data = {
            "browser": "Chromium " + browser.version,
            "viewports": [
                check(browser, args.url, *size, args.screenshots)
                for size in ((1440, 960), (390, 844))
            ],
        }
        browser.close()
    text = json.dumps(data, indent=2) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
