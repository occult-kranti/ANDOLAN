// Exercise the extracted package in one offline Chromium window; this is not a network or GPU benchmark.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { launchChromium, openOffline } from './browser-package.mjs';

const [directory, reportFile, screenshotFile] = process.argv.slice(2);
if (!directory || !reportFile || !screenshotFile)
  throw Error('Usage: node test_vanara_browser.mjs extracted-directory report.json screenshot.png');

const root = path.resolve(directory);
const html = path.join(root, 'yuga-rust.html');
const bytes = await readFile(html);
const sha = (data) => createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(await readFile(path.join(root, 'build.json'), 'utf8'));
assert.equal(sha(bytes), manifest.html_sha256, 'extracted HTML must match the package manifest');
const game = { html, bytes, html_sha256: sha(bytes) };
await Promise.all([mkdir(path.dirname(path.resolve(reportFile)), { recursive: true }),
  mkdir(path.dirname(path.resolve(screenshotFile)), { recursive: true })]);

const browser = await launchChromium();
const context = await browser.newContext({ viewport: { width: 1100, height: 720 }, offline: true });
const report = { result: 'fail', scope: 'one offline Chromium practice with software rendering; no online clients',
  html_sha256: game.html_sha256, browser: browser.version(), page_errors: [] };
let page;
try {
  ({ tab: page } = await openOffline(context, game));
  page.on('pageerror', (error) => report.page_errors.push(String(error)));
  await page.waitForFunction(() => window.yugaProbe?.().mode === 'ready', null, { timeout: 120000 });
  await page.locator('#hero').selectOption('hanuman');
  await page.locator('#begin').click();
  await page.waitForFunction(() => {
    const p = window.yugaProbe?.();
    return p?.mode === 'playing' && p.state?.abilities?.length === 6 && p.renderer?.frames > 3;
  }, null, { timeout: 120000 });
  assert.equal(await page.locator('#actions .slot').count(), 6);
  assert.match(await page.locator('#actions .slot').nth(5).innerText(), /V/);
  assert.equal(await page.locator('#actions .slot').nth(5).getAttribute('aria-keyshortcuts'), 'V');

  const screen = await page.evaluate(() => window.yugaProbe().renderer.targetScreens.find((t) => t.id === 3 && t.alive));
  assert.ok(screen?.inView, 'front practice guard should be visible');
  await page.locator('#actions .slot').nth(5).click();
  await page.mouse.move(screen.x, screen.y);
  await page.waitForFunction(() => {
    const p = window.yugaProbe();
    return p.input.armedSlot === 5 && p.input.groundAim?.ready && p.renderer.groundTargeting?.radius === 3;
  }, null, { timeout: 30000 });
  report.targeting = await page.evaluate(() => window.yugaProbe().renderer.groundTargeting);
  await page.mouse.click(screen.x, screen.y);
  await page.waitForFunction(() => {
    const p = window.yugaProbe();
    return p.renderer.senaCue?.visibleSpirits === 5 &&
      p.state.events.some((e) => e.id === 'vanara_sena' && e.kind === 'impact');
  }, null, { timeout: 60000 });
  const active = await page.evaluate(() => window.yugaProbe());
  report.visible_spirits = active.renderer.senaCue.visibleSpirits;
  report.impact = active.state.events.filter((e) => e.id === 'vanara_sena' && e.kind === 'impact').at(-1);
  assert.ok(report.impact.receipts.some((receipt) => receipt.unit === 3 && receipt.damage === 12),
    'the authority applies the initial hit to the selected guard');
  await page.screenshot({ path: screenshotFile, timeout: 90000 });
  report.screenshot_sha256 = sha(await readFile(screenshotFile));
  await page.waitForFunction(() => {
    const p = window.yugaProbe();
    return p.renderer.senaCue?.visibleSpirits === 0 && !p.renderer.visibleCasts.includes('vanara_sena');
  }, null, { timeout: 60000 });
  report.expired = true;

  // Restart through the ordinary UI and verify the actual keyboard shortcut.
  await page.keyboard.press('Escape');
  await page.locator('#reset').click();
  await page.waitForFunction(() => window.yugaProbe()?.mode === 'playing', null, { timeout: 30000 });
  const keyTarget = await page.evaluate(() => window.yugaProbe().renderer.targetScreens.find((t) => t.id === 3 && t.alive));
  assert.ok(keyTarget?.inView, 'guard should remain visible after restart');
  await page.mouse.move(keyTarget.x + 1, keyTarget.y + 1);
  await page.keyboard.press('v');
  await page.waitForFunction(() => window.yugaProbe().state.events.some((e) =>
    e.id === 'vanara_sena' && e.kind === 'begin'), null, { timeout: 30000 });
  report.keyboard_cast = true;

  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(500);
  report.compact_buttons = await page.locator('#actions .slot').evaluateAll((buttons) => buttons.map((button) => {
    const r = button.getBoundingClientRect();
    return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, label: button.getAttribute('aria-label') };
  }));
  assert.equal(report.compact_buttons.length, 6);
  assert.ok(report.compact_buttons.every((r) => r.left >= 0 && r.right <= 390 && r.top >= 0 && r.bottom <= 844 &&
    r.bottom - r.top >= 44 && r.label?.includes('·')), 'six accessible controls fit the portrait viewport');
  assert.deepEqual(report.page_errors, []);
  report.result = 'pass';
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.failure = String(error);
  console.error(error);
  process.exitCode = 1;
} finally {
  await writeFile(reportFile, JSON.stringify(report, null, 2) + '\n');
  await context.close();
  await browser.close();
}
