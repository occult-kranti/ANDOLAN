// Exercise the packaged camera against WASM-generated Sun and Moon wall cases.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { digest, launchChromium } from './browser-package.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const archive = path.resolve(process.argv[2] ?? path.join(root, 'downloads/yuga-rust-confluence.zip'));
const output = path.resolve(process.argv[3] ?? '/tmp/yuga-camera-browser');
const member = (name) => execFileSync('unzip', ['-p', archive, name], { maxBuffer: 160 * 1024 * 1024 });
const zipBytes = await readFile(archive);
const html = member('yuga-rust.html');
const wasm = member('yuga-rust.wasm');
const tag = '<script id="payload" type="application/json">';
const payloadStart = html.indexOf(tag) + tag.length;
const payloadEnd = html.indexOf('</script>', payloadStart);
assert.ok(payloadStart >= tag.length && payloadEnd > payloadStart);
const payload = JSON.parse(html.subarray(payloadStart, payloadEnd).toString());
const map = payload.map;
const boxes = [...map.authority_collision_boxes, ...map.traversal.native_collision_boxes].map((box) => {
  assert.equal(box.anchor, 'base_center');
  const [x, y, z] = box.position;
  const [width, height, depth] = box.size;
  return { min: [x - width / 2, y, z - depth / 2], max: [x + width / 2, y + height, z + depth / 2] };
});

const { instance } = await WebAssembly.instantiate(wasm, {});
const authority = instance.exports;
function snapshot(seat) {
  const offset = authority.duel_snapshot(seat);
  return JSON.parse(Buffer.from(authority.memory.buffer, offset, authority.duel_snapshot_len()));
}
const states = [];
for (const seat of [0, 1]) {
  // Separate fresh authorities are needed: the Moon case is a mirror of the
  // Sun wall position, not the opposite seat observing the Sun's run.
  assert.equal(authority.duel_start(0, 0), 1);
  const direction = seat ? 1 : -1;
  for (let i = 0; i < 240; i++)
    authority.duel_step(direction, 0, 0, 1, direction, 0, 0, -1);
  states.push(snapshot(seat));
}
assert.equal(states[0].actor.team, 'sun');
assert.equal(states[1].actor.team, 'moon');
assert.ok(Math.hypot(states[0].actor.pos[0] + 60, states[0].actor.pos[1] + 5.4) < 0.01);
assert.ok(Math.hypot(states[1].actor.pos[0] - 60, states[1].actor.pos[1] - 5.4) < 0.01);

const subtract = (a, b) => a.map((n, i) => n - b[i]);
const dot = (a, b) => a.reduce((sum, n, i) => sum + n * b[i], 0);
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]
];
const normalize = (v) => {
  const length = Math.hypot(...v);
  assert.ok(Number.isFinite(length) && length > 0);
  return v.map((n) => n / length);
};
function viewFrame(camera) {
  const from = [camera.position.x, camera.position.y, camera.position.z];
  const toward = [camera.look.x, camera.look.y, camera.look.z];
  const forward = normalize(subtract(toward, from));
  const right = normalize(cross(forward, [0, 1, 0]));
  return { from, forward, right, up: cross(right, forward) };
}
function project(world, camera, width, height) {
  const frame = viewFrame(camera);
  const relative = subtract(world, frame.from);
  const depth = dot(relative, frame.forward);
  const focal = height / (2 * Math.tan(camera.fov * Math.PI / 360));
  return { x: width / 2 + focal * dot(relative, frame.right) / depth,
    y: height / 2 - focal * dot(relative, frame.up) / depth, depth };
}
function inside(point, box) {
  return point.every((n, i) => n > box.min[i] + 1e-6 && n < box.max[i] - 1e-6);
}
function inspectCamera(camera, actor, width, height) {
  assert.ok(camera && camera.fov >= 48 && camera.fov <= 75);
  assert.ok(camera.fraction >= 0 && camera.fraction <= camera.safeFraction + 1e-8);
  const view = viewFrame(camera);
  assert.ok(boxes.every((box) => !inside(view.from, box)), 'camera center entered an authored box');
  const near = 0.12;
  const halfHeight = near * Math.tan(camera.fov * Math.PI / 360);
  const halfWidth = halfHeight * width / height;
  const corners = [];
  for (const x of [-1, 1]) {
    for (const y of [-1, 1]) {
      const point = view.from.map((n, i) =>
        n + near * view.forward[i] + x * halfWidth * view.right[i] + y * halfHeight * view.up[i]);
      assert.ok(boxes.every((box) => !inside(point, box)), 'a near-plane corner entered an authored box');
      corners.push(point);
    }
  }
  const feet = project([actor.pos[0], actor.y, actor.pos[1]], camera, width, height);
  const head = project([actor.pos[0], actor.y + 2.1, actor.pos[1]], camera, width, height);
  if (camera.fullyFramed) {
    for (const point of [feet, head]) {
      assert.ok(point.depth > near && point.x >= width * .05 - .01 && point.x <= width * .95 + .01 &&
        point.y >= height * .05 - .01 && point.y <= height * .95 + .01, 'framed subject clipped');
    }
  }
  return { feet, head, nearPlaneCorners: corners };
}

