// Reproducible, silent recordings of the actual PlayCanvas renderer.
// node games/yuga/tools/capture-art-review.mjs --plan
// After the release/browser gate: add --capture --pilot (Rama/Hanuman/Sita + 3 units)
// or --capture --all. Outputs are excluded from git under dist/ or test-results/.
// No runtime/art source edits; fixtures are labelled in every encoded frame.
import assert from 'node:assert/strict';
import { promises as fs, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, expect } from '@playwright/test';
import { tsImport } from 'tsx/esm/api';

const exec = promisify(execFile);
const activeTools = new Map();
async function trackedExec(file, args, options) {
  const operation = exec(file, args, { timeout: 120_000, killSignal: 'SIGKILL', ...options });
  activeTools.set(operation.child, operation);
  try { return await operation; } finally { activeTools.delete(operation.child); }
}
const root = fileURLToPath(new URL('../../../', import.meta.url));
const args = process.argv.slice(2);
const option = key => { const index = args.indexOf(key); return index < 0 ? undefined : args[index + 1]; };
if (!args.includes('--capture') && !args.includes('--plan')) {
  console.log('Use --plan, or --capture --pilot / --capture --all after the exclusive browser gate. Optional --out dist/yuga-art-review, --base-url http://127.0.0.1:5192, --skip-encode.');
  process.exit(0);
}
const pilot = args.includes('--pilot');
const output = path.resolve(root, option('--out') || `dist/yuga-art-review${pilot ? '-pilot' : ''}`);
assert.ok(['dist', 'test-results'].some(dir => output.startsWith(path.join(root, dir) + path.sep)), 'Write review artifacts only under dist/ or test-results/.');
assert.match(output, /^[a-zA-Z0-9/_. -]+$/, 'Use a simple output path for FFmpeg filter paths.');
const base = new URL(option('--base-url') || 'http://127.0.0.1:5192/');
assert.ok(base.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(base.hostname) && !base.username && !base.password && !base.search && !base.hash, 'Capture only an explicitly local development renderer.');
// Use the identical TypeScript definitions served by Vite, eliminating any
// stale dist/server pairing. tsx is an existing project dependency.
const { HEROES } = await tsImport('../shared/heroes.ts', import.meta.url);
const { ArenaSimulation } = await tsImport('../shared/simulation.ts', import.meta.url);
const { YUGA_PROTOCOL } = await tsImport('../shared/types.ts', import.meta.url);
const heroes = HEROES.filter(hero => !pilot || ['rama', 'hanuman', 'sita'].includes(hero.id));
const unitIds = (pilot ? ['soldier', 'yaksha', 'sky-sentinel'] : ['soldier', 'city-watch', 'minister', 'king', 'yaksha', 'naga', 'sky-sentinel']);
const hash = value => createHash('sha256').update(value).digest('hex');
const pause = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const relative = filename => path.relative(output, filename).split(path.sep).join('/');
async function filesUnder(directory) {
  const files = [];
  for (const entry of await fs.readdir(path.join(root, directory), { withFileTypes: true })) {
    const filename = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await filesUnder(filename));
    else if (entry.isFile()) files.push(filename);
  }
  return files;
}
const manifest = {
  schema: 1, startedAt: new Date().toISOString(), finishedAt: null, passed: false,
  scope: 'Actual PlayCanvas/GLB screen captures. Gallery is clip playback. Arena ability fixtures use staged positions/health and real simulation commands. Unit fixtures stage snapshots/events. Coastal views stage the player position and use ordinary keyboard aim/settings. No human match, earned kill, network capacity, sound recording or 4D claim.',
  audio: 'Silent: CDP captures rendered frames only. No soundtrack or commercial recording.',
  timing: 'Each JPEG is an actual Chromium screencast frame. Native timestamp differences request variable-frame durations; the image/encoder timebase can quantize them, so ffprobe durations and timing differences are recorded. No generated/interpolated motion. Capture overhead and repeated/held frames are not a game performance benchmark.',
  simulation: 'Imported directly from shared/simulation.ts through the installed tsx loader; Vite serves the same source. Ability simulation and staged unit ticks run at20Hz; fixture snapshots publish at5Hz, with immediate command results/stage changes. No compiled server fixture dependency.',
  presentation: 'Capture-only requestAnimationFrame scheduling waits100ms after each native callback batch. All queued callbacks, native timestamps and cancellation are preserved. This sampling budget reduces SwiftShader/CDP contention and is not a game or hardware frame-rate benchmark.',
  revision: (await exec('git', ['rev-parse', 'HEAD'], { cwd: root })).stdout.trim(),
  pilot, viewport: { width: 960, height: 600 }, encodedSize: { width: 960, height: 600 },
  heroIds: heroes.map(hero => hero.id), unitIds, expectedAbilities: heroes.length * 3,
  sources: [], assets: [], assetResponses: [], loads: [], shots: [], recordings: [], errors: [], files: [],
};
const sources = [...await filesUnder('games/yuga/client'), ...await filesUnder('games/yuga/shared'), 'games/yuga/index.html', 'vite.yuga.config.ts', 'package-lock.json', 'games/yuga/tools/capture-art-review.mjs'].sort();
for (const filename of sources) {
  manifest.sources.push({ path: filename, sha256: hash(await fs.readFile(path.join(root, filename))) });
}
for (const name of ['hero-assets.json', 'unit-assets.json']) {
  const filename = path.join(root, 'games/yuga/art', name), bytes = await fs.readFile(filename), data = JSON.parse(bytes);
  manifest.assets.push({ manifest: name, sha256: hash(bytes), models: data.models.map(({ id, sha256 }) => ({ id, sha256 })) });
}
if (args.includes('--plan') && !args.includes('--capture')) {
  console.log(JSON.stringify({ output, pilot, sourceFiles: sources.length, heroIds: manifest.heroIds, unitIds, city: pilot ? [] : ['day-high', 'night-high', 'day-low', 'night-low', 'coast-day-high', 'coast-night-high'], abilities: heroes.flatMap(hero => hero.abilities.map((ability, slot) => ({ hero: hero.id, slot, name: ability.name, kind: ability.kind, seconds: ability.mechanic === 'mithila-sanctuary' ? 8 : 6 }))), scope: manifest.scope }, null, 2));
  process.exit(0);
}
await fs.mkdir(output, { recursive: true });
assert.ok(!existsSync(path.join(output, 'manifest.json')), 'Use a fresh --out directory; preserve previous evidence.');
await fs.mkdir(path.join(output, 'shots'), { recursive: true });
const save = () => fs.writeFile(path.join(output, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
let server, browser, context, page, fixture, stopping = false;
const assetReads = [];
const shutdown = async () => {
  // Encoding starts after the browser is closed, so always cancel subprocesses
  // even when rendering-resource cleanup has already completed.
  const pending = [...activeTools.entries()];
  for (const [child] of pending) if (child.exitCode === null) child.kill('SIGKILL');
  await Promise.allSettled(pending.map(([, operation]) => operation));
  if (stopping) return; stopping = true;
  fixture?.close(); await context?.close().catch(() => {}); await browser?.close().catch(() => {});
  if (server && server.exitCode === null) { server.kill('SIGTERM'); await Promise.race([new Promise(resolve => server.once('exit', resolve)), pause(2000)]); }
};
process.once('SIGINT', () => { manifest.errors.push('Interrupted by SIGINT'); void shutdown().finally(() => save()).finally(() => process.exit(130)); });
process.once('SIGTERM', () => { manifest.errors.push('Interrupted by SIGTERM'); void shutdown().finally(() => save()).finally(() => process.exit(143)); });

async function startServer() {
  if (option('--base-url')) return;
  const log = await fs.open(path.join(output, 'vite.log'), 'w');
  server = spawn(process.execPath, [path.join(root, 'node_modules/vite/bin/vite.js'), '--config', 'vite.yuga.config.ts', '--host', '127.0.0.1', '--port', base.port, '--strictPort'], { cwd: root, stdio: ['ignore', log.fd, log.fd] });
  await log.close();
  const end = Date.now() + 30_000;
  while (Date.now() < end) {
    if (server.exitCode !== null) throw new Error(`Local Vite exited ${server.exitCode}; see vite.log.`);
    try { if ((await fetch(base, { signal: AbortSignal.timeout(1000) })).ok) return; } catch { /* Startup only. */ }
    await pause(200);
  }
  throw new Error('Local Vite did not become ready.');
}

async function newPage() {
  context = await browser.newContext({ viewport: manifest.viewport, deviceScaleFactor: 1, reducedMotion: 'no-preference' });
  page = await context.newPage(); page.setDefaultTimeout(45_000);
  await page.addInitScript(() => {
    const native = requestAnimationFrame.bind(window), queue = new Map();
    let next = 0, queued = false, dispatching = false, last = performance.now() - 100, timer;
    const schedule = () => {
      if (!queue.size || queued || dispatching || timer !== undefined) return;
      timer = window.setTimeout(() => {
        timer = undefined; queued = true;
        native(time => {
          queued = false; dispatching = true;
          for (const id of [...queue.keys()]) {
            const callback = queue.get(id); queue.delete(id);
            if (callback) try { callback(time); } catch (error) { window.setTimeout(() => { throw error; }, 0); }
          }
          dispatching = false; last = performance.now(); schedule();
        });
      }, Math.max(0, 100 - performance.now() + last));
    };
    window.requestAnimationFrame = callback => { const id = ++next; queue.set(id, callback); schedule(); return id; };
    window.cancelAnimationFrame = id => { queue.delete(id); };
  });
  page.on('pageerror', error => manifest.errors.push(`Page: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') manifest.errors.push(`Console: ${message.text()}`); });
  page.on('requestfailed', request => manifest.errors.push(`Request: ${request.url()} ${request.failure()?.errorText}`));
  page.on('response', response => {
    const url = new URL(response.url());
    // Vite also serves ?url module wrappers; only the binary fetch is evidence.
    if (!url.pathname.endsWith('.glb') || url.searchParams.has('url') || url.searchParams.has('import')) return;
    assetReads.push((async () => {
      const bytes = await response.body(), sha256 = hash(bytes), expected = manifest.assets.flatMap(value => value.models).find(value => value.sha256 === sha256);
      manifest.assetResponses.push({ url: response.url(), status: response.status(), bytes: bytes.length, sha256, modelId: expected?.id });
      assert.equal(response.status(), 200, `Model HTTP status: ${response.url()}`);
      assert.equal(bytes.subarray(0, 4).toString(), 'glTF', `Not a GLB: ${response.url()}`);
      assert.ok(expected, `Downloaded GLB does not match either source manifest: ${response.url()}`);
    })().catch(error => manifest.errors.push(String(error))));
  });
}
async function boot(heroId) {
  await page.goto(base.href, { waitUntil: 'domcontentloaded', timeout: 90_000 });
  await page.waitForFunction(() => !!window.__YUGA);
  await page.locator('#lobby-settings').click();
  await page.locator('#quality').selectOption('high');
  await page.locator('#lighting').selectOption('day');
  await page.locator('#mute').check();
  await page.locator('#reduced-motion').uncheck();
  await page.locator('#resume-game').click();
  await page.locator(`[data-hero="${heroId}"]`).click();
}
async function closePage() { fixture?.close(); fixture = undefined; await Promise.all(assetReads); await context.close(); context = undefined; page = undefined; }
async function diagnostics() { return page.evaluate(() => ({ playerId: window.__YUGA.playerId(), showcase: window.__YUGA.showcase(), assets: window.__YUGA.assets(), metrics: window.__YUGA.metrics(), snapshot: window.__YUGA.snapshot(), settings: { quality: document.querySelector('#quality')?.value, lighting: document.querySelector('#lighting')?.value } })); }
function brief(data) {
  const local = data.snapshot?.actors.find(actor => actor.id === data.playerId);
  return { settings: data.settings, showcase: data.showcase?.hero, instances: data.assets?.instances, units: data.assets?.units?.instances, fallback: data.assets?.fallback, unitFallback: data.assets?.units?.fallback, time: data.snapshot?.time, local: local && { x: local.x, z: local.z, yaw: local.yaw, health: local.health, shield: local.shield, cooldowns: local.cooldowns, cast: local.cast }, events: data.snapshot?.events, projectiles: data.snapshot?.projectiles, zones: data.snapshot?.zones, metrics: data.metrics };
}
function timelineSample(data) {
  const actor = data.snapshot?.actors.find(value => value.id === data.playerId);
  const instance = value => ({ id: value.id, state: value.state, action: value.action, animationTime: value.animationTime, loaded: value.loaded, fallback: value.fallback, transitions: value.transitions, poseBones: value.poseBones, pose: value.pose });
  return { time: data.snapshot?.time, local: actor && { x: actor.x, z: actor.z, y: actor.y, health: actor.health, shield: actor.shield, cast: actor.cast }, heroes: data.assets?.instances.map(instance), units: data.assets?.units?.instances.map(instance), projectiles: data.snapshot?.projectiles.length, zones: data.snapshot?.zones.map(zone => ({ id: zone.id, kind: zone.kind, x: zone.x, z: zone.z, life: zone.life })) };
}

// CDP produces actual rendered frames, not animation reconstruction. Each shot
// has its own bounded queue and is stopped before selecting the next action.
async function shot(id, title, mode, seconds, trigger = async () => {}, metadata = {}) {
  const directory = path.join(output, 'shots', id); await fs.mkdir(directory, { recursive: true });
  const session = await context.newCDPSession(page), frames = [];
  let queue = Promise.resolve(), writeError, active = true;
  session.on('Page.screencastFrame', event => {
    if (!active) { void session.send('Page.screencastFrameAck', { sessionId: event.sessionId }).catch(() => {}); return; }
    const index = frames.length, filename = path.join(directory, `${String(index).padStart(5, '0')}.jpg`);
    frames.push({ file: relative(filename), timestamp: event.metadata.timestamp, bytes: Buffer.byteLength(event.data, 'base64') });
    queue = queue.then(async () => { await fs.writeFile(filename, Buffer.from(event.data, 'base64')); await session.send('Page.screencastFrameAck', { sessionId: event.sessionId }); }).catch(error => { writeError = error; });
  });
  const record = { id, title, mode, seconds, ...metadata, frames, timeline: [], startedAt: new Date().toISOString(), before: brief(await diagnostics()) };
  manifest.shots.push(record);
  try {
    await session.send('Page.startScreencast', { format: 'jpeg', quality: 88, maxWidth: 960, maxHeight: 600, everyNthFrame: 1 });
    await trigger();
    const end = performance.now() + seconds * 1000;
    while (performance.now() < end) {
      await pause(Math.min(200, Math.max(0, end - performance.now())));
      if (metadata.category !== 'gallery') record.timeline.push(timelineSample(await diagnostics()));
    }
  } finally { active = false; await session.send('Page.stopScreencast').catch(() => {}); await queue; await session.detach(); }
  if (writeError) throw writeError;
  assert.ok(frames.length >= 2, `${id}: fewer than two actual rendered frames.`);
  assert.ok(frames.every(frame => Number.isFinite(frame.timestamp)), `${id}: missing native frame timestamps.`);
  record.after = brief(await diagnostics()); record.finishedAt = new Date().toISOString();
  const deltas = frames.slice(1).map((frame, index) => frame.timestamp - frames[index].timestamp);
  assert.ok(deltas.every(delta => delta >= 0), `${id}: nonmonotonic frame timestamps.`);
  record.frameStats = { count: frames.length, firstToLastSeconds: frames.at(-1).timestamp - frames[0].timestamp, largestGapSeconds: Math.max(...deltas), averageDeliveredFps: (frames.length - 1) / Math.max(.001, frames.at(-1).timestamp - frames[0].timestamp) };
  await save(); console.log(`Captured ${id}: ${frames.length} actual frames.`);
  return record;
}

// Test-only transport: no live room is joined. Ability commands/input still
// pass through the production ArenaSimulation; only the scene setup is staged.
async function abilityFixture(heroId) {
  const sim = new ArenaSimulation({ room: 'ART-REVIEW', seed: 20261016, botsPerTeam: 0, duration: 480 });
  const self = sim.addPlayer('review-local', 'Staged art review', heroId, 'sun');
  const enemy = sim.addPlayer('review-target', 'Staged target', 'duryodhana', 'moon');
  const ally = sim.addPlayer('review-ally', 'Staged ally', 'sita', 'sun');
  let socket, timer, previous = performance.now(), accumulator = 0, lastPublished = -Infinity;
  const wire = { joins: 0, welcomes: 0, snapshots: 0, lastSentAt: null };
  const results = [], commands = [], send = (immediate = true) => {
    const now = performance.now(); if (!socket || !immediate && now - lastPublished < 200) return;
    socket.send(JSON.stringify({ type: 'snapshot', snapshot: sim.snapshot() })); lastPublished = now;
    wire.snapshots++; wire.lastSentAt = new Date().toISOString();
  };
  const advance = () => {
    const now = performance.now(); accumulator += Math.min(.25, Math.max(0, (now - previous) / 1000)); previous = now;
    while (accumulator >= .05) { sim.step(.05); accumulator -= .05; }
    // Remove unrelated scheduled lane waves in this isolated visual fixture.
    for (const actor of sim.actors.values()) if (actor.kind === 'minion' && actor.minionRole !== 'summon') sim.actors.delete(actor.id);
    send(false);
  };
  const stage = slot => {
    const ability = HEROES.find(hero => hero.id === heroId).abilities[slot];
    Object.assign(self, { x: 0, z: -8, y: 0, yaw: 0, health: self.maxHealth, shield: 0 });
    Object.assign(ally, { x: -2.5, z: -6, y: 0, health: Math.round(ally.maxHealth * .45), shield: 0 });
    const distance = ['slow', 'pull'].includes(ability.kind) ? ability.range : Math.min(6, Math.max(2.5, ability.range - .5));
    Object.assign(enemy, { x: 0, z: -8 + distance, y: 0, health: enemy.maxHealth, shield: 0, respawn: 0 });
    sim.projectiles = []; sim.zones = []; send();
  };
  await page.routeWebSocket('**/ws', route => {
    socket = route;
    route.onMessage(raw => {
      const message = JSON.parse(String(raw));
      if (message.type === 'join') {
        wire.joins++; stage(0); route.send(JSON.stringify({ type: 'welcome', protocol: YUGA_PROTOCOL, id: self.id, room: sim.room, token: 'a'.repeat(48), snapshot: sim.snapshot() })); wire.welcomes++;
        previous = performance.now(); timer = setInterval(advance, 50);
      } else if (message.type === 'input') sim.input(self.id, message);
      else if (message.type === 'command') { const result = sim.command(self.id, message); commands.push({ time: sim.time, ...message }); results.push({ time: sim.time, ...result }); route.send(JSON.stringify(result)); send(); }
    });
  });
  return { stage, sim, commands, results, wire, close() { clearInterval(timer); socket = undefined; } };
}
async function joinFixture() {
  const load = { startedAt: new Date().toISOString(), samples: [] }; manifest.loads.push(load);
  await page.locator('#online-open').click(); await page.locator('#join-room').click();
  const deadline = Date.now() + 120_000;
  while (true) {
    const sample = await page.evaluate(() => {
      const metrics = window.__YUGA.metrics(), snapshot = window.__YUGA.snapshot(), self = snapshot?.actors.find(actor => actor.id === window.__YUGA.playerId());
      return { at: new Date().toISOString(), metrics, snapshot: snapshot && { phase: snapshot.phase, time: snapshot.time, tick: snapshot.tick, self: self && { id: self.id, health: self.health } }, visibility: document.visibilityState, focus: document.hasFocus(), focusId: document.activeElement?.id, dialog: document.querySelector('dialog[open]')?.id,
        loadingHidden: document.querySelector('#loading').hidden, loader: document.querySelector('#loading-copy').textContent, status: document.querySelector('#status-line').textContent,
        globalError: document.querySelector('#global-error').textContent, errorHidden: document.querySelector('#global-error').hidden };
    });
    load.samples.push({ ...sample, wire: fixture?.wire && { ...fixture.wire } });
    if (sample.metrics.ready && sample.snapshot && sample.loadingHidden) break;
    if (!sample.errorHidden && sample.globalError.includes('arena could not start')) throw new Error(`Fixture startup failed: ${sample.globalError}`);
    if (Date.now() >= deadline) throw new Error(`Fixture readiness timed out: ${JSON.stringify(load.samples.at(-1))}`);
    await pause(250);
  }
  load.finishedAt = new Date().toISOString(); await save();
  if (load.samples.at(-1).focusId !== 'arena') await page.locator('#arena').focus({ timeout: 5000 });
}
async function captureHero(hero) {
  await newPage(); fixture = await abilityFixture(hero.id); await boot(hero.id);
  await page.locator('#inspect-hero').click();
  await expect(page.locator('#showcase-status')).toContainText('Drag to rotate', { timeout: 60_000 });
  for (const [clip, seconds] of [['idle', 2], ['run', 2], ['fire', 2], ['cast1', 3], ['cast2', 3], ['cast3', 3]]) {
    const record = await shot(`${hero.id}-gallery-${clip}`, `${hero.name} / ${clip}`, 'GALLERY: actual GLB clip playback; no arena effects', seconds, () => page.locator(`[data-clip="${clip}"]`).click(), { heroId: hero.id, clip, category: 'gallery' });
    assert.equal(record.after.showcase.heroId, hero.id); assert.equal(record.after.showcase.fallback, false); assert.equal(record.after.showcase.state, clip);
  }
  await page.locator('#hero-dialog [data-close]').click(); await joinFixture();
  for (const [slot, ability] of hero.abilities.entries()) {
    fixture.stage(slot); await pause(450);
    const previous = fixture.results.length;
    const record = await shot(`${hero.id}-ability-${slot + 1}`, `${hero.name} / ${'QER'[slot]}: ${ability.name}`, 'STAGED ARENA: fixture positions/health; real accepted simulation cast', ability.mechanic === 'mithila-sanctuary' ? 8 : 6,
      () => page.keyboard.press(['KeyQ', 'KeyE', 'KeyR'][slot]), { heroId: hero.id, slot, ability: { ...ability }, category: 'ability' });
    const results = fixture.results.slice(previous); record.commands = fixture.commands.filter(command => results.some(result => result.id === command.id)); record.results = results;
    assert.ok(results.some(result => result.ok && result.code === 'ABILITY_CAST'), `${hero.id}/${slot}: no accepted command.`);
    assert.ok(record.after.events.some(event => event.type === 'ability' && event.actorId === 'review-local' && event.label === ability.name), `${hero.id}/${slot}: no authoritative ability event.`);
    assert.equal(record.after.fallback.length, 0); assert.equal(record.after.unitFallback.length, 0);
    if (ability.mechanic) {
      const before = record.before.instances.find(instance => instance.id === 'review-local');
      const locked = record.timeline.filter(sample => sample.local?.cast).flatMap(sample => sample.heroes.filter(instance => instance.id === 'review-local').map(instance => ({ ...instance, snapshotTime: sample.time, castStartedAt: sample.local.cast.startedAt })));
      // Received authority and the most recent presented pose can differ between
      // engine frames. Keep those raw samples, but do not call them cast poses.
      const presented = locked.filter(instance => instance.state === `cast${slot + 1}`);
      const allPresented = record.timeline.flatMap(sample => sample.heroes.filter(instance => instance.id === 'review-local' && instance.state === `cast${slot + 1}`));
      const timedEventReplays = record.timeline.flatMap(sample => sample.heroes.filter(instance => instance.id === 'review-local' && instance.action === `cast${slot + 1}`).map(instance => ({ snapshotTime: sample.time, state: instance.state, action: instance.action, authorityCasting: !!sample.local?.cast })));
      const legs = before.poseBones.flatMap((name, index) => /^(upperleg|lowerleg)/.test(name) ? [index * 4, index * 4 + 1, index * 4 + 2, index * 4 + 3] : []);
      const maxLegDelta = Math.max(0, ...presented.flatMap(instance => legs.map(index => Math.abs(instance.pose[index] - before.pose[index]))));
      record.lockedCastReview = { samples: locked.length, presentedWhileLocked: presented.length, allPresentedSamples: allPresented.length, states: [...new Set(locked.map(instance => instance.state))], timedEventReplays, prePresentationSamples: locked.filter(instance => instance.state !== `cast${slot + 1}`).map(({ snapshotTime, castStartedAt, state, action }) => ({ snapshotTime, castStartedAt, state, action })), firstSampledPresentationSnapshotAgeSeconds: presented.length ? presented[0].snapshotTime - presented[0].castStartedAt : null, maxLegQuaternionComponentDeltaFromReady: maxLegDelta, scope: 'Actual presented base-cast lower-leg rotations while authority is locked. Every presented base-cast sample, including after authority clears, must have no upper overlay; no event-driven replay of the timed ability is permitted. Received snapshots may precede the next rendered pose; those boundary samples remain in the raw timeline and are listed separately. Sampled snapshot age is not exact render latency. Authored recovery may end when authority releases movement.' };
      assert.ok(presented.length, `${hero.id}: full-body locked cast was not sampled.`);
      assert.ok(allPresented.every(instance => instance.action === ''), `${hero.id}: an upper action still overlays the presented full-body pose.`);
      assert.equal(timedEventReplays.length, 0, `${hero.id}: the timed ability replayed through the event-driven upper layer.`);
      assert.ok(maxLegDelta > .005, `${hero.id}: no meaningful actual lower-body change from the ready stance was sampled.`);
    }
  }
  manifest.recordings.push({ id: hero.id, kind: 'hero', shots: manifest.shots.filter(value => value.heroId === hero.id).map(value => value.id) });
  await closePage();
}

async function unitFixture(unitId) {
  const sim = new ArenaSimulation({ room: 'UNIT-REVIEW', botsPerTeam: 0 });
  const self = sim.addPlayer('review-local', 'Unit art review', 'rama', 'sun'); self.x = 0;
  const snapshot = sim.snapshot(), events = []; let socket, timer, mode = 'idle', serial = 0, elapsed = 0, lastShot = -99;
  let subject;
  if (['soldier', 'city-watch', 'minister', 'king'].includes(unitId)) {
    subject = { ...structuredClone(self), id: `review-${unitId}`, name: unitId, kind: 'minion', team: 'moon', bot: true, connected: false, x: 0, z: -59, yaw: Math.PI, minionRole: unitId === 'king' ? 'siege' : 'escort', unitArchetype: unitId };
    snapshot.actors.push(subject);
  } else {
    subject = snapshot.neutrals.find(neutral => neutral.species === unitId);
    Object.assign(subject, { x: 0, z: -59, yaw: Math.PI, health: subject.maxHealth, state: 'idle', respawnAt: 0 });
  }
  const send = () => socket?.send(JSON.stringify({ type: 'snapshot', snapshot: { ...snapshot, events: events.slice(-64) } }));
  const emit = type => events.push({ id: ++serial, type, actorId: type === 'shot' ? subject.id : self.id, ...(type === 'defeat' ? { targetId: subject.id } : {}), team: type === 'shot' ? subject.team : self.team, label: `Staged ${unitId} ${type}`, color: '#ffffff', x: subject.x, z: subject.z, time: snapshot.time });
  await page.routeWebSocket('**/ws', route => { socket = route; route.onMessage(raw => { if (JSON.parse(String(raw)).type !== 'join') return;
    route.send(JSON.stringify({ type: 'welcome', protocol: YUGA_PROTOCOL, id: self.id, room: sim.room, token: 'c'.repeat(48), snapshot }));
    timer = setInterval(() => { snapshot.time += .05; snapshot.tick++; elapsed += .05;
      if (mode === 'run') subject.x = Math.sin(elapsed * 3) * .8;
      if (mode === 'fire' && elapsed - lastShot >= .9) { emit('shot'); lastShot = elapsed; }
      if (snapshot.tick % 4 === 0) send();
    }, 50);
  }); });
  return { setMode(next) { mode = next; elapsed = 0; lastShot = -99; subject.x = 0;
    if (next === 'defeat') { if (subject.kind === 'neutral') { subject.health = 0; subject.state = 'dead'; subject.respawnAt = snapshot.time + 40; } else { snapshot.actors = snapshot.actors.filter(actor => actor.id !== subject.id); emit('defeat'); } }
    send();
  }, id: subject.id, close() { clearInterval(timer); socket = undefined; } };
}
async function captureUnit(unitId) {
  await newPage(); fixture = await unitFixture(unitId); await boot('rama'); await joinFixture();
  for (const clip of ['idle', 'run', 'fire', 'defeat']) {
    const record = await shot(`unit-${unitId}-${clip}`, `${unitId} / ${clip}`, 'STAGED UNIT: snapshot movement/attack/death; actual skin and animation', clip === 'defeat' ? 1.5 : 2.5, async () => fixture.setMode(clip), { unitId, clip, category: 'unit' });
    const instances = [...record.timeline.flatMap(sample => sample.units || []), ...record.after.units].filter(value => value.id === fixture.id);
    assert.ok(instances.some(instance => instance.loaded && !instance.fallback), `${unitId}: actual unit skin missing.`);
    assert.ok(instances.some(instance => clip === 'fire' ? instance.action === clip && instance.transitions.fire > 0 : instance.state === clip), `${unitId}: animation state not observed during clip.`);
  }
  manifest.recordings.push({ id: unitId, kind: 'unit', shots: manifest.shots.filter(value => value.unitId === unitId).map(value => value.id) });
  await closePage();
}
async function captureCity() {
  await newPage(); await boot('rama');
  await page.locator('#practice-play').click();
  await expect(page.locator('#loading')).toBeHidden({ timeout: 120_000 });
  await page.waitForFunction(() => window.__YUGA.metrics().ready && !!window.__YUGA.snapshot());
  for (const quality of ['high', 'low']) for (const lighting of ['day', 'night']) {
    await page.keyboard.press('Escape');
    await page.locator('#quality').selectOption(quality); await page.locator('#lighting').selectOption(lighting);
    await page.locator('#resume-game').click(); await pause(500);
    await shot(`city-${lighting}-${quality}`, `Sangam City / ${lighting} / ${quality} quality`, 'NATIVE PRACTICE: fixed camera; ordinary lighting/quality settings; bots continue', 4, async () => {}, { category: 'city', quality, lighting });
  }
  manifest.recordings.push({ id: 'day-night', kind: 'city', shots: manifest.shots.filter(record => record.category === 'city').map(record => record.id) });
  await closePage();
}

async function captureCoast() {
  await newPage(); fixture = await abilityFixture('rama'); await boot('rama'); await joinFixture();
  // The western court is staged for a repeatable environment review. Camera
  // orientation still comes from native controls, never a hidden renderer API.
  Object.assign(fixture.sim.actors.get('review-local'), { x: -46, z: 5, y: 0 });
  await page.locator('#arena').focus();
  await page.keyboard.down('KeyL');
  try { await page.waitForFunction(() => window.__YUGA.metrics().yaw <= -1.35, undefined, { timeout: 10_000 }); }
  finally { await page.keyboard.up('KeyL'); }
  await pause(750);
  for (const lighting of ['day', 'night']) {
    await page.keyboard.press('Escape'); await page.locator('#lighting').selectOption(lighting);
    await page.locator('#resume-game').click(); await pause(500);
    const record = await shot(`coast-${lighting}-high`, `Western marsh and Lanka gate / ${lighting}`, 'STAGED VIEW: player position; native keyboard aim and lighting settings', 4, async () => {}, { category: 'city', view: 'western-coast', staged: true, quality: 'high', lighting });
    assert.ok(Math.abs(record.after.local.x + 46) < .1 && Math.abs(record.after.local.z - 5) < .1, 'Coastal fixture moved from its declared review position.');
    assert.ok(record.after.metrics.yaw < -1.2 && record.after.metrics.yaw > -2, 'Coastal camera did not face the west gate.');
  }
  manifest.recordings.push({ id: 'western-coast', kind: 'city', shots: manifest.shots.filter(record => record.view === 'western-coast').map(record => record.id) });
  await closePage();
}

async function probe(filename) {
  const result = await trackedExec('ffprobe', ['-v', 'error', '-count_frames', '-show_entries', 'format=duration,size:stream=codec_name,width,height,avg_frame_rate,nb_read_frames', '-of', 'json', filename], { timeout: 30_000, maxBuffer: 1024 * 1024 });
  return JSON.parse(result.stdout);
}
async function runFFmpeg(args) { await trackedExec('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-threads', '2', '-filter_threads', '1', ...args], { maxBuffer: 2 * 1024 * 1024 }); }
async function concatenate(ids, filename) {
  const list = path.join(output, `${path.basename(filename)}.concat`);
  await fs.writeFile(list, ids.map(id => `file '${path.join(output, 'shots', id, 'clip.mp4')}'`).join('\n') + '\n');
  await runFFmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', filename]);
  return probe(filename);
}
async function encode() {
  const font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';
  assert.ok(existsSync(font), 'Expected system DejaVu font for permanent source/mode stamps.');
  for (const record of manifest.shots) {
    const directory = path.join(output, 'shots', record.id), list = path.join(directory, 'frames.concat');
    const lines = [];
    for (const [index, frame] of record.frames.entries()) {
      lines.push(`file '${path.join(output, frame.file)}'`);
      const duration = index + 1 < record.frames.length ? Math.max(.001, record.frames[index + 1].timestamp - frame.timestamp) : .08;
      lines.push(`duration ${duration.toFixed(6)}`);
    }
    lines.push(`file '${path.join(output, record.frames.at(-1).file)}'`); await fs.writeFile(list, lines.join('\n') + '\n');
    const label = path.join(directory, 'label.txt'); await fs.writeFile(label, `${record.title}\n${record.mode} | ${manifest.revision.slice(0, 8)} | silent`);
    const video = path.join(directory, 'clip.mp4');
    await runFFmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-vf', `scale=960:600:flags=lanczos,drawbox=x=0:y=ih-52:w=iw:h=52:color=black@0.86:t=fill,drawtext=fontfile=${font}:textfile=${label}:fontcolor=white:fontsize=13:x=12:y=h-43:line_spacing=5`, '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '22', '-pix_fmt', 'yuv420p', '-fps_mode', 'vfr', '-movflags', '+faststart', '-an', video]);
    record.video = relative(video); record.videoProbe = await probe(video); record.videoSha256 = hash(await fs.readFile(video));
    record.encodedTiming = { nativeFirstToLastSeconds: record.frameStats.firstToLastSeconds, requestedFinalHoldSeconds: .08, encodedDurationSeconds: Number(record.videoProbe.format.duration), differenceSeconds: Number(record.videoProbe.format.duration) - record.frameStats.firstToLastSeconds - .08 };
    const poster = path.join(directory, 'poster.jpg');
    await runFFmpeg(['-ss', String(Math.min(Number(record.videoProbe.format.duration) * .45, record.category === 'ability' ? 1.4 : 1)), '-i', video, '-frames:v', '1', '-q:v', '2', poster]);
    record.poster = relative(poster);
  }
  for (const recording of manifest.recordings) {
    const filename = path.join(output, `${recording.kind}-${recording.id}.mp4`);
    recording.video = relative(filename); recording.probe = await concatenate(recording.shots, filename);
  }
  const highlights = manifest.shots.filter(record => record.category === 'gallery' && record.clip === 'idle' || record.category === 'unit' && record.clip === 'fire' || record.category === 'ability' && ['rama', 'hanuman', 'sita'].includes(record.heroId) && record.slot === 2);
  const reel = path.join(output, 'showcase-reel.mp4'); await concatenate(highlights.map(record => record.id), reel);
  manifest.reel = { file: relative(reel), scope: 'Selected real clips; full roster/ability/unit coverage remains in the chapter files.', probe: await probe(reel) };
  for (const [name, selected] of [['heroes', manifest.shots.filter(record => record.category === 'gallery' && record.clip === 'idle')], ['abilities', manifest.shots.filter(record => record.category === 'ability')], ['units', manifest.shots.filter(record => record.category === 'unit' && record.clip === 'fire')], ['city', manifest.shots.filter(record => record.category === 'city')]]) {
    if (!selected.length) continue;
    const directory = path.join(output, `sheet-${name}`); await fs.mkdir(directory, { recursive: true });
    for (const [index, record] of selected.entries()) {
      const label = path.join(directory, `${index}.txt`); await fs.writeFile(label, record.title);
      await runFFmpeg(['-i', path.join(output, record.poster), '-vf', `scale=480:300,pad=480:340:0:0:color=#14242c,drawtext=fontfile=${font}:textfile=${label}:fontcolor=white:fontsize=17:x=10:y=310`, '-frames:v', '1', '-q:v', '2', path.join(directory, `${String(index).padStart(3, '0')}.jpg`)]);
    }
    const filename = path.join(output, `contact-${name}.jpg`), columns = name === 'abilities' ? 3 : 4;
    await runFFmpeg(['-framerate', '1', '-i', path.join(directory, '%03d.jpg'), '-vf', `tile=${columns}x${Math.ceil(selected.length / columns)}:padding=4:margin=4:color=#14242c`, '-frames:v', '1', '-q:v', '2', filename]);
    manifest.files.push({ path: relative(filename), category: name, subjects: selected.length });
  }
  const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  const cards = manifest.recordings.map(recording => `<article><h2>${escape(recording.id)}</h2><video controls preload="none" src="${escape(recording.video)}"></video><p><a download href="${escape(recording.video)}">Download chapter MP4</a></p></article>`).join('\n');
  await fs.writeFile(path.join(output, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>YUGA actual rendered art review</title><style>body{font:16px/1.5 system-ui;background:#10242c;color:#e8edde;max-width:1200px;margin:auto;padding:24px}a{color:#f1cd80}video,img{max-width:100%;height:auto}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px}article{min-width:0}h1{font-size:32px}</style><h1>YUGA: actual rendered art review</h1><p>${escape(manifest.scope)}</p><p>Silent variable-frame captures. Staged scenes are labelled in every video. Encoded frame rates do not establish game performance. Revision ${escape(manifest.revision)}.</p><video controls preload="metadata" src="showcase-reel.mp4"></video><p><a href="showcase-reel.mp4" download>Download highlight MP4</a> · <a href="manifest.json">Full provenance and frame manifest</a></p><p>${manifest.files.map(file => `<a href="${escape(file.path)}">${escape(file.category)} contact sheet (${file.subjects})</a>`).join(' · ')}</p><section>${cards}</section></html>`);
}

try {
  await save(); await startServer();
  browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  for (const hero of heroes) await captureHero(hero);
  for (const unitId of unitIds) await captureUnit(unitId);
  if (!pilot) { await captureCity(); await captureCoast(); }
  await shutdown();
  await Promise.all(assetReads);
  for (const source of manifest.sources) assert.equal(hash(await fs.readFile(path.join(root, source.path))), source.sha256, `Source changed during capture: ${source.path}`);
  assert.equal(manifest.shots.filter(record => record.category === 'ability').length, heroes.length * 3);
  assert.deepEqual(manifest.errors, [], 'Native capture errors; inspect manifest before encoding.');
  if (!args.includes('--skip-encode')) await encode();
  manifest.passed = true;
} catch (error) {
  manifest.errors.push(error instanceof Error ? error.stack : String(error)); console.error(manifest.errors.at(-1)); process.exitCode = 1;
  if (page && !page.isClosed()) await page.screenshot({ path: path.join(output, 'failure.png'), timeout: 10_000 }).catch(() => {});
}
finally { await shutdown(); manifest.finishedAt = new Date().toISOString(); await save(); }
