// Production-only, ordinary UI smoke. Run after yuga:lab:build; never starts Vite.
// node games/yuga/tools/smoke-lab-built.mjs --built dist/yuga-lab --flavor all
// Optional: --output test-results/yuga-lab-built --preset control-point
//           --port 0 --mount /yuga/lab/ OR --server http://127.0.0.1:8080/yuga/lab/
//           --public-url https://occult-kranti.github.io/ANDOLAN/yuga/lab/
// Environment equivalents: YUGA_LAB_SMOKE_{BUILT,OUTPUT,FLAVOR,PRESET,PORT,MOUNT,SERVER,PUBLIC_URL}.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, promises as fs } from 'node:fs';
import { createServer } from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, expect } from '@playwright/test';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const flags = new Map();
const allowed = new Set(['built', 'output', 'flavor', 'preset', 'port', 'mount', 'server', 'public-url']);
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i].replace(/^--/, ''), value = process.argv[i + 1];
  assert.ok(process.argv[i].startsWith('--') && allowed.has(key) && value && !value.startsWith('--'), `Unknown or incomplete argument: ${process.argv[i]}`);
  assert.ok(!flags.has(key), `Repeated argument: --${key}`); flags.set(key, value);
}
const option = (key, fallback) => flags.get(key) ?? process.env[`YUGA_LAB_SMOKE_${key.toUpperCase().replaceAll('-', '_')}`] ?? fallback;
const flavor = option('flavor', 'all');
assert.ok(['all', 'lane', 'control'].includes(flavor), 'Flavor must be all, lane, or control.');
const preset = option('preset', flavor === 'control' ? 'control-point' : 'lane-economy');
assert.ok(['lane-economy', 'control-point'].includes(preset), 'Unknown preset.');
assert.ok(flavor === 'all' || preset === (flavor === 'lane' ? 'lane-economy' : 'control-point'), 'Preset is not available in this flavor.');
const built = path.resolve(root, option('built', flavor === 'all' ? 'dist/yuga-lab' : `dist/yuga-${flavor}-lab`));
const output = path.resolve(root, option('output', `test-results/yuga-lab-built-${flavor}`));
const port = Number(option('port', '0'));
assert.ok(Number.isInteger(port) && port >= 0 && port <= 65535, 'Port must be 0–65535.');
const mount = option('mount', flavor === 'all' ? '/yuga/lab/' : `/yuga/${flavor}-lab/`);
assert.match(mount, /^\/(?:[a-zA-Z0-9_-]+\/)*$/, 'Mount must be a slash-delimited URL path ending with /.');
const external = option('server', '');
const publicAddress = option('public-url', '');
assert.ok(!external || !publicAddress, '--server and --public-url are mutually exclusive.');
const publicUrl = publicAddress ? new URL(publicAddress) : undefined;
if (publicUrl) {
  assert.ok(['lab', 'lane-lab', 'control-lab'].some(track => publicUrl.href === `https://occult-kranti.github.io/ANDOLAN/yuga/${track}/`)
    && !publicUrl.username && !publicUrl.password && !publicUrl.search && !publicUrl.hash,
  '--public-url must be an approved HTTPS GitHub Pages lab URL without credentials, query or fragment.');
}
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const evidence = {
  schema: 1, startedAt: new Date().toISOString(), passed: false, flavor, preset, hero: 'rama', seed: 7301,
  built: path.relative(root, built), viewport: { width: 960, height: 640 }, quality: 'low',
  scope: `Built production files over ${publicUrl ? 'public GitHub Pages HTTPS with normal certificate verification' : 'loopback HTTP'}. Native UI selects one local-bot preset, launches, pauses, resumes and returns. Read-only DOM checks; no development API, injected game state, frame throttling, multiplayer or performance claim.`,
  models: [], assets: [], pageErrors: [], consoleErrors: [], requestFailures: [], httpErrors: [],
};
let server, browser, context, page;
let phase = 'preflight';
const responseChecks = [];
const mime = new Map([['.html', 'text/html; charset=utf-8'], ['.js', 'text/javascript; charset=utf-8'], ['.css', 'text/css; charset=utf-8'], ['.glb', 'model/gltf-binary'], ['.png', 'image/png'], ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'], ['.webp', 'image/webp'], ['.json', 'application/json'], ['.woff2', 'font/woff2']]);

async function listFiles(directory) {
  const files = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const filename = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await listFiles(filename));
    else if (entry.isFile()) files.push(filename);
  }
  return files;
}
function modelFor(filename, models) {
  return models.find(model => filename === `${model.id}.glb` || filename.startsWith(`${model.id}-`));
}
async function noDevelopmentHooks() {
  const found = await page.evaluate(() => ['__YUGA', '__YUGA_LAB', '__ANDOLAN'].filter(key => Object.hasOwn(window, key)));
  assert.deepEqual(found, [], 'Production must omit game development hooks.');
}
async function startServer() {
  const realBuilt = await fs.realpath(built);
  server = createServer((request, response) => {
    void (async () => {
      if (!['GET', 'HEAD'].includes(request.method ?? '')) { response.writeHead(405); response.end(); return; }
      let pathname;
      try { pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname); }
      catch { response.writeHead(400); response.end(); return; }
      if (!pathname.startsWith(mount)) { response.writeHead(404); response.end(); return; }
      const relative = pathname.slice(mount.length) || 'index.html';
      const filename = path.resolve(realBuilt, relative);
      if (filename !== realBuilt && !filename.startsWith(`${realBuilt}${path.sep}`)) { response.writeHead(403); response.end(); return; }
      try {
        const realFile = await fs.realpath(filename);
        if (!realFile.startsWith(`${realBuilt}${path.sep}`)) { response.writeHead(403); response.end(); return; }
        const info = await fs.stat(realFile);
        if (!info.isFile()) { response.writeHead(404); response.end(); return; }
        const body = await fs.readFile(realFile);
        response.writeHead(200, { 'Content-Type': mime.get(path.extname(realFile)) ?? 'application/octet-stream', 'Content-Length': body.length, 'Cache-Control': 'no-store' });
        response.end(request.method === 'HEAD' ? undefined : body);
      } catch (error) {
        response.writeHead(error.code === 'ENOENT' || error.code === 'ENOTDIR' ? 404 : 500); response.end();
      }
    })().catch(() => { if (!response.headersSent) response.writeHead(500); response.end(); });
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  return new URL(`http://127.0.0.1:${server.address().port}${mount}`);
}

try {
  await fs.mkdir(output, { recursive: true });
  const indexBytes = await fs.readFile(path.join(built, 'index.html'));
  evidence.document = { localBytes: indexBytes.length, localSha256: sha256(indexBytes) };
  const manifests = await Promise.all(['hero-assets.json', 'unit-assets.json'].map(async name => {
    const bytes = await fs.readFile(path.join(root, 'games/yuga/art', name));
    return { name, sha256: sha256(bytes), models: JSON.parse(bytes).models };
  }));
  const expectedModels = manifests.flatMap(manifest => manifest.models);
  const unitIds = manifests.find(manifest => manifest.name === 'unit-assets.json').models.map(model => model.id);
  assert.equal(expectedModels.length, 21, 'Deliberately revise the built-asset gate if the roster changes.');
  evidence.manifests = manifests.map(({ name, sha256: digest }) => ({ name, sha256: digest }));
  const builtModels = [];
  for (const filename of (await listFiles(built)).filter(file => file.endsWith('.glb'))) {
    const model = modelFor(path.basename(filename), expectedModels);
    assert.ok(model, `Unknown built model: ${path.relative(built, filename)}`);
    const digest = sha256(await fs.readFile(filename));
    assert.equal(digest, model.sha256, `Built ${model.id} does not match its authored manifest.`);
    builtModels.push({ id: model.id, file: path.relative(built, filename), sha256: digest });
  }
  assert.equal(builtModels.length, 21, 'The production build must contain 21 binary GLBs.');
  assert.equal(new Set(builtModels.map(model => model.id)).size, 21, 'Every authored model must be present once.');
  evidence.builtModels = builtModels;
  const url = publicUrl ?? (external ? new URL(external) : await startServer());
  if (!publicUrl) assert.ok(url.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname), '--server accepts loopback HTTP only; approved public deployments require --public-url.');
  assert.ok(!url.username && !url.password && !url.search && !url.hash && url.pathname.endsWith('/'), 'Server URL must be a plain directory URL ending with /.');
  evidence.url = url.href; evidence.server = publicUrl ? 'public GitHub Pages HTTPS deployment, exact local build identity required' : external ? 'existing loopback HTTP server' : 'owned static HTTP server, exact built files, no SPA fallback';
  // Match the existing public smoke's managed transport. Do not log proxy details
  // or change certificate verification. Local HTTP never needs this proxy.
  const inheritedProxy = publicUrl && (process.env.HTTPS_PROXY || process.env.https_proxy || process.env.HTTP_PROXY || process.env.http_proxy);
  let proxy;
  if (inheritedProxy) {
    const proxyUrl = new URL(inheritedProxy);
    proxy = { server: `${proxyUrl.protocol}//${proxyUrl.host}` };
    if (proxyUrl.username) proxy.username = decodeURIComponent(proxyUrl.username);
    if (proxyUrl.password) proxy.password = decodeURIComponent(proxyUrl.password);
  }
  evidence.transport = { mode: publicUrl ? 'public-https' : 'loopback-http', tlsVerification: publicUrl ? true : null, inheritedProxySelected: !!proxy };
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, headless: true, proxy, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  context = await browser.newContext({ viewport: evidence.viewport });
  page = await context.newPage(); page.setDefaultTimeout(30000);
  page.on('pageerror', error => evidence.pageErrors.push({ phase, message: error.message }));
  page.on('console', message => { if (message.type() === 'error') evidence.consoleErrors.push({ phase, message: message.text() }); });
  page.on('requestfailed', request => evidence.requestFailures.push({ phase, url: request.url(), error: request.failure()?.errorText }));
  page.on('response', response => {
    const responsePhase = phase;
    if (response.status() >= 400) evidence.httpErrors.push({ phase: responsePhase, url: response.url(), status: response.status() });
    if (!/^https?:/.test(response.url())) return;
    evidence.assets.push({ phase: responsePhase, url: response.url(), status: response.status(), type: response.request().resourceType() });
    if (!new URL(response.url()).pathname.endsWith('.glb')) return;
    responseChecks.push((async () => {
      const model = { url: response.url(), status: response.status() }; evidence.models.push(model);
      try { const body = await response.body(); model.bytes = body.length; model.magic = body.subarray(0, 4).toString('ascii'); model.sha256 = sha256(body); }
      catch (error) { model.error = String(error); }
    })());
  });
  phase = 'lobby';
  const response = await page.goto(url.href, { waitUntil: 'domcontentloaded', timeout: 60000 });
  assert.equal(response?.status(), 200, 'Built document must be served successfully.');
  assert.equal(response.url(), url.href, 'The requested production document must not redirect to another location.');
  evidence.document.responseSha256 = sha256(await response.body());
  assert.equal(evidence.document.responseSha256, evidence.document.localSha256, 'HTTP server must serve the exact requested production build.');
  await expect(page.locator('#lab-lobby')).toBeVisible(); await noDevelopmentHooks();
  const label = { all: 'ORIGINAL PLAYABLE EXPERIMENTS · v1', lane: 'LANE ECONOMY TRACK · v1', control: 'HYBRID CONTROL TRACK · v1' }[flavor];
  await expect(page.locator('#lab-track-label')).toHaveText(label);
  evidence.label = await page.locator('#lab-track-label').textContent();
  await expect(page.locator('[data-experiment]:visible')).toHaveCount(flavor === 'all' ? 2 : 1);
  await page.locator(`#lab-lobby [data-experiment="${preset}"]`).click();
  await expect(page.locator(`[data-experiment="${preset}"]`)).toHaveAttribute('aria-pressed', 'true');
  await page.locator('#lab-hero').selectOption('rama'); await page.locator('#lab-seed').fill(String(evidence.seed));
  await page.locator('#lab-lobby-settings').click(); await expect(page.locator('#lab-settings-dialog')).toBeVisible();
  await page.locator('#lab-quality').selectOption('low'); await page.locator('#lab-lighting').selectOption('day');
  await page.locator('#lab-resume').click(); await expect(page.locator('#lab-settings-dialog')).toBeHidden();
  await page.screenshot({ path: path.join(output, 'lobby.png') });
  phase = 'launch'; await page.locator('#lab-launch').click();
  await expect(page.locator('#lab-hud')).toHaveAttribute('data-ready', 'true', { timeout: 150000 });
  await expect(page.locator('#lab-hud')).toHaveAttribute('data-warm-frames', '2');
  await expect(page.locator('#lab-loading')).toBeHidden(); await expect(page.locator('#lab-canvas')).toBeVisible();
  await expect(page.locator('#lab-error')).toBeHidden();
  await expect(page.locator('#lab-vitals-name')).toHaveText('Rama · SUN');
  await expect(page.locator('#lab-mode')).toHaveText(preset === 'control-point' ? 'HYBRID CONTROL · LOCAL BOTS' : 'LANE ECONOMY · LOCAL BOTS');
  if (preset === 'control-point') await expect(page.locator('#lab-point')).toBeVisible(); else await expect(page.locator('#lab-point')).toBeHidden();
  await expect(page.locator('#lab-ammo')).toHaveText('12 / 12');
  evidence.readiness = { ready: await page.locator('#lab-hud').getAttribute('data-ready'), warmFrames: Number(await page.locator('#lab-hud').getAttribute('data-warm-frames')), proof: 'Production DOM readiness is written only after two actual visible engine postrender callbacks; no test hook supplies it.' };
  phase = 'running';
  const initialClock = await page.locator('#lab-clock').textContent();
  await expect(page.locator('#lab-clock')).not.toHaveText(initialClock, { timeout: 15000 });
  evidence.runningClock = { initial: initialClock, advanced: await page.locator('#lab-clock').textContent() };
  await page.screenshot({ path: path.join(output, 'practice.png') });
  phase = 'pause'; await page.locator('#lab-pause').click();
  await expect(page.locator('#lab-settings-dialog')).toBeVisible();
  await expect(page.locator('#lab-pause-copy')).toContainText('This local run is paused');
  const pausedClock = await page.locator('#lab-clock').textContent(), pauseStarted = Date.now();
  await page.waitForTimeout(1400);
  assert.equal(await page.locator('#lab-clock').textContent(), pausedClock, 'Clock must remain unchanged while settings pause the local run.');
  evidence.pause = { clock: pausedClock, observedWallMs: Date.now() - pauseStarted };
  await page.screenshot({ path: path.join(output, 'paused.png') });
  phase = 'resume'; await page.locator('#lab-resume').click(); await expect(page.locator('#lab-settings-dialog')).toBeHidden();
  await expect(page.locator('#lab-canvas')).toBeFocused();
  await expect(page.locator('#lab-clock')).not.toHaveText(pausedClock, { timeout: 15000 });
  evidence.resumedClock = await page.locator('#lab-clock').textContent();
  phase = 'back'; await page.locator('#lab-pause').click(); await page.locator('#lab-back').click();
  await expect(page.locator('#lab-lobby')).toBeVisible(); await expect(page.locator('#lab-hud')).toBeHidden();
  await expect(page.locator('#lab-canvas')).toBeHidden(); await expect(page.locator('#lab-loading')).toBeHidden();
  await expect(page.locator('#lab-settings-dialog')).toBeHidden(); await expect(page.locator('#lab-launch')).toBeFocused();
  await expect(page.locator('#lab-error')).toBeHidden(); await noDevelopmentHooks();
  await page.screenshot({ path: path.join(output, 'returned.png') });
  await Promise.all(responseChecks);
  for (const model of evidence.models) {
    const modelUrl = new URL(model.url), expected = modelFor(path.basename(modelUrl.pathname), expectedModels);
    assert.ok(modelUrl.origin === url.origin && modelUrl.pathname.startsWith(url.pathname), `Model URL escaped the production mount: ${model.url}`);
    assert.equal(model.status, 200, `GLB HTTP error: ${model.url}`); assert.equal(model.magic, 'glTF', `Not binary glTF: ${model.url}`);
    assert.ok(expected, `Unexpected model URL: ${model.url}`); model.id = expected.id;
    assert.equal(model.sha256, expected.sha256, `Loaded ${expected.id} differs from its authored manifest.`);
  }
  const loaded = new Set(evidence.models.map(model => model.id));
  for (const id of ['rama', ...unitIds]) assert.ok(loaded.has(id), `Missing actual ${id} GLB response.`);
  const heroCount = [...loaded].filter(id => !unitIds.includes(id)).length;
  assert.ok(heroCount >= 1 && heroCount <= 6, 'Only the selected hero and five participating bots should preload.');
  evidence.loadedModels = { heroes: heroCount, units: unitIds.length, totalUnique: loaded.size, policy: 'Actual participating hero subset plus every unit; all 21 production files separately verified against authored manifests.' };
  for (const key of ['pageErrors', 'consoleErrors', 'requestFailures', 'httpErrors']) assert.deepEqual(evidence[key], [], `${key} must be empty.`);
  evidence.passed = true;
  console.log(`PASS built lab (${flavor}/${preset}): ${loaded.size} actual GLBs, two engine postrenders, native pause/resume/back, no development hooks or browser errors.`);
} catch (error) {
  evidence.failedPhase = phase; evidence.error = error instanceof Error ? error.stack : String(error); process.exitCode = 1;
  if (page) {
    evidence.visibleFailure = await page.evaluate(() => Object.fromEntries(['lab-error', 'lab-loading-copy', 'lab-mode', 'lab-clock'].map(id => [id, document.getElementById(id)?.textContent ?? null]))).catch(() => null);
    await page.screenshot({ path: path.join(output, 'failure.png'), timeout: 15000 }).catch(() => {});
  }
  console.error(evidence.error);
} finally {
  for (const [name, resource] of [['context', context], ['browser', browser]]) {
    try { await resource?.close(); } catch (error) { (evidence.cleanupErrors ??= []).push({ resource: name, error: String(error) }); }
  }
  await Promise.all(responseChecks);
  if (server) { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
  if (evidence.cleanupErrors?.length) { evidence.passed = false; process.exitCode = 1; }
  if (['pageErrors', 'consoleErrors', 'requestFailures', 'httpErrors'].some(key => evidence[key].length)) { evidence.passed = false; process.exitCode = 1; }
  evidence.finishedAt = new Date().toISOString();
  await fs.mkdir(output, { recursive: true }); await fs.writeFile(path.join(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
}
