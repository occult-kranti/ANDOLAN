/** node test_desk.mjs [production-base-or-desk-url] [report.json] */
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buffer as readStream } from 'node:stream/consumers';
import { digest, launchChromium } from '../../../yuga-rust/tools/browser-package.mjs';

const route = 'ember-rite/audio/index.html';
const entry = new URL(process.argv[2] || 'http://127.0.0.1:8886/');
if (!entry.pathname.endsWith('/index.html')) {
  const dir = entry.pathname.replace(/\/$/, '');
  entry.pathname = dir + (dir.endsWith('/ember-rite/audio') ? '/index.html' : '/' + route);
}
const local = name => new URL(name, import.meta.url);
const source = new URL('./', entry);
const scoreBytes = await readFile(local('manifest.json'));
const lineBytes = await readFile(local('voice-guide/lines.json'));
const score = JSON.parse(scoreBytes), lines = JSON.parse(lineBytes).clips;
const media = new Map(Object.values(score.assets).map(a => [a.file, a]));
for (const [name, line] of Object.entries(lines)) {
  media.set('voice-guide/' + name, {...line, seconds: line.samples / line.sample_rate, channels: 1});
}
assert.equal(media.size, 11);

const observed = new Map(), errors = [], downloads = new Map();
const report = {entry: route, scoreManifestSha256: digest(scoreBytes), voiceManifestSha256: digest(lineBytes)};
const browser = await launchChromium(false);

function observe(page) {
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (!response.ok()) return;
    const key = response.url(), types = observed.get(key) || new Set();
    types.add(response.request().resourceType());
    observed.set(key, types);
  });
}

function wasRequested(file, kind) {
  assert.ok(observed.get(new URL(file, source).href)?.has(kind), `Browser must request ${file} as ${kind}`);
}

async function playing(page, file, start = 0) {
  const item = media.get(file);
  await page.waitForFunction(({file, start, seconds}) => {
    const audio = document.querySelector('#sound');
    return audio.currentSrc === new URL(file, document.baseURI).href && audio.readyState >= 2 && !audio.paused &&
      !audio.error && !audio.seeking && Math.abs(audio.duration - seconds) < .002 && audio.currentTime > start + .01;
  }, {file, start, seconds: item.seconds}, {timeout: 10000});
  assert.equal(await page.locator('#download').getAttribute('href'), file);
  assert.ok(await page.locator('#notice').isHidden());
  wasRequested(file, 'media');
  let title = 'Full ritual mix';
  if (item.text) {
    const choice = page.locator(`[data-line="${item.event}"]`);
    assert.equal(await page.locator('#transcript').innerText(), item.text);
    assert.equal(await page.locator('#transcript').getAttribute('lang'), item.locale);
    assert.equal(await choice.getAttribute('aria-pressed'), 'true');
    title = `${await choice.innerText()} · ${await page.locator('#lang option:checked').innerText()}`;
  } else {
    assert.ok(await page.locator('#transcript').isHidden());
    if (file !== 'ritual-mix.flac') {
      const choice = page.locator(`[data-file="${file}"]`);
      assert.equal(await choice.getAttribute('aria-pressed'), 'true');
      title = await choice.getAttribute('data-title');
    }
  }
  assert.equal(await page.locator('#track').innerText(), title);
  assert.equal(await page.locator('[aria-pressed="true"]').count(), file === 'ritual-mix.flac' ? 0 : 1);
}

