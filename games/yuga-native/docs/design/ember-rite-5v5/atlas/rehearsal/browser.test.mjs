/** Check the exact release artifact through real controls, offline and in the game's opaque frame. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { launchChromium, openOffline } from "../../../../../../yuga-rust/tools/browser-package.mjs";

const artifact = new URL("../rehearsal.html", import.meta.url);
const content = await readFile(artifact, "utf8");
const browser = await launchChromium(false);
const errors = [];
const server = createServer((req, res) => {
  if (req.url.split("?")[0] !== "/drill") { res.writeHead(404).end(); return; }
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }).end(content);
});
async function advance(page, ms) { await page.clock.runFor(ms); }
async function hold(page, key, ms) {
  await page.keyboard.down(key);
  await advance(page, ms);
  await page.keyboard.up(key);
  await advance(page, 80);
}
async function marker(scope) {
  return (await scope.locator("#player").getAttribute("transform")).match(/-?\d+(?:\.\d+)?/g).map(Number);
}
async function select(scope, id, value) {
  await scope.locator("#" + id).selectOption(value);
  await scope.locator("#plan").focus();
}
async function assertSource(scope, expected) {
  assert.equal(await scope.locator("#district-name").textContent(), expected);
  assert.ok((await scope.locator("#marks > *").count()) > 6);
}

try {
  const desktop = await browser.newContext({ viewport: { width: 1280, height: 860 }, offline: true });
  const requests = [], allowed = new Set();
  desktop.on("page", p => p.on("pageerror", e => errors.push(e.message)));
  desktop.on("request", request => requests.push(request.url()));
  await desktop.clock.install({ time: new Date("2030-01-01T00:00:00Z") });
  await desktop.clock.pauseAt(new Date("2030-01-01T00:00:01Z"));
  const {tab: page, entry} = await openOffline(desktop, {html: fileURLToPath(artifact), bytes: Buffer.from(content)}, url => allowed.add(url));
  await page.getByRole("button", { name: "Mandala Rift" }).waitFor();
  await assertSource(page, "Mandala Rift");
  await page.screenshot({ path: join(tmpdir(), "yuga-ember-rite-r3-desktop.png"), fullPage: true });

  const lengthOfWalk = async (origin) => {
    await select(page, "start", origin);
    const [x] = await marker(page);
    await hold(page, "d", 512);
    return (await marker(page))[0] - x;
  };
  const dry = await lengthOfWalk("atk");
  const wet = await lengthOfWalk("ford");
  assert.ok(dry > 2 && Math.abs(wet/dry - .85) < .09, [dry, wet].toString());
  assert.match(await page.locator("#position").textContent(), /Shallows/);
  await select(page, "start", "atk");
  await hold(page, "s", 3100);
  const wall = await marker(page);
  await hold(page, "s", 600);
  assert.deepEqual(await marker(page), wall, "Spawn edge should stop walking");
  await select(page, "start", "b");
  await hold(page, "d", 2800);
  const cabinet = await marker(page);
  assert.ok(cabinet[0] > 44 && cabinet[0] < 46, "Body should stop at the Dye Cabinet");
  await hold(page, "d", 400);
  assert.deepEqual(await marker(page), cabinet);
  for (const [start, mark, turnOut, turnBack] of [
    ["temple_s", "One notch", "Right turn to South Pyramid", "Left turn to South Temple"],
    ["temple_n", "Two bars", "Left turn to North Pyramid", "Right turn to North Temple"]
  ]) {
    await select(page, "start", start);
    await hold(page, "d", 160);
    const entrance = await marker(page);
    assert.match(await page.locator("#interact").textContent(), new RegExp(mark + ".*" + turnOut));
    await hold(page, "e", 950);
    assert.deepEqual(await marker(page), entrance, "Early release cancels the fold");
    await page.keyboard.down("e");
    await advance(page, 1620);
    const exit = await marker(page);
    assert.notDeepEqual(exit, entrance);
    assert.match(await page.locator("#status").textContent(), new RegExp(turnOut));
    await advance(page, 1780);
    assert.deepEqual(await marker(page), exit, "A held key cannot echo through the return gate");
    await page.keyboard.up("e");
    await advance(page, 100);
    assert.match(await page.locator("#interact").textContent(), new RegExp(mark + ".*" + turnBack));
    await hold(page, "e", 1650);
    assert.deepEqual(await marker(page), entrance, "Reverse fold restores position and facing");
    assert.match(await page.locator("#status").textContent(), new RegExp(turnBack));
  }
  await select(page, "mode", "carry");
  await select(page, "start", "a");
  await page.keyboard.press("g");
  await advance(page, 120);
  assert.match(await page.locator("#status").textContent(), /dropped/);
  await hold(page, "e", 120);
  assert.match(await page.locator("#status").textContent(), /recovered/);
  await hold(page, "d", 400);
  const [plantX, plantY] = await marker(page);
  assert.ok(plantX > 1.5 && plantX < 3, "Plant offset must exceed centre interaction reach");
  await hold(page, "e", 4100);
  assert.equal(await page.locator("#handoff").isVisible(), true);
  const placed = await page.locator("#vessel").getAttribute("transform");
  assert.equal(placed, "translate(" + plantX + " " + plantY + ")");
  await page.locator("#handoff").click();
  assert.equal(await page.locator("#mode").inputValue(), "retake");
  assert.equal(await page.locator("#start").inputValue(), "b");
  assert.equal(await page.locator("#vessel").getAttribute("transform"), placed);
  assert.match(await page.locator("#clock").textContent(), /0:40/);

  await select(page, "start", "a");
  assert.equal(await page.locator("#interact").textContent(), "Interact", "Centre alone is out of reach");
  await hold(page, "w", 300);
  assert.match(await page.locator("#interact").textContent(), /Quench/);
  await page.keyboard.down("e");
  await advance(page, 850);
  assert.ok(Number(await page.locator("#progress").getAttribute("value")) > .1);
  await page.locator("#interrupt").click();
  await advance(page, 250);
  assert.match(await page.locator("#status").textContent(), /Interrupted/);
  assert.equal(Number(await page.locator("#progress").getAttribute("value")), 0);
  await page.keyboard.up("e");
  await advance(page, 130);
  await hold(page, "e", 3600);
  assert.match(await page.locator("#status").textContent(), /Quenched/);
  assert.equal(await page.locator("#time-title").textContent(), "Fire clock");

  await select(page, "mode", "explore");
  await page.keyboard.down("w");
  await advance(page, 300);
  await page.getByRole("button", { name: "Lanka", exact: true }).click();
  const newSpawn = await marker(page);
  await advance(page, 620);
  assert.deepEqual(await marker(page), newSpawn, "Switching districts clears held input");
  await page.keyboard.up("w");
  for (const title of ["Lanka", "Ayodhya", "Kurukshetra"]) {
    await page.getByRole("button", { name: title, exact: true }).click();
    await assertSource(page, title);
    await select(page, "start", "def");
    await select(page, "goal", "b");
    assert.match(await page.locator("#estimate").textContent(), /route estimate/);
  }
  assert.match(await page.locator("#start").textContent(), /Flood Bench/);
  await page.locator("#zoom").click();
  assert.equal(await page.locator("#zoom").getAttribute("aria-pressed"), "true");
  await page.keyboard.press("p");
  assert.equal(await page.locator("#pause").textContent(), "Resume");
  await page.keyboard.press("p");
  assert.equal(await page.locator("#pause").textContent(), "Pause");
  const districtData = await page.locator("#atlas-data").evaluate(el => JSON.parse(el.textContent).maps);
  for (const district of districtData) {
    await page.getByRole("button", {name: district.title, exact: true}).click();
    const study = district.architecture, node = district.nodes[study.node].xz;
    assert.equal(await page.locator("[data-masonry]").count(), district.building.solids.length);
    const angle = study.axis_deg * Math.PI / 180, c = Math.cos(angle), s = Math.sin(angle);
    const metres = ([x,z]) => [(x-node[0])*c - (z-node[1])*s, (x-node[0])*s + (z-node[1])*c];
    for (const side of [-1, 1]) {
      await select(page, "start", study.node);
      const banks = district.building.solids.map(piece => piece.ring.map(metres))
        .filter(p => p.every(([x]) => x*side > 0) && Math.max(...p.map(v=>v[1])) - Math.min(...p.map(v=>v[1])) > .45)
        .sort((a,b) => Math.min(...a.map(v=>Math.abs(v[0]))) - Math.min(...b.map(v=>Math.abs(v[0]))));
      const bank = banks[0], y = bank.reduce((total,v) => total+v[1], 0) / bank.length;
      if (Math.abs(y) > .1) {
        const axialKey = study.axis_deg === 90 ? (y>0 ? "d" : "a") : (y>0 ? "w" : "s");
        await hold(page, axialKey, Math.round(Math.abs(y)/5*1000));
      }
      const toward = study.axis_deg === 90 ? (side>0 ? "s" : "w") : (side>0 ? "d" : "a");
      await hold(page, toward, 1700);
      const contact = await marker(page);
      const [reached] = metres([contact[0], -contact[1]]);
      const gap = Math.min(...bank.map(v=>Math.abs(v[0]))) - Math.abs(reached);
      assert.ok(gap >= .445 && gap <= .72, study.name + " did not stop at its visible masonry, gap " + gap);
      await hold(page, toward, 300);
      assert.deepEqual(await marker(page), contact);
    }
    if (district.id === "ayodhya") {
      await select(page, "start", study.node);
      await page.screenshot({path: join(tmpdir(), "yuga-ember-rite-r3-measure-well.png"), fullPage: true});
    }
  }
  assert.deepEqual(requests.filter(url => /^(https?|wss?):/i.test(url) && !allowed.has(url)), [], "Local file requested the network");
  console.log("Desktop entry: " + (entry === "file" ? "file" : "loopback then offline; managed Chromium blocked file navigation"));
  await desktop.close();

  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = "http://127.0.0.1:" + server.address().port + "/drill";
  const mobile = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });
  const small = await mobile.newPage();
  small.on("pageerror", e => errors.push(e.message));
  await small.goto(address + "?map=ayodhya&exercise=retake&site=b");
  await mobile.setOffline(true);
  await small.getByRole("button", { name: "Ayodhya", exact: true }).waitFor();
  await assertSource(small, "Ayodhya");
  assert.equal(await small.locator("#goal").inputValue(), "b");
  assert.ok(await small.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), "Mobile layout overflows");
  const visibleSiteNames = await small.locator("#plan").evaluate(svg => {
    const frame = svg.getBoundingClientRect();
    return [...svg.querySelectorAll('[data-room="a"], [data-room="b"]')].every(label => {
      const box = label.getBoundingClientRect();
      return box.left >= frame.left && box.right <= frame.right;
    });
  });
  assert.ok(visibleSiteNames, "Both mobile site captions must fit on the plan");
  await small.screenshot({ path: join(tmpdir(), "yuga-ember-rite-r3-mobile.png"), fullPage: true });
  const mobileStart = await marker(small);
  await small.getByRole("button", { name: "Move north", exact: true }).tap();
  assert.ok((await marker(small))[1] < mobileStart[1], "A short touch should move the marker north");
  await mobile.close();

  const embedded = await browser.newContext();
  const served = await embedded.newPage();
  served.on("pageerror", e => errors.push(e.stack));
  await served.goto(address);
  await assertSource(served, "Mandala Rift");
  await served.close();
  const host = await embedded.newPage();
  host.on("pageerror", e => errors.push(e.stack));
  await host.setContent('<iframe id="sheet" sandbox="allow-scripts" title="Atlas rehearsal"></iframe>');
  await host.locator("#sheet").evaluate((frame, html) => { frame.srcdoc = html; }, content);
  const frame = host.frameLocator("#sheet");
  await frame.getByRole("button", { name: "Kurukshetra", exact: true }).click();
  await assertSource(frame, "Kurukshetra");
  assert.equal(await frame.locator("#start").evaluate(() => window.origin), "null", "Frame must have an opaque origin");
  const frameStart = await marker(frame);
  await frame.getByRole("button", { name: "Move east", exact: true }).click();
  assert.ok((await marker(frame))[0] > frameStart[0]);
  await embedded.close();
  assert.deepEqual(errors, [], "Uncaught browser error");
  console.log("Chromium passed offline keyboard, touch, served and opaque-frame rehearsal checks.");
} finally {
  await browser.close();
  if (server.listening) await new Promise(resolve => server.close(resolve));
}
