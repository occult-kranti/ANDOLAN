// Check that the illustrated face and playable controls survive both title crops.
import {
  openOffline,
  launchChromium,
  packageUnderTest,
  digest,
} from './browser-package.mjs';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const root = fileURLToPath(new URL('..', import.meta.url));
const [
  html = path.join(root, 'dist/yuga-rust.html'),
  dir = path.join(root, 'dist/hanuman-title'),
] = process.argv.slice(2);
await mkdir(dir, { recursive: true });
const game = await packageUnderTest(html),
  browser = await launchChromium(),
  context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    offline: true,
  });
try {
  const { tab } = await openOffline(context, game);
  await tab.waitForFunction(
    () => window.yugaProbe?.().mode === 'ready',
    undefined,
    { timeout: 90000 },
  );
  const results = [];
  for (const [w, h] of [
    [1280, 720],
    [390, 844],
  ]) {
    await tab.setViewportSize({ width: w, height: h });
    await tab.evaluate(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    );
    const details = await tab.evaluate(async () => {
      const image = document.querySelector('.cover'),
        style = getComputedStyle(image),
        portrait = new Image();
      portrait.src = style.backgroundImage.slice(5, -2);
      await portrait.decode();
      const elRect = (e) => {
        const r = e.getBoundingClientRect();
        return { x: r.x, y: r.y, w: r.width, h: r.height };
      };
      const card = elRect(image),
        s = Math.max(
          card.w / portrait.naturalWidth,
          card.h / portrait.naturalHeight,
        );
      // The eye in the generated title plate is at approximately 35% width and 18% height.
      const x =
        card.x +
        ((card.w - portrait.naturalWidth * s) *
          parseFloat(style.backgroundPositionX)) /
          100 +
        portrait.naturalWidth * s * 0.35;
      const y =
        card.y +
        ((card.h - portrait.naturalHeight * s) *
          parseFloat(style.backgroundPositionY)) /
          100 +
        portrait.naturalHeight * s * 0.18;
      return {
        viewport: [innerWidth, innerHeight],
        portrait: [portrait.naturalWidth, portrait.naturalHeight],
        illustratedEye: [x, y],
        controls: [...document.querySelectorAll('#match,#begin,#hero')].map(
          elRect,
        ),
        bodyWidth: document.documentElement.scrollWidth,
      };
    });
    assert.deepEqual(details.portrait, [1672, 941]);
    assert.ok(
      details.illustratedEye[0] > 0 &&
        details.illustratedEye[0] < w &&
        details.illustratedEye[1] > 0 &&
        details.illustratedEye[1] < h,
    );
    assert.ok(
      details.controls.every(
        (c) => c.x >= 0 && c.x + c.w <= w + 1 && c.y >= 0 && c.y + c.h <= h + 1,
      ),
    );
    assert.ok(
      !details.controls.some(
        (c) =>
          details.illustratedEye[0] >= c.x &&
          details.illustratedEye[0] <= c.x + c.w &&
          details.illustratedEye[1] >= c.y &&
          details.illustratedEye[1] <= c.y + c.h,
      ),
    );
    assert.ok(details.bodyWidth <= w);
    const bytes = await tab.screenshot({ path: dir + '/title-' + w + '.png' });
    results.push({ ...details, png_sha256: digest(bytes) });
  }
  await writeFile(
    dir + '/title-qa.json',
    JSON.stringify(
      {
        html_sha256: game.html_sha256,
        zip_sha256: game.zip_sha256,
        viewports: results,
      },
      null,
      2,
    ) + '\n',
  );
} finally {
  await browser.close();
}