async function checkDownload(page, file) {
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#download').click()]);
  assert.equal(download.suggestedFilename(), path.posix.basename(file));
  const bytes = await readStream(await download.createReadStream());
  const sha256 = digest(bytes);
  const item = media.get(file);
  assert.equal(sha256, item.sha256, `Downloaded bytes of ${file}`);
  const decoded = await page.evaluate(async ({encoded, rate}) => {
    const ctx = window.deskDecoder ??= new OfflineAudioContext(2, 1, rate);
    const raw = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
    const audio = await ctx.decodeAudioData(raw.buffer);
    return {frames: audio.length, channels: audio.numberOfChannels,
      hasSignal: audio.getChannelData(0).some(sample => Math.abs(sample) > .001)};
  }, {encoded: bytes.toString('base64'), rate: score.sample_rate_hz});
  assert.deepEqual(decoded, {frames: item.frames ?? item.samples, channels: item.channels, hasSignal: true});
  downloads.set(file, {file, bytes: bytes.length, frames: decoded.frames, channels: decoded.channels,
    seconds: Number(item.seconds.toFixed(6)), sha256});
  await download.delete();
}

async function seek(page, second, method = 'click') {
  const button = page.locator(`[data-at="${second}"]`);
  await button[method]();
  await playing(page, 'ritual-mix.flac', second);
  const time = await page.locator('#sound').evaluate(m => m.currentTime);
  assert.ok(time < second + 1.5, `Phase button sought ${time} instead of ${second}`);
  assert.equal(await button.getAttribute('aria-current'), 'true');
  assert.equal(await page.locator('[data-at][aria-current="true"]').count(), 1);
}

async function visuals(page) {
  const state = await page.evaluate(async () => {
    const image = document.querySelector('.record img');
    await Promise.all([document.fonts.ready, image.decode()]);
    return {image: {file: image.getAttribute('src'), width: image.naturalWidth, height: image.naturalHeight, alt: image.alt},
      fonts: [...document.fonts].filter(face => face.status === 'loaded').map(face => face.family.replaceAll('"', '')).sort(),
      bodyFont: getComputedStyle(document.body).fontFamily, titleFont: getComputedStyle(document.querySelector('h1')).fontFamily};
  });
  assert.equal(state.image.file, '../mandala-map-studio/concepts/items/rite-ember-vessel.webp');
  assert.ok(state.image.width > 0 && state.image.height > 0 && state.image.alt.length > 0);
  assert.match(state.bodyFont, /DM Sans/);
  assert.match(state.titleFont, /Barlow Condensed/);
  assert.ok(['Barlow Condensed', 'DM Sans'].every(font => state.fonts.includes(font)));
  wasRequested(state.image.file, 'image');
  for (const name of ['dm-sans-latin-400-normal.woff2', 'barlow-condensed-latin-600-normal.woff2']) {
    wasRequested('../four-hero-motion/viewer/fonts/' + name, 'font');
  }
  wasRequested('listen.css', 'stylesheet');
  wasRequested('listen.js', 'script');
  return {image: state.image, loadedFonts: state.fonts};
}

