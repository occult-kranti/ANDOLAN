/* Open the reference gallery offline at desktop and phone widths. */
const { chromium } = require('playwright');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const assert = require('node:assert/strict');

(async () => {
  const root = __dirname;
  const html = path.join(root, 'gallery.html');
  const browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || undefined,
    headless: true
  });
  const observations = [];
  try {
    for (const [width, height] of [[1440, 1000], [390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height }, offline: true });
      const page = await context.newPage();
      const errors = [];
      const external = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('request', req => { if (/^https?:/i.test(req.url())) external.push(req.url()); });
      await page.goto(pathToFileURL(html).href, { waitUntil: 'load' });
      const measures = await page.evaluate(async () => {
        const photos = [...document.images];
        photos.forEach(image => { image.loading = 'eager'; });
        await Promise.all(photos.map(image => image.decode()));
        return {
          title: document.title,
          imageCount: photos.length,
          imagesLoaded: photos.every(image => image.naturalWidth > 0 && image.naturalHeight > 0),
          cardCount: document.querySelectorAll('article').length,
          docWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
          linkCount: document.querySelectorAll('article a').length,
        };
      });
      assert.equal(measures.imageCount, 8);
      assert.equal(measures.cardCount, 8);
      assert.equal(measures.imagesLoaded, true);
      assert.ok(measures.docWidth <= measures.viewportWidth);
      assert.deepEqual(errors, []);
      assert.deepEqual(external, []);
      if (width === 1440) await page.screenshot({ path: path.join(root, 'gallery-preview.png'), fullPage: true });
      observations.push({ viewport: [width, height], ...measures, externalRequests: external.length, pageErrors: errors.length });
      await context.close();
    }
  } finally {
    await browser.close();
  }
  const hash = file => createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex');
  const receipt = { result: 'pass', htmlSha256: hash('gallery.html'), screenshotSha256: hash('gallery-preview.png'), observations };
  fs.writeFileSync(path.join(root, 'gallery-verification.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log(JSON.stringify(receipt, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
