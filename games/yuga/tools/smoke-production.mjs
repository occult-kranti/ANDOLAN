// Usage: npm run yuga:build && node games/yuga/tools/smoke-production.mjs
// Exercises built output only. The /yuga/ mount rewrites its prefix, never asset filenames.
import assert from 'node:assert/strict';
import { existsSync, promises as fs } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium, expect } from '@playwright/test';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const output = path.join(root, 'test-results/yuga-production');
const built = path.join(root, 'dist/yuga');
const serverFile = path.join(root, 'dist/yuga-server/games/yuga/server/server.js');
const heroesFile = path.join(root, 'dist/yuga-server/games/yuga/shared/heroes.js');
for (const filename of [path.join(built, 'index.html'), serverFile, heroesFile]) {
  assert.ok(existsSync(filename), `Missing ${filename}. Run npm run yuga:build first.`);
}
await fs.mkdir(output, { recursive: true });
const { createArenaServer } = await import(pathToFileURL(serverFile).href);
const { HEROES } = await import(pathToFileURL(heroesFile).href);
assert.equal(HEROES.length, 14, 'Update the production gate deliberately if the roster changes.');
const unitIds = ['soldier', 'city-watch', 'minister', 'king', 'yaksha', 'naga', 'sky-sentinel'];
const evidence = { startedAt: new Date().toISOString(), passed: false, build: {}, runs: [] };
for (const filename of [path.join(built, 'index.html'), serverFile]) {
  evidence.build[path.relative(root, filename)] = createHash('sha256').update(await fs.readFile(filename)).digest('hex');
}
let server, browser, context, page;
try {
  server = await createArenaServer({ host: '127.0.0.1', port: 0, staticDir: built });
  server.http.prependListener('request', request => {
    if (request.url?.startsWith('/yuga/')) request.url = request.url.slice('/yuga'.length);
  });
  const base = `http://127.0.0.1:${server.address.port}`;
  evidence.base = base;
  evidence.nestedMount = 'Harness strips /yuga only; identical built files and asset paths.';
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  for (const [name, prefix, hero] of [['root', '/', 'rama'], ['nested', '/yuga/', 'sita']]) {
    const run = { name, url: base + prefix, hero, models: [], pageErrors: [], requestFailures: [], clips: [], passed: false };
    evidence.runs.push(run);
    context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    page = await context.newPage();
    page.setDefaultTimeout(30000);
    page.on('pageerror', error => run.pageErrors.push(error.message));
    page.on('requestfailed', request => run.requestFailures.push({ url: request.url(), error: request.failure()?.errorText }));
    const responseChecks = [];
    page.on('response', response => {
      if (!new URL(response.url()).pathname.endsWith('.glb')) return;
      responseChecks.push((async () => {
        const model = { url: response.url(), status: response.status(), contentType: response.headers()['content-type'] };
        run.models.push(model);
        try { const body = await response.body(); model.bytes = body.length; model.magic = body.subarray(0, 4).toString('ascii'); }
        catch (error) { model.error = String(error); }
      })());
    });
    await page.goto(run.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    assert.equal(await page.evaluate(() => Object.hasOwn(window, '__YUGA')), false, 'Production must omit development hooks.');
    await expect(page.locator('[data-hero]')).toHaveCount(14);
    await page.locator(`[data-hero="${hero}"]`).click();
    await page.locator('#inspect-hero').click();
    await expect(page.locator('#hero-dialog')).toBeVisible();
    await expect(page.locator('#showcase-status')).toContainText('Drag to rotate', { timeout: 60000 });
    for (const clip of ['run', 'fire', 'cast1', 'cast2', 'cast3', 'jump', 'idle']) {
      const button = page.locator(`[data-clip="${clip}"]`);
      await expect(button).toBeEnabled();
      await button.click();
      await expect(button).toHaveAttribute('aria-pressed', 'true');
      run.clips.push(clip);
    }
    await page.screenshot({ path: path.join(output, `gallery-${name}.png`) });
    await page.locator('#hero-dialog [data-close]').click();
    await page.locator('#practice-play').click();
    await expect(page.locator('#hud')).toBeVisible({ timeout: 90000 });
    await expect(page.locator('#loading')).toBeHidden({ timeout: 90000 });
    await expect(page.locator('#status-line')).toContainText('Practice', { timeout: 90000 });
    await expect(page.locator('#global-error')).toBeHidden();
    await expect(page.locator('#ability-0 .ability-time')).toHaveText('READY');
    await page.locator('#arena').focus();
    await page.keyboard.press('KeyQ');
    await expect(page.locator('#ability-0 .ability-time')).toHaveText(/^\d+s$/);
    run.qCooldown = await page.locator('#ability-0 .ability-time').textContent();
    await page.screenshot({ path: path.join(output, `arena-${name}.png`) });
    await Promise.all(responseChecks);
    for (const model of run.models) {
      assert.equal(model.status, 200, `GLB failed: ${model.url}`);
      assert.equal(model.magic, 'glTF', `Response is not a binary glTF: ${model.url}`);
      assert.ok(model.bytes > 12, `Empty GLB: ${model.url}`);
    }
    for (const id of [...HEROES.map(hero => hero.id), ...unitIds]) {
      assert.ok(run.models.some(model => { const filename = path.basename(new URL(model.url).pathname); return filename === `${id}.glb` || filename.startsWith(`${id}-`); }), `Missing actual ${id} GLB response at ${prefix}`);
    }
    assert.equal(new Set(run.models.map(model => model.url)).size, 21, 'Expected fourteen hero and seven unit model URLs.');
    assert.deepEqual(run.pageErrors, [], 'Production JavaScript raised page errors.');
    assert.deepEqual(run.requestFailures, [], 'Production requests failed.');
    assert.equal(await page.evaluate(() => Object.hasOwn(window, '__YUGA')), false);
    run.passed = true;
    await context.close(); context = undefined; page = undefined;
    console.log(`PASS ${name}: twenty-one binary GLBs, gallery clips, Practice HUD and Q cooldown.`);
  }
  evidence.passed = true;
} catch (error) {
  evidence.error = error instanceof Error ? error.stack : String(error);
  if (page) await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {});
  console.error(evidence.error);
  process.exitCode = 1;
} finally {
  await context?.close();
  await browser?.close();
  await server?.close();
  evidence.finishedAt = new Date().toISOString();
  await fs.writeFile(path.join(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
}
