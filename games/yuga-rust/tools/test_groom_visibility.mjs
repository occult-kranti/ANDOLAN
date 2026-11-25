import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { Mat4, Vec3 } from 'playcanvas';
import { digest, launchChromium } from './browser-package.mjs';

const { values } = parseArgs({ options: { zip: { type: 'string' }, output: { type: 'string' } } });
const zip = values.zip || fileURLToPath(new URL('../downloads/yuga-rust-confluence.zip', import.meta.url));
const member = name => execFileSync('unzip', ['-p', zip, name], {maxBuffer: 128 * 1024 * 1024});
const html = member('yuga-rust.html');
const wasm = member('yuga-rust.wasm');
const { instance } = await WebAssembly.instantiate(wasm, {});
const authority = instance.exports;
assert.equal(authority.duel_start(0, 0), 1);
function snapshot() {
  const start = authority.duel_snapshot(0);
  return JSON.parse(Buffer.from(authority.memory.buffer, start, authority.duel_snapshot_len()));
}

// All world poses come from actual match movement in the shipped Rust binary.
const shots = [];
for (const [direction, ticks, band, visible] of [
  [-1, 24, 'near', true], [1, 20, 'middle-out', true], [1, 32, 'far', false],
  [-1, 32, 'middle-in', false], [-1, 20, 'near-again', true],
]) {
  for (let i = 0; i < ticks; i++) authority.duel_step(0, 0, 0, 1, 0, direction, 0, -1);
  shots.push({ band, visible, state: snapshot() });
}

// Independent view-matrix projection of the 2.1 m standing rig, in CSS pixels.
function projectedHeight(local, remote, height) {
  const [x, z] = local, [rx, rz] = remote;
  const view = new Mat4().setLookAt(new Vec3(x + 1.35, 4.4, z - 8.4),
    new Vec3(x + .15, .85, z + .2), Vec3.UP).invert();
  const focalPixels = height / (2 * Math.tan(48 * Math.PI / 360));
  function screenY(y) {
    const p = view.transformPoint(new Vec3(rx, y, rz));
    return p.y * focalPixels / -p.z;
  }
  return Math.abs(screenY(2.1) - screenY(0));
}

const browser = await launchChromium();
let page;
try {
  page = await browser.newPage({ viewport: { width: 760, height: 480 }, deviceScaleFactor: 1 });
  page.on('pageerror', error => console.error('Game error', error));
  const url = 'http://127.0.0.1:8791/yuga-rust.html';
  await page.route(url, route => route.fulfill({ contentType: 'text/html; charset=utf-8', body: html }));
  let room;
  await page.routeWebSocket('**/rooms', socket => {
    socket.onMessage(text => {
      if (JSON.parse(text).type === 'create') {
        room = socket;
        socket.send(JSON.stringify({type:'lobby', code:'GROOM', count:2, capacity:2, seat:0}));
        socket.send(JSON.stringify({type:'state', state:shots[0].state, accepted:null}));
      }
    });
  });
  await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 120_000});
  await page.waitForFunction(() => window.yugaProbe?.().mode === 'ready', undefined, {timeout: 120_000});
  await page.locator('.rooms summary').click();
  await page.locator('#create-room').click();
  const observed = [];
  for (const [index, {band, visible, state}] of shots.entries()) {
    if (process.env.DEBUG_GROOM) console.error('Testing', band, 'at tick', state.tick);
    if (index) room.send(JSON.stringify({type:'state', state, accepted:null}));
    const [x, z] = state.opponent.actor.pos;
    // Wait for interpolation to reach the physical position; a visibility failure
    // is reported by the assertion below instead of becoming an opaque timeout.
    await page.waitForFunction(({x,z,tick}) => {
      const probe = window.yugaProbe(), remote = probe.renderer?.remoteHeroes?.[0];
      return probe.mode === 'playing' && probe.state.tick === tick && remote &&
        Math.hypot(remote.pos[0] - x, remote.pos[1] - z) < .005;
    }, {x,z,tick:state.tick}, {timeout: 100_000});
    const sample = await page.evaluate(() => {
      const { renderer, state } = window.yugaProbe();
      const { hero, skinnedSurfaces, pos, groomVisible } = renderer.remoteHeroes[0];
      const canvas = document.querySelector('#arena');
      return { hero, skinnedSurfaces, pos, groomVisible, local:state.actor.pos,
        localSurfaces:renderer.heroSkinnedSurfaces, cssHeight:canvas.clientHeight,
        gl:canvas.getContext('webgl2')?.getParameter(WebGL2RenderingContext.VERSION) };
    });
    assert.match(sample.gl, /WebGL 2/);
    assert.equal(sample.hero, 'hanuman');
    assert.equal(sample.skinnedSurfaces, 18);
    assert.equal(sample.localSurfaces, 18);
    const pixels = projectedHeight(sample.local, sample.pos, sample.cssHeight);
    assert.ok(band.startsWith('middle') ? pixels > 55 && pixels < 70 : visible ? pixels > 70 : pixels < 55);
    assert.equal(sample.groomVisible, visible, band + ' at ' + pixels.toFixed(2) + ' px');
    observed.push({band, tick:state.tick, projected_css_px:+pixels.toFixed(2), ...sample});
  }
  assert.deepEqual(observed[1].pos, observed[3].pos);
  assert.deepEqual(observed[0].pos, observed[4].pos);
  const tag = '<script id="payload" type="application/json">';
  const start = html.indexOf(tag) + tag.length;
  const hero = JSON.parse(html.toString('utf8', start, html.indexOf('</script>', start))).blobs.hero;
  const result = { test:'Remote Hanuman groom hysteresis in packaged WebGL2 game', pass:true,
    transport:'Playwright dispatches five unmodified local Rust/WASM duel snapshots through the game room WebSocket handler.',
    chromium:browser.version(), zip_sha256:digest(await readFile(zip)), html_sha256:digest(html),
    wasm_sha256:digest(wasm), embedded_hanuman_sha256:digest(Buffer.from(hero, 'base64')),
    local_and_remote:'Both seats use the same finished Hanuman. The remote groomVisible diagnostic reads the cached PlayCanvas MeshInstance.visible flag.',
    observations:observed };
  const report = JSON.stringify(result, null, 2) + '\n';
  if (values.output) await writeFile(values.output, report);
  console.log(report);
} catch (error) {
  if (page) console.error(await page.evaluate(() => {
    const p = window.yugaProbe?.();
    return {mode:p?.mode, room:p?.room, tick:p?.state?.tick, remote:p?.renderer?.remoteHeroes,
      status:document.querySelector('#room-status')?.textContent, initial:document.querySelector('#status')?.textContent};
  }).catch(() => 'Game document unavailable'));
  throw error;
} finally {
  await browser.close();
}
