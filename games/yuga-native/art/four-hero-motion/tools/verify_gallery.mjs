// Test the public collection after extraction. Local assets are served from one directory only.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createReadStream, existsSync } from 'node:fs';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { chromium } from 'playwright';

const { values } = parseArgs({ options: { root: { type: 'string' }, output: { type: 'string' } } });
const root = path.resolve(values.root || fileURLToPath(new URL('../', import.meta.url)));
const evidence = path.resolve(values.output || path.join(root, 'evidence'));
const prefix = '/four-heroes/';
const mime = {
  '.js': 'application/javascript',
  '.vtt': 'text/vtt',
  '.html': 'text/html; charset=utf-8',
  '.webp': 'image/webp',
  '.png': 'image/png',
  '.mp4': 'video/mp4',
  '.md': 'text/plain; charset=utf-8',
  '.pdf': 'application/pdf',
};
const digest = (data) => createHash('sha256').update(data).digest('hex');
const report = {
  scope: 'Public gallery under a nested offline-package path. Only loopback requests allowed.',
  heroes: [],
  checks: [],
  external_requests: [],
  errors: [],
  failed_responses: [],
};
const server = createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, 'http://localhost').pathname;
    if (!pathname.startsWith(prefix)) {
      res.writeHead(404).end();
      return;
    }
    const relative = decodeURIComponent(pathname.slice(prefix.length));
    const file = path.resolve(root, relative.endsWith('/') || !relative ? relative + 'index.html' : relative);
    if (!file.startsWith(root + path.sep)) {
      res.writeHead(403).end();
      return;
    }
    const { size } = await stat(file);
    let start = 0,
      end = size - 1,
      status = 200;
    const headers = {
      'Content-Type': mime[path.extname(file)] ?? 'application/octet-stream',
      'Accept-Ranges': 'bytes',
    };
    if (req.headers.range) {
      const match = /^bytes=(\d+)-(\d*)$/.exec(req.headers.range);
      if (!match || Number(match[1]) >= size) {
        res.writeHead(416, { 'Content-Range': 'bytes */' + size }).end();
        return;
      }
      start = Number(match[1]);
      end = match[2] ? Math.min(Number(match[2]), size - 1) : size - 1;
      status = 206;
      headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
    }
    headers['Content-Length'] = end - start + 1;
    res.writeHead(status, headers);
    if (req.method === 'HEAD') res.end();
    else
      createReadStream(file, { start, end })
        .on('error', () => res.destroy())
        .pipe(res);
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}${prefix}`;
const browser = await chromium.launch({
  headless: true,
  executablePath:
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
    (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
await mkdir(evidence, { recursive: true });
const check = (ok, description) => {
  assert.ok(ok, description);
  report.checks.push(description);
  console.log(description);
};
async function open(options = {}, hash = '') {
  const page = await browser.newPage(options);
  page.setDefaultTimeout(15_000);
  page.on('pageerror', (error) => report.errors.push(error.message));
  page.on('websocket', (socket) => report.external_requests.push(socket.url()));
  page.on('response', (response) => {
    if (response.status() >= 400)
      report.failed_responses.push(`${response.status()} ${response.url().split(prefix).pop()}`);
  });
  await page.route(/^https?:\/\//, (route) => {
    const url = route.request().url();
    if (url.startsWith(base)) return route.continue();
    report.external_requests.push(url);
    return route.abort();
  });
  await page.goto(base + hash, { waitUntil: 'domcontentloaded' });
  return page;
}
async function verifyHero(page, id) {
  const name = await page.locator('#heroName').innerText();
  assert.equal(name.toLowerCase(), id);
  assert.equal(await page.locator(`[role=tab][aria-selected=true]`).getAttribute('id'), 't-' + id);
  assert.equal(await page.locator('#study').getAttribute('aria-labelledby'), 't-' + id);
  const info = await page.locator('#study img').evaluateAll(async (images) =>
    Promise.all(
      images.map(async (image) => {
        await image.decode();
        return {
          src: image.getAttribute('src'),
          width: image.naturalWidth,
          height: image.naturalHeight,
          alt: image.alt,
        };
      }),
    ),
  );
  assert.equal(info.length, 3);
  assert.ok(info.every((i) => i.width > 250 && i.height > 200 && i.alt && i.src.includes(id)));
  const rig = await page.locator('#rig').getAttribute('href'),
    script = await page.locator('#script').getAttribute('href');
  assert.equal(rig, 'viewer/index.html?hero=' + id);
  assert.equal(script, `scripts/${id}.md`);
  const scriptResponse = await page.request.get(base + script);
  assert.equal(scriptResponse.status(), 200);
  assert.match(await scriptResponse.text(), new RegExp('^# ' + id, 'i'));
  const viewerResponse = await page.request.get(base + rig);
  assert.equal(viewerResponse.status(), 200);
  assert.ok((await viewerResponse.text()).includes('<canvas'));
  const movie = page.locator('#heroFilm');
  await page.waitForFunction((id) => {
    const v = document.getElementById('heroFilm');
    return v.currentSrc.endsWith('/' + id + '.mp4') && v.readyState >= 1 && v.videoWidth > 0;
  }, id);
  const movieInfo = await movie.evaluate((v) => ({
    width: v.videoWidth,
    height: v.videoHeight,
    seconds: v.duration,
    controls: v.controls,
  }));
  assert.ok(movieInfo.controls && movieInfo.seconds > 2);
  assert.equal(await page.locator('#filmLink').getAttribute('href'), `media/video/${id}.mp4`);
  return { id, images: info, video: movieInfo, rig, script };
}
async function pressPlay(video) {
  await video.scrollIntoViewIfNeeded();
  await video.focus();
  if (!(await video.evaluate((v) => v.paused))) await video.press('Space');
  const start = await video.evaluate((v) => v.currentTime);
  await video.press('Space');
  await video.evaluate(
    (v, start) =>
      new Promise((resolve, reject) => {
        if (!v.paused && v.currentTime > start + 0.15) {
          resolve();
          return;
        }
        const stop = setTimeout(() => {
          v.removeEventListener('timeupdate', test);
          reject(Error('native play control did not advance'));
        }, 7500);
        function test() {
          if (!v.paused && v.currentTime > start + 0.15) {
            clearTimeout(stop);
            v.removeEventListener('timeupdate', test);
            resolve();
          }
        }
        v.addEventListener('timeupdate', test);
      }),
    start,
  );
}

async function chapter(page, group, videoId, title, expected) {
  await page
    .locator(group + ' button')
    .filter({ hasText: title })
    .click();
  await page.waitForFunction(
    ({ videoId, expected }) => {
      const v = document.getElementById(videoId);
      return !v.paused && !v.seeking && v.currentTime >= expected - 0.025 && v.currentTime < expected + 2.5;
    },
    { videoId, expected },
  );
  return { title, expected, actual: await page.locator('#' + videoId).evaluate((v) => v.currentTime) };
}
try {
  report.browser = browser.version();
  report.index_sha256 = digest(await readFile(path.join(root, 'index.html')));
  report.test_sha256 = digest(await readFile(fileURLToPath(import.meta.url)));
  const desktop = await open({ viewport: { width: 1366, height: 768 } });
  const book = await desktop.request.get(base + 'animator-book.pdf');
  assert.equal(book.status(), 200);
  assert.ok((await book.body()).subarray(0, 5).equals(Buffer.from('%PDF-')));
  check(true, 'both gallery navigation and the local illustrated PDF are available from a nested path');
  for (const id of ['hanuman', 'shiva', 'rama', 'krishna']) {
    await desktop.locator('#t-' + id).click();
    report.heroes.push(await verifyHero(desktop, id));
    if (id === 'hanuman') {
      await desktop.locator('#heroes').evaluate((el) => el.scrollIntoView({ block: 'start' }));
      report.desktop_png_sha256 = digest(
        await desktop.screenshot({ path: path.join(evidence, 'gallery-desktop.png') }),
      );
    }
    await pressPlay(desktop.locator('#heroFilm'));
    if (id === 'hanuman') {
      const trace = JSON.parse(await readFile(path.join(root, 'media/video/hanuman.json'), 'utf8'));
      const cue = trace.shots.find((s) => s.clip === 'tail_sweep');
      report.seeks = [
        await chapter(desktop, '#heroChapters', 'heroFilm', cue.label, cue.start_frame / trace.fps),
      ];
      check(true, 'the 3D action button plays the tail-sweep shot at its rendered start frame');
    }
  }
  check(
    true,
    'four normal tab selections display each named hero’s three original images, local script, rig link and playable motion video',
  );
  await desktop.locator('#t-krishna').focus();
  await desktop.keyboard.press('Home');
  assert.equal(await desktop.locator('#heroName').innerText(), 'Hanuman');
  await desktop.keyboard.press('ArrowRight');
  assert.equal(await desktop.locator('#heroName').innerText(), 'Shiva');
  assert.ok(desktop.url().endsWith('#hero-shiva'));
  await desktop.reload();
  await verifyHero(desktop, 'shiva');
  check(true, 'Home, arrow navigation and reloading a hero URL restore its selected tab and correct media');
  await desktop.getByRole('link', { name: 'Watch the signature moves' }).click();
  const film = desktop.locator('#signature video');
  const timeline = JSON.parse(await readFile(path.join(root, 'evidence/animatic.json'), 'utf8'));
  const krishna = timeline.timeline.find((s) => s.hero === 'krishna');
  report.seeks.push(
    await chapter(
      desktop,
      '#signatureChapters',
      'signatureFilm',
      krishna.ability,
      krishna.overview_start / timeline.fps,
    ),
  );
  check(true, 'the illustrated Krishna chapter begins playback at its recorded timeline boundary');
  await pressPlay(film);
  report.signature_seconds = await film.evaluate((v) => v.duration);
  check(
    report.signature_seconds > 10,
    'the signature link reaches the combined illustrated film and its native play control advances',
  );
  await desktop.close();
  const mobile = await open(
    { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 },
    '#hero-rama',
  );
  await verifyHero(mobile, 'rama');
  await mobile.locator('#t-krishna').tap();
  await verifyHero(mobile, 'krishna');
  const width = await mobile.evaluate(() => [innerWidth, document.documentElement.scrollWidth]);
  check(width[1] <= width[0] + 1, 'the 390-pixel gallery accepts touch and has no horizontal page overflow');
  await mobile.locator('#heroes').evaluate((el) => el.scrollIntoView({ block: 'start' }));
  report.mobile_png_sha256 = digest(
    await mobile.screenshot({ path: path.join(evidence, 'gallery-mobile.png') }),
  );
  await mobile.close();
  check(
    !report.errors.length && !report.external_requests.length && !report.failed_responses.length,
    'all gallery checks completed without external HTTP, WebSockets, missing media or page errors',
  );
  report.passed = true;
} catch (e) {
  report.passed = false;
  report.failure = String(e);
  console.error(e);
  process.exitCode = 1;
} finally {
  await writeFile(path.join(evidence, 'gallery-qa.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));
}
