"""Exercise the Monsoon Exchange atlas through its visible controls, including actual WebGL."""

import argparse
from hashlib import sha256
from io import BytesIO
import json
import time
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
LANDMARKS = {
    "sun-court": ("a", "Sun Court"),
    "indigo-cistern": ("b", "Indigo Cistern"),
    "weavers-gate": ("mid", "Weavers’ Gate"),
}


def image_metrics(data):
    image = Image.open(BytesIO(data)).convert("RGB")
    sample = image.resize((160, 120))
    return image, len(sample.getcolors(maxcolors=sample.width * sample.height))


def changed(first, second):
    difference = ImageChops.difference(first, second)
    r, g, b = difference.split()
    histogram = ImageChops.lighter(r, ImageChops.lighter(g, b)).histogram()
    return sum(histogram[12:]) / (difference.width * difference.height)


def wait_truth(page, expression, arg=None, timeout=30000):
    # Poll through DevTools without inserting eval into a document protected by the production CSP.
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        value = page.evaluate(expression, arg)
        if value:
            return value
        time.sleep(0.08)
    raise AssertionError(f"Browser condition did not become true: {expression}")


def boot(page, url):
    page.goto(url, wait_until="domcontentloaded")
    wait_truth(page, 'document.querySelectorAll("#plan .map-tag").length === 3')
    page.evaluate("document.fonts.ready")
    wait_truth(page, 'document.querySelector(".cover img").naturalWidth > 600')


def image_ready(page, selector):
    return wait_truth(
        page,
        "s => {const i = document.querySelector(s); return i?.complete && i.naturalWidth > 0 ? [i.naturalWidth,i.naturalHeight] : null;}",
        arg=selector,
    )


def settle_frame(page):
    page.evaluate(
        "new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
    )


def track_errors(page, failures, errors, network_failures):
    page.on(
        "requestfailed",
        lambda request: network_failures.append([request.url, request.failure]),
    )
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "response",
        lambda response: failures.append([response.url, response.status])
        if response.status >= 400
        else None,
    )


def play_film(page):
    page.get_by_role("link", name="Watch the filmed tour").click()
    video = page.locator("video")
    video.wait_for(state="visible")
    wait_truth(page, 'document.querySelector("video").readyState >= 2')
    width, height, duration = video.evaluate(
        "async v => {v.muted=true; await v.play(); return [v.videoWidth,v.videoHeight,v.duration];}"
    )
    assert (width, height, duration) == (1280, 720, 16)
    wait_truth(page, 'document.querySelector("video").currentTime > 0.35')
    return {"width": width, "height": height, "seconds": duration, "played": True}


