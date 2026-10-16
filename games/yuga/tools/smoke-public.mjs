// Run only after a successful Pages deployment and an exclusive browser slot.
// Read-only public smoke: no dev hooks, injected game state, account, or server join.
// Usage: node games/yuga/tools/smoke-public.mjs [https://host/ANDOLAN/yuga/]
import assert from 'node:assert/strict';
import { existsSync, promises as fs } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, expect } from '@playwright/test';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const output = path.resolve(root, process.env.YUGA_SMOKE_OUTPUT || 'test-results/yuga-public');
const gameUrl = new URL(process.argv[2] || 'https://occult-kranti.github.io/ANDOLAN/yuga/');
assert.equal(gameUrl.protocol, 'https:', 'Public smoke requires HTTPS with normal certificate verification.');
assert.ok(!gameUrl.username && !gameUrl.password && !gameUrl.search && !gameUrl.hash, 'Use a plain public game URL.');
assert.ok(gameUrl.pathname.endsWith('/yuga/'), 'Expected the deployed /yuga/ mount.');
const parentUrl = new URL('../', gameUrl);
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const manifests = await Promise.all(['hero-assets.json', 'unit-assets.json'].map(async name => {
  const bytes = await fs.readFile(path.join(root, 'games/yuga/art', name));
  return { name, sha256: hash(bytes), data: JSON.parse(bytes) };
}));
const expectedModels = manifests.flatMap(manifest => manifest.data.models);
assert.equal(expectedModels.length, 21, 'Expected fourteen heroes and seven units.');
assert.equal(new Set(expectedModels.map(model => model.id)).size, 21);
await fs.mkdir(output, { recursive: true });

