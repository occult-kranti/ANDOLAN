// Exercise the generated catalog as a public offline document. No catalog state is injected.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('../', import.meta.url));
const { values } = parseArgs({
  options: {
    html: { type: 'string', default: path.join(root, 'library.html') },
    output: { type: 'string', default: path.join(root, 'evidence') },
  },
});
const html = await readFile(values.html);
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const evidence = {
  html_sha256: sha(html),
  html_bytes: html.length,
  test_sha256: sha(await readFile(fileURLToPath(import.meta.url))),
  scope: 'Generated standalone catalog, desktop keyboard and mobile touch after disconnection',
  checks: [],
  filters: [],
  unexpected_requests: [],
  page_errors: [],
  source_links: [],
};
await mkdir(values.output, { recursive: true });
const server = createServer((req, res) => {
  if (req.url !== '/library.html' || req.method !== 'GET') {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': html.length });
  res.end(html);
});
await new Promise((resolve, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolve));
const url = 'http://127.0.0.1:' + server.address().port + '/library.html';
const executablePath =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
  (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
const browser = await chromium.launch({
  headless: true,
  executablePath,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
const check = (ok, msg) => {
  assert.ok(ok, msg);
  evidence.checks.push(msg);
  console.log(msg);
};
const records = (page) => page.locator('#results > li .record');
const normalized = (s) => s.trim().replace(/\s+/g, ' ');
const caption = async (page) => normalized(await page.locator('#result-count').textContent());
const first = async (page) => normalized(await records(page).first().innerText());

async function open(context, hash = '') {
  const page = await context.newPage();
  page.setDefaultTimeout(15_000);
  page.on('pageerror', (error) => evidence.page_errors.push(error.message));
  page.on('websocket', (ws) => evidence.unexpected_requests.push(ws.url()));
  await page.route(/^https?:\/\//, (route) => {
    if (route.request().isNavigationRequest() && route.request().url().split('#')[0] === url)
      return route.continue();
    evidence.unexpected_requests.push(route.request().url());
    return route.abort();
  });
  await context.setOffline(false);
  await page.goto(url + hash, { waitUntil: 'domcontentloaded', timeout: 120_000 });
  await context.setOffline(true);
  assert.ok(await page.evaluate(() => !navigator.onLine));
  await records(page).first().waitFor({ state: 'attached', timeout: 60_000 });
  return page;
}

async function verifyFilter(page, id) {
  const all = await caption(page);
  const box = page.locator('#' + id);
  const options = await box
    .locator('option')
    .evaluateAll((options) => options.map((o) => ({ value: o.value, label: o.textContent.trim() })));
  assert.ok(options.length >= 2, id + ' offers actual populated choices');
  const old = await box.inputValue(),
    sample = options.find((o) => o.value !== old && o.value.trim());
  assert.ok(sample);
  await box.selectOption(sample.value);
  await page.waitForFunction(
    ({ id, v }) => document.getElementById(id).value === v && document.querySelector('#results > li .record'),
    { id, v: sample.value },
  );
  const filtered = await caption(page);
  assert.notEqual(filtered, all, id + ' changed the number of matched resources');
  const expected = await page.evaluate(
    ({ field, value }) => {
      const library = JSON.parse(document.querySelector('#resource-data').textContent);
      const records = field.startsWith('asset-')
        ? library.assets
        : ['kind', 'language'].includes(field)
          ? library.projects
          : library.elements;
      return records.filter((record) => {
        const key = field.replace(/^asset-/, '');
        const raw = field === 'language' && record.languages?.length ? record.languages : record[key];
        const choices = Array.isArray(raw)
          ? raw
          : field === 'language'
            ? String(raw ?? '')
                .split(',')
                .map((v) => v.trim())
            : [raw];
        return choices.includes(value);
      }).length;
    },
    { field: id, value: sample.value },
  );
  assert.equal(
    Number(filtered.match(/[\d,]+/)[0].replaceAll(',', '')),
    expected,
    'displayed filter count matches the archived records for ' + id,
  );
  evidence.filters.push({ id, selection: sample.label, filtered, expected, all });
  await box.selectOption(old);
  await page.waitForFunction(
    (text) => document.getElementById('result-count').textContent.trim().replace(/\s+/g, ' ') === text,
    all,
  );
}

async function openDetail(page) {
  const row = records(page).first();
  await row.focus();
  await page.keyboard.press('Enter');
  await page.locator('#detail').waitFor({ state: 'visible' });
  const title = normalized(await page.locator('#detail-title').innerText());
  const hash = await page.evaluate(() => location.hash);
  const links = await page
    .locator('#detail a[href]')
    .evaluateAll((as) => [...new Set(as.map((a) => a.href).filter((h) => /^https?:\/\//.test(h)))]);
  assert.ok(title && hash && links.length > 0, 'detail exposes a title, deep link and source');
  return { title, hash, links };
}

async function assets(page) {
  await page.locator('#assets-tab').click();
  await page.locator('#results a[href^="#asset/"]').first().waitFor();
  evidence.assets_at_start = await caption(page);
  for (const id of ['asset-kind', 'asset-license']) await verifyFilter(page, id);
  check(true, 'art file type and license filters count the exact source records');
  const selected = await page.evaluate(() => {
    const assets = JSON.parse(document.querySelector('#resource-data').textContent).assets;
    const model = assets.find(
      (a) => a.kind === '3D model' && a.counts?.skins > 0 && a.clips?.some((c) => typeof c === 'string' && c),
    );
    const icon = assets.find((a) => a.kind === 'Icon' && a.preview_data && a.evidence === 'svg-inspected');
    return [model, icon].map((a) => ({
      id: a.id,
      name: a.name,
      kind: a.kind,
      source: a.source_url,
      license: a.license,
      clips: a.clips?.filter((c) => typeof c === 'string' && c),
      counts: a.counts,
      paths: a.paths,
    }));
  });
  evidence.assets = [];
  for (const asset of selected) {
    await page.locator('#asset-kind').selectOption(asset.kind);
    await page.locator('#search').fill(asset.name);
    const hash = '#asset/' + encodeURIComponent(asset.id);
    const exact = page.locator('#results a[href="' + hash + '"]');
    await exact.waitFor();
    await exact.focus();
    await page.keyboard.press('Enter');
    await page.locator('#detail').waitFor();
    const title = normalized(await page.locator('#detail-title').innerText());
    const body = page.locator('#detail-body');
    const bodyText = await body.innerText();
    const anchors = await body.locator('a[href^="http"]').evaluateAll((as) =>
      as.map((a) => ({
        href: a.href,
        protected:
          a.target === '_blank' && a.relList.contains('noopener') && a.relList.contains('noreferrer'),
      })),
    );
    const links = anchors.map((a) => a.href);
    assert.ok(anchors.every((a) => a.protected));
    assert.equal(title, asset.name);
    assert.ok(links.includes(asset.source));
    assert.ok(bodyText.includes(asset.license));
    if (asset.kind === '3D model') {
      const pairs = await body
        .locator('dt')
        .evaluateAll((ds) =>
          Object.fromEntries(
            ds.map((d) => [d.textContent.trim().toLowerCase(), d.nextElementSibling.textContent.trim()]),
          ),
        );
      for (const key of ['meshes', 'joints', 'animations'])
        assert.equal(Number(pairs[key].replaceAll(',', '')), asset.counts[key]);
      assert.ok(asset.clips.every((clip) => pairs['animation clips'].includes(clip)));
      check(
        true,
        'a rigged glTF model exposes the source descriptor’s mesh, joint, animation counts and named clips offline',
      );
    } else {
      const img = body.locator('img');
      await img.scrollIntoViewIfNeeded();
      await img.evaluate((el) => el.decode());
      const info = await img.evaluate((el) => ({
        embedded: el.currentSrc.startsWith('data:image/webp;base64,'),
        width: el.naturalWidth,
        height: el.naturalHeight,
      }));
      assert.ok(info.embedded && info.width > 0 && info.height > 0 && /vector contents/i.test(bodyText));
      check(
        true,
        'an inspected SVG has a decoded local thumbnail, artist rights and a revision-pinned source link',
      );
    }
    evidence.assets.push({ title, hash, kind: asset.kind, source: asset.source });
    await page.keyboard.press('Escape');
    await page.locator('#detail').waitFor({ state: 'hidden' });
    await page.locator('#search').fill('');
  }
  await page.locator('#asset-kind').selectOption('Icon');
  await page.locator('#results.contact-sheet .record img').first().waitFor();
  const thumbnails = await page.locator('#results.contact-sheet .record img').evaluateAll(async (images) => {
    await Promise.all(images.map((image) => image.decode()));
    return images.filter((image) => image.naturalWidth > 0 && image.src.startsWith('data:image/')).length;
  });
  check(thumbnails >= 10, 'the icon contact sheet displays multiple decoded offline previews together');
  await page.evaluate(() => scrollTo(0, 0));
  const sheet = path.join(values.output, 'library-assets.png');
  await page.screenshot({ path: sheet });
  evidence.asset_sheet_png_sha256 = sha(await readFile(sheet));
}

async function search(page) {
  for (const query of ['OpenMW', 'Blender', 'Godot', 'OpenRA', 'Bevy', 'Quake']) {
    await page.locator('#search').fill(query);
    await page.waitForTimeout(180);
    const items = records(page);
    if (!(await items.count())) continue;
    const hits = await items.allInnerTexts();
    if (hits.some((t) => t.toLowerCase().includes(query.toLowerCase()) && !/\byuga\b/i.test(t)))
      return { query, hits: hits.length, caption: await caption(page) };
  }
  throw Error('No externally named resource appeared in search');
}

async function buttonStates(page) {
  const samples = await page.evaluate(() => {
    const { elements, buttonSheet } = JSON.parse(document.querySelector('#resource-data').textContent);
    return {
      label: buttonSheet.label,
      credits: buttonSheet.credits,
      related: elements.find((el) => buttonSheet.ids.includes(el.id)),
      unrelated: elements.find((el) => !buttonSheet.ids.includes(el.id)),
      count: buttonSheet.ids.length,
    };
  });
  for (const [record, expectSheet] of [
    [samples.related, true],
    [samples.unrelated, false],
  ]) {
    await page.locator('#search').fill(record.name);
    await page.locator('#results a[href="#element/' + encodeURIComponent(record.id) + '"]').click();
    const figure = page.locator('#detail-body figure.button-sheet');
    if (expectSheet) {
      await figure.waitFor();
      const image = figure.locator('img[alt]');
      await image.scrollIntoViewIfNeeded();
      await image.evaluate((img) => img.decode());
      const dimensions = await image.evaluate((img) => [img.naturalWidth, img.naturalHeight]);
      const embeddedHash = await image.evaluate(async (img) => {
        const bytes = Uint8Array.from(atob(img.currentSrc.split(',')[1]), (c) => c.charCodeAt(0));
        const hash = await crypto.subtle.digest('SHA-256', bytes);
        return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
      });
      const reference = await readFile(path.join(root, 'evidence', 'button-state-contact-sheet.png'));
      const caption = normalized(await figure.locator('figcaption').innerText());
      assert.deepEqual(dimensions, [reference.readUInt32BE(16), reference.readUInt32BE(20)]);
      assert.equal(embeddedHash, sha(reference));
      assert.equal(await image.getAttribute('alt'), samples.label);
      assert.equal(caption, normalized(samples.credits));
      const [download] = await Promise.all([
        page.waitForEvent('download'),
        figure.getByRole('link', { name: 'Save full-size sheet' }).click(),
      ]);
      assert.match(download.suggestedFilename(), /\.png$/i);
      check(
        sha(await readFile(await download.path())) === embeddedHash,
        'a physical click saves the original full-resolution button sheet without a network connection',
      );
      evidence.button_states = {
        record: record.id,
        dimensions,
        png_sha256: embeddedHash,
        download_filename: download.suggestedFilename(),
        caption,
        linked_records: samples.count,
      };
    } else {
      assert.equal(await figure.count(), 0);
    }
    await page.keyboard.press('Escape');
    await page.locator('#detail').waitFor({ state: 'hidden' });
  }
  check(
    true,
    'a linked button states record shows the credited offline sheet and an unrelated entry clears it',
  );
}

async function desktop() {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  try {
    const page = await open(context);
    evidence.elements_at_start = await caption(page);
    const firstPage = await first(page);
    await page.locator('#next').click();
    assert.notEqual(await first(page), firstPage);
    await page.locator('#prev').click();
    assert.equal(await first(page), firstPage);
    check(true, 'desktop pagination advances real records and returns to the original first entry');
    for (const id of ['category', 'stack', 'use']) await verifyFilter(page, id);
    check(true, 'category, stack and intended use narrow the element catalog independently');
    await page.keyboard.press('/');
    check(
      await page.locator('#search').evaluate((e) => e === document.activeElement),
      'slash focuses catalog search',
    );
    evidence.verified_search = await search(page);
    check(true, 'a game-development query finds a named resource outside YUGA');
    await page.locator('#search').fill('zz-oort-needle-no-matching-records');
    await page.locator('#empty').waitFor();
    check((await records(page).count()) === 0, 'unmatched search displays an empty state');
    await page.locator('#reset').click();
    await records(page).first().waitFor();
    check(
      (await page.locator('#search').inputValue()) === '' &&
        (await caption(page)) === evidence.elements_at_start,
      'reset restores every verified element',
    );
    const shot = path.join(values.output, 'library-desktop.png');
    await page.screenshot({ path: shot });
    evidence.desktop_png_sha256 = sha(await readFile(shot));
    const detail = await openDetail(page);
    check(
      detail.hash.startsWith('#element/'),
      'keyboard opens an individually addressable element and its source links',
    );
    const direct = await page.evaluate((hash) => {
      const el = JSON.parse(document.querySelector('#resource-data').textContent).elements.find(
        (r) => r.id === decodeURIComponent(hash.split('/')[1]),
      );
      return { name: el.name, source: el.source_url };
    }, detail.hash);
    check(
      detail.title === direct.name &&
        detail.links.includes(direct.source) &&
        /\/blob\/[a-f0-9]{40}\//.test(direct.source),
      'element detail exposes the exact revision-pinned source stored for that record',
    );
    evidence.source_links = detail.links;
    evidence.element = { title: detail.title, hash: detail.hash };
    await page.keyboard.press('Escape');
    await page.locator('#detail').waitFor({ state: 'hidden' });
    check(
      await records(page)
        .first()
        .evaluate((e) => e === document.activeElement || e.contains(document.activeElement)),
      'Escape closes the detail and restores keyboard focus to the invoking result',
    );
    const deep = await open(context, detail.hash);
    await deep.locator('#detail').waitFor();
    const reloaded = normalized(await deep.locator('#detail-title').innerText());
    const reloadedLinks = await deep.locator('#detail a[href]').evaluateAll((as) => as.map((a) => a.href));
    check(
      reloaded === detail.title && detail.links.every((link) => reloadedLinks.includes(link)),
      'opening a saved element link restores its record and source URLs',
    );
    await deep.close();
    await buttonStates(page);
    await page.locator('#projects-tab').click();
    await page.locator('#results a[href^="#project/"]').first().waitFor();
    evidence.projects_at_start = await caption(page);
    for (const id of ['kind', 'language']) await verifyFilter(page, id);
    check(true, 'project discovery has its own working kind and language filters');
    evidence.project_search = await search(page);
    const project = await openDetail(page);
    check(
      project.hash.startsWith('#project/') && project.links.length > 0,
      'a named discovery project opens its own permalink and source',
    );
    evidence.project = { title: project.title, hash: project.hash, links: project.links };
    await page.keyboard.press('Escape');
    await assets(page);
  } finally {
    await context.close();
  }
}

async function mobile() {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    isMobile: true,
    hasTouch: true,
  });
  try {
    const page = await open(context);
    const shot = path.join(values.output, 'library-mobile.png');
    await page.screenshot({ path: shot });
    evidence.mobile_png_sha256 = sha(await readFile(shot));
    await page.locator('#projects-tab').tap();
    await page.locator('#results a[href^="#project/"]').first().waitFor();
    await page.locator('#elements-tab').tap();
    await page.locator('#results a[href^="#element/"]').first().waitFor();
    const layout = await page.evaluate(() => ({
      viewport: innerWidth,
      page: document.documentElement.scrollWidth,
    }));
    check(
      layout.page <= layout.viewport + 1,
      '390-pixel touch layout fits the viewport without horizontal page scrolling',
    );
    await records(page).first().tap();
    await page.locator('#detail').waitFor();
    const rect = await page.locator('#detail').boundingBox();
    check(
      rect && rect.x >= -1 && rect.x + rect.width <= 391,
      'touch opens a detail dialog within the phone viewport',
    );
    await page.locator('#close-detail').tap();
    await page.locator('#detail').waitFor({ state: 'hidden' });
  } finally {
    await context.close();
  }
}

try {
  evidence.browser = browser.version();
  await desktop();
  await mobile();
  check(
    !evidence.unexpected_requests.length && !evidence.page_errors.length,
    'offline browsing produces no external requests, WebSockets or uncaught errors',
  );
  evidence.passed = true;
} catch (error) {
  evidence.passed = false;
  evidence.failure = String(error);
  console.error(error);
  process.exitCode = 1;
} finally {
  await writeFile(path.join(values.output, 'browser-qa.json'), JSON.stringify(evidence, null, 2) + '\n');
  await browser.close();
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));
}