def verify(browser, url, captures, defer_film=False):
    site = urlparse(url).netloc
    design = json.loads((PROJECT / "plan/survey.json").read_bytes())
    geometry = json.loads((PROJECT / "plan/geometry.json").read_bytes())
    metrics = json.loads((PROJECT / "plan/metrics.json").read_bytes())
    approaches = [
        r
        for r in metrics["routes"]
        if r["rooms"][0] == "atk" and r["rooms"][-1] in ("a", "b")
    ]
    requests, failures, errors, network_failures, models = [], [], [], [], []
    ctx = browser.new_context(
        viewport={"width": 1240, "height": 850},
        reduced_motion="reduce",
        device_scale_factor=1,
    )
    ctx.add_init_script(
        """window.atlasCsp = [];
        document.addEventListener('securitypolicyviolation', e => window.atlasCsp.push([e.effectiveDirective, e.blockedURI]));
        const fetchOriginal = window.fetch;
        window.fetch = async function(...args) {
            const response = await fetchOriginal.apply(this,args);
            if (response.url.endsWith('/monsoon-exchange.glb') && (args[1]?.method || args[0]?.method || 'GET') === 'GET') {
                // Copy the browser's actual model response without a second network request.
                window.atlasGlbDigest = response.clone().arrayBuffer().then(bytes => crypto.subtle.digest('SHA-256', bytes))
                    .then(digest => Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2,'0')).join(''));
            }
            return response;
        };"""
    )
    page = ctx.new_page()
    page.on("request", lambda request: requests.append(request.url))
    page.on(
        "response",
        lambda response: models.append(response)
        if response.url.endswith("/monsoon-exchange.glb")
        and response.request.method == "GET"
        else None,
    )
    track_errors(page, failures, errors, network_failures)
    boot(page, url)
    assert page.title() == "Monsoon Exchange · YUGA map atlas"
    faces = page.evaluate(
        "Object.fromEntries(Array.from(document.fonts, f=>[f.family,f.status]))"
    )
    faces = {family.strip('"'): state for family, state in faces.items()}
    assert (
        faces.get("Atlas Barlow") == "loaded" and faces.get("Atlas DM") == "loaded"
    ), faces
    assert page.locator("#plan polygon").count() == len(geometry["floors"])
    assert page.locator("#plan .boundary line").count() == len(geometry["walls"])
    assert page.locator("#map-routes polyline").count() == len(design["links"])
    assert page.locator("#map-covers rect").count() == len(design["covers"])
    assert (
        page.locator("#place-facts").inner_text().find(str(len(design["rooms"]))) >= 0
    )
    assert not any(
        u.endswith(
            ("/three.bundle.mjs", "/orbit.js", "/monsoon-exchange.glb", "/metrics.json")
        )
        for u in requests
    )
    default_box = page.locator("#plan").get_attribute("viewBox")
    page.get_by_role("button", name="Inspect Sun Court").focus()
    page.keyboard.press("Enter")
    assert page.locator("#location").input_value() == "sun-court"
    assert page.locator("#plan").get_attribute("viewBox") != default_box
    assert page.locator("#place-name").inner_text() == "Sun Court"
    for key, (room, title) in LANDMARKS.items():
        page.select_option("#location", key)
        surveyed = next(r for r in design["rooms"] if r["id"] == room)
        x, y, width, height = map(
            float, page.locator("#plan").get_attribute("viewBox").split()
        )
        assert abs(x + width / 2 - surveyed["center"][0]) < 0.001
        assert abs(y + height / 2 + surveyed["center"][1]) < 0.001
        assert (
            page.get_by_role("button", name="Inspect " + title).get_attribute(
                "aria-pressed"
            )
            == "true"
        )
    page.locator("#cover-layer").uncheck()
    assert page.locator("#map-covers").get_attribute("visibility") == "hidden"
    page.locator("#route-layer").uncheck()
    assert page.locator("#map-routes").get_attribute("visibility") == "hidden"
    page.locator("#cover-layer").check()
    page.locator("#route-layer").check()
    page.select_option("#location", "overview")
    assert page.locator("#plan").get_attribute("viewBox") == default_box
    if captures:
        captures.mkdir(parents=True, exist_ok=True)
        page.evaluate("scrollTo(0,0)")
        page.screenshot(path=captures / "desktop.png")
        page.locator("#atlas").screenshot(path=captures / "survey.png")
    pictures = {"district_concept": image_ready(page, ".cover img")}
    for key in LANDMARKS:
        page.locator(f'[data-shot="{key}"]').click()
        assert page.locator("#location").input_value() == key
        assert (
            page.locator('[data-mode="still"]').get_attribute("aria-pressed") == "true"
        )
        wait_truth(
            page,
            'key => document.querySelector("#still").currentSrc.endsWith("/" + key + ".webp")',
            arg=key,
        )
        pictures[key] = image_ready(page, "#still")
    page.locator("#drawings").scroll_into_view_if_needed()
    pictures["painted_plan"] = image_ready(page, "#drawings figure:first-child img")
    pictures["blender_roof_plan"] = image_ready(
        page, "#drawings figure:nth-child(2) img"
    )
    pictures["technical_drawing"] = image_ready(page, "#drawings figure:last-child img")
    # Use the renderer itself and compare the read-back images after real camera input.
    page.select_option("#location", "overview")
    page.get_by_role("button", name="Orbit in 3D").click()
    canvas = page.locator("#orbit-surface canvas")
    canvas.wait_for(state="visible", timeout=120000)
    wait_truth(
        page,
        'document.querySelector("#orbit-surface canvas").dataset.landmark === "overview"',
        timeout=120000,
    )
    canvas.focus()
    page.keyboard.press("Home")
    settle_frame(page)
    first, distinct = image_metrics(canvas.screenshot(timeout=120000))
    assert distinct > 100, "The full model should produce shaded, distinct pixels"
    page.keyboard.press("ArrowRight")
    settle_frame(page)
    moved, _ = image_metrics(canvas.screenshot(timeout=120000))
    orbit_change = changed(first, moved)
    assert orbit_change > 0.008, orbit_change
    page.keyboard.press("Home")
    settle_frame(page)
    reset, _ = image_metrics(canvas.screenshot(timeout=120000))
    reset_change = changed(first, reset)
    assert reset_change < 0.04, reset_change
    if captures:
        first.save(captures / "orbit.png")
    for key in LANDMARKS:
        page.select_option("#location", key)
        assert canvas.get_attribute("data-landmark") == key
    settle_frame(page)
    detail, detail_colors = image_metrics(canvas.screenshot(timeout=120000))
    assert detail_colors > 55 and changed(first, detail) > 0.025
    for action in ("Turn", "Zoom in", "Zoom out", "Reset view"):
        page.get_by_role("button", name=action, exact=True).click()
    assert not any(u.endswith("/metrics.json") for u in requests)
    page.get_by_role("button", name="Walk a route").click()
    page.locator("#walk-panel").wait_for(state="visible")
    option_ids = page.locator("#walk-route option").evaluate_all(
        "opts => opts.map(o=>o.value)"
    )
    assert option_ids == [r["id"] for r in approaches]
    walk_pictures = {}
    for r in approaches:
        page.select_option("#walk-route", r["id"])
        assert canvas.get_attribute("data-route") == r["id"]
        assert (
            abs(float(page.locator("#walk-time").get_attribute("max")) - r["walk_s"])
            < 0.001
        )
        assert float(page.locator("#walk-time").input_value()) == 0
        page.get_by_role("button", name="Advance 5 m").click()
        assert page.locator("#walk-readout").inner_text().startswith("5 /")
        # The keyed range moves continuously by segment length and reaches the measured destination.
        progress = page.locator("#walk-time")
        progress.focus()
        page.keyboard.press("End")
        settle_frame(page)
        assert page.get_by_role("button", name="Return to start").is_visible()
        endpoint, samples = image_metrics(canvas.screenshot(timeout=120000))
        assert samples > 70
        walk_pictures[r["id"]] = {
            "metres": r["length_3d_m"],
            "seconds": r["walk_s"],
            "end_sampled_colors": samples,
        }
        if captures and r["id"] == "a-long":
            endpoint.save(captures / "walk-sun-court.png")
    page.emulate_media(reduced_motion="no-preference")
    page.locator("#walk-route").select_option("a-long")
    page.get_by_role("button", name="Start walk").click()
    wait_truth(
        page, 'Number(document.querySelector("#walk-time").value) > .4', timeout=30000
    )
    page.get_by_role("button", name="Pause walk").click()
    paused = float(page.locator("#walk-time").input_value())
    settle_frame(page)
    assert paused == float(page.locator("#walk-time").input_value())
    page.get_by_role("button", name="Return to orbit").click()
    assert (
        not page.locator("#walk-panel").is_visible()
        and canvas.get_attribute("data-route") is None
    )
    assert page.get_by_role("button", name="Walk a route").evaluate(
        "b=>document.activeElement===b"
    )
    page.emulate_media(reduced_motion="reduce")
    page.get_by_role("button", name="Floorplan", exact=True).click()
    assert not canvas.is_visible()
    page.get_by_role("button", name="Orbit in 3D").click()
    canvas.wait_for(state="visible")
    assert len([u for u in requests if u.endswith("/monsoon-exchange.glb")]) == 1
    assert len([u for u in requests if u.endswith("/three.bundle.mjs")]) == 1
    assert len(models) == 1
    model_sha = page.evaluate("window.atlasGlbDigest")
    assert (
        model_sha
        == sha256((PROJECT / "scene/monsoon-exchange.glb").read_bytes()).hexdigest()
    )
    assert not [
        u
        for u in requests
        if u.startswith(("http://", "https://")) and urlparse(u).netloc != site
    ]
    file_paths = page.locator("#files [data-asset]").evaluate_all(
        "elements => elements.map(e => ({name:e.dataset.asset,href:e.href}))"
    )
    checked_files = [
        entry
        for entry in file_paths
        if not (defer_film and entry["name"] == "film/district-tour.mp4")
    ]
    for entry in checked_files:
        status = page.evaluate(
            'async url => {const r = await fetch(url, {method:"HEAD"}); await r.arrayBuffer(); return r.status;}',
            entry["href"],
        )
        assert status == 200, (entry, status)
    assert not failures, failures
    assert not network_failures, network_failures
    assert not errors, errors
    csp = page.evaluate("window.atlasCsp")
    assert not csp, csp
    ctx.close()
    phone = browser.new_context(
        viewport={"width": 320, "height": 740},
        is_mobile=True,
        has_touch=True,
        device_scale_factor=1,
        reduced_motion="reduce",
    )
    mobile = phone.new_page()
    track_errors(mobile, failures, errors, network_failures)
    mobile_requests = []
    mobile.on("request", lambda r: mobile_requests.append(r.url))
    boot(mobile, url)
    assert mobile.evaluate("document.documentElement.scrollWidth === innerWidth")
    mobile.locator('[data-mode="still"]').tap()
    mobile.select_option("#location", "indigo-cistern")
    image_ready(mobile, "#still")
    assert mobile.evaluate("document.documentElement.scrollWidth === innerWidth")
    if captures:
        mobile.evaluate("scrollTo(0,0)")
        mobile.screenshot(path=captures / "phone.png")
    assert not any(path.endswith("/monsoon-exchange.glb") for path in mobile_requests)
    mobile.get_by_role("button", name="Orbit in 3D").tap()
    mobile.locator('#orbit-surface canvas[data-landmark="indigo-cistern"]').wait_for(
        state="visible", timeout=120000
    )
    mobile.get_by_role("button", name="Walk a route").tap()
    mobile.get_by_role("button", name="Advance 5 m").tap()
    assert mobile.locator("#walk-readout").inner_text().startswith("5 /")
    assert mobile.evaluate("document.documentElement.scrollWidth === innerWidth")
    if captures:
        mobile.locator(".sheet").screenshot(path=captures / "phone-walk.png")
    mobile.get_by_role("button", name="Return to orbit").tap()
    assert sum(path.endswith("/monsoon-exchange.glb") for path in mobile_requests) == 1
    phone.close()
    limited = browser.new_context(viewport={"width": 850, "height": 680})
    limited.add_init_script(
        """const get=HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind.startsWith('webgl')?null:get.call(this,kind,...args)};"""
    )
    fallback = limited.new_page()
    track_errors(fallback, failures, errors, network_failures)
    boot(fallback, url)
    fallback.get_by_role("button", name="Orbit in 3D").click()
    fallback.get_by_text("3D could not open.", exact=False).wait_for(timeout=60000)
    assert (
        fallback.locator('[data-mode="still"]').get_attribute("aria-pressed") == "true"
    )
    assert (
        fallback.locator("#load-state a")
        .get_attribute("href")
        .endswith("/film/district-tour.mp4")
    )
    image_ready(fallback, "#still")
    fallback.get_by_role("button", name="Floorplan", exact=True).click()
    assert fallback.locator("#plan").is_visible()
    assert not failures, failures
    assert not errors, errors
    assert not network_failures, network_failures
    movie = None if defer_film else play_film(fallback)
    limited.close()
    return {
        "browser": browser.version,
        "local_fonts": faces,
        "geometry": {
            "floor_patches": len(geometry["floors"]),
            "surveyed_wall_runs": len(geometry["walls"]),
            "rooms": len(design["rooms"]),
            "links": len(design["links"]),
            "cover": len(design["covers"]),
        },
        "landmarks": list(LANDMARKS),
        "picture_dimensions": pictures,
        "camera": {
            "overview_sampled_colors": distinct,
            "orbit_changed_fraction": round(orbit_change, 5),
            "reset_changed_fraction": round(reset_change, 5),
            "gate_sampled_colors": detail_colors,
        },
        "single_lazy_glb_request": True,
        "loaded_model_sha256": model_sha,
        "initial_3d_requests": 0,
        "third_party_runtime_requests": 0,
        "projection_consistent_with_metric_centers": True,
        "keyboard_site_pick_and_orbit": True,
        "walks": {
            "approaches": walk_pictures,
            "eye_height_m": design["rules"]["standing_eye_m"],
            "reduced_motion_step_m": 5,
            "real_time_start_pause": True,
            "walks_requested_before_opt_in": 0,
        },
        "phone_css_width": 320,
        "phone_orbit_and_touch_walk": True,
        "fallback": "WebGL context unavailable; Blender views and plan remained accessible",
        "recorded_tour": movie,
        "downloads_checked": [e["name"] for e in checked_files],
        "downloads_deferred": [e["name"] for e in file_paths if e not in checked_files],
        "source_sha256": {
            name: sha256((HERE / name).read_bytes()).hexdigest()
            for name in [
                "index.html",
                "atlas.css",
                "atlas.js",
                "orbit.js",
                "three.bundle.mjs",
            ]
        },
        "http_errors": failures,
        "network_errors": network_failures,
        "page_errors": errors,
        "csp_violations": csp,
    }


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("url")
    args.add_argument("--output", type=Path)
    args.add_argument("--captures", type=Path)
    args.add_argument("--chromium", default="/usr/bin/chromium")
    args.add_argument(
        "--defer-film-head",
        action="store_true",
        help="Exercise the atlas while the separately encoded MP4 is pending. The receipt explicitly records the deferred film request.",
    )
    opt = args.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=opt.chromium,
            args=[
                "--no-sandbox",
                "--enable-unsafe-swiftshader",
                "--use-angle=swiftshader",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            result = verify(browser, opt.url, opt.captures, opt.defer_film_head)
        finally:
            browser.close()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if opt.output:
        opt.output.write_text(text)
    print(text, end="")