// Chromium does not reliably inherit HTTPS_PROXY itself. Select the inherited
// sidecar explicitly, retaining its authentication if configured. Never log it.
const inheritedProxy = process.env.HTTPS_PROXY || process.env.https_proxy || process.env.HTTP_PROXY || process.env.http_proxy;
let proxy;
if (inheritedProxy) {
  const url = new URL(inheritedProxy);
  proxy = { server: `${url.protocol}//${url.host}` };
  if (url.username) proxy.username = decodeURIComponent(url.username);
  if (url.password) proxy.password = decodeURIComponent(url.password);
}
const evidence = {
  startedAt: new Date().toISOString(), passed: false, url: gameUrl.href,
  parentUrl: parentUrl.href, manifests: manifests.map(({ name, sha256 }) => ({ name, sha256 })),
  transport: { inheritedProxySelected: !!proxy, tlsVerification: true },
  models: [], pageErrors: [], consoleErrors: [], requestFailures: [], httpErrors: [],
  scope: 'Production static Pages game and local practice, including native Rama match → leave → Arjuna gallery → close → new Arjuna match. Ordinary sequential UI events do not force the separately tested synchronous gallery-disposal race. No public WSS endpoint is configured or claimed.',
};
let browser, context, page;
try {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, headless: true, proxy,
    args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  page = await context.newPage();
  page.setDefaultTimeout(45000);
  let phase = 'yuga';
  page.on('pageerror', error => evidence.pageErrors.push({ phase, message: error.message }));
  page.on('console', message => { if (message.type() === 'error') evidence.consoleErrors.push({ phase, message: message.text() }); });
  page.on('requestfailed', request => evidence.requestFailures.push({ phase, url: request.url(), error: request.failure()?.errorText }));
  const responseChecks = [];
  page.on('response', response => {
    if (response.status() >= 400) evidence.httpErrors.push({ phase, url: response.url(), status: response.status() });
    if (!new URL(response.url()).pathname.endsWith('.glb')) return;
    responseChecks.push((async () => {
      const model = { url: response.url(), status: response.status(), contentType: response.headers()['content-type'] };
      evidence.models.push(model);
      try {
        const body = await response.body();
        model.bytes = body.length; model.magic = body.subarray(0, 4).toString('ascii'); model.sha256 = hash(body);
      } catch (error) { model.error = String(error); }
    })());
  });
  const response = await page.goto(gameUrl.href, { waitUntil: 'domcontentloaded', timeout: 90000 });
  assert.equal(response?.status(), 200, 'Public game document must load.');
  evidence.document = { status: response.status(), url: response.url(), sha256: hash(await response.body()) };
  await expect(page.locator('[data-hero]')).toHaveCount(14);
  assert.equal(await page.evaluate(() => Object.hasOwn(window, '__YUGA')), false, 'Public build must omit development hooks.');
  await page.locator('[data-hero="rama"]').click();
  await expect(page.locator('[data-hero="rama"]')).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#hero-name')).toHaveText('Rama');
  await page.screenshot({ path: path.join(output, 'public-roster.png') });
  await page.locator('#practice-play').click();
  await expect(page.locator('#loading')).toBeHidden({ timeout: 150000 });
  await expect(page.locator('#hud')).toBeVisible();
  await expect(page.locator('#status-line')).toContainText('Practice');
  await expect(page.locator('#global-error')).toBeHidden();
  await expect(page.locator('#hero-hudname')).toHaveText(/^Rama · (SUN|MOON)$/);
  await expect(page.locator('#ability-0 .ability-time')).toHaveText('READY');
  await page.locator('#arena').focus();
  await page.keyboard.press('KeyQ');
  await expect(page.locator('#ability-0 .ability-time')).toHaveText(/^\d+s$/);
  evidence.qCooldown = await page.locator('#ability-0 .ability-time').textContent();
  evidence.hero = await page.locator('#hero-hudname').textContent();
  await page.screenshot({ path: path.join(output, 'public-practice.png') });
  // Reuse the existing arena app after a second gallery is created/destroyed.
  // Every action is native UI input; no dev hooks or synchronous DOM fixture.
  phase = 'yuga-gallery-restart';
  await page.keyboard.press('Escape');
  await expect(page.locator('#pause-dialog')).toBeVisible();
  await page.locator('#leave-game').click();
  await expect(page.locator('#lobby')).toBeVisible();
  await expect(page.locator('#hud')).toBeHidden();
  await page.locator('[data-hero="arjuna"]').click();
  await expect(page.locator('[data-hero="arjuna"]')).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#hero-name')).toHaveText('Arjuna');
  await page.locator('#inspect-hero').click();
  await expect(page.locator('#hero-dialog')).toBeVisible();
  await expect(page.locator('#showcase-name')).toHaveText('Arjuna');
  await expect(page.locator('#showcase-status')).toContainText('Drag to rotate', { timeout: 90000 });
  await expect(page.locator('#showcase-actions [data-clip="idle"]')).toBeEnabled();
  evidence.galleryRestart = { galleryHero: await page.locator('#showcase-name').textContent(), galleryStatus: await page.locator('#showcase-status').textContent(), input: 'Native sequential Settings/Leave, hero selection, gallery open/close, Practice and keyboard Q; no state injection or forced synchronous race.' };
  await page.screenshot({ path: path.join(output, 'public-arjuna-gallery.png') });
  await page.locator('#hero-dialog [data-close]').click();
  await expect(page.locator('#hero-dialog')).toBeHidden();
  await page.locator('#practice-play').click();
  await expect(page.locator('#loading')).toBeHidden({ timeout: 150000 });
  await expect(page.locator('#hud')).toBeVisible();
  await expect(page.locator('#status-line')).toContainText('Practice');
  await expect(page.locator('#global-error')).toBeHidden();
  await expect(page.locator('#hero-hudname')).toHaveText(/^Arjuna · (SUN|MOON)$/);
  await expect(page.locator('#ability-0 .ability-time')).toHaveText('READY');
  await page.locator('#arena').focus();
  await page.keyboard.press('KeyQ');
  await expect(page.locator('#ability-0 .ability-time')).toHaveText(/^\d+s$/);
  evidence.galleryRestart.matchHero = await page.locator('#hero-hudname').textContent();
  evidence.galleryRestart.qCooldown = await page.locator('#ability-0 .ability-time').textContent();
  evidence.galleryRestart.passed = true;
  await page.screenshot({ path: path.join(output, 'public-arjuna-practice.png') });
  await Promise.all(responseChecks);
  for (const model of evidence.models) {
    assert.equal(model.status, 200, `GLB HTTP failure: ${model.url}`);
    assert.equal(model.magic, 'glTF', `Response is not a binary glTF: ${model.url}`);
    const filename = path.basename(new URL(model.url).pathname);
    const expected = expectedModels.find(candidate => filename === `${candidate.id}.glb` || filename.startsWith(`${candidate.id}-`));
    assert.ok(expected, `Unexpected deployed model: ${filename}`);
    model.id = expected.id;
    assert.equal(model.sha256, expected.sha256, `Deployed ${expected.id} differs from the current asset manifest.`);
  }
  assert.equal(new Set(evidence.models.map(model => model.id)).size, 21, 'All twenty-one actual model responses are required.');
  assert.equal(await page.evaluate(() => Object.hasOwn(window, '__YUGA')), false);
  evidence.yugaPassed = true;
  // Same browser, sequential page: leaving gameplay also verifies normal teardown.
  phase = 'andolan-parent';
  const parent = await page.goto(parentUrl.href, { waitUntil: 'domcontentloaded', timeout: 90000 });
  assert.equal(parent?.status(), 200, 'Original ANDOLAN document must remain available.');
  await expect(page.locator('#title h1')).toHaveText('ANDOLAN');
  await expect(page.locator('#play-practice')).toBeVisible();
  await expect(page.locator('#practice-play')).toHaveCount(0);
  evidence.parent = { status: parent.status(), url: parent.url(), title: await page.title(), heading: await page.locator('#title h1').textContent() };
  await page.screenshot({ path: path.join(output, 'public-parent-andolan.png') });
  assert.deepEqual(evidence.pageErrors, [], 'Public JavaScript raised an error.');
  assert.deepEqual(evidence.consoleErrors, [], 'Public console reported an error.');
  assert.deepEqual(evidence.requestFailures, [], 'Public requests failed.');
  assert.deepEqual(evidence.httpErrors, [], 'Public responses returned HTTP errors.');
  evidence.passed = true;
  console.log('PASS public Pages: twenty-one matching binary GLBs, native Rama practice/Q and Arjuna gallery-close/practice/Q flow, no development hook, and original ANDOLAN parent page.');
} catch (error) {
  evidence.error = error instanceof Error ? error.stack : String(error);
  await page?.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
  console.error(evidence.error);
  process.exitCode = 1;
} finally {
  await context?.close(); await browser?.close();
  evidence.finishedAt = new Date().toISOString();
  await fs.writeFile(path.join(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
}
