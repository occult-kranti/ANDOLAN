// Exercise Vanara Sena between two independently rendered Chromium clients.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import { launchChromium } from './browser-package.mjs';

const [folder, reportFile, screenshotFile] = process.argv.slice(2);
if (!folder || !reportFile || !screenshotFile)
  throw Error('Usage: node test_vanara_two_browsers.mjs extracted-dir report.json screenshot.png');
const root = path.resolve(folder);
const host = spawn(process.execPath, [path.join(root, 'serve_rooms.mjs'), '--port', '0'],
  { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
let hostOutput = '';
for (const stream of [host.stdout, host.stderr]) stream.on('data', c => { hostOutput += c; });
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const errors = [], unexpected = [], sockets = [];
const observerWire = [];
const evidence = {
  result: 'running', scope: 'two independently rendered Chromium/SwiftShader clients on loopback Wasm host; no WAN or physical GPU',
  checks: [], page_errors: errors, unexpected_requests: unexpected,
};
const check = (test, label) => { assert.ok(test, label); evidence.checks.push(label); };
async function until(label, fn, timeout = 90000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const result = await fn(); if (result) return result;
    if (host.exitCode !== null || host.signalCode !== null)
      throw Error(label + ': host exited: ' + hostOutput.slice(-1000));
    await delay(40);
  }
  throw Error('Timeout waiting for ' + label + ': ' + hostOutput.slice(-1000));
}
const read = page => page.evaluate(() => window.yugaProbe?.() ?? { mode: 'loading' });
const distance = (a,b) => Math.hypot(a[0]-b[0], a[1]-b[1]);
let browser;
try {
  await Promise.all([mkdir(path.dirname(path.resolve(reportFile)), {recursive:true}), mkdir(path.dirname(path.resolve(screenshotFile)), {recursive:true})]);
  const port = await until('host start', () => Number(/127\.0\.0\.1:(\d+)/.exec(hostOutput)?.[1]));
  const origin = `http://127.0.0.1:${port}`;
  const documentUrl = `${origin}/yuga-rust.html`;
  const [html, wasm, testSource] = await Promise.all([
    readFile(path.join(root,'yuga-rust.html')), readFile(path.join(root,'yuga-rust.wasm')), readFile(fileURLToPath(import.meta.url))
  ]);
  const response = await fetch(documentUrl);
  assert.ok(response.ok && Buffer.from(await response.arrayBuffer()).equals(html), 'host serves the exact extracted HTML');
  Object.assign(evidence, {html_sha256:sha(html), wasm_sha256:sha(wasm), test_sha256:sha(testSource)});
  browser = await launchChromium();
  evidence.browser = browser.version();
  evidence.viewport = {width:760,height:480};
  async function client(hero) {
    const context = await browser.newContext({viewport:evidence.viewport});
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(hero + ': ' + e.message));
    page.on('request', req => {
      const u = new URL(req.url());
      if (['http:', 'https:'].includes(u.protocol) && (u.origin !== origin || u.pathname !== '/yuga-rust.html'))
        unexpected.push(u.origin + u.pathname);
    });
    page.on('websocket', socket => {
      const u = new URL(socket.url());
      if (u.host === `127.0.0.1:${port}` && u.pathname === '/rooms') {
        sockets.push(hero);
        if (hero === 'rama') socket.on('framereceived', ({payload}) => {
          try {
            const packet = JSON.parse(typeof payload === 'string' ? payload : payload.toString());
            const cast = packet.state?.opponent?.casts?.find(c => c.id === 'vanara_sena');
            if (cast && observerWire.length < 80) observerWire.push({tick:packet.state.tick, age:cast.age_ticks,
              release:cast.release_tick, end:cast.end_tick, target:cast.target, hp:packet.state.actor.hp});
          } catch { /* Non-JSON frames are not match snapshots. */ }
        });
      }
      else unexpected.push(u.origin + u.pathname);
    });
    await page.goto(documentUrl, {waitUntil:'domcontentloaded', timeout:120000});
    await page.waitForFunction(() => window.yugaProbe?.().mode === 'ready', null, {timeout:120000});
    await page.locator('#hero').selectOption(hero);
    await page.locator('.rooms summary').click();
    return {context,page};
  }
  const sun = await client('hanuman');
  const moon = await client('rama');
  await sun.page.locator('#room-size').selectOption('1');
  await sun.page.locator('#create-room').click();
  const code = await until('room code', async () => (await sun.page.locator('#room-code').inputValue()) || null);
  await moon.page.locator('#room-code').fill(code);
  await moon.page.locator('#join-room').click();
  await Promise.all([sun.page,moon.page].map(page => page.waitForFunction(() => {
    const p = window.yugaProbe?.();
    return p?.mode === 'playing' && p.state?.ruleset === 'hero_skirmish' && p.renderer?.frames > 3 && p.renderer?.remoteHeroes?.length === 1;
  }, null, {timeout:120000})));
  let first = await read(sun.page), observerStart = await read(moon.page);
  check(first.state.hero === 'hanuman' && observerStart.state.hero === 'rama', 'both selected heroes load in rendered clients');
  check(first.state.army.units.length === 0 && observerStart.state.army.units.length === 0, 'room has no wave units');
  check(first.state.abilities[5].id === 'vanara_sena' && observerStart.state.abilities.length === 5, 'Vanara Sena is Hanuman-only');
  const startingDistance = distance(first.state.actor.pos, first.state.opponent.actor.pos);
  await sun.page.keyboard.down('w');
  try {
    await sun.page.waitForFunction(() => {
      const p = window.yugaProbe?.(), a = p?.state?.actor?.pos, b = p?.state?.opponent?.actor?.pos;
      return a && b && Math.hypot(a[0]-b[0], a[1]-b[1]) < 9;
    }, null, {timeout:120000});
  } finally { await sun.page.keyboard.up('w'); }
  const movementStop = await read(sun.page);
  await sun.page.waitForFunction(tick => window.yugaProbe?.().state?.army?.tick >= tick + 8,
    movementStop.state.army.tick, {timeout:30000});
  first = await read(sun.page);
  const movedDistance = distance(first.state.actor.pos, first.state.opponent.actor.pos);
  check(movedDistance < 10 && movedDistance < startingDistance - 1, 'actual W input moves Hanuman into cast range');
  const targetScreen = first.renderer.targetScreens.find(t => t.kind === 'hero' && t.team === 'moon' && t.inView);
  assert.ok(targetScreen, 'opponent ground point must be visible from Hanuman camera');
  await sun.page.mouse.move(targetScreen.x, targetScreen.y);
  await sun.page.waitForFunction(() => {
    const p = window.yugaProbe?.(), a = p?.input?.ground, b = p?.state?.opponent?.actor?.pos;
    return a && b && Math.hypot(a[0]-b[0], a[1]-b[1]) < 1.5;
  }, null, {timeout:30000});
  const aimed = await read(sun.page);
  const target = aimed.input.ground;
  const enemyAtAim = aimed.state.opponent.actor.pos.slice();
  const observerHp = (await read(moon.page)).state.actor.hp;
  const lastSeq = aimed.state.events.at(-1)?.seq ?? 0;
  await moon.page.evaluate(() => {
    const trace = {samples:0, maxSpirits:0, remoteCastSamples:0, modes:{}, casts:[], last:null};
    window.__vanaraObserverTrace = trace;
    const sample = () => {
      const p = window.yugaProbe?.(); if (!p) return;
      trace.samples++;
      trace.modes[p.mode] = (trace.modes[p.mode] ?? 0) + 1;
      const remote = p.renderer?.remoteHeroes?.find(r => r.hero === 'hanuman');
      const cast = p.state?.opponent?.casts?.find(c => c.id === 'vanara_sena');
      if (cast) {
        trace.remoteCastSamples++;
        if (trace.casts.length < 40) trace.casts.push({tick:p.state.tick, age:cast.age_ticks, mode:p.mode,
          visibility:document.visibilityState, focused:document.hasFocus(),
          renderedFrames:p.renderer?.frames, spirits:remote?.senaSpirits ?? 0, renderCasts:remote?.casts ?? []});
      }
      trace.maxSpirits = Math.max(trace.maxSpirits, remote?.senaSpirits ?? 0);
      trace.last = {mode:p.mode,visibility:document.visibilityState,focused:document.hasFocus(),tick:p.state?.tick,frames:p.renderer?.frames,hp:p.state?.actor?.hp,
        remoteHero:remote?.hero,spirits:remote?.senaSpirits ?? 0,renderCasts:remote?.casts ?? []};
    };
    sample(); trace.timer = setInterval(sample,50);
  });
  const spiritReady = moon.page.waitForFunction(() => {
    const p = window.yugaProbe?.();
    return p?.mode === 'playing' && p.renderer?.remoteHeroes?.some(r => r.hero === 'hanuman' && r.senaSpirits === 5);
  }, null, {timeout:25000}).then(() => null, error => error);
  await sun.page.keyboard.press('v');
  const begin = await until('accepted V cast', async () => {
    const p = await read(sun.page);
    return p.state?.events?.find(e => e.seq > lastSeq && e.id === 'vanara_sena' && e.kind === 'begin');
  });
  const observerAtCast = await read(moon.page);
  const enemyAtCast = observerAtCast.state.actor.pos.slice();
  // The pointer is sampled again when V is pressed; allow a 0.5 m difference
  // for real camera interpolation, and require the enemy to be within the 3 m field.
  const aimDrift = distance(begin.target, target);
  evidence.aim = {sampled_ground:target, accepted_ground:begin.target, enemy_at_aim:enemyAtAim,
    enemy_at_cast:enemyAtCast, drift_m:aimDrift, defender_distance_m:distance(begin.target,enemyAtCast)};
  check(aimDrift < 0.5 && distance(begin.target, enemyAtCast) < 3, 'authority accepted a mouse target within the enemy field');
  const spiritError = await spiritReady;
  evidence.observer_trace = await moon.page.evaluate(() => {
    const trace = window.__vanaraObserverTrace;
    clearInterval(trace.timer); delete trace.timer; return trace;
  });
  evidence.observer_wire = observerWire;
  if (spiritError) throw spiritError;
  const rendered = await read(moon.page);
  const remoteHero = rendered.renderer.remoteHeroes.find(r => r.hero === 'hanuman');
  check(remoteHero?.senaSpirits === 5 && remoteHero.casts.includes('vanara_sena'), 'opponent renders five remote spectral cues from replicated cast');
  await moon.page.screenshot({path:screenshotFile, timeout:90000});
  const afterShot = await read(moon.page);
  const shotRemote = afterShot.renderer.remoteHeroes.find(r => r.hero === 'hanuman');
  const damageEvent = await until('authoritative impact receipt', async () => {
    const p = await read(sun.page);
    return p.state?.events?.find(e => e.cast_id === begin.cast_id && e.id === 'vanara_sena' && e.kind === 'impact' &&
      e.receipts?.some(r => r.damage > 0));
  });
  const damaged = await until('opponent health decreases', async () => {
    const p = await read(moon.page);
    return p.state?.actor?.hp < observerHp ? p.state.actor.hp : null;
  });
  check(damaged < observerHp, 'observer receives actual authoritative damage');
  check(sockets.length === 2, 'each client used one room WebSocket');
  check(errors.length === 0, 'no uncaught page errors');
  check(unexpected.length === 0, 'no unexpected external requests');
  Object.assign(evidence, {
    result:'pass', movement:{start_distance:startingDistance, cast_distance:movedDistance},
    cast:{id:begin.id, cast_id:begin.cast_id, target:begin.target, tick:begin.tick},
    observer:{hero:'rama', max_visible_spirits:remoteHero.senaSpirits,
      visible_after_screenshot:shotRemote?.senaSpirits ?? 0, hp_before:observerHp, hp_after:damaged},
    impact_receipts:damageEvent.receipts, screenshot_sha256:sha(await readFile(screenshotFile)),
    sockets,
  });
  await sun.context.close(); await moon.context.close();
  console.log(JSON.stringify(evidence,null,2));
} catch (error) {
  evidence.result = 'fail'; evidence.failure = String(error);
  console.error(error); process.exitCode = 1;
} finally {
  await writeFile(reportFile,JSON.stringify(evidence,null,2)+'\n');
  if (browser) await browser.close();
  host.kill('SIGTERM');
}
