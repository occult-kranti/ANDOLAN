// Photograph an actual ordinary lane match. Only the next animation frame is
// held while Chromium captures the composited HUD and game canvas.
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';
import { digest, launchChromium, openOffline, packageUnderTest } from './browser-package.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const [html = path.join(root, 'dist/yuga-rust.html'), out = path.join(root, 'dist/hanuman-casts')] = process.argv.slice(2);
await mkdir(out, { recursive: true });
const game = await packageUnderTest(html);
const browser = await launchChromium();
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, offline: true });
  const { tab } = await openOffline(context, game);
  await tab.waitForFunction(() => window.yugaProbe?.().mode === 'ready', undefined, { timeout: 120_000 });
  await tab.locator('#hero').selectOption('hanuman');
  await tab.locator('#match').click();
  await tab.waitForFunction(() => window.yugaProbe().state?.army && window.yugaProbe().renderer.heroId === 'hanuman');
  await tab.evaluate(() => {
    const requestFrame = window.requestAnimationFrame.bind(window);
    const delayed = [];
    let hold = false;
    window.requestAnimationFrame = callback => requestFrame(t => {
      if (hold) delayed.push(callback);
      else callback(t);
    });
    window.yugaCapture = {
      arm(action) {
        this.receipt = null;
        const watch = () => {
          const p = window.yugaProbe(), cast = p.state.casts.find(c => c.id === action.id);
          if (!cast || !['windup', 'travel', 'recovery'].includes(cast.phase) ||
              cast.age_ticks < action.minTick || p.renderer.activeClip !== action.clip ||
              !p.renderer.visibleCasts.includes(cast.id) || !p.renderer.poseTime) {
            requestFrame(watch);
            return;
          }
          this.receipt = {
            mode: p.playMode, hero: p.renderer.heroId, actor: p.state.actor.pos, tick: p.state.tick,
            cast: cast.id, clip: p.renderer.activeClip, phase: cast.phase, age_ticks: cast.age_ticks,
            pose_time_s: p.renderer.poseTime, pose_phase: p.renderer.posePhase,
            skinned_surfaces: p.renderer.heroSkinnedSurfaces, bones: p.renderer.heroBones,
            visible_casts: p.renderer.visibleCasts, wave: p.state.army.wave,
          };
          hold = true;
        };
        requestFrame(watch);
      },
      release() {
        hold = false;
        for (const cb of delayed.splice(0)) requestFrame(cb);
      },
    };
  });
  const actions = [
    { id: 'mountain_pulse', key: 'x', clip: 'mountain_pulse', minTick: 14 },
    { id: 'lanka_dahan', key: 'c', clip: 'tail_sweep', minTick: 8 },
  ];
  const frames = [];
  for (const [index, action] of actions.entries()) {
    if (index) {
      await tab.keyboard.press('Escape');
      await tab.locator('#reset').click();
    }
    // Give the ordinary third-person camera one rendered frame before the quick cast.
    await tab.waitForFunction(() => window.yugaProbe().mode === 'playing' && !window.yugaProbe().state.active);
    await tab.evaluate(a => window.yugaCapture.arm(a), action);
    await tab.keyboard.press(action.key);
    await tab.waitForFunction(() => !!window.yugaCapture.receipt, undefined, { polling: 100, timeout: 60_000 });
    const shot = await tab.screenshot({ path: path.join(out, action.id + '.png'), timeout: 60_000 });
    const record = await tab.evaluate(() => window.yugaCapture.receipt);
    assert.equal(record.mode, 'match');
    assert.equal(record.clip, action.clip);
    assert.equal(record.skinned_surfaces, 18);
    frames.push({ ...record, png_sha256: digest(shot), file: action.id + '.png' });
    await tab.evaluate(() => window.yugaCapture.release());
  }
  await writeFile(path.join(out, 'cast-captures.json'), JSON.stringify({
    html_sha256: game.html_sha256, zip_sha256: game.zip_sha256, viewport: [1280, 800],
    method: 'Offline Chromium, ordinary Play lane match, physical keypress, screenshot at an observed active rig pose. The next render frame is held during photography.',
    frames,
  }, null, 2) + '\n');
} finally {
  await browser.close();
}
