// Exercise the rendered cue in the packaged game with an ordinary keyboard cast.
import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { launchChromium, openOffline, packageUnderTest } from './browser-package.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const html = process.argv[2] ?? path.join(root, 'dist/yuga-rust.html');
const output = process.argv[3];
const game = await packageUnderTest(html);
const browser = await launchChromium();

try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, offline: true });
  const { tab, entry } = await openOffline(context, game);
  const errors = [];
  tab.on('pageerror', (error) => errors.push(String(error)));
  await tab.waitForFunction(() => window.yugaProbe?.().mode === 'ready', undefined, { timeout: 120_000 });
  await tab.locator('#hero').selectOption('hanuman');
  await tab.locator('#match').click();
  await tab.waitForFunction(() => window.yugaProbe().mode === 'playing' && window.yugaProbe().state?.army,
    undefined, { timeout: 120_000 });
  await tab.evaluate(() => {
    window.mountainReview = { flight: null, impact: null, ended: null };
    function observe() {
      const probe = window.yugaProbe();
      const cast = probe.state?.casts?.find((item) => item.id === 'mountain_pulse');
      const cue = probe.renderer?.mountainCue;
      if (cast && cue?.inFlight && !window.mountainReview.flight)
        window.mountainReview.flight = { cast, cue };
      if (cast && cue?.impactSparks && !window.mountainReview.impact)
        window.mountainReview.impact = { cast, cue };
      if (window.mountainReview.impact && !cast && cue && !cue.inFlight && !cue.impactSparks)
        window.mountainReview.ended = { tick: probe.state.tick, cue };
      if (!window.mountainReview.ended) requestAnimationFrame(observe);
    }
    requestAnimationFrame(observe);
  });
  await tab.keyboard.press('x');
  await tab.waitForFunction(() => window.mountainReview?.ended, undefined, { timeout: 120_000 });
  const observed = await tab.evaluate(() => window.mountainReview);
  assert.ok(observed.flight.cast.age_ticks >= observed.flight.cast.release_tick);
  assert.ok(observed.flight.cast.age_ticks <= observed.flight.cast.impact_tick);
  assert.ok(observed.flight.cue.renderSurfaces >= 2, 'the mountain has textured rock surfaces and an aura');
  assert.equal(observed.flight.cue.impactSparks, 0);
  assert.ok(observed.impact.cast.age_ticks >= observed.impact.cast.impact_tick);
  assert.ok(observed.impact.cast.age_ticks <= observed.impact.cast.impact_tick + 6);
  assert.equal(observed.impact.cue.inFlight, false);
  assert.equal(observed.impact.cue.impactSparks, 6);
  assert.deepEqual(errors, []);
  const report = { entry, html_sha256: game.html_sha256, zip_sha256: game.zip_sha256, observed, errors };
  if (output) await writeFile(output, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser.close();
}
