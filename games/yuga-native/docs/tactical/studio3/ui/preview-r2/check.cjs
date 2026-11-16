const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { pathToFileURL, fileURLToPath } = require('url');

(async () => {
  const output = __dirname;
  const pagePath = path.resolve(output, '../../PREVIEW.html');
  const priorPath = path.resolve(output, '../../../PREVIEW.html');
  const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  const errors = [], failedRequests = [], remoteRequests = [], checks = [];
  const browser = await chromium.launch({ headless: true, args: ['--disable-gpu', '--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
    page.on('pageerror', e => errors.push(String(e)));
    page.on('requestfailed', r => failedRequests.push({url: r.url(), error: r.failure()?.errorText}));
    page.on('request', r => { if (/^https?:/.test(r.url())) remoteRequests.push(r.url()); });
    await page.goto(pathToFileURL(pagePath).href);
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.querySelectorAll('#gallery img')].map(async img => { img.loading = 'eager'; await img.decode(); }));
    });
    await page.waitForFunction(() => document.querySelector('video').readyState >= 1);
    const state = await page.evaluate(() => ({
      images: [...document.querySelectorAll('#gallery img')].map(i => ({ path: i.src, width: i.naturalWidth, height: i.naturalHeight })),
      references: [...document.querySelectorAll('a[href],source[src],video[poster]')].map(e => e.href || e.src || new URL(e.poster, document.baseURI).href),
      video: { width: document.querySelector('video').videoWidth, height: document.querySelector('video').videoHeight, duration: document.querySelector('video').duration },
      fonts: [...document.fonts].map(f => ({ family: f.family, status: f.status })),
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth
    }));
    checks.push({ id: '13-native-images-decode', pass: state.images.length === 13 && state.images.every(i => i.width > 0 && i.height > 0) });
    const missing = state.references.filter(u => u.startsWith('file:')).filter(u => !fs.existsSync(fileURLToPath(new URL(u))));
    checks.push({ id: 'all-local-media-and-document-links-exist', pass: missing.length === 0, missing });
    checks.push({ id: 'native-film-metadata', pass: state.video.width === 1280 && state.video.height === 720 && state.video.duration === 9 });
    checks.push({ id: 'local-fonts-loaded', pass: state.fonts.length === 2 && state.fonts.every(f => f.status === 'loaded') });
    checks.push({ id: 'desktop-no-horizontal-overflow', pass: !state.horizontalOverflow });
    await page.locator('[data-filter=first]').click();
    checks.push({ id: 'first-person-filter', pass: await page.locator('.shot:visible').count() === 4 });
    await page.locator('[data-filter=all]').click();
    await page.locator('.shot button').first().click();
    await page.locator('#viewer-image').evaluate(i => i.decode());
    const opened = await page.locator('#viewer').evaluate(d => d.open);
    await page.keyboard.press('Escape');
    const returned = await page.locator('.shot button').first().evaluate(b => document.activeElement === b);
    checks.push({ id: 'open-original-lightbox-and-escape-return', pass: opened && returned });
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: path.join(output, 'desktop.png') });
    const metadataCancellations = failedRequests.filter(r => r.url.endsWith('/studio-motion.mp4') && r.error === 'net::ERR_ABORTED' && state.video.width === 1280 && state.video.height === 720 && state.video.duration === 9);
    const unexpectedFailures = failedRequests.filter(r => !metadataCancellations.includes(r));
    checks.push({ id: 'no-script-unexpected-resource-or-network-failure', pass: errors.length === 0 && unexpectedFailures.length === 0 && remoteRequests.length === 0, errors, unexpectedFailures, expectedMetadataPreloadCancellations: metadataCancellations, remoteRequests });
    const receipt = { task: 'YUGA-HERO-STUDIO3', command: 'node games/yuga-native/docs/tactical/studio3/ui/preview-r2/check.cjs', scope: 'One local Chromium path/media/desktop inspection. Native input and hardware performance are separate.', html: { path: pagePath, sha256: sha(pagePath) }, prior_gallery: { path: priorPath, sha256: sha(priorPath) }, screenshot: { path: path.join(output, 'desktop.png'), sha256: sha(path.join(output, 'desktop.png')) }, checks, media: state, passed: checks.filter(c => c.pass).length, total: checks.length };
    fs.writeFileSync(path.join(output, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
    console.log(JSON.stringify({ passed: receipt.passed, total: receipt.total, html_sha256: receipt.html.sha256, errors }));
    if (receipt.passed !== receipt.total) process.exitCode = 1;
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
