// One real graphical host and nine local WebSocket peers in a packaged 5v5 room.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { WebSocket } from 'ws';
import { launchChromium } from './browser-package.mjs';

const [folder, reportFile, screenshotFile] = process.argv.slice(2);
if (!folder || !reportFile || !screenshotFile) throw Error('Usage: node test_5v5_browser.mjs extracted-dir report.json screenshot.png');
const root = path.resolve(folder);
const host = spawn(process.execPath, [path.join(root, 'serve_rooms.mjs'), '--port', '0'],
  { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
let log = ''; for (const stream of [host.stdout, host.stderr]) stream.on('data', c => { log += c; });
const sockets = [];
async function until(label, fn, timeout = 90000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const result = await fn(); if (result) return result;
    if (host.exitCode !== null) throw Error(label + ': host exited: ' + log.slice(-1000));
    await delay(50);
  }
  throw Error('Timeout waiting for ' + label + ': ' + log.slice(-1000));
}
let browser;
try {
  const port = await until('host start', () => Number(/127\.0\.0\.1:(\d+)/.exec(log)?.[1]));
  const origin = `http://127.0.0.1:${port}`;
  browser = await launchChromium();
  const page = await browser.newPage({ viewport: { width: 1100, height: 720 } });
  const errors = [], external = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    const u = new URL(request.url());
    if (['http:', 'https:'].includes(u.protocol) && u.origin !== origin) external.push(u.origin);
  });
  await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.waitForFunction(() => window.yugaProbe?.().mode === 'ready', null, { timeout: 120000 });
  assert.equal(await page.locator('#room-size').inputValue(), '5');
  await page.locator('.rooms summary').click();
  await page.locator('#create-room').click();
  const code = await until('browser room code', async () => (await page.locator('#room-code').inputValue()) || null);
  for (let i = 1; i < 10; i++) {
    const socket = new WebSocket(`ws://127.0.0.1:${port}/rooms`, { origin });
    sockets.push(socket);
    await new Promise((resolve, reject) => socket.once('open', resolve).once('error', reject));
    socket.send(JSON.stringify({ type: 'join', code, hero: i % 2 ? 'rama' : 'hanuman' }));
  }
  await page.waitForFunction(() => {
    const p = window.yugaProbe?.();
    return p?.mode === 'playing' && p.state?.ruleset === 'hero_skirmish' &&
      p.state?.roster?.length === 9 && p.renderer?.remoteHeroes?.length === 9 && p.renderer?.frames > 3;
  }, null, { timeout: 120000 });
  const before = await page.evaluate(() => window.yugaProbe());
  assert.equal(before.state.army.units.length, 0);
  assert.equal(before.renderer.armyVisible, 0);
  assert.equal(before.state.score.target, 25);
  assert.match(await page.locator('#objective').innerText(), /Sun 0\s*\/\s*Moon 0.*First to 25/);
  await page.keyboard.down('w');
  await until('physical keyboard movement', async () => {
    const p = await page.evaluate(() => window.yugaProbe());
    return Math.hypot(...p.state.actor.pos.map((v, i) => v - before.state.actor.pos[i])) > 0.05;
  });
  await page.keyboard.up('w');
  await page.screenshot({ path: screenshotFile });
  assert.deepEqual(errors, []); assert.deepEqual(external, []);
  const after = await page.evaluate(() => window.yugaProbe());
  const report = { result: 'pass', scope: 'one Chromium client and nine WebSocket peers on a loopback Wasm host',
    browser: browser.version(), remote_heroes: after.renderer.remoteHeroes.length,
    visible_wave_units: after.renderer.armyVisible, target_score: after.state.score.target,
    before_position: before.state.actor.pos, after_position: after.state.actor.pos,
    html_sha256: createHash('sha256').update(await readFile(path.join(root, 'yuga-rust.html'))).digest('hex'),
    errors, external_requests: external };
  await writeFile(reportFile, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  for (const socket of sockets) socket.terminate();
  if (browser) await browser.close();
  host.kill('SIGTERM');
}
