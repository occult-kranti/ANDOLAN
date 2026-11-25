// Run from this checkout with Playwright Chromium and unzip available.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const archive = fileURLToPath(new URL('../../../../yuga-rust/downloads/yuga-rust-confluence.zip', import.meta.url));
const output = process.argv[2] || fileURLToPath(new URL('./standalone-file.json', import.meta.url));
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const extract = (name) => execFileSync('unzip', ['-p', archive, name], { maxBuffer: 128 * 1024 * 1024 });
const folder = await mkdtemp(path.join(os.tmpdir(), 'yuga-solo-file-'));
let browser;
try {
  assert.deepEqual(await readdir(folder), []);
  const filename = 'yuga-rust.html';
  const filepath = path.join(folder, filename);
  await writeFile(filepath, extract(filename));
  const html = await readFile(filepath);
  assert.equal(sha(html), JSON.parse(extract('build.json')).html_sha256);
  assert.deepEqual(await readdir(folder), [filename]);
  const url = pathToFileURL(filepath).href;
  // Use Playwright's stock Chromium. There is no local server, relaxed file-access policy or security override.
  browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const context = await browser.newContext({ offline: true, serviceWorkers: 'block', viewport: { width: 1000, height: 660 } });
  const external = [], fileRequests = [], errors = [];
  const protocols = {};
  context.on('request', req => {
    const scheme = new URL(req.url()).protocol;
    protocols[scheme] = (protocols[scheme] || 0) + 1;
    if (scheme === 'file:') fileRequests.push(req.url());
  });
  await context.route(/^https?:/i, route => {
    external.push(route.request().url());
    return route.abort('internetdisconnected');
  });
  await context.routeWebSocket(/.*/, socket => {
    external.push(socket.url());
    socket.close({ code: 1000, reason: 'Offline certification' });
  });
  const tab = await context.newPage();
  tab.on('pageerror', error => errors.push(error.message));
  await tab.goto(url, { waitUntil: 'domcontentloaded', timeout: 120_000 });
  await tab.waitForFunction(() => window.yugaProbe?.().mode === 'ready', undefined, { timeout: 120_000 });
  assert.equal(tab.url(), url);
  assert.equal(await tab.evaluate(() => navigator.onLine), false);
  assert.equal(await tab.locator('#create-room').isDisabled(), true);
  await tab.locator('#hero').selectOption('hanuman');
  await tab.locator('#begin').click();
  await tab.waitForFunction(() => window.yugaProbe().mode === 'playing' && window.yugaProbe().renderer.frames > 0);
  const read = () => tab.evaluate(() => window.yugaProbe());
  const start = await read();
  assert.equal(start.playMode, 'drill');
  assert.equal(start.renderer.heroId, 'hanuman');
  assert.equal(start.renderer.heroSkinnedSurfaces, 18);
  await tab.keyboard.down('w');
  try {
    await tab.waitForFunction(([x, z]) => {
      const [px, pz] = window.yugaProbe().state.actor.pos;
      return Math.hypot(px - x, pz - z) >= 0.65;
    }, start.state.actor.pos);
  } finally {
    await tab.keyboard.up('w');
  }
  const moved = await read();
  await tab.keyboard.press('q');
  await tab.waitForFunction(() => {
    const s = window.yugaProbe().state;
    return s.events.some(e => e.id === 'vajra_kavacha' && e.kind === 'impact' && e.receipts.some(r => r.shield_after > 0));
  }, undefined, { timeout: 60_000 });
  const after = await read();
  const events = after.state.events.filter(e => e.id === 'vajra_kavacha');
  const event = kind => events.find(e => e.kind === kind);
  assert.equal(event('release').tick - event('begin').tick, 7);
  assert.deepEqual(external, []);
  assert.deepEqual(errors, []);
  assert.deepEqual(fileRequests, [url]);
  assert.deepEqual(await readdir(folder), [filename]);
  const report = {
    browser: await browser.version(), entry: 'file://', html_bytes: html.length, html_sha256: sha(html),
    archive_sha256: sha(await readFile(archive)), only_file_in_folder: filename,
    browser_online: false, external_requests: external, uncaught_errors: errors, request_schemes: protocols,
    mode: start.playMode, hero: start.renderer.heroId, rig_joints: start.renderer.heroBones,
    skinned_surfaces: start.renderer.heroSkinnedSurfaces, input: ['select Hanuman', 'click Hanuman practice', 'hold W', 'press Q'],
    origin: start.state.actor.pos, moved_to: moved.state.actor.pos, cast: event('begin').id,
    begin_tick: event('begin').tick, release_tick: event('release').tick, impact_tick: event('impact').tick,
    shield_receipts: event('impact').receipts, private_room_button_disabled: true,
  };
  await writeFile(output, JSON.stringify(report, null, 2) + '\n');
  console.log(report.html_sha256, report.browser, report.cast);
} finally {
  await browser?.close();
  await rm(folder, { recursive: true, force: true });
}
