// Exercise the map drill through the normal offline title, including close and clean re-entry.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { digest, launchChromium, openOffline } from './browser-package.mjs';

const [directory, reportFile] = process.argv.slice(2);
if (!directory || !reportFile) throw Error('Pass an extracted release directory and a report path.');
const root = path.resolve(directory);
const html = path.join(root, 'yuga-rust.html');
const bytes = await readFile(html);
const standalone = await readFile(path.join(root, 'ember-rite.html'));
const manifest = JSON.parse(await readFile(path.join(root, 'build.json'), 'utf8'));
assert.equal(digest(bytes), manifest.html_sha256);
assert.equal(digest(standalone), manifest.rehearsal.sha256);
const browser = await launchChromium();
try {
  const context = await browser.newContext({offline: true, viewport: {width: 1000, height: 720}});
  const {tab, entry} = await openOffline(context, {html, bytes});
  const frame = tab.frameLocator('#rehearsal-frame');
  const open = tab.getByRole('button', {name: 'Ember Rite map rehearsal'});
  const dialog = tab.getByRole('dialog', {name: 'Ember Rite solo map rehearsal'});
  const outcomes = [];
  const mixKey = 'yuga.ember-rite.rehearsal.mix.v1';
  for (const district of ['Lanka', 'Kurukshetra']) {
    await open.click();
    await dialog.waitFor();
    await frame.getByRole('heading', {name: 'Mandala Rift', exact: true}).waitFor();
    const drill = tab.frames().find(f => f.url() === 'about:srcdoc');
    assert.ok(drill);
    assert.equal(await drill.evaluate(() => self.origin), 'null');
    assert.equal(await drill.evaluate(() => {
      try { localStorage.getItem('test'); return false; }
      catch (error) { return error.name === 'SecurityError'; }
    }), true);
    await frame.locator('#mix-settings > summary').click();
    const music = frame.locator('#music-volume');
    if (!outcomes.length) {
      await frame.locator('#mono').check();
      await music.focus();
      await music.press('Home');
      for (let step = 0; step < 3; step++) await music.press('ArrowRight');
      await frame.getByRole('button', {name: 'Enable sound'}).click();
    } else {
      await frame.getByRole('button', {name: 'Resume sound'}).waitFor();
      assert.equal(await frame.locator('#sound-toggle').getAttribute('aria-pressed'), 'false');
      assert.equal(await frame.locator('#mono').isChecked(), true);
      assert.equal(await music.inputValue(), '3');
      assert.equal(await frame.locator('#captions').isChecked(), true);
      await frame.getByRole('button', {name: 'Resume sound'}).click();
    }
    await frame.getByRole('button', {name: 'Mute sound'}).waitFor();
    await tab.waitForFunction(key => {
      const saved = JSON.parse(localStorage.getItem(key));
      return saved?.music === 0.03 && saved.mono && saved.enabled;
    }, mixKey);
    assert.equal(await frame.locator('#districts button').count(), 4);
    await frame.getByRole('button', {name: district, exact: true}).click();
    await frame.locator('#mode').selectOption('retake');
    await frame.getByRole('heading', {name: district, exact: true}).waitFor();
    await tab.getByRole('button', {name: 'Back to game title'}).click();
    await dialog.waitFor({state: 'hidden'});
    await tab.waitForFunction(() => !document.getElementById('rehearsal-frame').hasAttribute('srcdoc'));
    assert.equal(await tab.evaluate(() => document.activeElement.id), 'rehearsal-button');
    outcomes.push(district);
  }
  assert.equal(await tab.locator('#menu').isVisible(), true);
  assert.equal(await tab.locator('#play').isVisible(), false);
  await writeFile(reportFile, JSON.stringify({result: 'pass', entry, drill_hash: digest(standalone),
    html_sha256: digest(bytes), districts_tested_through_title: outcomes, opaque_frame: true,
    fresh_drill_and_focus_on_return: true, browser_version: browser.version(),
    preferences_restored: {mono: true, captions: true, music: 0.03},
    fresh_gesture_required_after_reopening: true}, null, 2) + '\n');
} finally {
  await browser.close();
}
