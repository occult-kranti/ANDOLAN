"""Exercise and compare the real offline viewer, including a complete WebGL model load."""

import argparse
from io import BytesIO
import json
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


def changed_fraction(original, variant):
    before, after = (
        Image.open(BytesIO(data)).convert("RGB") for data in (original, variant)
    )
    diff = ImageChops.difference(before, after)
    red, green, blue = diff.split()
    strongest = ImageChops.lighter(red, ImageChops.lighter(green, blue))
    return sum(strongest.histogram()[12:]) / (diff.width * diff.height)


def check(url, browser):
    page = browser.new_page(
        viewport={"width": 800, "height": 650}, device_scale_factor=1
    )
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(url, wait_until="networkidle")
    checked = []
    for name in ("overview", "site-a", "site-b"):
        page.select_option("#view", name)
        for finish in ("baseline", "jade"):
            page.locator(f'[data-finish="{finish}"]').click()
            page.wait_for_function(
                '(args) => {const i=document.querySelector("#still");return i.complete && i.naturalWidth===1024 && i.src.endsWith(args);}',
                arg=f"/{name}-{finish}.png",
            )
            checked.append(f"{name}-{finish}")
    page.get_by_role("button", name="Inspect in 3D").click()
    page.get_by_role("button", name="Show renders").wait_for(timeout=240000)
    canvas = page.locator("canvas")
    canvas.wait_for()
    status = page.locator("#status").inner_text()
    assert status.startswith("23 ground materials"), status
    page.locator('[data-finish="baseline"]').click()
    original = canvas.screenshot(timeout=90000)
    page.locator('[data-finish="jade"]').click()
    jade = canvas.screenshot(timeout=90000)
    changed = changed_fraction(original, jade)
    assert changed > 0.015, f"Only {changed:.3%} of Site B WebGL pixels changed."
    page.select_option("#view", "overview")
    page.wait_for_function(
        'document.getElementById("still").src.endsWith("/overview-jade.png")'
    )
    page.get_by_role("button", name="Show renders").click()
    assert not canvas.is_visible()
    page.set_viewport_size({"width": 390, "height": 840})
    page.select_option("#view", "site-a")
    page.get_by_role("button", name="Original").click()
    assert page.locator("#mode").is_visible()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    page.close()
    return {
        "stills_loaded": checked,
        "webgl": status,
        "site_b_changed_pixel_fraction": round(changed, 5),
        "mobile_css_width": 390,
        "page_errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with sync_playwright() as api:
        browser = api.chromium.launch(
            executable_path=args.chromium,
            args=[
                "--no-sandbox",
                "--enable-unsafe-swiftshader",
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            report = check(args.url, browser)
        finally:
            browser.close()
    result = json.dumps(report, indent=2) + "\n"
    print(result, end="")
    if args.output:
        args.output.write_text(result)