await mkdir(output, { recursive: true });
const browser = await launchChromium();
const cases = [];
try {
  for (const seat of [0, 1]) {
    const team = seat ? 'moon' : 'sun';
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1.5 });
    const page = await context.newPage();
    const errors = [], external = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    const pageUrl = 'http://127.0.0.1:8791/yuga-rust.html';
    await page.route('**/*', (route) => {
      if (route.request().url() === pageUrl) return route.fulfill({ contentType: 'text/html', body: html });
      external.push(route.request().url());
      return route.abort();
    });
    await page.routeWebSocket('**/rooms', (socket) => {
      socket.onMessage((message) => {
        if (JSON.parse(message).type !== 'create') return;
        socket.send(JSON.stringify({ type: 'lobby', code: 'CAMERA', count: 2, capacity: 2, seat }));
        socket.send(JSON.stringify({ type: 'state', state: states[seat], accepted: null }));
      });
    });
    await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout: 120_000 });
    await page.waitForFunction(() => window.yugaProbe?.().mode === 'ready', null, { timeout: 120_000 });
    await page.locator('#hero').selectOption('hanuman');
    await page.locator('.rooms summary').click();
    await page.locator('#create-room').click();
    await page.waitForFunction(({ team, tick }) => {
      const p = window.yugaProbe?.();
      return p?.mode === 'playing' && p.state?.tick === tick && p.state.actor.team === team &&
        p.renderer?.cameraClearance && p.renderer.frames > 5;
    }, { team, tick: states[seat].tick }, { timeout: 120_000 });
    for (const viewport of [
      { width: 1280, height: 800, label: 'desktop' },
      { width: 390, height: 844, label: 'portrait' },
      { width: 1920, height: 600, label: 'wide' }
    ]) {
      const previousFrames = await page.evaluate(() => window.yugaProbe().renderer.frames);
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForFunction(({ width, height, previousFrames }) => {
        const p = window.yugaProbe?.(), canvas = document.querySelector('#arena');
        return p?.renderer?.frames > previousFrames + 3 && canvas?.clientWidth === width && canvas?.clientHeight === height;
      }, { ...viewport, previousFrames }, { timeout: 120_000 });
      const current = await page.evaluate(() => {
        const p = window.yugaProbe(), canvas = document.querySelector('#arena');
        const rect = canvas.getBoundingClientRect();
        return { actor: p.state.actor, camera: p.renderer.cameraClearance,
          width: rect.width, height: rect.height, left: rect.left, top: rect.top,
          frames: p.renderer.frames, cameraForward: p.renderer.cameraForward };
      });
      assert.equal(current.actor.team, team);
      assert.equal(current.cameraForward, seat ? -1 : 1);
      const geometry = inspectCamera(current.camera, current.actor, current.width, current.height);
      const pointer = { x: current.left + current.width * .5, y: current.top + current.height * .7 };
      // Dispatch to the canvas so HUD controls do not mask the input mapping;
      // verify its real screen-to-world result by projecting it independently.
      await page.locator('#arena').dispatchEvent('pointermove', { clientX: pointer.x, clientY: pointer.y });
      const input = await page.evaluate(() => window.yugaProbe().input);
      assert.ok(input.ground?.every(Number.isFinite), 'pointer should hit the ground');
      const projectedPointer = project([input.ground[0], 0, input.ground[1]], current.camera, current.width, current.height);
      assert.ok(Math.abs(projectedPointer.x - (pointer.x - current.left)) < 2 &&
        Math.abs(projectedPointer.y - (pointer.y - current.top)) < 2, 'ground point should project back to pointer');
      if (viewport.label === 'desktop') {
        assert.ok(current.camera.fullyFramed, team + ' should fit in the desktop view');
        await page.screenshot({ path: path.join(output, team + '.png') });
      }
      cases.push({ team, viewport: viewport.label, device_scale_factor: 1.5, ...current, ...geometry, pointer, ground: input.ground, projectedPointer });
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    await context.close();
  }
  const report = { test: 'Packaged camera clearance with live Rust/WASM snapshots and staged room transport',
    zip_sha256: digest(zipBytes), html_sha256: digest(html), wasm_sha256: digest(wasm),
    chromium: browser.version(), authority_steps_per_case: 240, page_errors: [], external_requests: [], cases };
  await writeFile(path.join(output, 'camera-browser.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ output, checks: cases.length, zip_sha256: report.zip_sha256 }, null, 2));
} finally {
  await browser.close();
}