try {
  report.browser = 'Chromium ' + browser.version();
  const desktop = await browser.newContext({viewport: {width: 1280, height: 800}, acceptDownloads: true});
  const page = await desktop.newPage();
  observe(page);
  assert.ok((await page.goto(entry.href)).ok(), 'Listening desk must load');
  report.presentation = await visuals(page);
  assert.equal(await page.locator('audio').count(), 1);
  assert.ok(await page.locator('#sound').evaluate(audio => audio.paused && audio.controls));
  await page.locator('#sound').evaluate(audio => { window.originalDeskTransport = audio; audio.volume = .42; });

  const drone = page.locator('[data-file="drone.flac"]');
  for (let i = 0; i < 35 && !await drone.evaluate(el => el === document.activeElement); i++) {
    await page.keyboard.press('Tab');
  }
  assert.ok(await drone.evaluate(el => el.matches(':focus-visible') && getComputedStyle(el).outlineStyle !== 'none'));
  await page.keyboard.press('Space');
  await playing(page, 'drone.flac');
  report.keyboard = {tabReached: 'drone.flac', visibleFocus: true, activation: 'Space'};

  for (const item of Object.values(score.assets)) {
    if (item.file === 'ritual-mix.flac') continue;
    await page.locator(`[data-file="${item.file}"]`).click();
    await playing(page, item.file);
    await checkDownload(page, item.file);
  }
  await page.locator('[data-line="ignite"]').click();
  await playing(page, 'voice-guide/ignite-en.wav');
  await checkDownload(page, 'voice-guide/ignite-en.wav');
  await page.locator('[data-line="ignite"]').click();
  await playing(page, 'voice-guide/ignite-en.wav');
  await page.locator('#lang').selectOption('hi');
  await playing(page, 'voice-guide/ignite-hi.wav');
  await checkDownload(page, 'voice-guide/ignite-hi.wav');
  await page.locator('[data-line="quench"]').click();
  await playing(page, 'voice-guide/quench-hi.wav');
  await checkDownload(page, 'voice-guide/quench-hi.wav');
  await page.locator('[data-line="quench"]').click();
  await playing(page, 'voice-guide/quench-hi.wav');
  await page.locator('#lang').selectOption('en');
  await playing(page, 'voice-guide/quench-en.wav');
  await checkDownload(page, 'voice-guide/quench-en.wav');
  const sameTransport = await page.locator('#sound').evaluate(m => m === window.originalDeskTransport && m.volume === .42);
  assert.ok(sameTransport);
  report.transport = {players: 1, volumePreserved: true, changedLanguageDuringPlayback: ['ignite', 'quench']};

  for (const second of [0, 10, 20, 30]) await seek(page, second);
  report.phaseButtonSeeksSeconds = [0, 10, 20, 30];
  await checkDownload(page, 'ritual-mix.flac');
  await seek(page, 0);
  // Run the real transport through all four phase changes at its default speed.
  await page.evaluate(() => {
    window.deskPhasesHeard = new Set([0]);
    const media = document.querySelector('#sound');
    media.addEventListener('timeupdate', () => {
      const active = document.querySelector('[data-at][aria-current="true"]');
      if (active) window.deskPhasesHeard.add(Number(active.dataset.at));
    });
  });
  await page.waitForFunction(() => document.querySelector('#sound').ended, null, {timeout: 52000});
  report.fullPlayback = await page.locator('#sound').evaluate(m => ({seconds: m.currentTime, rate: m.playbackRate,
    ended: m.ended, phases: [...window.deskPhasesHeard]}));
  assert.deepEqual(report.fullPlayback, {seconds: 40, rate: 1, ended: true, phases: [0, 10, 20, 30]});
  await desktop.close();

  const phone = await browser.newContext({viewport: {width: 320, height: 720}, isMobile: true, hasTouch: true, deviceScaleFactor: 2});
  const touch = await phone.newPage();
  observe(touch);
  await touch.goto(entry.href);
  await touch.locator('#lang').selectOption('hi');
  await touch.locator('[data-line="quench"]').tap();
  await playing(touch, 'voice-guide/quench-hi.wav');
  const layout = await touch.evaluate(() => ({viewport: innerWidth, document: document.documentElement.scrollWidth,
    overflow: [...document.querySelectorAll('button, select, a, audio, #transcript')].filter(el => {
      const box = el.getBoundingClientRect();
      return box.width && (box.left < -1 || box.right > innerWidth + 1);
    }).map(el => el.textContent.trim() || el.id)}));
  assert.deepEqual(layout, {viewport: 320, document: 320, overflow: []});
  await seek(touch, 30, 'tap');
  report.phone = {...layout, tapped: ['voice-guide/quench-hi.wav', '30-second phase']};
  await phone.close();
  assert.deepEqual(errors, []);
  assert.equal(downloads.size, media.size);
  report.verifiedNativePlaybackAndDownloads = [...downloads.values()].sort((a, b) => a.file.localeCompare(b.file));
  const output = JSON.stringify(report, null, 2) + '\n';
  if (process.argv[3]) {
    await mkdir(path.dirname(process.argv[3]), {recursive: true});
    await writeFile(process.argv[3], output);
  }
  process.stdout.write(output);
} finally {
  await browser.close();
}
