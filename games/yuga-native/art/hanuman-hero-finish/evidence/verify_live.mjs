// Exercise the shipped enhanced mesh and its pre-cast indicator using public controls.
import assert from 'node:assert/strict';
import path from 'node:path';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import {
  digest,
  packageUnderTest,
  openOffline,
  launchChromium,
} from '../../../../yuga-rust/tools/browser-package.mjs';
const dir = fileURLToPath(new URL('./', import.meta.url));
const game = path.resolve(dir, '../../../../yuga-rust');
const { values } = parseArgs({
  options: {
    input: { type: 'string', default: path.join(game, 'dist/yuga-rust.html') },
    output: { type: 'string', default: dir },
  },
});
const packaged = await packageUnderTest(values.input);
const browser = await launchChromium();
const context = await browser.newContext({ viewport: { width: 1024, height: 640 }, deviceScaleFactor: 1 });
const checks = [],
  errors = [];
const report = {
  html_sha256: packaged.html_sha256,
  archive_sha256: packaged.zip_sha256,
  browser: browser.version(),
  test_sha256: digest(await readFile(fileURLToPath(import.meta.url))),
  checks,
  errors,
};
const check = (ok, s) => {
  assert.ok(ok, s);
  checks.push(s);
  console.log(s);
};
context.on('page', (p) => p.on('pageerror', (e) => errors.push(e.message)));
let activePage;
try {
  const { tab: page, entry } = await openOffline(context, packaged);
  activePage = page;
  report.transport = entry;
  await page.locator('#begin').click({ timeout: 120000 });
  await page.waitForFunction(() => window.yugaProbe?.().mode === 'playing', null, { timeout: 120000 });
  const read = () => page.evaluate(() => window.yugaProbe());
  const first = await read();
  const surface = first.renderer.heroSkinnedSurfaces;
  const model = await readFile(path.resolve(dir, '../models/hanuman-enhanced.glb'));
  const gltf = JSON.parse(model.subarray(20, 20 + model.readUInt32LE(12)).toString('utf8'));
  const expected = gltf.meshes
    .flatMap((mesh) => mesh.primitives)
    .filter((p) => 'WEIGHTS_0' in p.attributes).length;
  check(
    first.renderer.heroBones === 167 && surface === expected && expected > 17,
    'the playing hero instantiates all weighted finish primitives on the original 167-joint rig',
  );
  report.rig = {
    hero: first.renderer.heroId,
    live_surfaces: surface,
    expected_weighted_primitives: expected,
    glb_sha256: digest(model),
  };
  assert.equal(first.input.mountainAim, null);
  await page.locator('[data-slot="4"]').click();
  await page.waitForFunction(
    () => window.yugaProbe().state.tick >= 6 && window.yugaProbe().input.armedSlot === 4,
    null,
    { polling: 100, timeout: 100000 },
  );
  const guard = (await read()).renderer.targetScreens.find((s) => s.id === 3);
  assert.ok(guard);
  async function aim(x, y) {
    x = Math.round(x);
    y = Math.round(y);
    await page.mouse.move(x, y);
    await page.waitForFunction(
      ({ x, y }) => {
        const i = window.yugaProbe().input;
        return (
          i.pointer &&
          Math.hypot(i.pointer[0] - x, i.pointer[1] - y) < 2 &&
          i.mountainAim?.ground &&
          i.ground &&
          Math.hypot(i.ground[0] - i.mountainAim.ground[0], i.ground[1] - i.mountainAim.ground[1]) < 0.08
        );
      },
      { x, y },
      { timeout: 20000 },
    );
    await page.waitForTimeout(150);
    return (await read()).input.mountainAim;
  }
  const good = await aim(guard.x, guard.y);
  const initialCoach = await page.locator('#match-detail').innerText();
  assert.ok(initialCoach.startsWith('0/5 techniques'));
  report.clear = {
    cue: good,
    target: first.state.targets.find((u) => u.id === 3).pos,
    screen: [guard.x, guard.y],
  };
  check(good.ready && good.code === 0, 'the armed circle marks an in-range guard before any cast');

  const photo = await page.screenshot({ path: path.join(values.output, 'finish-live.png'), timeout: 90000 });
  report.png_sha256 = digest(photo);
  let invalid = null;
  for (const [x, y] of [
    [30, 110],
    [970, 120],
    [85, 240],
    [512, 82],
    [943, 235],
    [500, 116],
  ]) {
    if (!(await page.evaluate(([x, y]) => document.elementFromPoint(x, y)?.id === 'arena', [x, y]))) continue;
    const cue = await aim(x, y);
    if (!cue.ready && cue.ground) {
      invalid = cue;
      break;
    }
  }
  check(
    invalid && [1, 2].includes(invalid.code),
    'aiming elsewhere visibly identifies an invalid pre-cast point',
  );
  report.invalid = invalid;
  const events = (await read()).state.events || [];
  const before = events.filter((e) => e.kind === 'begin' && e.id === 'mountain_pulse').length;
  await page.mouse.down();
  await page.mouse.up();
  await page.waitForTimeout(170);
  const after = await read();
  check(
    !after.state.active && after.input.armedSlot === 4 && after.state.abilities[4].cooldown_ticks === 0,
    'clicking invalid ground leaves the charge and selection available',
  );
  assert.equal(
    (after.state.events || []).filter((e) => e.kind === 'begin' && e.id === 'mountain_pulse').length,
    before,
  );
  const rejectedCoach = await page.locator('#match-detail').innerText();
  check(rejectedCoach === initialCoach, 'an out-of-range click awards zero practice techniques');
  report.rejected_coach = { before: initialCoach, after: rejectedCoach };
  await aim(guard.x, guard.y);
  await page.keyboard.press('Escape');
  await page.waitForFunction(
    () => window.yugaProbe().input.armedSlot === null && window.yugaProbe().input.mountainAim === null,
  );
  check(
    (await read()).mode === 'playing',
    'Escape removes the uncommitted cue and preserves the running drill',
  );
  await page.keyboard.press('KeyX');
  await page.waitForFunction(() => window.yugaProbe().state.abilities[4].cooldown_ticks > 0, null, {
    timeout: 30000,
  });
  check(
    (await read()).input.mountainAim === null,
    'the X shortcut still commits Mountain Pulse directly on the same target',
  );
  check(!errors.length, 'no uncaught browser error while aiming and casting');
  report.passed = true;
} catch (err) {
  report.passed = false;
  report.failure = String(err);
  if (activePage)
    report.last_observation = await activePage
      .evaluate(() => {
        const p = window.yugaProbe();
        return {
          mode: p.mode,
          tick: p.state?.tick,
          frames: p.renderer?.frames,
          input: p.input,
          actor: p.state?.actor,
          status: document.querySelector('#status').textContent,
        };
      })
      .catch(() => null);
  process.exitCode = 1;
  console.error(err);
} finally {
  await writeFile(path.join(values.output, 'finish-live.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
}
